#!/usr/bin/env python3
"""Independent empty-path oracle for the grounded c280 classifier 0x5a leaf."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_RDX

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from test_olmsmoother2_case0012_c280_weight42_oracle_20260717 import actual_case  # noqa: E402
from test_olmsmoother2_case0012_ada0_matrix_oracle_20260717 import EXPECTED_AEX_SHA256, fixture  # noqa: E402
from test_smoother2_producer import AEX_PATH  # noqa: E402

ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"
F32_ZERO = "00000000"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def ec40_empty_oracle(row: dict[str, Any]) -> dict[str, Any]:
    require(row["classifier_index"] == 0x5A, "not a 0x5a fixture")
    require(row["c280"]["count"] == 0, "0x5a emitted a polygon")
    require(row["c280"]["vertices"] == [], "0x5a returned unexpected vertices")
    require(row["weight_calls"] == [], "0x5a reached the weight owner despite empty output")
    return {"status": "exact_empty", "polygon_count": 0, "vertex_order": [], "rgba_raw_float_bits": True, "weights_raw_float_bits": True}


def ground() -> dict[str, Any]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    start = asm.find("; === FUN_18000ec40")
    end = asm.find("; ===", start + 8)
    leaf = asm[start:end if end >= 0 else None]
    dstart = decomp.find("// === FUN_18000ec40")
    dend = decomp.find("// ===", dstart + 8)
    dleaf = decomp[dstart:dend if dend >= 0 else None]
    for anchor in ("CALL 0x18000e0e0", "CALL 0x18000dbd0", "CALL 0x18000d230", "JMP 0x18000e430"):
        require(anchor in leaf, f"missing AEX ec40 owner edge {anchor}")
    for anchor in ("FUN_18000e0e0((longlong)param_1,(int *)param_2)", "FUN_18000dbd0((int *)&local_58", "FUN_18000d230(&local_58", "FUN_18000e430(param_1,(int *)param_2"):
        require(anchor in dleaf, f"missing decomp ec40 owner edge {anchor}")
    require("case 0x5a" in decomp and "FUN_18000f4a0" in decomp, "0x5a dispatch family owner missing")
    return {"aex_sha256": EXPECTED_AEX_SHA256, "owner": "FUN_18000ec40@0x18000ec40", "path": ["FUN_18000e0e0@0x18000e0e0", "FUN_18000dbd0@0x18000dbd0", "FUN_18000d230@0x18000d230", "FUN_18000e430@0x18000e430", "FUN_1800104d0@0x1800104d0"], "scalar_contract": "e430/13630 weight path is not entered for either 0x5a fixture"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding = ground()
    source = fixture()
    rows = []
    for raw in (200, 100, 10, 0, 1):
        for gate in (0, 1):
            for multiplier in (0.0, 1.0, 2.0):
                row = actual_case(source, raw, gate, multiplier)
                if row["classifier_index"] == 0x5A:
                    rows.append(row)
    require(len(rows) == 2, f"expected two 0x5a fixtures, found {len(rows)}")
    comparisons = [ec40_empty_oracle(row) for row in rows]
    report = {"verdict": "PASS_EXACT_C280_0X5A_EMPTY_PATH_ORACLE", "scope": "fresh actual AEX c280 over the natural matrix; independent FUN_18000ec40 empty-path oracle for both 0x5a fixtures", "grounding": grounding, "cases_0x5a": rows, "comparisons_0x5a": comparisons, "first_new_owner": None, "claims_not_made": ["No non-empty 0x5a geometry claim", "No Windows/AE execution claim", "No production Mac source or ledger edit"]}
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join(["# OLMSmoother2 case0012 c280 0x5a oracle", "", "## Verdict", "", f"`{report['verdict']}`", "", "Both natural `0x5a` fixtures matched the independently grounded empty path: polygon count zero, no vertex order, no RGBA records, and no raw weights.", "", "No next owner was reached; no production source or ledger was edited.", ""]) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
