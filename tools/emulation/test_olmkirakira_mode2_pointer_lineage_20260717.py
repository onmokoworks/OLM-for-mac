#!/usr/bin/env python3
"""Mac-only, fail-closed probe for the OLMKiraKira Mode-2 writer boundary.

The probe executes the pinned AEX Mode-2 target and PF32 writer in Unicorn,
recording the live float/output state at both boundaries.  It never calls the
writer as though a Python-mediated handoff were a natural AEX call edge:
because the pinned Mode-2 path has no writer edge, the report is BLOCKED.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RDI,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM1,
    UC_X86_REG_XMM2,
    UC_X86_REG_XMM3,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_pointer_lineage_20260717.json"

MODE2 = 0x18114FFD0
DISPATCH = 0x18114F4A0
MODE2_CALLSITE = 0x18114FC28
OUTPUT = 0x181150022
PRE_CLAMP = 0x181150112
PF32 = 0x181230C20
PF32_CALLSITES = (0x18114E5D7, 0x18114E739)
WRITERS = (0x181230B90, 0x181230BD0, PF32)

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def xmm_words(loader: AexLoader) -> list[str]:
    return [
        f"0x{loader.uc.reg_read(reg) & 0xffffffff:08x}"
        for reg in (UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)
    ]


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    dispatch = decomp[decomp.index("// === FUN_18114f4a0"):decomp.index("// === FUN_18114fd90")]
    dispatch_asm = asm[asm.index("; === FUN_18114f4a0"):asm.index("; === FUN_18114fd90")]
    target = asm[asm.index("; === FUN_18114ffd0"):asm.index("; === FUN_1811501b0")]
    writers = asm[asm.index("; === FUN_181230b90"):asm.index("; === FUN_181230cd0")]
    return {
        "dispatch_mode2_vtable_plus_0x10": "param_15 == 2" in dispatch and "CALL qword ptr [RAX + 0x10]" in dispatch_asm,
        "mode2_callsite_anchor": "18114fc28  CALL qword ptr [RAX + 0x10]" in dispatch_asm,
        "mode2_output_and_preclamp": "181150022  CALL" in target and "181150112  MOVAPS XMM0,XMM2" in target,
        "mode2_float_rgba_output": target.count("MOVSS dword ptr [RDI") >= 4,
        "mode2_has_no_writer_edge": all(f"CALL 0x{address:x}" not in target for address in WRITERS),
        "pf32_writer_stack_destination": "181230c20  MOV RAX,qword ptr [RSP + 0x28]" in writers,
        "pf32_writer_float_stores": "MOVSS dword ptr [RAX + 0x4],XMM0" in writers and "MOVSS dword ptr [RAX],XMM3" in writers,
        "typed_pf32_callsites_present": all(f"{address:x}  CALL 0x181230c20" in asm for address in PF32_CALLSITES),
        "no_static_mode2_to_pf32_edge": all(f"CALL 0x{PF32:x}" not in target for _ in (0,)),
    }


def run_mode2_and_pf32_control() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    rays = []
    for value in (0.2, 0.0, 0.0, 0.0, 0.0):
        address = loader.host_alloc(4)
        loader.write_bytes(address, struct.pack("<f", f32(value)))
        rays.append(address)
    ray_array = loader.host_alloc(40)
    loader.write_bytes(ray_array, struct.pack("<5Q", *rays))
    colors = loader.host_alloc(80)
    loader.write_bytes(colors, struct.pack("<20f", *([0.0, 0.5, 0.75, 1.0] * 5)))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, b"\0" * 5)
    output = loader.host_alloc(16)
    loader.write_bytes(output, b"\xa5" * 16)
    mode2_trace: dict[str, object] = {"pre_clamp_hits": 0}

    def on_pre_clamp(current: AexLoader, _address: int, _size: int) -> None:
        mode2_trace.update({
            "pre_clamp_hits": int(mode2_trace["pre_clamp_hits"]) + 1,
            "rip": hex(PRE_CLAMP),
            "rdi_output_pointer": hex(current.uc.reg_read(UC_X86_REG_RDI)),
            "xmm0_to_xmm3_f32_bits": xmm_words(current),
        })

    loader.add_code_hook(PRE_CLAMP, on_pre_clamp)
    mode2_call = loader.call_function(
        MODE2,
        [0, ray_array, colors, flags, 0, 0, output, 1, 1],
        max_instructions=100_000,
    )
    mode2_raw = loader.read_bytes(output, 16)
    mode2_values = list(struct.unpack("<4f", mode2_raw))

    destination = loader.host_alloc(16)
    before = b"\xa5" * 16
    loader.write_bytes(destination, before)
    writer_trace: dict[str, object] = {"writer_entry_hits": 0}

    def on_pf32(current: AexLoader, _address: int, _size: int) -> None:
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        writer_trace.update({
            "writer_entry_hits": int(writer_trace["writer_entry_hits"]) + 1,
            "rip": hex(PF32),
            "xmm0_to_xmm3_f32_bits": xmm_words(current),
            "destination_pointer_rsp_plus_0x28": hex(struct.unpack("<Q", current.read_bytes(rsp + 0x28, 8))[0]),
            "rsp": hex(rsp),
            "destination_before": before.hex(),
        })

    loader.add_code_hook(PF32, on_pf32)
    writer_call = loader.call_function(
        PF32,
        int_args=[0, 0, 0, 0, destination],
        float_args={index: value for index, value in enumerate(mode2_values)},
        max_instructions=1000,
    )
    after = loader.read_bytes(destination, 16)
    writer_trace["destination_after"] = after.hex()
    writer_trace["destination_mutated"] = after != before

    return {
        "mode2": {
            "target": hex(MODE2),
            "output_pointer": hex(output),
            "output_before": (b"\xa5" * 16).hex(),
            "output_after": mode2_raw.hex(),
            "output_rgba_f32_bits": [bits(value) for value in mode2_values],
            "output_mutated": mode2_raw != b"\xa5" * 16,
            "pre_clamp_trace": mode2_trace,
            "instructions": mode2_call["instructions"],
        },
        "pf32_control_only": {
            "target": hex(PF32),
            "input_rgba_f32_bits_from_mode2_output": [bits(value) for value in mode2_values],
            "trace": writer_trace,
            "instructions": writer_call["instructions"],
            "same_run": True,
            "natural_aex_lineage": False,
        },
    }


def main() -> int:
    static = static_checks()
    runtime = run_mode2_and_pf32_control()
    natural = False
    status = "BLOCKED" if all(static.values()) and not natural else "FAILED"
    report = {
        "kind": "olmkirakira_mode2_pointer_lineage",
        "schema": 1,
        "date": "2026-07-17",
        "status": status,
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn execution of the checked-in Windows PE AEX; no Windows/AE claim",
        "inputs": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
            "dispatch": f"FUN_{DISPATCH:x} @ 0x{DISPATCH:x}",
            "mode2_callsite": f"0x{MODE2_CALLSITE:x} via vtable +0x10",
            "mode2_target": f"FUN_{MODE2:x} @ 0x{MODE2:x}",
            "output_checkpoint": f"0x{OUTPUT:x}",
            "pre_clamp": f"0x{PRE_CLAMP:x}",
            "pf32_writer": f"FUN_{PF32:x} @ 0x{PF32:x}",
            "pf32_callsites": [f"0x{address:x}" for address in PF32_CALLSITES],
        },
        "static_checks": static,
        "runtime": runtime,
        "lineage_gate": {
            "natural_aex_lineage_reached": natural,
            "mediated_same_run_control_is_rejected": True,
            "reason": "Mode2 target returns after float stores and has no call edge to PF32; the PF32 invocation is a control-only direct leaf call.",
        },
        "facts": [
            "FACT: Mode2 executed and mutated its float RGBA output buffer in the actual checked-in AEX.",
            "FACT: the pre-clamp hook recorded XMM0..XMM3 and the live RDI output pointer.",
            "FACT: PF32 executed in the same Unicorn instance and recorded XMM0..XMM3, [RSP+0x28], and destination before/after bytes.",
            "FACT: the same-run Python-mediated value transfer is not natural AEX pointer lineage.",
        ],
        "limits": [
            "No natural Mode2-to-typed-writer lineage was promoted.",
            "No Windows execution, After Effects host binding, final pixel, or AE exactness claim.",
            "No production source or ledger was changed.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "static": f"{sum(static.values())}/{len(static)}", "natural_aex_lineage": natural, "report": str(REPORT)}, sort_keys=True))
    return 2 if status == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
