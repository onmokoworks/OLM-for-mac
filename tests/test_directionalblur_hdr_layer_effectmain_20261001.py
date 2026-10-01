import collections,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_hdr_layer_20261001 as hdr_layer
import probe_directionalblur_hdr_20261001 as hdr
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_layer_general_effectmain_harness_20261001.cpp'
REPORT=ROOT/'reports/directionalblur_hdr_layer_production_20261001.json'
BASELINE=ROOT/'reports/directionalblur_hdr_layer_baseline_20261001.json'
class HDRLayerPublicTests(unittest.TestCase):
 def test_sse_correction_and_native_hdr_layer_outputs(self):
  baseline=json.loads(BASELINE.read_text());self.assertEqual(baseline['case_count'],180);self.assertEqual(baseline['exact_count'],144)
  self.assertEqual(sum(c['mac_process_returncode']==-11 for c in baseline['cases']),24)
  self.assertEqual(sum(c['mac_process_returncode']==0 and not c['exact'] for c in baseline['cases']),12)
  self.assertTrue(all(c['layer_profile']=='extreme_finite' for c in baseline['cases'] if not c['exact']))
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],180);self.assertEqual(r['exact_count'],180)
  self.assertEqual(r['production_source_sha256'],hdr_layer.sha(hdr_layer.owner.SOURCE.read_bytes()))
  self.assertEqual(r['probe_sha256'],hdr_layer.sha(Path(hdr_layer.__file__).read_bytes()))
  self.assertEqual(r['harness_sha256'],hdr_layer.sha(hdr_layer.HARNESS.read_bytes()))
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route']==3 and c['mac_process_returncode']==0 for c in r['cases']))
  self.assertEqual([c['native_raw_sha256'] for c in r['cases']],[c['native_raw_sha256'] for c in baseline['cases']])
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_hdr_layer_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];data=hdr_layer.input_pixels(w,h,c['input_profile']);field=hdr.pixels(w,h,c['layer_profile'])
     self.assertEqual(hdr_layer.sha(data),c['input_sha256']);self.assertEqual(hdr_layer.sha(field),c['layer_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),'32',params,mode],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
      self.assertEqual(int(lines['ERROR']),0);self.assertEqual(hdr_layer.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,2] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
if __name__=='__main__':unittest.main()
