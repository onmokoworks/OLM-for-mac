import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_native_noise_bounds_20261001 as native
import probe_directionalblur_general_features_20261001 as feature
import probe_directionalblur_fixed_getter_20261001 as fixed
REPORT=ROOT/'reports/directionalblur_native_noise_bounds_20261001.json'
class NoiseBoundsTests(unittest.TestCase):
    def test_actual_aex_table_bounds(self):
        r=json.loads(REPORT.read_text());self.assertEqual(r['case_count'],36);self.assertEqual(r['out_of_bounds_count'],12)
        self.assertEqual(r['aex_sha256'],native.sha(fixed.owner.AEX.read_bytes()))
        self.assertEqual(r['probe_sha256'],native.sha(Path(native.__file__).read_bytes()))
        self.assertEqual(r['loader_sha256'],native.sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()))
        for c in r['cases']:
            w,h=c['work_geometry'];actual=native.witness(c['offset'],c['seed'],w,h)
            for key in ('allocation_sizes','offset_normalized_bits','table_read_count','minimum_read_offset','maximum_read_offset','out_of_bounds','first_out_of_bounds','completed','executed_imports'):
                self.assertEqual(actual[key],c[key])
            if c['out_of_bounds']:
                self.assertLess(c['first_out_of_bounds']['byte_offset'],0)
                self.assertEqual(c['first_out_of_bounds']['allocation_size'],404)
    def test_candidate_rejects_invalid_reads_atomically(self):
        env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        with tempfile.TemporaryDirectory(prefix='dblur_noise_bounds_') as td:
            for sanitize in (False,True):
                binary=Path(td)/('sanitized' if sanitize else 'o2');previous=fixed.HARNESS
                try:fixed.HARNESS=feature.HARNESS;fixed.compile_harness(binary,sanitize)
                finally:fixed.HARNESS=previous
                for seed in (1,7,1000):
                    for offset in (-32768,-720,-36,-35,-18,32767):
                        for depth in (8,16,32):
                            data=feature.owner.typed(feature.owner.pixels(9,7,True),depth)
                            result=subprocess.run([str(binary),'9','7',str(depth),f'5=7,10=11,15=73.75,18={seed},19={offset}'],input=data,check=True,capture_output=True,env=env)
                            lines=dict(l.split(' ',1) for l in result.stdout.decode().splitlines())
                            if offset in (-32768,-720):
                                self.assertNotEqual(int(lines['ERROR']),0)
                                self.assertEqual(lines['RAW'],'')
                                if depth==8:
                                    self.assertNotEqual(int(lines['PUBLIC_ERROR']),0)
                                    self.assertNotEqual(int(lines['ROUTE']),1001)
                                else:
                                    self.assertEqual(int(lines['ERROR']),-1)
                                    self.assertNotEqual(int(lines['PUBLIC_ERROR']),0)
                            else:self.assertEqual(int(lines['ERROR']),0)
if __name__=='__main__':unittest.main()
