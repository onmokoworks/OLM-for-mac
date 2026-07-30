#!/usr/bin/env python3
"""AE-free static contract for DistanceGradation typed compose dispatch."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASM = ROOT / "disasm" / "DistanceGradation.aex.asm.txt"


def function_block(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def assert_dispatch_contract(classic: str, pf8: str, pf16: str, smart: str) -> None:
    # Classic Render selects from the world depth word at +0x2c.
    assert "181173d58  MOVZX ECX,word ptr [RAX + 0x2c]" in classic
    assert "181173d5e  CMP CX,0x8" in classic
    assert "181173e14  CALL 0x181170380" in classic
    assert "181173e1e  CMP CX,0x10" in classic
    assert "181173ed4  CALL 0x181170280" in classic
    assert "181173ede  CMP CX,0x20" in classic
    assert "181173f6d  CALL 0x181172a10" in classic
    assert "181173ffc  LEA RCX,[0x181170c90]" in classic

    # The typed iterate wrappers install the expected per-pixel callbacks.
    assert "181170428  LEA RCX,[0x181170870]" in pf8
    assert "181170328  LEA RCX,[0x181170480]" in pf16

    # Smart Render's request flag bit 0 chooses PF16 when set, PF8 when clear.
    assert "181174db6  TEST byte ptr [R9 + 0x10],0x1" in smart
    assert "181174dbb  JZ 0x181174dfd" in smart
    assert "181174df1  CALL 0x181170280" in smart
    assert "181174e31  CALL 0x181170380" in smart


def blocks() -> tuple[str, str, str, str]:
    text = ASM.read_text(encoding="utf-8")
    classic = function_block(
        text,
        "; === FUN_181173d20 @ 181173d20 ===",
        "; === FUN_181174060 @ 181174060 ===",
    )
    pf16 = function_block(
        text,
        "; === FUN_181170280 @ 181170280 ===",
        "; === FUN_181170380 @ 181170380 ===",
    )
    pf8 = function_block(
        text,
        "; === FUN_181170380 @ 181170380 ===",
        "; === FUN_181170480 @ 181170480 ===",
    )
    smart = function_block(
        text,
        "181174da9  MOV R8,qword ptr [R10]",
        "181174e3d  MOV RDX,R14",
    )
    return classic, pf8, pf16, smart


class DistanceGradationStaticDispatchContractTest(unittest.TestCase):
    def test_distancegradation_static_dispatch_contract(self) -> None:
        assert_dispatch_contract(*blocks())

    def test_adversarial_dispatch_mutations_fail(self) -> None:
        mutations = [
            (0, "181173e14  CALL 0x181170380", "181173e14  CALL 0x181170280"),
            (2, "181170328  LEA RCX,[0x181170480]", "181170328  LEA RCX,[0x181170870]"),
            (3, "181174dbb  JZ 0x181174dfd", "181174dbb  JNZ 0x181174dfd"),
        ]
        for block_index, old, new in mutations:
            with self.subTest(old=old, new=new):
                mutated = list(blocks())
                self.assertIn(old, mutated[block_index])
                mutated[block_index] = mutated[block_index].replace(old, new, 1)
                with self.assertRaises(AssertionError):
                    assert_dispatch_contract(*mutated)


if __name__ == "__main__":
    unittest.main()
