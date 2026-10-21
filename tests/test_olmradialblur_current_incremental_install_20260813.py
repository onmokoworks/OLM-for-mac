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
AUDITOR = ROOT / "tools/emulation/audit_olmradialblur_current_incremental_install_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_current_incremental_install_20260813.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module():
    spec = importlib.util.spec_from_file_location("radial_current_install_audit", AUDITOR)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class RadialCurrentInstallAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = module()
        cls.report = json.loads(REPORT.read_text())

    def test_pinned_auditor_and_report(self):
        self.assertEqual(sha(AUDITOR), "b34c6cd045c1f61ca41f87958592945c438534e17196ded3a6db09c6d64eedb3")
        self.assertEqual(sha(REPORT), "fbe5d90d77fffad6db29a8c0811ffb9a958c93413f520c0e921c68ad1418f6fe")

    def test_default_read_only_live_audit(self):
        before = REPORT.read_bytes()
        subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, check=True)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_exact_installed_partition(self):
        self.mod.validate(self.report)
        self.assertEqual(self.report["identity_change"]["target_plugins"], ["OLMRadialBlur"])
        self.assertTrue(self.report["identity_change"]["other_nine_rows_exact"])

    def test_tamper_rejected(self):
        for mutation in (
            lambda d: d["installed"].__setitem__("new_sha256", "0" * 64),
            lambda d: d["installed"]["old_full_inventory_exact_copies"].pop(),
            lambda d: d["identity_change"].__setitem__("other_nine_rows_exact", False),
            lambda d: d["all10_preflight"].__setitem__("exact_bundles", 9),
            lambda d: d["scope"].__setitem__("after_effects_launched", True),
        ):
            altered = copy.deepcopy(self.report)
            mutation(altered)
            with self.assertRaises(ValueError):
                self.mod.validate(altered)

    def test_unknown_key_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["extra"] = True
        with self.assertRaises(ValueError):
            self.mod.validate(altered)


if __name__ == "__main__":
    unittest.main()
