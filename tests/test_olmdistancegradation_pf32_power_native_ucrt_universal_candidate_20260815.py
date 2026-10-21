import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/audit_olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.json"

spec = importlib.util.spec_from_file_location("dg_native_universal", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DistanceNativeUniversalCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(REPORT.read_text())

    def rejected(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        self.assertFalse(module.validate(value, live=False))

    def test_current_candidate(self):
        self.assertTrue(module.validate(self.value))
        self.assertEqual(module.DOC.read_text(), module.markdown(self.value))

    def test_rejects_architecture_count(self):
        self.rejected(lambda value: value["summary"].__setitem__("architectures", 1))

    def test_rejects_slice_count(self):
        self.rejected(lambda value: value["slices"]["arm64"].__setitem__("raw_exact_cells", 7))

    def test_rejects_raw_hash(self):
        self.rejected(lambda value: value["slices"]["x86_64"]["rows"][0].__setitem__("raw_sha256", "0" * 64))

    def test_rejects_public_marker(self):
        self.rejected(lambda value: value["slices"]["arm64"].__setitem__("public_marker", "PASS"))


if __name__ == "__main__":
    unittest.main()
