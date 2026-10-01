"""Public gamma/HDR and FLOAT32 membership counterexamples, with AEX binding."""
import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
replay = importlib.import_module('replay_olmsmoother2_gamma_composition_20261001')
probe = replay.probe
BASELINE_SOURCE = 'd44b4e653077fa79a2a717be3f9fc809f2a4d66f3431dec4dad3c4f702d64d03'


def capture(path):
    data = json.loads(path.read_text())
    assert data['aex_sha256'] == probe.base.retained.native_identity.AEX_SHA256
    assert data['frozen_worker_sha256'] == probe.base.retained.FROZEN_SHA
    for dependency, expected in data['dependencies_sha256'].items():
        assert probe.base.sha((ROOT / dependency).read_bytes()) == expected, dependency
    return data


class GammaCompositionTests(unittest.TestCase):
    def test_current_source_replay(self):
        data = replay.replay(probe.SOURCE.read_text())
        self.assertEqual(data['case_count'], 2280)
        self.assertEqual(data['render_count'], 4560)
        self.assertEqual(data['summary']['raw_exact_count'], 4560)

    def test_captures_and_route_binding(self):
        # Saved captures retain their historical source identity. The separate
        # live replay above tests future source changes against the same oracle.
        saved = json.loads((ROOT / 'reports/olmsmoother2_gamma_composition_replay_20261001.json').read_text())
        source_sha = saved['source_sha256']
        self.assertNotEqual(source_sha, BASELINE_SOURCE)
        self.assertEqual(saved['summary']['raw_exact_count'], 4560)
        for dependency, expected in saved['dependencies_sha256'].items():
            self.assertEqual(probe.base.sha((ROOT / dependency).read_bytes()), expected, dependency)
        for matrix, baseline_path in replay.CAPTURES.items():
            baseline = capture(baseline_path)
            production = capture(baseline_path.with_name(baseline_path.name.replace('baseline', 'production')))
            self.assertEqual(baseline['source_sha256'], BASELINE_SOURCE)
            self.assertEqual(production['source_sha256'], source_sha)
            expected = list(probe.specifications(matrix))
            self.assertEqual(len(expected), 840 if matrix == 'hdr' else 1440)
            self.assertEqual(baseline['case_count'], len(expected))
            self.assertEqual(production['case_count'], len(expected))
            differences = []
            for index, (spec, before, after) in enumerate(zip(expected, baseline['cases'], production['cases'])):
                for key, value in spec.items():
                    self.assertEqual(before[key], value)
                    self.assertEqual(after[key], value)
                raw, _ = probe.fixture(spec['fixture'], spec['depth'])
                for key in ('input_sha256', 'parameter_payload', 'native_raw_sha256'):
                    self.assertEqual(before[key], after[key], (matrix, index, key))
                self.assertEqual(after['input_sha256'], probe.base.sha(raw))
                self.assertTrue(after['raw_exact'])
                self.assertEqual(after['production_raw_sha256'], after['native_raw_sha256'])
                self.assertEqual(after['mac_callbacks'], [1, 1, 1, 15, 15, 1])
                for case in (before, after):
                    self.assertTrue(case['session_clean'])
                    self.assertEqual(case['unsupported_suite_calls'], [])
                    self.assertEqual(case['frame_done']['status'], 'ok')
                    self.assertTrue(case['frame_done']['output']['guards_intact'])
                if not before['raw_exact']:
                    differences.append(index)
                    self.assertEqual(before['version'], 2)
                    self.assertEqual(before['gamma_mode'], 2)
                    self.assertEqual(before['mac_error'], 0)
            self.assertEqual(len(differences), 0 if matrix == 'hdr' else 16)

        route = capture(ROOT / 'reports/olmsmoother2_gamma_membership_public_route_20261001.json')
        self.assertEqual(route['source_sha256'], BASELINE_SOURCE)
        self.assertEqual(route['case_count'], 2)
        v1, v2 = route['rows']
        self.assertEqual([v1['internal_version_flag'], v2['internal_version_flag']], [1, 0])
        self.assertEqual(v1['gamma_color_4c30_call_observations'], 0)
        self.assertEqual(v2['gamma_color_4c30_call_observations'], 12)
        self.assertEqual(v2['gamma_color_4c30_call_rvas'], ['0xaa39', '0xaa4a', '0xaa5c'])
        self.assertEqual(v2['inverse_lut_length'], 10000)
        self.assertEqual(v2['inverse_lut_prefix_bytes'], 4096)
        for row in route['rows']:
            self.assertTrue(row['guards_intact'])
            self.assertEqual(row['unsupported_suite_calls'], [])
            self.assertEqual(row['render_mode'], 'smart-cpu')


if __name__ == '__main__':
    unittest.main()
