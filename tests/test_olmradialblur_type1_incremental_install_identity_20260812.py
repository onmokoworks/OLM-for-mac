import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmradialblur_type1_incremental_install_identity_20260812.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_incremental_install_identity_20260812.json"


def load():
    spec = importlib.util.spec_from_file_location("radial_type1_install_identity", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RadialType1IncrementalInstallIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def reject(self, mutation):
        report = copy.deepcopy(self.report)
        mutation(report)
        with self.assertRaises(AssertionError):
            self.module.validate(report)

    def test_validate(self):
        self.module.validate(copy.deepcopy(self.report))

    def test_default_cli_is_read_only_validation(self):
        doc = REPORT.with_suffix(".md")
        before = (REPORT.read_bytes(), doc.read_bytes())
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS_OLMRADIALBLUR_TYPE1_INCREMENTAL_INSTALL_IDENTITY_20260812", result.stdout)
        self.assertEqual((REPORT.read_bytes(), doc.read_bytes()), before)

    def test_source_hash_tamper(self):
        self.reject(lambda report: report.__setitem__("production_source_sha256", "0" * 64))

    def test_core_header_hash_tamper(self):
        self.reject(lambda report: report.__setitem__("core_header_sha256", "0" * 64))

    def test_installed_hash_tamper(self):
        self.reject(
            lambda report: report["bundles"]["installed"].__setitem__("binary_sha256", "0" * 64)
        )

    def test_staged_inventory_tamper(self):
        self.reject(lambda report: report["bundles"]["staged"]["manifest"].pop())

    def test_backup_inventory_tamper(self):
        self.reject(lambda report: report["bundles"]["backup"]["manifest"].pop())

    def test_bundle_count_tamper(self):
        self.reject(lambda report: report.__setitem__("installed_bundle_count", 2))

    def test_other_plugin_change_tamper(self):
        self.reject(
            lambda report: report["identity_transition"]["changed_plugins"].append("OLMBlur")
        )

    def test_changed_fields_tamper(self):
        self.reject(
            lambda report: report["identity_transition"]["changed_fields"]["OLMRadialBlur"].append(
                "codesign_exact"
            )
        )

    def test_rollback_tamper(self):
        self.reject(
            lambda report: report["transaction"].__setitem__("rollback_bundle_retained", False)
        )


if __name__ == "__main__":
    unittest.main()
