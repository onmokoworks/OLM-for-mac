from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASM = (ROOT / "disasm/OLMKiraKira.aex.asm.txt").read_text(encoding="utf-8")


def body(start: str, end: str) -> str:
    left = ASM.index(start)
    return ASM[left:ASM.index(end, left)]


class Merge2OuterComposeStaticTests(unittest.TestCase):
 def test_depth_owners_bind_ray_output_to_compose_and_typed_writer(self) -> None:
    pf8_owner = body("; === FUN_18114d220", "; === FUN_18114d7f0")
    pf32_owner = body("; === FUN_18114d7f0", "; === FUN_18114ddc0")
    pf16_compose = body("; === FUN_18114ddc0", "; === FUN_18114e110")
    pf8_compose = body("; === FUN_18114e110", "; === FUN_18114e460")
    pf32_compose = body("; === FUN_18114e460", "; === FUN_18114e7b0")

    self.assertIn("18114d62c  CALL 0x18114f4a0", pf8_owner)
    self.assertIn("18114d73d  CALL 0x18114e110", pf8_owner)
    self.assertIn("18114dbfc  CALL 0x18114f4a0", pf32_owner)
    self.assertIn("18114dd0d  CALL 0x18114e460", pf32_owner)
    self.assertIn("CALL 0x181230bd0", pf16_compose)
    self.assertIn("CALL 0x181230b90", pf8_compose)
    self.assertIn("CALL 0x181230c20", pf32_compose)


 def test_outer_compose_has_two_exact_modes_and_no_screen_formula(self) -> None:
    for start, end in (
        ("; === FUN_18114ddc0", "; === FUN_18114e110"),
        ("; === FUN_18114e110", "; === FUN_18114e460"),
        ("; === FUN_18114e460", "; === FUN_18114e7b0"),
    ):
        compose = body(start, end)
        # state +0x44 selects mode 1 or 2; other values return without pixels.
        self.assertIn("MOV ECX,dword ptr [RCX + 0x44]", compose)
        self.assertIn("SUB ECX,0x1", compose)
        self.assertIn("CMP ECX,0x1", compose)
        # Mode 1 normalizes RGB by the summed, opacity-scaled alpha.
        self.assertIn("DIVSS", compose)
        # Mode 2 is the other branch and never divides/normalizes RGB.
        mode2 = compose[compose.index("CMP ECX,0x1"):compose.index("DIVSS")]
        self.assertNotIn("DIVSS", mode2)
        # Neither branch contains the screen identity's subtract/multiply shape.
        self.assertNotIn("SUBSS", compose)


 def test_float_rgba_layout_and_writer_call_register_contract(self) -> None:
    compose = body("; === FUN_18114e460", "; === FUN_18114e7b0")
    # Both source and glow advance by one interleaved float RGBA pixel.
    self.assertEqual(compose.count("ADD RDI,0x10"), 2)
    self.assertEqual(compose.count("ADD RBX,0x10"), 2)
    # Writer ABI: R,G,B,A in XMM0..3; destination is stack arg 5.
    for callsite in ("18114e5d7", "18114e739"):
        window = compose[compose.index(callsite) - 180:compose.index(callsite) + 40]
        self.assertIn("MOVAPS XMM3,XMM0", window)
        self.assertIn("MOVAPS XMM0", window)
        self.assertIn("MOVAPS XMM2", window)
        self.assertIn("MOVAPS XMM1", window)
        self.assertIn("MOV qword ptr [RSP + 0x20],RBP", window)
        self.assertIn("CALL 0x181230c20", window)


if __name__ == "__main__":
    unittest.main()
