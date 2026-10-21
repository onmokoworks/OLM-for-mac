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
INSTALLER = ROOT / "scripts/install_olmsmoother2_pf8_pf16_pf32_incremental_20260814.py"
AUDITOR = ROOT / "tools/emulation/audit_olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.py"
REPORT = ROOT / "refs/conformance/olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.json"
DOC = REPORT.with_suffix(".md")
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother2.plugin/Contents/MacOS/OLMSmoother2"
EXPECTED_INSTALLER = "b85a68eb800491cef972c2aa149e6e89fda32a9596d97d03784b3e2fb0e263cb"
EXPECTED_AUDITOR = "51265f3a90b408e95d76e607edf980fd4ca5888cd0bbc25a7118c7baa1fc5647"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Smoother2TransactionalInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(INSTALLER) != EXPECTED_INSTALLER or sha(AUDITOR) != EXPECTED_AUDITOR:
            raise AssertionError("installer/auditor identity drift")
        cls.installer = load(INSTALLER, "smoother2_installer_test")
        cls.auditor = load(AUDITOR, "smoother2_auditor_test")

    def test_default_installer_is_read_only(self):
        paths = [IDENTITY, INSTALLED]
        for optional in (REPORT, DOC, *self.installer.prepared_artifacts(), *self.installer.post_artifacts()):
            if optional.exists() and optional.is_file():
                paths.append(optional)
        before = {str(path): sha(path) for path in paths}
        state_before = self.installer.artifact_state()
        result = subprocess.run([sys.executable, str(INSTALLER)], cwd=ROOT, capture_output=True, text=True)
        if sha(IDENTITY) == self.installer.EXPECTED_PRE_IDENTITY:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["transaction_artifact_state"], state_before)
            self.assertIn(payload["status"], {"dry_run_prepare_ready_no_mutation", "dry_run_install_ready_prepared_no_mutation"})
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("accepted pre-install identity manifest drift", result.stderr)
        self.assertEqual(before, {str(path): sha(path) for path in paths})

    def test_identity_projection_changes_only_smoother2_and_timestamps(self):
        source = self.installer.PRE_IDENTITY if self.installer.PRE_IDENTITY.exists() else IDENTITY
        before = json.loads(source.read_text())
        after = self.installer.identity_projection(before, "test-time")
        change = self.installer.transition(before, after)
        self.assertEqual(change["changed_plugins"], ["OLMSmoother2"])
        self.assertEqual(change["changed_fields"], {"OLMSmoother2": ["sha256", "source_bundle", "source_sha256"]})
        self.assertEqual(change["top_level_changed_fields"], ["accepted_at", "installed_after"])
        self.assertTrue(change["other_nine_rows_exact"])

    def test_live_audit_and_saved_report_are_exact(self):
        saved = json.loads(REPORT.read_text())
        self.auditor.validate(saved)
        self.assertEqual(saved, self.auditor.generate())
        self.assertEqual(saved["after_effects_processes"], [])

    def test_recanonicalized_report_tamper_fails_closed(self):
        saved = json.loads(REPORT.read_text())
        attacks = []
        unknown = copy.deepcopy(saved)
        unknown["extra"] = True
        attacks.append(unknown)
        changed_candidate = copy.deepcopy(saved)
        changed_candidate["candidate"]["binary_sha256"] = "0" * 64
        attacks.append(changed_candidate)
        changed_claim = copy.deepcopy(saved)
        changed_claim["claims_not_made"][0] = "AE was launched"
        attacks.append(changed_claim)
        changed_transition = copy.deepcopy(saved)
        changed_transition["identity_transition"]["changed_plugins"] = ["OLMSmoother", "OLMSmoother2"]
        attacks.append(changed_transition)
        for attack in attacks:
            with self.assertRaises(RuntimeError):
                self.auditor.validate(attack)

    def test_release_docs_state_install_and_defer_ae(self):
        docs = [
            ROOT / "notes/CONFORMANCE_LEDGER.md",
            ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md",
            ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md",
            ROOT / "refs/conformance/olmsmoother2_completion_matrix_20260805.md",
        ]
        for path in docs:
            text = path.read_text()
            self.assertIn("c8ea1f0e", text, path)
            self.assertIn("7212ca5c", text, path)
        combined = "\n".join(path.read_text() for path in docs)
        self.assertIn("AE", combined)
        self.assertIn("defer", combined.lower())
        status = json.loads((ROOT / "refs/conformance/olm_release_gate_status_20260806.json").read_text())
        self.assertEqual(status["status"], "release_gate_pending_or_invalid")
        self.assertFalse(status["releasable"])

    def test_bundle_and_identity_chain_are_exact(self):
        if sha(IDENTITY) == self.installer.EXPECTED_PRE_IDENTITY:
            self.assertEqual(sha(INSTALLED), self.installer.EXPECTED_OLD)
        else:
            self.assertEqual(sha(INSTALLED), self.installer.EXPECTED_NEW)
            self.assertEqual(sha(IDENTITY), self.auditor.POST_IDENTITY_SHA256)
            for bundle in (self.installer.BACKUP, self.installer.PRE_SWAP, self.installer.MOVED_OLD):
                self.assertEqual(sha(self.installer.executable(bundle)), self.installer.EXPECTED_OLD)
        self.assertEqual(self.installer.ae_pids(), [])


if __name__ == "__main__":
    unittest.main()
