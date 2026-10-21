#!/usr/bin/env python3
"""Tamper-close tests for the Radial Strength-290 native UCRT request."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmradialblur_strength290_ucrt_math_request_20260814.py"
SCRIPT_SHA256 = "c9e7165abea6a1f7e273f99b4ea40c7f943d95ed3e180c5d90948cccc147ea7e"
SPEC = importlib.util.spec_from_file_location("radial_strength290_ucrt_request", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class Strength290UcrtRequestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.report = MOD.REPORT.read_bytes()
        self.note = MOD.NOTE.read_bytes()

    def tearDown(self) -> None:
        MOD.REPORT.write_bytes(self.report)
        MOD.NOTE.write_bytes(self.note)

    def temporary_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="radial-ucrt-request-tamper-")
        package = Path(temporary.name) / MOD.REQUEST_ID
        shutil.copytree(MOD.PACKAGE, package)
        zip_path = Path(temporary.name) / (MOD.REQUEST_ID + ".zip")
        shutil.copy2(MOD.PACKAGE_ZIP, zip_path)
        return temporary, package, zip_path

    def package_tamper(self, mutate) -> None:
        temporary, package, zip_path = self.temporary_package()
        try:
            mutate(package)
            with mock.patch.object(MOD, "PACKAGE", package), mock.patch.object(MOD, "PACKAGE_ZIP", zip_path):
                with self.assertRaises(ValueError):
                    MOD.validate_package(live=False)
        finally:
            temporary.cleanup()

    def report_tamper(self, mutate) -> None:
        value = json.loads(self.report)
        mutate(value)
        MOD.REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            MOD.validate_persisted()

    def test_generator_identity_and_live_package(self) -> None:
        self.assertEqual(hashlib.sha256(SCRIPT.read_bytes()).hexdigest(), SCRIPT_SHA256)
        MOD.validate_package()
        MOD.validate_persisted()

    def test_windows_script_hash_checks_dependencies_before_native_load(self) -> None:
        ps = MOD.powershell()
        expected = MOD.file_payloads()
        for name, variable in (
            ("UcrtRadialMathCapture.cs", "$expectedCsharpSha256"),
            ("math_vectors.json", "$expectedVectorsSha256"),
            ("request_manifest.json", "$expectedManifestSha256"),
        ):
            sha = hashlib.sha256(expected[name]).hexdigest()
            self.assertIn(f'{variable} = "{sha}"', ps)
        self.assertLess(ps.index('throw "Exact 577-vector table SHA-256 mismatch"'),
                        ps.index("Add-Type -LiteralPath $csharpPath"))

    def test_exact_system32_module_is_loaded_and_verified(self) -> None:
        cs = MOD.csharp()
        ps = MOD.powershell()
        self.assertIn("LoadLibraryEx(absoluteSystem32Path", cs)
        self.assertIn("GetModuleFileName(module", cs)
        self.assertNotIn('DllImport("ucrtbase.dll"', cs)
        self.assertIn("[UcrtRadialMathCapture]::Initialize($ucrtPath)", ps)
        self.assertIn("[StringComparison]::OrdinalIgnoreCase", ps)
        self.assertIn('throw "Loaded UCRT identity mismatch"', ps)

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = {
            path: path.read_bytes() for path in (*[MOD.PACKAGE / name for name in MOD.FILES],
                                                 MOD.PACKAGE_ZIP, MOD.REPORT, MOD.NOTE)
        }
        for args in ([], ["--validate-only"]):
            run = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_vector_one_away_rejected(self) -> None:
        def mutate(package: Path) -> None:
            path = package / "math_vectors.json"
            rows = json.loads(path.read_text())
            rows[0]["argument_bits"] = "0x4f800001"
            path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
        self.package_tamper(mutate)

    def test_vector_removal_rejected(self) -> None:
        def mutate(package: Path) -> None:
            path = package / "math_vectors.json"
            rows = json.loads(path.read_text())
            path.write_text(json.dumps(rows[:-1], indent=2, sort_keys=True) + "\n")
        self.package_tamper(mutate)

    def test_manifest_overclaim_rejected(self) -> None:
        def mutate(package: Path) -> None:
            path = package / "request_manifest.json"
            value = json.loads(path.read_text())
            value["claims_not_made"] = []
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        self.package_tamper(mutate)

    def test_csharp_symbol_tamper_rejected(self) -> None:
        self.package_tamper(lambda package: (package / "UcrtRadialMathCapture.cs").write_text(
            (package / "UcrtRadialMathCapture.cs").read_text().replace(
                'GetProcAddress(module, "atan2f")', 'GetProcAddress(module, "atan2")')))

    def test_powershell_host_launch_tamper_rejected(self) -> None:
        self.package_tamper(lambda package: (package / "run_olmradialblur_strength290_ucrt_math.ps1").write_text(
            (package / "run_olmradialblur_strength290_ucrt_math.ps1").read_text() + "\nStart-Process AfterFX.exe\n"))

    def test_zip_content_tamper_rejected(self) -> None:
        temporary, package, zip_path = self.temporary_package()
        try:
            raw = bytearray(zip_path.read_bytes())
            raw[-1] ^= 1
            zip_path.write_bytes(raw)
            with mock.patch.object(MOD, "PACKAGE", package), mock.patch.object(MOD, "PACKAGE_ZIP", zip_path):
                with self.assertRaises((ValueError, OSError)):
                    MOD.validate_package(live=False)
        finally:
            temporary.cleanup()

    def test_native_return_false_claim_rejected(self) -> None:
        self.report_tamper(lambda value: value["boundary"].__setitem__("native_return_included", True))

    def test_promotion_false_claim_rejected(self) -> None:
        self.report_tamper(lambda value: value["boundary"].__setitem__("production_admission_changed", True))


if __name__ == "__main__":
    unittest.main()
