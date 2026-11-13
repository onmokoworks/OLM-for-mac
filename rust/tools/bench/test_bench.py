import copy
import unittest

from bench import assignments, drop_frames, parse_report, stats
from report import adjusted


class FrameCleanupTests(unittest.TestCase):
    def test_drop_frames_removes_png_and_native_only(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for name in ('rust-0.png', 'rust-0.rgba16le', 'rust-0.rgba32f-le', 'keep.json'):
                (d / name).write_bytes(b'x')
            manifest = {'cases': [{'output': str(d / 'rust-0.png')}, {'output': str(d / 'rust-1.png')}]}
            self.assertEqual(drop_frames(manifest), 3)
            self.assertEqual(sorted(p.name for p in d.iterdir()), ['keep.json'])


class StatisticsTests(unittest.TestCase):
    def test_angle_uses_typed_components(self):
        self.assertEqual(assignments('OLMDirectionalBlur', 'heavy')[0],
                         {'slot': 1, 'components': [35]})

    def test_median_not_mean_and_min(self):
        self.assertEqual(stats([8, 1, 2, 3, 100]), {'n': 5, 'median_ms': 3, 'min_ms': 1})

    def test_even(self):
        self.assertEqual(stats([2, 4])['median_ms'], 3)

    def test_bad_values(self):
        for values in ([], [-1], [float('nan')], [float('inf')]):
            with self.assertRaises(ValueError):
                stats(values)

    def test_subtraction(self):
        self.assertEqual(adjusted([3, 5, 7], 2), {'n': 3, 'median_ms': 3, 'min_ms': 1})
        self.assertIsNone(adjusted([1, 4, 9], 2))


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {'route': 'smart16', 'cases': [{'id': '0'}, {'id': '1'}]}
        self.report = {'schema': 'aexcompat.independent_case_batch', 'schema_version': 1,
                       'route': 'smart16', 'isolation': 'fresh_sequence', 'complete': True,
                       'session_close': {'independent_cases_clean': True}, 'plugin_sha256': 'abc',
                       'cases': [{'id': str(i), 'case_index': i, 'passed': True, 'evidence_valid': True,
                                  'evidence_provisional': False, 'case_cleanup': True,
                                  'plugin_sha256': 'abc', 'requested_route': 'smart16',
                                  'performance_diagnostics': {'render_selector_ns': 2000000,
                                      'worker_render_ns': 3000000, 'broker_frame_wall_ns': 4000000}}
                                 for i in range(2)]}

    def test_units_and_order(self):
        self.report['cases'].reverse()
        self.assertEqual(parse_report(self.report, self.manifest, 'abc')[0]['render_selector_ns'], 2)

    def test_reject_bad_envelopes(self):
        for field, value in [('route', 'smart8'), ('plugin_sha256', 'bad'), ('complete', False)]:
            report = copy.deepcopy(self.report); report[field] = value
            with self.assertRaises(ValueError):
                parse_report(report, self.manifest, 'abc')

    def test_reject_missing_duplicate_and_partial(self):
        for mode in ('missing', 'duplicate', 'failed', 'provisional'):
            report = copy.deepcopy(self.report)
            if mode == 'missing': report['cases'].pop()
            if mode == 'duplicate': report['cases'][1]['id'] = '0'
            if mode == 'failed': report['cases'][1]['passed'] = False
            if mode == 'provisional': report['cases'][1]['evidence_provisional'] = True
            with self.assertRaises(ValueError):
                parse_report(report, self.manifest, 'abc')

    def test_reject_nonfinite_timing(self):
        self.report['cases'][0]['performance_diagnostics']['render_selector_ns'] = float('nan')
        with self.assertRaises(ValueError):
            parse_report(self.report, self.manifest, 'abc')


if __name__ == '__main__':
    unittest.main()
