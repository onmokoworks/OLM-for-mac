import collections,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_layer_20261001 as layer
import probe_directionalblur_fixed_getter_20261001 as fixed
import test_dblur_generic_backonly_effectmain_20260821 as base
REPORT=ROOT/'reports/directionalblur_layer_baseline_20261001.json'
CHOICES=ROOT/'reports/directionalblur_layer_declared_choices_20261001.json'
class LayerWitnessTests(unittest.TestCase):
 def test_independent_layer_typed_candidate_against_native(self):
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],72);self.assertEqual(r['exact_count'],72)
  self.assertEqual(r['production_source_sha256'],layer.sha(layer.owner.SOURCE.read_bytes()))
  self.assertEqual(r['probe_sha256'],layer.sha(Path(layer.__file__).read_bytes()))
  self.assertEqual(r['harness_sha256'],layer.sha(layer.HARNESS.read_bytes()))
  groups=collections.defaultdict(list)
  for c in r['cases']:groups[(tuple(c['geometry']),c['depth'],c['mode'],c['feature'])].append(c['native_raw_sha256'])
  self.assertEqual(len(groups),36);self.assertTrue(all(len(set(v))==2 for v in groups.values()))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_layer_replay_') as td:
   for sanitize in (False,True):
    binary=Path(td)/('sanitized' if sanitize else 'o2');previous=fixed.HARNESS
    try:fixed.HARNESS=layer.HARNESS;fixed.compile_harness(binary,sanitize)
    finally:fixed.HARNESS=previous
    for c in r['cases']:
     self.assertTrue(c['exact']);self.assertEqual(c['mac_route'],1001);self.assertNotEqual(c['public_dispatch_error'],0)
     w,h=c['geometry'];data=layer.owner.typed(layer.owner.pixels(w,h,True),c['depth']);field=layer.owner.typed(layer.layer_pixels(w,h,c['layer_profile']),c['depth'])
     self.assertEqual(layer.sha(data),c['input_sha256']);self.assertEqual(layer.sha(field),c['layer_sha256']);self.assertNotEqual(data,field)
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     q=subprocess.run([str(binary),str(w),str(h),str(c['depth']),params],input=data+field,check=True,capture_output=True,env=env)
     lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
     self.assertEqual(int(lines['PUBLIC_ERROR']),c['public_dispatch_error']);self.assertEqual(int(lines['ERROR']),0)
     self.assertEqual(layer.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
 def test_declared_choices_and_real_mac_parameter_setup(self):
  r=json.loads(CHOICES.read_text());self.assertEqual(r['selected_layer_case_count'],8);self.assertEqual(r['selected_layers_match_generated_count'],8)
  native=next(p for p in r['native_declarations'] if p['slot']==16)
  self.assertEqual(native['valid_max'],2);self.assertEqual(len(native['choices'].split('|')),3)
  for c in r['cases']:
   for selected in c['selected_layer_cases']:
    self.assertTrue(selected['matches_unselected_layer']);self.assertEqual(selected['native_raw_sha256'],c['unselected_layer_raw_sha256'])
    self.assertTrue(selected['frame_done']['output']['guards_intact'])
  with tempfile.TemporaryDirectory(prefix='dblur_layer_setup_') as td:
   previous=base.CPP
   try:
    base.CPP=(ROOT/'tools/emulation/directionalblur_layer_params_harness_20261001.cpp').read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
    binary=base.build(Path(td),False)
   finally:base.CPP=previous
   q=subprocess.run([str(binary)],check=True,capture_output=True)
   lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
   self.assertEqual(int(lines['ERROR']),0);self.assertEqual(int(lines['COUNT']),21)
   self.assertEqual(int(lines['CHOICES']),native['valid_max']);self.assertEqual(int(lines['LABELS']),3)
if __name__=='__main__':unittest.main()
