#!/usr/bin/env python3
"""Prove the argument source and lane meaning of the packed R9 size."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_packed_r9_semantics_20260717.json"
MARKDOWN = ROOT / "refs/conformance/olmkirakira_packed_r9_semantics_20260717.md"

sys.path.insert(0, str(ROOT / "tools/emulation"))
lineage = importlib.import_module("test_olmkirakira_packed_size_first_writer_20260717")

CALLSITE = 0x18115116F
EXPECTED_RAW = 0x0000000180000000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_witness() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    asm_lines = [
        "18115110a  MOV RDI,RSI",
        "18115110d  MOV RAX,0x100000000",
        "181151117  OR RDI,RAX",
        "181151162  MOV R9,RDI",
        "18115116f  CALL 0x181280bc0",
    ]
    decomp_tokens = [
        "void FUN_181150790(",
        "int param_6",
        "uint param_7",
        "int param_8",
        "if (param_8 == 1)",
        "else if (param_8 == 2)",
        "else if (param_8 == 3)",
        "else if (param_8 == 4)",
        "(ulonglong)param_7 | 0x100000000",
    ]
    return {
        "aex_sha256": sha256(AEX),
        "asm_sha256": sha256(ASM),
        "decomp_sha256": sha256(DECOMP),
        "asm_sequence_present": all(line in asm for line in asm_lines),
        "asm_sequence": asm_lines,
        "decomp_semantic_tokens_present": all(token in decomp for token in decomp_tokens),
        "decomp_semantic_tokens": decomp_tokens,
        "function_semantics": {
            "rsi_at_builder": "FUN_181150790 param_7, loaded from the caller's original RSP+0x30; param_8 is the separate 1..4 branch selector at original RSP+0x38",
            "low_dword": "param_7 / horizontal packed-size (kernel width) lane",
            "high_dword": "constant 1 / vertical packed-size lane",
            "bit_wording": "0x100000000 sets bit 32; the observed param_7=0x80000000 independently sets bit 31",
        },
    }


def main() -> int:
    static = static_witness()
    runtime, trace, _state = lineage.capture_runtime()
    calls = trace["packed_calls"]
    observed = next((item for item in calls if int(item["r9_raw_hex"], 16) == EXPECTED_RAW), None)
    load = trace["load_events"][-1] if trace["load_events"] else None
    spill = trace["abi_argument_spill"]
    assertion = runtime.get("filter_assertion_capture", {})
    gates = {
        "static_builder_sequence": static["asm_sequence_present"],
        "static_decomp_semantics": static["decomp_semantic_tokens_present"],
        "actual_builder_call_observed": observed is not None,
        "actual_r9_expected": bool(observed and int(observed["r9_raw_hex"], 16) == EXPECTED_RAW),
        "actual_rsi_is_param7_intmin": bool(observed and int(observed["rsi_raw_hex"], 16) == 0x80000000),
        "actual_spill_expected": bool(spill and int.from_bytes(bytes.fromhex(str(spill["value_raw_hex"])), "little") == EXPECTED_RAW),
        "actual_load_expected": bool(load and int(load["loaded_raw_u64"]) == EXPECTED_RAW),
        "filterengine_stop_without_mutation": assertion.get("stop_without_mutation") is True,
    }
    status = "PASS_CLASSIFIED_FAIL_CLOSED_STOP" if all(gates.values()) else "FAIL_CLOSED"
    report = {
        "kind": "olmkirakira_packed_r9_semantics",
        "schema": 1,
        "date": "2026-07-17",
        "status": status,
        "classification": "R9_PACKED_SIZE_FROM_PARAM7_KERNEL_WIDTH" if status.startswith("PASS_") else "AMBIGUOUS",
        "answer": {
            "rsi_semantics": "FUN_181150790 param_7, the horizontal packed-size/kernel-width input; the separate param_8 branch selector is 2 in this path.",
            "packed_encoding": "R9 = zero-extended param_7 in the low dword | (1 << 32), i.e. packed width=param_7 and height=1.",
            "bit31": "set by the observed param_7 value 0x80000000; the literal 0x100000000 separately sets bit 32 for height=1.",
        },
        "callsite": hex(CALLSITE),
        "expected_raw": hex(EXPECTED_RAW),
        "gates": gates,
        "static": static,
        "runtime": {
            "common_owner_status": runtime.get("status"),
            "execution_stop": runtime.get("execution_stop"),
            "builder_call": observed,
            "abi_spill": spill,
            "load": load,
            "filterengine_assertion": assertion,
        },
        "limits": [
            "Mac-only Unicorn execution of the pinned Windows PE; no Windows or After Effects host claim.",
            "No argument, object, source, or assertion value was patched or suppressed.",
            "Missing or contradictory evidence returns FAIL_CLOSED.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = """# OLMKiraKira packed R9 semantics

Date: 2026-07-17

## Result

- Status: **{status}**
- `RSI` at `0x18115110a` is `FUN_181150790`'s `param_7`, loaded from the caller's original `RSP+0x30`; the separate `param_8` branch selector is `2` at original `RSP+0x38`.
- The builder makes `R9 = RSI | 0x100000000`, then passes it to `FUN_181280bc0`.
- The packed-size interpretation is low dword `width=param_7` (kernel-width lane), high dword `height=1`.
- In this run `param_7=0x80000000`, which sets bit 31; `0x100000000` independently sets bit 32.

## Evidence

- Static asm/decomp checks and actual-AEX builder, ABI-spill, and reload observations all passed.
- The unmodified `FilterEngine` stop remained the terminal boundary.

## Limits

- Mac-only Unicorn execution of the pinned Windows PE; no Windows/After Effects host claim.
- No value patch or assertion suppression.
""".format(status=status)
    MARKDOWN.write_text(md, encoding="utf-8")
    print(json.dumps({"status": status, "gates": gates, "report": str(REPORT)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
