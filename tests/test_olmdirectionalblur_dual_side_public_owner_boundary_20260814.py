from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmdirectionalblur_dual_side_public_owner_boundary_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_dual_side_public_owner_boundary_20260814.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("dblur_dual_boundary", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalDualSidePublicOwnerBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.report = json.loads(REPORT.read_text())

    def test_saved_report_validates_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run(
            [sys.executable, str(GENERATOR), "--validate-only"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_exact_6_fail_closed_rows(self) -> None:
        self.assertTrue(self.generator.validate(self.report))
        self.assertEqual(len(self.report["rows"]), 6)
        self.assertEqual(self.report["boundary"]["arm64_public_exact_cells"], 15)
        self.assertEqual(self.report["boundary"]["x86_64_public_exact_cells"], 9)
        self.assertEqual({row["error"] for row in self.report["rows"]}, {516})
        self.assertEqual({row["error_symbol"] for row in self.report["rows"]}, {"PF_Err_BAD_CALLBACK_PARAM"})

    def test_recanonicalized_row_tamper_is_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["output_storage_unchanged"] = False
        changed["rows_sha256"] = self.generator.digest(changed["rows"])
        self.assertFalse(self.generator.validate(changed, live=False))

    def test_claim_and_identity_tamper_are_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["boundary"]["x86_64_public_exact_cells"] = 15
        self.assertFalse(self.generator.validate(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["identities"]["production_source_sha256"] = "0" * 64
        self.assertFalse(self.generator.validate(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        self.assertFalse(self.generator.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()
