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
GENERATOR = ROOT / "tools/emulation/test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("dblur_exported_smart", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalDualSideExportedSmartClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_pin_and_read_only_validation(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(GENERATOR), "--validate-only"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_arm64_and_x86_fifteen_boundary(self) -> None:
        self.assertTrue(self.generator.validate(self.report))
        self.assertEqual(len(self.report["exported_aex_rows"]), 15)
        self.assertEqual(len(self.report["mac_public_exact_rows"]), 30)
        self.assertEqual(self.report["summary"]["arm64_promoted_raw_exact"], 15)
        self.assertEqual(self.report["summary"]["x86_64_promoted_raw_exact"], 15)
        self.assertEqual(self.report["summary"]["x86_64_native_ucrt_promoted"], 6)
        self.assertEqual(self.report["summary"]["x86_64_remaining_fail_closed"], 0)

    def test_recanonicalized_row_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["mac_public_exact_rows"][0]["raw_sha256"] = "0" * 64
        changed["mac_public_exact_rows_sha256"] = self.generator.digest(changed["mac_public_exact_rows"])
        self.assertFalse(self.generator.validate(changed, live=False))

    def test_promotion_and_scope_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["exported_aex_rows"][0]["promoted_on_mac_arches"] = []
        changed["exported_aex_rows_sha256"] = self.generator.digest(changed["exported_aex_rows"])
        self.assertFalse(self.generator.validate(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["scope"]["native_windows_ucrt_capture"] = False
        self.assertFalse(self.generator.validate(changed, live=False))

    def test_identity_and_unknown_key_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["identities"]["worker_sha256"] = "0" * 64
        self.assertFalse(self.generator.validate(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        self.assertFalse(self.generator.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()
