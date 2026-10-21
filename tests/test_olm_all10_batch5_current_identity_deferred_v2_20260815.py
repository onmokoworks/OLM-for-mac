from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olm_all10_batch5_current_identity_deferred_v2_20260815.py"
REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_deferred_v2_contract_20260815.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("olm_batch5_deferred_v2", RUNNER)
    module = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module)
    module.configure()
    return module


def ae_processes() -> list[str]:
    value = subprocess.run(["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True, check=True)
    return sorted(line.strip() for line in value.stdout.splitlines()
                  if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
                  or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line)


class Batch5DeferredV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner(); cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_prepared_contract_and_live_refusal_are_read_only(self) -> None:
        before = REPORT.read_bytes(); processes = ae_processes()
        normal = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True)
        refused = subprocess.run([sys.executable, str(RUNNER), "--run"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
        self.assertNotEqual(refused.returncode, 0); self.assertIn("AE execution forbidden", refused.stdout + refused.stderr)
        self.assertTrue(self.runner.validate_contract(copy.deepcopy(self.report)))
        self.assertEqual(REPORT.read_bytes(), before); self.assertEqual(ae_processes(), processes)

    def test_retarget_verifies_actual_ten_installed_and_source_bundles(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_batch5_v2_identity_") as raw:
            output = Path(raw) / "retargeted.json"
            command = [sys.executable, str(RUNNER), "--identity", str(self.runner.BASE_MODULE.PREDECESSOR_IDENTITY),
                       "--emit-retargeted-contract", str(output)]
            value = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(value.returncode, 0, value.stdout + value.stderr)
            report = json.loads(output.read_text(encoding="utf-8")); target = report["identity_retarget"]["target"]
            self.assertTrue(target["actual_installed_and_source_bundles_verified"])
            self.assertEqual(len(target["plugins"]), 10)
            self.assertTrue(all(row["architectures"] == ["arm64", "x86_64"] and
                                row["installed_count_one"] and row["strict_codesign_valid"]
                                for row in target["plugins"]))
            self.assertTrue(self.runner.validate_contract(report, self.runner.BASE_MODULE.PREDECESSOR_IDENTITY))

    def test_fabricated_manifest_is_rejected(self) -> None:
        value = json.loads(self.runner.BASE_MODULE.PREDECESSOR_IDENTITY.read_text(encoding="utf-8"))
        value["plugins"][0]["sha256"] = value["plugins"][0]["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory(prefix="olm_batch5_v2_fake_") as raw:
            identity = Path(raw) / "fake.json"; identity.write_text(json.dumps(value))
            output = Path(raw) / "contract.json"
            run = subprocess.run([sys.executable, str(RUNNER), "--identity", str(identity),
                                  "--emit-retargeted-contract", str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0); self.assertFalse(output.exists())

    def test_every_reserved_output_target_is_rejected_without_creation(self) -> None:
        targets = [self.runner.FUTURE_RAW, self.runner.FUTURE_SUMMARY, self.runner.FUTURE_RECEIPT,
                   self.runner.FUTURE_ARTIFACT_DIR, self.runner.FUTURE_ARTIFACT_DIR / "nested.json"]
        self.assertTrue(all(not path.exists() for path in targets))
        for target in targets:
            run = subprocess.run([sys.executable, str(RUNNER), "--identity", str(self.runner.BASE_MODULE.PREDECESSOR_IDENTITY),
                                  "--emit-retargeted-contract", str(target)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0); self.assertFalse(target.exists())

    def test_policy_and_closed_schema(self) -> None:
        policy = self.report["host_frame_policy"]
        self.assertEqual(policy["enabled"], ["OLMBlur", "OLMDirectionalBlur"])
        self.assertEqual(len(policy["disabled_after_load_add"]), 8)
        self.assertEqual(policy["numerical_assessment"], "not_assessed")
        for mutation in (lambda x:x.update(extra=True),
                         lambda x:x["execution"].update(live_entrypoint_present=True),
                         lambda x:x["future_paths"].update(all_absent=False)):
            changed=copy.deepcopy(self.report);mutation(changed);self.assertFalse(self.runner.validate_contract(changed))


if __name__ == "__main__":
    unittest.main()
