import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_olmcolorkey_around_range_20261001 as owner
class AroundRangeTests(unittest.TestCase):
 def test_exported_owner_range_replay_and_atomic_failures(self):
  read=lambda name:json.loads((ROOT/'reports'/name).read_text())
  baseline=read('colorkey_around_range_baseline_20261001.json');production=read('colorkey_around_range_production_20261001.json')
  self.assertEqual(baseline['case_count'],540);self.assertEqual(baseline['summary'],{'classic':18,'smart':18})
  self.assertEqual(production['summary'],{'classic':540,'smart':540});self.assertEqual(production['source_sha256'],owner.sha(owner.SOURCE.read_bytes()))
  self.assertEqual([c['actual_sha256'] for c in baseline['cases']],[c['actual_sha256'] for c in production['cases']])
  reports=[read(n) for n in ('colorkey_around_range_full_candidate_20261001.json','colorkey_around_range_boundary_candidate_20261001.json','colorkey_around_range_column_production_20261001.json')]
  self.assertEqual([r['case_count'] for r in reports],[6480,6480,540]);self.assertEqual(reports[1]['summary'],{'classic':6256,'smart':6256})
  self.assertEqual(reports[2]['summary'],{'classic':540,'smart':540})
  for r in [baseline,production,*reports]:
   self.assertEqual(r['probe_sha256'],owner.sha(Path(owner.__file__).read_bytes()));self.assertEqual(r['harness_sha256'],owner.sha(owner.HARNESS.encode()))
   self.assertEqual(r['worker_sha256'],production['worker_sha256']);self.assertEqual(r['aex_sha256'],production['aex_sha256'])
  float_before=read('colorkey_blur_float_materialization_candidate_20261001.json');float_after=read('colorkey_blur_float_materialization_production_20261001.json')
  self.assertEqual(float_before['summary']['range_candidate'],{'classic':24,'smart':24});self.assertEqual(float_before['summary']['float_candidate'],{'classic':30,'smart':30})
  self.assertEqual(float_after['summary']['production'],{'classic':30,'smart':30})
  self.assertEqual([c['actual_sha256'] for c in float_before['cases']],[c['actual_sha256'] for c in float_after['cases']])
  cases=[c for r in reports for c in r['cases']]
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='olmck_range_replay_') as td:
   for sanitize in (False,True):
    exe=owner.compile_public(Path(td)/('sanitized' if sanitize else 'o2'),owner.SOURCE.read_text(),sanitize)
    selected=[c for c in cases if c['fixture']['width']==1 and c['blur_type']==1] if sanitize else cases
    for c in selected:
     f=c['fixture'];source,_=owner.around.source_fixture(f,c['depth']);self.assertEqual(owner.sha(source),c['input_sha256'])
     self.assertTrue(c['guards_intact']);values={p['slot']:p.get('value') for p in c['parameter_values']}
     required={1:int(c['keep']),4:int(c['premultiplied']),14:c['thin'],15:c['type'],18:c['blur'],19:c['blur_type'],20:2,23:int(c['replace'])}
     self.assertTrue(all(values[k]==v for k,v in required.items()))
     for route in (0,1):
      err,raw=owner.mac_render(exe,f,c['depth'],c['thin'],c['type'],c['keep'],route,c['blur'],c['premultiplied'],c['replace'],c['blur_type'],env)
      self.assertEqual(err,0);self.assertEqual(owner.sha(raw),c['actual_sha256'],(f,c['thin'],c['blur_type'],c['blur'],c['depth'],route))
    for c in float_after['cases']:
     for route in (0,1):
      err,raw=owner.mac_render(exe,c['fixture'],c['depth'],0,2,c['keep'],route,c['amount'],False,False,2,env)
      self.assertEqual(err,0);self.assertEqual(owner.sha(raw),c['actual_sha256'])
    fixture={'id':'atomic','width':9,'height':7,'alpha':'mixed'}
    for depth in ('PF8','PF16','PF32'):
     for thin,blur in ((0,-1),(0,4001),(-4001,1.5),(4001,1.5)):
      for route in (0,1):
       err,raw=owner.mac_render(exe,fixture,depth,thin,2,True,route,blur,False,False,2,env)
       self.assertNotEqual(err,0);self.assertEqual(raw,b'')
if __name__=='__main__':unittest.main()
