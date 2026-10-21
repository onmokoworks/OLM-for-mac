from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_batch5_current_identity_deferred_v1_20260815.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_batch5_current_identity_deferred_v1_20260815.jsx"
REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_deferred_v1_contract_20260815.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("olm_batch5_deferred_v1", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def ae_processes() -> list[str]:
    value = subprocess.run(["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True, check=True)
    return sorted(line.strip() for line in value.stdout.splitlines()
                  if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
                  or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line)


class Batch5DeferredV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_prepared_contract_is_exact_read_only_and_no_ae(self) -> None:
        before = REPORT.read_bytes(); processes = ae_processes()
        run = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.runner.validate_contract(copy.deepcopy(self.report)))
        self.assertEqual(REPORT.read_bytes(), before)
        self.assertEqual(ae_processes(), processes)

    def test_all_live_entrypoints_refuse_before_outputs(self) -> None:
        processes = ae_processes(); before = self.runner.future_outputs_absent()
        run = subprocess.run([sys.executable, str(RUNNER), "--run"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("AE execution forbidden", run.stdout + run.stderr)
        with self.assertRaises(SystemExit):
            self.runner.execute_batch5()
        self.assertTrue(before and self.runner.future_outputs_absent())
        self.assertEqual(ae_processes(), processes)

    def test_policy_disables_all_bounded_effects_and_has_no_numerical_claim(self) -> None:
        policy = self.report["host_frame_policy"]
        self.assertEqual(policy["enabled"], ["OLMBlur", "OLMDirectionalBlur"])
        self.assertEqual(len(policy["disabled_after_load_add"]), 8)
        self.assertIn("OLMToonDilate", policy["disabled_after_load_add"])
        self.assertEqual(policy["numerical_assessment"], "not_assessed")
        self.assertIn("No pixel-exact", policy["claim_boundary"])
        text = PAYLOAD.read_text(encoding="utf-8")
        self.assertIn("OLMToonDilate and the other seven bounded effects are disabled", text)
        self.assertIn("Numerical behavior is not assessed", text)

    def test_retarget_is_validated_and_never_overwrites(self) -> None:
        processes = ae_processes()
        with tempfile.TemporaryDirectory(prefix="olm_batch5_retarget_test_") as raw:
            output = Path(raw) / "retargeted.json"
            command = [sys.executable, str(RUNNER), "--identity", str(self.runner.PREDECESSOR_IDENTITY),
                       "--emit-retargeted-contract", str(output)]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(self.runner.validate_contract(value, self.runner.PREDECESSOR_IDENTITY))
            self.assertEqual(value["status"], "AE_FORBIDDEN_RETARGETED_IDENTITY_VALIDATED")
            self.assertEqual(value["identity_retarget"]["target"]["plugin_count"], 10)
            before = hashlib.sha256(output.read_bytes()).hexdigest()
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), before)
        self.assertEqual(ae_processes(), processes)

    def test_closed_contract_rejects_tampering(self) -> None:
        for mutation in (
            lambda value: value.update(extra=True),
            lambda value: value["execution"].update(live_entrypoint_present=True),
            lambda value: value["host_frame_policy"]["enabled"].append("OLMToonDilate"),
            lambda value: value["host_frame_policy"].update(numerical_assessment="exact"),
            lambda value: value["future_paths"].update(all_absent=False),
        ):
            changed = copy.deepcopy(self.report); mutation(changed)
            self.assertFalse(self.runner.validate_contract(changed))


if __name__ == "__main__":
    unittest.main()
