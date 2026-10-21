import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.json"

spec = importlib.util.spec_from_file_location("dg_pf32_power_native_closure", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DistancePF32PowerNativeClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(REPORT.read_text())

    def rejected(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        self.assertFalse(module.validate(value, live=False))

    def test_current_evidence(self):
        self.assertTrue(module.validate(self.value))
        self.assertEqual(module.DOC.read_text(), module.markdown(self.value))

    def test_rejects_summary_tamper(self):
        self.rejected(lambda value: value["summary"].__setitem__("same_source_full_raw_exact", 7))

    def test_rejects_raw_hash_tamper(self):
        self.rejected(lambda value: value["rows"][0].__setitem__("current_production_raw_sha256", "0" * 64))

    def test_rejects_native_delta_tamper(self):
        self.rejected(lambda value: value["native_return"].__setitem__("native_differs_libsystem", 0))

    def test_rejects_public_count_tamper(self):
        self.rejected(lambda value: value["public_contract"].__setitem__("pf32_power_positive_cells", 7))


if __name__ == "__main__":
    unittest.main()
