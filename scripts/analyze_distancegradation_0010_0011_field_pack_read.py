#!/usr/bin/env python3
"""Classify the OLMDistanceGradation 0010/0011 PF16 field-pack/read boundary."""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md"


WITNESSES = [
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [6, 40],
        "mode": "outside",
        "raw_distance": 41.0,
        "threshold": 82.0,
        "mac_field_x": 0.9002838730812073,
        "mac_out_a": 0.09971612691879272,
        "mac_store_a": 3267,
        "windows_xmm2_alpha": 0.0997314,
        "windows_store_a": 3268,
    },
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [901, 394],
        "mode": "inside",
        "raw_distance": 44.0113639831543,
        "threshold": 63.0,
        "mac_field_x": 0.6985930800437927,
        "mac_out_a": 0.3014069199562073,
        "mac_store_a": 9877,
        "windows_xmm2_alpha": 0.301392,
        "windows_store_a": 9876,
    },
    {
        "case_id": "olmdistancegradation_extended__case_0011",
        "xy": [915, 392],
        "mode": "inside",
        "raw_distance": 46.81879806518555,
        "threshold": 348.0,
        "mac_field_x": 0.1345367729663849,
        "mac_out_a": 0.8654632570336151,
        "mac_store_a": 28360,
        "windows_xmm2_alpha": None,
        "windows_store_a": 28359,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def store_from_field_word(field_word: int) -> int:
    field_x = field_word / 32768.0
    # The active cases are no-background Gradation Color with default invert
    # shape: output alpha is 1 - field_x, then the AEX writer truncates after
    # multiplying by 32768.
    return int((1.0 - field_x) * 32768.0)


def analyze_witness(row: dict[str, Any]) -> dict[str, Any]:
    mac_field_word_float = row["mac_field_x"] * 32768.0
    windows_field_word_required = 32768 - int(row["windows_store_a"])
    windows_field_x_required = windows_field_word_required / 32768.0
    denom_required = (
        row["raw_distance"] / windows_field_x_required
        if windows_field_x_required != 0.0
        else None
    )
    models = {}
    for name, field_word in {
        "floor_mac_field_word": math.floor(mac_field_word_float),
        "ceil_mac_field_word": math.ceil(mac_field_word_float),
        "round_half_up_mac_field_word": math.floor(mac_field_word_float + 0.5),
        "python_round_mac_field_word": round(mac_field_word_float),
    }.items():
        models[name] = {
            "field_word": int(field_word),
            "store_a": store_from_field_word(int(field_word)),
            "matches_windows_store": store_from_field_word(int(field_word)) == row["windows_store_a"],
        }
    return {
        **row,
        "mac_field_word_float": mac_field_word_float,
        "mac_field_word_fraction": mac_field_word_float - math.floor(mac_field_word_float),
        "windows_field_word_required": windows_field_word_required,
        "windows_field_x_required": windows_field_x_required,
        "field_word_delta_required_minus_mac_float": windows_field_word_required - mac_field_word_float,
        "denom_required_to_match_windows": denom_required,
        "models": models,
    }


def decision(rows: list[dict[str, Any]]) -> str:
    model_names = list(rows[0]["models"])
    matching_all = [
        name
        for name in model_names
        if all(row["models"][name]["matches_windows_store"] for row in rows)
    ]
    if matching_all:
        return "single-field-pack-model-matches-all"
    if any(any(model["matches_windows_store"] for model in row["models"].values()) for row in rows):
        return "field-pack-alone-insufficient-sign-flipped-boundary"
    return "field-pack-models-all-rejected"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation 0010/0011 field-pack/read audit - 2026-07-09",
        "",
        "This is a local arithmetic audit, not an implementation change. It checks",
        "whether the new Windows PF16 store words can be explained by simply packing",
        "the current Mac float field into a PF16 field world before `FUN_181170480`",
        "reads it.",
        "",
        f"- Decision: `{report['decision']}`",
        "",
        "| Case | XY | Mac field*32768 | Required field word | Delta | floor | ceil | round-half-up |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["witnesses"]:
        xy = f"({row['xy'][0]},{row['xy'][1]})"
        models = row["models"]
        def mark(name: str) -> str:
            model = models[name]
            suffix = "*" if model["matches_windows_store"] else ""
            return f"{model['store_a']}{suffix}"
        lines.append(
            f"| `{row['case_id']}` | `{xy}` | {row['mac_field_word_float']:.9f} | "
            f"{row['windows_field_word_required']} | "
            f"{row['field_word_delta_required_minus_mac_float']:.9f} | "
            f"{mark('floor_mac_field_word')} | {mark('ceil_mac_field_word')} | "
            f"{mark('round_half_up_mac_field_word')} |"
        )
    lines.extend(
        [
            "",
            "`*` marks a model that reproduces the Windows store word for that single witness.",
            "",
            "## Reading",
            "",
            "- Windows `FUN_181170480` reads a PF16 field-world word and multiplies by `1/32768`; the current Mac port reads `std::vector<float> df.x` directly.",
            "- A PF16 field-world read is therefore a plausible missing boundary, but no single `floor`/`ceil`/`round` pack rule explains all sign-flipped witnesses.",
            "- The remaining discriminator is a raw-distance / normalization-denominator / OpenCV field-pack boundary, not final `clamp16()` alone.",
            "- Do not change global output rounding from this audit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    witnesses = [analyze_witness(row) for row in WITNESSES]
    report = {
        "kind": "olmdistancegradation_0010_0011_field_pack_read_audit",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": decision(witnesses),
        "witnesses": witnesses,
        "source_reports": [
            "refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            "decomp/DistanceGradation.aex.c.txt FUN_181170480",
            "disasm/DistanceGradation.aex.asm.txt FUN_181170480",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
