import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_general_input_20261001 as owner
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_general_features_effectmain_harness_20261001.cpp'
REPORT=ROOT/'reports/directionalblur_general_features_production_20261001.json'
class GeneralPublicTests(unittest.TestCase):
 def test_classic_and_smart_native_hashes_and_cleanup(self):
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],180);self.assertEqual(r['exact_count'],180)
  self.assertEqual(r['production_source_sha256'],owner.sha(owner.SOURCE.read_bytes()))
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route']==3 for c in r['cases']))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_feature_public_') as td:
   for sanitize in (False,True):
    build_dir=Path(td)/('sanitized' if sanitize else 'o2');build_dir.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(build_dir,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];data=owner.typed(owner.pixels(w,h,True),c['depth'])
     self.assertEqual(owner.sha(data),c['input_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),str(c['depth']),params,mode],input=data,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
      self.assertEqual(int(lines['ERROR']),0);self.assertEqual(owner.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()]
      self.assertEqual(counts[:3],[21,21,1] if mode=='smart' else [0,0,0])
    for depth in (16,32):
     data=owner.typed(owner.pixels(9,7,True),depth)
     for mode in ('partial','checkin','layercheckin','checkout','output','budget','memorybudget','negative','budgetclassic','negativeclassic'):
      q=subprocess.run([str(binary),'9','7',str(depth),'5=7,10=11,3=37.75,15=73.75',mode],input=data,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
      self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
