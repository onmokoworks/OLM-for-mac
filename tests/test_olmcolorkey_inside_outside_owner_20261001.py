import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_inside_outside_owner_20261001 as owner
import colorkey_public_blur_candidate_20261001 as recovery
LAST_VALIDATION={}
class InsideOutsideTests(unittest.TestCase):
 def test_exported_owner_replay_and_atomic_failures(self):
  names=('colorkey_inside_outside_baseline_candidate_20261001.json','colorkey_inside_outside_boundary_candidate_20261001.json','colorkey_inside_outside_toggle_candidate_20261001.json')
  reports=[json.loads((ROOT/'reports'/name).read_text()) for name in names]
  self.assertEqual([r['case_count'] for r in reports],[1404,4212,5616])
  self.assertEqual(reports[0]['summary'],{'production':{'classic':222,'smart':222},'candidate':{'classic':1392,'smart':1392}})
  for r in reports[1:]:
   self.assertEqual(r['summary']['candidate'],{'classic':r['case_count'],'smart':r['case_count']})
   self.assertEqual(r['recovery_candidate_tool_sha256'],owner.sha(Path(recovery.__file__).read_bytes()))
   self.assertEqual(r['recovery_probe_sha256'],owner.sha((ROOT/'tools/emulation/probe_olmcolorkey_public_blur_recovery_20261001.py').read_bytes()))
  for r in reports:
   self.assertEqual(r['probe_sha256'],owner.sha(Path(owner.__file__).read_bytes()))
   self.assertEqual(r['harness_sha256'],owner.sha(owner.HARNESS.encode()))
   self.assertEqual(r['aex_sha256'],reports[0]['aex_sha256']);self.assertEqual(r['worker_sha256'],reports[0]['worker_sha256'])
  nan=json.loads((ROOT/'reports/colorkey_blur_nan_semantics_20261001.json').read_text())
  self.assertEqual(nan['case_count'],12);self.assertEqual(nan['native_case_report_sha256'],owner.sha((ROOT/'reports'/names[0]).read_bytes()))
  self.assertTrue(all(c['results']['revised']['exact'] and not c['results']['first']['exact'] for c in nan['cases']))
  cases=[c for r in reports for c in r['cases']];env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1');counts={};atomic=0
  with tempfile.TemporaryDirectory(prefix='olmck_inside_outside_replay_') as td:
   for sanitize in (False,True):
    exe=owner.compile_public(Path(td)/('sanitized' if sanitize else 'o2'),owner.SOURCE.read_text(),sanitize)
    selected=[c for c in cases if (c['fixture']['width']==1 and c['blur_type']==1) or c['blur'] in (0,1e-50,1e-40)] if sanitize else cases;n=0
    for c in selected:
     source,_=owner.around.source_fixture(c['fixture'],c['depth']);self.assertEqual(owner.sha(source),c['input_sha256'])
     self.assertTrue(c['guards_intact']);values={p['slot']:p.get('value') for p in c['parameter_values']}
     required={1:int(c['keep']),4:int(c['premultiplied']),14:c['thin'],15:c['type'],18:c['blur'],19:c['blur_type'],20:c['direction'],23:int(c['replace'])}
     self.assertTrue(all(values[k]==v for k,v in required.items()))
     for route in (0,1):
      err,raw=owner.mac_render(exe,c,route,env)
      self.assertEqual(err,0);self.assertEqual(len(raw),c['raw_pixel_bytes']);self.assertEqual(owner.sha(raw),c['actual_sha256'],(c['fixture'],c['direction'],c['thin'],c['blur_type'],c['blur'],c['depth'],route));n+=1
    counts['asan_ubsan' if sanitize else 'o2']=n
    for direction in (1,3):
     for depth in ('PF8','PF16','PF32'):
      for thin,blur in ((0,-1),(0,4001),(-4001,1.5),(4001,1.5)):
       c={'fixture':{'id':'atomic','width':9,'height':7,'alpha':'mixed'},'depth':depth,'thin':thin,'type':2,'keep':True,'blur':blur,'premultiplied':False,'replace':False,'blur_type':2,'direction':direction}
       for route in (0,1):
        err,raw=owner.mac_render(exe,c,route,env);self.assertNotEqual(err,0);self.assertEqual(raw,b'');atomic+=1
    print('PUBLIC_BLUR_REPLAY',sanitize,n,flush=True)
  LAST_VALIDATION.update(native_case_count=len(cases),successful_render_counts=counts,atomic_failure_render_count=atomic,source_sha256=owner.sha(owner.SOURCE.read_bytes()))
if __name__=='__main__':unittest.main()
