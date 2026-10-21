from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_remaining6_native_ucrt_replay_20260815.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_native_ucrt_replay_20260815.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("dblur_native_ucrt_replay", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalRemaining6NativeUcrtReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_tool()
        cls.report = json.loads(REPORT.read_text())

    def test_frozen_report_validates_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(TOOL), "--validate-only"], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)
        self.assertTrue(self.tool.validate(self.report))

    def test_all_six_match_native_and_preexisting_x86(self) -> None:
        self.assertEqual(len(self.report["rows"]), 6)
        self.assertTrue(all(row["same_table_full_raw_exact"] for row in self.report["rows"]))
        self.assertTrue(all(row["native_matches_preexisting_x86_raw"] for row in self.report["rows"]))
        self.assertEqual(self.report["decision"]["promotable_cells"], 6)
        self.assertFalse(self.report["decision"]["production_math_change_required"])

    def test_row_and_decision_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["native_matches_preexisting_x86_raw"] = False
        changed["rows_sha256"] = self.tool.digest(changed["rows"])
        self.assertFalse(self.tool.validate(changed))
        changed = copy.deepcopy(self.report)
        changed["decision"]["production_math_change_required"] = True
        self.assertFalse(self.tool.validate(changed))


if __name__ == "__main__":
    unittest.main()
