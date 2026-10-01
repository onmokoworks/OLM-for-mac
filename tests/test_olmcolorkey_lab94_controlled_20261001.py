"""Replay controlled Lab94 exported-owner output without substituting UCRT claims."""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
LAST_VALIDATION={}
class ControlledLab94Tests(unittest.TestCase):
 def test_authored_double_slider_and_controlled_scalar_owner(self):
  controlled,double=[json.loads((ROOT/'reports'/n).read_text()) for n in ('colorkey_lab94_controlled_owner_20261001.json','colorkey_lab94_double_slider_20261001.json')]
  self.assertEqual(controlled['case_count'],630);self.assertEqual(controlled['calibration_count'],396);self.assertEqual(controlled['calibration_exact_count'],396)
  self.assertEqual(double['case_count'],594);self.assertEqual(double['summary']['production'],{'classic':492,'smart':492});self.assertEqual(double['summary']['candidate'],{'classic':594,'smart':594})
  for search in controlled['searches']:
   self.assertEqual(search['first_matched_bits'],search['last_unmatched_bits']+1);self.assertTrue(any(v['matched'] for v in search['trace']));self.assertTrue(any(not v['matched'] for v in search['trace']))
  build=json.loads((ROOT/'reports/colorkey_lab94_controlled_worker_build_20261001.json').read_text())
  self.assertTrue(build['frozen_source_and_worker_unchanged']);self.assertEqual(build['controlled_worker_sha256'],controlled['controlled_worker_sha256']);self.assertEqual(build['patch_sha256'],owner.sha((ROOT/'tools/emulation/aexcompat_colorkey_lab94_controlled_atan2f_20261001.patch').read_bytes()))
  self.assertEqual(controlled['frozen_worker_sha256'],'0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61')
  for r in (controlled,double):
   self.assertEqual(r['aex_sha256'],'9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c');self.assertEqual(r['controlled_worker_sha256'],build['controlled_worker_sha256'])
   for name,digest in r['dependencies_sha256'].items():self.assertEqual(owner.sha((ROOT/name).read_bytes()),digest,name)
  original=owner.fixture
  def choose(f,depth):return original(f,depth) if 'profile' in f else independent.fixture(f,depth)
  owner.fixture=choose;env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');counts={}
  try:
   with tempfile.TemporaryDirectory(prefix='olmck_lab94_production_replay_') as td:
    temp=Path(td)
    for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
     exe=owner.compile_public(temp/name,owner.SOURCE.read_text(),sanitize);n=0
     for r in (controlled,double):
      for c in r['cases']:
       raw,_=choose(c['fixture'],c['depth']);self.assertEqual(owner.sha(raw),c['input_sha256']);self.assertTrue(c['session_clean']);self.assertEqual(c['unsupported_suite_calls'],[]);self.assertTrue(c['frame_done']['output']['guards_intact'])
       for route in (0,1):
        err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None);self.assertEqual(err,0);self.assertEqual(len(out),c['raw_pixel_bytes']);self.assertEqual(owner.sha(out),c['actual_sha256'],(name,c['label'],c['depth'],route));n+=1
     counts[name]=n;print('CONTROLLED_LAB94_REPLAY',name,n,flush=True)
  finally:owner.fixture=original
  LAST_VALIDATION.update(source_sha256=owner.sha(owner.SOURCE.read_bytes()),case_rows_replayed=1224,successful_render_counts=counts,double_slider_historical_differences_closed=102,reference_kind='controlled-host-f32-atan2f',native_windows_ucrt_verified=False)
if __name__=='__main__':unittest.main()
