import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/'tools/emulation/probe_directionalblur_general_input_20261001.py'
spec=importlib.util.spec_from_file_location('dblur_owner',PROBE)
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
REPORTS=('directionalblur_general_input_production_20261001.json',
         'directionalblur_general_input_boundary_production_20261001.json',
         'directionalblur_general_input_signed_production_20261001.json')

class DirectionalOwnerTests(unittest.TestCase):
    def test_current_parameter_getter_and_dispatcher_exact(self):
        with tempfile.TemporaryDirectory(prefix='dblur_owner_replay_') as td:
            binary=Path(td)/'normal';sanitized=Path(td)/'sanitized'
            probe.compile_harness(binary);probe.compile_harness(sanitized,True)
            env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
            for name in REPORTS:
                r=json.loads((ROOT/'reports'/name).read_text())
                self.assertEqual(r['exact_count'],54);self.assertEqual(len(r['cases']),54)
                self.assertEqual(r['production_source_sha256'],probe.sha(probe.SOURCE.read_bytes()))
                self.assertEqual(r['probe_sha256'],probe.sha(PROBE.read_bytes()))
                self.assertEqual(r['harness_sha256'],probe.sha(probe.HARNESS.read_bytes()))
                for core,digest in r['core_sha256'].items():self.assertEqual(digest,probe.sha((ROOT/'core'/core).read_bytes()))
                for c in r['cases']:
                    w,h=c['geometry'];data=probe.typed(probe.pixels(w,h,c['fixture']=='odd-mixed'),c['depth'])
                    self.assertEqual(probe.sha(data),c['input_sha256'])
                    self.assertEqual(c['frame_done']['output']['checksum'],c['windows_raw_sha256'])
                    self.assertTrue(c['frame_done']['output']['guards_intact']);self.assertTrue(c['raw_exact'])
                    self.assertEqual(c['mac_materialized_angle'],math.floor(c['angle']))
                    self.assertEqual(c['mac_route'],2)
                    for exe in (binary,sanitized):
                        out=subprocess.run([str(exe),str(w),str(h),str(c['depth']),str(c['angle']),str(c['front']),str(c['back'])],input=data,check=True,capture_output=True,env=env)
                        lines=dict(l.split(' ',1) for l in out.stdout.decode().splitlines())
                        self.assertEqual(probe.sha(bytes.fromhex(lines['RAW'])),c['windows_raw_sha256'])
                        self.assertEqual(float(lines['ANGLE']),math.floor(c['angle']))
                        self.assertEqual(int(lines['ROUTE']),2)

if __name__=='__main__':unittest.main()
