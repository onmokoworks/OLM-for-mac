#!/usr/bin/env python3
"""Record the bounded Mode 3 Gaussian geometry contract.

This audit joins the checked-in Ghidra decomp/assembly with actual-AEX helper
witnesses.  It proves only the call geometry and shape preservation observed
at the recovered helper boundary; it does not implement or select a kernel.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
SWEEP = ROOT / "refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json"
RETURN = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_geometry_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_geometry_20260718.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    returned = json.loads(RETURN.read_text(encoding="utf-8"))

    decomp_anchor = (
        "FUN_181272ec0(local_218,local_200,0x100000000,"
        "(double)(int)param_7 * DAT_18148d670);"
    )
    asm_anchor = "1811510d5  MULSD XMM3,qword ptr [0x18148d670]"
    asm_lines = asm.splitlines()
    callsite_lines = [line for line in asm_lines if "1811510" in line]
    static = {
        "decomp_mode3_call_present": decomp_anchor in decomp,
        "decomp_mode3_call_count": decomp.count(decomp_anchor),
        "decomp_helper": "0x181272ec0",
        "decomp_packed_size_literal": "0x100000000",
        "asm_sigma_load_present": asm_anchor in asm,
        "asm_size_load_present": "1811510dd  MOV R8,0x100000000" in asm,
        "asm_call_present": "181151100  CALL 0x181272ec0" in asm,
        "asm_return_jump_present": "181151105  JMP 0x181150f3d" in asm,
        "callsite_excerpt": callsite_lines,
    }

    cases = sweep["cases"]
    observed = [
        {
            "length": case["length"],
            "expected_sigma_x_f64": case["expected_sigma_x_f64"],
            "observed_sigma_x_f64": case["sigma_x_f64"],
            "observed_size_words": case["size"],
            "status": case["status"],
        }
        for case in cases
    ]
    output = returned["output_capture"]["output_array_after"]["mat"]
    input_shape = returned["execution"]["input_shape"]
    returned_shape = [output["rows"], output["cols"]]
    actual = {
        "sweep_aex_sha256": sweep["aex_sha256"],
        "all_sweep_points_captured": all(case["status"] == "captured" for case in cases),
        "all_sigma_matches": all(case["sigma_matches_expected"] for case in cases),
        "all_sizes_are_0x100000000": all(case["size"] == [0, 1] for case in cases),
        "observed": observed,
        "return_witness_status": returned["status"],
        "return_witness_aex_sha256": returned["execution"]["aex_sha256"],
        "return_input_shape": input_shape,
        "return_output_shape": returned_shape,
        "return_output_type": {
            "channels": output["channels"],
            "depth_code": output["depth_code"],
            "word_count": output["word_count"],
        },
        "return_shape_preserved": returned_shape == input_shape,
    }
    facts = [
        "The recovered Mode 3 caller invokes FUN_181272ec0 once with packed size 0x100000000, decoded by the actual probe as [0, 1].",
        "The same caller multiplies the integer ray length by the .rdata double at 0x18148d670; the checked-in sweep decodes that constant as 0.5.",
        "Actual-AEX helper captures for lengths 1, 2, 5, and 9 all report [0, 1] and sigma equal to length * 0.5.",
        "The actual-AEX caller-return witness preserves a 7x9 CV_32FC1 matrix shape and returns 63 float32 words.",
    ]
    limits = [
        "This proves call geometry and one observed shape-preserving return, not the Gaussian kernel coefficients or accumulation order.",
        "The packed [0, 1] size is recorded as the wrapper's actual captured words; this audit does not reinterpret it as a complete semantic API signature.",
        "No Mode 4 recurrence, boundary policy, quantization rule, or production implementation change is justified.",
    ]
    report = {
        "schema": "olmkirakira-mode3-gaussian-geometry/1",
        "kind": "olmkirakira_mode3_gaussian_geometry_audit",
        "date": "2026-07-18",
        "status": "bounded_geometry_shape_proven",
        "ae_exact_claim": False,
        "production_edit": False,
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": sha256(AEX)},
        "sources": {
            "decomp": {"path": str(DECOMP.relative_to(ROOT)), "sha256": sha256(DECOMP)},
            "asm": {"path": str(ASM.relative_to(ROOT)), "sha256": sha256(ASM)},
            "sweep": {"path": str(SWEEP.relative_to(ROOT)), "sha256": sha256(SWEEP)},
            "return_witness": {"path": str(RETURN.relative_to(ROOT)), "sha256": sha256(RETURN)},
        },
        "static": static,
        "actual_aex": actual,
        "FACT": facts,
        "LIMIT": limits,
    }
    required = [
        static["decomp_mode3_call_present"],
        static["asm_sigma_load_present"],
        static["asm_size_load_present"],
        static["asm_call_present"],
        static["asm_return_jump_present"],
        actual["all_sweep_points_captured"],
        actual["all_sigma_matches"],
        actual["all_sizes_are_0x100000000"],
        actual["return_witness_status"] == "captured",
        actual["return_shape_preserved"],
        actual["return_output_type"]["channels"] == 1,
        actual["return_output_type"]["depth_code"] == 5,
    ]
    if not all(required):
        raise AssertionError(json.dumps(report, indent=2))
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        """# OLMKiraKira Mode 3 Gaussian geometry audit (2026-07-18)

Status: **bounded_geometry_shape_proven**
AE exact: **false**
Production edit: **none**

## Bounded result

The recovered Mode 3 call in `FUN_181150790` passes packed size
`0x100000000` (`[0, 1]` in the actual wrapper capture) to
`FUN_181272ec0`, and derives `sigmaX` as `int(length) * 0.5`. Actual-AEX
helper captures for lengths 1, 2, 5, and 9 report that same size and the
expected sigma. A caller-return witness with a 7x9 `CV_32FC1` input returns a
7x9, 63-word float32 output.

This proves the bounded call geometry and observed shape preservation. It does
not prove Gaussian coefficients, border handling, accumulation order, or any
Mode 4 recurrence. No production source was changed.

## Evidence

- Ghidra decomp: `FUN_181150790` calls `FUN_181272ec0` with
  `0x100000000` and `DAT_18148d670`.
- AEX disassembly: `0x1811510d5` loads the constant at `0x18148d670`,
  `0x1811510dd` loads `0x100000000`, and `0x181151100` calls the Gaussian
  wrapper.
- Actual-AEX sweep: `olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json`.
- Actual-AEX return: `olmkirakira_mode3_gaussian_output_actual_aex_20260713.json`.

## Re-run

`python3 tools/emulation/audit_olmkirakira_mode3_gaussian_geometry_20260718.py`

`python3 tools/emulation/test_olmkirakira_mode3_gaussian_geometry_20260718.py`
""",
        encoding="utf-8",
    )
    print("PASS_OLMKIRAKIRA_MODE3_GAUSSIAN_GEOMETRY_AUDIT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
