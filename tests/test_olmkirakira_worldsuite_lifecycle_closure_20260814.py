from __future__ import annotations
import copy, hashlib, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"tools/emulation/test_olmkirakira_worldsuite_lifecycle_closure_20260814.py"
REPORT=ROOT/"refs/conformance/olmkirakira_worldsuite_lifecycle_closure_20260814.json"
GEN_SHA="872047a865e2262c66d2746c33d148df69d73cc3a18d0ef551da06c07e7052d8"

def load():
    s=importlib.util.spec_from_file_location("kira_world",GEN);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class KiraWorldSuiteLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.m=load();cls.r=json.loads(REPORT.read_text())
    def test_generator_identity(self):
        if GEN_SHA!="PENDING": self.assertEqual(hashlib.sha256(GEN.read_bytes()).hexdigest(),GEN_SHA)
    def test_report(self): self.m.validate(self.r)
    def test_row_tamper(self):
        x=copy.deepcopy(self.r);x["rows"][0]["get"]=3;x["rows_sha256"]=self.m.canonical(x["rows"])
        with self.assertRaises(AssertionError): self.m.validate(x)
    def test_scope_tamper(self):
        x=copy.deepcopy(self.r);x["claims"]["native_ae"]=True
        with self.assertRaises(AssertionError): self.m.validate(x)
    def test_unknown_key(self):
        x=copy.deepcopy(self.r);x["extra"]=True
        with self.assertRaises(AssertionError): self.m.validate(x)

if __name__=="__main__": unittest.main()
