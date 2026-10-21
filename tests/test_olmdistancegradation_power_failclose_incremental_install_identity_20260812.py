from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmdistancegradation_power_failclose_incremental_install_20260812.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_power_failclose_incremental_install_identity_20260812.json"


def load():
    spec = importlib.util.spec_from_file_location("dg_power_install", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PowerFailcloseIncrementalInstallIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.report = json.loads(REPORT.read_text())

    def reject(self, mutation):
        report = copy.deepcopy(self.report)
        mutation(report)
        with self.assertRaises(AssertionError):
            self.module.validate(report)

    def test_validate(self):
        self.module.validate(copy.deepcopy(self.report))

    def test_source_tamper(self):
        self.reject(lambda report: report.__setitem__("production_source_sha256", "0" * 64))

    def test_install_script_tamper(self):
        self.reject(lambda report: report.__setitem__("install_script_sha256", "0" * 64))

    def test_codegen_tamper(self):
        self.reject(lambda report: report.__setitem__("universal_codegen_report_sha256", "0" * 64))

    def test_public_contract_tamper(self):
        self.reject(lambda report: report.__setitem__("public_contract_report_sha256", "0" * 64))

    def test_pre_manifest_tamper(self):
        self.reject(lambda report: report.__setitem__("pre_identity_manifest_sha256", "0" * 64))

    def test_post_manifest_tamper(self):
        self.reject(lambda report: report.__setitem__("accepted_identity_manifest_sha256", "0" * 64))

    def test_installed_hash_tamper(self):
        self.reject(lambda report: report["bundles"]["installed"].__setitem__("binary_sha256", "0" * 64))

    def test_backup_manifest_tamper(self):
        self.reject(lambda report: report["bundles"]["installed_backup"]["manifest"].pop())

    def test_moved_old_manifest_tamper(self):
        self.reject(lambda report: report["bundles"]["moved_old"]["manifest"].pop())

    def test_other_plugin_change_tamper(self):
        self.reject(lambda report: report["identity_transition"]["changed_plugins"].append("OLMBlur"))

    def test_changed_fields_tamper(self):
        self.reject(lambda report: report["identity_transition"]["distance_row_changed_fields"].pop())

    def test_historical_sequence_overclaim_tamper(self):
        self.reject(lambda report: report["observed_recovery"].__setitem__("historical_invocation_sequence_independently_reconstructed", True))

    def test_signature_kind_tamper(self):
        self.reject(lambda report: report["bundles"]["candidate"].__setitem__("signing_kind", "Developer ID"))


if __name__ == "__main__":
    unittest.main()
