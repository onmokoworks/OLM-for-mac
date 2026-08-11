#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode1_exported_effectmain_all_depths_20260812.json"


class Mode1ExportedEffectMainAllDepthsTests(unittest.TestCase):
    def test_three_depths_are_exact(self) -> None:
        subprocess.run(["python3", str(PROBE)], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual({row["depth"] for row in report["rows"]}, {"PF8", "PF16", "PF32"})
        self.assertTrue(all(row["exact"] and row["guards_intact"] and
                            row["input_unchanged"] and row["mac_padding_preserved"]
                            for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
