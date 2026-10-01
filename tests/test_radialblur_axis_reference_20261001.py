"""Reference corrections must be proved independently of production output tuning."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_axis_reference_20261001')
public = probe.public


def load(name):
    return json.loads((ROOT/'reports'/name).read_text())


class AxisReferenceTests(unittest.TestCase):
    def test_current_public_pixels_with_strict_sanitizers(self):
        capture = load('radialblur_axis_reference_public_20261001.json')
        offset = load('radialblur_noise_offset_counterfactual_20261001.json')
        current = {(r['matrix'], r['row_index']): r for r in offset['rows'] if r['group'] == 'retained'}
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        count = 0
        with tempfile.TemporaryDirectory(prefix='radial_axis_strict_san_') as directory:
            temp = Path(directory)
            binary = public.build(temp/'san', public.SOURCE.read_text(), sanitize=True)
            for row in capture['rows']:
                for command in ('classic', 'smart'):
                    error, raw, metadata = public.mac_render(binary, temp, row, command, env)
                    result = current[(row['matrix'], row['row_index'])]['results']['getter_and_profiles'][command]
                    self.assertEqual(error, result['error'])
                    self.assertEqual(public.sha(raw) if not error else None, result['raw_sha256'])
                    self.assertEqual(metadata, result['metadata'])
                    self.assertEqual(not error and public.sha(raw) == row['corrected_raw_sha256'],
                                     result['raw_exact'])
                    count += 1
        self.assertEqual(count, 620)
        print('AXIS_STRICT_SANITIZER_PUBLIC', count, flush=True)

    def test_retained_windows_scalar_and_host_reexecution(self):
        capture = load('radialblur_atan2_axis_scalar_20261001.json')
        with tempfile.TemporaryDirectory(prefix='radial_axis_scalar_test_') as directory:
            observed = probe.scalar_probe(Path(directory))
        self.assertEqual(observed, capture)
        self.assertEqual(capture['summary'], {
            'vector_count': 576, 'host_f32_exact': 556, 'corrected_reference_exact': 572,
            'double_cast_exact': 576, 'corrected_axis_count': 16,
            'corrected_axis_native_exact': 16, 'nonaxis_unchanged': 560})
        axes = [r for r in capture['rows'] if r['corrected_axis']]
        self.assertEqual(len(axes), 16)
        for row in axes:
            self.assertEqual(row['left_bits'], '0x00000000')
            self.assertEqual(row['host_f32_bits'], '0x40490fda')
            self.assertEqual(row['corrected_reference_bits'], row['native_ucrt_result_bits'])
        self.assertEqual(capture['native_ucrt_identity']['product_version'], '10.0.26100.8875')

    def test_public_reclassification_preserves_mac_and_parent_capture(self):
        capture = load('radialblur_axis_reference_public_20261001.json')
        typed_mac = load('radialblur_typed_angle_mac_baseline_20261001.json')
        self.assertEqual(capture['summary'], probe.summarize(capture['rows']))
        self.assertEqual(capture['summary'], {
            'case_count': 310, 'parent_reacquired_hash_exact': 310,
            'reference_raw_changed': 97, 'both_commands_exact': 94,
            'parent_both_commands_exact': 68, 'mac_rejected': 94,
            'different': 122, 'became_exact': 26, 'lost_exact': 0})
        self.assertEqual(capture['public_replay_count'], 1240)
        self.assertEqual(capture['native_reacquisition_count'], 620)
        self.assertFalse(capture['production_source_changed'])
        for matrix, path in probe.CAPTURES.items():
            previous = json.loads(path.read_text())
            retained = previous['rows'] if matrix == 'typed' else previous['cases']
            rows = [r for r in capture['rows'] if r['matrix'] == matrix]
            self.assertEqual(len(rows), len(retained))
            self.assertEqual(capture['matrix_summaries'][matrix], probe.summarize(rows))
            for index, (row, old) in enumerate(zip(rows, retained)):
                self.assertEqual(row['row_index'], index)
                self.assertEqual(row['input_sha256'], public.sha(public.fixture(row)))
                self.assertEqual(row['parent_raw_sha256'], old['native_raw_sha256'])
                self.assertEqual(row['native_api_parameters'], public.native_case(row)['parameters'])
                baseline = typed_mac['rows'][index] if matrix == 'typed' else old
                for command in ('classic', 'smart'):
                    result, before = row['results'][command], baseline['results'][command]
                    self.assertEqual(result['raw_sha256'], before['raw_sha256'])
                    self.assertEqual(result['error'], before['error'])
                    self.assertEqual(result['parent_raw_exact'], before['raw_exact'])
                    self.assertEqual(result['corrected_raw_exact'], not result['error'] and
                                     result['raw_sha256'] == row['corrected_raw_sha256'])
                self.assertTrue(row['session_clean'])
                self.assertFalse(row['unsupported_suite_calls'])
                for frame in (row['frame_done'], row['parent_frame_done']):
                    self.assertEqual(frame['render_error'], 0)
                    self.assertTrue(frame['output']['guards_intact'])
        self.assertEqual(capture['matrix_summaries']['topology']['both_commands_exact'], 76)

    def test_first_difference_and_live_source_bindings(self):
        capture = load('radialblur_axis_reference_public_20261001.json')
        sampler = load('radialblur_axis_sampler_first_difference_20261001.json')
        build = load('radialblur_axis_reference_build_20261001.json')
        parent = load('radialblur_typed_trace_reference_build_20261001.json')
        offset = load('radialblur_noise_offset_counterfactual_20261001.json')
        self.assertEqual(build['parent_worker_sha256'], parent['worker_sha256'])
        self.assertTrue(build['parent_source_and_worker_unchanged'])
        self.assertEqual(build['parent_build_sha256'], public.sha((ROOT/'reports/radialblur_typed_trace_reference_build_20261001.json').read_bytes()))
        self.assertEqual(capture['worker_sha256'], build['worker_sha256'])
        self.assertEqual(capture['axis_build_sha256'], public.sha((ROOT/'reports/radialblur_axis_reference_build_20261001.json').read_bytes()))
        self.assertEqual(build['patch_sha256'], public.sha((ROOT/'tools/emulation/aexcompat_radial_atan2_axis_20261001.patch').read_bytes()))
        self.assertEqual(build['builder_sha256'], public.sha((ROOT/'tools/emulation/build_radialblur_axis_reference_20261001.py').read_bytes()))
        for name in ('radialblur_atan2_axis_scalar_20261001.json', 'radialblur_axis_reference_public_20261001.json',
                     'radialblur_axis_sampler_first_difference_20261001.json'):
            for path, expected in load(name)['dependencies_sha256'].items():
                if path == 'mac/OLMRadialBlur/OLMRadialBlur.cpp':
                    self.assertEqual(expected, offset['source_before_sha256'])
                elif path == 'mac/OLMRadialBlur/OLMRadialBlur.h':
                    self.assertEqual(expected, offset['header_before_sha256'])
                else:
                    self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        self.assertEqual(capture['source_sha256'], offset['source_before_sha256'])
        self.assertEqual(public.sha(public.SOURCE.read_bytes()), offset['candidate_source_sha256'])
        self.assertEqual(sampler['public_coordinate'], [0, 5])
        self.assertEqual(sampler['relative_coordinate'], [-8, 0])
        self.assertEqual(sampler['traces']['parent']['angle_f32_le_hex'], 'da0f4940')
        self.assertEqual(sampler['traces']['corrected']['angle_f32_le_hex'], 'db0f4940')
        self.assertEqual(sampler['traces']['corrected']['sample_rgba_f32_le_hex'], sampler['mac_sample_rgba_f32_le_hex'])
        self.assertEqual(sampler['traces']['corrected']['raw_sha256'], sampler['mac_raw_sha256'])
        self.assertTrue(sampler['corrected_trace_matches_typed_resident'])
        self.assertTrue(sampler['corrected_trace_and_mac_full_raw_exact'])


if __name__ == '__main__':
    unittest.main()
