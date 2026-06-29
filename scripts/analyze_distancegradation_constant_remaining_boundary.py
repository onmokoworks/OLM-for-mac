#!/usr/bin/env python3
"""Analyze remaining OLMDistanceGradation 16bpc Constant boundary residuals."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refs.scripts.verify_manifest import load_rgba


CASE_IDS = (
    "olmdistancegradation_extended__case_0020",
    "olmdistancegradation_extended__case_0021",
    "olmdistancegradation_extended__case_0022",
    "olmdistancegradation_extended__case_0023",
)


def repo_root() -> Path:
    return ROOT


def params_by_name(case: dict) -> dict[str, object]:
    params: dict[str, object] = {}
    for effect in case.get("effects", []):
        if effect.get("match_name") != "OLM Distance Gradation":
            continue
        for param in effect.get("params", []):
            params[param["name"]] = param.get("value")
    return params


def distance_stats(values: np.ndarray, threshold: float) -> dict[str, object]:
    if values.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "nearest_threshold_delta": None,
            "within_0_25": 0,
            "within_0_5": 0,
            "within_1_0": 0,
        }
    deltas = np.abs(values - threshold)
    return {
        "count": int(values.size),
        "min": float(values.min()),
        "max": float(values.max()),
        "nearest_threshold_delta": float(deltas.min()),
        "within_0_25": int((deltas <= 0.25).sum()),
        "within_0_5": int((deltas <= 0.5).sum()),
        "within_1_0": int((deltas <= 1.0).sum()),
    }


def main() -> int:
    root = repo_root()
    request_dir = root / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
    candidate_dir = root / "refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_constant_binary_20260629_1454/candidate"
    manifest = json.loads((request_dir / "reference_manifest.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in manifest["cases"]}

    rows = []
    for case_id in CASE_IDS:
        case = cases[case_id]
        params = params_by_name(case)
        frame = case["frame"]
        input_frame = case["before_effects_frame"]
        reference = load_rgba(request_dir / "expected" / frame).astype(np.int64)
        candidate = load_rgba(candidate_dir / frame).astype(np.int64)
        source = load_rgba(request_dir / "input" / input_frame).astype(np.int64)
        diff = candidate - reference
        changed = np.any(diff != 0, axis=2)

        alpha_mask = source[:, :, 3] > 0
        inside_dist = ndimage.distance_transform_edt(alpha_mask)
        outside_dist = ndimage.distance_transform_edt(~alpha_mask)
        inside_values = inside_dist[changed]
        outside_values = outside_dist[changed]
        in_out = int(params["In/Out"])
        inside_threshold = float(params["Inside Threshold"])
        outside_threshold = float(params["Outside Threshold"])

        if in_out == 1:
            active_values = inside_values
            active_threshold = inside_threshold
            active_side = "inside"
        elif in_out == 2:
            active_values = outside_values
            active_threshold = outside_threshold
            active_side = "outside"
        else:
            inside_delta = np.abs(inside_values - inside_threshold)
            outside_delta = np.abs(outside_values - outside_threshold)
            use_inside = inside_delta <= outside_delta
            active_values = np.where(use_inside, inside_values, outside_values)
            active_threshold = np.where(use_inside, inside_threshold, outside_threshold)
            active_side = "both-nearest"

        yx = np.argwhere(changed)
        examples = []
        for y, x in yx[:8]:
            examples.append(
                {
                    "x": int(x),
                    "y": int(y),
                    "source": source[y, x].tolist(),
                    "reference": reference[y, x].tolist(),
                    "candidate": candidate[y, x].tolist(),
                    "delta": diff[y, x].tolist(),
                    "inside_distance": float(inside_dist[y, x]),
                    "outside_distance": float(outside_dist[y, x]),
                    "inside_threshold_delta": float(inside_dist[y, x] - inside_threshold),
                    "outside_threshold_delta": float(outside_dist[y, x] - outside_threshold),
                }
            )

        active_delta = np.abs(active_values - active_threshold)
        rows.append(
            {
                "case_id": case_id,
                "frame": frame,
                "params": params,
                "nonzero_px": int(changed.sum()),
                "max_diff": int(np.abs(diff).max()),
                "mean_abs_diff": float(np.abs(diff).mean()),
                "active_side": active_side,
                "inside_distance_stats": distance_stats(inside_values, inside_threshold),
                "outside_distance_stats": distance_stats(outside_values, outside_threshold),
                "active_nearest_threshold_delta": float(active_delta.min()) if active_delta.size else None,
                "active_within_1_0": int((active_delta <= 1.0).sum()) if active_delta.size else 0,
                "examples": examples,
            }
        )

    output = {
        "kind": "olmdistancegradation_16bpc_constant_remaining_boundary",
        "date": "2026-06-29",
        "request_dir": str(request_dir.relative_to(root)),
        "candidate_dir": str(candidate_dir.relative_to(root)),
        "conclusion": (
            "The remaining Constant-mode residuals after the binary-threshold fix are sparse "
            "and sit on distance-threshold boundary decisions. Treat them as OpenCV/AEX "
            "distanceTransform threshold ownership work, not compose/writeback tuning."
        ),
        "rows": rows,
    }

    json_path = root / "refs/conformance/olmdistancegradation_16bpc_constant_remaining_boundary_20260629.json"
    md_path = root / "refs/conformance/olmdistancegradation_16bpc_constant_remaining_boundary_20260629.md"
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc Constant Remaining Boundary",
        "",
        f"- Request dir: `{output['request_dir']}`",
        f"- Candidate dir: `{output['candidate_dir']}`",
        f"- Conclusion: {output['conclusion']}",
        "",
        "| Case | nonzero_px | max | mean | active side | active <=1px from threshold | nearest delta |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in rows:
        nearest = row["active_nearest_threshold_delta"]
        nearest_text = "n/a" if nearest is None else f"{nearest:.6f}"
        lines.append(
            f"| `{row['case_id']}` | {row['nonzero_px']} | {row['max_diff']} | "
            f"{row['mean_abs_diff']:.4f} | `{row['active_side']}` | "
            f"{row['active_within_1_0']} | {nearest_text} |"
        )
    lines.extend(["", "## Witness Examples", ""])
    for row in rows:
        lines.append(f"### {row['case_id']}")
        for ex in row["examples"][:4]:
            lines.append(
                f"- `({ex['x']},{ex['y']})`: ref={ex['reference']} cand={ex['candidate']} "
                f"inside={ex['inside_distance']:.6f} outside={ex['outside_distance']:.6f}"
            )
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json_path)
    print(md_path)
    for row in rows:
        print(
            row["case_id"],
            "nonzero_px",
            row["nonzero_px"],
            "active_within_1_0",
            row["active_within_1_0"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
