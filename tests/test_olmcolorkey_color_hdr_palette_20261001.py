"""Production decisions against independently authored typed color/HDR palettes."""
import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_color_hdr_palette_20261001 as campaign
LAST_VALIDATION={}
class ColorHdrPaletteTests(unittest.TestCase):
 def test_classifier_materialization_and_hdr_decisions(self):
  base=json.loads((ROOT/'reports/colorkey_color_hdr_palette_baseline_20261001.json').read_text());candidate=json.loads((ROOT/'reports/colorkey_classifier_materialization_candidate_replay_20261001.json').read_text())
  self.assertEqual(base['case_count'],576);self.assertEqual(base['summary'],{'classic':560,'smart':560})
  self.assertEqual(candidate['summary'],{name:{'render_count':1152,'exact_count':1152} for name in ('o2','asan_ubsan')})
  for r in (base,candidate):
   for name,digest in r['dependencies_sha256'].items():self.assertEqual(owner.sha((ROOT/name).read_bytes()),digest,name)
  self.assertEqual(sum(c['reference_kind']=='controlled-host-f32-atan2f' for c in base['cases']),48)
  self.assertEqual(sum(c['reference_kind']=='frozen-exported-owner' for c in base['cases']),528)
  original=owner.fixture;owner.fixture=campaign.fixture;env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');counts={}
  try:
   with tempfile.TemporaryDirectory(prefix='olmck_color_hdr_palette_replay_') as td:
    temp=Path(td)
    for sanitize,name in ((False,'o2'),(True,'asan_ubsan')):
     exe=owner.compile_public(temp/name,owner.SOURCE.read_text(),sanitize);n=0
     for c in base['cases']:
      raw,_=campaign.fixture(c['fixture'],c['depth']);self.assertEqual(owner.sha(raw),c['input_sha256']);self.assertEqual(c['worker_sha256'],base['controlled_worker_sha256'] if c['reference_kind']=='controlled-host-f32-atan2f' else base['frozen_worker_sha256']);self.assertTrue(c['session_clean']);self.assertEqual(c['unsupported_suite_calls'],[]);self.assertTrue(c['frame_done']['output']['guards_intact'])
      for route in (0,1):
       err,out=owner.mac_render(exe,temp,c,route,env if sanitize else None);self.assertEqual(err,0);self.assertEqual(len(out),c['raw_pixel_bytes']);self.assertEqual(owner.sha(out),c['actual_sha256'],(name,c['label'],c['depth'],route));n+=1
     counts[name]=n;print('COLOR_HDR_PALETTE_REPLAY',name,n,flush=True)
  finally:owner.fixture=original
  LAST_VALIDATION.update(source_sha256=owner.sha(owner.SOURCE.read_bytes()),captured_case_rows_replayed=576,successful_render_counts=counts,historical_counterexamples_closed=16,controlled_reference_rows=48,frozen_reference_rows=528)
if __name__=='__main__':unittest.main()
