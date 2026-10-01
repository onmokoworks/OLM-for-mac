"""SDK parameter regression and honest replay of remaining RadialBlur differences."""
import collections
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
public = importlib.import_module('probe_radialblur_public_aligned_20261001')
latest = importlib.import_module('radialblur_current_public_20261001')
units = importlib.import_module('probe_radialblur_parameter_units_20261001')


def report(name):
    return json.loads((ROOT/'reports'/name).read_text())


class PublicParameterTests(unittest.TestCase):
    def test_actual_import_free_leaves_and_angle_fragment(self):
        capture = report('radialblur_parameter_units_20261001.json')
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), capture['aex_sha256'])
        for name, expected in capture['dependencies_sha256'].items():
            self.assertEqual(latest.historical_dependency_sha256(name), expected, name)
        constants, rows = units.leaf_observations()
        self.assertEqual(constants, capture['constants'])
        self.assertEqual(rows, capture['leaf_rows'])
        self.assertEqual(constants['0x1800212d8']['hex'], '12e7faa146df913f')
        self.assertEqual(constants['0x180025550']['hex'], '399d52a246df913e')
        for row in rows:
            self.assertEqual(row['leaves']['slider']['i32'], row['raw_fixed'])
            self.assertEqual(row['leaves']['angle']['i32'], row['raw_fixed'])
        forty_five = next(r for r in rows if r['degrees_if_sdk_angle'] == 45)
        self.assertEqual(forty_five['angle_instruction_fragment_i32'], 51471)
        # This prevents silently substituting ordinary degree-to-radian math.
        self.assertEqual(next(r for r in rows if r['raw_fixed'] == 65536)
                         ['leaves']['noise_offset']['hex'], '35fa8e3c')

    def test_capture_settings_are_aligned_and_residuals_remain(self):
        before = report('radialblur_public_getters_aligned_20261001.json')
        after = report('radialblur_public_getters_edge_fixed_20261001.json')
        topology = report('radialblur_public_topology_aligned_20261001.json')
        build = report('radialblur_controlled_reference_build_20261001.json')
        self.assertEqual(before['summary']['both_cmd_exact_count'], 2)
        self.assertEqual(after['summary']['both_cmd_exact_count'], 4)
        self.assertEqual(topology['summary']['both_cmd_exact_count'], 52)
        self.assertEqual(before['source_sha256'], topology['source_sha256'])
        self.assertNotEqual(before['source_sha256'], after['source_sha256'])
        current = report('radialblur_public_getters_angle_fixed_20261001.json')
        offset = report('radialblur_noise_offset_counterfactual_20261001.json')
        self.assertEqual(offset['source_before_sha256'], current['source_sha256'])
        self.assertEqual(json.loads((ROOT/'reports/radialblur_pf8_writer_public_20261001.json').read_text())['source_before_sha256'], offset['candidate_source_sha256'])
        self.assertEqual(current['summary']['both_cmd_exact_count'], 5)
        self.assertTrue(build['frozen_source_and_worker_unchanged'])
        for before_case, after_case in zip(before['cases'], after['cases']):
            for key in ('input_sha256', 'parameters', 'parameter_payload', 'native_api_parameters', 'native_raw_sha256'):
                self.assertEqual(before_case[key], after_case[key], key)
        for capture in (before, after, topology):
            self.assertEqual(capture['worker_sha256'], build['controlled_worker_sha256'])
            self.assertEqual(capture['controlled_build_sha256'],
                             public.sha((ROOT/'reports/radialblur_controlled_reference_build_20261001.json').read_bytes()))
            for name, expected in capture['dependencies_sha256'].items():
                if name == str(public.SOURCE.relative_to(ROOT)):
                    self.assertEqual(expected, capture['source_sha256'])
                elif name == 'mac/OLMRadialBlur/OLMRadialBlur.h':
                    self.assertEqual(expected, offset['header_before_sha256'])
                else:
                    self.assertEqual(latest.historical_dependency_sha256(name), expected, name)
            self.assertEqual(len(capture['cases']), capture['case_count'])
            for case in capture['cases']:
                self.assertEqual(public.sha(public.fixture(case)), case['input_sha256'])
                self.assertEqual(public.native_case(case)['parameters'], case['native_api_parameters'])
                self.assertTrue(case['session_clean'])
                self.assertEqual(case['unsupported_suite_calls'], [])
                self.assertTrue(case['frame_done']['output']['guards_intact'])
                self.assertEqual(case['frame_done']['output']['checksum'], case['native_raw_sha256'])
        self.assertEqual(sum(c['results']['classic']['error'] != 0 for c in topology['cases']), 84)

    def test_live_public_replay_o2_and_sanitizers(self):
        offset = latest.capture()
        cases = [r for r in offset['rows'] if r['group'] == 'retained' and r['matrix'] in ('getters', 'topology')]
        self.assertEqual(len(cases), 282)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        total = 0
        with tempfile.TemporaryDirectory(prefix='radial_public_parameters_') as directory:
            temp = Path(directory)
            for sanitize in (False, True):
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                outcomes = collections.Counter()
                for case in cases:
                    for route in ('classic', 'smart'):
                        error, raw, metadata = public.mac_render(binary, temp, case, route, env)
                        expected = case['results'][route]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata'])
                        self.assertEqual(not error and public.sha(raw) == case['reference_raw_sha256'], expected['raw_exact'])
                        self.assertEqual(metadata['callbacks'], [0,0,0,0,0,1,1] if route == 'classic'
                                         else [1,32,32,1,1,1,1])
                        outcomes['error' if error else 'exact' if expected['raw_exact'] else 'different'] += 1
                        total += 1
                expected_outcomes = collections.Counter()
                for case in cases:
                    for expected in case['results'].values():
                        expected_outcomes['error' if expected['error'] else 'exact' if expected['raw_exact'] else 'different'] += 1
                self.assertEqual(outcomes, expected_outcomes)
                # Independently exercise all integer UI values, including values
                # for which the current renderer still rejects this input.
                base = next(c for c in public.specifications('getters')
                            if c['state'] == 'neutral' and c['family'] == 1 and c['depth'] == 8)
                for value in range(101):
                    case = json.loads(json.dumps(base))
                    for parameter in case['parameters']:
                        if parameter['slot'] == 7: parameter['value'] = value
                        if parameter['slot'] == 13: parameter['value'] = 100-value
                        if parameter['slot'] == 10: parameter['value'] = 2
                    for route in ('classic', 'smart'):
                        error, raw, metadata = public.mac_render(binary, temp, case, route, env)
                        self.assertEqual(metadata['outer_edge'], value)
                        self.assertEqual(metadata['inner_edge'], 100-value)
                        self.assertIn(error, (0, 516))
                        if error: self.assertEqual(raw, b'')
                        total += 1
                print('RADIAL_PUBLIC_REPLAY', 'san' if sanitize else 'o2', dict(outcomes), total, flush=True)
        self.assertEqual(total, 1532)


if __name__ == '__main__':
    unittest.main()
