import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_general_features_20261001 as probe
import probe_directionalblur_fixed_getter_20261001 as fixed
REPORT=ROOT/'reports/directionalblur_general_features_candidate_20261001.json'
class GeneralFeatureTests(unittest.TestCase):
    def test_retained_candidate_against_native_owner(self):
        r=json.loads(REPORT.read_text())
        self.assertEqual(r['case_count'],180);self.assertEqual(r['exact_count'],180)
        self.assertEqual(r['production_source_sha256'],probe.sha(probe.owner.SOURCE.read_bytes()))
        self.assertEqual(r['probe_sha256'],probe.sha(Path(probe.__file__).read_bytes()))
        self.assertEqual(r['harness_sha256'],probe.sha(probe.HARNESS.read_bytes()))
        env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        with tempfile.TemporaryDirectory(prefix='dblur_feature_replay_') as td:
            for sanitize in (False,True):
                binary=Path(td)/('sanitized' if sanitize else 'o2');previous=fixed.HARNESS
                try:fixed.HARNESS=probe.HARNESS;fixed.compile_harness(binary,sanitize)
                finally:fixed.HARNESS=previous
                for c in r['cases']:
                    self.assertTrue(c['exact']);self.assertEqual(c['mac_route'],1001)
                    self.assertNotEqual(c['public_dispatch_error'],0)
                    w,h=c['geometry'];data=probe.owner.typed(probe.owner.pixels(w,h,True),c['depth'])
                    self.assertEqual(probe.sha(data),c['input_sha256'])
                    self.assertTrue(c['frame_done']['output']['guards_intact'])
                    self.assertEqual(c['frame_done']['output']['checksum'],c['native_raw_sha256'])
                    params=','.join(f'{s}={v}' for s,v in c['parameters'].items())
                    result=subprocess.run([str(binary),str(w),str(h),str(c['depth']),params],input=data,check=True,capture_output=True,env=env)
                    lines=dict(l.split(' ',1) for l in result.stdout.decode().splitlines())
                    self.assertEqual(int(lines['PUBLIC_ERROR']),c['public_dispatch_error'])
                    self.assertEqual(int(lines['ERROR']),0)
                    self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['native_raw_sha256'])
if __name__=='__main__':unittest.main()
