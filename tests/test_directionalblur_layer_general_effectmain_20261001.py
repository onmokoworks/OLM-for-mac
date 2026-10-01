import json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_layer_general_20261001 as layer
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_layer_general_effectmain_harness_20261001.cpp'
REPORT=ROOT/'reports/directionalblur_layer_general_production_20261001.json'
class LayerPublicTests(unittest.TestCase):
 def test_classic_smart_odd_stride_native_outputs_and_atomic_cleanup(self):
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],120);self.assertEqual(r['exact_count'],120)
  self.assertEqual(r['production_source_sha256'],'8c9c0c34e220d3cd281d7b1ba3c6673704af42437fbc02dba30de8d5f7fa8010')
  self.assertEqual(r['probe_sha256'],layer.sha(Path(layer.__file__).read_bytes()))
  self.assertEqual(r['harness_sha256'],layer.sha(layer.HARNESS.read_bytes()))
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route']==3 for c in r['cases']))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_layer_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];depth=c['depth']
     data=layer.owner.typed(layer.owner.pixels(w,h,True),depth)
     field=layer.owner.typed(layer.layer_pixels(w,h,c['layer_profile']),depth)
     self.assertEqual(layer.sha(data),c['input_sha256']);self.assertEqual(layer.sha(field),c['layer_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),str(depth),params,mode],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
      self.assertEqual(int(lines['ERROR']),0);self.assertEqual(layer.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[:3],[21,21,2] if mode=='smart' else [0,0,0]);self.assertEqual(counts[3],counts[4])
    for depth in (16,32):
     data=layer.owner.typed(layer.owner.pixels(9,7,True),depth)
     field=layer.owner.typed(layer.layer_pixels(9,7,'inverse'),depth)
     modes=['partial','checkin','layercheckin','checkout','output','budget','budgetclassic','memorybudget']
     modes += ['missingclassic']
     modes += [m+suffix for m in ('rowbytes','origin','format','formaterror','alias') for suffix in ('','classic')]
     for mode in modes:
      q=subprocess.run([str(binary),'9','7',str(depth),'5=7,10=11,3=37.75',mode],input=data+field,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0,mode);self.assertEqual(lines['RAW'],'')
      counts=[int(x) for x in lines['COUNTS'].split()];self.assertEqual(counts[3],counts[4])
      if mode=='layercheckin':self.assertEqual(counts[:3],[21,21,2])
     # Every Layer channel is checked before processing, using unaligned rows.
     for channel in range(4):
      for value in ([32769] if depth==16 else [float('nan'),float('inf'),float('-inf')]):
       bad=bytearray(field);struct.pack_into('<H' if depth==16 else '<f',bad,channel*(2 if depth==16 else 4),value)
       for mode in ('classic','smart'):
        q=subprocess.run([str(binary),'9','7',str(depth),'5=7,10=11,3=37.75',mode],input=data+bad,check=True,capture_output=True,env=env)
        lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines());self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
