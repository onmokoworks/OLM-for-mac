from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/discriminate_olmsmoother_v1_vs_smoother2_forced_v1_20260728.py"
SPEC = importlib.util.spec_from_file_location("smoother_v1_discriminator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SmootherV1DiscriminatorTests(unittest.TestCase):
    def test_premultiply_uses_pinned_nearest_rule_and_preserves_alpha(self) -> None:
        self.assertEqual(
            MODULE.premultiply_rgba(bytes([200, 200, 200, 135, 255, 1, 2, 0])),
            bytes([106, 106, 106, 135, 0, 0, 0, 0]),
        )

    def test_complete_parameter_mapping(self) -> None:
        case = {"effect": {"params": [
            {"name": "Use Color Key", "value": 0},
            {"name": "Color Key", "value": [1, 1, 1, 1]},
            {"name": "Do Smooth Range", "value": 6},
        ]}}
        mapped = MODULE.assignments(case)
        self.assertEqual(len(mapped["v1"]), 3)
        self.assertEqual(len(mapped["v2_forced_v1"]), 15)
        self.assertIn("Smoother Version@7=1", mapped["v2_forced_v1"])
        self.assertIn("Smooth Range@6=6", mapped["v2_forced_v1"])

    def test_diff_is_byte_exact(self) -> None:
        self.assertTrue(MODULE.diff(b"\x00\xff", b"\x00\xff")["exact"])
        result = MODULE.diff(b"\x00\xff", b"\x01\xfd")
        self.assertFalse(result["exact"])
        self.assertEqual(result["mismatched_bytes"], 2)
        self.assertEqual(result["max_abs_diff"], 2)

    def test_schema_does_not_call_decoded_png_a_raw_plane(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('"raw_pf8_rgba"', source)
        self.assertIn('"decoded_worker_png_rgba"', source)
        self.assertIn('"raw_pf8_argb_sha256"', source)
        self.assertNotIn('"byte_exact_equivalent_for_declared_inputs"', source)

    def test_raw_sha256_requires_strict_hex_and_normalizes_case(self) -> None:
        lower = "0123456789abcdef" * 4
        self.assertEqual(MODULE.normalize_sha256(lower.upper()), lower)
        for malformed in ("z" * 64, "a" * 63, "a" * 65):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    MODULE.normalize_sha256(malformed)


if __name__ == "__main__":
    unittest.main()
