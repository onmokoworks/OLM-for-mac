import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/emulation/audit_olm_all10_batch5_v3_one_shot_failure_20260815.py"
REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_one_shot_failure_metadata_20260815.json"

spec = importlib.util.spec_from_file_location("batch5_v3_failure_audit", AUDIT)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)


class Batch5V3OneShotFailureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_checked_report_revalidates_without_ae(self):
        proc = subprocess.run(
            [sys.executable, str(AUDIT)], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("no-retry", proc.stdout)

    def test_report_separates_protocol_from_startup_loader_evidence(self):
        audit.validate_report(self.report)
        self.assertEqual(self.report["attempt"]["raw_plugin_rows"], 0)
        self.assertFalse(self.report["classification"]["plugin_specific_runtime_observation_available"])
        self.assertTrue(self.report["host_breadcrumb"]["all10_no_loader_recognized_and_ignored"])
        self.assertIsNone(self.report["classification"]["effect_add_attempted"])
        self.assertIsNone(self.report["classification"]["render_attempted"])
        self.assertFalse(self.report["classification"]["numerical_behavior_assessed"])

    def test_retry_authorization_tamper_fails_closed(self):
        changed = copy.deepcopy(self.report)
        changed["attempt"]["retry_authorized"] = True
        with self.assertRaises(AssertionError):
            audit.validate_report(changed)

    def test_runtime_attribution_tamper_fails_closed(self):
        changed = copy.deepcopy(self.report)
        changed["classification"]["plugin_specific_runtime_observation_available"] = True
        with self.assertRaises(AssertionError):
            audit.validate_report(changed)

    def test_incomplete_loader_excerpt_fails_closed(self):
        text = audit.EXCERPT.read_text().replace(
            "No loaders recognized this plugin, so the plugin is set to Ignore.",
            "", 1,
        )
        with self.assertRaises(AssertionError):
            audit.validate_excerpt(text)


if __name__ == "__main__":
    unittest.main()
