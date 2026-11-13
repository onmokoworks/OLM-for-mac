import unittest

from measure import process_sample, stats, summarize_cases, summarize_performance


class MeasurementTests(unittest.TestCase):
    def test_nested_clock_is_subtracted_once(self):
        r = {"stdout": '{"worker_diagnostics":{"elapsed_ms":100}}', "pid": 12,
             "elapsed_seconds": .4, "returncode": 0, "timeout": False}
        s = process_sample(r)
        self.assertEqual(s["outside_render_worker_ms"], 300)
        self.assertEqual(s["wall_ms"], 400)

    def test_absent_worker_timing_is_not_invented(self):
        s = process_sample({"stdout": '[]', "pid": 1, "elapsed_seconds": .2,
                            "returncode": 0, "timeout": False})
        self.assertIsNone(s["outside_render_worker_ms"])

    def test_failures_and_slow_samples_are_retained(self):
        sample = {"wall_ms": 1000, "render_worker_lifetime_ms": None,
                  "outside_render_worker_ms": None}
        rows = [{"status": "reference_timeout", "sides": {"reference": sample}}]
        summary = summarize_cases(rows)
        self.assertEqual(summary["failures"], ["reference_timeout"])
        self.assertEqual(summary["exact_pairs"], 0)
        self.assertEqual(summary["wall_ms"]["median"], 1000)

    def test_repeated_frame_ratio_excludes_cold_from_warm(self):
        base = dict(width=320, height=180, input_write_ns=1000, worker_setup_ns=1000,
                    worker_render_ns=6000, selector_dispatch_ns=5000,
                    worker_finalize_ns=1000, output_verify_ns=1000)
        report = {"status": "available", "samples": [
            dict(base, cold=True, session_open_ns=100000, wall_ns=40000),
            dict(base, cold=False, session_open_ns=None, wall_ns=10000),
            dict(base, cold=False, session_open_ns=None, wall_ns=20000)]}
        row = summarize_performance([report])[0]
        self.assertAlmostEqual(row["open_plus_cold_over_warm"], 140 / 15)
        self.assertEqual(row["warm_count"], 2)
        self.assertEqual(row["cold_count"], 1)

    def test_incomplete_diagnostic_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize_performance([{"status": "unavailable", "samples": []}])

    def test_no_outliers_are_discarded(self):
        self.assertEqual(stats([1, 2, 1000]),
                         {"count": 3, "median": 2, "min": 1, "max": 1000})
        self.assertIsNone(stats([])["median"])


if __name__ == "__main__":
    unittest.main()
