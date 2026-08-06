#!/usr/bin/env python3
"""Fail closed when release-facing claims drift from the frozen gate/package."""

from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md"
MATRIX = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
STATUS = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
PACKAGE = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
PACKAGE_SHA256 = "64f58ef0901d6dc0ba1b67ceb139b63a5ab496cdb9f72868b9fcd6c9dd6db190"
EXPECTED_ROWS = {
    ("ColorKeep", "colorkeep_opaque_cells_red_darkgray", depth)
    for depth in (8, 16, 32)
} | {
    ("OLMKiraKira", "kk_mapped_bm4_mm1_hi_r5_orange_opaque", depth)
    for depth in (8, 16, 32)
} | {("OLMSmoother v1", "case_0001", 16)}


class ReleaseDocumentationConsistencyTest(unittest.TestCase):
    def test_notes_pin_host_and_do_not_promote_smoother_v1_pf32(self) -> None:
        text = NOTES.read_text(encoding="utf-8")
        for phrase in (
            "After Effects `26.3x87`",
            "CPU `SOFTWARE`",
            "exactly seven Windows AE rows",
            "The AEX has no native PF32 callback",
            "32bpc projects are AE host-converted",
            "PF8 centered neutral Inner Strength 1..64",
            "PF16 Type3 Layer is limited to 16x16",
        ):
            self.assertIn(phrase, text)

    def test_matrix_has_no_superseded_release_holes(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        self.assertNotIn("**Missing Inner representative**", text)
        self.assertNotIn("Real production/host hole", text)
        self.assertIn("PF8 Inner is geometry-generic only inside its admitted", text)
        self.assertIn("PF16 Type3 Layer is exact only for 16x16", text)

    def test_gate_and_seven_row_package_match_release_notes(self) -> None:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "release_gate_pass")
        self.assertTrue(status["releasable"])
        self.assertEqual(status["mac_ae_representative"]["counts"], {
            "invalid": 0, "pending": 0, "proven": 10,
        })
        self.assertEqual(status["universal_installs"]["bundle_count"], 10)
        self.assertEqual(hashlib.sha256(PACKAGE.read_bytes()).hexdigest(), PACKAGE_SHA256)
        with zipfile.ZipFile(PACKAGE) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
        rows = {(r["plugin"], r["case_id"], r["depth"]) for r in contract["acquire"]}
        self.assertEqual(rows, EXPECTED_ROWS)


if __name__ == "__main__":
    unittest.main()
