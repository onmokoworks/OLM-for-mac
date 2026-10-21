import copy, importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs/olmblur_retained_public_universal_candidate_v4_20260813"
PATH = HANDOFF / "verify_candidate.py"
SPEC = importlib.util.spec_from_file_location("olmblur_v4", PATH)
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

class CandidateV4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads(MODULE.REPORT.read_text()); MODULE.validate(cls.value)
    def test_live(self): self.assertEqual(MODULE.collect(self.value), {k:self.value["candidate"][k] for k in ("bundle","binary_sha256","architectures","info_minimum_system_version","slices","inventory")})
    def test_scope(self): self.assertFalse(self.value["scope"]["installed"]); self.assertFalse(self.value["scope"]["after_effects_launched"])
    def test_tamper(self):
        for mutation in (
            lambda v:v["source"].update(sha256="0"*64),
            lambda v:v["authorities"]["pf32_closure"].update(sha256="0"*64),
            lambda v:v["candidate"].update(binary_sha256="0"*64),
            lambda v:v.update(extra=True),
        ):
            changed=copy.deepcopy(self.value);mutation(changed)
            with self.assertRaises((ValueError,KeyError)):MODULE.validate(changed)

if __name__ == "__main__": unittest.main()
