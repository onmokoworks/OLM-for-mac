#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"


class Mode4FullCallerMultilineFixtureTests(unittest.TestCase):
    def test_mat_rows_are_flattened_without_dropping_later_rows(self) -> None:
        spec = importlib.util.spec_from_file_location("kira_mode4_fullcaller", PROBE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module.flatten_mat_rows([[0.0, 0.25], [0.5, 0.75], [1.0, 1.25]]),
            [0.0, 0.25, 0.5, 0.75, 1.0, 1.25],
        )


if __name__ == "__main__":
    unittest.main()
