"""Focused tests for reproducibility, bit comparison, rejection and reduction."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import struct
import subprocess
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

SCRATCH = Path(os.environ.get('OLM_FUZZ_TEST_SCRATCH', ROOT/'orchestra/state/T02-fuzz-framework-radialblur'))


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


class ReplayProvenanceTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='replay_unit_', dir=SCRATCH)
        self.directory = Path(self.temp.name).resolve()
        self.corpus = self.directory/'corpus'
        self.corpus.mkdir()
        self.worker = self.directory/'worker'
        self.worker.write_bytes(b'\x00')
        self.args = argparse.Namespace(replay=self.corpus, worker=None, case_timeout=None)

    def tearDown(self):
        self.temp.cleanup()

    def save(self, name, worker=None, **provenance):
        worker = worker or self.worker
        path = self.corpus/(name+'.json')
        path.write_text(json.dumps({'provenance':{
            'worker_path':str(worker), 'worker_sha256':sha(worker.read_bytes()), **provenance}}))
        return path

    def test_mixed_worker_and_timeout_replay(self):
        from run import replay
        prepared = []

        class WorkerSensitive(Synthetic):
            def __init__(self, args):
                self.worker, self.timeout = args.worker, args.case_timeout

            def prepare(self, scratch, deadline):
                prepared.append((self.worker, self.timeout))
                return {'worker_path':str(self.worker), 'worker_sha256':sha(self.worker.read_bytes())}

            def oracle(self, case, directory, deadline):
                return {'status':'ok'}, self.worker.read_bytes()*len(case['pixels'])

        other = self.directory/'other-worker'
        other.write_bytes(b'\x01')
        # Interleave workers, including two timeouts for the same worker.
        settings = [(self.worker, 3), (other, 7), (self.worker, 3), (self.worker, 10)]
        deadline = time.monotonic()+10
        for index, (worker, timeout) in enumerate(settings):
            adapter = WorkerSensitive(argparse.Namespace(worker=worker, case_timeout=timeout))
            case = adapter.generate(1, index)
            result = evaluate(adapter, case, self.directory, deadline)
            provenance = {'worker_path':str(worker), 'worker_sha256':sha(worker.read_bytes())}
            if index != 3:  # Old corpora retain the ten-second fallback.
                provenance['case_timeout_seconds'] = timeout
            save_corpus(self.corpus/f'{index}.json', adapter, case, case, result, {'accepted':[]}, provenance)
        report = {}
        self.assertEqual(replay(WorkerSensitive, self.args, self.directory, deadline, report), 0)
        self.assertEqual(prepared, [settings[0], settings[1], settings[3]])
        self.assertEqual(report['completed'], 4)
        self.assertTrue(report['replay_matches_saved'])
        self.assertEqual([r['group'] for r in report['replays']], [0, 1, 0, 2])
        self.assertIsNone(report['provenance'])
        self.assertIsNone(report['case_timeout_seconds'])
        self.assertEqual([g['provenance']['case_timeout_seconds'] for g in report['replay_groups']], [3, 7, 10])
        self.args.worker, self.args.case_timeout = other, 2
        report = {}
        self.assertEqual(replay(WorkerSensitive, self.args, self.directory, deadline, report), 1)
        self.assertFalse(report['replay_matches_saved'])
        self.assertEqual(report['provenance']['worker_path'], str(other))
        self.assertEqual(report['case_timeout_seconds'], 2)

    def test_invalid_binding_fails_before_adapter_setup_and_names_corpus(self):
        from run import replay
        self.save('0-valid')
        path = self.corpus/'1-invalid.json'
        valid = {'worker_path':str(self.worker), 'worker_sha256':sha(self.worker.read_bytes())}
        for provenance in ({}, None, {'worker_path':str(self.worker)},
                           {'worker_sha256':valid['worker_sha256']},
                           dict(valid, worker_path=str(self.directory/'missing-worker')),
                           dict(valid, worker_sha256='0'*64)):
            with self.subTest(provenance=provenance):
                path.write_text(json.dumps({'provenance':provenance}))
                with patch('run.prepare') as prepare:
                    with self.assertRaises(ValueError) as error:
                        replay(Synthetic, self.args, self.directory, time.monotonic()+5, {})
                    self.assertIn(str(path), str(error.exception))
                    self.assertIn('--worker', str(error.exception))
                    prepare.assert_not_called()

    def test_explicit_overrides_bypass_recorded_binding_and_timeout(self):
        from run import replay_groups
        path = self.save('case', worker_path='/missing/worker', worker_sha256='wrong',
                         case_timeout_seconds=-1)
        self.args.worker, self.args.case_timeout = self.worker, 2.5
        self.assertEqual(replay_groups(self.args), {(self.worker, 2.5):[path]})
        path.write_text(json.dumps({'provenance':None}))
        self.assertEqual(replay_groups(self.args), {(self.worker, 2.5):[path]})

    def test_timeout_validation_and_independent_override(self):
        from run import replay_groups
        for timeout in (0, -1, True, '10', None, float('inf'), float('nan')):
            with self.subTest(timeout=timeout):
                path = self.save('case', case_timeout_seconds=timeout)
                with self.assertRaises(ValueError) as error:
                    replay_groups(self.args)
                self.assertIn(str(path), str(error.exception))
                self.assertIn('--case-timeout', str(error.exception))
        self.args.case_timeout = 4
        self.assertEqual(replay_groups(self.args), {(self.worker, 4):[path]})
        self.args.case_timeout = None
        self.args.worker = self.worker
        self.save('case', case_timeout_seconds=8)
        self.assertEqual(replay_groups(self.args), {(self.worker, 8):[path]})

    def test_cli_defaults_do_not_override_corpus(self):
        from run import options
        argv = ['run.py', '--plugin', 'radialblur', '--scratch', str(self.directory)]
        with patch('run.default_worker', return_value=self.worker) as default:
            with patch.object(sys, 'argv', argv+['--replay', str(self.corpus)]):
                args = options()
            self.assertIsNone(args.worker)
            self.assertIsNone(args.case_timeout)
            default.assert_not_called()
            with patch.object(sys, 'argv', argv):
                args = options()
            self.assertEqual(args.worker, self.worker)
            self.assertEqual(args.case_timeout, 10)
            with patch.object(sys, 'argv', argv+['--replay', str(self.corpus),
                                               '--worker', str(self.worker), '--case-timeout', '6']):
                args = options()
            self.assertEqual(args.worker, self.worker)
            self.assertEqual(args.case_timeout, 6)

    def test_cli_bad_hash_exits_nonzero_with_filename(self):
        path = self.save('bad-hash', worker_sha256='0'*64)
        report = self.directory/'report.json'
        result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/fuzz/run.py'),
            '--plugin', 'radialblur', '--replay', str(path), '--jobs', '2',
            '--scratch', str(self.directory), '--report', str(report)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(str(path), result.stderr)
        self.assertIn('SHA-256 mismatch', result.stderr)
        self.assertEqual(json.loads(report.read_text())['status'], 'setup_error')


if __name__ == '__main__':
    unittest.main()
