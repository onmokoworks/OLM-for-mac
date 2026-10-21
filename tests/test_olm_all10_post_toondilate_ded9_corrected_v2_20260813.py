import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_post_toondilate_ded9_corrected_v2_20260813.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_post_toondilate_ded9_corrected_v2_20260813.jsx"
CONTRACT = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_contract_20260813.json"
RUNNER_SHA256 = "484016105f3c82e68857b6924fdc88a937f8d811ad7fc92f688472cc0fb3c1d7"
CONTRACT_SHA256 = "8adaae1f6cce55889bad5eced7c3dc9a29a3bc4d81f19da9e1b0ac46fd60107c"

spec = importlib.util.spec_from_file_location("toon_v2", RUNNER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def result(stdout, stderr="", rc=0):
    return subprocess.CompletedProcess(["osascript"], rc, stdout, stderr)


class ToonCorrectedV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(RUNNER.read_bytes()).hexdigest() == RUNNER_SHA256
        assert hashlib.sha256(CONTRACT.read_bytes()).hexdigest() == CONTRACT_SHA256

    def test_default_is_read_only_and_ae_forbidden_contract(self):
        self.assertTrue(mod.outputs_absent())
        evidence = (mod.FAILURE1_RAW, mod.FAILURE1_SUMMARY, mod.FAILURE1_RECEIPT, mod.FAILURE2_RAW, mod.FAILURE2_SUMMARY, mod.FAILURE2_RECEIPT, mod.FAILURE2_METADATA, CONTRACT)
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence}
        run = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        value = json.loads(run.stdout)
        self.assertEqual(value["status"], "ready_read_only")
        self.assertTrue(value["outputs_absent"])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
        self.assertEqual(value["contract"]["status"], "AE_FORBIDDEN_DEFERRED_BATCH_CHECKPOINT")
        before_pids = mod.B.ae_pids()
        forbidden = subprocess.run([sys.executable, str(RUNNER), "--run"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(forbidden.returncode, 0)
        self.assertIn("AE forbidden: deferred batch checkpoint", forbidden.stderr)
        self.assertEqual(mod.B.ae_pids(), before_pids)
        self.assertTrue(mod.outputs_absent())
        bad_timeout = subprocess.run([sys.executable, str(RUNNER), "--run", "--timeout", "0"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(bad_timeout.returncode, 0)
        self.assertIn("--timeout must be positive", bad_timeout.stderr)
        self.assertEqual(mod.B.ae_pids(), before_pids)
        with self.assertRaisesRegex(RuntimeError, "AE forbidden"):
            mod.execute_v2(900)
        with self.assertRaisesRegex(RuntimeError, "AE forbidden"):
            mod._execute_v2_locked(900)
        self.assertEqual(mod.B.ae_pids(), before_pids)

    def test_exact_readiness_success_and_argv_transport(self):
        nonce = "ab" * 16
        expected = mod.readiness_stdout(nonce, 1)
        self.assertTrue(mod.exact_readiness_result(result(expected), [321], 321, nonce, 1))
        command = mod.readiness_probe_command(nonce, 1)
        self.assertEqual(command[:2], ["osascript", "-e"])
        self.assertEqual(command[-2], "--")
        self.assertIn(nonce, command[-1])
        self.assertIn("on run argv", command[2])

    def test_readiness_rejects_every_one_away(self):
        nonce = "cd" * 16
        good = mod.readiness_stdout(nonce, 2)
        bad = (
            result(good, rc=1), result(good, stderr="warning"), result(good.rstrip("\n")),
            result(good + "\n"), result("1\n"), result(good.replace(nonce, "ef" * 16)),
            result(good.replace('"version":"26.3x87"', '"version":"26.3x88"')),
            result(good.replace('"schema":"olm.ae-doscript-readiness/1"', '"schema":"wrong"')),
            result(good.replace('"probe_index":2', '"probe_index":3')),
            result(good[:-2] + ',"extra":true}\n'),
            result('{"ready":true,"schema":"olm.ae-doscript-readiness/1","status":"ok","version":"26.3.0","nonce":"' + nonce + '","probe_index":2}\n'),
        )
        for observed in bad:
            self.assertFalse(mod.exact_readiness_result(observed, [321], 321, nonce, 2))
        self.assertFalse(mod.exact_readiness_result(result(good), [321, 322], 321, nonce, 2))

    def test_consecutive_rule_resets_on_failure(self):
        self.assertTrue(mod.has_two_consecutive_exact([{"exact": True}, {"exact": True}]))
        self.assertFalse(mod.has_two_consecutive_exact([{"exact": True}, {"exact": False}, {"exact": True}]))
        self.assertFalse(mod.has_two_consecutive_exact([{"exact": False}, {"exact": True}]))
        self.assertFalse(mod.has_two_consecutive_exact([{"exact": True}]))

    def test_poll_producer_bytes_validate_in_consumer(self):
        seen = []
        def executor(command):
            js = command[-1]
            marker = 'nonce:"'
            nonce = js.split(marker, 1)[1].split('"', 1)[0]
            index = int(js.split('probe_index:', 1)[1].split('}', 1)[0])
            seen.append((nonce, index))
            return result(mod.readiness_stdout(nonce, index))
        ok, samples = mod.poll_readiness(321, executor, lambda: [321], timeout=1.0)
        self.assertTrue(ok)
        self.assertEqual(len(samples), 2)
        evidence = {
            "schema": mod.READINESS_SCHEMA, "same_fresh_pid": 321,
            "version_probe": {"sampled_at": "2026-08-13T00:00:00+00:00", "returncode": 0, "stdout": mod.GET_VERSION, "stderr": ""},
            "samples": samples, "post_probe_pids": [321], "consecutive_exact": 2,
            "receipt_created_after_readiness": True,
        }
        self.assertTrue(mod.validate_v2_readiness(evidence, 321))
        self.assertTrue(all(row["stdout"].endswith("\n") for row in samples))

    def readiness_evidence(self):
        samples = []
        for index, nonce in enumerate(("1" * 32, "2" * 32), 1):
            samples.append({
                "probe_index": index, "nonce": nonce, "returncode": 0,
                "stdout": mod.readiness_stdout(nonce, index), "stderr": "",
                "pids": [321], "exact": True,
            })
        return {
            "schema": mod.READINESS_SCHEMA,
            "same_fresh_pid": 321,
            "version_probe": {
                "sampled_at": "2026-08-13T00:00:00+00:00", "returncode": 0,
                "stdout": mod.GET_VERSION, "stderr": "",
            },
            "samples": samples,
            "post_probe_pids": [321],
            "consecutive_exact": 2,
            "receipt_created_after_readiness": True,
        }

    def test_v2_readiness_evidence_exact_and_recanonicalized_tamper(self):
        value = self.readiness_evidence()
        self.assertTrue(mod.validate_v2_readiness(value, 321))
        mutations = (
            lambda x: x.update(extra=True),
            lambda x: x.update(schema="wrong"),
            lambda x: x.update(same_fresh_pid=322),
            lambda x: x.update(post_probe_pids=[321, 322]),
            lambda x: x.update(consecutive_exact=1),
            lambda x: x.update(receipt_created_after_readiness=False),
            lambda x: x["version_probe"].update(stdout="26.3x87"),
            lambda x: x["version_probe"].update(stderr="warning"),
            lambda x: x["samples"][0].update(nonce="2" * 32),
            lambda x: x["samples"][0].update(probe_index=2),
            lambda x: x["samples"][0].update(stdout="1\n"),
            lambda x: x["samples"][0].update(stderr="warning"),
            lambda x: x["samples"][0].update(pids=[322]),
            lambda x: x["samples"][0].update(exact=False),
            lambda x: x["samples"][0].update(extra=True),
            lambda x: x["samples"].insert(1, {**copy.deepcopy(x["samples"][0]), "probe_index": 2}),
        )
        for mutate in mutations:
            bad = copy.deepcopy(value); mutate(bad)
            self.assertFalse(mod.validate_v2_readiness(bad, 321))

    def test_v2_summary_and_persisted_gate_recomputes_readiness(self):
        readiness = self.readiness_evidence()
        raw = {"host": {"pid": 321}, "v2_contract": mod.contract(), "v2_launcher_readiness": readiness}
        summary = {
            "raw_report": {"path": str(mod.RAW.relative_to(ROOT))},
            "v2_contract": mod.contract(), "v2_launcher_readiness": copy.deepcopy(readiness),
        }
        self.assertTrue(mod.validate_v2_outputs(summary, raw, mod.RAW))
        mutations = (
            lambda s, r: s["v2_launcher_readiness"]["samples"][0].update(stdout="1\n"),
            lambda s, r: (s["v2_launcher_readiness"]["samples"][0].update(stdout="1\n"), r["v2_launcher_readiness"]["samples"][0].update(stdout="1\n")),
            lambda s, r: r["host"].update(pid=322),
            lambda s, r: s["v2_contract"].update(status="GO"),
            lambda s, r: r["v2_contract"].update(extra=True),
            lambda s, r: s["raw_report"].update(path="wrong"),
        )
        for mutate in mutations:
            bad_summary, bad_raw = copy.deepcopy(summary), copy.deepcopy(raw)
            mutate(bad_summary, bad_raw)
            self.assertFalse(mod.validate_v2_outputs(bad_summary, bad_raw, mod.RAW))
        self.assertFalse(mod.validate_v2_outputs(summary, raw, ROOT / "wrong.json"))

    def test_receipt_only_after_readiness_and_o_excl(self):
        old = mod.RECEIPT
        try:
            with tempfile.TemporaryDirectory() as directory:
                mod.RECEIPT = Path(directory) / "receipt.json"
                with self.assertRaises(RuntimeError):
                    mod.create_receipt_after_readiness([{"exact": True}], 321)
                self.assertFalse(mod.RECEIPT.exists())
                with self.assertRaises(RuntimeError):
                    mod.create_receipt_after_readiness([{"exact": True}, {"exact": False}], 321)
                self.assertFalse(mod.RECEIPT.exists())
                evidence = self.readiness_evidence()
                mod.create_receipt_after_readiness(evidence, 321)
                receipt = json.loads(mod.RECEIPT.read_text())
                self.assertEqual(set(receipt), {"schema", "created_at"})
                self.assertEqual(receipt["schema"], "olm.all10-fresh-ae-invocation-receipt/1")
                with self.assertRaises(RuntimeError):
                    mod.create_receipt_after_readiness(evidence, 321)
        finally:
            mod.RECEIPT = old

    def test_both_failure_classes_and_crash_closure_are_exact(self):
        self.assertTrue(mod.validate_failures(mod.failure_authorities()))
        value = mod.failure_authorities()
        self.assertEqual(value["unsupported_generic_toon_frame_attempt"]["classification"], "immutable_failure_owner_contract_mismatch")
        self.assertEqual(value["pre_payload_doscriptfile_failure"]["classification"], "immutable_failure_pre_payload_doscriptfile_error_not_plugin_crash")
        for mutate in (
            lambda x: x.update(extra=True),
            lambda x: x["unsupported_generic_toon_frame_attempt"]["raw"].update(sha256="0" * 64),
            lambda x: x["pre_payload_doscriptfile_failure"]["receipt"].update(path="wrong"),
            lambda x: x["pre_payload_doscriptfile_failure"]["failure_metadata"].update(sha256="0" * 64),
            lambda x: x["pre_payload_doscriptfile_failure"].update(classification="toon_crash"),
        ):
            bad = copy.deepcopy(value); mutate(bad)
            self.assertFalse(mod.validate_failures(bad))

    def test_contract_recanonicalized_tamper_and_paths(self):
        self.assertTrue(mod.validate_contract(mod.contract()))
        value = mod.contract()
        mutations = (
            lambda x: x.update(extra=True),
            lambda x: x["paths"].update(receipt="wrong"),
            lambda x: x["readiness"].update(consecutive_exact=1),
            lambda x: x["readiness"]["order"].reverse(),
            lambda x: x["dependencies"]["v1_runner"].update(sha256="0" * 64),
            lambda x: x.update(claim_boundary="pixel exact"),
            lambda x: x.update(status="GO"),
        )
        for mutate in mutations:
            bad = copy.deepcopy(value); mutate(bad)
            self.assertFalse(mod.validate_contract(bad))
        self.assertNotEqual(mod.RAW, mod.FAILURE1_RAW)
        self.assertNotEqual(mod.RAW, mod.FAILURE2_RAW)
        release = (ROOT / "refs/conformance/olm_release_gate_manifest_20260806.json").read_text()
        self.assertNotIn(str(mod.SUMMARY.relative_to(ROOT)), release)

    def test_payload_is_versioned_and_pins_v1_execution(self):
        text = PAYLOAD.read_text()
        self.assertIn("ae_host_all10_post_toondilate_ded9_corrected_20260813.jsx", text)
        self.assertEqual(hashlib.sha256(mod.V1_PAYLOAD.read_bytes()).hexdigest(), mod.V1_PAYLOAD_SHA256)


if __name__ == "__main__":
    unittest.main()
