import copy, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'tools/emulation/test_olmblur_smart_public_admission_20260813.py'
GENERATOR_SHA='9ed39da2248a5d3e8b3c759fe3f91019eb6335afa257527167aa3c0dda711e70'
SPEC=importlib.util.spec_from_file_location('blur_closure',PATH);M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class ClosureTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.report=json.loads(M.REPORT.read_text());M.validate(cls.report)
  def rejects(self,mut):
    d=copy.deepcopy(self.report);mut(d)
    with self.assertRaises((ValueError,RuntimeError,KeyError,TypeError,IndexError)):M.validate(d)
  def test_exact_live_identities(self):
    self.assertEqual(M.sha(PATH),GENERATOR_SHA);self.assertEqual(M.sha(M.SOURCE),M.EXPECTED['source']);self.assertEqual(M.sha(M.PROBE),M.EXPECTED['probe'])
  def test_top_schema_and_authority_tamper(self):
    for mut in (lambda d:d.update(extra=True),lambda d:d.pop('status'),lambda d:d.__setitem__('status','PASS'),lambda d:d.__setitem__('claim_boundary','broadened'),lambda d:d['claims_not_made'].clear()):self.rejects(mut)
  def test_identity_matrix_summary_tamper(self):
    for mut in (lambda d:d['identities']['source'].__setitem__('sha256','0'*64),lambda d:d['identities']['windows_exported_report'].__setitem__('role','native AE'),lambda d:d['matrix']['rowbytes'].__setitem__('PF16',216),lambda d:d['matrix']['parameters'].__setitem__('amount_f64',5.0001),lambda d:d['matrix']['active_source_sha256'].__setitem__('PF32','0'*64),lambda d:d['summary'].__setitem__('smart_render_negatives',90)):self.rejects(mut)
  def test_recanonicalized_run_row_tamper(self):
    def recanon(d):d['run_sha256']=__import__('hashlib').sha256(('\n'.join(d['run_lines'])+'\n').encode()).hexdigest()
    for mutate in (lambda r:r.__setitem__(0,r[0].replace('pass=1','pass=0')),lambda r:r.pop(12),lambda r:r.append(r[0]),lambda r:r.__setitem__(20,r[20].replace('actual=516','actual=0')),lambda r:r.__setitem__(-2,r[-2].replace('unchanged=1','unchanged=0'))):
      def m(d,mutate=mutate):mutate(d['run_lines']);recanon(d)
      self.rejects(m)
  def test_gates_doc_and_readonly_default(self):
    self.rejects(lambda d:d['gates'].pop());self.assertEqual(M.DOC.read_text(),M.md(self.report))

if __name__=='__main__':unittest.main()
