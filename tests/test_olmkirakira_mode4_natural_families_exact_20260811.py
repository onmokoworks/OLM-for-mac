#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_natural_families_exact_20260811.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_natural_families_exact_20260811.json"


class Mode4NaturalFamiliesExactTests(unittest.TestCase):
    def test_five_same_run_families_are_exact(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["exact"], {
            "cases": 5, "ray_words": 75, "typed_rows": 15,
            "remaining_family_typed_rows": 12, "typed_bytes": 2100,
            "max_ulp": 0,
        })
        self.assertEqual({case["same_run_direction"]["slot"] for case in report["cases"]}, set(range(5)))
        self.assertEqual({case["name"] for case in report["cases"]}, {
            "horizontal_control", "vertical_rot17_len7", "diagonal_rot13_len11",
            "diagonal2_rotm11_len9", "highlight_constant_radius3",
        })
        for case in report["cases"]:
            self.assertEqual(len(case["same_run_seed_f32"]), 15)
            self.assertEqual(case["selected_ray_u32"], case["portable_ray_u32"])
            self.assertEqual(set(case["typed_outputs"]), {"PF8", "PF16", "PF32"})
            for typed in case["typed_outputs"].values():
                self.assertEqual(typed["actual_hex"], typed["portable_hex"])


if __name__ == "__main__":
    unittest.main()
