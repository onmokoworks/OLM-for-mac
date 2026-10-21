#!/usr/bin/env python3
"""Tamper-close tests for the RadialBlur Type-1 inverse-cell closure."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.py"
SPEC = importlib.util.spec_from_file_location("radial_type1_inverse_closure", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ClosureTamper(unittest.TestCase):
    def setUp(self) -> None:
        self.report = MOD.REPORT.read_bytes()
        self.doc = MOD.DOC.read_bytes()

    def tearDown(self) -> None:
        MOD.REPORT.write_bytes(self.report)
        MOD.DOC.write_bytes(self.doc)

    def tamper(self, mutate) -> None:
        value = json.loads(self.report)
        mutate(value)
        MOD.REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        with self.assertRaises(RuntimeError):
            MOD.validate_report()

    def test_checked_in_report_validates(self) -> None:
        MOD.validate_report()

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = (MOD.REPORT.read_bytes(), MOD.DOC.read_bytes())
        for args in ([], ["--validate-only"]):
            run = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((MOD.REPORT.read_bytes(), MOD.DOC.read_bytes()), before)

    def test_schema_tamper(self) -> None:
        self.tamper(lambda value: value.__setitem__("schema", "forged"))

    def test_98_cell_matrix_tamper(self) -> None:
        self.tamper(lambda value: value["cells"].pop())

    def test_exact_five_flag_count_tamper(self) -> None:
        self.tamper(lambda value: value["flag_counts"].__setitem__("pairwise", 9))

    def test_selector_hash_tamper(self) -> None:
        self.tamper(lambda value: value["selector_contract"].__setitem__(
            "canonical_compact_sha256", "0" * 64))

    def test_production_source_identity_tamper(self) -> None:
        self.tamper(lambda value: value.__setitem__("production_source_sha256", "0" * 64))

    def test_fresh_integration_verification_tamper(self) -> None:
        self.tamper(lambda value: value["fresh_integration_verification"].__setitem__(
            "different_bytes", 1))

    def test_per_family_planes_tamper(self) -> None:
        self.tamper(lambda value: value["fresh_integration_verification"]["per_family"]
                    ["pairwise"]["raw_exact_planes"].append("prepass_alpha"))

    def test_core_sampler_identity_tamper(self) -> None:
        self.tamper(lambda value: value["core_sampler_source"].__setitem__(
            "sha256", "0" * 64))

    def test_universal_build_tamper(self) -> None:
        self.tamper(lambda value: value["fresh_integration_verification"]
                    ["isolated_universal_build"].__setitem__(
                        "universal_binary_sha256", "0" * 64))

    def test_unsigned_build_boundary_tamper(self) -> None:
        self.tamper(lambda value: value["fresh_integration_verification"]
                    ["isolated_universal_build"]["codesign"].__setitem__(
                        "type", "Developer ID"))

    def test_core_sampler_file_tamper_without_editing_source(self) -> None:
        source = MOD.NOISE_HEADER.read_text()
        forged = source.replace("1.0f / plane.cell_size", "plane.cell_size / 1.0f", 1)
        with tempfile.TemporaryDirectory(prefix="radial-core-sampler-tamper-") as raw:
            path = Path(raw) / "dblur_noise.h"
            path.write_text(forged)
            with mock.patch.object(MOD, "NOISE_HEADER", path):
                with self.assertRaises(RuntimeError):
                    MOD.core_sampler_contract()

    def test_type2_type3_control_tamper(self) -> None:
        self.tamper(lambda value: value["controls"].__setitem__("type2", {}))

    def test_strength290_boundary_tamper(self) -> None:
        self.tamper(lambda value: value["controls"].__setitem__(
            "strength290", "publicly admitted"))

    def test_owner_provenance_tamper(self) -> None:
        self.tamper(lambda value: value.__setitem__("owner_provenance", {}))

    def test_supersession_tamper(self) -> None:
        self.tamper(lambda value: value.__setitem__(
            "supersedes_stale_inactive_only_wording", []))

    def test_markdown_tamper(self) -> None:
        MOD.DOC.write_text("forged\n")
        with self.assertRaises(RuntimeError):
            MOD.validate_report()

    def test_production_selector_broadening_is_rejected_without_editing_source(self) -> None:
        source = MOD.SOURCE.read_text()
        needle = "use_aex_typed_rotation_size_noise_components_32x18);"
        self.assertIn(needle, source)
        forged = source.replace(
            needle,
            "use_aex_typed_rotation_size_noise_components_32x18 || "
            "use_aex_typed_rotation_offset_noise_components_32x18);",
            1,
        )
        with tempfile.TemporaryDirectory(prefix="radial-inverse-selector-tamper-") as raw:
            path = Path(raw) / "OLMRadialBlur.cpp"
            path.write_text(forged)
            with mock.patch.object(MOD, "SOURCE", path):
                with self.assertRaises(RuntimeError):
                    MOD.selector_contract()

    def test_production_sampler_disconnect_is_rejected_without_editing_source(self) -> None:
        source = MOD.SOURCE.read_text()
        needle = "use_aex_rotation_type1_inverse_cell_32x18)"
        self.assertIn(needle, source)
        forged = source.replace(needle, "use_aex_rotation_type1_inverse_cell_32x18 && false)", 1)
        with tempfile.TemporaryDirectory(prefix="radial-inverse-sampler-tamper-") as raw:
            path = Path(raw) / "OLMRadialBlur.cpp"
            path.write_text(forged)
            with mock.patch.object(MOD, "SOURCE", path):
                with self.assertRaises(RuntimeError):
                    MOD.selector_contract()


if __name__ == "__main__":
    unittest.main()
