"""Verify restored Lab comparisons through composed Thin/Blur public callbacks."""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_lab_state_boundary_20261001 as independent
LAST_VALIDATION={}
class LabEdgeTransferTests(unittest.TestCase):
 def test_composed_lab_classifier_matches_owner(self):
  report=json.loads((ROOT/'reports/colorkey_lab_edge_transfer_20261001.json').read_text())
  self.assertEqual(report['case_count'],144);self.assertEqual(report['summary'],{'classic':144,'smart':144})
  self.assertEqual(report['aex_sha256'],'9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c')
  self.assertEqual(report['worker_sha256'],'0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61')
  for path,digest in report['dependencies_sha256'].items():self.assertEqual(owner.sha((ROOT/path).read_bytes()),digest,path)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');original=owner.fixture;owner.fixture=independent.fixture;counts={}
  try:
   with tempfile.TemporaryDirectory(prefix='olmck_lab_edge_replay_') as td:
    temp=Path(td)
    for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
     exe=owner.compile_public(temp/name,owner.SOURCE.read_text(),sanitize);n=0
     for c in report['cases']:
      raw,_=owner.fixture(c['fixture'],c['depth']);self.assertEqual(owner.sha(raw),c['input_sha256']);self.assertTrue(c['session_clean']);self.assertEqual(c['unsupported_suite_calls'],[]);self.assertTrue(c['frame_done']['output']['guards_intact'])
      for route in (0,1):
       err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None);self.assertEqual(err,0);self.assertEqual(len(out),c['raw_pixel_bytes']);self.assertEqual(owner.sha(out),c['actual_sha256'],(name,c['label'],c['depth'],route));n+=1
     counts[name]=n;print('LAB_EDGE_REPLAY',name,n,flush=True)
  finally:owner.fixture=original
  LAST_VALIDATION.update(source_sha256=owner.sha(owner.SOURCE.read_bytes()),successful_render_counts=counts,case_rows_replayed=144)
if __name__=='__main__':unittest.main()
