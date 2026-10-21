from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "tools/emulation/audit_olmkirakira_fp_contract_incremental_install_20260813.py"
REPORT = ROOT / "refs/conformance/olmkirakira_fp_contract_incremental_install_identity_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
AUDITOR_SHA256 = "59a99938c718d68a6183d6ca7b7d3d17db6e6803479b351212dd18111d20c70d"
REPORT_SHA256 = "6a568e19967a787c2d3a54c4884422c7a7d092f52d1d8b486dd86e6e9adc40d7"
MARKDOWN_SHA256 = "e11c9aa43e91308d0ed393e60c097fad3b38d33f37dd2881acca0f348d1e8cae"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("kira_fp_install_audit", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class KiraFpContractIncrementalInstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load()
        cls.report = json.loads(REPORT.read_text())

    def reject(self, mutation) -> None:
        changed = copy.deepcopy(self.report)
        mutation(changed)
        with self.assertRaises(RuntimeError):
            self.audit.validate(changed)

    def test_default_live_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(self.audit.STATUS, run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(AUDITOR), AUDITOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_kira_only_transition_and_rollback(self) -> None:
        transition = self.report["identity_transition"]
        self.assertEqual(transition["changed_plugins_and_fields"], {"OLMKiraKira": ["sha256", "source_bundle", "source_sha256"]})
        self.assertTrue(transition["other_nine_rows_exact"])
        self.assertEqual(self.report["old_rollback_copy_count"], 3)
        self.assertTrue(self.report["old_rollback_full_inventories_exact"])

    def test_inventory_and_identity_tamper_rejected(self) -> None:
        self.reject(lambda row: row["installed"]["inventory"][0].__setitem__("sha256", "0" * 64))
        self.reject(lambda row: row["identity_transition"].__setitem__("other_nine_rows_exact", False))
        self.reject(lambda row: row["authorities"].__setitem__("post_identity", "0" * 64))

    def test_rollback_and_transaction_tamper_rejected(self) -> None:
        self.reject(lambda row: row["old_copies"].pop("moved_old"))
        self.reject(lambda row: row["transaction"].__setitem__("post_identity_sha256", "0" * 64))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda row: row["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda row: row["scope"].__setitem__("developer_id_or_notarization", True))


if __name__ == "__main__":
    unittest.main()
