#!/usr/bin/env python3
"""Generate lossless C++ X-macro IR for PF16 interpolation CFGs.

The consumer supplies OLM_PF16_INSN/BRANCH/CALL macros. Calls already use
portable helper names, so production integration never needs AEX addresses.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = (
    ("mainkernel16", 617, "OLMSmoother_mainkernel16.generated.inc"),
    ("executor16", 188, "OLMSmoother_executor16.generated.inc"),
)
CALLS = {
    0x1800021F0: "ColorCompare16",
    0x180005F60: "InterpExecutor16Exact",
    0x180001000: "LinearOffsetFunction",
    0x180001020: "LinearOffsetOneValue",
    0x180001040: "LinearOffsetZeroOneValue",
    0x180001070: "LinearOffsetZeroValue",
    0x180001090: "LinearThreeOffsetFunction",
    0x180001620: "ColorBlend16",
    0x180001ED0: "AlphaBlend16",
    0x180003FF0: "NeighborExtract16",
    0x18000B720: "SecurityCheckCookie",
}


def quote(text):
    return json.dumps(text)


def generate(name, expected, filename):
    source = ROOT / f"refs/conformance/olmsmoother_v1_{name}_cfg_20260806.json"
    cfg = json.loads(source.read_text())
    instructions = [ins for block in cfg["blocks"] for ins in block["instructions"]]
    by_address = {int(ins["address"], 0): ins for ins in instructions}
    assert len(by_address) == expected
    lines = [
        f"// Generated from {source.name}",
        f"// actual AEX SHA-256: {cfg['aex_sha256']}",
        "// Define the OLM_PF16_* macros before including this file.",
    ]
    for address in sorted(by_address):
        ins = by_address[address]
        mnemonic, operands = ins["mnemonic"], ins["operands"]
        if mnemonic == "call":
            try:
                target = int(operands, 16)
            except ValueError:
                assert operands == "qword ptr [rax]"
                lines.append(f"OLM_PF16_CALL_INDIRECT(0x{address:x}, {quote(operands)})")
            else:
                assert target in CALLS, hex(target)
                lines.append(f"OLM_PF16_CALL(0x{address:x}, {CALLS[target]})")
        elif mnemonic.startswith("j"):
            lines.append(f"OLM_PF16_BRANCH(0x{address:x}, {mnemonic}, {operands})")
        elif mnemonic == "ret":
            lines.append(f"OLM_PF16_RET(0x{address:x})")
        else:
            lines.append(f"OLM_PF16_INSN(0x{address:x}, {mnemonic}, {quote(operands)}, {quote(ins['bytes'])})")
    output = ROOT / "mac/OLMSmoother/Mac" / filename
    output.write_text("\n".join(lines) + "\n")
    print(filename, len(by_address))


def main():
    for spec in SPECS:
        generate(*spec)


if __name__ == "__main__":
    main()
