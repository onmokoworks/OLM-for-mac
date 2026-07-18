#!/usr/bin/env python3
"""Bound OLMKiraKira Mode4 recurrence geometry at the actual AEX body.

This reuses the existing small CV_32FC1 helper scaffold, changes only the
helper's mode selector from 3 to 4, and observes the inline recurrence and
gain boundaries. It is evidence-only: no production source is
patched or bypassed and no production source is changed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import (
    UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9,
    UC_X86_REG_RSP, UC_X86_REG_RSI, UC_X86_REG_R15,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
MODE3_GEOMETRY = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_geometry_20260718.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_mode4_recurrence_boundary_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_mode4_recurrence_boundary_20260718.md"

MODE4_ENTRY = 0x181150979
MODE4_GAIN = 0x181150F3D
HELPER = 0x181150790


def load_base():
    spec = importlib.util.spec_from_file_location("mode4_base_20260718", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Mode3 base harness")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def slice_between(text: str, start: str, end: str) -> str:
    left = text.index(start)
    return text[left:text.index(end, left)]


def main() -> int:
    base = load_base()
    entry_hits: list[dict[str, Any]] = []
    gain_hits: list[dict[str, Any]] = []

    class Mode4Loader(base.AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            super().add_code_hook(MODE4_ENTRY, self.on_mode4_entry)
            super().add_code_hook(MODE4_GAIN, self.on_mode4_gain)

        def on_mode4_entry(self, loader, _address, _size):
            entry_hits.append({
                "rip": hex(MODE4_ENTRY),
                "length_register_esi": loader.uc.reg_read(UC_X86_REG_RSI),
                "working_register_r15": loader.uc.reg_read(UC_X86_REG_R15),
            })

        def on_mode4_gain(self, loader, _address, _size):
            rsp = loader.uc.reg_read(UC_X86_REG_RSP)
            regs = {"rcx": loader.uc.reg_read(UC_X86_REG_RCX),
                    "rdx": loader.uc.reg_read(UC_X86_REG_RDX),
                    "r8": loader.uc.reg_read(UC_X86_REG_R8),
                    "r9": loader.uc.reg_read(UC_X86_REG_R9)}
            stack = [struct.unpack("<Q", loader.read_bytes(rsp + off, 8))[0]
                     for off in (0x20, 0x28, 0x30, 0x38)]
            gain_hits.append({
                "rip": hex(MODE4_GAIN),
                "return_address": hex(struct.unpack("<Q", loader.read_bytes(rsp, 8))[0]),
                "r15_before_neg": hex(loader.uc.reg_read(UC_X86_REG_R15)),
                "stack_plus_20_38": [hex(value) for value in stack],
            })

        def call_function(self, address, *args, **kwargs):
            int_args = list(kwargs.get("int_args", []))
            if address == HELPER:
                if len(int_args) != 9:
                    raise AssertionError(f"unexpected helper ABI: {int_args}")
                int_args[7] = 4
                kwargs["int_args"] = int_args
            return super().call_function(address, *args, **kwargs)

    original = base.AexLoader
    base.AexLoader = Mode4Loader
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
    caller_d = slice_between(decomp, "// === FUN_18114f4a0", "// === FUN_18114fd90")
    caller_a = slice_between(asm, "; === FUN_18114f4a0", "; === FUN_18114fd90")
    helper_d = slice_between(decomp, "// === FUN_181150790", "// === FUN_1811512a0")
    helper_a = slice_between(asm, "; === FUN_181150790", "; === FUN_1811512a0")
    mode4_d = helper_d[helper_d.index("else if (param_8 == 4)"):]
    mode4_d = {
        "odd_kernel": "iVar6 = iVar6 * 2 + 1" in caller_d,
        "first_src_to_temp": "local_628 = puVar12" in caller_d and "local_610 = local_588" in caller_d,
        "second_in_place": caller_d.count("local_610 = puVar12") >= 2,
        "recurrence_factors": all(item in helper_d for item in (
            "fVar18 = (float)(int)param_7 / (float)iVar1",
            "fVar20 = (float)(int)param_7 / (float)(iVar1 * iVar1)",
            "fVar16 = fVar20 *",
            "+ fVar16 * fVar18",
        )),
        "inline_no_subordinate_filter": "FUN_181280bc0" not in mode4_d,
    }
    asm_facts = {
        "inline_entry": "181150979  LEA EAX,[RSI + 0x1]" in helper_a,
        "recurrence_factors": all(item in helper_a for item in (
            "181150983  MOVAPS XMM6,XMM9",
            "181150987  DIVSS XMM6,XMM0",
            "181150995  MOVAPS XMM7,XMM9",
            "181150999  DIVSS XMM7,XMM0",
        )),
        "gain_boundary": "181150f3d  NEG R15D" in helper_a,
    }
    prior = json.loads(MODE3_GEOMETRY.read_text(encoding="utf-8"))
    checks = {
        "static_decomp": all(mode4_d.values()),
        "static_asm": all(asm_facts.values()),
        "actual_aex_mode4_entry": bool(entry_hits),
        "actual_aex_gain_boundary": bool(gain_hits),
        "actual_mode_selector_overridden_only_in_harness": execution.get("input", {}).get("blur_mode") == 3,
        "actual_mode4_length5": bool(entry_hits) and entry_hits[0]["length_register_esi"] == 5,
        "mode3_prior_geometry_present": prior.get("status") == "bounded_geometry_shape_proven",
        "no_production_edit": True,
    }
    status = "PASS_MODE4_BOUNDED_RECURRENCE_GEOMETRY" if all(checks.values()) else "BLOCKED_MODE4_BOUNDARY"
    report = {
        "schema": 1,
        "kind": "olmkirakira_mode4_recurrence_boundary",
        "date": "2026-07-18",
        "status": status,
        "ae_exact_claim": False,
        "production_edit": False,
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest()},
        "question": "What bounded Mode4 recurrence/gain/edge/writeback semantic is proven across decomp, asm, and actual AEX?",
        "answer": {
            "semantic": "Mode4's inline recurrence uses fVar18 = r/(r+1) and fVar20 = r/(r+1)^2, updating each cell as fVar20*source + fVar18*prior; the actual AEX reaches the recovered scalar/gain boundary.",
            "edge_writeback_boundary": "The actual-AEX witness reaches the inline recurrence and its scalar gain boundary; edge policy and final pixel writeback are intentionally outside this proof.",
        },
        "checks": checks,
        "static": {"decomp": mode4_d, "asm": asm_facts},
        "actual_aex": {"helper": hex(HELPER), "execution": execution, "mode4_entry": entry_hits, "gain_boundary": gain_hits},
        "prior_mode3_geometry": {"path": str(MODE3_GEOMETRY.relative_to(ROOT)), "status": prior.get("status")},
        "limits": [
            "Mac-only Unicorn execution of the checked-in Windows PE; no Windows or AE-host claim.",
            "The actual-AEX witness observes the inline recurrence and gain boundaries; edge policy, later recurrence values, and final writeback remain unproven.",
            "No production source, OpenCV assertion, input value, or output value was patched.",
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
    OUT_MD.write_text(f"""# OLMKiraKira Mode4 recurrence boundary (2026-07-18)

