"""Prove the PF8 writer against native leaf bits and natural public samples."""
import importlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
public = importlib.import_module('probe_radialblur_public_aligned_20261001')
probe = importlib.import_module('probe_radialblur_pf8_writer_20261001')
current = importlib.import_module('radialblur_current_public_20261001')


class PF8WriterTests(unittest.TestCase):
    def test_native_quantizer_integer_boundaries_and_indefinite_values(self):
        from aex_loader import AexLoader
        loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
        output = loader.bump_alloc(16)
        values = {0, 0x80000000, 1, 0x80000001, 0x3f800000, 0xbf800000,
                  0x7f800000, 0xff800000, 0x7fc00000, 0xffc00000,
                  0x7f7fffff, 0xff7fffff, 0x4b008081, 0xcb008081}
        for integer in range(-32, 288):
            bits = struct.unpack('<I', struct.pack('<f', integer/255.0))[0]
            values.update([bits-1, bits, bits+1] if bits else [0, 1, 0x80000001])
        rng = random.Random(20261001)
        values.update(rng.getrandbits(32) for _ in range(128))
        ordered = sorted(values)
        vectors = [(bits, ordered[(i+113)%len(ordered)], ordered[(i+217)%len(ordered)],
                    ordered[(i+389)%len(ordered)]) for i, bits in enumerate(ordered)]
        expected = []
        for vector in vectors:
            # The actual public owner MINSS selects 1.0 on an unordered RGB.
            arguments = [struct.pack('<I', bits) for bits in vector]
            for i in range(3):
                if not struct.unpack('<f', arguments[i])[0] < 1.0:
                    arguments[i] = struct.pack('<f', 1.0)
            loader.write_bytes(output, bytes([0xa5])*16)
            loader.call_function(0x180017400, int_args=[0, 0, 0, 0, output],
                                 float_args=dict(enumerate(arguments)), max_instructions=32)
            self.assertFalse(loader.import_log)
            self.assertEqual(loader.read_bytes(output+4, 12), bytes([0xa5])*12)
            expected.append(loader.read_bytes(output, 4).hex())
        payload = ''.join(' '.join(f'{b:08x}' for b in v)+'\n' for v in vectors)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        original = public.initial.HARNESS
        try:
            public.initial.HARNESS = ROOT/'tools/emulation/radialblur_pf8_writer_sdk_harness_20261001.cpp'
            with tempfile.TemporaryDirectory(prefix='radial_pf8_quantizer_') as directory:
                for sanitize in [False, True]:
                    binary = public.build(Path(directory)/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                    run = subprocess.run([str(binary)], input=payload, capture_output=True, text=True,
                                         check=True, env=env)
                    self.assertEqual(run.stderr, '')
                    self.assertEqual(run.stdout.splitlines(), expected)
        finally:
            public.initial.HARNESS = original
        print('PF8_WRITER_NATIVE_SCALARS', len(vectors), 'SDK_REPLAYS', 2*len(vectors), flush=True)

    def test_natural_sampler_and_writer_witness_bindings(self):
        report = current.capture()
        import pefile
        pe = pefile.PE(str(public.initial.AEX))
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        self.assertEqual(public.sha(pe.get_data(0x17400, 0x39)), report['native_writer_bytes_sha256'])
        self.assertEqual(public.sha(pe.get_data(0x7bdd, 0x1e)), report['native_owner_rgb_min_bytes_sha256'])
        for path, expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        self.assertEqual(report['summary'], probe.summarize(report['rows']))
        self.assertEqual(report['summary'], {'case_count': 694, 'both_commands_exact': 308,
                                            'different': 302, 'mac_rejected': 84, 'became_exact': 45,
                                            'lost_exact': 0, 'raw_changed': 51})
        before = json.loads(probe.CAPTURE.read_text())
        self.assertEqual(report['source_before_sha256'], before['source_sha256'])
        self.assertEqual(report['reference_capture_sha256'], public.sha(probe.CAPTURE.read_bytes()))
        for row, old in zip(report['rows'], before['rows']):
            for key in ['parameters', 'family', 'geometry', 'depth', 'pattern', 'state', 'input_sha256',
                        'reference_raw_sha256', 'parent_raw_sha256', 'group', 'matrix', 'row_index']:
                self.assertEqual(row[key], old[key])
            for command in ['classic', 'smart']:
                result = row['results'][command]
                self.assertEqual(result['error'], old['results'][command]['error'])
                self.assertEqual(result['metadata'], old['results'][command]['metadata'])
                self.assertEqual(result['raw_exact'], not result['error'] and
                                 result['raw_sha256'] == row['reference_raw_sha256'])
                if row['depth'] != 8 or row['family'] != 1:
                    self.assertTrue(result['before_raw_unchanged'])
        self.assertEqual(len(report['natural_public_witnesses']), 4)
        for witness in report['natural_public_witnesses']:
            self.assertEqual(witness['native_raw_sha256'], witness['after_raw_sha256'])
            self.assertTrue(witness['trace_typed_resident_raw_exact'])
            for point in witness['selected_points']:
                self.assertEqual(point['native_sample_rgba_f32_le_hex'], point['before_mac_sample_rgba_f32_le_hex'])
                self.assertEqual(point['native_writer_argb8_hex'], point['after_argb8_hex'])
        for depth in [8, 16, 32]:
            rows = [r for r in report['rows'] if r['group'] == 'independent' and r['family'] == 1 and r['depth'] == depth]
            self.assertEqual(len(rows), 64)
            self.assertEqual(probe.summarize(rows)['both_commands_exact'], 64)

    def test_live_public_current_production(self):
        capture = current.capture()
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        count = 0
        with tempfile.TemporaryDirectory(prefix='radial_pf8_public_test_') as directory:
            temp = Path(directory)
            for sanitize in [False, True]:
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for case in capture['rows']:
                    self.assertEqual(public.sha(public.fixture(case)), case['input_sha256'])
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, command, env)
                        result = case['results'][command]
                        self.assertEqual(error, result['error'])
                        self.assertEqual(public.sha(raw) if not error else None, result['raw_sha256'])
                        self.assertEqual(metadata, result['metadata'])
                        self.assertEqual(not error and public.sha(raw) == case['reference_raw_sha256'], result['raw_exact'])
                        count += 1
                print('PF8_WRITER_CURRENT_PUBLIC', count, flush=True)
        self.assertEqual(count, 2776)


if __name__ == '__main__':
    unittest.main()
