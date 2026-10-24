
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/"tools/emulation/test_olmblur_pf32_retained_public_closure_20260813.py"
S=importlib.util.spec_from_file_location("pf32",PATH);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Closure(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.v=json.loads(M.REPORT.read_text());M.validate(c.v)
 def reject(self,fn):
  v=copy.deepcopy(self.v);fn(v)
  with self.assertRaises(ValueError):M.validate(v)
 def test_partition(self):self.assertEqual((19,1),(sum(r["mismatched_bytes"]==0 for r in self.v["owner_rows"]),sum(r["mismatched_bytes"]>0 for r in self.v["owner_rows"])))
 def test_schema(self):self.reject(lambda v:v.__setitem__("extra",1))
 def test_owner_recanonicalized(self):
  def m(v):v["owner_rows"][0]["mismatched_bytes"]=1;v["owner_rows_sha256"]=hashlib.sha256(json.dumps(v["owner_rows"],sort_keys=True,separators=(",",":")).encode()).hexdigest()
  self.reject(m)
 def test_mac_recanonicalized(self):
  def m(v):v["mac_run_lines"][0]=v["mac_run_lines"][0].replace("exact=1","exact=0");v["mac_run_sha256"]=hashlib.sha256(("\n".join(v["mac_run_lines"])+"\n").encode()).hexdigest()
  self.reject(m)
 def test_claim(self):self.reject(lambda v:v.__setitem__("claim_boundary","broader"))
 def test_current_docs_and_candidate(self):
  for rel in ("docs/archive/README_20260822.md","docs/archive/KNOWN_LIMITATIONS_20260822.md","notes/CONFORMANCE_LEDGER.md","refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md","refs/conformance/olm_release_completion_matrix_20260806.md","refs/conformance/olm_mac_port_orchestrator_boundary_20260805.md"):
   text=(ROOT/rel).read_text();self.assertIn("22eb712a",text,rel);self.assertIn("ecdf3d93",text,rel);self.assertIn("20/20",text,rel)
  self.assertTrue((resolve_asset(ROOT/"handoffs/olmblur_retained_public_universal_candidate_v4_20260813/build_identity.json")).is_file())
if __name__=="__main__":unittest.main()
