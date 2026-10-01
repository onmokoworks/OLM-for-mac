"""Finite tiny alpha must retain RGB in the real two-stage Rotation sampler."""
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
probe = importlib.import_module('probe_radialblur_rotation_alpha_20261001')
public = probe.public
current = importlib.import_module('radialblur_current_public_20261001')


class NeutralAlphaTests(unittest.TestCase):
    def test_sampler_original_leaf_and_real_sdk_boundaries(self):
        from aex_loader import AexLoader
        bits = {0, 0x80000000, 0x3f800000, 0xbf800000, 0x00800000, 0x80800000}
        for value in [1e-8, 1e-12, 1e-20, 2**-24, 2**-46]:
            b = struct.unpack('<I', struct.pack('<f', value))[0]
            for n in [b-1, b, b+1]: bits.update([n, n | 0x80000000])
        values = sorted(bits); expected = []
        loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
        source = loader.bump_alloc(64); output = loader.bump_alloc(32)
        for b in values:
            pixel = struct.pack('<3fI', .25, .5, .75, b)
            loader.write_bytes(source, pixel*4); loader.write_bytes(output, bytes([0xa5])*32)
            loader.call_function(loader.image_base+0x1000,
                                 int_args=[source, output, 2, 8, 0x3e800000, 0x3f000000], max_instructions=500)
            self.assertFalse(loader.import_log)
            self.assertEqual(loader.read_bytes(output+16, 16), bytes([0xa5])*16)
            expected.append(''.join(f'{n:08x}' for n in struct.unpack('<4I', loader.read_bytes(output, 16))))
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        harness = public.initial.HARNESS
        try:
            public.initial.HARNESS = ROOT/'tools/emulation/radialblur_rotation_alpha_sdk_harness_20261001.cpp'
            with tempfile.TemporaryDirectory(prefix='radial_sampler_alpha_sdk_') as directory:
                for sanitize in [False, True]:
                    binary = public.build(Path(directory)/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                    run = subprocess.run([str(binary)], input=''.join(f'{b:08x}\n' for b in values), capture_output=True,
                                         text=True, check=True, env=env)
                    self.assertEqual(run.stderr, '')
                    self.assertEqual(run.stdout.splitlines(), expected)
        finally:
            public.initial.HARNESS = harness
        print('NATIVE_SAMPLER_ALPHA_BOUNDARIES', len(values), 'SDK_REPLAYS', 2*len(values), flush=True)

    def test_live_matrix_and_natural_planes(self):
        saved = json.loads((ROOT/'reports/radialblur_rotation_neutral_alpha_public_20261001.json').read_text())
        live = current.capture(); before = json.loads(probe.neutral.BEFORE.read_text())
        self.assertEqual(public.sha(probe.candidate_source(probe.neutral.before_source()).encode()), saved['source_sha256'])
        self.assertEqual(saved['summary'], {'case_count': 694, 'both_commands_exact': 559, 'different': 51,
                                            'mac_rejected': 84, 'became_exact': 54, 'lost_exact': 0, 'raw_changed': 54})
        for path, expected in saved['dependencies_sha256'].items():
            self.assertEqual(current.historical_dependency_sha256(path), expected)
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER']); parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), saved['window_worker_sha256'])
        self.assertEqual(public.sha(parent.read_bytes()), saved['controlled_worker_sha256'])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        with tempfile.TemporaryDirectory(prefix='radial_neutral_alpha_production_') as directory:
            temp = Path(directory); native_count = live_count = 0
            for row, old in zip(saved['rows'], before['rows']):
                self.assertEqual(row['parameters'], old['parameters']); self.assertEqual(row['input_sha256'], public.sha(public.fixture(row)))
                if row['results']['classic']['raw_exact'] and not old['results']['classic']['raw_exact']:
                    raw, frame, _, close, _ = public.native_render(parent, temp, row)
                    self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                    self.assertEqual(frame['render_error'], 0); self.assertTrue(frame['output']['guards_intact'])
                    self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls']); native_count += 1
            for sanitize in [False, True]:
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for case in live['rows']:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, command, env)
                        expected = case['results'][command]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata']); live_count += 1
                print('NEUTRAL_ALPHA_PRODUCTION_PUBLIC', live_count, flush=True)
            self.assertEqual(native_count, 54); self.assertEqual(live_count, 2776)
            natural = probe.neutral.natural(worker, temp, before, probe.neutral.before_source(), public.SOURCE.read_text())
            for observed, retained in zip(natural, saved['natural_witnesses']):
                for key in ['mac_dimensions', 'field_comparisons', 'mac_raw_sha256', 'candidate_raw_exact']:
                    self.assertEqual(observed[key], retained[key])
                self.assertTrue(observed['candidate_raw_exact'])
                self.assertTrue(all(p['different_words'] == 0 for p in observed['field_comparisons']['candidate'].values()))
        print('NEUTRAL_ALPHA_NEW_EXACT_NATIVE', native_count, flush=True)


if __name__ == '__main__':
    unittest.main()
