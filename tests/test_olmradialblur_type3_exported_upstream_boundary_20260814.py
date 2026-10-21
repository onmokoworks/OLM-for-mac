from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmradialblur_type3_exported_upstream_boundary_20260814.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.json"
DOC = ROOT / "refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.md"


def load_generator():
    spec = importlib.util.spec_from_file_location("radial_type3_upstream", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RadialType3ExportedUpstreamBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.report = json.loads(REPORT.read_text())

    def test_default_is_read_only_and_exact(self) -> None:
        before = (REPORT.read_bytes(), DOC.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS_OLMRADIALBLUR_TYPE3_EXPORTED_UPSTREAM_STATIC_BOUNDARY", run.stdout)
        self.assertEqual((REPORT.read_bytes(), DOC.read_bytes()), before)

    def test_static_chain_and_policy(self) -> None:
        self.assertFalse(self.report["static_chain"]["initialized_before_materializer"])
        self.assertEqual(self.report["static_chain"]["fixed_copy_bytes"], 0x78)
        self.assertFalse(self.report["production_policy"]["windows_exported_type3_is_numerical_oracle"])
        self.assertTrue(self.report["production_policy"]["bounded_windows_typed_owner_retained"])
        self.assertTrue(self.report["production_policy"]["mac_public_45_row_admission_unchanged"])

    def test_unknown_and_policy_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)
        changed = copy.deepcopy(self.report)
        changed["production_policy"]["windows_exported_type3_is_numerical_oracle"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)

    def test_static_and_identity_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["static_chain"]["initialized_before_materializer"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)
        changed = copy.deepcopy(self.report)
        changed["identities"]["aex_sha256"] = "0" * 64
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)


if __name__ == "__main__":
    unittest.main()
