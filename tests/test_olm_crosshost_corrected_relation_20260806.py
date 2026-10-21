#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CorrectedRelationTests(unittest.TestCase):
    def test_bounded_verifier_accepts_without_raw_or_kira_overclaim(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_olm_crosshost_corrected_relation_20260806.py")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "accepted_bounded_relation")
        self.assertEqual(payload["color_keep_relation_exact_depths"], [8, 16, 32])
        self.assertEqual(payload["kira_operation_exact_depths"], [])
        self.assertEqual(payload["raw_cross_host_exact_rows"], [])

    def test_normalized_pf32_control_exact_does_not_promote_kira_effect(self) -> None:
        data = json.loads((ROOT / "refs/conformance/olmkirakira_crosshost_normalized_mac_ae_20260806.json").read_text(encoding="utf-8"))
        pf32 = next(row for row in data["rows"] if row["depth"] == 32)
        self.assertTrue(pf32["branches"]["no_effect"]["exact"])
        self.assertEqual(pf32["branches"]["no_effect"]["mismatched_values"], 0)
        self.assertFalse(pf32["branches"]["effect_on"]["exact"])
        self.assertEqual(pf32["branches"]["effect_on"]["mismatched_values"], 6220800)
        self.assertEqual(data["status"], "mismatch")

    def test_corrected_binding_and_host_transfer_are_all_depth(self) -> None:
        data = json.loads((ROOT / "refs/conformance/olm_crosshost_corrected_return_audit_20260806.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["rows"]), 6)
        for row in data["rows"]:
            self.assertTrue(row["channel_binding_correct"])
            self.assertTrue(row["source_interpretation_equal"])
            self.assertEqual(row["no_effect_host_transfer"]["conflicting_input_words"], 0)
            self.assertAlmostEqual(row["no_effect_host_transfer"]["effective_power_median"], 2.4, places=4)


if __name__ == "__main__": unittest.main()
