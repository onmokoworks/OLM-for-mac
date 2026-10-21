from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmtoondilate_ded9_incremental_install_identity_20260813.py"
REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json"
DOC = REPORT.with_suffix(".md")
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
HANDOFF = ROOT / "handoffs/olmtoondilate_ded9_incremental_install_20260813"
TRANSACTION = HANDOFF / "install_transaction.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
INSTALLED_BINARY = (
    Path.home()
    / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
)
EXPECTED_SCRIPT_SHA256 = "531c1f3d3cea9392a673d9c3f5f7d47582696dd8e04ebd9f0b6e0c4aace8cbcf"


def load():
    spec = importlib.util.spec_from_file_location("toon_ded9_post_install", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ToonDed9IncrementalInstallIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(SCRIPT) != EXPECTED_SCRIPT_SHA256:
            raise AssertionError("post-install identity auditor identity drift")
        cls.module = load()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.expected = cls.module.generate()
        cls.original_generate = cls.module.generate
        cls.module.generate = lambda: copy.deepcopy(cls.expected)

    @classmethod
    def tearDownClass(cls):
        cls.module.generate = cls.original_generate

    def reject(self, mutation):
        value = copy.deepcopy(self.report)
        mutation(value)
        with self.assertRaises(AssertionError):
            self.module.validate(value)

    def test_live_generate_and_canonical_report_exact(self):
        self.assertEqual(self.report, self.expected)
        self.assertEqual(self.report["status"], self.module.STATUS)

    def test_default_cli_is_read_only(self):
        paths = (REPORT, DOC, IDENTITY, TRANSACTION, PREINSTALL, INSTALLED_BINARY)
        before = tuple(sha(path) for path in paths)
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, tuple(sha(path) for path in paths))

    def test_source_project_installer_and_generator_tamper(self):
        self.reject(lambda row: row.__setitem__("production_source_sha256", "0" * 64))
        self.reject(lambda row: row.__setitem__("project_sha256", "0" * 64))
        self.reject(lambda row: row.__setitem__("installer_sha256", "0" * 64))
        self.reject(lambda row: row.__setitem__("generator_sha256", "0" * 64))

    def test_build_prepared_transaction_identity_hash_tamper(self):
        for key in (
            "build_identity_sha256", "preinstall_manifest_sha256", "transaction_sha256",
            "pre_identity_manifest_sha256", "accepted_identity_manifest_sha256",
            "accepted_identity_postcopy_sha256",
        ):
            self.reject(lambda row, key=key: row.__setitem__(key, "0" * 64))

    def test_new_bundle_full_inventory_tamper(self):
        self.reject(lambda row: row["bundles"]["candidate"]["manifest"].pop())
        self.reject(lambda row: row["bundles"]["installed"]["manifest"][2].__setitem__("sha256", "0" * 64))
        self.reject(lambda row: row["bundles"]["installed"].__setitem__("binary_sha256", "0" * 64))

    def test_old_three_copy_full_inventory_tamper(self):
        for name in ("installed_backup", "pre_swap_original", "moved_old"):
            self.reject(lambda row, name=name: row["bundles"][name]["manifest"].pop())
            self.reject(lambda row, name=name: row["bundles"][name].__setitem__("binary_sha256", "0" * 64))

    def test_macos11_architecture_signature_and_export_tamper(self):
        self.reject(lambda row: row["bundles"]["installed"]["macho_slice_minimum_versions"].__setitem__("arm64", "26.2"))
        self.reject(lambda row: row["bundles"]["candidate"]["architectures"].pop())
        self.reject(lambda row: row["bundles"]["installed"].__setitem__("strict_codesign", False))
        self.reject(lambda row: row["bundles"]["candidate"]["required_exports"]["x86_64"].__setitem__("_EffectMain", 0))

    def test_build_evidence_tamper(self):
        self.reject(lambda row: row["authoritative_build_evidence"].__setitem__("sha256", "0" * 64))
        self.reject(lambda row: row["authoritative_build_evidence"]["slice_minimum_versions"].__setitem__("x86_64", "26.2"))
        self.reject(lambda row: row["authoritative_build_evidence"]["required_exports"]["arm64"].pop())

    def test_prepared_evidence_tamper(self):
        self.reject(lambda row: row["prepared_evidence"].__setitem__("sha256", "0" * 64))
        self.reject(lambda row: row["prepared_evidence"]["candidate_snapshot_full_manifest"].pop())
        self.reject(lambda row: row["prepared_evidence"].__setitem__("same_volume_stage_and_handoff", False))

    def test_transaction_tamper(self):
        self.reject(lambda row: row["transaction"].__setitem__("atomic_exchange_api", "two renames"))
        self.reject(lambda row: row["transaction"].__setitem__("old_bundle_copy_count", 2))
        self.reject(lambda row: row["transaction"].__setitem__("post_identity_sha256", "0" * 64))
        self.reject(lambda row: row["transaction"]["identity_changed_plugins"].append("OLMBlur"))

    def test_identity_transition_tamper(self):
        self.reject(lambda row: row["identity_transition"]["changed_plugins"].append("OLMBlur"))
        self.reject(lambda row: row["identity_transition"]["changed_fields"]["OLMToonDilate"].pop())
        self.reject(lambda row: row["identity_transition"].__setitem__("other_nine_rows_exact", False))
        self.reject(lambda row: row["identity_transition"]["top_level_changed_fields"].append("configuration"))

    def test_absence_ae_and_count_tamper(self):
        self.reject(lambda row: row["after_effects_processes_at_audit"].append(1234))
        self.reject(lambda row: row.__setitem__("installed_bundle_count", 2))
        self.reject(lambda row: row.__setitem__("stage_absent", False))
        self.reject(lambda row: row.__setitem__("failed_new_absent", False))

    def test_claim_boundary_and_overclaim_tamper(self):
        self.reject(lambda row: row.__setitem__("claim_boundary", "release ready"))
        self.reject(lambda row: row["boundaries"].__setitem__("developer_id_signed", True))
        self.reject(lambda row: row["boundaries"].__setitem__("notarized", True))
        self.reject(lambda row: row["boundaries"].__setitem__("manifest_and_bundle_single_atomic_transaction", True))
        self.reject(lambda row: row["boundaries"].__setitem__("ae_operation_performed_by_auditor", True))


if __name__ == "__main__":
    unittest.main()
