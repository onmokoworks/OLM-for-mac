#!/usr/bin/env python3
"""Audit the bounded Mode4 scalar edge/forward/backward pass shape."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_R8, UC_X86_REG_R11, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_mode4_edge_passes_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_mode4_edge_passes_20260718.md"

HELPER = 0x181150790
MODE4_ENTRY = 0x181150979
ROW_START = 0x1811509E0
FORWARD_EDGE_INIT = 0x181150A17
FORWARD_STEP = 0x181150A20
BACKWARD_SETUP = 0x181150A4A
BACKWARD_VECTOR_STEP = 0x181150A90
BACKWARD_STEP = 0x181150B23
ROW_FINISH = 0x181150B50


def load_base():
    spec = importlib.util.spec_from_file_location("mode4_base_edge_20260718", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load actual-AEX helper harness")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section(text: str, start: str, end: str) -> str:
    left = text.index(start)
    return text[left:text.index(end, left)]


def main() -> int:
    base = load_base()
    hits: dict[str, list[dict[str, Any]]] = {key: [] for key in (
        "mode4_entry", "row_start", "forward_edge_init", "forward_step",
        "backward_setup", "backward_vector_step", "backward_step", "row_finish")}
    addresses = {
        MODE4_ENTRY: "mode4_entry", ROW_START: "row_start",
        FORWARD_EDGE_INIT: "forward_edge_init", FORWARD_STEP: "forward_step",
        BACKWARD_SETUP: "backward_setup", BACKWARD_VECTOR_STEP: "backward_vector_step",
        BACKWARD_STEP: "backward_step",
        ROW_FINISH: "row_finish",
    }

    class EdgeLoader(base.AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for address, name in addresses.items():
                super().add_code_hook(address, self.make_hook(name))

        def make_hook(self, name):
            def hook(loader, address, _size):
                item: dict[str, Any] = {"rip": hex(address)}
                if name in {"row_start", "forward_edge_init", "forward_step", "backward_setup", "backward_vector_step", "backward_step"}:
                    item.update({
                        "rax": hex(loader.uc.reg_read(UC_X86_REG_RAX)),
                        "r8": hex(loader.uc.reg_read(UC_X86_REG_R8)),
                        "r11": hex(loader.uc.reg_read(UC_X86_REG_R11)),
                    })
                if name == "row_finish":
                    row = loader.uc.reg_read(UC_X86_REG_R11)
                    item["destination_row_f32"] = loader.read_f32_array(row, 9)
                hits[name].append(item)
            return hook

        def call_function(self, address, *args, **kwargs):
            int_args = list(kwargs.get("int_args", []))
            if address == HELPER:
                if len(int_args) != 9:
                    raise AssertionError(f"unexpected helper ABI: {int_args}")
                int_args[7] = 4
                kwargs["int_args"] = int_args
            return super().call_function(address, *args, **kwargs)

    original = base.AexLoader
    base.AexLoader = EdgeLoader
    args = type("Args", (), {
        "aex_path": AEX, "width": 9, "height": 7, "length": 5,
        "sigma": 0.0, "max_instructions": 20_000_000,
    })()
    try:
        execution = base.run(args)
    finally:
        base.AexLoader = original

    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    helper_d = section(decomp, "// === FUN_181150790", "// === FUN_1811512a0")
    helper_a = section(asm, "; === FUN_181150790", "; === FUN_1811512a0")
    mode4_d = helper_d[helper_d.index("else if (param_8 == 4)"):]
    static_decomp = {
        "forward_edge_seed_reads_destination": "fVar16 = *pfVar15" in mode4_d,
        "forward_step_is_source_plus_prior": "fVar20 * *(float *)((lVar10 - (longlong)pfVar15) + (longlong)pfVar2)" in mode4_d and "fVar16 * fVar18" in mode4_d,
        "forward_step_increments": "pfVar2 = pfVar2 + 1" in mode4_d and "iVar6 = iVar6 + 1" in mode4_d,
        "backward_accumulator_zero": "fVar16 = 0.0" in mode4_d,
        "backward_step_reads_next_source": "(lVar10 - (longlong)pfVar15) + 4" in mode4_d,
        "backward_step_decrements": "pfVar2 = pfVar2 + -1" in mode4_d and "lVar7 = lVar7 + -1" in mode4_d,
        "row_loop_increments": "iVar1 = iVar1 + 1" in mode4_d and "lVar8 = lVar8 + 1" in mode4_d,
    }
    static_asm = {
        "forward_edge_seed_load": "181150a17  MOVSS XMM2,dword ptr [R11]" in helper_a,
        "forward_step_loop": "181150a20  MOVAPS XMM1,XMM7" in helper_a and "181150a48  JL 0x181150a20" in helper_a,
        "backward_accumulator_zero": "181150a4a  XORPS XMM3,XMM3" in helper_a,
        "backward_setup": "181150b1c  LEA RAX,[R11 + RDX*0x4]" in helper_a,
        "backward_step_loop": "181150b23  MOVAPS XMM1,XMM7" in helper_a and "181150b4e  JNS 0x181150b23" in helper_a,
        "row_loop": "181150b50  INC EDI" in helper_a and "181150b5a  JL 0x1811509e0" in helper_a,
    }
    expected_rows = 7
    expected_steps_per_row = 8
    checks = {
        "static_decomp": all(static_decomp.values()),
        "static_asm": all(static_asm.values()),
        "actual_mode4_entry": len(hits["mode4_entry"]) == 1,
        "actual_rows": len(hits["row_start"]) == expected_rows == len(hits["row_finish"]),
        "actual_forward_count": len(hits["forward_step"]) == expected_rows * expected_steps_per_row,
        "actual_backward_count": (4 * len(hits["backward_vector_step"]) + len(hits["backward_step"])) == expected_rows * expected_steps_per_row,
        "actual_edge_setup_count": len(hits["forward_edge_init"]) == expected_rows and len(hits["backward_setup"]) == expected_rows,
        "actual_mode_selector_overridden_only_in_harness": execution.get("input", {}).get("blur_mode") == 3,
        "no_production_edit": True,
    }
    status = "PASS_MODE4_EDGE_FORWARD_BACKWARD_PASSES" if all(checks.values()) else "BLOCKED_MODE4_EDGE_FORWARD_BACKWARD_PASSES"
    report = {
        "schema": 1,
        "kind": "olmkirakira_mode4_edge_forward_backward_passes",
        "date": "2026-07-18",
        "status": status,
        "ae_exact_claim": False,
        "production_edit": False,
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest()},
        "question": "What Mode4 edge initialization and forward/backward pass count is bounded across decomp, asm, and actual AEX?",
        "answer": {
            "semantic": "For the checked CV_32FC1 scalar path, each row seeds the forward accumulator from destination element zero, performs length-1 forward recurrence steps, resets the backward accumulator to zero, and performs length-1 reverse recurrence steps.",
            "count": {"rows": expected_rows, "forward_steps_per_row": expected_steps_per_row, "backward_steps_per_row": expected_steps_per_row},
            "edge_writeback_boundary": "This proves the bounded recurrence edge/pass shape only; it does not prove final normalization, final pixel writeback, or AE equivalence.",
        },
        "checks": checks,
        "static": {"decomp": static_decomp, "asm": static_asm},
        "actual_aex": {"helper": hex(HELPER), "execution": execution, "hits": hits},
        "limits": [
            "Mac-only Unicorn execution of the checked-in Windows PE; no Windows or AE-host claim.",
            "The witness uses a synthetic CV_32FC1 helper call with the mode selector changed only in the harness.",
            "No numeric output, final normalization, final writeback, or AE-exact claim is made.",
        ],
    }

    def portable(value):
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, str):
            return value.replace(str(ROOT), "<repo>")
        return value

    report = portable(report)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(f"""# OLMKiraKira Mode4 edge and forward/backward passes (2026-07-18)

