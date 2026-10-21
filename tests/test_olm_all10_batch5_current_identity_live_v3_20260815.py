from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock


ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/run_olm_all10_batch5_current_identity_live_v3_20260815.py"
PAYLOAD=ROOT/"scripts/ae_host_all10_batch5_current_identity_live_v3_20260815.jsx"
REPORT=ROOT/"refs/conformance/olm_all10_batch5_current_identity_live_v3_contract_20260815.json"


def load_runner():
    spec=importlib.util.spec_from_file_location("olm_batch5_live_v3",RUNNER);module=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(module);return module


def ae_processes():
    value=subprocess.run(["ps","-ax","-o","pid=,command="],capture_output=True,text=True,check=True)
    return sorted(line.strip() for line in value.stdout.splitlines()
                  if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
                  or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line)


class Batch5LiveV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner=load_runner();cls.report=json.loads(REPORT.read_text(encoding="utf-8"))

    def test_default_is_read_only_exact_go(self):
        before=REPORT.read_bytes();processes=ae_processes()
        value=subprocess.run([sys.executable,str(RUNNER)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(value.returncode,0,value.stdout+value.stderr)
        output=json.loads(value.stdout);self.assertFalse(output["ae_run_executed"])
        self.assertEqual(output["identity_sha256"],"ede4857b810e9f2901561ee8a3a9179c4c508dc2ee058525aa3f46dff4164079")
        self.assertTrue(self.runner.validate_contract(copy.deepcopy(self.report)))
        self.assertEqual(REPORT.read_bytes(),before);self.assertEqual(ae_processes(),processes)
        self.assertTrue(self.runner.outputs_absent())

    def test_actual_identity_and_host_policy_are_exact(self):
        identity=self.report["accepted_identity"]
        self.assertTrue(identity["exact_hash"] and identity["actual_installed_and_source_bundles_verified"])
        self.assertEqual(identity["plugin_count"],10);self.assertEqual(len(identity["plugins"]),10)
        self.assertTrue(all(row["architectures"]==["arm64","x86_64"] and row["installed_count_one"] and row["strict_codesign_valid"] for row in identity["plugins"]))
        policy=self.report["host_frame_policy"]
        self.assertEqual(policy["enabled"],["OLMBlur","OLMDirectionalBlur"]);self.assertEqual(len(policy["disabled_after_load_add"]),8)
        self.assertIn("OLMToonDilate",policy["disabled_after_load_add"]);self.assertEqual(policy["numerical_assessment"],"not_assessed")
        text=PAYLOAD.read_text(encoding="utf-8");self.assertIn('numerical_render_assessment: \\"not_assessed\\"',text)

    def test_exact_run_dispatch_is_fixed_without_executing_ae(self):
        captured=[]
        def fake_main():captured.append(list(sys.argv));return 37
        processes=ae_processes()
        with mock.patch.object(self.runner.BASE_MODULE,"main",fake_main):
            self.assertEqual(self.runner.execute_once(),37)
        self.assertEqual(ae_processes(),processes);self.assertTrue(self.runner.outputs_absent())
        self.assertEqual(captured,[[str(self.runner.BASE_RUNNER),"--raw-report",str(self.runner.RAW),"--summary",str(self.runner.SUMMARY),"--artifact-dir",str(self.runner.ARTIFACT_DIR),"--timeout","900"]])

    def test_o_excl_receipt_and_one_shot_contract_are_pinned(self):
        base=self.runner.BASE_RUNNER.read_text(encoding="utf-8")
        self.assertIn("os.O_WRONLY | os.O_CREAT | os.O_EXCL",base)
        execution=self.report["execution"]
        self.assertTrue(execution["o_excl_receipt_before_launch"] and execution["single_attempt_no_retry"])
        self.assertEqual(self.report["fixed_outputs"]["receipt"],str(self.runner.RECEIPT.relative_to(ROOT)))
        self.assertEqual(self.report["exact_run_command"],f"python3 {RUNNER.relative_to(ROOT)} --run")

    def test_closed_contract_rejects_tamper(self):
        for mutation in (lambda x:x.update(extra=True),lambda x:x["accepted_identity"].update(sha256="0"*64),
                         lambda x:x["execution"].update(exact_flag="--go"),lambda x:x["preflight"].update(process_count=1),
                         lambda x:x["fixed_outputs"].update(all_absent=False),lambda x:x["host_frame_policy"]["enabled"].append("OLMToonDilate"),
                         lambda x:x["host_frame_policy"].update(numerical_assessment="exact")):
            changed=copy.deepcopy(self.report);mutation(changed);self.assertFalse(self.runner.validate_contract(changed))


if __name__=="__main__":unittest.main()
