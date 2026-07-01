#!/usr/bin/env python3
"""Probe Constant boundary ownership variants for OLMDistanceGradation 16bpc.

This is a bounded diagnostic for the remaining Constant/background family after
the Constant-specific THRESH_BINARY improvement. It does not change the plugin;
it checks whether a tiny threshold-ownership tightening on Constant/no-blur
cases improves the focused whole-frame witnesses.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from scipy import ndimage


REPO = Path(__file__).resolve().parents[1]
REQUEST_ZIP = REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmdistancegradation_extended_exact.zip"
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_threshold_bias_20260630.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_threshold_bias_20260630.md"

FOCUS = [
    "olmdistancegradation_extended__case_0020",
    "olmdistancegradation_extended__case_0021",
    "olmdistancegradation_extended__case_0022",
    "olmdistancegradation_extended__case_0023",
]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(REPO / "refs" / "scripts" / "verify_manifest.py", "verify_manifest")
DG = load_module(REPO / "refs" / "scripts" / "olmdistancegradation_cli.py", "olmdistancegradation_cli")


def constant_field_with_bias(mask: np.ndarray, threshold: int, ds_scale: float, bias: float) -> np.ndarray:
    dist = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    t = 1.0 if threshold == 0 else float(threshold) * ds_scale
    t = max(t, 1.0)
    return (dist > (t + bias)).astype(np.float32)


def render_variant(input_rgba_u16: np.ndarray, params: dict[str, object], threshold_bias: float) -> np.ndarray:
    rgba = input_rgba_u16.astype(np.float32) / 65535.0
    alpha = rgba[..., 3]
    mask = (alpha > 0.0).astype(np.uint8)

    invert = bool(int(params.get("invert", 0)))
    in_out = int(params.get("in_out", DG.IN_OUT_BOTH))
    inside_threshold = int(params.get("inside_threshold", 128))
    outside_threshold = int(params.get("outside_threshold", 128))
    render_mode = int(params.get("render_mode", DG.RENDER_MODE_RGB))
    use_bg = bool(int(params.get("use_background_color", 0)))
    grad_color = DG.color_param(params.get("gradation_color"), (1.0, 0.0, 0.0, 1.0))
    bg_color = DG.color_param(params.get("bg_color"), (0.0, 0.0, 0.0, 1.0))
    interp_mode = int(params.get("interpolation_mode", DG.INTERP_LINEAR))
    power = float(params.get("power", 5.0))
    blur_mode = int(params.get("blur_mode", DG.BLUR_MODE_NONE))
    blur_size = int(params.get("blur_size", 0))
    ds = 1.0

    def field_for(current_mask: np.ndarray, threshold: int) -> np.ndarray:
        if interp_mode == DG.INTERP_CONSTANT and blur_mode == DG.BLUR_MODE_NONE:
            return constant_field_with_bias(current_mask, threshold, ds, threshold_bias)
        return DG.dt_to_normalized(current_mask, threshold, ds)

    if in_out == DG.IN_OUT_INSIDE:
        if not np.any(mask == 0):
            x = np.full(mask.shape, 0.0 if invert else 1.0, dtype=np.float32)
        else:
            x = field_for(mask, inside_threshold)
    elif in_out == DG.IN_OUT_OUTSIDE:
        x = field_for(1 - mask, outside_threshold)
    else:
        inside = field_for(mask, inside_threshold)
        outside = field_for(1 - mask, outside_threshold)
        x = np.maximum(inside, outside).astype(np.float32)

    constant_blur = interp_mode == DG.INTERP_CONSTANT and blur_mode != DG.BLUR_MODE_NONE and blur_size > 0
    if constant_blur:
        x = (x >= 1.0).astype(np.float32)

    if blur_mode != DG.BLUR_MODE_NONE and blur_size > 0:
        radius = blur_size
        if blur_mode == DG.BLUR_MODE_SCALE:
            radius = int(float(blur_size) * ds + 0.5)
        if constant_blur:
            radius *= 2
        x = DG.blur_reflect101(x, max(radius, 1))

    if not invert:
        x = 1.0 - x

    if interp_mode == DG.INTERP_SPHERE:
        t = 1.0 - x
        x = np.sqrt(np.maximum(1.0 - t * t, 0.0)).astype(np.float32)
    elif interp_mode == DG.INTERP_POWER:
        x = np.power(x, power).astype(np.float32)
    elif interp_mode == DG.INTERP_CONSTANT and not constant_blur:
        x = (x > 0.0).astype(np.float32)

    if in_out == DG.IN_OUT_INSIDE:
        out_alpha_base = alpha
    elif in_out == DG.IN_OUT_OUTSIDE:
        out_alpha_base = np.maximum(1.0 - alpha, 0.0)
    else:
        out_alpha_base = np.ones_like(alpha, dtype=np.float32)

    if render_mode == DG.RENDER_MODE_RGB:
        ir = np.full_like(alpha, grad_color[0], dtype=np.float32)
        ig = np.full_like(alpha, grad_color[1], dtype=np.float32)
        ib = np.full_like(alpha, grad_color[2], dtype=np.float32)
    else:
        ir, ig, ib = rgba[..., 0], rgba[..., 1], rgba[..., 2]

    out = np.zeros_like(rgba, dtype=np.float32)
    if use_bg:
        one_x = 1.0 - x
        out[..., 0] = one_x * bg_color[0] + x * ir
        out[..., 1] = one_x * bg_color[1] + x * ig
        out[..., 2] = one_x * bg_color[2] + x * ib
        out[..., 3] = out_alpha_base
        out[..., 0] *= out[..., 3]
        out[..., 1] *= out[..., 3]
        out[..., 2] *= out[..., 3]
    else:
        out[..., 3] = out_alpha_base * x
        out[..., 0] = ir * out[..., 3]
        out[..., 1] = ig * out[..., 3]
        out[..., 2] = ib * out[..., 3]

    return np.clip(np.floor(out * 65535.0 + 0.5), 0, 65535).astype(np.uint16)


def diff_stats(candidate: np.ndarray, reference: np.ndarray) -> dict[str, object]:
    delta = np.abs(candidate.astype(np.int64) - reference.astype(np.int64))
    nz = np.any(delta != 0, axis=-1)
    return {
        "max_diff": int(delta.max()),
        "mean_diff": float(delta.mean()),
        "nonzero_px": int(nz.sum()),
    }


def main() -> int:
    variants = [
        ("bias_0.0_current", 0.0),
        ("bias_0.001", 0.001),
        ("bias_0.01", 0.01),
        ("bias_0.1", 0.1),
        ("bias_0.5", 0.5),
        ("bias_1.0", 1.0),
    ]

    results: list[dict] = []
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        with zipfile.ZipFile(REQUEST_ZIP) as zf:
            zf.extractall(td_path)
        root = next(p for p in td_path.iterdir() if p.is_dir())
        manifest = json.loads((root / "reference_manifest.json").read_text(encoding="utf-8"))

        for cid in FOCUS:
            case = next(c for c in manifest["cases"] if c["id"] == cid)
            params = {
                DG.key_for_name(param.get("name", "")): param.get("value")
                for param in case["effects"][0]["params"]
                if param.get("value") is not None
            }
            input_img = VERIFY.load_rgba(root / "input" / case["before_effects_frame"]).astype(np.uint16)
            ref_img = VERIFY.load_rgba(root / "expected" / case["frame"]).astype(np.uint16)
            rows = []
            for name, bias in variants:
                cand = render_variant(input_img, params, bias)
                rows.append({"variant": name, "threshold_bias": bias, **diff_stats(cand, ref_img)})
            rows.sort(key=lambda row: (row["nonzero_px"], row["mean_diff"], row["max_diff"]))
            results.append({"case_id": cid, "variant_results": rows})

    payload = {
        "kind": "olmdistancegradation_16bpc_constant_threshold_bias",
        "status": "diagnostic",
        "request_zip": str(REQUEST_ZIP),
        "results": results,
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc Constant Threshold Bias - 2026-06-30",
        "",
        "Whole-frame comparison of small Constant/no-blur threshold-bias variants on the focused boundary cases.",
        "",
        "| Case | Best variant | Best nonzero px | Current nonzero px | Best mean | Current mean |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    improved_cases = 0
    for row in results:
        best = row["variant_results"][0]
        current = next(v for v in row["variant_results"] if v["variant"] == "bias_0.0_current")
        if best["variant"] != "bias_0.0_current":
            improved_cases += 1
        lines.append(
            f"| `{row['case_id'].split('__')[-1]}` | `{best['variant']}` | {best['nonzero_px']} | {current['nonzero_px']} | {best['mean_diff']:.6f} | {current['mean_diff']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            f"- Cases improved by any bias variant: `{improved_cases}/{len(results)}`.",
            "- This is only a bounded threshold-ownership probe for Constant/no-blur slices.",
            "- If no bias variant wins decisively, the remaining lane is probably not a simple `>` vs `> + eps` ownership tweak.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
