import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_type3_layer_20260814.py"
SPEC = importlib.util.spec_from_file_location("current_type3", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CurrentInstalledType3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(MODULE.REPORT.read_text())

    def test_report_validates(self):
        self.assertTrue(MODULE.validate(self.report))

    def test_identity_tamper_rejected(self):
        value = copy.deepcopy(self.report)
        value["identities"]["installed_binary_sha256"] = "0" * 64
        self.assertFalse(MODULE.validate(value))

    def test_recanonicalized_count_tamper_rejected(self):
        value = copy.deepcopy(self.report)
        value["slices"]["arm64"]["positive"] = 4
        value["slices"]["arm64"]["negative"] = 53
        self.assertFalse(MODULE.validate(value))


if __name__ == "__main__":
    unittest.main()
