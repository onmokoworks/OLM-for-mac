"""Live public Classic/Smart replay of independent Layer and long Dual inputs."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_directionalblur_dual_independent_20261001')
REPORT = ROOT/'reports/directionalblur_dual_independent_baseline_20261001.json'


class IndependentDualTests(unittest.TestCase):
    def test_public_current_source(self):
        capture = json.loads(REPORT.read_text())
        self.assertEqual(capture['aex_sha256'], probe.AEX_SHA)
        self.assertEqual(capture['worker_sha256'], probe.WORKER_SHA)
        self.assertEqual(capture['case_count'], 216)
        self.assertEqual(len(capture['cases']), 216)
        self.assertEqual(capture['summary']['both_cmd_exact_count'], 216)
        # Capture source identity is historical; replay current source below.
        for dependency, expected in capture['dependencies_sha256'].items():
            if dependency == str(probe.SOURCE.relative_to(ROOT)):
                self.assertEqual(expected, capture['source_sha256'])
            else:
                self.assertEqual(probe.sha((ROOT/dependency).read_bytes()), expected, dependency)
        self.assertTrue(capture['origin_capability_probe']['unknown_origin_field_rejected'])
        self.assertFalse(capture['origin_capability_probe']['aex_origin_render_proved'])
        expected = list(probe.specifications())
        self.assertEqual(len(expected), 216)
        for spec, case in zip(expected, capture['cases']):
            spec = json.loads(json.dumps(spec))  # JSON parameter slots are keys.
            for key, value in spec.items():
                self.assertEqual(case[key], value)
            data, layer = probe.inputs(case)
            self.assertEqual(probe.sha(data), case['input_sha256'])
            self.assertEqual(probe.sha(layer), case['layer_sha256'])
            self.assertTrue(case['session_clean'])
            self.assertEqual(case['unsupported_suite_calls'], [])
            self.assertTrue(case['frame_done']['output']['guards_intact'])
            self.assertEqual(case['frame_done']['output']['checksum'], case['native_raw_sha256'])
            for result in case['results'].values():
                self.assertTrue(result['raw_exact'])
        count = 0
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        with tempfile.TemporaryDirectory(prefix='dblur_independent_replay_') as directory:
            for sanitize in (False, True):
                binary = probe.build(Path(directory)/('san' if sanitize else 'o2'), probe.SOURCE.read_text(), sanitize)
                for case in capture['cases']:
                    for mode in ('classic', 'smart'):
                        error, raw, callbacks = probe.mac_render(binary, case, mode, env)
                        self.assertEqual(error, 0, (case['mode'], case['feature']))
                        self.assertEqual(probe.sha(raw), case['native_raw_sha256'])
                        self.assertEqual(callbacks[:3], [0,0,0] if mode == 'classic' else [21,21,2])
                        self.assertEqual(callbacks[3], callbacks[4])
                        count += 1
                print('DBLUR_INDEPENDENT_REPLAY', 'san' if sanitize else 'o2', count, flush=True)
        self.assertEqual(count, 864)


if __name__ == '__main__':
    unittest.main()
