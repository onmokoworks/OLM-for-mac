from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_olmradialblur_worldsuite_lifecycle_20260814.py"
INSTALLER_SHA256 = "8bdd3e750d57011d1d45541e8e58ea9618222ce2a42d0201115c68fb3b08d393"
SPEC = importlib.util.spec_from_file_location("radial_worldsuite_installer", INSTALLER)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class RadialWorldSuiteInstallerTest(unittest.TestCase):
    def test_installer_identity(self) -> None:
        if INSTALLER_SHA256 != "PENDING":
            self.assertEqual(hashlib.sha256(INSTALLER.read_bytes()).hexdigest(), INSTALLER_SHA256)

    def test_authorities(self) -> None:
        live_identity = MOD.impl.base.sha256(MOD.impl.IDENTITY)
        post_identity = MOD.impl.base.sha256(MOD.impl.POST_IDENTITY)
        self.assertIn(live_identity, {MOD.impl.EXPECTED_PRE_IDENTITY, post_identity})
        authority = MOD.impl.authority()
        self.assertEqual(authority["source_sha256"], MOD.impl.SOURCE_SHA256)
        self.assertEqual(authority["candidate"]["binary_sha256"], MOD.impl.NEW_SHA256)

    def test_dry_run_is_non_mutating(self) -> None:
        identity_before = MOD.impl.base.sha256(MOD.impl.IDENTITY)
        installed_before = MOD.impl.base.inventory(MOD.paths()["installed"])
        ran = subprocess.run([sys.executable, str(INSTALLER)], cwd=ROOT, check=True,
                             capture_output=True, text=True)
        status = json.loads(ran.stdout)["status"]
        self.assertIn(status, {"dry_run_prepare_ready_no_mutation",
                               "dry_run_install_ready_no_mutation",
                               "installed_pending_deferred_batched_ae_checkpoint_no_mutation"})
        self.assertEqual(MOD.impl.base.sha256(MOD.impl.IDENTITY), identity_before)
        self.assertEqual(MOD.impl.base.inventory(MOD.paths()["installed"]), installed_before)

    def test_paths_are_exact_and_bounded(self) -> None:
        paths = MOD.paths()
        self.assertEqual(set(paths), {"installed", "backup", "pre_swap", "moved_old",
                                     "failed_new", "stage"})
        self.assertEqual(paths["installed"].name, "OLMRadialBlur.plugin")
        self.assertEqual(paths["stage"].name, ".OLMRadialBlur.worldsuite-stage-20260814")


if __name__ == "__main__":
    unittest.main()
