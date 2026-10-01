"""Production YUV/YCrCb limits against native boundaries and finite-overflow witnesses."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
import probe_olmcolorkey_typed_controls_20261001 as owner
import probe_olmcolorkey_rgb_hsv_yuv_boundary_20261001 as boundary
import probe_olmcolorkey_finite_overflow_20261001 as overflow
import probe_olmcolorkey_yuv_third_limit_20261001 as third

LAST_VALIDATION = {}


class YuvLimitsTests(unittest.TestCase):
    def test_native_threshold_and_unordered_predicates(self):
        definitions = (
            ('rgb_hsv_yuv_boundary', boundary.fixture, 1728, 1536),
            ('finite_overflow', overflow.fixture, 512, 448),
            ('yuv_third_limit', boundary.fixture, 108, 84),
        )
        reports = []
        for name, fixture, count, old_exact in definitions:
            report = json.loads((ROOT / f'reports/colorkey_{name}_baseline_20261001.json').read_text())
            self.assertEqual(report['case_count'], count)
            old = report['summary'] if name == 'rgb_hsv_yuv_boundary' else report['summary']['production']
            self.assertEqual(old, {'classic': old_exact, 'smart': old_exact})
            self.assertEqual(report['frozen_worker_sha256'], boundary.FROZEN_SHA)
            for path, digest in report['dependencies_sha256'].items():
                self.assertEqual(owner.sha((ROOT / path).read_bytes()), digest, path)
            if name == 'rgb_hsv_yuv_boundary':
                self.assertEqual(report['family_count'], 144)
                for search in report['searches']:
                    self.assertEqual(search['first_matched_bits'], search['last_unmatched_bits'] + 1)
                    observations = {item['threshold_bits']: item['matched'] for item in search['trace']}
                    self.assertFalse(observations[search['last_unmatched_bits']])
                    self.assertTrue(observations[search['first_matched_bits']])
            else:
                self.assertEqual(report['summary']['candidate'], {'classic': count, 'smart': count})
            reports.append((name, fixture, report))
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1')
        saved_fixture = owner.fixture
        counts = {}
        try:
            with tempfile.TemporaryDirectory(prefix='olmck_yuv_limits_replay_') as directory:
                temp = Path(directory)
                for sanitize, build in ((False, 'o2'), (True, 'asan_ubsan')):
                    exe = owner.compile_public(temp / build, owner.SOURCE.read_text(), sanitize)
                    total = 0
                    for name, fixture, report in reports:
                        owner.fixture = fixture
                        for case in report['cases']:
                            raw, _ = fixture(case['fixture'], case['depth'])
                            self.assertEqual(owner.sha(raw), case['input_sha256'])
                            self.assertTrue(case['session_clean'])
                            self.assertEqual(case['unsupported_suite_calls'], [])
                            self.assertTrue(case['frame_done']['output']['guards_intact'])
                            for route in (0, 1):
                                error, out = owner.mac_render(exe, temp, case, route, env if sanitize else None)
                                self.assertEqual(error, 0)
                                self.assertEqual(len(out), case['raw_pixel_bytes'])
                                self.assertEqual(owner.sha(out), case['actual_sha256'],
                                                 (build, name, case['label'], case['depth'], route))
                                total += 1
                        print('YUV_LIMITS_REPLAY', build, name, total, flush=True)
                    counts[build] = total
        finally:
            owner.fixture = saved_fixture
        LAST_VALIDATION.update(source_sha256=owner.sha(owner.SOURCE.read_bytes()),
                               capture_rows_replayed=2348, historical_counterexamples_closed=280,
                               successful_render_counts=counts,
                               negative_third_controls_are_outside_ui_range=True)


if __name__ == '__main__':
    unittest.main()
