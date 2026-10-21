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
RUNNER = ROOT / "scripts/run_olm_all10_current_identity_deferred_v3_20260814.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_current_identity_deferred_v3_20260814.jsx"
REPORT = ROOT / "refs/conformance/olm_all10_current_identity_deferred_v3_contract_20260814.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("olm_current_identity_v3", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def ae_processes() -> list[str]:
    run = subprocess.run(["ps", "-ax", "-o", "pid=,command="], text=True, capture_output=True, check=True)
    return sorted(
        line.strip() for line in run.stdout.splitlines()
        if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
        or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line
    )


class CurrentIdentityDeferredV3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_default_is_read_only_and_current(self) -> None:
        before = REPORT.read_bytes()
        processes_before = ae_processes()
        run = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        status = json.loads(run.stdout)
        self.assertTrue(status["current_identity_valid"])
        self.assertTrue(status["future_outputs_absent"])
        self.assertFalse(status["after_effects_launched"])
        self.assertEqual(REPORT.read_bytes(), before)
        self.assertEqual(ae_processes(), processes_before)

    def test_run_flag_refuses_before_outputs(self) -> None:
        before = self.runner.future_outputs_absent()
        processes_before = ae_processes()
        run = subprocess.run([sys.executable, str(RUNNER), "--run"], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("AE execution forbidden", run.stdout + run.stderr)
        self.assertTrue(before)
        self.assertTrue(self.runner.future_outputs_absent())
        self.assertEqual(ae_processes(), processes_before)

    def test_direct_execute_refuses(self) -> None:
        with self.assertRaises(SystemExit):
            self.runner.execute_v3()

    def test_contract_exact_and_closed(self) -> None:
        self.assertTrue(self.runner.validate_contract(self.report))
        self.assertEqual(self.report["current_identity"]["sha256"], self.runner.PINS["identity"])
        self.assertEqual(self.report["host_frame_policy"]["enabled"], ["OLMBlur", "OLMDirectionalBlur"])
        self.assertIn("OLMToonDilate", self.report["host_frame_policy"]["disabled"])
        self.assertFalse(self.report["execution"]["live_entrypoint_present"])
        self.assertTrue(self.report["future_paths"]["all_absent"])

    def test_claim_and_schema_tamper_rejected(self) -> None:
        for mutation in (
            lambda value: value.update(extra=True),
            lambda value: value["execution"].update(live_entrypoint_present=True),
            lambda value: value["host_frame_policy"]["enabled"].append("OLMToonDilate"),
            lambda value: value["current_identity"].update(sha256="0" * 64),
        ):
            changed = copy.deepcopy(self.report)
            mutation(changed)
            self.assertFalse(self.runner.validate_contract(changed))

    def test_payload_is_direct_current_base_transform(self) -> None:
        text = PAYLOAD.read_text(encoding="utf-8")
        self.assertIn("ae_host_all10_current_install_fresh_validation_20260812.jsx", text)
        self.assertNotIn("post_toondilate_ded9_corrected_20260813.jsx", text)
        self.assertIn("Numerical behavior is not assessed", text)


if __name__ == "__main__":
    unittest.main()
