"""Natural Rotation field equality is distinct from final output completion."""
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
probe = importlib.import_module('probe_radialblur_rotation_fields_20261001')
public = probe.public


def report():
    return json.loads((ROOT/'reports/radialblur_rotation_fields_20261001.json').read_text())


class RotationFieldsTests(unittest.TestCase):
    def test_original_simd_leaf_and_generated_mantissas(self):
        model, scalar = probe.leaf_probe()
        saved = report()
        self.assertEqual(scalar, saved['scalar_leaf'])
        self.assertEqual(len(model), 30000*4)
        self.assertEqual(public.sha(model), saved['gaussian_scalar_double_exp_comparison']['native_sha256'])
        self.assertEqual(scalar['argument_count'], 30000)
        self.assertEqual(scalar['vector_calls'], 7500)
        self.assertFalse(scalar['native_windows_rcpps_verified'])

    def test_binding_and_candidate_scope(self):
        saved = report()
        self.assertEqual(public.sha(public.SOURCE.read_bytes()), saved['source_sha256'])
        self.assertFalse(saved['production_source_changed'])
        self.assertEqual(public.sha(probe.candidate_source(public.SOURCE.read_text()).encode()),
                         saved['candidate_source_sha256'])
        for path, expected in saved['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        self.assertEqual(saved['native_dimensions'], [1800, 15])
        self.assertEqual(saved['mac_dimensions'], [1800, 16])
        self.assertTrue(saved['native_owned_rows_only'])
        self.assertEqual(saved['trace']['witness_count'], saved['trace']['window_count']+1)
        self.assertTrue(saved['trace']['simd_dispatcher_observed'])
        self.assertEqual(saved['field_comparisons']['before']['accum']['different_words'], 187)
        self.assertEqual(saved['field_comparisons']['before']['normalized']['different_words'], 157)
        for field in saved['field_comparisons']['candidate'].values():
            self.assertEqual(field['different_words'], 0)
        self.assertEqual(saved['field_comparisons']['candidate_san'], saved['field_comparisons']['candidate'])
        old = json.loads(probe.CAPTURE.read_text())
        self.assertEqual(len(saved['rows']), len(old['rows']))
        self.assertEqual(saved['public_replay_count'], 2776)
        for row, before in zip(saved['rows'], old['rows']):
            for key in ['group', 'matrix', 'row_index', 'family', 'depth', 'geometry', 'pattern',
                        'state', 'parameters', 'input_sha256', 'reference_raw_sha256']:
                self.assertEqual(row[key], before[key])
            self.assertEqual(row['input_sha256'], public.sha(public.fixture(row)))
            for command, result in row['results'].items():
                self.assertEqual(result['error'], before['results'][command]['error'])
                self.assertEqual(result['before_raw_exact'], before['results'][command]['raw_exact'])
                self.assertEqual(result['raw_exact'], not result['error'] and
                                 result['raw_sha256'] == row['reference_raw_sha256'])
        self.assertEqual(saved['candidate_summary']['lost_exact'], 0)
        # A Gaussian field reconstruction is not a closed Rotation renderer.
        self.assertNotEqual(saved['natural_results']['candidate']['raw_sha256'],
                            saved['natural_case']['reference_raw_sha256'])


    def test_inverse_coordinates_and_sampler_reexecution(self):
        inverse = importlib.import_module('probe_radialblur_rotation_inverse_20261001')
        saved = json.loads((ROOT/'reports/radialblur_rotation_inverse_20261001.json').read_text())
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER'])
        with tempfile.TemporaryDirectory(prefix='radial_inverse_test_') as directory:
            observed = inverse.run(worker, Path(directory))
        for key in ['comparisons', 'selected_points', 'native_angle_scale_f32_le_hex',
                    'native_step_degree_f32_le_hex', 'native_step_radian_f32_le_hex',
                    'witness_count', 'native_raw_sha256', 'source_sha256', 'candidate_inverse_source_sha256',
                    'field_report_sha256', 'mac_raw_sha256', 'inverse_candidate_natural_raw_exact']:
            self.assertEqual(observed[key], saved[key], key)
        self.assertEqual(saved['witness_count'], 898)
        self.assertEqual(saved['comparisons']['before']['coordinates']['different_words'], 183)
        self.assertEqual(saved['comparisons']['before']['sample_rgba']['different_words'], 573)
        for path, expected in saved['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()), expected)


    def test_natural_sdk_planes_and_readonly_reference_replay(self):
        saved = report(); case = saved['natural_case']
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER'])
        parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), saved['worker_sha256'])
        self.assertEqual(public.sha(parent.read_bytes()), saved['parent_worker_sha256'])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        old_harness = public.initial.HARNESS
        with tempfile.TemporaryDirectory(prefix='radial_rotation_fields_test_') as directory:
            temp = Path(directory); hp = temp/'planes.cpp'; hp.write_text(probe.plane_harness())
            try:
                public.initial.HARNESS = hp
                for name, source, sanitize in [('before', public.SOURCE.read_text(), False),
                        ('candidate', probe.candidate_source(public.SOURCE.read_text()), False),
                        ('candidate_san', probe.candidate_source(public.SOURCE.read_text()), True)]:
                    binary = public.build(temp/name, source, sanitize=sanitize)
                    planes = temp/f'{name}_planes'; planes.mkdir()
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, command,
                                            dict(env, ROTATION_PLANES_DIRECTORY=str(planes)))
                        self.assertEqual(error, 0)
                        self.assertEqual(public.sha(raw), saved['natural_results'][name]['raw_sha256'])
                        self.assertEqual(metadata, case['results'][command]['metadata'])
                        self.assertEqual(list(struct.unpack('<2i', (planes/'dimensions.i32').read_bytes())), [1800, 16])
                        for nm, _, _, _, size in probe.PLANES:
                            if nm == 'gaussian': continue
                            data = (planes/f'{nm}.f32').read_bytes()[:size]
                            self.assertEqual(public.sha(data), saved['field_comparisons'][name][nm]['mac_sha256'])
            finally:
                public.initial.HARNESS = old_harness
            native, trace = probe.trace_planes(worker, temp, case)
            self.assertEqual(trace['window_count'], saved['trace']['window_count'])
            for name, data in native.items():
                expected = saved['scalar_leaf']['model_sha256'] if name == 'gaussian' else saved['field_comparisons']['before'][name]['native_sha256']
                self.assertEqual(public.sha(data), expected)
            assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind'] == 'a' else '')+'='+
                           (','.join(map(str, q['value'])) if isinstance(q['value'], list) else str(q['value']))
                           for q in public.native_case(case)['parameters']]
            observed = []
            specs = [(parent, 'function=0xb680,arg=rcx,size=32,occurrence=1'),
                     (worker, 'function=0xb680,arg=rcx,size=32,occurrence=1,offset=0'),
                     (worker, 'function=0xb680,arg=rcx,size=16,occurrence=1,offset=16')]
            for reference, spec in specs:
                cmd = [str(reference), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
                       str(temp/'zero.png'), '--pixel-format', 'argb32f', '--watch', spec, *assignments]
                output = json.loads(subprocess.run(cmd, check=True, capture_output=True).stdout)
                self.assertEqual(output['raw_pixel_sha256'], case['reference_raw_sha256'])
                smart = next(t for t in output['execution_traces'] if t['selector'] == 'SMART_RENDER')
                self.assertFalse(smart['truncated'])
                self.assertFalse(smart['dropped_memory_witnesses'])
                witness = smart['memory_witnesses'][0]
                observed.append(bytes.fromhex(witness['after']['hex']))
            self.assertEqual(observed[0], observed[1])
            self.assertEqual(observed[0][16:32], observed[2])
            for invalid in ['offset=0,offset=1', 'offset=16777217', 'deref=16777217', 'size=4097']:
                spec = 'function=0xb680,arg=rcx,occurrence=1,'+invalid
                if not invalid.startswith('size='): spec += ',size=4'
                cmd = [str(worker), 'render-trace-png', str(public.initial.AEX), str(temp/'input.png'),
                       str(temp/'invalid.png'), '--pixel-format', 'argb32f', '--watch', spec, *assignments]
                rejected = subprocess.run(cmd, capture_output=True)
                self.assertNotEqual(rejected.returncode, 0)
            count = 0
            for family in [1, 2]:
                for depth in [8, 16, 32]:
                    for geometry in [[23, 13], [31, 19]]:
                        row = next(r for r in saved['rows'] if r['group'] == 'independent' and
                                   r['family'] == family and r['depth'] == depth and r['geometry'] == geometry)
                        outputs = []
                        for reference in [parent, worker]:
                            raw, frame, _, close, _ = public.native_render(reference, temp, row)
                            self.assertEqual(frame['render_error'], 0)
                            self.assertTrue(frame['output']['guards_intact'])
                            self.assertTrue(close['session_clean'])
                            self.assertFalse(close['unsupported_suite_calls'])
                            self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                            outputs.append(raw); count += 1
                        self.assertEqual(outputs[0], outputs[1])
            print('ROTATION_REFERENCE_CALIBRATION', count, 'SDK_NATURAL_REPLAYS', 6, flush=True)


if __name__ == '__main__':
    unittest.main()
