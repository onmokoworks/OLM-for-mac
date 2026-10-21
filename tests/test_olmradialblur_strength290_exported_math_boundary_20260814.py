#!/usr/bin/env python3
"""Tamper-close tests for the Radial Strength-290 math boundary."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmradialblur_strength290_exported_math_boundary_20260814.py"
SCRIPT_SHA256 = "7af2816f7588ec71d33332c0a65be5bd639f54304c18f4144e47f0ceec7f8fd6"
SPEC = importlib.util.spec_from_file_location("radial_strength290_boundary", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class Strength290BoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.report = MOD.REPORT.read_bytes()
        self.markdown = MOD.MARKDOWN.read_bytes()

    def tearDown(self) -> None:
        MOD.REPORT.write_bytes(self.report)
        MOD.MARKDOWN.write_bytes(self.markdown)

    def tamper(self, mutate) -> None:
        value = json.loads(self.report)
        mutate(value)
        MOD.REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            MOD.validate_persisted()

    def test_generator_identity_and_persisted_report(self) -> None:
        self.assertEqual(hashlib.sha256(SCRIPT.read_bytes()).hexdigest(), SCRIPT_SHA256)
        MOD.validate_persisted()

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = (self.report, self.markdown)
        for args in ([], ["--validate-only"]):
            run = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((MOD.REPORT.read_bytes(), MOD.MARKDOWN.read_bytes()), before)

    def test_unknown_top_level_key_rejected(self) -> None:
        self.tamper(lambda value: value.__setitem__("forged", True))

    def test_false_promotion_rejected(self) -> None:
        self.tamper(lambda value: value["boundary"].__setitem__("production_admission_added", True))

    def test_native_ucrt_overclaim_rejected(self) -> None:
        self.tamper(lambda value: value["boundary"].__setitem__("native_windows_ucrt_capture_received", True))

    def test_exported_internal_pair_tamper_rejected(self) -> None:
        self.tamper(lambda value: value["owners"]["exported_smart_aexcompat_f32_math"].__setitem__(
            "output_sha256", value["owners"]["aex_internal_owner"]["output_sha256"]))

    def test_diff_histogram_tamper_rejected(self) -> None:
        self.tamper(lambda value: value["comparison"]["ulp_histogram"].__setitem__("1", 55))

    def test_source_identity_tamper_rejected(self) -> None:
        self.tamper(lambda value: value["fixture"].__setitem__("active_source_sha256", "0" * 64))

    def test_patch_identity_tamper_rejected(self) -> None:
        self.tamper(lambda value: value["identities"].__setitem__(
            "aexcompat_float_math_patch_sha256", "0" * 64))

    def test_call_census_tamper_rejected(self) -> None:
        self.tamper(lambda value: value["actual_exported_call_census"]["atan2f"].__setitem__(
            "unique_pairs", 575))

    def test_markdown_tamper_rejected(self) -> None:
        MOD.MARKDOWN.write_text("forged\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            MOD.validate_persisted()


if __name__ == "__main__":
    unittest.main()
