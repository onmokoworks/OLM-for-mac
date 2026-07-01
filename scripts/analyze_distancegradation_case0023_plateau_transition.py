#!/usr/bin/env python3
"""Analyze how the best case_0023 Constant helper variant changes residual buckets.

This stays diagnostic-only. It compares the current Constant helper against the
best local probe variant (`trunc_plateau_binary`) for the remaining
OLMDistanceGradation 16bpc `case_0023` lane and reports which EDT buckets and
endpoint pairs actually improve.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage


REPO = Path(__file__).resolve().parents[1]
REQUEST_ZIP = REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmdistancegradation_extended_exact.zip"
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_case0023_plateau_transition_20260701.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_case0023_plateau_transition_20260701.md"
CASE_ID = "olmdistancegradation_extended__case_0023"
CURRENT_CANDIDATE = (
    REPO
    / "refs"
    / "reports"
    / "ae_single_case_distancegradation_constant_no_post_20260630"
    / "olmdistancegradation_extended__case_0023"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png"
)


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
    if variant == "trunc_second_dt_invnorm":
        norm = normalize_from_actual_max(dist2)
        return np.clip(1.0 - norm, 0.0, 1.0).astype(np.float32)
    raise ValueError(f"unknown variant: {variant}")


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
            outside = two_stage_constant_field(outside_mask, outside_threshold, ds, variant)
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


def rgba_key(px: np.ndarray) -> str:
    return ",".join(str(int(v)) for v in px.tolist())


def bucketize(candidate: np.ndarray, reference: np.ndarray, inside: np.ndarray, outside: np.ndarray) -> dict[str, object]:
    residual = np.any(candidate != reference, axis=-1)
    ys, xs = np.where(residual)
    buckets: dict[str, dict[str, object]] = {}
    endpoint_pairs: dict[str, int] = defaultdict(int)
    examples: list[dict[str, object]] = []
    for idx, (y, x) in enumerate(zip(ys.tolist(), xs.tolist(), strict=False)):
        cand_px = candidate[y, x]
        ref_px = reference[y, x]
        inside_v = float(inside[y, x])
        outside_v = float(outside[y, x])
        key = f"{inside_v:.6f}"
        bucket = buckets.setdefault(
            key,
            {
                "inside_distance": inside_v,
                "count": 0,
                "outside_distance_values": set(),
                "candidate_rgba_counts": defaultdict(int),
                "reference_rgba_counts": defaultdict(int),
            },
        )
        bucket["count"] += 1
        bucket["outside_distance_values"].add(round(outside_v, 6))
        bucket["candidate_rgba_counts"][rgba_key(cand_px)] += 1
        bucket["reference_rgba_counts"][rgba_key(ref_px)] += 1
        endpoint_pairs[f"{rgba_key(cand_px)} -> {rgba_key(ref_px)}"] += 1
        if idx < 12:
            examples.append(
                {
                    "x": x,
                    "y": y,
                    "inside_distance": inside_v,
                    "outside_distance": outside_v,
                    "candidate_rgba": cand_px.tolist(),
                    "reference_rgba": ref_px.tolist(),
                }
            )
    serializable_buckets = []
    for _, row in sorted(buckets.items(), key=lambda item: float(item[0])):
        serializable_buckets.append(
            {
                "inside_distance": row["inside_distance"],
                "count": row["count"],
                "outside_distance_values": sorted(row["outside_distance_values"]),
                "candidate_rgba_counts": dict(sorted(row["candidate_rgba_counts"].items())),
                "reference_rgba_counts": dict(sorted(row["reference_rgba_counts"].items())),
            }
        )
    return {
        "residual_px": int(residual.sum()),
        "buckets": serializable_buckets,
        "endpoint_pairs": dict(sorted(endpoint_pairs.items())),
        "examples": examples,
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        with zipfile.ZipFile(REQUEST_ZIP) as zf:
            zf.extractall(td_path)
        root = next(p for p in td_path.iterdir() if p.is_dir())
        manifest = json.loads((root / "reference_manifest.json").read_text(encoding="utf-8"))
        case = next(c for c in manifest["cases"] if c["id"] == CASE_ID)
        params = {
            DG.key_for_name(param.get("name", "")): param.get("value")
            for param in case["effects"][0]["params"]
            if param.get("value") is not None
        }
        input_img = VERIFY.load_rgba(root / "input" / case["before_effects_frame"]).astype(np.uint16)
        ref_img = VERIFY.load_rgba(root / "expected" / case["frame"]).astype(np.uint16)

    alpha = input_img[..., 3].astype(np.float32) / 65535.0
    mask = (alpha > 0.0).astype(np.uint8)
    inside = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    outside = ndimage.distance_transform_edt((1 - mask) != 0).astype(np.float32)

    current = VERIFY.load_rgba(CURRENT_CANDIDATE).astype(np.uint16)
    plateau = render_variant(input_img, params, "trunc_plateau_binary")
    current_diag = bucketize(current, ref_img, inside, outside)
    plateau_diag = bucketize(plateau, ref_img, inside, outside)

    current_buckets = {f"{row['inside_distance']:.6f}": row for row in current_diag["buckets"]}
    plateau_buckets = {f"{row['inside_distance']:.6f}": row for row in plateau_diag["buckets"]}
    bucket_transition = []
    for key in sorted(set(current_buckets) | set(plateau_buckets), key=float):
        before = current_buckets.get(key)
        after = plateau_buckets.get(key)
        bucket_transition.append(
            {
                "inside_distance": float(key),
                "current_count": int(before["count"]) if before else 0,
                "plateau_count": int(after["count"]) if after else 0,
                "delta_count": (int(after["count"]) if after else 0) - (int(before["count"]) if before else 0),
                "current_candidate_rgba_counts": before["candidate_rgba_counts"] if before else {},
                "plateau_candidate_rgba_counts": after["candidate_rgba_counts"] if after else {},
                "reference_rgba_counts": (before or after or {}).get("reference_rgba_counts", {}),
            }
        )

    payload = {
        "kind": "olmdistancegradation_16bpc_case0023_plateau_transition",
        "status": "diagnostic",
        "request_zip": str(REQUEST_ZIP),
        "case_id": CASE_ID,
        "current_candidate": str(CURRENT_CANDIDATE),
        "current_constant": current_diag,
        "trunc_plateau_binary": plateau_diag,
        "bucket_transition": bucket_transition,
        "reading": [
            "The only improved local variant remains trunc_plateau_binary on the outside-side Constant helper.",
            "This report shows which raw inside-EDT buckets actually shrink under that variant.",
            "Use it to decide whether the next source edit should stay in outside-side Constant helper staging or move back to generic BOTH ownership."
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc case_0023 Plateau Transition - 2026-07-01",
        "",
        "Bucket-by-bucket comparison between the current Constant helper and the best local outside-side probe variant `trunc_plateau_binary`.",
        "",
        f"- Current residual px: `{current_diag['residual_px']}`",
        f"- Plateau residual px: `{plateau_diag['residual_px']}`",
        "",
        "| Inside raw EDT | Current count | Plateau count | Delta |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in bucket_transition:
        lines.append(
            f"| `{row['inside_distance']:.6f}` | {row['current_count']} | {row['plateau_count']} | {row['delta_count']} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- If improvement concentrates only in the `inside EDT = 1.0` bucket while the threshold-edge bucket stays wrong, the next edit should stay in the outside-side Constant helper staging for `Both + Outside Threshold=0`.",
            "- If both the `1.0` plateau bucket and the near-threshold `36.013885...` bucket shrink together, the surviving issue is more likely the combined `BOTH` ownership rule than a pure equality tweak.",
            "- This is still a local probe, not proof of the Windows rule.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
