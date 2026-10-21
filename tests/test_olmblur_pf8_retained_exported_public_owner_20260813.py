import copy, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"tools/emulation/test_olmblur_pf8_retained_exported_public_owner_20260813.py"
SPEC=importlib.util.spec_from_file_location("pf8_owner",PATH);MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)

class TestPF8Owner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.value=json.loads(MOD.REPORT.read_text());MOD.validate(cls.value)
    def rejected(self,mutate):
        value=copy.deepcopy(self.value);mutate(value)
        with self.assertRaises(ValueError):MOD.validate(value)
    def test_exact_partition(self):self.assertEqual(11,sum(r["mismatched_bytes"]==0 for r in self.value["rows"]))
    def test_generator_identity(self):self.assertEqual("7c76270f45f9366f2d5686da73170f17f42121de097bc7b0ad494dcf735a4e17",MOD.hashlib.sha256(PATH.read_bytes()).hexdigest())
    def test_top_extra(self):self.rejected(lambda v:v.__setitem__("extra",1))
    def test_row_recanonicalized(self):
        def mutate(v):v["rows"][0]["mismatched_bytes"]=1;v["canonical_rows_sha256"]=MOD.hashlib.sha256(json.dumps(v["rows"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
        self.rejected(mutate)
    def test_identity(self):self.rejected(lambda v:v["identities"]["actual_aex"].__setitem__("sha256","0"*64))
    def test_claim(self):self.rejected(lambda v:v.__setitem__("claim_boundary","broader"))
if __name__=="__main__":unittest.main()
