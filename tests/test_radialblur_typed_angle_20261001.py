"""Real typed public AEX context versus SDK reader and native transform argument."""
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
public = importlib.import_module('probe_radialblur_public_aligned_20261001')
route = importlib.import_module('probe_radialblur_typed_angle_route_20261001')
HARNESS = ROOT/'tools/emulation/radialblur_angle_sdk_harness_20261001.cpp'


def load(name):
    return json.loads((ROOT/'reports'/name).read_text())


class TypedAngleTests(unittest.TestCase):
    def test_typed_trace_and_parent_calibration_bindings(self):
        capture = load('radialblur_typed_angle_public_route_20261001.json')
        build = load('radialblur_typed_trace_reference_build_20261001.json')
        base = load('radialblur_controlled_reference_build_20261001.json')
        self.assertEqual(capture['case_count'], 28)
        self.assertEqual(len(capture['rows']), 28)
        self.assertEqual(capture['worker_sha256'], build['worker_sha256'])
        self.assertEqual(build['parent_worker_sha256'], base['controlled_worker_sha256'])
        self.assertTrue(build['parent_source_and_worker_unchanged'])
        self.assertEqual(capture['build_sha256'], public.sha((ROOT/'reports/radialblur_typed_trace_reference_build_20261001.json').read_bytes()))
        self.assertEqual(build['base_build_sha256'], public.sha((ROOT/'reports/radialblur_controlled_reference_build_20261001.json').read_bytes()))
        for name, expected in capture['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/name).read_bytes()), expected, name)
        before = load('radialblur_public_getters_edge_fixed_20261001.json')
        self.assertEqual(len(capture['calibration']), 30)
        for row, old in zip(capture['calibration'], before['cases']):
            self.assertTrue(row['parent_and_typed_worker_equal'])
            self.assertEqual(row['raw_sha256'], old['native_raw_sha256'])
        for row, spec in zip(capture['rows'], route.cases()):
            for key, value in spec.items(): self.assertEqual(row[key], value)
            self.assertEqual(row['center'], [10, 7])
            self.assertEqual(public.native_case(row)['parameters'], row['native_api_parameters'])
            self.assertEqual(public.sha(public.fixture(row)), row['input_sha256'])
            self.assertTrue(row['session_clean'])
            self.assertEqual(row['render_mode'], 'smart-cpu')
            angle = next(p['value'] for p in row['parameters'] if p['slot'] == 18)
            self.assertEqual(row['angle_raw_hex'], struct.pack('<i', round(angle*65536)).hex())
            self.assertEqual(row['noise_offset_f32_hex'], row['noise_offset_builder_f32_hex'])
        offset_one = [r for r in capture['rows'] if r['state'] == 'offset'
                      and next(p['value'] for p in r['parameters'] if p['slot'] == 28) == 1]
        self.assertTrue(offset_one)
        self.assertTrue(all(r['noise_offset_f32_hex'] == '35fa8e3c' for r in offset_one))

    def test_sdk_angle_materialization_o2_sanitizers(self):
        capture = load('radialblur_typed_angle_public_route_20261001.json')
        expected_boundary = {-20564372: -358915, -7055345: -123138,
                             14253070: 248762, 20963609: 365883}
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        original = public.initial.HARNESS
        total = 0
        try:
            public.initial.HARNESS = HARNESS
            with tempfile.TemporaryDirectory(prefix='radial_angle_sdk_') as directory:
                for sanitize in (False, True):
                    binary = public.build(Path(directory)/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                    for row in capture['rows']:
                        angle = next(p['value'] for p in row['parameters'] if p['slot'] == 18)
                        offset = next(p['value'] for p in row['parameters'] if p['slot'] == 28)
                        raw_angle, raw_offset = round(angle*65536), round(offset*65536)
                        run = subprocess.run([str(binary), str(raw_angle), str(raw_offset)],
                                             capture_output=True, text=True, check=True, env=env)
                        self.assertEqual(run.stderr, '')
                        degrees, argument, cosine, sine, observed_offset = run.stdout.split()
                        self.assertEqual(float(degrees), angle)
                        self.assertEqual(int(argument), row['angle_builder_i32'])
                        self.assertEqual(struct.pack('<I', int(cosine, 16)).hex(), row['transform_cos_f32_hex'])
                        self.assertEqual(struct.pack('<I', int(sine, 16)).hex(), row['transform_sin_f32_hex'])
                        if raw_angle in expected_boundary:
                            self.assertEqual(int(argument), expected_boundary[raw_angle])
                        # This historical SDK harness prints the integer part.
                        # Full phase bits are checked by the separate Offset test.
                        phase = struct.unpack('<f', bytes.fromhex(row['noise_offset_f32_hex']))[0]
                        self.assertEqual(int(observed_offset), int(phase))
                        total += 1
                    print('RADIAL_TYPED_SDK', 'san' if sanitize else 'o2', total, flush=True)
        finally:
            public.initial.HARNESS = original
        self.assertEqual(total, 56)

    def test_public_pixels_o2_and_sanitizers(self):
        native = load('radialblur_typed_angle_public_route_20261001.json')
        capture = load('radialblur_typed_angle_mac_baseline_20261001.json')
        self.assertEqual(capture['summary'], {'both_commands_exact': 11, 'different': 13, 'mac_rejected': 4})
        offset = load('radialblur_noise_offset_counterfactual_20261001.json')
        current_rows = [r for r in offset['rows'] if r['group'] == 'retained' and r['matrix'] == 'typed']
        self.assertEqual(len(current_rows), 28)
        for name, expected in capture['dependencies_sha256'].items():
            if name == 'mac/OLMRadialBlur/OLMRadialBlur.cpp':
                self.assertEqual(expected, offset['source_before_sha256'])
            elif name == 'mac/OLMRadialBlur/OLMRadialBlur.h':
                self.assertEqual(expected, offset['header_before_sha256'])
            else:
                self.assertEqual(public.sha((ROOT/name).read_bytes()), expected, name)
        self.assertEqual(public.sha(public.SOURCE.read_bytes()), offset['candidate_source_sha256'])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        total = 0
        with tempfile.TemporaryDirectory(prefix='radial_angle_pixels_') as directory:
            temp = Path(directory)
            for sanitize in (False, True):
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for index, (case, row) in enumerate(zip(native['rows'], current_rows)):
                    self.assertEqual(row['row_index'], index)
                    self.assertEqual(case['input_sha256'], row['input_sha256'])
                    self.assertEqual(case['native_raw_sha256'], row['native_raw_sha256'])
                    for mode in ('classic', 'smart'):
                        error, raw, metadata = public.mac_render(binary, temp, case, mode, env)
                        result = row['results']['getter_and_profiles'][mode]
                        self.assertEqual(error, result['error'])
                        self.assertEqual(public.sha(raw) if not error else None, result['raw_sha256'])
                        self.assertEqual(not error and public.sha(raw) == case['native_raw_sha256'], result['raw_exact'])
                        self.assertEqual(metadata, result['metadata'])
                        total += 1
                print('RADIAL_TYPED_PIXELS', 'san' if sanitize else 'o2', total, flush=True)
        self.assertEqual(total, 112)


if __name__ == '__main__':
    unittest.main()
