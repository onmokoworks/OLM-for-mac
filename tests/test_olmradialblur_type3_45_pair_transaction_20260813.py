from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/install_olmradialblur_type3_45_pair_20260813.py"
SPEC = importlib.util.spec_from_file_location("type3_45_pair_install", PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
installer = module.installer


class RadialType345PairTransactionTest(unittest.TestCase):
    def preflight(self):
        if installer.artifact_state() == "installed":
            return json.loads(installer.PREPARED.read_text())["preflight"]
        return installer.collect_preflight()

    def test_authority_and_live_old(self):
        preflight = self.preflight()
        self.assertEqual(preflight["plugin"]["source_sha256"], installer.SOURCE_SHA256)
        self.assertEqual(preflight["plugin"]["candidate"]["binary_sha256"], installer.NEW_SHA256)
        self.assertEqual(preflight["plugin"]["installed_before"]["binary_sha256"], installer.OLD_SHA256)

    def test_default_is_read_only(self):
        before_identity = installer.IDENTITY.read_bytes()
        before_inventory = installer.base.inventory(installer.paths()["installed"])
        result = subprocess.run([sys.executable, str(PATH)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(json.loads(result.stdout)["status"], {
            "dry_run_prepare_ready_no_mutation",
            "dry_run_install_ready_no_mutation",
            "installed_pending_deferred_batched_ae_checkpoint_no_mutation",
        })
        self.assertEqual(installer.IDENTITY.read_bytes(), before_identity)
        self.assertEqual(installer.base.inventory(installer.paths()["installed"]), before_inventory)

    def test_no_ae(self):
        self.assertEqual(installer.base.ae_pids(), [])


if __name__ == "__main__":
    unittest.main()
