#!/usr/bin/env python3
"""Pin the actual public PF32 Smart owner and the bounded Mac admission."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
ASM = ROOT / "disasm/DistanceGradation.aex.asm.txt"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def function(text: str, name: str, next_name: str) -> str:
    start = text.index(f"; === {name}")
    return text[start:text.index(f"; === {next_name}", start)]

def main() -> int:
    asm = ASM.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    entry = function(asm, "entryPointFunc @ 181174bd0", "FUN_181174f90 @ 181174f90")
    smart = function(asm, "FUN_181173d20 @ 181173d20", "FUN_181174060 @ 181174060")
    facts = {
        "public_case_0x18_calls_smart_owner": "181174f0e  CALL 0x181173d20" in entry,
        "smart_reads_declared_bitdepth": "181173d58  MOVZX ECX,word ptr [RAX + 0x2c]" in smart,
        "smart_pf32_branch": "181173ede  CMP CX,0x20" in smart,
        "smart_input_checkout": "181173f22  CALL qword ptr [RAX]" in smart,
        "smart_output_checkout": "181173f3e  CALL qword ptr [RAX + 0x10]" in smart,
        "smart_pf32_whole_owner": "181173f6d  CALL 0x181172a10" in smart,
        "smart_float_compose": "181173ffc  LEA RCX,[0x181170c90]" in smart,
        "smart_iterate_float": "181174024  CALL qword ptr [R10]" in smart,
        "production_accepts_depth_32": "extra->input->bitdepth != 32" in source,
        "production_pf32_branch": "RenderBits<PF_PixelFloat>(in_data, params, input_world, output_world, true)" in source,
        "production_bounded_predicate": "is_admitted_pf32_smart_exported_matrix" in source,
        "production_balances_layer_checkout": "extra->cb->checkin_layer_pixels(in_data->effect_ref, DG_INPUT)" in source,
        "production_validates_world_formats": "input_format != expected_format || output_format != expected_format" in source,
    }
    assert all(facts.values()), facts
    report = {
        "schema": "olmdistancegradation.pf32-smartrender-boundary/3",
        "status": "PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_STATIC_AND_BOUNDED_PRODUCTION",
        "aex_sha256": sha(AEX),
        "disassembly_sha256": sha(ASM),
        "production_source_sha256": sha(SOURCE),
        "facts": facts,
        "actual_owner_chain": [
            "entryPointFunc case 0x18", "FUN_181173d20 bitdepth 0x20",
            "input/output checkout", "FUN_181172a10 PF32 whole owner",
            "PF iterateFloat Suite v1", "FUN_181170c90 compose",
        ],
        "production_boundary": "PF32 Smart is admitted only by the fixed 17x11 exported matrix predicate; unlisted tuples remain PF_Err_BAD_CALLBACK_PARAM",
        "supersedes": "The earlier version misclassified case 0x0b as SmartRender and falsely reported that the AEX had no PF32 Smart owner.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
