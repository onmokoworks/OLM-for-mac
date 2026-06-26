#!/usr/bin/env python3
"""Compare simple 16bpc DistanceGradation field-combine variants.

This is a diagnostic only. It checks whether the current `Both=max(inside, outside)`
rule can be replaced by a simpler alternative such as `min`, `inside`, `outside`,
or an `Outside Threshold=0` special case for the focused extended cases.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[1]
REQUEST_ZIP = REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmdistancegradation_extended_exact.zip"
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_variants_20260626.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_variants_20260626.md"

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


def render_variant(input_rgba_u16: np.ndarray, params: dict[str, object], both_mode: str, zero_mode: str) -> np.ndarray:
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

    if in_out == DG.IN_OUT_INSIDE:
        if not np.any(mask == 0):
            x = np.full(mask.shape, 0.0 if invert else 1.0, dtype=np.float32)
        else:
            x = DG.dt_to_normalized(mask, inside_threshold, ds)
    elif in_out == DG.IN_OUT_OUTSIDE:
        x = DG.dt_to_normalized(1 - mask, outside_threshold, ds)
    else:
        inside = DG.dt_to_normalized(mask, inside_threshold, ds)
        outside = DG.dt_to_normalized(1 - mask, outside_threshold, ds)
        if zero_mode == "inside-only-when-outside-zero" and outside_threshold == 0:
            x = inside
        elif zero_mode == "force-zero-when-outside-zero" and outside_threshold == 0:
            x = np.zeros_like(inside, dtype=np.float32)
        elif both_mode == "min":
            x = np.minimum(inside, outside).astype(np.float32)
        elif both_mode == "inside":
            x = inside
        elif both_mode == "outside":
            x = outside
        else:
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
        ("current_max", {"both_mode": "max", "zero_mode": "none"}),
        ("both_min", {"both_mode": "min", "zero_mode": "none"}),
        ("both_inside", {"both_mode": "inside", "zero_mode": "none"}),
        ("both_outside", {"both_mode": "outside", "zero_mode": "none"}),
        ("outside_zero_inside_only", {"both_mode": "max", "zero_mode": "inside-only-when-outside-zero"}),
        ("outside_zero_force_zero", {"both_mode": "max", "zero_mode": "force-zero-when-outside-zero"}),
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
            for name, config in variants:
                cand = render_variant(input_img, params, **config)
                rows.append({"variant": name, **diff_stats(cand, ref_img)})
            rows.sort(key=lambda row: (row["nonzero_px"], row["mean_diff"], row["max_diff"]))
            results.append({"case_id": cid, "variant_results": rows})

    payload = {
        "kind": "olmdistancegradation_16bpc_constant_variants",
        "status": "diagnostic",
        "request_zip": str(REQUEST_ZIP),
        "results": results,
        "conclusion": [
            "A witness-level `Both=min(...)` intuition does not survive a whole-frame check.",
            "For the focused 16bpc extended cases, the simple `min`, `inside`, `outside`, or `Outside Threshold=0` shortcut variants all stay incorrect, and some are dramatically worse than the current `Both=max(...)` baseline.",
            "So the remaining 16bpc DistanceGradation mismatch is not solved by a one-line combine-rule swap; it still points to a narrower upstream field-prep / threshold-zero branch.",
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# DistanceGradation 16bpc Constant Variants - 2026-06-26",
        "",
        "Whole-frame comparison of simple `Both` / threshold-zero variants on the focused extended cases.",
        "",
        "| Case | Best variant | Best nonzero px | Current nonzero px | Note |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in results:
        best = row["variant_results"][0]
        current = next(v for v in row["variant_results"] if v["variant"] == "current_max")
        note = "current stays best or tied"
        if best["variant"] != "current_max":
            note = "variant beats current"
        lines.append(
            f"| `{row['case_id'].split('__')[-1]}` | `{best['variant']}` | {best['nonzero_px']} | {current['nonzero_px']} | {note} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "- The witness-level `min(...)` hint is real, but it does not improve the whole frame by itself.",
            "- Simple swaps such as `Both=min`, `Both=inside`, or `Both=outside` are not safe fixes.",
            "- The remaining problem still looks like a narrower upstream field-prep rule, especially around Constant mode and `Outside Threshold=0`.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
