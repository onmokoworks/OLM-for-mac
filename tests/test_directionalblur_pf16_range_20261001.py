import json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_pf16_range_20261001 as probe
import probe_directionalblur_pf16_source_features_20261001 as source_probe
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_pf16_range_effectmain_harness_20261001.cpp'
class PF16RangeTests(unittest.TestCase):
 def test_native_range_classic_smart_and_actual_layer_bound(self):
  before=json.loads((ROOT/'reports/directionalblur_pf16_range_baseline_20261001.json').read_text())
  after=json.loads((ROOT/'reports/directionalblur_pf16_range_production_20261001.json').read_text())
  self.assertEqual(before['case_count'],144);self.assertEqual(before['exact_count'],144);self.assertEqual(before['public_exact_count'],0)
  self.assertEqual(after['case_count'],144);self.assertEqual(after['public_exact_count'],144)
  self.assertEqual(after['production_source_sha256'],'3c91c7af8c3bc0c0abe2bcbd9a1806b2cab95cc55ac41823ead5a79269313638')
  self.assertEqual(after['budget_sha256'],probe.sha((ROOT/'core/dblur_generic_budget.h').read_bytes()))
  self.assertEqual(after['probe_sha256'],probe.sha(Path(probe.__file__).read_bytes()))
  for key in ('probe_sha256','harness_sha256','worker_sha256','aex_sha256'):self.assertEqual(before[key],after[key])
  self.assertEqual([c['native_raw_sha256'] for c in before['cases']],[c['native_raw_sha256'] for c in after['cases']])
  supplement=json.loads((ROOT/'reports/directionalblur_pf16_source_features_production_20261001.json').read_text())
  self.assertEqual(supplement['case_count'],72);self.assertEqual(supplement['public_exact_count'],72)
  self.assertEqual(supplement['production_source_sha256'],'3c91c7af8c3bc0c0abe2bcbd9a1806b2cab95cc55ac41823ead5a79269313638')
  self.assertEqual(supplement['probe_sha256'],probe.sha(Path(source_probe.__file__).read_bytes()))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_pf16_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__');binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in after['cases']+supplement['cases']:
     w,h=c['geometry'];profile=c['profile'];placement=c['placement']
     data=probe.pixels(w,h,profile if placement!='layer' else 'sdr');field=probe.pixels(w,h,profile if placement!='source' else 'sdr')
     self.assertEqual(probe.sha(data),c['input_sha256']);
     if 'layer_sha256' in c:self.assertEqual(probe.sha(field),c['layer_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),'16',','.join(f'{s}={v}' for s,v in c['parameters'].items()),mode],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0);self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,2] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
    for w,h in ((9,7),(37,29),(64,36)):
     data=probe.pixels(w,h,'sdr')
     for profile in ('rgb_extended','alpha_extended','all_extended','boundary'):
      field=probe.pixels(w,h,profile)
      for angle in (-17.25,17.25,123.5):
       for noise in (1,37.75,100):
        q=subprocess.run([str(binary),str(w),str(h),'16',f'1={angle},15={noise}','boundcheck'],input=data+field,check=True,capture_output=True,env=env)
        lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(lines['BOUNDCHECK'],'1')
    # Max uint16 Layer coefficients amplify the span to almost four. Final
    # admission must reject this workload before reading the poisoned source.
    w,h=720,480;data=probe.pixels(w,h,'sdr');field=struct.pack('<4H',65535,65535,65535,65535)*(w*h)
    for mode in ('layerbudgetclassic','layerbudget'):
     q=subprocess.run([str(binary),str(w),str(h),'16','5=80,10=80,15=100',mode],input=data+field,check=True,capture_output=True,env=env)
     lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
