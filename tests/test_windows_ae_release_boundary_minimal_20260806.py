#!/usr/bin/env python3
"""Keep the one-shot Windows package aligned with the frozen release matrix."""

from __future__ import annotations

import importlib.util
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
PACKAGE = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
PACKAGER = ROOT / "scripts/package_windows_ae_release_boundary_minimal_20260806.py"
EXPECTED = {
    ("ColorKeep", "colorkeep_opaque_cells_red_darkgray", depth) for depth in (8, 16, 32)
} | {
    ("OLMKiraKira", "kk_mapped_bm4_mm1_hi_r5_orange_opaque", depth) for depth in (8, 16, 32)
} | {("OLMSmoother v1", "case_0001", 16)}


def load_packager():
    spec = importlib.util.spec_from_file_location("olm_minimal_packager", PACKAGER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MinimalWindowsBoundaryScopeTest(unittest.TestCase):
    def test_authoritative_matrix_declares_exact_required_families(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        required = (
            "ColorKeep controlled calibration at PF8/PF16/PF32",
            "OLMKiraKira controlled Mode4 calibration at PF8/PF16/PF32",
            "OLMSmoother v1 PF16, one representative canonical row",
            "These seven observations belong in one batch.",
        )
        for phrase in required:
            self.assertIn(phrase, text)

    def test_packager_and_checked_in_zip_have_exact_seven_rows(self) -> None:
        module = load_packager()
        self.assertEqual(module.SELECTED, EXPECTED)
        self.assertEqual(set(module.REUSED), {
            "OLMBlur", "OLMColorKey", "OLMToonDilate", "OLMSmoother2",
            "OLMDistanceGradation", "OLMDirectionalBlur", "OLMRadialBlur",
        })
        with zipfile.ZipFile(PACKAGE) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
            embedded_matrix = archive.read(contract["authoritative_release_scope"]["member"])
        rows = {(r["plugin"], r["case_id"], r["depth"]) for r in contract["acquire"]}
        self.assertEqual(rows, EXPECTED)
        self.assertEqual(len(contract["acquire"]), 7)
        self.assertEqual(embedded_matrix, MATRIX.read_bytes())


if __name__ == "__main__":
    unittest.main()
