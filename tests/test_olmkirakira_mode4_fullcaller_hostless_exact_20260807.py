#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_fullcaller_hostless_exact_20260807.json"


class Mode4FullCallerHostlessExactTests(unittest.TestCase):
    def test_actual_aex_fullcaller_is_exact_through_pf32_writer(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["abi"]["argument_slots"], 16)
        self.assertEqual(report["comparison"]["highlight_plane_words"], 4)
        self.assertEqual(report["comparison"]["aggregation_words"], 16)
        self.assertEqual(report["comparison"]["final_pf32_words"], 16)
        self.assertEqual(report["comparison"]["max_ulp"], 0)
        self.assertEqual(report["actual_aex"]["suite_acquire_count"], 12)
        self.assertEqual(report["actual_aex"]["suite_release_count"], 12)
        self.assertIsNone(report["actual_aex"]["fault"])


if __name__ == "__main__":
    unittest.main()
