#!/usr/bin/env python3
"""Probe final inverse-sample float sequencing for RadialBlur Zoom case_0009.

This reads the quantize-locus report and replays only the final alpha bilinear
sum under several local arithmetic sequences. It deliberately does not render
images or change the implementation. The goal is to test whether weight/sum
precision alone can explain the Windows top-row alpha=254 set `{6,7,12}`.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCUS_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_quantize_locus_20260709.json"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md"
TARGET_ALPHA254 = {6, 7, 12}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locus-json", type=Path, default=DEFAULT_LOCUS_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def q_epsilon(alpha: float) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0 + 1.0e-4))))


def q_truncate(alpha: float) -> int:
    return int(max(0, min(255, math.floor(alpha * 255.0))))


def f32_mul(a: float, b: float) -> float:
    return f32(f32(a) * f32(b))


def f32_add(a: float, b: float) -> float:
    return f32(f32(a) + f32(b))


def weights_from(radius_index: float, angle_index: float) -> dict[str, Any]:
    xi = math.floor(radius_index)
    yi = math.floor(angle_index)
    fx = f32(radius_index - float(xi))
    fy = f32(angle_index - float(yi))
    one_minus_fx = f32(1.0 - fx)
    one_minus_fy = f32(1.0 - fy)
    current_double = [
        float(one_minus_fx) * float(one_minus_fy),
        float(fx) * float(one_minus_fy),
        float(one_minus_fx) * float(fy),
        float(fx) * float(fy),
    ]
    product_f32 = [
        f32_mul(one_minus_fx, one_minus_fy),
        f32_mul(fx, one_minus_fy),
        f32_mul(one_minus_fx, fy),
        f32_mul(fx, fy),
    ]
    return {
        "xi": int(xi),
        "yi": int(yi),
        "fx": fx,
        "fy": fy,
        "current_double": current_double,
        "product_f32": product_f32,
    }


def alpha_sequences(cell_alpha: list[float], weights: dict[str, Any]) -> dict[str, float]:
    cd = weights["current_double"]
    pf = weights["product_f32"]
    current_double = sum(float(a) * float(w) for a, w in zip(cell_alpha, cd))
    current_terms_f32_sum_double = sum(float(f32_mul(a, w)) for a, w in zip(cell_alpha, pf))
    sequential = 0.0
    for a, w in zip(cell_alpha, pf):
        sequential = f32_add(sequential, f32_mul(a, w))
    grouped = f32_add(
        f32_add(f32_mul(cell_alpha[0], pf[0]), f32_mul(cell_alpha[1], pf[1])),
        f32_add(f32_mul(cell_alpha[2], pf[2]), f32_mul(cell_alpha[3], pf[3])),
    )
    return {
        "current_double_sum": current_double,
        "f32_products_sum_double": current_terms_f32_sum_double,
        "f32_sequential_sum": sequential,
        "f32_grouped_sum": grouped,
        "weight_sum_double": sum(cd),
        "weight_sum_f32_products_double": sum(pf),
        "weight_sum_f32_sequential": alpha_sequences_ones(pf),
    }


def alpha_sequences_ones(weights: list[float]) -> float:
    out = 0.0
    for weight in weights:
        out = f32_add(out, weight)
    return out


def classify(points: list[dict[str, Any]], sequence_name: str, quantizer: str) -> dict[str, Any]:
    emitted = set()
    qfunc = q_epsilon if quantizer == "epsilon" else q_truncate
    for point in points:
        q = qfunc(point["sequences"][sequence_name])
        if q == 254:
            emitted.add(point["x"])
    return {
        "sequence": sequence_name,
        "quantizer": quantizer,
        "emitted_254": sorted(emitted),
        "tp": sorted(emitted & TARGET_ALPHA254),
        "fp": sorted(emitted - TARGET_ALPHA254),
        "fn": sorted(TARGET_ALPHA254 - emitted),
    }


def build_report(locus: dict[str, Any], locus_path: Path) -> dict[str, Any]:
    polar_rows = locus["variants"]["polar_alpha"]["row"]
    points: list[dict[str, Any]] = []
    for row in polar_rows:
        cell_alpha = row.get("cell_alpha")
        if not isinstance(cell_alpha, list) or len(cell_alpha) != 4:
            continue
        radius_index = float(row["radius_index"])
        angle_index = float(row["angle_index"])
        weights = weights_from(radius_index, angle_index)
        sequences = alpha_sequences([float(v) for v in cell_alpha], weights)
        points.append(
            {
                "x": int(row["x"]),
                "reference": row["reference"],
                "polar_alpha_candidate": row["candidate"],
                "radius_index": radius_index,
                "angle_index": angle_index,
                "xi": weights["xi"],
                "yi": weights["yi"],
                "fx": weights["fx"],
                "fy": weights["fy"],
                "cell_alpha": [float(v) for v in cell_alpha],
                "weights_current_double": weights["current_double"],
                "weights_product_f32": weights["product_f32"],
                "sequences": sequences,
                "q_epsilon": {name: q_epsilon(value) for name, value in sequences.items()},
                "q_truncate": {name: q_truncate(value) for name, value in sequences.items()},
            }
        )

    sequence_names = [
        "current_double_sum",
        "f32_products_sum_double",
        "f32_sequential_sum",
        "f32_grouped_sum",
        "weight_sum_double",
        "weight_sum_f32_products_double",
        "weight_sum_f32_sequential",
    ]
    classifications = [
        classify(points, name, quantizer)
        for name in sequence_names
        for quantizer in ("epsilon", "truncate")
    ]
    return {
        "kind": "olmradialblur_zoom_case0009_final_sample_float_sequence",
        "schema": 1,
        "source_locus": str(locus_path),
        "case_id": locus["case_id"],
        "target_alpha254": sorted(TARGET_ALPHA254),
        "points": points,
        "classifications": classifications,
        "interpretation": (
            "All epsilon-quantized final-sample arithmetic variants miss the Windows alpha=254 "
            "set, including the all-one x=7 spoiler. Truncate-only variants either miss target "
            "pixels or add broad false positives. Therefore weight/sum precision alone is "
            "rejected; the live lane must move to final-polar cell selection, coordinate "
            "generation, or source-plane population."
        ),
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom Final-Sample Float Sequence Probe",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Target Windows alpha=254 x positions: `{report['target_alpha254']}`",
        "",
        "## Classification",
        "",
        "| Sequence | Quantizer | emitted 254 | TP | FP | FN |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["classifications"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['sequence']}`",
                    f"`{item['quantizer']}`",
                    f"`{item['emitted_254']}`",
                    f"`{item['tp']}`",
                    f"`{item['fp']}`",
                    f"`{item['fn']}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Target Points", ""])
    lines.append("| x | ref | cell_alpha | fx | fy | current alpha | f32 seq alpha | eps q | trunc q |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for point in report["points"]:
        if point["x"] not in TARGET_ALPHA254:
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(point["x"]),
                    f"`{point['reference']}`",
                    f"`{point['cell_alpha']}`",
                    f"`{point['fx']}`",
                    f"`{point['fy']}`",
                    f"`{point['sequences']['current_double_sum']}`",
                    f"`{point['sequences']['f32_sequential_sum']}`",
                    f"`{point['q_epsilon']['f32_sequential_sum']}`",
                    f"`{point['q_truncate']['f32_sequential_sum']}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    locus = json.loads(args.locus_json.read_text(encoding="utf-8"))
    report = build_report(locus, args.locus_json)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    for item in report["classifications"]:
        if item["sequence"] == "f32_sequential_sum" and item["quantizer"] == "epsilon":
            print(f"f32_sequential_epsilon={item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
