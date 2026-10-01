"""Calibrated reference evidence must preserve production and unknown boundaries."""
import importlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_doublecast_reference_20261001')
axis = importlib.import_module('probe_radialblur_axis_reference_20261001')
public = probe.public
latest = importlib.import_module('radialblur_current_public_20261001')


def load(name):
    return json.loads((ROOT/'reports'/name).read_text())


class DoublecastReferenceTests(unittest.TestCase):
    def test_native_scalar_reexecution_and_dependencies(self):
        with tempfile.TemporaryDirectory(prefix='radial_doublecast_scalar_') as directory:
            observed = axis.scalar_probe(Path(directory))
        self.assertEqual(observed, load('radialblur_atan2_axis_scalar_20261001.json'))
        self.assertEqual(observed['summary']['double_cast_exact'], 576)
        build = load('radialblur_doublecast_reference_build_20261001.json')
        self.assertTrue(build['parent_source_and_worker_unchanged'])
        self.assertEqual(build['trace_witness_limit'], 1024)
        for key, name in [('patch_sha256', 'tools/emulation/aexcompat_radial_doublecast_reference_20261001.patch'),
                          ('builder_sha256', 'tools/emulation/build_radialblur_doublecast_reference_20261001.py'),
                          ('parent_build_sha256', 'reports/radialblur_axis_reference_build_20261001.json')]:
            self.assertEqual(build[key], public.sha((ROOT/name).read_bytes()))
        for name in ['radialblur_doublecast_reference_public_20261001.json',
                     'radialblur_doublecast_sampler_native_coverage_20261001.json']:
            report = load(name)
            self.assertEqual(report['worker_sha256'], build['worker_sha256'])
            self.assertEqual(report['parent_worker_sha256'], build['parent_worker_sha256'])
            for path, expected in report['dependencies_sha256'].items():
                if path == 'mac/OLMRadialBlur/OLMRadialBlur.cpp':
                    self.assertEqual(expected, json.loads((ROOT/'reports/radialblur_pf8_writer_public_20261001.json').read_text())['source_before_sha256'])
                else:
                    self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        self.assertEqual(load('radialblur_doublecast_reference_public_20261001.json')['build_sha256'],
                         public.sha((ROOT/'reports/radialblur_doublecast_reference_build_20261001.json').read_bytes()))

    def test_reclassification_preserves_all_mac_and_parent_results(self):
        report = load('radialblur_doublecast_reference_public_20261001.json')
        before = load('radialblur_noise_offset_counterfactual_20261001.json')
        self.assertFalse(report['production_source_changed'])
        self.assertEqual(len(report['rows']), len(before['rows']))
        self.assertEqual(report['summary'], probe.summarize(report['rows']))
        self.assertEqual(report['summary'], {
            'case_count': 694, 'parent_reacquired_hash_exact': 694, 'reference_raw_changed': 69,
            'parent_both_commands_exact': 228, 'both_commands_exact': 263, 'different': 347,
            'mac_rejected': 84, 'became_exact': 35, 'lost_exact': 0})
        self.assertEqual(report['public_replay_count'], 2776)
        self.assertEqual(report['controlled_reacquisition_count'], 1388)
        for row, old in zip(report['rows'], before['rows']):
            for key in ['family', 'geometry', 'depth', 'pattern', 'state', 'parameters',
                        'group', 'matrix', 'row_index', 'input_sha256']:
                self.assertEqual(row[key], old[key])
            self.assertEqual(row['input_sha256'], public.sha(public.fixture(row)))
            self.assertEqual(row['parent_raw_sha256'], old['native_raw_sha256'])
            self.assertTrue(row['parent_reacquired_hash_exact'])
            self.assertTrue(row['session_clean'])
            self.assertFalse(row['unsupported_suite_calls'])
            for frame in [row['parent_frame_done'], row['frame_done']]:
                self.assertEqual(frame['render_error'], 0)
                self.assertTrue(frame['output']['guards_intact'])
            for command in ['classic', 'smart']:
                result = row['results'][command]
                previous = old['results']['getter_and_profiles'][command]
                for key in ['raw_sha256', 'error', 'metadata']:
                    self.assertEqual(result[key], previous[key])
                self.assertEqual(result['parent_raw_exact'], previous['raw_exact'])
                self.assertEqual(result['raw_exact'], not result['error'] and
                                 result['raw_sha256'] == row['reference_raw_sha256'])
        for matrix, summary in report['matrix_summaries'].items():
            self.assertEqual(summary, probe.summarize([r for r in report['rows'] if r['matrix'] == matrix]))
        for family, depth, exact in [(1, 8, 33), (1, 16, 64), (1, 32, 64), (2, 8, 0), (2, 16, 0), (2, 32, 0)]:
            rows = [r for r in report['rows'] if r['group'] == 'independent'
                    and r['family'] == family and r['depth'] == depth]
            self.assertEqual(len(rows), 64)
            self.assertEqual(probe.summarize(rows)['both_commands_exact'], exact)

    def test_covered_angles_and_uncovered_row_are_separate(self):
        report = load('radialblur_doublecast_sampler_native_coverage_20261001.json')
        native = json.loads(axis.NATIVE.read_text())['native_rows']
        lookup = {(r['left_bits'], r['right_bits']): r['native_ucrt_result_bits']
                  for r in native if r['function'] == 'atan2f'}
        self.assertEqual(report['native_rows_sha256'], axis.NATIVE_ROWS_SHA)
        self.assertEqual(report['summary'], {'angle_count': 888, 'native_scalar_covered': 857,
                                            'native_scalar_uncovered': 31, 'corrected_reference_mac_raw_exact': 2})
        tau = struct.unpack('<d', bytes.fromhex(report['native_angle_wrap_f64_le_hex']))[0]
        self.assertEqual(tau, 6.2831853)
        for row in report['rows']:
            width, height = row['geometry']
            self.assertEqual(row['center'], [width//2, height//2])
            expected, unknown = bytearray(), []
            for y in range(height):
                for x in range(width):
                    key = tuple('0x'+struct.pack('>f', value).hex()
                                for value in [y-height//2, x-width//2])
                    if key not in lookup:
                        unknown.append([x, y]); continue
                    angle = struct.unpack('>f', bytes.fromhex(lookup[key][2:]))[0]
                    expected.extend(struct.pack('<f', angle+tau if angle < 0 else angle))
            self.assertEqual(row['angle_count'], width*height)
            self.assertEqual(row['native_scalar_covered'], len(expected)//4)
            self.assertEqual(row['uncovered_coordinates'], unknown)
            self.assertEqual(unknown, [] if width == 23 else [[x, 18] for x in range(31)])
            self.assertEqual(row['native_covered_observed_angle_sha256'], public.sha(expected))
            self.assertEqual(row['native_covered_expected_angle_sha256'], public.sha(expected))
            self.assertEqual(row['corrected_raw_sha256'], row['mac_raw_sha256'])
            self.assertTrue(row['corrected_trace_resident_exact'])
            self.assertEqual(row['parent_different_bytes'], 0 if width == 23 else 5)
            for point in row['selected_points']:
                key = tuple(point['native_scalar_argument_bits_yx'])
                self.assertEqual(point['native_scalar_result_bits'], lookup[key])
                self.assertEqual(point['corrected_angle_f32_le_hex'], bytes.fromhex(lookup[key][2:])[::-1].hex())
                self.assertNotEqual(point['parent_angle_f32_le_hex'], point['corrected_angle_f32_le_hex'])
                self.assertEqual(point['corrected_sample_rgba_f32_le_hex'], point['mac_sample_rgba_f32_le_hex'])

    def test_changed_and_residual_public_cases_with_strict_sanitizers(self):
        rows = load('radialblur_doublecast_reference_public_20261001.json')['rows']
        selected = [r for r in rows if not r['results']['classic']['parent_raw_exact']
                    and r['results']['classic']['raw_exact']]
        for family in [1, 2]:
            for depth in [8, 16, 32]:
                for geometry in [[23, 13], [31, 19]]:
                    row = next(r for r in rows if r['group'] == 'independent' and r['family'] == family
                               and r['depth'] == depth and r['geometry'] == geometry)
                    if row not in selected: selected.append(row)
        selected.append(next(r for r in rows if r['results']['classic']['error']))
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        count = 0
        current = latest.keyed_rows()
        with tempfile.TemporaryDirectory(prefix='radial_doublecast_public_test_') as directory:
            temp = Path(directory)
            for sanitize in [False, True]:
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize=sanitize)
                for row in selected:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, row, command, env)
                        expected = current[(row['group'], row['matrix'], row['row_index'])]['results'][command]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata'])
                        self.assertEqual(not error and public.sha(raw) == row['reference_raw_sha256'], expected['raw_exact'])
                        count += 1
        print('DOUBLECAST_CURRENT_PUBLIC_REPLAYS', count, 'CASES', len(selected), flush=True)


if __name__ == '__main__':
    unittest.main()
