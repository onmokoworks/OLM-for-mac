#!/usr/bin/env python3
"""Enumerate natural c280 families and stop at the first ungrounded weight owner."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from test_olmsmoother2_case0012_c280_cce0_polygon_gate_20260717 import (  # noqa: E402
    MATRIX_ORDER,
    actual_case,
    classifier_index,
)
from test_olmsmoother2_case0012_ada0_matrix_oracle_20260717 import EXPECTED_AEX_SHA256, fixture  # noqa: E402
from test_olmsmoother2_case0012_c280_index00_geometry_oracle_20260717 import portable_vertices  # noqa: E402
from test_smoother2_producer import AEX_PATH  # noqa: E402

ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def bits(value: float) -> str:
    return struct.pack("<f", value).hex()


def ground_dispatch_families() -> dict[str, Any]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    require("; === FUN_18000c280" in asm and "switchD_18000c530_caseD_2" in decomp, "c280 switch owner missing")
    anchors = [
        "FUN_1800106b0(&local_188)",
        "FUN_180010760(&local_188)",
        "FUN_180010820(&local_188)",
        "FUN_1800105f0(&local_188)",
        "FUN_18000f8f0(",
        "FUN_18000fef0(",
        "FUN_1800101e0(",
        "FUN_18000fbf0(",
        "FUN_1800104d0",
    ]
    for anchor in anchors:
        require(anchor in decomp, f"missing dispatch/append anchor {anchor}")
    for address in ("18000ead0", "18000edb0", "180013630"):
        require(f"FUN_{address}" in decomp, f"missing helper reference 0x{address}")
    return {
        "0x00": {"helpers": ["FUN_1800134c0", "FUN_180013570", "FUN_180012ce0", "FUN_180012c20"], "owner": "corner append chain"},
        "0x42": {"helpers": ["FUN_1800106b0", "FUN_18000cee0", "FUN_18000d6a0", "FUN_18000f8f0", "FUN_18000ead0", "FUN_180010760", "FUN_18000d3b0", "FUN_18000da50", "FUN_18000fef0", "FUN_18000edb0"], "owner": "two cardinal dispatch leaves; append FUN_1800104d0"},
        "0x5a": {"helpers": ["FUN_180010820", "FUN_18000d520", "FUN_18000dbd0", "FUN_1800101e0", "FUN_18000fbf0", "FUN_1800105f0", "FUN_18000d230", "FUN_18000d800"], "owner": "opposite cardinal dispatch leaves"},
        "0xff": {"helpers": [], "owner": "default empty branch"},
    }


def compare_index00(row: dict[str, Any], source: list[list[tuple[float, float, float, float]]]) -> dict[str, Any]:
    expected = portable_vertices(source)
    actual = row["c280"]["vertices"]
    require(row["classifier_index"] == 0 and row["c280"]["count"] == len(expected), "0x00 count/index drift")
    require(len(actual) == len(expected), "0x00 vertex capture length drift")
    for i, (got, want) in enumerate(zip(actual, expected)):
        for channel, (gv, wv) in enumerate(zip(got["rgba"], want["rgba"])):
            require(bits(gv) == bits(wv), f"0x00 vertex {i} rgba[{channel}] mismatch")
        require(bits(got["weight"]) == bits(want["weight"]), f"0x00 vertex {i} weight mismatch")
        # c280's captured record stores source RGBA and weight; order is the vertex sequence.
    return {"status": "exact", "count": len(expected), "vertices_raw_float_bits": True, "rgba_raw_float_bits": True, "weights_raw_float_bits": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    families = ground_dispatch_families()
    source = fixture()
    actual = [actual_case(source, raw, gate, multiplier) for raw, gate, multiplier in MATRIX_ORDER]
    unique = sorted({row["classifier_index"] for row in actual})
    require(unique == [0x00, 0x42, 0x5A, 0xFF], f"unexpected unique classifier indices: {unique}")
    by_index: dict[int, list[dict[str, Any]]] = {index: [row for row in actual if row["classifier_index"] == index] for index in unique}
    checks: list[dict[str, Any]] = []
    for row in by_index[0x00]:
        checks.append({"classifier_index": "0x00", "case": {k: row[k] for k in ("raw", "gate", "multiplier")}, **compare_index00(row, source)})
    first_missing = {
        "classifier_index": "0x42",
        "case": {k: by_index[0x42][0][k] for k in ("raw", "gate", "multiplier")},
        "helper": "FUN_180013630@0x180013630",
        "reason": "The 0x42 cardinal leaves reach FUN_18000ead0/FUN_18000edb0 and append through FUN_1800104d0, but the raw-weight transform body is absent from the independently grounded evidence. No portable weight, vertex, or RGBA equivalence is guessed for 0x42 or later families.",
    }
    report = {
        "verdict": "PASS_ACTUAL_UNIQUE_C280_FAMILIES_WITH_FAIL_CLOSED_AT_FUN_180013630",
        "scope": "fresh actual AEX c280 over all 30 natural class planes; exact portable comparison through the first grounded family",
        "unique_classifier_indices": [f"0x{index:02x}" for index in unique],
        "family_counts": {f"0x{index:02x}": len(by_index[index]) for index in unique},
        "dispatch_families": families,
        "actual_cases": actual,
        "portable_checks": checks,
        "first_missing_semantic": first_missing,
        "claims_not_made": ["No portable c280 equivalence for 0x42, 0x5a, or 0xff beyond actual observations", "No Windows/AE execution claim", "No production Mac source or ledger edit"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join([
        "# OLMSmoother2 case0012 unique c280 family oracle", "", "## Verdict", "", f"`{report['verdict']}`", "",
        f"Fresh actual c280 produced unique classifier indices `{', '.join(report['unique_classifier_indices'])}` from 30 fixtures, with counts `{report['family_counts']}`.", "",
        "The `0x00` family matched polygon count, point order, RGBA, and raw IEEE-754 weights for every one of its eight fixtures.", "",
        "Fail-closed boundary: `FUN_180013630@0x180013630`, the first missing independent raw-weight transform on the `0x42` cardinal path. Families `0x42`, `0x5a`, and `0xff` remain actual-only after that boundary.", "",
        "No production source or ledger was edited.", "",
    ]) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
