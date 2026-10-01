"""Prove the generic Rotation restoration without promoting finite coverage."""
import importlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_rotation_restoration_20261001')
public = probe.public
current = importlib.import_module('radialblur_current_public_20261001')


class RotationRestorationTests(unittest.TestCase):
    def test_original_vector_leaf_and_production_gaussian_weights(self):
        fields = probe.inverse.fields
        native, _ = fields.leaf_probe()
        xs, *_ = fields.exponents()
        expected = [f'{word:08x}' for word in struct.unpack('<30000I', native)]
        payload = ''.join(f'E {fields.bits(x):08x}\n' for x in xs)
        lengths = [1, 2, 3, 4, 7, 9, 16, 31, 32, 63, 100, 251, 1000, 2999, 3000]
        for length in lengths:
            payload += f'W {length:x}\n'
            expected.append(''.join(expected[i*(30000//length)] for i in range(length)))
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        old_harness = public.initial.HARNESS
        try:
            public.initial.HARNESS = ROOT/'tools/emulation/radialblur_rotation_gaussian_sdk_harness_20261001.cpp'
            with tempfile.TemporaryDirectory(prefix='radial_rotation_gaussian_sdk_') as directory:
                for sanitize in [False, True]:
                    binary = public.build(Path(directory)/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                    run = subprocess.run([str(binary)], input=payload, capture_output=True, text=True,
                                         check=True, env=env)
                    self.assertEqual(run.stderr, '')
                    self.assertEqual(run.stdout.splitlines(), expected)
        finally:
            public.initial.HARNESS = old_harness
        print('ROTATION_GAUSSIAN_NATIVE_ARGS', 30000, 'SDK_EXPS', 60000, 'WEIGHT_LENGTHS', 2*len(lengths), flush=True)

    def test_full_matrix_production_and_frozen_original_reference(self):
        saved = current.capture(); old = json.loads(probe.BEFORE.read_text())
        self.assertEqual(public.SOURCE.read_text(), probe.restored_source())
        self.assertEqual(saved['counterfactual_source_sha256'], public.sha(probe.inverse.candidate_inverse_source(probe.before_source()).encode()))
        self.assertEqual(saved['summary'], probe.writer.summarize(saved['rows']))
        self.assertEqual(saved['summary'], {'case_count': 694, 'both_commands_exact': 505, 'different': 105,
                                            'mac_rejected': 84, 'became_exact': 197, 'lost_exact': 0, 'raw_changed': 237})
        for path, expected in saved['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        worker = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), saved['controlled_worker_sha256'])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        native_count = live_count = 0
        with tempfile.TemporaryDirectory(prefix='radial_rotation_production_matrix_') as directory:
            temp = Path(directory)
            for case, before in zip(saved['rows'], old['rows']):
                for key in ['parameters', 'group', 'matrix', 'row_index', 'family', 'depth', 'geometry',
                            'pattern', 'state', 'input_sha256', 'reference_raw_sha256']:
                    self.assertEqual(case[key], before[key])
                self.assertEqual(public.sha(public.fixture(case)), case['input_sha256'])
                if not before['results']['classic']['raw_exact'] and case['results']['classic']['raw_exact']:
                    raw, frame, _, close, _ = public.native_render(worker, temp, case)
                    self.assertEqual(public.sha(raw), case['reference_raw_sha256'])
                    self.assertEqual(frame['render_error'], 0); self.assertTrue(frame['output']['guards_intact'])
                    self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls'])
                    native_count += 1
            for sanitize in [False, True]:
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for case in saved['rows']:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, command, env)
                        expected = case['results'][command]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata'])
                        self.assertEqual(not error and public.sha(raw) == case['reference_raw_sha256'], expected['raw_exact'])
                        live_count += 1
                print('ROTATION_PRODUCTION_PUBLIC', live_count, flush=True)
        self.assertEqual(native_count, 197)
        self.assertEqual(live_count, 2776)
        print('ROTATION_NEW_EXACT_NATIVE_REACQUIRED', native_count, flush=True)
        for family in [1, 2]:
            for depth in [8, 16, 32]:
                rows = [r for r in saved['rows'] if r['group'] == 'independent' and r['family'] == family and r['depth'] == depth]
                self.assertEqual(len(rows), 64)
                self.assertTrue(all(r['results']['classic']['raw_exact'] and r['results']['smart']['raw_exact'] for r in rows))


if __name__ == '__main__':
    unittest.main()
