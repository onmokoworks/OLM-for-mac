#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_fullcaller_hostless_exact_20260807.json"
PRODUCTION = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"


class Mode4FullCallerHostlessExactTests(unittest.TestCase):
    def test_actual_aex_fullcaller_is_exact_through_all_typed_writers(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["abi"]["argument_slots"], 16)
        self.assertEqual(report["comparison"]["highlight_plane_words"], 4)
        self.assertEqual(report["comparison"]["aggregation_words"], 16)
        self.assertEqual(report["comparison"]["final_pf8_bytes"], 16)
        self.assertEqual(report["comparison"]["final_pf16_bytes"], 32)
        self.assertEqual(report["comparison"]["final_pf32_bytes"], 64)
        self.assertEqual(report["comparison"]["max_ulp"], 0)
        typed = report["actual_aex"]["typed_outputs"]
        self.assertEqual(set(typed), {"PF8", "PF16", "PF32"})
        for depth in typed:
            self.assertEqual(typed[depth]["actual_hex"], typed[depth]["portable_hex"])
        self.assertEqual(report["actual_aex"]["suite_acquire_count"], 12)
        self.assertEqual(report["actual_aex"]["suite_release_count"], 12)
        self.assertIsNone(report["actual_aex"]["fault"])

    def test_mac_production_owns_the_bounded_highlight_and_typed_writer(self) -> None:
        source = PRODUCTION.read_text(encoding="utf-8")
        self.assertIn("olm::kirakira::highlight_isotropic_box_blur(", source)
        self.assertIn(
            "*PixelAt<PixelT>(output, x, y) = PixelTraits<PixelT>::WriteAexTruncate(out);",
            source,
        )
        self.assertNotIn(
            "info.merge_mode == 2\n\t\t\t\t? PixelTraits<PixelT>::WriteAexTruncate(out)",
            source,
        )


if __name__ == "__main__":
    unittest.main()
