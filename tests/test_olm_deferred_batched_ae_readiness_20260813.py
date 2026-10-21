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
AUDITOR = ROOT / "tools/emulation/audit_olm_deferred_batched_ae_readiness_20260813.py"
REPORT = ROOT / "refs/conformance/olm_deferred_batched_ae_readiness_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_deferred_batched_ae_readiness_20260813.md"
AUDITOR_SHA256 = "ac8c96ddf4466e1163b552ca4879339e38f5fdfab9870c99a5f72278eddf3102"
REPORT_SHA256 = "2629881d49d75ef752b6fc6280225bfd515b03be03b642bb57f9d68641783c0b"
MARKDOWN_SHA256 = "48e63ff52b7dc9349d90df931f0f6049d03b7cda41baf06959f2f86b15c3449f"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_auditor():
    spec = importlib.util.spec_from_file_location("deferred_ae_readiness", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class DeferredBatchedAeReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_auditor()
        cls.report = json.loads(REPORT.read_text())

    def test_default_read_only_live(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS_DEFERRED_BATCHED_AE_READINESS_NO_LAUNCH", run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_no_launch_and_pending_boundary(self) -> None:
        self.assertFalse(self.report["scope"]["after_effects_launch_authorized"])
        self.assertFalse(self.report["scope"]["after_effects_launched"])
        self.assertTrue(self.report["scope"]["future_checkpoint_must_be_single_batched_run"])
        self.assertTrue(self.report["scope"]["future_checkpoint_requires_new_host_automation_authority"])
        self.assertFalse(self.report["host_automation"]["available"])
        self.assertEqual(self.report["host_automation"]["blocked_command"], "DoScriptFile")
        self.assertFalse(self.report["host_automation"]["payload_observed"])
        self.assertTrue(self.report["host_automation"]["current_runner_execution_forbidden"])
        self.assertFalse(self.report["host_automation"]["current_runner_state"]["dependency_valid"])
        self.assertFalse(self.report["host_automation"]["current_runner_state"]["after_effects_reached"])
        v3 = self.report["host_automation"]["v3_hostless_state"]
        self.assertTrue(v3["contract_valid"])
        self.assertTrue(v3["current_identity_valid"])
        self.assertTrue(v3["future_outputs_absent"])
        self.assertFalse(v3["live_entrypoint_present"])
        self.assertFalse(v3["after_effects_reached"])
        plugin = self.report["host_automation"]["scripting_plugin_on_disk"]
        self.assertTrue(plugin["on_disk_present"])
        self.assertEqual(set(plugin["architectures"]), {"arm64", "x86_64"})
        self.assertTrue(plugin["codesign_deep_strict_valid"])
        self.assertIn("not a causal proof", self.report["host_automation"]["runtime_load_or_registration_status"])
        self.assertTrue(plugin["loader_log"]["marked_ignore"])
        self.assertFalse(plugin["loader_log"]["loaded"])
        self.assertEqual(self.report["host_automation"]["historical_success_control"]["status"], "pass")
        self.assertEqual(self.report["host_automation"]["historical_success_control"]["script_invocation_returncode"], 0)
        self.assertIn("separate reviewed change", self.report["host_automation"]["next_required_host_action"])
        self.assertEqual(self.report["preflight"]["after_effects"], [])
        self.assertEqual(self.report["release_boundary"]["saved_status"], "release_gate_pending_or_invalid")
        self.assertFalse(self.report["release_boundary"]["releasable"])

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(AUDITOR), AUDITOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_unknown_key_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)

    def test_claim_escalation_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["scope"]["after_effects_launched"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["release_boundary"]["releasable"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["host_automation"]["available"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)

    def test_preflight_tamper_rejected(self) -> None:
        for key, value in (("passes", 1), ("bundle_count", 9), ("returncode", 0), ("byte_identical", False)):
            changed = copy.deepcopy(self.report)
            changed["preflight"][key] = value
            with self.assertRaises(RuntimeError):
                self.audit.validate_schema(changed)


if __name__ == "__main__":
    unittest.main()
