import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_layer_geometry_disabled_20261001 as geo
import probe_directionalblur_layer_general_20261001 as layer
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_layer_geometry_effectmain_harness_20261001.cpp'
REPORT=ROOT/'reports/directionalblur_layer_geometry_production_20261001.json'
NONE=ROOT/'reports/directionalblur_layer_none_20261001.json'
class LayerGeometryPublicTests(unittest.TestCase):
 def test_native_dimension_gate_and_classic_smart_no_field_identity(self):
  failed=json.loads((ROOT/'reports/directionalblur_layer_geometry_baseline_20261001.json').read_text())
  self.assertEqual(failed['case_count'],288);self.assertEqual(failed['exact_count'],0);self.assertEqual(failed['native_cropped_control_exact_count'],0)
  baseline=json.loads((ROOT/'reports/directionalblur_layer_geometry_disabled_baseline_20261001.json').read_text())
  self.assertEqual(baseline['exact_count'],288);self.assertTrue(all(c['public_dispatch_error']!=0 and c['mac_route']==1001 for c in baseline['cases']))
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],288);self.assertEqual(r['exact_count'],288);self.assertEqual(r['native_disabled_control_exact_count'],288)
  self.assertEqual(r['production_source_sha256'],geo.sha(geo.owner.SOURCE.read_bytes()));self.assertEqual(r['probe_sha256'],geo.sha(Path(geo.__file__).read_bytes()));self.assertEqual(r['harness_sha256'],geo.sha(geo.HARNESS.read_bytes()))
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route'] in (2,3) for c in r['cases']))
  self.assertEqual([c['native_raw_sha256'] for c in baseline['cases']],[c['native_raw_sha256'] for c in r['cases']])
  none=json.loads(NONE.read_text());self.assertEqual(none['case_count'],54);self.assertEqual(none['exact_count'],54)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_geometry_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];lw,lh=c['layer_geometry'];depth=c['depth']
     data=geo.owner.typed(geo.owner.pixels(w,h,True),depth);field=geo.owner.typed(layer.layer_pixels(lw,lh,c['layer_profile']),depth)
     self.assertEqual(geo.sha(data),c['input_sha256']);self.assertEqual(geo.sha(field),c['layer_sha256'])
     self.assertTrue(c['native_disabled_control_exact']);self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),str(depth),params,mode,str(lw),str(lh)],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0);self.assertEqual(geo.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,2] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
    for c in none['cases']:
     w,h=c['geometry'];depth=c['depth'];data=geo.owner.typed(geo.owner.pixels(w,h,True),depth);field=geo.owner.typed(layer.layer_pixels(w,h,'inverse'),depth)
     self.assertTrue(c['frame_done']['output']['guards_intact']);params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('noneclassic','none'):
      q=subprocess.run([str(binary),str(w),str(h),str(depth),params,mode,str(w),str(h)],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0);self.assertEqual(geo.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      self.assertEqual([int(x) for x in lines['COUNTS'].split()][:3],[21,21,1] if mode=='none' else [0,0,0])
    # Inactive Layer payloads must never be read or queried for their format.
    for depth in (16,32):
     data=geo.owner.typed(geo.owner.pixels(9,7,True),depth);field=geo.owner.typed(layer.layer_pixels(5,4,'inverse'),depth)
     witness=next(c for c in r['cases'] if c['geometry']==[9,7] and c['layer_geometry']==[5,4] and c['depth']==depth and c['mode']=='dual' and c['feature']=='components' and c['layer_profile']=='inverse')
     params=','.join(f'{s}={v}' for s,v in witness['parameters'].items())
     for mode in ('ignoredpoison','ignoredpoisonclassic','ignoredalias','ignoredaliasclassic'):
      q=subprocess.run([str(binary),'9','7',str(depth),params,mode,'5','4'],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertEqual(int(lines['ERROR']),0,mode);self.assertEqual(geo.sha(bytes.fromhex(lines['RAW'])),witness['native_raw_sha256'])
    # A consumed Layer still requires valid dimensions, format and payload.
    for depth in (16,32):
     data=geo.owner.typed(geo.owner.pixels(9,7,True),depth);field=geo.owner.typed(layer.layer_pixels(9,7,'inverse'),depth)
     modes=['partial','checkin','layercheckin','checkout','output','budget','budgetclassic','memorybudget']
     modes += [m+suffix for m in ('rowbytes','origin','format','formaterror','alias') for suffix in ('','classic')]
     for mode in modes:
      q=subprocess.run([str(binary),'9','7',str(depth),'5=7,10=11,3=37.75',mode,'9','7'],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0,mode);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
