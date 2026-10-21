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
AUDITOR = ROOT / "tools/emulation/audit_olm_all10_current_source_installed_authority_20260813.py"
REPORT = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.md"
MATRIX = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
LEDGER = ROOT / "notes/CONFORMANCE_LEDGER.md"
AUDITOR_SHA256 = "265fbccfc875c96a9cff3149a8e1cf5eb070e6863f9f939fe2dfc30d14913b8b"
REPORT_SHA256 = "8138180651e805e352fdb6ffd2e91abd426803d7395d949a545e73c421f3e6f9"
MARKDOWN_SHA256 = "19d079e5d5fee7d1acbd96f812592d85e949c4d38273c7eab21e2cc1729ff81a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_auditor():
    spec = importlib.util.spec_from_file_location("all10_source_authority", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class All10CurrentSourceInstalledAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_auditor()
        cls.report = json.loads(REPORT.read_text())

    def test_default_is_read_only_and_live_exact(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS_ALL10_CURRENT_SOURCE_CANDIDATE_INSTALLED_EXACT_AE_DEFERRED", run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_all_ten_exact(self) -> None:
        self.assertEqual(len(self.report["plugins"]), 10)
        self.assertEqual(self.report["after_effects_processes"], [])
        for row in self.report["plugins"]:
            self.assertTrue(all(row["checks"].values()), row["plugin"])
            self.assertEqual(sorted(row["architectures"]), ["arm64", "x86_64"])

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(AUDITOR), AUDITOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_release_docs_keep_identity_only_boundary(self) -> None:
        matrix = MATRIX.read_text()
        ledger = LEDGER.read_text()
        ledger_words = " ".join(ledger.split())
        self.assertIn("olm_all10_current_source_installed_authority_20260813", matrix)
        self.assertIn("provenance/identity prerequisite", matrix)
        self.assertIn("not native-host pixel evidence", matrix)
        self.assertIn("all-10 current source-to-installed authority closure", ledger_words)
        self.assertIn("adds no numerical or Developer ID/notarization claim", ledger_words)

    def test_unknown_top_level_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)

    def test_unknown_row_and_check_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["plugins"][0]["extra"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["plugins"][0]["checks"]["extra"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)

    def test_failed_or_relabelled_claim_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["plugins"][0]["checks"]["source_sha_exact"] = False
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["scope"]["numerical_claim_added"] = True
        with self.assertRaises(RuntimeError):
            self.audit.validate_schema(changed)


if __name__ == "__main__":
    unittest.main()
