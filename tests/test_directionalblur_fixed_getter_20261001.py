import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
import probe_directionalblur_fixed_getter_20261001 as probe
REPORT=ROOT/'reports/directionalblur_fixed_getter_core_partition_production_20261001.json'

class FixedGetterTests(unittest.TestCase):
    def test_native_builder_and_typed_core_partition(self):
        r=json.loads(REPORT.read_text())
        self.assertTrue(r['core_candidate'])
        self.assertEqual(r['getter_exact_count'],47);self.assertEqual(r['render_exact_count'],135)
        self.assertEqual(r['production_source_sha256'],'9c105f51a3e2659b42d9f07faca3ef68ab947a295df19bbea473e028ee93df1a')
        self.assertEqual(r['probe_sha256'],probe.sha(Path(probe.__file__).read_bytes()))
        self.assertEqual(r['harness_sha256'],probe.sha(probe.HARNESS.read_bytes()))
        self.assertEqual(r['loader_sha256'],probe.sha((ROOT/'tools/emulation/aex_loader.py').read_bytes()))
        env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        with tempfile.TemporaryDirectory(prefix='dblur_fixed_replay_') as td:
            binaries=(Path(td)/'o2',Path(td)/'sanitized')
            probe.compile_harness(binaries[0]);probe.compile_harness(binaries[1],True)
            for c in r['getter_cases']:
                self.assertTrue(c['getter_exact']);self.assertTrue(c['native_equals_whole_control'])
                self.assertEqual(c['native']['executed_imports'],['memset'])
                data=probe.owner.typed(probe.owner.pixels(7,5,True),8)
                for binary in binaries:
                    out=subprocess.run([str(binary),'7','5','8',str(c['slot']),str(c['value'])],input=data,check=True,capture_output=True,env=env)
                    lines=dict(l.split(' ',1) for l in out.stdout.decode().splitlines())
                    self.assertEqual(int(lines['BITS']),c['native']['normalized_bits'])
                    self.assertEqual(float(lines['INFO']),math.floor(c['value']))
            for c in r['render_cases']:
                self.assertTrue(c['raw_exact']);self.assertEqual(c['classification'],'exact')
                w,h=c['geometry'];data=probe.owner.typed(probe.owner.pixels(w,h,True),c['depth'])
                self.assertEqual(probe.sha(data),c['input_sha256'])
                self.assertEqual(c['frame_done']['output']['checksum'],c['windows_raw_sha256'])
                self.assertTrue(c['frame_done']['output']['guards_intact'])
                for binary in binaries:
                    args=[str(binary),str(w),str(h),str(c['depth']),str(c['slot']),str(c['value'])]
                    # Retained capture had deep feature refusals. Current public
                    # dispatcher must match every native hash without bypass.
                    public=subprocess.run(args,input=data,check=True,capture_output=True,env=env)
                    lines=dict(l.split(' ',1) for l in public.stdout.decode().splitlines())
                    self.assertEqual(int(lines['ERROR']),0)
                    if not int(lines['ERROR']):
                        self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['windows_raw_sha256'])
                    out=subprocess.run(args+['1'],input=data,check=True,capture_output=True,env=env)
                    lines=dict(l.split(' ',1) for l in out.stdout.decode().splitlines())
                    self.assertEqual(int(lines['ERROR']),0)
                    self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['windows_raw_sha256'])

if __name__=='__main__':unittest.main()
