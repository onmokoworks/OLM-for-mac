from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_source_bound_union_20260813.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_source_bound_union_20260813.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("directional_installed_union", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DirectionalInstalledSourceBoundUnionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_tool()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_saved_report_validates(self):
        self.module.validate(self.report)

    def test_slice_digest_tamper_rejected(self):
        tampered = copy.deepcopy(self.report)
        tampered["slices"][0]["natural64"]["positive_cells"][0]["name"] = "forged"
        with self.assertRaises(RuntimeError):
            self.module.validate(tampered)

    def test_recanonicalized_count_tamper_rejected(self):
        tampered = copy.deepcopy(self.report)
        tampered["slices"][1]["natural64"]["positive_cell_count"] = 14
        tampered["slices_digest"] = self.module.canonical_sha(tampered["slices"])
        with self.assertRaises(RuntimeError):
            self.module.validate(tampered)

    def test_recanonicalized_cell_tamper_rejected(self):
        tampered = copy.deepcopy(self.report)
        tampered["slices"][0]["natural64"]["positive_cells"][0]["name"] = "forged"
        tampered["slices_digest"] = self.module.canonical_sha(tampered["slices"])
        with self.assertRaises(RuntimeError):
            self.module.validate(tampered)

    def test_recanonicalized_type3_tamper_rejected(self):
        tampered = copy.deepcopy(self.report)
        tampered["slices"][0]["type3_layer"]["positive_cells"][0]["output_active_sha256"] = "0" * 64
        tampered["slices_digest"] = self.module.canonical_sha(tampered["slices"])
        with self.assertRaises(RuntimeError):
            self.module.validate(tampered)

    def test_unknown_key_rejected(self):
        tampered = copy.deepcopy(self.report)
        tampered["extra"] = True
        with self.assertRaises(RuntimeError):
            self.module.validate(tampered)


if __name__ == "__main__":
    unittest.main()
