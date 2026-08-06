#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/test_olmkirakira_mode4_highlight_hostless_actual_aex_20260807.py"


class Mode4HighlightHostlessActualAexTests(unittest.TestCase):
    def test_actual_aex_aggregation_compose_writer_is_word_exact(self) -> None:
        result = subprocess.run(
            ["python3", str(PROBE)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("PASS_OLMKIRAKIRA_MODE4_HIGHLIGHT_HOSTLESS_ACTUAL_AEX", result.stdout)


if __name__ == "__main__":
    unittest.main()
