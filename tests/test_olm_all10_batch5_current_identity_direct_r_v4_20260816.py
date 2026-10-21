import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_batch5_current_identity_direct_r_v4_20260816.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("olm_batch5_direct_r_v4", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch5DirectRV4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_runner()
        cls.source = RUNNER.read_text(encoding="utf-8")

    def test_default_is_read_only_and_state_aware(self):
        before = {path: path.exists() for path in (
            self.runner.RAW, self.runner.SUMMARY,
            self.runner.ARTIFACT_DIR, self.runner.INVOCATION_RECEIPT,
        )}
        value = subprocess.run([sys.executable, str(RUNNER)], capture_output=True, text=True)
        report = json.loads(value.stdout)
        self.assertEqual(report["launch_mode"], "direct_executable_dash_r")
        self.assertEqual(report["plugin_count"], 10)
        self.assertEqual(report["ae_pids"], [])
        expected_ready = all(not exists for exists in before.values())
        self.assertEqual(value.returncode, 0 if expected_ready else 1)
        self.assertEqual(report["status"], "ready_no_ae" if expected_ready else "blocked")
        self.assertEqual(report["reserved_outputs_absent"], expected_ready)
        self.assertEqual(before, {path: path.exists() for path in before})

    def test_launch_path_bypasses_apple_events(self):
        self.assertIn('[str(EXECUTABLE), "-r", str(launch_wrapper)]', self.source)
        self.assertNotIn('["open", "-a", "Adobe After Effects 2026"]', self.source)
        self.assertNotIn('["osascript", "-e", apple_script]', self.source)
        self.assertIn('"mode": "direct_executable_dash_r"', self.source)

    def test_exact_batch5_identity_and_policy(self):
        manifest, identities = self.runner.verify_identity()
        self.assertEqual(len(identities), 10)
        self.assertEqual(self.runner.ENABLED_HOST_FRAME_PLUGINS,
                         {"OLMBlur", "OLMDirectionalBlur"})
        self.assertEqual(self.runner.PAYLOAD.name,
                         "ae_host_all10_batch5_current_identity_live_v3_20260815.jsx")
        self.assertEqual(self.runner.sha256(self.runner.IDENTITY),
                         "ede4857b810e9f2901561ee8a3a9179c4c508dc2ee058525aa3f46dff4164079")
        self.assertIn("accepted_at", manifest)

    def test_one_shot_paths_are_versioned_and_fixed(self):
        self.assertEqual(self.runner.RAW.parent, ROOT / "refs/conformance")
        self.assertEqual(self.runner.SUMMARY.parent, ROOT / "refs/conformance")
        self.assertEqual(self.runner.ARTIFACT_DIR.parent, ROOT / "handoffs")
        self.assertIn("direct_r_v4", self.runner.RAW.name)
        self.assertIn("direct_r_v4", self.runner.SUMMARY.name)
        self.assertIn("direct_r_v4", self.runner.ARTIFACT_DIR.name)
        self.assertIn("os.O_EXCL", self.source)

    def test_preserved_failure_is_startup_modal_not_plugin_claim(self):
        report_path = ROOT / "refs/conformance/olm_all10_batch5_direct_r_v4_startup_modal_failure_20260816.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "fail_closed_no_retry")
        self.assertEqual(report["attempt"]["plugin_rows"], 0)
        self.assertIsNone(report["attempt"]["plugin_execution_reached"])
        self.assertFalse(report["attempt"]["retry_performed"])
        self.assertEqual(report["post_cleanup"]["after_effects_or_aerender_processes"], [])
        self.assertIn("CEggApp::BirthPrefs",
                      report["artifacts"]["macos_incident"]["key_frames"])
        for artifact in report["artifacts"].values():
            path = ROOT / artifact["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"])


if __name__ == "__main__":
    unittest.main()
