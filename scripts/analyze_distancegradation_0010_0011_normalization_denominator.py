#!/usr/bin/env python3
"""Audit OLMDistanceGradation 0010/0011 normalization-denominator deltas."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md"


WITNESSES = [
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [6, 40],
        "mode": "outside",
        "raw_distance": 41.0,
        "mac_field_x": 0.9002838730812073,
        "normalization_denominator_kind": "actual_raw_max",
        "ui_threshold": 82.0,
        "windows_field_word_required": 29500,
        "windows_store_a": 3268,
    },
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [901, 394],
        "mode": "inside",
        "raw_distance": 44.0113639831543,
        "mac_field_x": 0.6985930800437927,
        "normalization_denominator_kind": "ui_threshold",
        "ui_threshold": 63.0,
        "windows_field_word_required": 22892,
        "windows_store_a": 9876,
    },
    {
        "case_id": "olmdistancegradation_extended__case_0011",
        "xy": [915, 392],
        "mode": "inside",
        "raw_distance": 46.81879806518555,
        "mac_field_x": 0.1345367729663849,
        "normalization_denominator_kind": "ui_threshold",
        "ui_threshold": 348.0,
        "windows_field_word_required": 4409,
        "windows_store_a": 28359,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def analyze(row: dict[str, Any]) -> dict[str, Any]:
    required_x = row["windows_field_word_required"] / 32768.0
    mac_denominator = row["raw_distance"] / row["mac_field_x"] if row["mac_field_x"] else None
    required_denominator = row["raw_distance"] / required_x if required_x else None
    raw_required_if_mac_denominator_fixed = required_x * mac_denominator if mac_denominator else None
    raw_required_if_ui_threshold_fixed = required_x * row["ui_threshold"]
    return {
        **row,
        "mac_field_word_float": row["mac_field_x"] * 32768.0,
        "windows_field_x_required": required_x,
        "mac_denominator_implied": mac_denominator,
        "denominator_required_if_raw_fixed": required_denominator,
        "denominator_delta_required_minus_mac": (
            required_denominator - mac_denominator
            if required_denominator is not None and mac_denominator is not None
            else None
        ),
        "raw_required_if_mac_denominator_fixed": raw_required_if_mac_denominator_fixed,
        "raw_delta_required_minus_mac": (
            raw_required_if_mac_denominator_fixed - row["raw_distance"]
            if raw_required_if_mac_denominator_fixed is not None
            else None
        ),
        "raw_required_if_ui_threshold_fixed": raw_required_if_ui_threshold_fixed,
        "raw_delta_if_ui_threshold_fixed": raw_required_if_ui_threshold_fixed - row["raw_distance"],
    }


def decision(rows: list[dict[str, Any]]) -> str:
    kinds = {row["normalization_denominator_kind"] for row in rows}
    if "actual_raw_max" in kinds and "ui_threshold" in kinds:
        return "mixed-actual-max-and-threshold-half-boundary"
    return "single-denominator-family"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation 0010/0011 normalization denominator audit - 2026-07-09",
        "",
        "This audit quantifies how far the current Mac raw distance or normalization",
        "denominator must move to reproduce the Windows-required PF16 field words.",
        "It is not an implementation patch.",
        "",
        f"- Decision: `{report['decision']}`",
        "",
        "| Case | XY | Mode | Denom kind | Mac denom | Required denom | Denom delta | Raw delta if denom fixed |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report["witnesses"]:
        xy = f"({row['xy'][0]},{row['xy'][1]})"
        lines.append(
            f"| `{row['case_id']}` | `{xy}` | {row['mode']} | "
            f"{row['normalization_denominator_kind']} | "
            f"{row['mac_denominator_implied']:.12g} | "
            f"{row['denominator_required_if_raw_fixed']:.12g} | "
            f"{row['denominator_delta_required_minus_mac']:.12g} | "
            f"{row['raw_delta_required_minus_mac']:.12g} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- `(6,40)` is not threshold-normalized by `82`; it is normalized by the outside field's actual max (`~45.54119`).",
            "- `(901,394)` and `(915,392)` are threshold-limited inside-field witnesses.",
            "- All three are half-boundary scale problems, but they are not a single global denominator constant.",
            "- The next local proof should inspect the AEX/OpenCV field preparation path that produces the stored field world: actual max measurement, threshold clamp precision, and PF16 field-world packing.",
            "- Do not change final output rounding from this audit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    witnesses = [analyze(row) for row in WITNESSES]
    report = {
        "kind": "olmdistancegradation_0010_0011_normalization_denominator_audit",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": decision(witnesses),
        "witnesses": witnesses,
        "source_reports": [
            "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
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
