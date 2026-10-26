#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_compose_matrix_actual_aex_20260811.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_compose_matrix_actual_aex_20260811.json"
PRODUCTION = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"


class Mode4ComposeMatrixActualAexTests(unittest.TestCase):
    def test_compose_matrix_is_raw_exact(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["exact"], {
            "cases": 5, "aggregate_bytes": 320, "typed_bytes": 560, "max_ulp": 0,
        })
        self.assertEqual({case["merge_mode"] for case in report["cases"]}, {1, 2})
        self.assertEqual({case["directional_slot"] for case in report["cases"]}, {0, 3})
        self.assertTrue(any(case["flags"][0] and case["flags"][4] for case in report["cases"]))
        for case in report["cases"]:
            self.assertEqual(set(case["typed_outputs"]), {"PF8", "PF16", "PF32"})
            for typed in case["typed_outputs"].values():
                self.assertEqual(typed["actual_hex"], typed["portable_hex"])

    def test_production_preserves_actual_slot_order_and_length_one(self) -> None:
        source = PRODUCTION.read_text(encoding="utf-8")
        source += "\n".join(p.read_text() for p in sorted((ROOT / "mac/OLMKiraKira").glob("Kira*.inc")))
        self.assertIn("if (length <= 0) return input;", source)
        self.assertNotIn("if (length <= 1) return input;", source)
        d2 = source.index("AddColoredUnion(glow, diagonal2")
        highlight = source.index("AddColoredUnion(glow, highlight")
        self.assertLess(d2, highlight)
        self.assertEqual(source.count("AddColoredUnion(glow,"), 5)
        self.assertNotIn("AddColoredMerge2(glow,", source)
        self.assertIn("state+0x48 to one", source)


if __name__ == "__main__":
    unittest.main()
