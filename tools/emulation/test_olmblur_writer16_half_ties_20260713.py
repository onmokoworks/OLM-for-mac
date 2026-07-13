#!/usr/bin/env python3
"""Execute the actual OLMBlur PF16 writer on controlled half ties."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_XMM6

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
ENTRY = 0x1800030E2
STOP = 0x180003123
VALUES = (1100.5, 1101.5, 32767.5)


def run() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    source = loader.bump_alloc(12, align=16)
    output = loader.bump_alloc(8, align=16)
    loader.write_bytes(source, struct.pack("<3f", *VALUES))
    loader.write_bytes(output, struct.pack("<4H", 0x8000, 0xDEAD, 0xDEAD, 0xDEAD))

    loader.uc.reg_write(UC_X86_REG_RDI, source + 8)
    loader.uc.reg_write(UC_X86_REG_RBX, output)
    loader.uc.reg_write(
        UC_X86_REG_XMM6,
        int.from_bytes(struct.pack("<f", 0.5) + b"\0" * 12, "little"),
    )

    def stop(uc, address, size, user_data):
        if address == STOP:
            uc.emu_stop()

    loader.uc.hook_add(UC_HOOK_CODE, stop, begin=STOP, end=STOP)
    result = loader.call_function(ENTRY, max_instructions=1000)
    words = struct.unpack("<4H", loader.read_bytes(output, 8))
    expected = tuple(int(value + 0.5) for value in VALUES)
    nearest_even = tuple(round(value) for value in VALUES)
    assert words[1:] == expected
    assert expected != nearest_even
    return {
        "schema": "olmblur.actual-aex-writer16-half-ties/1",
        "binary": str(AEX.relative_to(ROOT)),
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "entry": hex(ENTRY),
        "stop_before": hex(STOP),
        "input_raw_f32": list(VALUES),
        "stored_agrb16": list(words),
        "add_half_then_truncate_rgb": list(expected),
        "nearest_even_rgb": list(nearest_even),
        "instructions": result["instructions"],
        "status": "pass_actual_aex_distinguishes_half_ties",
        "scope": "writer semantics only; not AE or case conformance",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
