from __future__ import annotations
import copy, importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "handoffs/olmblur_pf32_retained_public_universal_candidate_v3_20260813/verify_candidate.py"
SPEC = importlib.util.spec_from_file_location("olmblur_v3", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class OLMBlurV3Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(MODULE.REPORT.read_text())
        MODULE.validate(cls.value)

    def reject(self, mutation):
        value = copy.deepcopy(self.value)
        mutation(value)
        with self.assertRaises(ValueError):
            MODULE.validate(value)

    def test_live(self):
        MODULE.validate(self.value)

    def test_tamper(self):
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d["source"].update(sha256="0" * 64),
            lambda d: d["authorities"]["pf8_closure"].update(sha256="0" * 64),
            lambda d: d["build"].update(sha256="0" * 64),
            lambda d: d["candidate"].update(binary_sha256="0" * 64),
            lambda d: d["candidate"].update(signature="Developer ID"),
            lambda d: d["scope"].update(installed=True),
        ):
            self.reject(mutation)

if __name__ == "__main__":
    unittest.main()
