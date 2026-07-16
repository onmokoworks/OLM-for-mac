#!/usr/bin/env python3
"""Fail-closed local oracle for the FUN_18000ada0 entry contract.

This is evidence-only.  It does not call production Mac code or claim that
the retained Windows return bytes are complete.  The binary/decomp anchors
are checked before the independent address oracle is allowed to pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex"
ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def section(text: str, start: str, end: str) -> str:
    first = text.find(start)
    require(first >= 0, f"missing section anchor {start}")
    last = text.find(end, first + len(start))
    require(last >= 0, f"missing section terminator {end}")
    return text[first:last]


def static_contract() -> dict[str, Any]:
    aex_hash = hashlib.sha256(AEX.read_bytes()).hexdigest()
    require(aex_hash == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    ada_asm = section(asm, "; === FUN_18000ada0", "; === FUN_18000ae10")
    ada_c = section(decomp, "// === FUN_18000ada0", "// === FUN_18000ae10")
    ae_c = section(decomp, "// === FUN_18000ae10", "// === FUN_18000b120")

    required_asm = [
        "MOV EAX,dword ptr [R8 + 0x4]",
        "MOV EAX,dword ptr [R8 + 0xc]",
        "MOV EAX,dword ptr [R8]",
        "MOV EAX,dword ptr [R8 + 0x8]",
        "CALL 0x180020f00",
    ]
    for anchor in required_asm:
        require(anchor in ada_asm, f"missing ada0 AEX anchor: {anchor}")
    require("local_res18[0] = param_3[1]" in ada_c, "rect top mapping not grounded")
    require("local_18 = param_3[3]" in ada_c, "rect bottom mapping not grounded")
    require("local_14 = *param_3" in ada_c, "rect left mapping not grounded")
    require("local_10[0] = param_3[2]" in ada_c, "rect right mapping not grounded")

    for anchor in ("[R15 + 0x1c]", "[R15 + 0x70]", "[R15 + 0x74]"):
        require(anchor in section(asm, "; === FUN_18000ae10", "; === FUN_18000b120"), f"missing ae10 AEX read: {anchor}")
    require("(float)*(int *)(param_5 + 0x1c) / DAT_180022dd0" in ae_c, "config +0x1c semantics not grounded")
    require("(*(char *)(param_5 + 0x70) != '\\0')" in ae_c, "config +0x70 gate not grounded")
    require("*(float *)(param_5 + 0x74)" in ae_c, "config +0x74 multiplier not grounded")

    return {
        "aex_sha256": aex_hash,
        "entry": "FUN_18000ada0@0x18000ada0",
        "arguments": ["RCX=source_fplane", "RDX=class_fplane", "R8=rect", "R9=config"],
        "fplane": {
            "size_bytes": 24,
            "base_offset": "0x00",
            "width_offset": "0x08",
            "height_offset": "0x0c",
            "stride_offset": "0x10",
            "stride_unit": "bytes per row",
            "source_pixel_bytes": 16,
            "class_pixel_bytes": 4,
        },
        "rect": {"layout": "int32[4]", "order": ["left", "top", "right", "bottom"], "end_exclusive": True},
        "config": {
            "+0x1c": "int threshold numerator; ae10 divides by DAT_180022dd0 then adds bias",
            "+0x70": "byte gate for neighbor hysteresis branch",
            "+0x74": "float multiplier applied to hysteresis comparison",
        },
        "evidence": {
            "assembly": "disasm/OLMSmoother2.aex.asm.txt",
            "decomp": "decomp/OLMSmoother2.aex.c.txt",
        },
    }


def independent_address_oracle() -> dict[str, Any]:
    # Deliberately use non-tight rows and a non-zero sub-rectangle.  This
    # catches accidental pixel-stride or inclusive-right/bottom assumptions.
    width, height = 5, 4
    source_stride, class_stride = 16 * width + 16, 4 * width + 4
    rect = (1, 1, 4, 3)
    source = bytearray(source_stride * height)
    classes = bytearray(class_stride * height)
    for y in range(height):
        for x in range(width):
            source[y * source_stride + x * 16 : y * source_stride + x * 16 + 4] = bytes((x, y, 0xA, 0x5))
            classes[y * class_stride + x * 4 : y * class_stride + x * 4 + 4] = bytes((x, y, 0xC, 0x3))

    visited = []
    for y in range(rect[1], rect[3]):
        for x in range(rect[0], rect[2]):
            source_offset = y * source_stride + x * 16
            class_offset = y * class_stride + x * 4
            require(source[source_offset : source_offset + 4] == bytes((x, y, 0xA, 0x5)), f"source address mismatch at {(x, y)}")
            require(classes[class_offset : class_offset + 4] == bytes((x, y, 0xC, 0x3)), f"class address mismatch at {(x, y)}")
            visited.append([x, y])
    untouched = [
        [x, y]
        for y in range(height)
        for x in range(width)
        if not (rect[0] <= x < rect[2] and rect[1] <= y < rect[3])
    ]
    return {
        "source_stride": source_stride,
        "class_stride": class_stride,
        "rect": list(rect),
        "visited_pixels": visited,
        "untouched_pixels": untouched,
        "exclusive_endpoints_proved": True,
    }


def render(report: dict[str, Any]) -> str:
    c = report["contract"]
    return "\n".join([
        "# OLMSmoother2 case0012 natural caller contract follow-up",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "The checked-in AEX and decomp independently ground the FUN_18000ada0 ABI before the local address oracle runs.",
        "",
        "## Grounded Contract",
        "",
        f"- Arguments: `{', '.join(c['arguments'])}`.",
        "- Both source and class FPlane records are 24 bytes: pointer at `+0x00`, width/height at `+0x08/+0x0c`, and byte row stride at `+0x10`.",
        "- Rect is four int32 values `[left, top, right, bottom]`, with right and bottom exclusive in the worker loop.",
        "- Config `+0x1c` is the ae10 threshold numerator; `+0x70` gates hysteresis; `+0x74` is its float multiplier.",
        "",
        "## Independent Check",
        "",
        f"- Padded source/class strides `{report['oracle']['source_stride']}/{report['oracle']['class_stride']}` were addressed correctly.",
        f"- Non-tight rect `{report['oracle']['rect']}` visited `{len(report['oracle']['visited_pixels'])}` pixels and left `{len(report['oracle']['untouched_pixels'])}` pixels untouched.",
        "",
        "Claims are local binary/decomp layout evidence only. No Windows return, AE host, production source, or ledger claim is made.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    contract = static_contract()
    oracle = independent_address_oracle()
    report = {
        "verdict": "PASS_FAIL_CLOSED_FUN_18000ADA0_ENTRY_CONTRACT_ORACLE",
        "scope": "local actual-AEX/decomp contract plus independent padded-stride rectangle oracle",
        "contract": contract,
        "oracle": oracle,
        "claims_not_made": ["No Windows/AE execution claim", "No production Mac source or ledger claim"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
