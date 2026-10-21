import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/'tools/emulation/test_olmblur_pf16_7x5_public_admission_20260813.py'
S=importlib.util.spec_from_file_location('blur7closure',PATH);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads(M.REPORT.read_text());M.validate(cls.d)
 def reject(self,fn):
  d=copy.deepcopy(self.d);fn(d)
  with self.assertRaises((ValueError,RuntimeError,KeyError,TypeError)):M.validate(d)
 def test_live(self):self.assertEqual(self.d,M.build(M.run()))
 def test_authority(self):
  for fn in (lambda d:d.update(extra=1),lambda d:d.__setitem__('status','PASS'),lambda d:d.__setitem__('claim_boundary','broad'),lambda d:d['claims_not_made'].clear()):self.reject(fn)
 def test_identity_contract(self):
  for fn in (lambda d:d['identities']['worker'].__setitem__('sha256','0'*64),lambda d:d['contract'].__setitem__('rowbytes',68),lambda d:d['contract']['parameters'].__setitem__('legacy',1)):self.reject(fn)
 def test_recanonicalized_row(self):
  def fn(d):d['run_lines'][0]=d['run_lines'][0].replace('exact=1','exact=0');d['run_sha256']=hashlib.sha256(('\n'.join(d['run_lines'])+'\n').encode()).hexdigest()
  self.reject(fn)
 def test_docs(self):
  self.assertEqual(M.DOC.read_text(),M.md(self.d))
  docs={path:('22eb712a','ecdf3d93') for path in (
   'README.md','KNOWN_LIMITATIONS.md','notes/CONFORMANCE_LEDGER.md',
   'refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md',
   'refs/conformance/olm_release_completion_matrix_20260806.md',
   'refs/conformance/olm_mac_port_orchestrator_boundary_20260805.md')}
  for path,needles in docs.items():
   text=(ROOT/path).read_text()
   for needle in needles:self.assertIn(needle,text,path)
if __name__=='__main__':unittest.main()
