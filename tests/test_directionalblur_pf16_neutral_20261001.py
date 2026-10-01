import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_pf16_neutral_20261001 as probe
import probe_directionalblur_pf16_range_20261001 as range_probe
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_general_features_effectmain_harness_20261001.cpp'
class PF16NeutralTests(unittest.TestCase):
 def test_native_raw_range_classic_smart_odd_stride_and_cleanup(self):
  before=json.loads((ROOT/'reports/directionalblur_pf16_neutral_baseline_20261001.json').read_text())
  after=json.loads((ROOT/'reports/directionalblur_pf16_neutral_production_20261001.json').read_text())
  self.assertEqual(before['case_count'],150);self.assertEqual(before['exact_count'],150);self.assertEqual(before['public_exact_count'],42)
  self.assertEqual(after['case_count'],150);self.assertEqual(after['public_exact_count'],150)
  self.assertEqual(after['production_source_sha256'],probe.sha(probe.owner.SOURCE.read_bytes()))
  self.assertEqual(after['probe_sha256'],probe.sha(Path(probe.__file__).read_bytes()))
  self.assertEqual(after['harness_sha256'],probe.sha(probe.HARNESS.read_bytes()))
  for key in ('probe_sha256','harness_sha256','worker_sha256','aex_sha256'):self.assertEqual(before[key],after[key])
  self.assertEqual([c['native_raw_sha256'] for c in before['cases']],[c['native_raw_sha256'] for c in after['cases']])
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route']==(1 if c['mode']=='retained_back' else 2) for c in after['cases']))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_pf16_neutral_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__');binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in after['cases']:
     w,h=c['geometry'];data=range_probe.pixels(w,h,c['profile'])
     self.assertEqual(probe.sha(data),c['input_sha256']);self.assertTrue(c['frame_done']['output']['guards_intact'])
     self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),'16',','.join(f'{s}={v}' for s,v in c['parameters'].items()),mode],input=data,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0);self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,1] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
    data=range_probe.pixels(9,7,'all_extended')
    for mode in ('partial','checkin','layercheckin','checkout','output','budget','memorybudget','budgetclassic'):
     q=subprocess.run([str(binary),'9','7','16','5=7,10=11',mode],input=data,check=True,capture_output=True,env=env)
     lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
