import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/'tools/emulation/test_olmblur_pf16_7x5_exported_public_owner_20260813.py'
S=importlib.util.spec_from_file_location('blur7public',PATH);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class PublicOwner(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads(M.REPORT.read_text());M.validate(cls.d)
 def reject(self,fn):
  d=copy.deepcopy(self.d);fn(d)
  with self.assertRaises((ValueError,RuntimeError,KeyError,TypeError)):M.validate(d)
 def test_live(self):self.assertEqual(self.d,M.live())
 def test_authority_tamper(self):
  for fn in (lambda d:d.update(extra=1),lambda d:d.__setitem__('status','PASS'),lambda d:d['claims_not_made'].clear(),lambda d:d.__setitem__('claim_boundary','native AE')):self.reject(fn)
 def test_contract_tamper(self):
  for fn in (lambda d:d['contract'].__setitem__('rowbytes',68),lambda d:d['contract']['parameters'].__setitem__('amount_f64',5.0),lambda d:d['contract'].__setitem__('active_source_sha256','0'*64)):self.reject(fn)
 def test_result_tamper(self):
  for fn in (lambda d:d['public_result'].__setitem__('active_sha256','0'*64),lambda d:d['public_result'].__setitem__('mismatched_bytes',1),lambda d:d['gates'].__setitem__('padding_untouched',False)):self.reject(fn)
if __name__=='__main__':unittest.main()
