#!/usr/bin/env python3
"""Extract the two native PF16 control-flow functions from the pinned AEX."""
import hashlib, json
from pathlib import Path
import capstone, pefile

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
SPECS = (
    (0x180002740, 0x1800033C4, "olmsmoother_v1_subhandler16_cfg_20260806.json"),
    (0x180009960, 0x180009E30, "olmsmoother_v1_edgewalker16_cfg_20260806.json"),
)


def extract(start: int, end: int, filename: str) -> None:
    pe = pefile.PE(str(AEX)); base = pe.OPTIONAL_HEADER.ImageBase
    code = pe.get_memory_mapped_image()[start - base:end - base]
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    instructions = list(cs.disasm(code, start)); imap = {i.address: i for i in instructions}
    leaders = {start}; edges = []
    for ins in instructions:
        nxt = ins.address + ins.size
        if ins.mnemonic.startswith("j"):
            target = int(ins.op_str, 16); leaders.add(target)
            if ins.mnemonic == "jmp": edges.append((ins.address, target, "jump"))
            else:
                leaders.add(nxt)
                edges.extend(((ins.address, target, "branch_true"), (ins.address, nxt, "branch_false")))
    blocks = []
    for address in sorted(x for x in leaders if start <= x < end):
        sequence = []; cursor = address
        while cursor in imap:
            ins = imap[cursor]
            sequence.append({"address": hex(cursor), "bytes": ins.bytes.hex(),
                             "mnemonic": ins.mnemonic, "operands": ins.op_str})
            cursor += ins.size
            if ins.mnemonic.startswith("j") or ins.mnemonic == "ret" or cursor in leaders: break
        blocks.append({"start": hex(address), "end_exclusive": hex(cursor), "instructions": sequence})
    report = {"schema_version": 1, "status": "cfg_extracted", "aex_sha256": SHA,
              "range": [hex(start), hex(end)], "instruction_count": len(instructions),
              "block_count": len(blocks), "blocks": blocks,
              "edges": [{"from_instruction": hex(a), "to_block": hex(b), "kind": k}
                        for a, b, k in edges]}
    out = ROOT / "refs/conformance" / filename
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(filename, len(instructions), len(blocks), len(edges))


def main() -> None:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    for spec in SPECS: extract(*spec)


if __name__ == "__main__": main()
