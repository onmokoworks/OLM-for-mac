#!/usr/bin/env python3
"""Focused fail-closed contract test for the case_0004 boundary audit."""

from __future__ import annotations

import json
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmblur_case0004_checkpoint_resume_20260718.py"
REPORT = ROOT / "refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.json"

SPEC = importlib.util.spec_from_file_location("olmblur_case0004_boundary_audit", AUDIT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Case0004BoundaryAuditTest(unittest.TestCase):
    def test_checked_in_report_is_boundary_scoped_and_fail_closed(self) -> None:
        report = json.loads(REPORT.read_text())
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["fact"]["resumed"]["helpers"])
        self.assertIn("helper_output", report["inference"])
        self.assertFalse(report["inference"]["writer_pre_store"])
        self.assertIn("does not claim AE exact", report["claim_limit"])
        self.assertNotIn(str(Path.home()), REPORT.read_text())

    def test_source_has_no_mutation_or_exactness_shortcuts(self) -> None:
        source = AUDIT.read_text()
        for forbidden in ("write_bytes(FUN_HORIZONTAL", "write_bytes(FUN_VERTICAL", "claim_exact", "promote_exact"):
            self.assertNotIn(forbidden, source)
        self.assertIn("load_checkpoint", source)
        self.assertIn("WRITER_PRE", source)
        self.assertIn("WRITER_POST", source)

    def test_empty_witness_helper_must_not_vacuously_complete(self) -> None:
        resumed = {"helpers": [{"witnesses_before": {}}], "writer": []}
        self.assertEqual(
            MODULE.classify({}, resumed),
            "helper_entry_observed_helper_output_incomplete",
        )
        report = MODULE.build_report(Path("/tmp/unused.aexcp"), {}, resumed, 1)
        self.assertFalse(report["inference"]["helper_output"])


if __name__ == "__main__":
    unittest.main()
