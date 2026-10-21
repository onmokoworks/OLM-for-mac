from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260813.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("olm_batch5_installer_test", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch5Installer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_installer()

    def test_transaction_is_installed_and_ae_is_absent(self):
        self.assertEqual(self.module.base.artifact_state(), "installed")
        self.assertEqual(self.module.base.ae_pids(), [])

    def test_candidate_installed_full_inventories(self):
        for name, item in self.module.PLUGINS.items():
            candidate = self.module.base.verify_bundle(name, item["candidate"], item["new"], require_macos11=True)
            installed = self.module.base.verify_bundle(name, self.module.paths(name)["installed"], item["new"], require_macos11=True)
            self.assertEqual(installed["manifest"], candidate["manifest"], name)

    def test_three_old_inventory_exact_copies(self):
        for name, item in self.module.PLUGINS.items():
            reference = self.module.base.verify_bundle(name, self.module.paths(name)["backup"], item["old"], require_macos11=False)
            for key in ("pre_swap", "moved_old"):
                copy = self.module.base.verify_bundle(name, self.module.paths(name)[key], item["old"], require_macos11=False)
                self.assertEqual(copy["manifest"], reference["manifest"], f"{name}/{key}")

    def test_identity_change_is_exactly_targets_and_timestamps(self):
        before = json.loads(self.module.PRE_IDENTITY.read_text())
        after = json.loads(self.module.IDENTITY.read_text())
        old = {row["plugin"]: row for row in before["plugins"]}
        new = {row["plugin"]: row for row in after["plugins"]}
        self.assertEqual({name for name in old if old[name] != new[name]}, set(self.module.PLUGINS))
        self.assertEqual({key for key in before if key != "plugins" and before[key] != after[key]}, {"accepted_at", "installed_after"})

    def test_transaction_exact_rows(self):
        data = json.loads(self.module.TRANSACTION.read_text())
        self.assertEqual(data["schema"], "olm.hostless-batch5-install-transaction/1")
        self.assertEqual(data["status"], "installed_pending_single_batched_ae_checkpoint")
        self.assertEqual(set(data["plugins"]), set(self.module.PLUGINS))
        for name, item in self.module.PLUGINS.items():
            self.assertEqual(data["plugins"][name], {"old": item["old"], "new": item["new"]})

    def test_default_command_is_read_only(self):
        identity_before = self.module.IDENTITY.read_bytes()
        transaction_before = self.module.TRANSACTION.read_bytes()
        result = subprocess.run([sys.executable, str(INSTALLER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "installed_pending_single_batched_ae_checkpoint_no_mutation")
        self.assertEqual(self.module.IDENTITY.read_bytes(), identity_before)
        self.assertEqual(self.module.TRANSACTION.read_bytes(), transaction_before)


if __name__ == "__main__":
    unittest.main()
