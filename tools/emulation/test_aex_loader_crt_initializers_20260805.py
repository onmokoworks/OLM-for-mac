#!/usr/bin/env python3
"""Synthetic focused test for AexLoader's opt-in MS CRT walkers."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RSP


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"


def callback_code(address: int, counter: int, return_value: int) -> bytes:
    # inc qword ptr [rip+disp32]; mov eax,imm32; ret
    displacement = counter - (address + 7)
    return b"\x48\xff\x05" + struct.pack("<i", displacement) + b"\xb8" + struct.pack("<I", return_value) + b"\xc3"


def main() -> int:
    loader = AexLoader(str(AEX), fast=True)
    assert "_initterm" not in loader.import_impls
    loader.enable_crt_initializer_imports()

    code1, code2 = 0x180001000, 0x180001020
    counter1, counter2 = 0x1818C4000, 0x1818C4008
    slots = 0x1818C4020
    loader.write_bytes(code1, callback_code(code1, counter1, 0))
    loader.write_bytes(code2, callback_code(code2, counter2, 5))
    loader.write_bytes(counter1, b"\0" * 16)
    loader.write_bytes(slots, struct.pack("<4Q", code1, 0, code2, code1))

    loader.uc.reg_write(UC_X86_REG_RBX, 0x1122334455667788)
    loader.uc.reg_write(UC_X86_REG_RSP, 0x0F080000)
    stack_witness = 0x0F07FF00
    loader.write_bytes(stack_witness, b"outer-stack-witness")
    result = loader.import_impls["_initterm"](loader.uc, [slots, slots + 32, 0, 0])
    assert result == 0
    assert struct.unpack("<Q", loader.read_bytes(counter1, 8))[0] == 2
    assert struct.unpack("<Q", loader.read_bytes(counter2, 8))[0] == 1
    assert loader.uc.reg_read(UC_X86_REG_RBX) == 0x1122334455667788
    assert loader.uc.reg_read(UC_X86_REG_RSP) == 0x0F080000
    assert loader.read_bytes(stack_witness, len(b"outer-stack-witness")) == b"outer-stack-witness"

    loader.write_bytes(counter1, b"\0" * 16)
    loader.write_bytes(slots, struct.pack("<3Q", code2, code1, code1))
    result = loader.import_impls["_initterm_e"](loader.uc, [slots, slots + 24, 0, 0])
    assert result == 5
    assert struct.unpack("<Q", loader.read_bytes(counter1, 8))[0] == 0
    assert struct.unpack("<Q", loader.read_bytes(counter2, 8))[0] == 1

    for begin, end in ((slots + 1, slots + 8), (slots + 16, slots), (0, 8)):
        try:
            loader.import_impls["_initterm"](loader.uc, [begin, end, 0, 0])
        except ValueError:
            pass
        else:
            raise AssertionError("invalid CRT range accepted")
    loader.write_bytes(slots, struct.pack("<Q", 0x20000000))
    try:
        loader.import_impls["_initterm"](loader.uc, [slots, slots + 8, 0, 0])
    except ValueError:
        pass
    else:
        raise AssertionError("non-executable CRT callback accepted")

    loader.write_bytes(slots, struct.pack("<Q", code1))
    original_call = loader.call_function
    def recursive_call(_target, *args, **kwargs):
        return loader.import_impls["_initterm"](loader.uc, [slots, slots + 8, 0, 0])
    loader.call_function = recursive_call  # type: ignore[method-assign]
    try:
        loader.import_impls["_initterm"](loader.uc, [slots, slots + 8, 0, 0])
    except RuntimeError as exc:
        assert "reentrant" in str(exc)
    else:
        raise AssertionError("reentrant CRT walk accepted")
    finally:
        loader.call_function = original_call  # type: ignore[method-assign]
    print("PASS_AEX_LOADER_CRT_INITIALIZERS_20260805")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
