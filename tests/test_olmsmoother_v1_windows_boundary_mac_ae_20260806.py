#!/usr/bin/env python3
"""Static fail-closed contract for the Smoother v1 PF16 Mac replay gate."""
from __future__ import annotations

import ast
import hashlib
import json
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olmsmoother_v1_windows_boundary_mac_ae_20260806.py"
REQUEST = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.json"
ROW_ID = "olmsmoother_v1__canonical_3__case_0001__16bpc"


class SmootherV1WindowsBoundaryMacAEContractTests(unittest.TestCase):
    def test_runner_is_valid_python_and_pins_canonical_request(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip", source)
        self.assertIn("6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652", source)
        for gate in ("raw_float32_compare", "loaded_smoother_modules", "parameter_surface_exact", "pf16_exact_eligible",
                     "beginSuppressDialogs", "endSuppressDialogs", "with timeout of 900 seconds"):
            self.assertIn(gate, source)

    def test_canonical_request_contains_exactly_one_native_pf16_smoother_row(self) -> None:
        self.assertEqual(
            hashlib.sha256(REQUEST.read_bytes()).hexdigest(),
            "6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652",
        )
        with zipfile.ZipFile(REQUEST) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
        rows = [row for row in contract["acquire"] if row["row_id"] == ROW_ID]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["plugin"], row["depth"], row["case_id"]), ("OLMSmoother v1", 16, "case_0001"))
        self.assertEqual(row["source_sha256"], "166cafc8aaa2bb2d78ed26a12fe95b6dcf0f6eeeabd7f3a4daaf0ceece500e4c")
        self.assertEqual([(item["match_name"], item["value"]) for item in row["parameter_writes"]], [
            ("OLM Smoother-0001", 0),
            ("OLM Smoother-0002", [1.0, 1.0, 1.0, 1.0]),
            ("OLM Smoother-0003", 6),
        ])

    def test_current_mac_replay_remains_fail_closed(self) -> None:
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["row_id"], ROW_ID)
        self.assertEqual(report["status"], "mismatch")
        self.assertFalse(report["pf16_exact_eligible"])
        self.assertTrue(report["host_identity"]["exact"])
        self.assertTrue(report["parameter_surface_exact"])
        self.assertTrue(report["branches"]["no_effect"]["raw_float32_compare"]["equal"])
        effect = report["branches"]["effect_on"]["raw_float32_compare"]
        self.assertFalse(effect["equal"])
        self.assertEqual(effect["nonzero_count"], 183)


if __name__ == "__main__":
    unittest.main()
