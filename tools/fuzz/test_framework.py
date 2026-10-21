"""Focused tests for reproducibility, bit comparison, rejection and reduction."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import (apply_operation, command, evaluate, load_corpus, mismatch_routes,
                  raw_diff, save_corpus, sha, shrink)
from adapters.radialblur import Adapter, ROOT

SCRATCH = ROOT/'orchestra/state/T02-fuzz-framework-radialblur'


def make_adapter():
    return Adapter(argparse.Namespace(max_size=256, case_timeout=2,
                                     main=ROOT, worker=Path(sys.executable)))


class Synthetic:
    name = 'synthetic'
    generator_version = 1
    max_size = 256
    routes = ('classic', 'smart')

    def defaults(self, w, h):
        return [{'slot':1,'kind':'i','value':0}]

    def generate(self, seed, index):
        return {'seed':seed, 'index':index, 'geometry':[8,8], 'depth':8,
                'parameters':[{'slot':1,'kind':'i','value':8}],
                'pixels':bytes(range(256))}

    def resize(self, case, old_geometry):
        return case

    def simple_pixels(self, case):
        return bytes(int(v >= 128) for v in case['pixels'])

    def oracle(self, case, directory, deadline):
        if case['parameters'][0]['value'] == 0:
            return {'status':'reject'}, b''
        return {'status':'ok'}, bytes(len(case['pixels']))

    def candidate(self, case, directory, route, deadline):
        size = len(case['pixels'])
        mismatches = min(case['geometry']) >= 2 and case['parameters'][0]['value'] >= 2
        return {'status':'ok'}, (b'\x01'+bytes(size-1)) if mismatches else bytes(size)

    def first_stage(self, case, directory, results, deadline):
        return 'synthetic-stage'


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='unit_', dir=SCRATCH)
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_production_debug_environment_is_not_inherited(self):
        with patch.dict(os.environ, {'OLMRADIALBLUR_DEBUG_DUMP_PATH':'outside-scratch',
                                    'OLMRADIALBLUR_FORCE_SCALAR_PRODUCER':'1'}):
            adapter = make_adapter()
        self.assertNotIn('OLMRADIALBLUR_DEBUG_DUMP_PATH', adapter.env)
        self.assertNotIn('OLMRADIALBLUR_FORCE_SCALAR_PRODUCER', adapter.env)

    def test_bits_not_numeric_equality(self):
        positive = struct.pack('<II', 0, 0x7fc00001)
        negative = struct.pack('<II', 0x80000000, 0x7fc00002)
        result = raw_diff(positive, negative, 32)
        self.assertEqual(result['different_words'], 2)
        self.assertEqual(result['first_word'], 0)
        self.assertEqual(raw_diff(b'ab',b'abc',8)['different_bytes'], 1)
        self.assertEqual(raw_diff(b'abc',b'ab',8)['different_words'], 1)

    def test_generator_legal_and_reproducible(self):
        adapter = make_adapter()
        depths, geometries, profiles, padding = set(), set(), set(), set()
        declarations = {p['slot']:p for p in adapter.controls}
        for index in range(500):
            case = adapter.generate(1, index)
            self.assertEqual(case, adapter.generate(1, index))
            self.assertNotEqual(case['pixels'], adapter.generate(2,index)['pixels'])
            w,h = case['geometry']
            self.assertTrue(1 <= w <= 256 and 1 <= h <= 256)
            self.assertEqual(len(case['pixels']), w*h*(case['depth']//8)*4)
            depths.add(case['depth']); geometries.add((w,h)); profiles.add(case['profile'])
            padding.add(case['input_padding'])
            for p in case['parameters']:
                decl = declarations[p['slot']]
                if p['kind'] in ('p','a'):
                    values = p['value'] if isinstance(p['value'],list) else [p['value']]
                    self.assertTrue(all(-2**31 <= v*65536 < 2**31 for v in values))
                else:
                    self.assertLessEqual(decl['valid_min'],p['value'])
                    self.assertLessEqual(p['value'],decl['valid_max'])
                    if p['kind'] in ('u','i','b'):
                        self.assertIsInstance(p['value'],int)
            if case['depth'] == 16:
                self.assertTrue(all(0 <= v <= 32768 for v, in struct.iter_unpack('<H',case['pixels'])))
        self.assertEqual(depths, {8,16,32})
        self.assertEqual(profiles, {'sdr','hdr','signed','nonfinite'})
        self.assertIn((1,1),geometries)
        self.assertTrue(any(w==1 and h>1 for w,h in geometries))
        self.assertTrue(any(h==1 and w>1 for w,h in geometries))
        self.assertTrue(any(max(w,h)>200 for w,h in geometries))
        self.assertTrue(any(n%2 for n in padding))

    def test_reject_is_never_a_pixel_mismatch(self):
        adapter = Synthetic()
        case = adapter.generate(1,0)
        case['parameters'][0]['value'] = 0
        result = evaluate(adapter,case,self.directory,time.monotonic()+2)
        self.assertEqual(result['oracle']['status'],'reject')
        self.assertFalse(mismatch_routes(result))
        self.assertEqual(result['routes']['classic']['status'],'uncompared')

    def test_shrink_preserves_routes_and_replay(self):
        adapter = Synthetic()
        original = adapter.generate(1,0)
        deadline = time.monotonic()+5
        result = evaluate(adapter,original,self.directory,deadline)
        reduced, observed, reduction = shrink(adapter,original,result,self.directory,deadline,128)
        self.assertEqual(mismatch_routes(observed),['classic','smart'])
        self.assertLess(len(reduced['pixels']),len(original['pixels']))
        self.assertLess(reduced['parameters'][0]['value'],8)
        self.assertEqual(set(reduced['pixels']),{0})
        self.assertEqual(observed['first_mismatching_stage'],'synthetic-stage')
        path = self.directory/'case.json'
        save_corpus(path,adapter,original,reduced,observed,reduction,{})
        loaded, saved = load_corpus(path,adapter)
        self.assertEqual(loaded,reduced)
        self.assertEqual(evaluate(adapter,loaded,self.directory,deadline),observed)
        saved.pop('pixels_zlib_base64')
        path.write_text(json.dumps(saved))
        procedural, _ = load_corpus(path,adapter)
        self.assertEqual(procedural,reduced)

    def test_resize_and_pixel_simplification(self):
        adapter = make_adapter()
        case = dict(adapter.generate(1,0), geometry=[4,4], depth=32,
                    pixels=struct.pack('<I',0x7fc12345)*64, parameters=adapter.defaults(4,4))
        reduced = apply_operation(adapter,case,{'kind':'crop','geometry':[2,2]})
        center = next(p['value'] for p in reduced['parameters'] if p['slot']==2)
        self.assertEqual(center,[1,1])
        self.assertEqual(adapter.simple_pixels(reduced),bytes(64))

    @unittest.skipUnless(os.environ.get('OLM_FUZZ_INTEGRATION'), 'set OLM_FUZZ_INTEGRATION=1 for real public-path replay')
    def test_real_repeated_replay_and_shrink(self):
        from run import default_worker, main_checkout
        adapter = Adapter(argparse.Namespace(max_size=256,case_timeout=5,
                          main=main_checkout(),worker=default_worker()))
        adapter.prepare(self.directory,time.monotonic()+60)
        case = adapter.generate(1,91)
        directory = self.directory/'repeated'
        directory.mkdir()
        first = evaluate(adapter,case,directory,time.monotonic()+15)
        second = evaluate(adapter,case,directory,time.monotonic()+15)
        self.assertEqual(first,second)
        self.assertEqual(first['oracle']['status'], 'ok')
        if mismatch_routes(first):
            reduced,result,reduction = shrink(adapter,case,first,directory,time.monotonic()+20,32)
            self.assertTrue(reduction['accepted'])
            self.assertTrue(mismatch_routes(result))
        # A future production fix may make this witness exact; that is success.

    def test_deadline_kills_subprocess(self):
        start = time.monotonic()
        result, _, _ = command([sys.executable,'-c','import time; time.sleep(30)'],
                               timeout=.05,deadline=start+1)
        self.assertEqual(result['status'],'budget')
        self.assertLess(time.monotonic()-start,1)
        result, _, _ = command(['executable-must-not-launch'],timeout=1,deadline=start-1)
        self.assertEqual(result['status'],'budget')


if __name__ == '__main__':
    unittest.main()