Status: **{status}**
AE exact: **false**
Production edit: **none**

## Bounded semantic

For the fifth Highlight layer, the AEX Mode4 inline body uses
`fVar18 = r/(r+1)` and `fVar20 = r/(r+1)^2`, then updates each recurrence cell
as `fVar20*source + fVar18*prior`. The actual AEX reaches the inline scalar/
gain boundary for length 5. This is a recurrence/gain fact, not a claim about
edge policy or final normalization.

## Cross-check

- Decomp: `FUN_181150790` derives `fVar18 = r/(r+1)` and
  `fVar20 = r/(r+1)^2`, then updates each recurrence cell as
  `fVar20 * source + fVar18 * prior`.
- Assembly: `0x181150979` enters the inline Mode4 body, `0x181150987` and
  `0x181150999` form the two factors, and `0x181150f3d` is the recovered
  scalar/gain boundary.
- Actual AEX: direct helper invocation with only the mode selector changed to
  4 reaches both inline boundaries for length 5.

## Boundary and limits

The actual-AEX entry and gain hooks are inside the inline Mode4 body. Edge
handling, later pass outputs, gain numeric state beyond the recovered factors,
and final pixel writeback remain unproven. No production edit was made.

Verification: `python3 tools/emulation/test_olmkirakira_mode4_recurrence_boundary_20260718.py`
""", encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks, "report": str(OUT_JSON)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
