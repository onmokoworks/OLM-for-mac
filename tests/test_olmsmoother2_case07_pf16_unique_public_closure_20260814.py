import copy
import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmsmoother2_case07_pf16_unique_public_closure_20260814.py"
REPORT = ROOT / "refs/conformance/olmsmoother2_case07_pf16_unique_public_closure_20260814.json"
TOOL_SHA256 = "95f9550f7b22259072214dd40d08320d12a93777cea0fba82946c82157403553"

spec = importlib.util.spec_from_file_location("pf16_case07", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class Case07PF16ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REPORT.read_text())

    def test_generator_identity_and_live_validation(self):
        self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), TOOL_SHA256)
        self.assertTrue(module.validate(self.data, live=True))

    def test_default_is_read_only_validate(self):
        before = REPORT.read_bytes()
        run = subprocess.run(["python3", str(TOOL)], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_contract_and_reconstruction_tamper_rejected(self):
        for path, value in [
            (("contract", "depth"), 32),
            (("contract", "input_active_sha256"), "0" * 64),
            (("input_reconstruction", "all_words_have_exact_code_over_32768"), False),
            (("input_reconstruction", "distinct_float_words_by_channel"), {"A": 1}),
            (("windows_effect_on_relation", "max_raw_u32_delta"), 1),
        ]:
            changed = copy.deepcopy(self.data)
            changed[path[0]][path[1]] = value
            self.assertFalse(module.validate(changed, live=False), path)

    def test_public_case_tamper_rejected(self):
        for mutation in ("name", "pass", "extra", "remove"):
            changed = copy.deepcopy(self.data)
            if mutation == "name": changed["public_cases"][1]["name"] = "source_other"
            elif mutation == "pass": changed["public_cases"][1]["pass"] = False
            elif mutation == "extra": changed["public_cases"][1]["extra"] = 1
            else: changed["public_cases"].pop()
            self.assertFalse(module.validate(changed, live=False), mutation)

    def test_top_level_and_claim_tamper_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["extra"] = True
        self.assertFalse(module.validate(changed, live=False))
        changed = copy.deepcopy(self.data)
        changed["claims_not_made"].pop()
        self.assertFalse(module.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()
