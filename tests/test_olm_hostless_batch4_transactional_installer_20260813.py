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
INSTALLER = ROOT / "scripts/install_olm_hostless_batch4_20260813.py"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLER_SHA256 = "9c585ad852e114bff25bc144d32fd79e442df7cc507e20f871350526e40d678f"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("batch4_installer", INSTALLER)
assert spec and spec.loader
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def make_bundle(path: Path, name: str, payload: bytes) -> None:
    binary = path / "Contents/MacOS" / name
    binary.parent.mkdir(parents=True)
    binary.write_bytes(payload)
    (path / "Contents/Info.plist").write_text("plist")


def swap(left: Path, right: Path) -> None:
    temporary = left.with_name(left.name + ".swap")
    os.rename(left, temporary)
    os.rename(right, left)
    os.rename(temporary, right)


class Batch4TransactionalInstaller(unittest.TestCase):
    def test_external_identity_and_default_dry_run_are_read_only(self) -> None:
        self.assertEqual(sha256(INSTALLER), INSTALLER_SHA256)
        watched = [IDENTITY]
        for name, spec_row in installer.PLUGINS.items():
            watched.extend((installer.executable(spec_row["candidate"], name), installer.executable(installer.paths(name)["installed"], name)))
        before = {str(path): sha256(path) for path in watched}
        state = installer.artifact_state()
        result = subprocess.run([sys.executable, str(INSTALLER)], cwd=ROOT, check=True, capture_output=True, text=True)
        expected = {"clean": "dry_run_prepare_ready_no_mutation",
                    "prepared": "dry_run_install_ready_no_mutation",
                    "installed": "installed_pending_batched_ae_smoke_no_mutation"}[state]
        self.assertEqual(json.loads(result.stdout)["status"], expected)
        self.assertEqual(before, {str(path): sha256(path) for path in watched})

    def sandbox(self, base: Path):
        handoff = base / "handoff"
        media = base / "MediaCore"
        identity = base / "identity.json"
        identity.write_text('{"plugins":[]}\n')
        specs = {}
        for index, name in enumerate(installer.PLUGINS):
            candidate = base / "candidates" / f"{name}.plugin"
            installed = media / f"{name}.plugin"
            make_bundle(candidate, name, f"new-{index}".encode())
            make_bundle(installed, name, f"old-{index}".encode())
            specs[name] = {"candidate": candidate, "old": sha256(installer.executable(installed, name)),
                           "new": sha256(installer.executable(candidate, name))}
        values = {
            "HANDOFF": handoff, "MEDIA_CORE": media, "IDENTITY": identity,
            "PRE_IDENTITY": handoff / "identity_before.json", "POST_IDENTITY": handoff / "identity_after.json",
            "PREPARED": handoff / "prepared.json", "TRANSACTION": handoff / "transaction.json",
            "PLUGINS": specs,
            "EXPECTED_PRE_IDENTITY": sha256(identity),
        }
        return values, specs, identity

    @staticmethod
    def fake_verify(name: str, bundle: Path, expected: str, *, require_macos11: bool):
        if sha256(installer.executable(bundle, name)) != expected:
            raise RuntimeError("fake binary mismatch")
        return {"binary_sha256": expected, "manifest": installer.inventory(bundle)}

    @staticmethod
    def fake_copy(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)

    def test_prepare_four_plugins_is_exact_and_media_identity_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            values, specs, identity = self.sandbox(Path(raw))
            with ExitStack() as stack:
                for name, value in values.items(): stack.enter_context(mock.patch.object(installer, name, value))
                stack.enter_context(mock.patch.object(installer, "verify_bundle", side_effect=self.fake_verify))
                stack.enter_context(mock.patch.object(installer, "copy_bundle", side_effect=self.fake_copy))
                preflight = {"plugins": {name: {"candidate": self.fake_verify(name, row["candidate"], row["new"], require_macos11=True),
                                                 "installed_before": self.fake_verify(name, installer.paths(name)["installed"], row["old"], require_macos11=False)}
                                         for name, row in specs.items()}}
                identity_before = identity.read_bytes()
                installed_before = {name: installer.inventory(installer.paths(name)["installed"]) for name in specs}
                result = installer.prepare_transaction(preflight, identity_before)
                self.assertEqual(result["candidate_count"], 4)
                self.assertEqual(installer.artifact_state(), "prepared")
                self.assertTrue(installer.validate_prepared(preflight)["old_bundle_full_inventories_exact"])
                self.assertEqual(identity.read_bytes(), identity_before)
                self.assertEqual(installed_before, {name: installer.inventory(installer.paths(name)["installed"]) for name in specs})

    def test_prepare_second_plugin_failure_cleans_everything(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            values, specs, identity = self.sandbox(Path(raw))
            calls = 0
            def failing_copy(source: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 3: raise RuntimeError("injected backup failure")
                self.fake_copy(source, destination)
            with ExitStack() as stack:
                for name, value in values.items(): stack.enter_context(mock.patch.object(installer, name, value))
                stack.enter_context(mock.patch.object(installer, "verify_bundle", side_effect=self.fake_verify))
                stack.enter_context(mock.patch.object(installer, "copy_bundle", side_effect=failing_copy))
                preflight = {"plugins": {name: {"candidate": self.fake_verify(name, row["candidate"], row["new"], require_macos11=True),
                                                 "installed_before": self.fake_verify(name, installer.paths(name)["installed"], row["old"], require_macos11=False)}
                                         for name, row in specs.items()}}
                before = identity.read_bytes()
                with self.assertRaisesRegex(RuntimeError, "injected backup failure"):
                    installer.prepare_transaction(preflight, before)
                self.assertEqual(installer.artifact_state(), "clean")
                self.assertEqual(identity.read_bytes(), before)

    def test_failure_after_third_swap_restores_all_four_and_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            values, specs, identity = self.sandbox(Path(raw))
            with ExitStack() as stack:
                for name, value in values.items(): stack.enter_context(mock.patch.object(installer, name, value))
                stack.enter_context(mock.patch.object(installer, "verify_bundle", side_effect=self.fake_verify))
                stack.enter_context(mock.patch.object(installer, "copy_bundle", side_effect=self.fake_copy))
                stack.enter_context(mock.patch.object(installer, "atomic_exchange", side_effect=swap))
                stack.enter_context(mock.patch.object(installer, "ae_pids", return_value=[]))
                preflight = {"plugins": {name: {"candidate": self.fake_verify(name, row["candidate"], row["new"], require_macos11=True),
                                                 "installed_before": self.fake_verify(name, installer.paths(name)["installed"], row["old"], require_macos11=False)}
                                         for name, row in specs.items()}}
                identity_before = identity.read_bytes()
                installer.prepare_transaction(preflight, identity_before)
                original_exchange = installer.atomic_exchange
                calls = 0
                def fail_third(left: Path, right: Path) -> None:
                    nonlocal calls
                    calls += 1
                    if calls == 3: raise RuntimeError("injected third swap failure")
                    swap(left, right)
                with mock.patch.object(installer, "atomic_exchange", side_effect=fail_third):
                    with self.assertRaisesRegex(RuntimeError, "injected third swap failure"):
                        installer.install(preflight)
                for name, row in specs.items():
                    self.assertEqual(sha256(installer.executable(installer.paths(name)["installed"], name)), row["old"])
                self.assertEqual(identity.read_bytes(), identity_before)

    def test_reject_partial_transaction_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            values, _, _ = self.sandbox(Path(raw))
            with ExitStack() as stack:
                for name, value in values.items(): stack.enter_context(mock.patch.object(installer, name, value))
                installer.PRE_IDENTITY.parent.mkdir(parents=True)
                installer.PRE_IDENTITY.write_text("partial")
                self.assertEqual(installer.artifact_state(), "partial")


if __name__ == "__main__":
    unittest.main()
