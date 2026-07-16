"""Focused contract tests for the case_0004 natural checkpoint probe."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "emulation"
LEGACY = TOOLS / "probe_olmblur_case0004_staged_helper_replay.py"
PROBE = TOOLS / "probe_olmblur_case0004_checkpoint_resume_20260717.py"


class Case0004CheckpointResumeTest(unittest.TestCase):
    def test_legacy_bounded_probe_is_unchanged(self) -> None:
        expected = subprocess.run(
            ["git", "show", "HEAD:tools/emulation/probe_olmblur_case0004_staged_helper_replay.py"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        self.assertEqual(LEGACY.read_bytes(), expected)

    def test_checkpoint_probe_has_natural_and_fail_closed_contract(self) -> None:
        source = PROBE.read_text()
        for forbidden in ("write_bytes(FUN_HORIZONTAL", "portable_full_cone_result", "def crop("):
            self.assertNotIn(forbidden, source)
        self.assertIn("--save-checkpoint-at-rip", source)
        self.assertIn("--resume-checkpoint", source)
        self.assertIn("WRITER_PRE", source)
        self.assertIn("WRITER_POST", source)

    def test_missing_resume_checkpoint_is_nonzero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PROBE), "--resume-checkpoint", "/tmp/olmblur-case0004-missing.aexcp",
             "--max-instructions", "1"],
            cwd=ROOT, check=False, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "fail-closed"', result.stdout)


if __name__ == "__main__":
    unittest.main()
