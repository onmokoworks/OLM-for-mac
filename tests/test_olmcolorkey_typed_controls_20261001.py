import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
LAST_VALIDATION={}
class TypedControlsTests(unittest.TestCase):
 def test_initial_matte_recovery_and_measured_controls(self):
  names=('colorkey_typed_hdr_baseline_20261001.json','colorkey_signed_zero_transfer_candidate_20261001.json','colorkey_typed_palette_baseline_20261001.json','colorkey_spaces_diagnostics_20261001.json')
  hdr,transfer,palette,spaces=[json.loads((ROOT/'reports'/n).read_text()) for n in names]
  self.assertEqual(hdr['case_count'],352);self.assertEqual(hdr['summary'],{'classic':328,'smart':328})
  self.assertEqual(transfer['case_count'],1408);self.assertEqual(transfer['summary'],{'classic':1408,'smart':1408})
  self.assertEqual(palette['case_count'],216);self.assertEqual(palette['summary'],{'classic':216,'smart':216})
  self.assertEqual(spaces['case_count'],432);self.assertEqual(spaces['measured_count'],396);self.assertEqual(spaces['reference_failure_count'],36);self.assertEqual(spaces['summary'],{'classic':288,'smart':288})
  failures=[c for c in spaces['cases'] if c['reference_status']=='failed']
  self.assertTrue(all('unsupported Win64 import' in c['reference_stderr'] and '!atan2f' in c['reference_stderr'] for c in failures))
  known_differences=[c for c in spaces['cases'] if c['reference_status']=='measured' and not c['results']['classic']['exact']]
  self.assertEqual(len(known_differences),108) # Historical counterexamples remain explicit, not PASS evidence.
  for r in (hdr,transfer,palette,spaces):
   self.assertEqual(r['harness_sha256'],owner.sha(owner.HARNESS.read_bytes()))
   self.assertEqual(r['aex_sha256'],hdr['aex_sha256']);self.assertEqual(r['worker_sha256'],hdr['worker_sha256'])
  for r in (hdr,palette):self.assertEqual(r['probe_sha256'],owner.sha(Path(owner.__file__).read_bytes()))
  self.assertEqual(transfer['typed_probe_sha256'],owner.sha(Path(owner.__file__).read_bytes()))
  self.assertEqual(spaces['typed_probe_sha256'],owner.sha(Path(owner.__file__).read_bytes()))
  verified_space_cases=[c for c in spaces['cases'] if c['reference_status']=='measured' and c['results']['classic']['exact']]
  cases=hdr['cases']+transfer['cases']+palette['cases']+verified_space_cases
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');counts={};atomic=0
  with tempfile.TemporaryDirectory(prefix='olmck_typed_controls_replay_') as td:
   temp=Path(td)
   for sanitize in (False,True):
    exe=owner.compile_public(temp/('san' if sanitize else 'o2'),owner.SOURCE.read_text(),sanitize)
    selected=hdr['cases']+transfer['cases']+[c for c in palette['cases'] if next(v['value'] for v in c['parameters'] if v['slot']==22)==25] if sanitize else cases;n=0
    for c in selected:
     data,_=owner.fixture(c['fixture'],c['depth']);self.assertEqual(owner.sha(data),c['input_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertTrue(c['session_clean']);self.assertEqual(c['unsupported_suite_calls'],[])
     for route in (0,1):
      err,raw=owner.mac_render(exe,temp,c,route,env);self.assertEqual(err,0);self.assertEqual(len(raw),c['raw_pixel_bytes']);self.assertEqual(owner.sha(raw),c['actual_sha256'],(c['fixture'],c['depth'],c['label'],route));n+=1
    counts['asan_ubsan' if sanitize else 'o2']=n;print('TYPED_CONTROLS_REPLAY',sanitize,n,flush=True)
    for depth in ('PF8','PF16','PF32'):
     for thin,blur in ((-4001,0),(4001,0),(0,-1),(0,4001)):
      c={'fixture':{'id':'atomic','width':9,'height':7,'alpha':'mixed','profile':'sdr'},'depth':depth,'parameters':owner.parameters(thin=thin,blur=blur),'label':'atomic'}
      for route in (0,1):
       err,raw=owner.mac_render(exe,temp,c,route,env);self.assertNotEqual(err,0);self.assertEqual(raw,b'');atomic+=1
  LAST_VALIDATION.update(captured_case_rows_replayed=len(cases),successful_render_counts=counts,atomic_failure_render_count=atomic,source_sha256=owner.sha(owner.SOURCE.read_bytes()),unresolved_lab_counterexamples=108,reference_lab94_import_failures=36)
if __name__=='__main__':unittest.main()
