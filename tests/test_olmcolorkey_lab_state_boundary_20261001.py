"""Compare production Lab decisions with retained exported AEX owner witnesses."""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
LAST_VALIDATION={}

class LabStateBoundaryTests(unittest.TestCase):
 def test_native_key_state_and_adjacent_thresholds(self):
  paths=[ROOT/'reports'/name for name in ('colorkey_lab_state_baseline_20261001.json','colorkey_lab_threshold_boundary_20261001.json','colorkey_spaces_diagnostics_20261001.json')]
  state,boundary,spaces=[json.loads(p.read_text()) for p in paths]
  self.assertEqual(state['case_count'],432);self.assertEqual(state['summary']['candidate'],{'classic':422,'smart':422})
  self.assertEqual(boundary['case_count'],162);self.assertEqual(boundary['summary']['candidate'],{'classic':131,'smart':131})
  self.assertEqual(len(boundary['searches']),27)
  for search in boundary['searches']:
   self.assertEqual(search['first_matched_bits'],search['last_unmatched_bits']+1)
   self.assertTrue(any(v['matched'] for v in search['trace']))
   self.assertTrue(any(not v['matched'] for v in search['trace']))
  candidate=json.loads((ROOT/'reports/colorkey_lab_arithmetic_candidate_replay_20261001.json').read_text())
  self.assertEqual(candidate['summary'],{n:{'render_count':1980,'exact_count':1980} for n in ('o2','asan_ubsan')})
  for path in paths:self.assertEqual(candidate['input_report_sha256'][str(path.relative_to(ROOT))],owner.sha(path.read_bytes()))
  for report in (state,boundary,candidate):
   for path,digest in report['dependencies_sha256'].items():self.assertEqual(owner.sha((ROOT/path).read_bytes()),digest,path)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');original_fixture=owner.fixture;counts={}
  try:
   with tempfile.TemporaryDirectory(prefix='olmck_lab_production_replay_') as td:
    temp=Path(td)
    for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
     exe=owner.compile_public(temp/name,owner.SOURCE.read_text(),sanitize);n=0
     for report in (state,boundary,spaces):
      self.assertEqual(report['aex_sha256'],'9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c')
      self.assertEqual(report['worker_sha256'],'0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61')
      owner.fixture=original_fixture if report is spaces else independent.fixture
      for c in report['cases']:
       if c.get('reference_status','measured')!='measured':continue
       raw,_=owner.fixture(c['fixture'],c['depth']);self.assertEqual(owner.sha(raw),c['input_sha256'])
       self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertTrue(c['session_clean']);self.assertEqual(c['unsupported_suite_calls'],[])
       for route in (0,1):
        err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None)
        self.assertEqual(err,0);self.assertEqual(len(out),c['raw_pixel_bytes']);self.assertEqual(owner.sha(out),c['actual_sha256'],(name,c['label'],c['depth'],c.get('threshold_bits'),route));n+=1
     counts[name]=n;print('LAB_PRODUCTION_REPLAY',name,n,flush=True)
  finally:owner.fixture=original_fixture
  LAST_VALIDATION.update(source_sha256=owner.sha(owner.SOURCE.read_bytes()),successful_render_counts=counts,case_rows_replayed=990,historical_space_counterexamples_closed=108,lab94_scalar_reference_failures=36)

if __name__=='__main__':unittest.main()
