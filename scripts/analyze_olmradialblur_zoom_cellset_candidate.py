#!/usr/bin/env python3
"""Evaluate bounded final-polar cell-set candidates for RadialBlur Zoom.

This is a local triage script. It does not change rendering behavior. It asks
whether a small, global `(angle_cell_offset, radius_cell_offset)` applied to
the four final-polar cells can explain the Windows top-row alpha=254 set for
`case_0009` without broad false positives.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LOCUS_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_quantize_locus_20260709.json"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_cellset_candidate_20260709.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_cellset_candidate_20260709.md"


def load_prefill_module() -> Any:
    path = ROOT / "scripts" / "analyze_olmradialblur_zoom_prefill_coordinate_probe.py"
    spec = importlib.util.spec_from_file_location("olmrb_prefill_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--locus-json", type=Path, default=LOCUS_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--offset-span", type=int, default=2)
    return parser.parse_args()


def q_epsilon(alpha: float, prefill: Any) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0 + 1.0e-4))))


def q_truncate(alpha: float) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0))))


def final_weights(row: dict[str, Any], prefill: Any) -> dict[str, Any]:
    radius_index = float(row["radius_index"])
    angle_index = float(row["angle_index"])
    ri = math.floor(radius_index)
    ai = math.floor(angle_index)
    fx = prefill.f32(radius_index - float(ri))
    fy = prefill.f32(angle_index - float(ai))
    return {
        "ri": int(ri),
        "ai": int(ai),
        "fx": fx,
        "fy": fy,
        "weights": [
            float(1.0 - fx) * float(1.0 - fy),
            float(fx) * float(1.0 - fy),
            float(1.0 - fx) * float(fy),
            float(fx) * float(fy),
        ],
    }


def cell_alpha_for(prefill: Any, alpha: np.ndarray, geom: dict[str, Any], ai: int, ri: int, mode: str) -> float:
    ai = ai % int(geom["angular_count"])
    ri = max(0, min(int(geom["radius_count"]) - 1, ri))
    sx, sy = prefill.source_xy_for_cell(
        ai,
        ri,
        int(geom["min_r"]),
        float(geom["step_rad"]),
        float(geom["ratio"]),
        float(geom["cx"]),
        float(geom["cy"]),
        float(geom["base_angle"]),
        mode,
    )
    return float(prefill.bilinear_alpha_repeat_f32(alpha, sx, sy)["alpha"])


def candidate_alpha(
    prefill: Any,
    alpha: np.ndarray,
    geom: dict[str, Any],
    row: dict[str, Any],
    angle_offset: int,
    radius_offset: int,
    source_mode: str,
) -> dict[str, Any]:
    fw = final_weights(row, prefill)
    base_cells = [
        [fw["ai"], fw["ri"]],
        [fw["ai"], fw["ri"] + 1],
        [fw["ai"] + 1, fw["ri"]],
        [fw["ai"] + 1, fw["ri"] + 1],
    ]
    cells = [[ai + angle_offset, ri + radius_offset] for ai, ri in base_cells]
    cell_alphas = [cell_alpha_for(prefill, alpha, geom, ai, ri, source_mode) for ai, ri in cells]
    total = sum(a * w for a, w in zip(cell_alphas, fw["weights"]))
    return {
        "alpha": total,
        "cells": cells,
        "cell_alphas": cell_alphas,
        "weights": fw["weights"],
    }


def classify(rows: list[dict[str, Any]], candidate_by_x: dict[int, dict[str, Any]], quantizer: str) -> dict[str, Any]:
    target = {int(row["x"]) for row in rows if row["reference"][3] == 254}
    qfunc = q_truncate if quantizer == "truncate" else lambda value: q_epsilon(value, None)
    emitted = {x for x, item in candidate_by_x.items() if qfunc(float(item["alpha"])) == 254}
    return {
        "quantizer": quantizer,
        "emitted_254": sorted(emitted),
        "tp": sorted(emitted & target),
        "fp": sorted(emitted - target),
        "fn": sorted(target - emitted),
        "score_tuple": [len(target - emitted), len(emitted - target), -len(emitted & target)],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    prefill = load_prefill_module()
    manifest, case = prefill.load_case(args.case_id)
    params = prefill.params_from_case(case)
    geom = prefill.geometry(manifest, case, params)
    image_alpha = np.asarray(geom["image"], dtype=np.uint8)[..., 3].astype(np.float32) / 255.0
    locus = prefill.read_json(args.locus_json)
    rows = locus["variants"]["polar_alpha"]["row"]
    target = sorted(int(row["x"]) for row in rows if row["reference"][3] == 254)
    results: list[dict[str, Any]] = []
    span = int(args.offset_span)
    for source_mode in ("cpp-aex-float", "cpp-double", "python-prefill-f32"):
        for angle_offset in range(-span, span + 1):
            for radius_offset in range(-span, span + 1):
                by_x: dict[int, dict[str, Any]] = {}
                for row in rows:
                    x = int(row["x"])
                    by_x[x] = candidate_alpha(
                        prefill,
                        image_alpha,
                        geom,
                        row,
                        angle_offset,
                        radius_offset,
                        source_mode,
                    )
                classifications = [classify(rows, by_x, "epsilon"), classify(rows, by_x, "truncate")]
                results.append(
                    {
                        "source_mode": source_mode,
                        "angle_offset": angle_offset,
                        "radius_offset": radius_offset,
                        "classifications": classifications,
                        "target_details": {str(x): by_x[x] for x in target},
                    }
                )
    ranked = sorted(
        results,
        key=lambda item: (
            min(cls["score_tuple"] for cls in item["classifications"]),
            abs(item["angle_offset"]) + abs(item["radius_offset"]),
            item["source_mode"],
        ),
    )
    return {
        "kind": "olmradialblur_zoom_case0009_cellset_candidate",
        "schema": 1,
        "case_id": args.case_id,
        "source_locus": str(args.locus_json),
        "target_alpha254": target,
        "offset_span": span,
        "top_candidates": ranked[:20],
        "all_candidate_count": len(results),
        "interpretation": (
            "A candidate is only useful if it hits the target alpha=254 row positions with few false "
            "positives. If only truncate variants work and they still produce false positives, this "
            "should remain a witness request rather than a Mac implementation change."
        ),
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom Cell-Set Candidate Probe",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Target alpha=254 x positions: `{report['target_alpha254']}`",
        f"- Offset span: `+/-{report['offset_span']}`",
        "",
        "## Top Candidates",
        "",
        "| Rank | source mode | angle offset | radius offset | quantizer | emitted 254 | TP | FP | FN |",
        "| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for idx, candidate in enumerate(report["top_candidates"], start=1):
        best = sorted(candidate["classifications"], key=lambda item: item["score_tuple"])[0]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx),
                    f"`{candidate['source_mode']}`",
                    str(candidate["angle_offset"]),
                    str(candidate["radius_offset"]),
                    f"`{best['quantizer']}`",
                    f"`{best['emitted_254']}`",
                    f"`{best['tp']}`",
                    f"`{best['fp']}`",
                    f"`{best['fn']}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Best Target Details", ""])
    if report["top_candidates"]:
        best_candidate = report["top_candidates"][0]
        lines.append(
            f"- Best offsets: mode=`{best_candidate['source_mode']}`, "
            f"angle=`{best_candidate['angle_offset']}`, radius=`{best_candidate['radius_offset']}`"
        )
        for x, detail in best_candidate["target_details"].items():
            lines.append(f"- x={x}: alpha=`{detail['alpha']}`, cells=`{detail['cells']}`, cell_alphas=`{detail['cell_alphas']}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    if report["top_candidates"]:
        best = report["top_candidates"][0]
        best_cls = sorted(best["classifications"], key=lambda item: item["score_tuple"])[0]
        print(
            "best="
            + json.dumps(
                {
                    "source_mode": best["source_mode"],
                    "angle_offset": best["angle_offset"],
                    "radius_offset": best["radius_offset"],
                    "classification": best_cls,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
