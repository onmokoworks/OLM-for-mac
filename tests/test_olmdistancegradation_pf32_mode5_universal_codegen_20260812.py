import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tools/emulation/audit_olmdistancegradation_pf32_mode5_universal_codegen_20260812.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_mode5_universal_codegen_20260812.json"


def module():
    spec = importlib.util.spec_from_file_location("dg_mode5_codegen", GEN)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


class DistanceGradationMode5UniversalCodegen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = module()
        cls.report = json.loads(REPORT.read_text())

    def rejected(self, mutate):
        value = copy.deepcopy(self.report)
        mutate(value)
        with self.assertRaises(AssertionError):
            self.m.validate(value)

    def test_validate_only(self):
        result = subprocess.run(
            [sys.executable, str(GEN), "--validate-only"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_report(self):
        self.m.validate(copy.deepcopy(self.report))

    def test_binary_identity_tamper(self):
        self.rejected(lambda p: p.__setitem__("binary_sha256", "0" * 64))

    def test_bundle_inventory_tamper(self):
        self.rejected(lambda p: p["candidate_bundle_inventory"].pop())

    def test_codesign_tamper(self):
        self.rejected(lambda p: p.__setitem__("strict_codesign", False))

    def test_slice_fused_operation_tamper(self):
        self.rejected(lambda p: p["slices"]["arm64"].__setitem__("fused_op_count", 1))

    def test_slice_helper_count_tamper(self):
        self.rejected(lambda p: p["slices"]["x86_64"].__setitem__("product_helper_calls", 2))

    def test_runtime_admitted_count_tamper(self):
        self.rejected(lambda p: p["runtime_production_source_universal_mode5"]["arm64"].__setitem__("raw_exact_cells", 8))

    def test_runtime_power_count_tamper(self):
        self.rejected(lambda p: p["runtime_production_source_universal_mode5"]["x86_64"].__setitem__("power_fail_closed_cells", 7))

    def test_runtime_power_output_tamper(self):
        self.rejected(lambda p: p["runtime_production_source_universal_mode5"]["arm64"]["power_fail_closed_rows"][0].__setitem__("output_untouched_sha256", "1" * 64))

    def test_runtime_power_promoted_tamper(self):
        self.rejected(lambda p: p["runtime_production_source_universal_mode5"]["x86_64"]["rows"][-1].__setitem__("raw_exact", True))

    def test_native_ucrt_claim_tamper(self):
        self.rejected(lambda p: p["claims_not_made"].remove("No native Windows UCRT powf result for PF32 Power"))


if __name__ == "__main__":
    unittest.main()
