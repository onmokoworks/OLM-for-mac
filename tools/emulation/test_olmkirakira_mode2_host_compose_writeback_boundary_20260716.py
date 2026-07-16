#!/usr/bin/env python3
"""Bound the Mode-2 post-clamp host compose/writeback gap.

This is intentionally static-only.  It checks the pinned AEX bytes through
the checked-in loader and correlates the decomp/assembly slices, but it does
not pretend that a local AEX load is a Windows/AE host execution.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DECOMP = ROOT / "decomp" / "OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm" / "OLMKiraKira.aex.asm.txt"
AEX = ROOT / "aex" / "OLMKiraKira" / "Plugins" / "64" / "2025" / "OLMKiraKira.aex"
JSON_OUT = ROOT / "refs" / "conformance" / "olmkirakira_mode2_host_compose_writeback_boundary_20260716.json"
MD_OUT = ROOT / "refs" / "conformance" / "olmkirakira_mode2_host_compose_writeback_boundary_20260716.md"

TARGET = 0x18114FFD0
THRESHOLD = 0x181489990
ZERO_FILL = 0x181150250
PRE_CLAMP = 0x181150112
CLAMP = 0x181156740
WRITER_U8 = 0x181230B90
WRITER_U16 = 0x181230BD0
WRITER_F32 = 0x181230C20

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def slice_between(text: str, start: str, end: str) -> str:
    left = text.index(start)
    right = text.index(end, left)
    return text[left:right]


def static_checks() -> tuple[dict[str, bool], dict[str, str]]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    d_target = slice_between(decomp, "// === FUN_18114ffd0 @ 18114ffd0 ===", "// === FUN_1811501b0 @ 1811501b0 ===")
    a_target = slice_between(asm, "; === FUN_18114ffd0 @ 18114ffd0 ===", "; === FUN_1811501b0 @ 1811501b0 ===")
    d_dispatch = slice_between(decomp, "// === FUN_18114f4a0 @ 18114f4a0 ===", "// === FUN_18114fd90 @ 18114fd90 ===")
    a_dispatch = slice_between(asm, "; === FUN_18114f4a0 @ 18114f4a0 ===", "; === FUN_18114fd90 @ 18114fd90 ===")
    a_u8 = slice_between(asm, "; === FUN_181230b90 @ 181230b90 ===", "; === FUN_181230bd0 @ 181230bd0 ===")
    a_u16 = slice_between(asm, "; === FUN_181230bd0 @ 181230bd0 ===", "; === FUN_181230c20 @ 181230c20 ===")
    a_f32 = slice_between(asm, "; === FUN_181230c20 @ 181230c20 ===", "; === FUN_181230cd0 @ 181230cd0 ===")
    checks = {
        "mode2_target_is_present": "FUN_18114ffd0 @ 18114ffd0" in d_target and "18114ffd0  MOV RAX,RSP" in a_target,
        "dispatch_mode2_uses_vtable_plus_0x10": "param_15 == 2" in d_dispatch and "CALL qword ptr [RAX + 0x10]" in a_dispatch,
        "dispatch_mode1_and_mode2_share_float_output_setup": a_dispatch.count("MOVSS XMM0,dword ptr [RBP + 0x608]") == 2 and a_dispatch.count("LEA RCX,[RBP + 0x2e0]") >= 2,
        "target_zero_fills_output": "FUN_181150250(param_7,iVar3 * 4" in d_target and "CALL 0x181150250" in a_target,
        "target_reads_float64_threshold": "dVar1 = DAT_181489990" in d_target and "MOVSD XMM7,qword ptr [0x181489990]" in a_target,
        "target_has_four_clamps": d_target.count("FUN_181156740") >= 4 and a_target.count("CALL 0x181156740") == 4,
        "target_writes_float_rgba": "MOVSS dword ptr [RDI],XMM2" in a_target and "MOVSS dword ptr [RDI + 0xc],XMM0" in a_target,
        "target_returns_after_clamp": a_target.rstrip().endswith("18115019e  RET"),
        "target_has_no_host_writer_call": all(f"CALL 0x{address:x}" not in a_target for address in (WRITER_U8, WRITER_U16, WRITER_F32)),
        "target_has_no_byte_or_word_store": "MOV byte ptr" not in a_target and "MOV word ptr" not in a_target,
        "u8_writer_stores_bytes": "MOV byte ptr [RCX + 0x1],AL" in a_u8 and "MOV byte ptr [RCX],AL" in a_u8,
        "u16_writer_stores_words": "MOV word ptr [RCX + 0x2],AX" in a_u16 and "MOV word ptr [RCX],AX" in a_u16,
        "f32_writer_stores_float_words": "MOVSS dword ptr [RAX + 0x4],XMM0" in a_f32 and "MOVSS dword ptr [RAX],XMM3" in a_f32,
    }
    evidence = {
        "dispatch_mode2": "FUN_18114f4a0 -> indirect vtable +0x10 -> output pointer setup at 0x18114fc2d..0x18114fc28",
        "target_boundary": "0x181150112 clamp input -> four 0x181156740 calls -> float stores -> RET at 0x18115019e",
        "writer_candidates": "0x181230b90 byte stores; 0x181230bd0 word stores; 0x181230c20 float stores",
    }
    return checks, evidence


def emulator_bytes() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    threshold_raw = loader.read_bytes(THRESHOLD, 8)
    return {
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "threshold_raw_le_f64": threshold_raw.hex(),
        "threshold_f64": struct.unpack("<d", threshold_raw)[0],
        "address_bytes": {
            f"0x{address:x}": loader.read_bytes(address, 8).hex()
            for address in (TARGET, ZERO_FILL, PRE_CLAMP, CLAMP, WRITER_U8, WRITER_U16, WRITER_F32)
        },
        "loader": "tools/emulation/aex_loader.py AexLoader(fast=True)",
    }


def build_report() -> dict[str, object]:
    checks, evidence = static_checks()
    loaded = emulator_bytes()
    return {
        "kind": "olmkirakira_mode2_host_compose_writeback_boundary",
        "schema": 1,
        "date": "2026-07-16",
        "status": "pass" if all(checks.values()) and loaded["threshold_f64"] == 0.001 else "failed",
        "ae_exact_claim": False,
        "evidence_class": "static-only checked-in AEX/decomp/assembly boundary audit",
        "scope": "Mode-2 output after four clamps through the unresolved host compose/writeback boundary; no PNG tuning",
        "inputs": {
            "aex": str(AEX.relative_to(ROOT)),
            "decomp": str(DECOMP.relative_to(ROOT)),
            "disasm": str(ASM.relative_to(ROOT)),
            "target": f"FUN_18114ffd0 @ 0x{TARGET:x}",
            "threshold": f"DAT_181489990 @ 0x{THRESHOLD:x}, float64",
            "writer_candidates": [f"0x{WRITER_U8:x}", f"0x{WRITER_U16:x}", f"0x{WRITER_F32:x}"],
        },
        "static_checks": checks,
        "checked_in_aex_emulator": loaded,
        "facts": [
            "FACT: Mode 2 dispatch reaches an indirect vtable slot at +0x10 and supplies the float output pointer setup used by the aggregation target.",
            "FACT: FUN_18114ffd0 reads DAT_181489990 as a float64 comparison value, and the loaded pinned AEX stores 0.001 at that address.",
            "FACT: FUN_18114ffd0 writes only float RGBA values after four independent FUN_181156740 clamps, then returns.",
            "FACT: separate checked-in helpers perform byte, word, and float stores at FUN_181230b90, FUN_181230bd0, and FUN_181230c20.",
        ],
        "inferences": [
            "INFERENCE: the Mode-2 target's post-clamp buffer is an intermediate float RGBA result, not proof of host compose or final writeback.",
            "INFERENCE: no checked-in static chain binds this Mode-2 output pointer to a unique host compose site or one of the writer helpers.",
        ],
        "missing_evidence": [
            "Same-run Windows/AE trace with pinned AEX hash and Mode-2 vtable target.",
            "The output pointer after 0x18115019e, followed by the host compose operation and its source/glow inputs.",
            "Typed pre-writeback RGBA and the selected PF8/PF16/PF32 writer entry, input scale, conversion, and destination address.",
            "Final AE output comparison for the same pixel; PNG-only comparison is insufficient.",
        ],
        "limits": [
            "This is not AEX execution, Windows execution, host binding, or AE exactness.",
            "No production source, ledger, or PNG was changed.",
        ],
        "address_evidence": evidence,
    }


def markdown(report: dict[str, object]) -> str:
    checks = report["static_checks"]
    loaded = report["checked_in_aex_emulator"]
    lines = [
        "# OLMKiraKira Mode 2 host compose/writeback boundary",
        "",
        "Date: 2026-07-16",
        "Status: **pass / static-only bounded evidence**",
        "AE exact: **false**",
        "",
        "## Result",
        "",
        "The checked-in decomp/assembly and AEX loader evidence narrow Mode 2 to an intermediate float RGBA buffer. The target reads the pinned float64 threshold `0.001`, performs five-ray accumulation, applies four clamps, stores float channels, and returns. It does not call the separate byte/word/float writer helpers.",
        "",
        "The writer candidates are `FUN_181230b90` (byte stores), `FUN_181230bd0` (word stores), and `FUN_181230c20` (float stores). No unique host compose/writeback chain from the Mode-2 output pointer to those helpers is statically bound here.",
        "",
        "## FACT",
        "",
        "- Mode 2 dispatch uses vtable slot `+0x10`; the target is `FUN_18114ffd0 @ 0x18114ffd0`.",
        "- `DAT_181489990 @ 0x181489990` is loaded by `AexLoader` as little-endian float64 `0.001`.",
        "- `FUN_18114ffd0` ends after the four `FUN_181156740` calls and float stores at `RET 0x18115019e`.",
        "- Separate writer helper instruction bodies are present, but no same-run host binding is present in checked-in evidence.",
        "",
        "## INFERENCE",
        "",
        "- The post-clamp float buffer is an intermediate result; its later host compose and writeback semantics remain unresolved.",
        "- This witness is static-only and does not promote AE exactness.",
        "",
        "## Verification",
        "",
        "```text",
        f"python3 tools/emulation/test_olmkirakira_mode2_host_compose_writeback_boundary_20260716.py",
        f"=> status={report['status']}; static={sum(checks.values())}/{len(checks)}; threshold={loaded['threshold_f64']}",
        "```",
        "",
        "## Missing evidence",
        "",
        "- Same-run Windows/AE trace with AEX hash and selected Mode-2 target.",
        "- Output pointer after the final clamp, host compose inputs/formula, typed pre-writeback RGBA, writer entry/conversion, and destination address.",
        "- Same-pixel AE output comparison; PNG-only evidence is insufficient.",
        "",
        "No production source, ledger, or PNG was changed.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    JSON_OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD_OUT.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "static": f"{sum(report['static_checks'].values())}/{len(report['static_checks'])}", "threshold": report["checked_in_aex_emulator"]["threshold_f64"], "json": str(JSON_OUT), "md": str(MD_OUT)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
