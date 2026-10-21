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
SCRIPT = ROOT / "tools/emulation/audit_colorkeep_count9_incremental_install_identity_20260813.py"
REPORT = ROOT / "refs/conformance/colorkeep_count9_incremental_install_identity_20260813.json"
DOC = REPORT.with_suffix(".md")


def load():
    spec = importlib.util.spec_from_file_location("colorkeep_install_identity", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ColorKeepCount9IncrementalInstallIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def test_live_generate_and_report_are_exact(self):
        self.assertEqual(self.report, self.expected)
        self.assertEqual(self.report["production_source_sha256"],
                         "3ff3a4d4319f5b3b5519e517fcf591be417c97e4e9dd62117fe4e42f66ebdfd3")

    def test_default_cli_is_read_only(self):
        before = (hashlib.sha256(REPORT.read_bytes()).hexdigest(),
                  hashlib.sha256(DOC.read_bytes()).hexdigest())
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, (hashlib.sha256(REPORT.read_bytes()).hexdigest(),
                                  hashlib.sha256(DOC.read_bytes()).hexdigest()))

    def test_top_level_and_identity_tamper(self):
        self.reject(lambda report: report.__setitem__("extra", True))
        self.reject(lambda report: report.__setitem__("accepted_identity_manifest_sha256", "0" * 64))

    def test_source_project_and_script_tamper(self):
        self.reject(lambda report: report.__setitem__("production_source_sha256", "0" * 64))
        self.reject(lambda report: report.__setitem__("project_sha256", "0" * 64))
        self.reject(lambda report: report.__setitem__("install_script_sha256", "0" * 64))

    def test_build_and_deployment_tamper(self):
        self.reject(lambda report: report["build_evidence"].__setitem__("sha256", "0" * 64))
        self.reject(lambda report: report["bundles"]["installed"]["macho_slice_minimum_versions"].__setitem__("arm64", "26.2"))
        self.reject(lambda report: report["bundles"]["staged"].__setitem__("info_plist_minimum_system_version", "26.2"))

    def test_universal_signature_and_export_tamper(self):
        self.reject(lambda report: report["bundles"]["installed"].__setitem__("strict_codesign", False))
        self.reject(lambda report: report["bundles"]["source"]["architectures"].pop())
        self.reject(lambda report: report["bundles"]["staged"]["effect_main_exports"].__setitem__("x86_64", 0))

    def test_new_and_old_inventory_tamper(self):
        self.reject(lambda report: report["bundles"]["installed"]["manifest"].pop())
        self.reject(lambda report: report["bundles"]["moved_old"]["manifest"].pop())
        self.reject(lambda report: report["bundles"]["pre_swap_original"].__setitem__("binary_sha256", "0" * 64))

    def test_identity_transition_tamper(self):
        self.reject(lambda report: report["identity_transition"]["changed_plugins"].append("OLMBlur"))
        self.reject(lambda report: report["identity_transition"]["changed_fields"]["ColorKeep"].pop())
        self.reject(lambda report: report["identity_transition"].__setitem__("other_nine_rows_exact", False))

    def test_atomic_transaction_and_rollback_tamper(self):
        self.reject(lambda report: report["transaction"].__setitem__("same_volume_atomic_bundle_exchange", False))
        self.reject(lambda report: report["boundaries"].__setitem__("same_volume_namespace_atomic_bundle_exchange", False))
        self.reject(lambda report: report["boundaries"].__setitem__("rollback_original_retained", False))
        self.reject(lambda report: report["boundaries"].__setitem__("manifest_and_bundle_single_atomic_transaction", True))

    def test_preflight_and_ae_tamper(self):
        self.reject(lambda report: report["stable_all10_preflight_collections"].pop())
        self.reject(lambda report: report["after_effects_processes_at_audit"].append(1234))
        self.reject(lambda report: report.__setitem__("installed_bundle_count", 2))

    def test_inventory_and_distribution_boundary_tamper(self):
        self.reject(lambda report: report["inventory_scope"]["not_claimed"].pop())
        self.reject(lambda report: report["boundaries"].__setitem__("developer_id_signed", True))
        self.reject(lambda report: report["boundaries"].__setitem__("ae_operation_performed", True))


if __name__ == "__main__":
    unittest.main()
