from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olm_all10_hostless_fixed_fixture_batch_20260814.py"
SPEC = importlib.util.spec_from_file_location("all10_hostless_batch", TOOL)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class AllTenHostlessBatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.log_bytes = MOD.LOG.read_bytes()
        cls.report = json.loads(MOD.REPORT.read_text(encoding="utf-8"))

    def test_live_report_validates(self) -> None:
        MOD.validate_report(self.report, self.log_bytes)

    def test_runner_identity_is_live(self) -> None:
        self.assertEqual(MOD.sha256_bytes(MOD.RUNNER.read_bytes()), MOD.EXPECTED_RUNNER_SHA256)

    def test_log_tamper_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            MOD.validate_report(self.report, self.log_bytes + b"\n")

    def test_scope_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["scope"]["native_ae_claim"] = True
        with self.assertRaises(AssertionError):
            MOD.validate_report(changed, self.log_bytes)

    def test_unknown_key_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(AssertionError):
            MOD.validate_report(changed, self.log_bytes)


if __name__ == "__main__":
    unittest.main()
