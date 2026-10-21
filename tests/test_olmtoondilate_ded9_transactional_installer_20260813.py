from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_olmtoondilate_ded9_incremental_20260813.py"
AUDITOR = ROOT / "tools/emulation/audit_olmtoondilate_ded9_transactional_install_readiness_20260813.py"
REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_transactional_install_readiness_20260813.json"
DOC = REPORT.with_suffix(".md")
SUPERSESSION_REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_transactional_install_readiness_supersession_20260813.json"
SUPERSESSION_DOC = SUPERSESSION_REPORT.with_suffix(".md")
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLED_BINARY = (
    Path.home()
    / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
)
EXPECTED_AUDITOR_SHA256 = "e75b5f5049c87bb7ff5f6f94c2007ad063afbf1f87a98e2f7dfeedeca1af91fe"
POST_IDENTITY_SHA256 = "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_bundle(path: Path, payload: bytes) -> None:
    binary = path / "Contents/MacOS/OLMToonDilate"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(payload)
    (path / "Contents/Info.plist").write_text("plist")


class ToonTransactionalInstaller(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if digest(AUDITOR) != EXPECTED_AUDITOR_SHA256:
            raise AssertionError("transaction readiness auditor identity drift")
        cls.installer = load(INSTALLER, "toon_ded9_installer_test")
        cls.auditor = load(AUDITOR, "toon_ded9_auditor_test")
        cls.post_installed = digest(IDENTITY) == POST_IDENTITY_SHA256
        cls.report_path = SUPERSESSION_REPORT if cls.post_installed else REPORT
        cls.doc_path = SUPERSESSION_DOC if cls.post_installed else DOC
        cls.report = json.loads(cls.report_path.read_text(encoding="utf-8"))

    def test_default_installer_is_read_only_and_prepare_ready(self):
        paths = (IDENTITY, INSTALLED_BINARY, REPORT, DOC, SUPERSESSION_REPORT, SUPERSESSION_DOC)
        before = {str(path): digest(path) for path in paths}
        result = subprocess.run(
            [sys.executable, str(INSTALLER)], cwd=ROOT, capture_output=True, text=True,
        )
        if self.post_installed:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("accepted pre-install identity manifest drift", result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            expected_status = (
                "dry_run_install_ready_prepared_no_mutation"
                if self.report["status"] == self.auditor.INSTALL_GO
                else "dry_run_prepare_ready_no_mutation"
            )
            self.assertEqual(json.loads(result.stdout)["status"], expected_status)
        self.assertEqual(before, {str(path): digest(path) for path in paths})

    def test_prepare_simulation_is_exact_idempotent_and_cleanup_safe(self):
        module = self.installer
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            handoff = base / "handoff"
            handoff.mkdir()
            installed = base / "MediaCore/OLMToonDilate.plugin"
            candidate = handoff / "candidate/OLMToonDilate.plugin"
            make_bundle(installed, b"old-binary")
            make_bundle(candidate, b"new-binary")
            identity = base / "identity.json"
            identity.write_text('{"pre":true}\n')
            old_hash = digest(installed / "Contents/MacOS/OLMToonDilate")
            new_hash = digest(candidate / "Contents/MacOS/OLMToonDilate")
            identity_hash = digest(identity)
            values = {
                "HANDOFF": handoff,
                "CANDIDATE": candidate,
                "INSTALLED": installed,
                "BACKUP": handoff / "installed_backup/OLMToonDilate.plugin",
                "PRE_SWAP": handoff / "pre_swap_original/OLMToonDilate.plugin",
                "MOVED_OLD": handoff / "moved_old/OLMToonDilate.plugin",
                "FAILED_NEW": handoff / "failed_new/OLMToonDilate.plugin",
                "STAGED": base / "MediaCore/.stage",
                "IDENTITY": identity,
                "PRE_IDENTITY": handoff / "identity_before.json",
                "POST_IDENTITY_COPY": handoff / "identity_after.json",
                "PREINSTALL": handoff / "preinstall.json",
                "TRANSACTION": handoff / "transaction.json",
                "EXPECTED_OLD": old_hash,
                "EXPECTED_NEW": new_hash,
                "EXPECTED_PRE_IDENTITY": identity_hash,
            }

            def verify(bundle: Path, expected: str, require_macos11: bool):
                self.assertEqual(digest(module.executable(bundle)), expected)
                return {"binary_sha256": expected, "manifest": module.inventory(bundle)}

            def copy_bundle(source: Path, destination: Path):
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination)

            with ExitStack() as stack:
                for name, value in values.items():
                    stack.enter_context(mock.patch.object(module, name, value))
                stack.enter_context(mock.patch.object(module, "verify_bundle", side_effect=verify))
                stack.enter_context(mock.patch.object(module, "copy_bundle", side_effect=copy_bundle))
                old_manifest = module.inventory(installed)
                new_manifest = module.inventory(candidate)
                preflight = {
                    "candidate": {"binary_sha256": new_hash, "manifest": new_manifest},
                    "installed_before": {"binary_sha256": old_hash, "manifest": old_manifest},
                }
                identity_before = identity.read_bytes()
                installed_before = copy.deepcopy(old_manifest)
                result = module.prepare_transaction(preflight, identity_before)
                self.assertEqual(result["status"], "prepared_install_ready_no_mediacore_or_identity_mutation")
                self.assertEqual(identity.read_bytes(), identity_before)
                self.assertEqual(module.inventory(installed), installed_before)
                self.assertEqual(module.artifact_state(), "prepared")
                self.assertTrue(module.validate_prepared(preflight)["old_bundle_full_inventories_exact"])
                module.cleanup_prepare_artifacts()
                self.assertEqual(module.artifact_state(), "clean")
                self.assertEqual(identity.read_bytes(), identity_before)
                self.assertEqual(module.inventory(installed), installed_before)

    def test_fault_after_swap_restores_old_bundle_and_exact_identity(self):
        module = self.installer
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            installed = base / "MediaCore/OLMToonDilate.plugin"
            staged = base / "MediaCore/.stage"
            make_bundle(installed, b"failed-new")
            make_bundle(staged, b"old-binary")
            identity = base / "identity.json"
            pre_identity = b'{"accepted":"before"}\n'
            identity.write_bytes(b'{"accepted":"failed-new"}\n')
            post_identity = base / "identity_after.json"
            post_identity.write_text("failed")
            old_hash = digest(staged / "Contents/MacOS/OLMToonDilate")

            def exchange(left: Path, right: Path):
                temp = left.with_name(".exchange-temp")
                os.rename(left, temp)
                os.rename(right, left)
                os.rename(temp, right)

            values = {
                "INSTALLED": installed,
                "STAGED": staged,
                "IDENTITY": identity,
                "POST_IDENTITY_COPY": post_identity,
                "EXPECTED_OLD": old_hash,
            }
            with ExitStack() as stack:
                for name, value in values.items():
                    stack.enter_context(mock.patch.object(module, name, value))
                stack.enter_context(mock.patch.object(module, "atomic_exchange", side_effect=exchange))
                module.restore_after_failure(pre_identity, swapped=True, old_moved=False)
            self.assertEqual(digest(installed / "Contents/MacOS/OLMToonDilate"), old_hash)
            self.assertEqual(identity.read_bytes(), pre_identity)
            self.assertFalse(staged.exists())
            self.assertFalse(post_identity.exists())

    def test_prepare_partial_failure_auto_cleans_and_preserves_targets(self):
        module = self.installer
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            handoff = base / "handoff"
            handoff.mkdir()
            installed = base / "MediaCore/OLMToonDilate.plugin"
            candidate = handoff / "candidate/OLMToonDilate.plugin"
            make_bundle(installed, b"old-binary")
            make_bundle(candidate, b"new-binary")
            identity = base / "identity.json"
            identity.write_bytes(b'{"pre":true}\n')
            old_hash = digest(module.executable(installed))
            new_hash = digest(module.executable(candidate))
            identity_hash = digest(identity)
            old_manifest = module.inventory(installed)
            new_manifest = module.inventory(candidate)
            preflight = {
                "transaction_artifact_state": "clean",
                "candidate": {"binary_sha256": new_hash, "manifest": new_manifest},
                "installed_before": {"binary_sha256": old_hash, "manifest": old_manifest},
            }
            values = {
                "HANDOFF": handoff,
                "CANDIDATE": candidate,
                "INSTALLED": installed,
                "BACKUP": handoff / "installed_backup/OLMToonDilate.plugin",
                "PRE_SWAP": handoff / "pre_swap_original/OLMToonDilate.plugin",
                "MOVED_OLD": handoff / "moved_old/OLMToonDilate.plugin",
                "FAILED_NEW": handoff / "failed_new/OLMToonDilate.plugin",
                "STAGED": base / "MediaCore/.stage",
                "IDENTITY": identity,
                "PRE_IDENTITY": handoff / "identity_before.json",
                "POST_IDENTITY_COPY": handoff / "identity_after.json",
                "PREINSTALL": handoff / "preinstall.json",
                "TRANSACTION": handoff / "transaction.json",
                "EXPECTED_OLD": old_hash,
                "EXPECTED_NEW": new_hash,
                "EXPECTED_PRE_IDENTITY": identity_hash,
            }

            def verify(bundle: Path, expected: str, require_macos11: bool):
                self.assertEqual(digest(module.executable(bundle)), expected)
                return {"binary_sha256": expected, "manifest": module.inventory(bundle)}

            calls = 0

            def fail_second_copy(source: Path, destination: Path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("injected second-backup failure")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination)

            identity_before = identity.read_bytes()
            installed_before = copy.deepcopy(old_manifest)
            with ExitStack() as stack:
                for name, value in values.items():
                    stack.enter_context(mock.patch.object(module, name, value))
                stack.enter_context(mock.patch.object(module, "verify_bundle", side_effect=verify))
                stack.enter_context(mock.patch.object(module, "copy_bundle", side_effect=fail_second_copy))
                stack.enter_context(mock.patch.object(module, "collect_preflight", return_value=preflight))
                stack.enter_context(mock.patch.object(sys, "argv", [str(INSTALLER), "--prepare"]))
                with self.assertRaisesRegex(RuntimeError, "injected second-backup failure"):
                    module.main()
                self.assertEqual(module.artifact_state(), "clean")
            self.assertEqual(identity.read_bytes(), identity_before)
            self.assertEqual(module.inventory(installed), installed_before)

    def test_canonical_readiness_report_and_default_auditor_are_read_only(self):
        expected = self.auditor.generate()
        self.assertEqual(self.report, expected)
        if self.post_installed:
            self.assertEqual(self.report["status"], self.auditor.SUPERSEDED)
            self.assertFalse(
                self.report["historical_prepared_readiness"]["treated_as_live_current_state"],
            )
        else:
            self.assertIn(self.report["status"], (self.auditor.BUILD_GO, self.auditor.INSTALL_GO))
        before = tuple(digest(path) for path in (
            REPORT, DOC, SUPERSESSION_REPORT, SUPERSESSION_DOC, IDENTITY, INSTALLED_BINARY,
        ))
        result = subprocess.run(
            [sys.executable, str(AUDITOR)], cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, tuple(digest(path) for path in (
            REPORT, DOC, SUPERSESSION_REPORT, SUPERSESSION_DOC, IDENTITY, INSTALLED_BINARY,
        )))

    def test_readiness_report_tamper_rejected(self):
        original_generate = self.auditor.generate
        expected = original_generate()
        self.auditor.generate = lambda: copy.deepcopy(expected)
        try:
            mutations = (
                (
                    lambda row: row["historical_prepared_readiness"].__setitem__("sha256", "0" * 64),
                    lambda row: row["current_post_install_authority"].__setitem__("report_sha256", "0" * 64),
                    lambda row: row["historical_prepared_readiness"].__setitem__("treated_as_live_current_state", True),
                    lambda row: row.__setitem__("install_operation_performed", True),
                )
                if self.post_installed else (
                    lambda row: row.__setitem__("installer_sha256", "0" * 64),
                    lambda row: row["prospective_identity_transition"]["changed_plugins"].append("OLMBlur"),
                    lambda row: row["transaction_plan"].__setitem__("failure_restores_exact_pre_identity_bytes", False),
                    lambda row: row.__setitem__("install_flag_executed", True),
                )
            )
            for mutation in mutations:
                tampered = copy.deepcopy(self.report)
                mutation(tampered)
                with self.assertRaises(AssertionError):
                    self.auditor.validate(tampered)
        finally:
            self.auditor.generate = original_generate


if __name__ == "__main__":
    unittest.main()
