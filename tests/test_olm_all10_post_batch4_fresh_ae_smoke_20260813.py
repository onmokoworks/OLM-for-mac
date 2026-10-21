import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_post_batch4_fresh_ae_smoke_20260813.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_post_toondilate_ded9_corrected_v2_20260813.jsx"
CONTRACT = ROOT / "refs/conformance/olm_all10_post_batch4_fresh_ae_smoke_contract_20260813.json"
RUNNER_SHA256 = "50a99fa42ce2470d8d63e3929cbcc2ff7c68fe0c34854d67841bbf1bf4a93e3b"
PAYLOAD_SHA256 = "e18b061acc71e62dfa0cbea3b65ad778343618d6db7fd427d74fbaf2427d4e64"
CONTRACT_SHA256 = "68091c803a3cdc25d930a1099123ae07c0b01ee064b138afeda3c405dec74a3b"

spec = importlib.util.spec_from_file_location("batch4_fresh_smoke", RUNNER)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class Batch4FreshAESmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(RUNNER.read_bytes()).hexdigest() == RUNNER_SHA256
        assert hashlib.sha256(PAYLOAD.read_bytes()).hexdigest() == PAYLOAD_SHA256
        assert hashlib.sha256(CONTRACT.read_bytes()).hexdigest() == CONTRACT_SHA256

    def test_default_is_read_only_ready_and_outputs_absent(self):
        self.assertEqual(mod.V.B.ae_pids(), [])
        self.assertTrue(mod.outputs_absent())
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (RUNNER, PAYLOAD, CONTRACT, mod.POST_INSTALL, mod.IDENTITY, mod.TRANSACTION)
        }
        run = subprocess.run(
            [sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        value = json.loads(run.stdout)
        self.assertEqual(value["status"], "attempt_failed_no_retry")
        self.assertTrue(value["outputs_absent"])
        self.assertEqual(value["contract"], mod.contract())
        self.assertEqual(
            before,
            {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before},
        )
        self.assertEqual(mod.V.B.ae_pids(), [])

    def test_current_batch_authority_is_exact(self):
        authority = mod.batch_authority()
        self.assertEqual(authority["batch_plugins"], [
            "OLMBlur", "OLMColorKey", "OLMSmoother", "OLMSmoother2"
        ])
        self.assertEqual(authority["enabled_generic_frame_plugins"], [
            "OLMBlur", "OLMDirectionalBlur"
        ])
        self.assertEqual(authority["numerical_assessment"], "not_assessed_by_ae_smoke")
        self.assertEqual(hashlib.sha256(mod.POST_INSTALL.read_bytes()).hexdigest(), mod.POST_INSTALL_SHA)
        self.assertEqual(hashlib.sha256(mod.IDENTITY.read_bytes()).hexdigest(), mod.IDENTITY_SHA)
        self.assertEqual(hashlib.sha256(mod.TRANSACTION.read_bytes()).hexdigest(), mod.TRANSACTION_SHA)
        self.assertEqual(hashlib.sha256(mod.FAILURE.read_bytes()).hexdigest(), mod.FAILURE_SHA)
        mod.V.B.verify_identity()

    def test_contract_is_closed_against_recanonicalized_tamper(self):
        self.assertTrue(mod.validate_contract(mod.contract()))
        mutations = (
            lambda x: x.update(extra=True),
            lambda x: x.update(status="AE_FORBIDDEN_DEFERRED_BATCH_CHECKPOINT"),
            lambda x: x["paths"].update(raw="wrong"),
            lambda x: x["batch4_post_install_authority"]["post_install"].update(sha256="0" * 64),
            lambda x: x["batch4_post_install_authority"]["accepted_identity"].update(path="wrong"),
            lambda x: x["batch4_post_install_authority"]["transaction"].update(sha256="0" * 64),
            lambda x: x["batch4_post_install_authority"]["batch_plugins"].reverse(),
            lambda x: x["batch4_post_install_authority"]["enabled_generic_frame_plugins"].append("OLMToonDilate"),
            lambda x: x["batch4_post_install_authority"].update(numerical_assessment="raw_exact"),
            lambda x: x["readiness"].update(consecutive_exact=1),
            lambda x: x["dependencies"]["v1_runner"].update(sha256="0" * 64),
            lambda x: x.update(claim_boundary="numerical exact"),
        )
        for mutate in mutations:
            value = copy.deepcopy(mod.contract())
            mutate(value)
            self.assertFalse(mod.validate_contract(value))

    def test_retry_is_code_forbidden_without_launch(self):
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("p.add_argument('--run',action='store_true')", text)
        self.assertIn("if not a.run:", text)
        self.assertIn("refusing retry after preserved one-shot readiness failure", text)
        self.assertNotIn("return V.execute_v2(a.timeout)", text)
        before_pids = mod.V.B.ae_pids()
        retry = subprocess.run(
            [sys.executable, str(RUNNER), "--run", "--timeout", "900"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertNotEqual(retry.returncode, 0)
        self.assertIn("refusing retry after preserved one-shot readiness failure", retry.stderr)
        self.assertTrue(mod.outputs_absent())
        self.assertEqual(mod.V.B.ae_pids(), before_pids)

    def test_preserved_failure_snapshot_and_scope(self):
        failure = json.loads(mod.FAILURE.read_text(encoding="utf-8"))
        self.assertEqual(set(failure), {
            "schema", "status", "captured_at", "attempt", "frozen_execution_authority",
            "canonical_output_observation", "post_failure_state", "release_audit", "claim_boundary",
        })
        self.assertEqual(failure["status"], "FAILURE_PRESERVED_NO_RETRY_RELEASE_GATE_BLOCKED")
        self.assertTrue(failure["attempt"]["one_shot"])
        self.assertFalse(failure["attempt"]["retry_authorized"])
        self.assertEqual(failure["attempt"]["failure_stage"], "pre_receipt_doscript_readiness")
        self.assertFalse(failure["attempt"]["payload_started"])
        self.assertEqual(failure["attempt"]["plugin_rows_observed"], 0)
        self.assertFalse(failure["attempt"]["numerical_behavior_assessed"])
        for name, row in failure["frozen_execution_authority"].items():
            if name == "launch_contract":
                self.assertEqual(row["attempt_sha256"], "1594a670830701eb4b700bd6e1b0aa5f4942f3dbcea7c1352bf4fd8955de6f57")
                continue
            path = ROOT / row["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"])
        self.assertTrue(all(failure["canonical_output_observation"][key] for key in (
            "raw_report_absent", "summary_absent", "artifact_dir_absent", "invocation_receipt_absent"
        )))
        self.assertEqual(failure["post_failure_state"]["after_effects_processes"], [])
        self.assertEqual(failure["release_audit"]["status"], "release_gate_pending_or_invalid")
        self.assertFalse(failure["release_audit"]["releasable"])


if __name__ == "__main__":
    unittest.main()
