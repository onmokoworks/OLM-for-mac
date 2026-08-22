import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "refs/conformance/olm_native_ae_declared_matrix_54_20260823.json"


class NativeAEDeclaredMatrixEvidenceTests(unittest.TestCase):
    def test_fixed_three_gate_evidence_is_complete_and_bounded(self) -> None:
        report = json.loads(REPORT.read_text())
        self.assertEqual(report["kind"], "olm_native_ae_declared_matrix_summary")
        self.assertEqual(
            report["totals"],
            {"plugins": 10, "cells": 54, "campaign_passed": 54,
             "consumer_reverified": 54, "failed": 0},
        )
        campaigns = report["campaigns"]
        self.assertEqual(len(campaigns), 10)
        self.assertEqual(sum(row["cells"] for row in campaigns), 54)
        self.assertEqual(len({row["plugin"] for row in campaigns}), 10)
        self.assertTrue(all(len(row["installed_sha256"]) == 64 for row in campaigns))
        self.assertTrue(all(len(row["campaign_sha256"]) == 64 for row in campaigns))
        self.assertIn("not additional gates", report["three_gate_policy"])

    def test_public_docs_bind_the_summary_without_adding_a_gate(self) -> None:
        gates = (ROOT / "docs/PUBLIC_BETA_3_GATES.md").read_text()
        support = (ROOT / "docs/BETA_SUPPORT.md").read_text()
        report_name = REPORT.name
        self.assertIn(report_name, gates)
        self.assertIn(report_name, support)
        self.assertIn("54/54", gates)
        self.assertIn("54/54", support)
        self.assertIn("新しい判断基準ではありません", support)


if __name__ == "__main__":
    unittest.main()
