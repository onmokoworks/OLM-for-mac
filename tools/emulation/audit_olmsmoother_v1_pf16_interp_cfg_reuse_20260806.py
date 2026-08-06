#!/usr/bin/env python3
"""Audit PF16 interpolation CFG boundaries and structural PF8 reuse."""
import hashlib
import json
from difflib import SequenceMatcher
from pathlib import Path

import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
FUNCTIONS = {
    "MainInterpKernel16": (0x180004B80, 0x18000556F),
    "InterpExecutor16": (0x180005F60, 0x180006263),
    "MainInterpKernel8": (0x180005570, 0x180005F5F),
    "InterpExecutor8": (0x180006270, 0x18000656A),
}


def disassemble(pe, start, end):
    base = pe.OPTIONAL_HEADER.ImageBase
    blob = pe.get_memory_mapped_image()[start - base:end - base]
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    return list(cs.disasm(blob, start))


def unwind_spans(pe, start, end):
    base = pe.OPTIONAL_HEADER.ImageBase
    return [[hex(base + item.struct.BeginAddress), hex(base + item.struct.EndAddress)]
            for item in pe.DIRECTORY_ENTRY_EXCEPTION
            if start <= base + item.struct.BeginAddress < end]


def direct_calls(instructions):
    calls = []
    for ins in instructions:
        if ins.mnemonic != "call":
            continue
        try:
            target = hex(int(ins.op_str, 16))
        except ValueError:
            target = ins.op_str
        calls.append({"site": hex(ins.address), "target": target})
    return calls


def pair_report(pf16, pf8):
    a = [ins.mnemonic for ins in pf16]
    b = [ins.mnemonic for ins in pf8]
    matcher = SequenceMatcher(a=a, b=b, autojunk=False)
    edits = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            edits.append({"kind": tag, "pf16": a[i1:i2], "pf8": b[j1:j2],
                          "pf16_index": [i1, i2], "pf8_index": [j1, j2]})
    return {"mnemonic_similarity": matcher.ratio(), "mnemonic_edits": edits}


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    pe = pefile.PE(str(AEX))
    decoded = {name: disassemble(pe, *bounds) for name, bounds in FUNCTIONS.items()}
    functions = {}
    for name, bounds in FUNCTIONS.items():
        instructions = decoded[name]
        functions[name] = {
            "range": [hex(bounds[0]), hex(bounds[1])],
            "byte_count": bounds[1] - bounds[0],
            "instruction_count": len(instructions),
            "last_instruction": {
                "address": hex(instructions[-1].address),
                "mnemonic": instructions[-1].mnemonic,
                "operands": instructions[-1].op_str,
            },
            "unwind_spans": unwind_spans(pe, *bounds),
            "instruction_set": sorted({ins.mnemonic for ins in instructions}),
            "calls": direct_calls(instructions),
        }
    report = {
        "schema_version": 1,
        "status": "audited",
        "aex_sha256": AEX_SHA256,
        "functions": functions,
        "pf8_reuse": {
            "main": pair_report(decoded["MainInterpKernel16"], decoded["MainInterpKernel8"]),
            "executor": pair_report(decoded["InterpExecutor16"], decoded["InterpExecutor8"]),
        },
    }
    assert report["pf8_reuse"]["main"]["mnemonic_similarity"] == 1.0
    assert report["pf8_reuse"]["executor"]["mnemonic_edits"] == [{
        "kind": "delete", "pf16": ["nop"], "pf8": [],
        "pf16_index": [61, 62], "pf8_index": [61, 61],
    }]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
