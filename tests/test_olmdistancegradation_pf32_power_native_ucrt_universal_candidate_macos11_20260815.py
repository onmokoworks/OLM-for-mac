import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/audit_olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815.json"

spec = importlib.util.spec_from_file_location("dg_native_macos11_candidate", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DistanceNativeMacOS11CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(REPORT.read_text())

    def rejected(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        self.assertFalse(module.validate(value, live=False))

    def test_live_candidate(self):
        self.assertTrue(module.validate(self.value))
        self.assertEqual(module.DOC.read_text(), module.markdown(self.value))

    def test_rejects_minos(self):
        self.rejected(lambda value: value["candidate"]["minimum_macos"].__setitem__("x86_64", "26.2"))

    def test_rejects_extra_export(self):
        self.rejected(lambda value: value["candidate"]["ae_entrypoint_exports"]["arm64"].append("_PluginDataEntryFunction2"))

    def test_rejects_binary_identity(self):
        self.rejected(lambda value: value["candidate"].__setitem__("binary_sha256", "0" * 64))

    def test_rejects_runtime_count(self):
        self.rejected(lambda value: value["source_runtime"]["x86_64"].__setitem__("raw_exact_cells", 7))

    def test_rejects_superseded_boundary(self):
        self.rejected(lambda value: value["supersedes"].__setitem__("reason", "none"))

    def test_rejects_scope_mutation(self):
        self.rejected(lambda value: value["scope"].__setitem__("mediacore_changed", True))


if __name__ == "__main__":
    unittest.main()
