from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260815.py"
READINESS = ROOT / "refs/conformance/olm_hostless_batch5_install_readiness_20260815.json"
AUDITOR = ROOT / "tools/emulation/audit_olm_hostless_batch5_transaction_20260815.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(module); return module


class Batch5TransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(INSTALLER, "batch5_test")

    def test_frozen_exact_five_and_superseded_distance_rejected(self):
        self.assertEqual(set(self.m.PLUGINS), {"OLMKiraKira", "OLMColorKey", "OLMToonDilate", "OLMDirectionalBlur", "OLMDistanceGradation"})
        self.assertEqual(self.m.PLUGINS["OLMDistanceGradation"]["new"], "9a97a076c118fd1015f40d922bf7f21be7a041f1f049a0e465cc0bc9cd1cd349")
        self.assertNotIn("d138c75d7dbd4c9ca3643988eebd9d53b7581947b6e22aa0f424de6433e2f206", {s["new"] for s in self.m.PLUGINS.values()})
        self.assertEqual(self.m.PLUGINS["OLMDistanceGradation"]["exports"], {"_EffectMain"})

    def test_readiness_is_exact_and_transaction_namespace_valid(self):
        self.assertEqual(hashlib.sha256(READINESS.read_bytes()).hexdigest(), self.m.READINESS_SHA256)
        report = json.loads(READINESS.read_text())
        self.assertEqual(set(report["plugins"]), set(self.m.PLUGINS))
        self.assertIn(self.m.artifact_state(), {"clean", "prepared", "installed"})
        self.assertEqual(self.m.ae_pids(), [])

    def test_read_only_transaction_auditor(self):
        before_identity = self.m.IDENTITY.read_bytes()
        before_state = self.m.artifact_state()
        audit = load(AUDITOR, "batch5_transaction_audit").audit()
        expected = {"clean": "PASS_BATCH5_CLEAN_READY_NO_MUTATION",
                    "prepared": "PASS_BATCH5_PREPARED_NO_INSTALL",
                    "installed": "PASS_BATCH5_INSTALLED_PENDING_AE"}[before_state]
        self.assertEqual(audit["status"], expected)
        self.assertEqual(self.m.IDENTITY.read_bytes(), before_identity)
        self.assertEqual(self.m.artifact_state(), before_state)

    def test_cli_is_explicit_and_identity_allowlist_is_narrow(self):
        source = INSTALLER.read_text(); tree = ast.parse(source)
        self.assertIn('group.add_argument("--prepare"', source)
        self.assertIn('group.add_argument("--install"', source)
        self.assertIn('group.add_argument("--rollback"', source)
        self.assertIn('for k in ("sha256", "source_bundle", "source_sha256")', source)
        self.assertIn('changed != allowed', source)
        self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name == "atomic_exchange" for n in ast.walk(tree)))
        self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name == "rollback_installed" for n in ast.walk(tree)))

    def test_ae_and_top_level_aerender_processes_are_both_rejected(self):
        replies = [subprocess.CompletedProcess([], 0, "2025\n", ""),
                   subprocess.CompletedProcess([], 0, "2026\n", "")]
        with mock.patch.object(self.m, "run", side_effect=replies) as called:
            self.assertEqual(self.m.ae_pids(), [2025, 2026])
        patterns = [call.args[2] for call in called.call_args_list]
        self.assertIn("MacOS/After Effects", patterns[0])
        self.assertIn("[^/]+/aerender", patterns[1])

    def test_manifest_source_sha_retains_installed_exact_semantics(self):
        source = INSTALLER.read_text()
        self.assertIn('rows[n]["source_sha256"] = s["new"]', source)
        self.assertNotIn('rows[n]["source_sha256"] = s["source_sha256"]', source)

    def test_transaction_artifacts_match_current_preinstall_state(self):
        state = self.m.artifact_state()
        self.assertIn(state, {"clean", "prepared", "installed"})
        self.assertEqual(self.m.PRE_IDENTITY.exists(), state in {"prepared", "installed"})
        self.assertEqual(self.m.POST_IDENTITY.exists(), state == "installed")
        self.assertEqual(self.m.PREPARED.exists(), state in {"prepared", "installed"})
        self.assertEqual(self.m.TRANSACTION.exists(), state == "installed")
        self.assertFalse(self.m.ROLLBACK.exists())
        for name in self.m.PLUGINS:
            for key in ("backup", "pre_swap"):
                self.assertEqual(self.m.paths(name)[key].exists(), state in {"prepared", "installed"}, (name, key))
            self.assertEqual(self.m.paths(name)["moved_old"].exists(), state == "installed", (name, "moved_old"))
            for key in ("failed_new", "stage"):
                self.assertFalse(self.m.paths(name)[key].exists(), (name, key))


if __name__ == "__main__": unittest.main()
