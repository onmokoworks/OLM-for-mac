import json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_layer_span_budget_20261001 as span
import probe_directionalblur_hdr_20261001 as hdr
import test_dblur_generic_backonly_effectmain_20260821 as base
REPORT=ROOT/'reports/directionalblur_layer_span_budget_production_20261001.json'
BASELINE=ROOT/'reports/directionalblur_layer_span_budget_baseline_20261001.json'
class LayerSpanBudgetTests(unittest.TestCase):
 def test_native_large_layer_outputs_actual_field_bound_and_preflight(self):
  before=json.loads(BASELINE.read_text());self.assertEqual(before['case_count'],3);self.assertEqual(before['exact_count'],0);self.assertTrue(all(c['mac_error']!=0 for c in before['cases']))
  original=(ROOT/'tools/emulation/directionalblur_layer_general_effectmain_harness_20261001.cpp').read_text().replace('w>64||h>64','w>1024||h>1024')
  self.assertEqual(before['harness_sha256'],span.sha(original.encode()))
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],3);self.assertEqual(r['exact_count'],3)
  self.assertEqual(r['production_source_sha256'],'04b74f69c77f44206c1d230b35f25ee8b9ffbda8cfb2f198fc40f56d8606b1ee');self.assertEqual(r['budget_sha256'],'ea22a8b4f3d2ec189b1af3442178e80beb6cc73dec455d66796033ab55c1a6e3')
  self.assertEqual(r['probe_sha256'],span.sha(Path(span.__file__).read_bytes()));self.assertEqual(r['harness_sha256'],span.sha(span.HARNESS.read_bytes()))
  self.assertEqual([c['native_raw_sha256'] for c in r['cases']],[c['native_raw_sha256'] for c in before['cases']]);self.assertTrue(all(c['native_layer_changes_output'] for c in r['cases']))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_layer_span_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=span.HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];data=span.source(w,h);field=span.field(w,h,c['layer_profile']);self.assertEqual(span.sha(data),c['input_sha256']);self.assertEqual(span.sha(field),c['layer_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),'32',params,mode],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0);self.assertEqual(span.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,2] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
    # Bound validation uses the actual scalar field/rotator, including signed
    # cancellation, floating overflow and final float Strength multiplication.
    for w,h in ((9,7),(37,29),(64,36)):
     data=span.source(w,h)
     for profile in ('positive_hdr','signed_rgb','extended_alpha','extreme_finite','float_boundary','full_float_max'):
      if profile=='full_float_max':
       maximum=struct.unpack('<f',struct.pack('<I',0x7f7fffff))[0]
       field=b''.join(struct.pack('<4f',maximum,maximum if i%2 else -maximum,0,.125) for i in range(w*h))
      else:field=hdr.pixels(w,h,profile)
      for angle in (-17.25,17.25,123.5):
       for noise in (1,37.75,100):
        q=subprocess.run([str(binary),str(w),str(h),'32',f'1={angle},15={noise}','boundcheck'],input=data+field,check=True,capture_output=True,env=env)
        lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(lines['BOUNDCHECK'],'1')
    # A high Layer span is rejected before touching an unreadable source.
    w,h=720,480;data=span.source(w,h);field=struct.pack('<4f',1,80,80,80)*(w*h)
    for mode in ('layerbudgetclassic','layerbudget'):
     q=subprocess.run([str(binary),str(w),str(h),'32','5=7,10=11',mode],input=data+field,check=True,capture_output=True,env=env)
     lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
