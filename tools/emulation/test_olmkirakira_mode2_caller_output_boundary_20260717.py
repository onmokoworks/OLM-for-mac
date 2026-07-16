#!/usr/bin/env python3
"""Bound the immediate Mode-2 caller/output handoff.

The direct target execution is actual checked-in AEX execution.  The larger
caller is kept static because its first argument is a host-owned vtable object
with external allocation and callback state that the checked-in loader does
not model.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_caller_output_boundary_20260717.json"
CALLER = 0x18114F4A0
MODE1_SLOT = 0x8
MODE2_SLOT = 0x10
TARGET = 0x18114FFD0
WRITERS = (0x181230B90, 0x181230BD0, 0x181230C20)

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def f32_bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def direct_target_witness() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    rays = []
    for value in (0.2, 0.0, 0.0, 0.0, 0.0):
        address = loader.host_alloc(4)
        loader.write_bytes(address, struct.pack("<f", value))
        rays.append(address)
    ray_array = loader.host_alloc(40)
    loader.write_bytes(ray_array, struct.pack("<5Q", *rays))
    colors = loader.host_alloc(80)
    loader.write_bytes(colors, struct.pack("<20f", *([0.0, 0.5, 0.75, 1.0] * 5)))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, b"\0" * 5)
    output = loader.host_alloc(16)
    loader.write_bytes(output, b"\xa5" * 16)
    call = loader.call_function(
        TARGET,
        [0, ray_array, colors, flags, 0, 0, output, 1, 1],
        max_instructions=100_000,
    )
    raw = loader.read_bytes(output, 16)
    values = loader.read_f32_array(output, 4)
    expected = ["0x3f000000", "0x3f400000", "0x3f800000", "0x3e4ccccd"]
    return {
        "target": f"0x{TARGET:x}",
        "output_address": f"0x{output:x}",
        "output_raw_hex": raw.hex(),
        "output_rgba_f32_bits": [f32_bits(value) for value in values],
        "expected_output_rgba_f32_bits": expected,
        "output_matches_expected": [f32_bits(value) for value in values] == expected,
        "instructions": call["instructions"],
    }


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    d_start = decomp.index("// === FUN_18114f4a0 @ 18114f4a0 ===")
    d_end = decomp.index("// === FUN_18114fd90 @ 18114fd90 ===", d_start)
    a_start = asm.index("; === FUN_18114f4a0 @ 18114f4a0 ===")
    a_end = asm.index("; === FUN_18114fd90 @ 18114fd90 ===", a_start)
    d_body, a_body = decomp[d_start:d_end], asm[a_start:a_end]
    callsite = a_body[a_body.index("18114fbcf  MOV R10"):a_body.index("18114fc8a  MOV RBX")]
    return {
        "immediate_caller_present": f"FUN_{CALLER:x}" in d_body and f"{CALLER:x}" in a_body,
        "mode1_and_mode2_vtable_slots": f"CALL qword ptr [RAX + 0x{MODE1_SLOT:x}]" in a_body and f"CALL qword ptr [RAX + 0x{MODE2_SLOT:x}]" in a_body,
        "mode2_target_callsite": "18114fc28  CALL qword ptr [RAX + 0x10]" in a_body,
        "caller_forwards_output_arg7": "MOV qword ptr [RSP + 0x30],RCX" in callsite and "MOV RCX,qword ptr [RBP + -0x20]" in callsite,
        "caller_passes_dimensions_and_opacity": "MOV ECX,dword ptr [RBP + 0x5e8]" in callsite and "MOV ECX,dword ptr [RBP + 0x5e0]" in callsite,
        "post_call_has_no_output_read": "18114fc8a  MOV RBX" in a_body and "[RBP + -0x20]" not in a_body[a_body.index("18114fc8a  MOV RBX"):],
        "post_call_has_no_typed_writer": all(f"CALL 0x{address:x}" not in a_body[a_body.index("18114fc8a  MOV RBX"):a_body.index("18114fd17")] for address in WRITERS),
        "caller_returns_after_cleanup": "18114fd54  CALL 0x18132b1c0" in a_body and a_body.rstrip().endswith("18114fd54  CALL 0x18132b1c0"),
    }


def main() -> int:
    static = static_checks()
    actual = direct_target_witness()
    report = {
        "kind": "olmkirakira_mode2_caller_output_boundary",
        "schema": 1,
        "date": "2026-07-17",
        "status": "pass" if all(static.values()) and actual["output_matches_expected"] else "failed",
        "ae_exact_claim": False,
        "evidence_class": "actual checked-in AEX target execution plus immediate-caller static callsite audit",
        "inputs": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
            "immediate_caller": f"FUN_{CALLER:x} @ 0x{CALLER:x}",
            "mode1_vtable_slot": f"+0x{MODE1_SLOT:x}",
            "mode2_vtable_slot": f"+0x{MODE2_SLOT:x}",
            "mode2_target": f"FUN_{TARGET:x} @ 0x{TARGET:x}",
        },
        "static_checks": static,
        "actual_aex_target_witness": actual,
        "boundary": {
            "caller_to_target": "FUN_18114f4a0 indirect vtable +0x10 -> FUN_18114ffd0",
            "target_output_argument": "target param_7 / RDI receives caller [RBP-0x20] forwarded at [RSP+0x30]",
            "after_target_return": "caller performs vector cleanup/deallocation and returns; no output read, host compose, or typed writer call is present",
            "first_unavailable_abi": "the host-owned object passed as caller param_1 (vtable slots, channel allocation/callback state, and upstream buffers) required to execute FUN_18114f4a0 end-to-end",
        },
        "facts": [
            "FACT: the immediate AEX caller selects Mode 1 through vtable slot +0x8 and Mode 2 through +0x10.",
            "FACT: the Mode-2 callsite forwards its output pointer as target param_7; the actual target writes the proven float RGBA tuple there.",
            "FACT: the immediate caller has no post-call read of that output pointer and no PF8/PF16/PF32 writer call before returning.",
            "FACT: the direct target witness executed against the pinned AEX and wrote the expected float RGBA bytes.",
        ],
        "inferences": [
            "INFERENCE: Merge Mode participates in selecting the aggregation target before the result reaches the caller-owned float buffer.",
            "INFERENCE: the next consumer of that buffer is outside this immediate AEX caller slice; this evidence does not place Merge Mode in later writer selection.",
        ],
        "limits": [
            "The full caller cannot be executed by the checked-in loader without its host-owned object/ABI and upstream allocations.",
            "The first unavailable ABI is the caller param_1 vtable/channel object, before any host compose/writeback observation.",
            "No PNG, Windows host result, or AE exactness is claimed.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "static": f"{sum(static.values())}/{len(static)}", "actual_aex_target": actual["output_matches_expected"], "report": str(REPORT)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
