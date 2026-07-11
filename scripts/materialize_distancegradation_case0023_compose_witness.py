#!/usr/bin/env python3
"""Materialize OLMDistanceGradation case_0023 compose/writeback witness facts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EMU_DIR = ROOT / "tools" / "emulation"
sys.path.insert(0, str(EMU_DIR))

import test_dg_compose as dg_compose  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


def build_report() -> dict[str, Any]:
    leaf = dg_compose.run_leaf_check()
    triplet_raw = dg_compose.run_triplet_check()
    triplet = []
    for xy, row in sorted(triplet_raw.items()):
        triplet.append(
            {
                "xy": list(xy),
                "field_x": row["field_x"],
                "raw_words_agrb": list(row["raw_words_agrb"]),
                "raw_rgba": list(row["raw_rgba"]),
                "promoted_rgba": list(row["promoted_rgba"]),
                "windows_final_rgba16": list(row["windows_final_rgba16"]),
                "match_promoted": row["match_promoted"],
            }
        )
    all_triplet_match = all(row["match_promoted"] for row in triplet)
    leaf_ok = leaf["use_bg_on"]["match"] and leaf["use_bg_off"]["match"]
    return {
        "kind": "olmdistancegradation_case0023_compose_witness",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "compose-writeback-triplet-binary-grounded" if leaf_ok and all_triplet_match else "failed",
        "source": "tools/emulation/test_dg_compose.py",
        "aex": str(dg_compose.AEX_PATH.relative_to(ROOT)),
        "function": "DistanceGradation.aex FUN_181170480",
        "case_id": "olmdistancegradation_extended__case_0023",
        "leaf_check": jsonable(leaf),
        "triplet": triplet,
        "promotion_rule": "trunc(half_word / 32768.0 * 65535.0)",
        "safe_claim": (
            "For the case_0023 threshold triplet, executing the Windows AEX compose/writeback callback locally "
            "maps injected field_x values to the recorded runtime RGBA16 words for this witness. The 2026-07-07 "
            "reference export audit supersedes treating those recorded words as the current PNG reference at every "
            "point, so this witness is a field-to-color mapping check, not current AE exact evidence."
        ),
        "limitations": [
            "field_x values are injected from already-recorded threshold-side field witnesses; this does not re-prove field generation",
            "the recorded triplet words are not authoritative over the 2026-07-07 current Windows Software PNG recapture",
            "promotion rule is empirically grounded on this triplet, not all possible intermediate values",
            "8bpc sibling and non-linear interpolation branches are not covered by this witness",
            "this is binary-grounded local emulation evidence, not Mac AE exact completion",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    leaf = report["leaf_check"]
    lines = [
        f"# OLMDistanceGradation case_0023 Compose Witness - {report['materialized_at'][:10]}",
        "",
        f"- Status: `{report['status']}`",
        f"- Source: `{report['source']}`",
        f"- AEX: `{report['aex']}`",
        f"- Function: `{report['function']}`",
        f"- Case: `{report['case_id']}`",
        f"- Promotion rule: `{report['promotion_rule']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## Leaf Check",
        "",
        f"- use_bg=1: got `{leaf['use_bg_on']['got']}` expected `{leaf['use_bg_on']['expected']}` match `{leaf['use_bg_on']['match']}`",
        f"- use_bg=0: got `{leaf['use_bg_off']['got']}` expected `{leaf['use_bg_off']['expected']}` match `{leaf['use_bg_off']['match']}`",
        "",
        "## Triplet",
        "",
        "| XY | field_x | raw AGRB | promoted RGBA16 | recorded RGBA16 | match |",
        "| --- | ---: | --- | --- | --- | ---: |",
    ]
    for row in report["triplet"]:
        xy = row["xy"]
        lines.append(
            f"| `({xy[0]},{xy[1]})` | `{row['field_x']}` | `{row['raw_words_agrb']}` | "
            f"`{row['promoted_rgba']}` | `{row['windows_final_rgba16']}` | `{row['match_promoted']}` |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report()
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_compose_witness_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_compose_witness_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_md(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    if report["status"] != "compose-writeback-triplet-binary-grounded":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
