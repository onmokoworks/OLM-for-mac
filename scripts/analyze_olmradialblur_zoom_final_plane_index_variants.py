#!/usr/bin/env python3
"""Probe final-plane index/coordinate variants for RadialBlur Zoom case_0009.

This is a local evidence script. It does not render images or change Mac code.
It asks whether bounded changes to the final polar-plane index calculation
can explain the Windows top-row alpha=254 set without broad false positives.
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
LOCUS_JSON = ROOT / "refs/conformance/olmradialblur_zoom_case0009_quantize_locus_20260709.json"
DEFAULT_JSON = ROOT / "refs/conformance/olmradialblur_zoom_case0009_final_plane_index_variants_20260709.json"
DEFAULT_MD = ROOT / "refs/conformance/olmradialblur_zoom_case0009_final_plane_index_variants_20260709.md"
TARGET_ALPHA254 = {6, 7, 12}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
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
    return parser.parse_args()


def q_epsilon(alpha: float) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0 + 1.0e-4))))


def q_truncate(alpha: float) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0))))


def shifted_alpha(
    cellset: Any,
    prefill: Any,
    alpha: np.ndarray,
    geom: dict[str, Any],
    row: dict[str, Any],
    *,
    source_mode: str,
    angle_bias: float,
    radius_bias: float,
    fraction_mode: str,
) -> dict[str, Any]:
    shifted = dict(row)
    radius_index = float(row["radius_index"]) + radius_bias
    angle_index = float(row["angle_index"]) + angle_bias
    if fraction_mode == "f32-before-floor":
        radius_index = prefill.f32(radius_index)
        angle_index = prefill.f32(angle_index)
    shifted["radius_index"] = radius_index
    shifted["angle_index"] = angle_index
    result = cellset.candidate_alpha(
        prefill,
        alpha,
        geom,
        shifted,
        0,
        0,
        source_mode,
    )
    result["radius_index"] = radius_index
    result["angle_index"] = angle_index
    result["fraction_mode"] = fraction_mode
    return result


def classify(rows: list[dict[str, Any]], by_x: dict[int, dict[str, Any]], quantizer: str) -> dict[str, Any]:
    qfunc = q_truncate if quantizer == "truncate" else q_epsilon
    emitted = {x for x, item in by_x.items() if qfunc(float(item["alpha"])) == 254}
    target = {int(row["x"]) for row in rows if int(row["reference"][3]) == 254}
    return {
        "quantizer": quantizer,
        "emitted_254": sorted(emitted),
        "tp": sorted(emitted & target),
        "fp": sorted(emitted - target),
        "fn": sorted(target - emitted),
        "score_tuple": [len(target - emitted), len(emitted - target), -len(emitted & target)],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    prefill = load_module("olmrb_prefill_probe", ROOT / "scripts/analyze_olmradialblur_zoom_prefill_coordinate_probe.py")
    cellset = load_module("olmrb_cellset_probe", ROOT / "scripts/analyze_olmradialblur_zoom_cellset_candidate.py")
    manifest, case = prefill.load_case(args.case_id)
    params = prefill.params_from_case(case)
    geom = prefill.geometry(manifest, case, params)
    image_alpha = np.asarray(geom["image"], dtype=np.uint8)[..., 3].astype(np.float32) / 255.0
    locus = prefill.read_json(args.locus_json)
    rows = locus["variants"]["polar_alpha"]["row"]
    biases = [-1.0, -0.5, -0.001, -0.0001, 0.0, 0.0001, 0.001, 0.5, 1.0]
    source_modes = ["cpp-aex-float", "cpp-double", "python-prefill-f32"]
    fraction_modes = ["double-before-floor", "f32-before-floor"]
    results: list[dict[str, Any]] = []

    for source_mode in source_modes:
        for fraction_mode in fraction_modes:
            for angle_bias in biases:
                for radius_bias in biases:
                    by_x = {
                        int(row["x"]): shifted_alpha(
                            cellset,
                            prefill,
                            image_alpha,
                            geom,
                            row,
                            source_mode=source_mode,
                            angle_bias=angle_bias,
                            radius_bias=radius_bias,
                            fraction_mode=fraction_mode,
                        )
                        for row in rows
                    }
                    classifications = [classify(rows, by_x, "epsilon"), classify(rows, by_x, "truncate")]
                    results.append(
                        {
                            "source_mode": source_mode,
                            "fraction_mode": fraction_mode,
                            "angle_bias": angle_bias,
                            "radius_bias": radius_bias,
                            "classifications": classifications,
                            "target_details": {str(x): by_x[x] for x in sorted(TARGET_ALPHA254)},
                        }
                    )

    ranked = sorted(
        results,
        key=lambda item: (
            min(cls["score_tuple"] for cls in item["classifications"]),
            abs(float(item["angle_bias"])) + abs(float(item["radius_bias"])),
            item["source_mode"],
            item["fraction_mode"],
        ),
    )
    best = ranked[0] if ranked else None
    best_cls = sorted(best["classifications"], key=lambda item: item["score_tuple"])[0] if best else None
    return {
        "kind": "olmradialblur_zoom_case0009_final_plane_index_variants",
        "schema": 1,
        "case_id": args.case_id,
        "source_locus": str(args.locus_json),
        "target_alpha254": sorted(TARGET_ALPHA254),
        "biases_tested": biases,
        "top_candidates": ranked[:20],
        "all_candidate_count": len(results),
        "interpretation": (
            "This probes only final-plane index arithmetic. A candidate is implementation-worthy only if it "
            "hits x=[6,7,12] with no or very few false positives and is later grounded by asm/runtime witness. "
            f"Current best emits {best_cls['emitted_254'] if best_cls else []}; keep this as analysis evidence, "
            "not a Mac source change."
        ),
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom Final-Plane Index Variant Probe",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Target alpha=254 x positions: `{report['target_alpha254']}`",
        f"- Candidates tested: `{report['all_candidate_count']}`",
        "",
        "## Top Candidates",
        "",
        "| Rank | source mode | fraction mode | angle bias | radius bias | quantizer | emitted 254 | TP | FP | FN |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for index, candidate in enumerate(report["top_candidates"], start=1):
        best = sorted(candidate["classifications"], key=lambda item: item["score_tuple"])[0]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{candidate['source_mode']}`",
                    f"`{candidate['fraction_mode']}`",
                    str(candidate["angle_bias"]),
                    str(candidate["radius_bias"]),
                    f"`{best['quantizer']}`",
                    f"`{best['emitted_254']}`",
                    f"`{best['tp']}`",
                    f"`{best['fp']}`",
                    f"`{best['fn']}`",
                ]
            )
            + " |"
        )
    if report["top_candidates"]:
        best = report["top_candidates"][0]
        lines.extend(["", "## Best Target Details", ""])
        lines.append(
            f"- Best: mode=`{best['source_mode']}`, fraction=`{best['fraction_mode']}`, "
            f"angle_bias=`{best['angle_bias']}`, radius_bias=`{best['radius_bias']}`"
        )
        for x, detail in best["target_details"].items():
            lines.append(
                f"- x={x}: alpha=`{detail['alpha']}`, radius_index=`{detail['radius_index']}`, "
                f"angle_index=`{detail['angle_index']}`, cells=`{detail['cells']}`, "
                f"cell_alphas=`{detail['cell_alphas']}`"
            )
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
                    "fraction_mode": best["fraction_mode"],
                    "angle_bias": best["angle_bias"],
                    "radius_bias": best["radius_bias"],
                    "classification": best_cls,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
