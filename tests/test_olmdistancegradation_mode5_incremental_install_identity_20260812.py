import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmdistancegradation_mode5_incremental_install_20260812.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_mode5_incremental_install_identity_20260812.json"


def load():
    spec = importlib.util.spec_from_file_location("dg_mode5_install", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IncrementalInstallIdentity(unittest.TestCase):
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

    def test_backup_manifest_tamper(self):
        self.reject(lambda report: report["bundles"]["backup"]["manifest"].pop())

    def test_installed_hash_tamper(self):
        self.reject(lambda report: report["bundles"]["installed"].__setitem__("binary_sha256", "0" * 64))

    def test_other_plugin_change_tamper(self):
        self.reject(lambda report: report["identity_transition"]["changed_plugins"].append("OLMBlur"))

    def test_rollback_tamper(self):
        self.reject(lambda report: report["transaction"].__setitem__("rollback_bundle_retained", False))


if __name__ == "__main__":
    unittest.main()
