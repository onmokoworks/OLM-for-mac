#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_natural_fullframe_exact_20260811.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_natural_fullframe_exact_20260811.json"


class Mode4NaturalFullFrameExactTests(unittest.TestCase):
    def test_same_run_seed_direction_ray_and_typed_outputs_are_exact(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(len(report["actual_aex"]["same_run_seed_f32"]), 15)
        self.assertEqual(report["actual_aex"]["same_run_direction"], {
            "slot": 1, "angle_degrees": 0, "length": 5, "blur_mode": 4,
            "seed_mat_address": report["actual_aex"]["same_run_direction"]["seed_mat_address"],
        })
        self.assertEqual(len(report["actual_aex"]["selected_ray_u32"]), 15)
        self.assertEqual(
            report["actual_aex"]["selected_ray_u32"],
            report["actual_aex"]["portable_ray_u32"],
        )
        self.assertEqual(report["comparison"], {
            "ray_plane_words": 15,
            "aggregation_words": 60,
            "final_pf8_bytes": 60,
            "final_pf16_bytes": 120,
            "final_pf32_bytes": 240,
            "max_ulp": 0,
            "ray_portable_owner": "core/kirakira_mode4.h",
            "compose_portable_owner": "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py",
            "mac_typed_writer_owner": "mac/OLMKiraKira/OLMKiraKira.cpp PixelTraits::WriteAexTruncate, selected unconditionally after RenderTyped compose",
        })
        typed = report["actual_aex"]["typed_outputs"]
        self.assertEqual(set(typed), {"PF8", "PF16", "PF32"})
        for output in typed.values():
            self.assertEqual(output["actual_hex"], output["portable_hex"])


if __name__ == "__main__":
    unittest.main()