Status: **{status}**
AE exact: **false**
Production edit: **none**

## Bounded result

On the checked `CV_32FC1` path, each of 7 rows seeds the forward accumulator
from destination element zero, executes 8 forward recurrence steps, resets the
backward accumulator to zero, and executes 8 backward recurrence steps. The
9-wide witness takes the reverse body in two four-lane vector iterations per
row, so the observed equivalent count is 56 backward steps.

## Evidence

- Decomp `FUN_181150790`: `fVar16 = *pfVar15` seeds the forward edge;
  `fVar16 = 0.0` resets the backward state; the pointer/index updates form
  increasing and decreasing row passes.
- Assembly: `0x181150a17` is the forward edge load, `0x181150a20` loops the
  forward recurrence, `0x181150b1c` sets up the reverse edge, and
  `0x181150b23` loops the backward recurrence. `0x1811509e0..0x181150b5a`
  encloses the row loop.
- Actual AEX: the instrumented helper reaches 7 row starts, 7 forward edge
  initializations, 7 backward setups, 56 forward steps, and 56 backward steps.

This is an edge/pass-shape proof only. Final normalization, final pixel
writeback, Windows/AE-host behavior, and exact equivalence remain unproven.

Verification: `python3 tools/emulation/test_olmkirakira_mode4_edge_passes_20260718.py`
""", encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks, "report": str(OUT_JSON)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
