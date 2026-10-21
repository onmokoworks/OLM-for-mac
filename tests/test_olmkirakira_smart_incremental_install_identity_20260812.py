import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olmkirakira_smart_incremental_install_identity_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_smart_incremental_install_identity_20260812.json"
SCRIPT_SHA256 = "14aa116e59062a43e93f62e68189a7231d0d7a635c0bec1559032ce890083fac"


def load():
    spec = importlib.util.spec_from_file_location("kira_smart_install_identity", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class KiraSmartIncrementalInstallIdentity(unittest.TestCase):
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
        self.assertEqual(hashlib.sha256(SCRIPT.read_bytes()).hexdigest(), SCRIPT_SHA256)
        self.module.validate(copy.deepcopy(self.report))

    def test_default_cli_is_read_only(self):
        doc = REPORT.with_suffix(".md")
        before = (REPORT.read_bytes(), doc.read_bytes())
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS_OLMKIRAKIRA_SMART_INCREMENTAL_INSTALL_IDENTITY_20260812", result.stdout)
        self.assertEqual((REPORT.read_bytes(), doc.read_bytes()), before)

    def test_top_level_key_tamper(self):
        self.reject(lambda report: report.__setitem__("extra", True))

    def test_source_and_project_tamper(self):
        self.reject(lambda report: report.__setitem__("production_source_sha256", "0" * 64))
        self.reject(lambda report: report.__setitem__("project_sha256", "0" * 64))
        self.reject(lambda report: report.__setitem__("highlight_header_sha256", "0" * 64))
        self.reject(lambda report: report.__setitem__("workspace_dependency_manifest_sha256", "0" * 64))

    def test_build_log_and_arch_evidence_tamper(self):
        self.reject(lambda report: report["build_evidence"].__setitem__("sha256", "0" * 64))
        self.reject(lambda report: report["build_evidence"]["linked_architectures"].pop())
        self.reject(lambda report: report["build_evidence"].__setitem__("warning_marker_line_count", 0))
        self.reject(lambda report: report["build_evidence"].__setitem__("error_marker_line_count", 1))
        self.reject(lambda report: report["build_evidence"].__setitem__("project_macosx_deployment_target_11_exact_occurrences", 1))

    def test_canonical_inventory_and_binary_tamper(self):
        self.reject(lambda report: report["bundles"]["staged"]["manifest"].pop())
        self.reject(lambda report: report["bundles"]["installed"].__setitem__("binary_sha256", "0" * 64))

    def test_retained_inventory_tamper(self):
        self.reject(lambda report: report["bundles"]["retained_installed_backup"]["manifest"].pop())
        self.reject(lambda report: report["bundles"]["pre_swap_original"].__setitem__("binary_sha256", "0" * 64))

    def test_deployment_codesign_and_universal_tamper(self):
        self.reject(lambda report: report["bundles"]["source"]["deployment"]["macho_slice_minimum_versions"].__setitem__("arm64", "12.0"))
        self.reject(lambda report: report["bundles"]["installed"].__setitem__("strict_codesign", False))
        self.reject(lambda report: report["bundles"]["staged"].__setitem__("universal_exact", False))

    def test_identity_manifest_and_transition_tamper(self):
        self.reject(lambda report: report.__setitem__("pre_identity_manifest_sha256", "0" * 64))
        self.reject(lambda report: report["identity_transition"]["changed_plugins"].append("OLMBlur"))
        self.reject(lambda report: report["identity_transition"]["top_level_changed_fields"].pop())
        self.reject(lambda report: report["identity_transition"]["unchanged_plugins"].pop())

    def test_observation_wording_boundary_tamper(self):
        self.reject(lambda report: report["observed_retention"].__setitem__("transaction_method_or_order_inferred", True))
        self.reject(lambda report: report["inventory_scope"]["not_claimed"].pop())

    def test_generated_at_tamper(self):
        self.reject(lambda report: report.__setitem__("generated_at", "1999-01-01T00:00:00+00:00"))

    def test_markdown_tamper(self):
        original_doc = self.module.DOC
        with tempfile.TemporaryDirectory() as directory:
            self.module.DOC = Path(directory) / "report.md"
            self.module.DOC.write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                self.module.validate(copy.deepcopy(self.report))
        self.module.DOC = original_doc

    def test_smoke_artifact_and_all10_tamper(self):
        self.reject(lambda report: report["retained_post_install_ae_smoke"].__setitem__("report_sha256", "0" * 64))
        self.reject(lambda report: report["retained_post_install_ae_smoke"].__setitem__("plugin_count", 9))

    def test_smoke_kira_claim_boundary_tamper(self):
        self.reject(lambda report: report["retained_post_install_ae_smoke"]["kira"].__setitem__("effect_enabled_numerical_render_attempted", True))
        self.reject(lambda report: report["retained_post_install_ae_smoke"]["kira"].__setitem__("numerical_render_supported", True))


if __name__ == "__main__":
    unittest.main()
