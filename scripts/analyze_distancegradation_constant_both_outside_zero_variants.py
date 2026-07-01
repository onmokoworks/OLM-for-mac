#!/usr/bin/env python3
"""Probe narrow BOTH+OutsideThreshold=0 helper variants for DistanceGradation 16bpc.

This stays diagnostic-only. It targets the only focused Constant case family
that showed a positive signal under the broader 2026-06-30 two-stage helper
probe: `In/Out=Both` with `Outside Threshold=0`.
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
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_both_outside0_variants_20260630.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_both_outside0_variants_20260630.md"

FOCUS = [
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


def normalize_from_actual_max(field: np.ndarray) -> np.ndarray:
    raw_max = float(np.max(field)) if field.size else 0.0
    denom = raw_max if raw_max > 1.0 else 1.0
    return (field / denom).astype(np.float32)


def current_constant_field(mask: np.ndarray, threshold: int, ds_scale: float) -> np.ndarray:
    dist = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    t = 1.0 if threshold == 0 else float(threshold) * ds_scale
    return (dist > max(t, 1.0)).astype(np.float32)


def two_stage_constant_field(mask: np.ndarray, threshold: int, ds_scale: float, variant: str) -> np.ndarray:
    dist1 = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    t = 1.0 if threshold == 0 else float(threshold) * ds_scale
    t = max(t, 1.0)
    trunc = np.minimum(dist1, t).astype(np.float32)

    if variant == "trunc_plateau_binary":
        return (trunc >= t).astype(np.float32)

    stage2_seed = (trunc < t).astype(np.uint8)
    dist2 = ndimage.distance_transform_edt(stage2_seed != 0).astype(np.float32)

    if variant == "trunc_second_dt_binary_lt1":
        return (dist2 < 1.0).astype(np.float32)
    if variant == "trunc_second_dt_norm":
        return normalize_from_actual_max(dist2)
    if variant == "trunc_second_dt_invnorm":
        norm = normalize_from_actual_max(dist2)
        return np.clip(1.0 - norm, 0.0, 1.0).astype(np.float32)
    raise ValueError(f"unknown variant: {variant}")


def constant_field(mask: np.ndarray, threshold: int, ds_scale: float, variant: str) -> np.ndarray:
    if variant == "current_constant":
        return current_constant_field(mask, threshold, ds_scale)
    return two_stage_constant_field(mask, threshold, ds_scale, variant)


def render_variant(input_rgba_u16: np.ndarray, params: dict[str, object], variant: str) -> np.ndarray:
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

    def general_field(current_mask: np.ndarray, threshold: int) -> np.ndarray:
        if interp_mode == DG.INTERP_CONSTANT and blur_mode == DG.BLUR_MODE_NONE:
            return current_constant_field(current_mask, threshold, ds)
        return DG.dt_to_normalized(current_mask, threshold, ds)

    if in_out == DG.IN_OUT_INSIDE:
        x = general_field(mask, inside_threshold)
    elif in_out == DG.IN_OUT_OUTSIDE:
        x = general_field(1 - mask, outside_threshold)
    else:
        inside = general_field(mask, inside_threshold)
        outside_mask = 1 - mask
        outside = general_field(outside_mask, outside_threshold)
        if (
            interp_mode == DG.INTERP_CONSTANT
            and blur_mode == DG.BLUR_MODE_NONE
            and outside_threshold == 0
            and variant != "current_constant"
        ):
            outside = constant_field(outside_mask, outside_threshold, ds, variant)
        x = np.maximum(inside, outside).astype(np.float32)

    if not invert:
        x = 1.0 - x

    if interp_mode == DG.INTERP_SPHERE:
        t = 1.0 - x
        x = np.sqrt(np.maximum(1.0 - t * t, 0.0)).astype(np.float32)
    elif interp_mode == DG.INTERP_POWER:
        x = np.power(x, power).astype(np.float32)
    elif interp_mode == DG.INTERP_CONSTANT:
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
        "current_constant",
        "trunc_plateau_binary",
        "trunc_second_dt_binary_lt1",
        "trunc_second_dt_norm",
        "trunc_second_dt_invnorm",
    ]
    results: list[dict[str, object]] = []
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
            for variant in variants:
                cand = render_variant(input_img, params, variant)
                rows.append({"variant": variant, **diff_stats(cand, ref_img)})
            rows.sort(key=lambda row: (row["nonzero_px"], row["mean_diff"], row["max_diff"]))
            results.append(
                {
                    "case_id": cid,
                    "outside_threshold": params.get("outside_threshold"),
                    "variant_results": rows,
                }
            )

    payload = {
        "kind": "olmdistancegradation_16bpc_constant_both_outside0_variants",
        "status": "diagnostic",
        "request_zip": str(REQUEST_ZIP),
        "results": results,
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc BOTH+Outside=0 Constant Variants - 2026-06-30",
        "",
        "Targeted whole-frame probe that only changes the outside-side Constant helper in `In/Out=Both` cases.",
        "",
        "| Case | Outside Threshold | Best by nonzero | Best by mean | Current nonzero px | Current mean | Reading |",
        "| --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in results:
        current = next(v for v in row["variant_results"] if v["variant"] == "current_constant")
        best_nonzero = min(row["variant_results"], key=lambda r: (r["nonzero_px"], r["mean_diff"], r["max_diff"]))
        best_mean = min(row["variant_results"], key=lambda r: (r["mean_diff"], r["nonzero_px"], r["max_diff"]))
        if best_nonzero["variant"] == "current_constant" and best_mean["variant"] == "current_constant":
            reading = "current stays best"
        elif best_nonzero["variant"] != "current_constant" and best_mean["variant"] == "current_constant":
            reading = "nonzero improves only"
        elif best_nonzero["variant"] == "current_constant" and best_mean["variant"] != "current_constant":
            reading = "mean improves only"
        else:
            reading = "both improve"
        lines.append(
            f"| `{row['case_id'].split('__')[-1]}` | {row['outside_threshold']} | `{best_nonzero['variant']}` ({best_nonzero['nonzero_px']}) | `{best_mean['variant']}` ({best_mean['mean_diff']:.6f}) | {current['nonzero_px']} | {current['mean_diff']:.6f} | {reading} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- This does not change the inside-side helper or general compose logic.",
            "- A win only on `case_0023` would strengthen the `Both + Outside Threshold=0` staging hypothesis without proving it globally.",
            "- Flat results would push the next move back toward exact helper staging / threshold ownership proof from Windows rather than a Mac-side code experiment.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
