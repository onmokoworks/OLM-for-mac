from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/audit_olmsmoother_source_bound_universal_candidates_20260813.py"
spec = importlib.util.spec_from_file_location("smoother_build_audit", TOOL)
audit = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(audit)

CURRENT_AUDIT_TOOL_SHA256 = "c2ced3b4bc10e35497fa0c6b1bc2095f9669f2618bc61a8d5efb4a671be56649"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CandidateIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(audit.MANIFEST.read_text())

    def test_frozen_build_and_current_relation(self) -> None:
        self.assertEqual(sha256(TOOL), CURRENT_AUDIT_TOOL_SHA256)
        audit.validate_current_relation(copy.deepcopy(self.data))

    def test_unknown_top_level_key_rejected(self) -> None:
        data = copy.deepcopy(self.data); data["extra"] = 1
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)

    def test_claim_widening_rejected(self) -> None:
        data = copy.deepcopy(self.data); data["claim_boundary"]["installed"] = True
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)

    def test_claim_authority_and_extra_key_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["claim_boundary"]["numerical_claim_authority"] = "forged.json"
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)
        data = copy.deepcopy(self.data)
        data["claim_boundary"]["extra"] = False
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)

    def test_source_stability_tamper_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        first = next(iter(data["bound_inputs_after"]))
        data["bound_inputs_after"][first]["sha256"] = "0" * 64
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)

    def test_validator_identity_tamper_rejected_live(self) -> None:
        data = copy.deepcopy(self.data)
        first = next(iter(data["validation_files"]))
        data["validation_files"][first]["sha256"] = "1" * 64
        with self.assertRaises(AssertionError): audit.validate_current_relation(data)

    def test_architecture_tamper_rejected_live(self) -> None:
        data = copy.deepcopy(self.data); data["builds"]["OLMSmoother"]["architectures"] = ["arm64"]
        with self.assertRaises(AssertionError): audit.validate_current_relation(data)

    def test_build_command_export_and_codesign_tamper_rejected(self) -> None:
        data = copy.deepcopy(self.data)
        data["builds"]["OLMSmoother"]["command"][-2] = "MACOSX_DEPLOYMENT_TARGET=26.2"
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)
        data = copy.deepcopy(self.data)
        data["builds"]["OLMSmoother2"]["exports"]["arm64"] = ["_EffectMain", "_forged"]
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)
        data = copy.deepcopy(self.data)
        data["builds"]["OLMSmoother2"]["codesign"] = "Developer ID"
        with self.assertRaises(AssertionError): audit.validate_data(data, live=False)

    def test_inventory_tamper_rejected_live(self) -> None:
        data = copy.deepcopy(self.data)
        file_row = next(row for row in data["builds"]["OLMSmoother2"]["inventory"] if row["kind"] == "file")
        file_row["sha256"] = "f" * 64
        with self.assertRaises(AssertionError): audit.validate_current_relation(data)

    def test_current_docs_separate_build_time_and_installed_state(self) -> None:
        release_notes = (ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md").read_text()
        matrix = (ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md").read_text()
        boundary = (ROOT / "refs/conformance/olm_mac_port_orchestrator_boundary_20260805.md").read_text()
        ledger = (ROOT / "notes/CONFORMANCE_LEDGER.md").read_text()
        self.assertIn("両bundleはその後batch4でfull inventory exactにinstall済み", release_notes)
        self.assertIn("current installed relation `olm_hostless_batch4_incremental_install_20260813", matrix)
        self.assertNotIn("The source-bound Universal candidate is not installed", boundary)
        self.assertIn("That manifest is immutable pre-install build", ledger)


if __name__ == "__main__":
    unittest.main()
