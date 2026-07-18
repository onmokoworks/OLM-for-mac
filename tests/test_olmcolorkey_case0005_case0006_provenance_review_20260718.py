#!/usr/bin/env python3
"""Regression test for the OLMColorKey case_0005/0006 provenance review."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_REPORT = (
    ROOT
    / "refs"
    / "reports"
    / "ae_host_validation_20260618_232926"
    / "ae_pixel_olmcolorkey_20260606"
    / "reports"
    / "ae_pixel_edgethin_residual.json"
)
EXACT_MANIFEST = ROOT / "refs" / "conformance" / "bitdepth_16bpc_exact_manifest_20260709.json"
REQUEST_DIR = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "requests"
    / "ae_pixel_bitdepth16_olmcolorkey_exact_20260625"
)
RESULT_DIR = ROOT / "handoff" / "ae_pixel_validation_20260618" / "results" / "bitdepth16_olmcolorkey_exact"
CANONICAL_REF_DIR = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_bitdepth_16bpc_normalized_exact_20260625"
    / "OLMbit-depthconformancebatch"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OLMColorKeyCase0005Case0006ProvenanceTests(unittest.TestCase):
    def test_old_zero_diff_report_is_not_self_sufficient_exactness(self):
        report = load_json(OLD_REPORT)
        self.assertEqual(sorted(report.keys()), ["cases", "summary"])
        rows = {row["id"]: row for row in report["cases"]}
        for case_id in ("case_0005", "case_0006"):
            row = rows[case_id]
            self.assertEqual(row["status"], "compared")
            self.assertEqual(row["max_diff"], 0)
            self.assertEqual(row["nonzero_px"], 0)
            self.assertTrue(row["pass"])

    def test_committed_16bpc_chain_promotes_both_cases_to_ae_exact(self):
        manifest = load_json(EXACT_MANIFEST)
        request = load_json(REQUEST_DIR / "request_manifest.json")
        reference = load_json(REQUEST_DIR / "reference_manifest.json")

        threshold = request["threshold_groups"][0]
        self.assertEqual(threshold["name"], "16bpc_all_exact")
        self.assertEqual(threshold["max_diff"], 0)
        self.assertEqual(threshold["mean_diff"], 0.0)
        self.assertEqual(threshold["nonzero_px_percent"], 0.0)

        manifest_cases = {row["case_id"]: row for row in manifest["cases"]}
        request_cases = {row["id"]: row for row in request["cases"]}
        reference_cases = {row["id"]: row for row in reference["cases"]}

        for case_id in ("olmcolorkey__case_0005", "olmcolorkey__case_0006"):
            self.assertIn(case_id, threshold["case_ids"])
            self.assertEqual(reference_cases[case_id]["bits_per_channel"], 16)
            self.assertEqual(reference_cases[case_id]["project_gpu_accel_type"]["current_name"], "SOFTWARE")
            self.assertEqual(reference_cases[case_id]["requested_effect"]["name"], "OLM Color Key")

            row = manifest_cases[case_id]
            self.assertEqual(row["result_status"], "AE exact")
            self.assertEqual(row["reference_kind"], "Windows AE Software")
            self.assertEqual(row["runner_kind"], "Mac AE plugin")
            self.assertEqual(row["max_diff"], 0)
            self.assertEqual(row["mean_diff"], 0.0)
            self.assertEqual(row["nonzero_px_percent"], 0.0)

            frame = request_cases[case_id]["frame"]
            result_png = ROOT / row["output_path"]
            expected_png = REQUEST_DIR / "expected" / frame
            canonical_png = CANONICAL_REF_DIR / frame

            digest = sha256(result_png)
            self.assertEqual(digest, row["output_sha256"])
            self.assertEqual(digest, sha256(expected_png))
            self.assertEqual(digest, sha256(canonical_png))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
