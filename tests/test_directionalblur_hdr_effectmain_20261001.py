import json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_hdr_20261001 as hdr
import test_dblur_generic_backonly_effectmain_20260821 as base
HARNESS=ROOT/'tools/emulation/directionalblur_general_features_effectmain_harness_20261001.cpp'
REPORT=ROOT/'reports/directionalblur_hdr_production_20261001.json'
class HDRPublicTests(unittest.TestCase):
 def test_public_hdr_native_hashes_and_nonfinite_rejection(self):
  r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],120);self.assertEqual(r['exact_count'],120)
  self.assertEqual(r['production_source_sha256'],'a1044ffb9a07fc1aab42fe626efa944b128513cc45580733669469327802024d')
  self.assertEqual(r['probe_sha256'],hdr.sha(Path(hdr.__file__).read_bytes()))
  self.assertTrue(all(c['public_dispatch_error']==0 and c['mac_route'] in (2,3) for c in r['cases']))
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_hdr_public_') as td:
   for sanitize in (False,True):
    directory=Path(td)/('sanitized' if sanitize else 'o2');directory.mkdir();previous=base.CPP
    try:
     base.CPP=HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp','__PRODUCTION__')
     binary=base.build(directory,sanitize)
    finally:base.CPP=previous
    for c in r['cases']:
     w,h=c['geometry'];data=hdr.pixels(w,h,c['profile']);self.assertEqual(hdr.sha(data),c['input_sha256'])
     self.assertTrue(c['frame_done']['output']['guards_intact'])
     self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
     params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
     for mode in ('classic','smart'):
      q=subprocess.run([str(binary),str(w),str(h),'32',params,mode],input=data,check=True,capture_output=True,env=env)
      lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
      self.assertEqual(int(lines['ERROR']),0);self.assertEqual(hdr.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
      self.assertEqual([int(x) for x in lines['COUNTS'].split()][:3],[21,21,1] if mode=='smart' else [0,0,0])
    for channel in range(4):
     for value in (float('nan'),float('inf'),float('-inf')):
      data=bytearray(hdr.pixels(9,7,'positive_hdr'));struct.pack_into('<f',data,channel*4,value)
      for params in ('5=7,10=11','5=7,10=11,3=37.75,15=73.75'):
       for mode in ('classic','smart'):
        q=subprocess.run([str(binary),'9','7','32',params,mode],input=bytes(data),check=True,capture_output=True,env=env)
        lines=dict(l.split(' ',1) for l in q.stdout.decode().splitlines())
        self.assertNotEqual(int(lines['ERROR']),0);self.assertEqual(lines['RAW'],'')
if __name__=='__main__':unittest.main()
