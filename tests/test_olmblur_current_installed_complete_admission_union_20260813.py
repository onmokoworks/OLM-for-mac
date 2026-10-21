from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmblur_current_installed_complete_admission_union_20260813.py"
REPORT = ROOT / "refs/conformance/olmblur_current_installed_complete_admission_union_20260813.json"


def load_module():
    spec = importlib.util.spec_from_file_location("olmblur_installed_union", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class OLMBlurInstalledUnionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity(self):
        self.assertEqual(hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
                         "550471d66ac878693db5a1bb1d32694ab060204735b44b02cd0053ff2c54303d")

    def test_report_schema_and_cardinality(self):
        self.module.validate(self.report)
        self.assertEqual(self.report["summary"]["cells_total"], 80)
        self.assertEqual(self.report["summary"]["negative_controls_per_slice"], 1298)

    def test_tampering_fails(self):
        mutations = (
            lambda r: r.update(extra=True),
            lambda r: r["scope"].update(native_after_effects=True),
            lambda r: r["summary"].update(cells_per_slice=39),
            lambda r: r["authorities"].update(installed="0" * 64),
            lambda r: r["architectures"]["arm64"]["PF8"].update(line_count=0),
            lambda r: r["architectures"]["x86_64"]["PF32"].update(transcript_sha256="0" * 64),
        )
        for mutation in mutations:
            candidate = copy.deepcopy(self.report)
            mutation(candidate)
            with self.assertRaises(RuntimeError):
                self.module.validate(candidate)


if __name__ == "__main__":
    unittest.main()
