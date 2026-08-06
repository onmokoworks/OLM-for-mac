#!/usr/bin/env python3
"""Extract the complete PF16 interpolation functions from the pinned AEX."""
import hashlib
import json
from pathlib import Path

import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
SPECS = (
    ("mainkernel16", 0x180004B80, 0x18000556F),
    ("executor16", 0x180005F60, 0x180006263),
)


def extract(pe, name, start, end):
    base = pe.OPTIONAL_HEADER.ImageBase
    code = pe.get_memory_mapped_image()[start - base:end - base]
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    instructions = list(cs.disasm(code, start))
    imap = {item.address: item for item in instructions}
    leaders = {start}
    edges = []
    for ins in instructions:
        nxt = ins.address + ins.size
        if ins.mnemonic.startswith("j"):
            target = int(ins.op_str, 16)
            leaders.add(target)
            if ins.mnemonic == "jmp":
                edges.append((ins.address, target, "jump"))
            else:
                leaders.add(nxt)
                edges.extend(((ins.address, target, "branch_true"),
                              (ins.address, nxt, "branch_false")))
    blocks = []
    for address in sorted(item for item in leaders if start <= item < end):
        sequence, cursor = [], address
        while cursor in imap:
            ins = imap[cursor]
            sequence.append({"address": hex(cursor), "bytes": ins.bytes.hex(),
                             "mnemonic": ins.mnemonic, "operands": ins.op_str})
            cursor += ins.size
            if ins.mnemonic.startswith("j") or ins.mnemonic == "ret" or cursor in leaders:
                break
        blocks.append({"start": hex(address), "end_exclusive": hex(cursor),
                       "instructions": sequence})
    spans = []
    for item in pe.DIRECTORY_ENTRY_EXCEPTION:
        begin = base + item.struct.BeginAddress
        if start <= begin < end:
            spans.append([hex(begin), hex(base + item.struct.EndAddress)])
    report = {
        "schema_version": 1, "status": "cfg_extracted", "function": name,
        "aex_sha256": SHA, "range": [hex(start), hex(end)],
        "unwind_spans": spans, "instruction_count": len(instructions),
        "block_count": len(blocks), "blocks": blocks,
        "edges": [{"from_instruction": hex(a), "to_block": hex(b), "kind": kind}
                  for a, b, kind in edges],
    }
    output = ROOT / f"refs/conformance/olmsmoother_v1_{name}_cfg_20260806.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(name, len(instructions), len(blocks), len(edges))


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    pe = pefile.PE(str(AEX))
    for spec in SPECS:
        extract(pe, *spec)


if __name__ == "__main__":
    main()
