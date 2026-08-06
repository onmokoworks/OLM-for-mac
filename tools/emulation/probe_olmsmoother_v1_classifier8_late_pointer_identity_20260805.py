#!/usr/bin/env python3
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_R9,
    UC_X86_REG_R11,
    UC_X86_REG_R13,
    UC_X86_REG_R15,
    UC_X86_REG_RAX,
    UC_X86_REG_RBP,
    UC_X86_REG_RBX,
    UC_X86_REG_RDI,
    UC_X86_REG_RSI,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
OUT = ROOT / "refs/conformance/olmsmoother_v1_classifier8_late_pointer_identity_20260805.json"
ENTRY = 0x180008060
LATE = 0x180009388
EARLY = 0x1800087F0
DIRECTIONS = (5, 3, 1, 7)


def rotate_clockwise(values):
    return [values[6], values[3], values[0], values[7], values[4], values[1], values[8], values[5], values[2]]


def ptr_index(pointer, pointers):
    try:
        return pointers.index(pointer)
    except ValueError:
        return None


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA256
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    state = loader.host_alloc(64, align=16)
    pixels = [loader.host_alloc(4, align=4) for _ in range(9)]
    neighbors = loader.host_alloc(72, align=16)
    loader.write_bytes(neighbors, struct.pack("<9Q", *pixels))
    current = {}
    hits = []

    def hook(uc, address, size, user_data):
        regs = {
            "rbx": uc.reg_read(UC_X86_REG_RBX),
            "r15": uc.reg_read(UC_X86_REG_R15),
            "r9": uc.reg_read(UC_X86_REG_R9),
            "rbp": uc.reg_read(UC_X86_REG_RBP),
            "rsi": uc.reg_read(UC_X86_REG_RSI),
            "r11": uc.reg_read(UC_X86_REG_R11),
            "r13": uc.reg_read(UC_X86_REG_R13),
            "rax": uc.reg_read(UC_X86_REG_RAX),
            "rdi": uc.reg_read(UC_X86_REG_RDI),
        }
        hits.append({
            **current,
            "boundary": hex(address),
            "pointer_indices": {name: ptr_index(value, pixels) for name, value in regs.items()},
            "registers": {name: hex(value) for name, value in regs.items()},
        })

    loader.uc.hook_add(UC_HOOK_CODE, hook, begin=EARLY, end=EARLY)
    loader.uc.hook_add(UC_HOOK_CODE, hook, begin=LATE, end=LATE)
    base = [0, 0, 0, 0, 0, 1, 1, 1, 1]
    fixtures = []
    rotated = base
    for rotation in range(4):
        fixtures.append((f"binary_rotation_{rotation}", list(rotated)))
        rotated = rotate_clockwise(rotated)
    # Non-binary colors ensure pointer identity is not inferred only from equal values.
    fixtures.append(("distinct_channels", list(range(9))))

    calls = []
    for fixture_name, values in fixtures:
        words = [[255, value * 17, value * 7, value * 3] for value in values]
        for pointer, word in zip(pixels, words):
            loader.write_bytes(pointer, bytes(word))
        for tolerance in (0, 1, 6, 254):
            loader.write_bytes(state, b"\0" * 64)
            loader.write_bytes(state + 8, struct.pack("<i", tolerance))
            for direction in DIRECTIONS:
                current.clear()
                current.update(fixture=fixture_name, values=values, tolerance=tolerance, direction=direction)
                before = len(hits)
                result = loader.call_function(ENTRY, [state, 464, 170, neighbors, direction], max_instructions=100000)["rax"]
                calls.append({**current, "result": result, "late_hit": len(hits) != before})

    report = {
        "schema_version": 1,
        "status": "captured",
        "actual_aex_sha256": SHA256,
        "entry": hex(ENTRY),
        "late_boundary": hex(LATE),
        "calls": calls,
        "late_hits": hits,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
