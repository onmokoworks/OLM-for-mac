from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json"
AUDIT = ROOT / "refs/conformance/olmdistancegradation_32bpc_float_evidence_audit_20260715.json"
AUDITOR = ROOT / "refs/scripts/smoke_audit_olmdistancegradation_32bpc_float_evidence_20260715.py"


class DistanceGradation32bpcMacValidationTest(unittest.TestCase):
    def test_contract_is_fail_closed_and_scoped(self) -> None:
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["status"], "sendable_fail_closed_no_ae_exact_claim")
        self.assertEqual(request["candidate_case_count"], 29)
        self.assertTrue(request["required_contract"]["float_preserving"])
        self.assertTrue(request["acceptance"]["candidate_return_is_not_ae_exact"])
        self.assertIn("raw_float_comparison_summary", request["per_case_binding_required"])

    def test_audit_has_no_mac_exact_cases(self) -> None:
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(audit["candidate_subset"]["case_count"], 29)
        self.assertEqual(audit["rejected_or_pending"]["mac_exact_case_count"], 0)
        self.assertEqual(len(audit["cases"]), 29)
        for case in audit["cases"]:
            self.assertEqual(case["render_set_id"], "software_32bpc")
            self.assertTrue(case["input_sha256"])
            self.assertTrue(case["output_sha256"])
            self.assertEqual(len(case["effect"]["params"]), 12)

    def test_auditor_rechecks_imported_pairs(self) -> None:
        result = subprocess.run([sys.executable, str(AUDITOR), "--check"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"candidate_case_count": 29', result.stdout)


if __name__ == "__main__":
    unittest.main()
