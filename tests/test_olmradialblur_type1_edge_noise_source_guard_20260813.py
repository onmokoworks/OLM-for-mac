from __future__ import annotations
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"tools/emulation/test_olmradialblur_type1_edge_noise_source_guard_20260813.py";s=importlib.util.spec_from_file_location("edge",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.r=json.loads(m.REPORT.read_text())
 def test_valid(c):m.validate(c.r)
 def test_source(c):
  x=copy.deepcopy(c.r);x["active_source_sha256"]["PF8"]="0"*64
  with c.assertRaises(RuntimeError):m.validate(x)
 def test_run(c):
  x=copy.deepcopy(c.r);x["runs"][0]["lines"][0]="x"
  with c.assertRaises(RuntimeError):m.validate(x)
 def test_claim(c):
  x=copy.deepcopy(c.r);x["claim_boundary"]["proven"]="all"
  with c.assertRaises(RuntimeError):m.validate(x)
 def test_schema(c):
  x=copy.deepcopy(c.r);x["x"]=1
  with c.assertRaises(RuntimeError):m.validate(x)
if __name__=="__main__":unittest.main()
