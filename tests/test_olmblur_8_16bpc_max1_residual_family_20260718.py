#!/usr/bin/env python3
"""Regression test for the bounded OLMBlur max=1 family audit."""

from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/emulation/test_olmblur_8_16bpc_max1_residual_family_20260718.py"


class OLMBlurMax1AuditTests(unittest.TestCase):
    def test_report_reproduces_and_keeps_the_bounded_fact(self):
        result = runpy.run_path(str(AUDIT), run_name="audit")
        result["main"]()
        report = result["REPORT"]
        self.assertTrue(report.exists())
        self.assertIn("not classified as a final-writer-only issue", report.read_text())
