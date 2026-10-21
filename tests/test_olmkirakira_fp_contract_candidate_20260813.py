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
AUDITOR = ROOT / "tools/emulation/audit_olmkirakira_fp_contract_candidate_20260813.py"
HANDOFF = ROOT / "handoffs/olmkirakira_fp_contract_universal_candidate_20260813"
REPORT = HANDOFF / "build_identity.json"
MARKDOWN = HANDOFF / "README.md"
AUDITOR_SHA256 = "1c9dbc9b9b762f6c48715e76b817a9374cd4ff1cf8fe7d1e1c34005d7bb17b19"
REPORT_SHA256 = "9bf6570d46ad6cc5e181b28c21ff4077a127c4e850fe29f7a9ef892b2404b2d5"
MARKDOWN_SHA256 = "90148396acd9efac3b33a00ea994dfc6e96c9efec71ebf0a9918fc0551359ce4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("kira_fp_candidate_audit", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class KiraFpContractCandidateTest(unittest.TestCase):
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
        before = (REPORT.read_bytes(), MARKDOWN.read_bytes())
        run = subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(self.audit.STATUS, run.stdout)
        self.assertEqual(before, (REPORT.read_bytes(), MARKDOWN.read_bytes()))

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(AUDITOR), AUDITOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_public_replay_is_complete(self) -> None:
        replay = self.report["public_replay"]
        self.assertEqual((replay["positive_count"], replay["negative_count"], replay["request_control_count"]), (42, 765, 3))
        self.assertTrue(replay["all_positive_oracle_classic_smart_exact"])
        self.assertTrue(replay["all_negative_output_untouched_and_input_headers_immutable"])

    def test_authority_and_unknown_key_tamper(self) -> None:
        self.reject(lambda row: row["authorities"].__setitem__("production_source", "0" * 64))
        self.reject(lambda row: row.__setitem__("extra", True))

    def test_recanonicalized_replay_tamper(self) -> None:
        self.reject(lambda row: row["public_replay"]["digests"].__setitem__("positive_cells", "0" * 64))
        self.reject(lambda row: row["public_replay"].__setitem__("positive_count", 41))

    def test_inventory_export_and_signature_tamper(self) -> None:
        self.reject(lambda row: row["bundle_inventory"][0].__setitem__("sha256", "0" * 64))
        self.reject(lambda row: row["required_exports"]["arm64"].pop())
        self.reject(lambda row: row.__setitem__("strict_deep_adhoc_codesign", False))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda row: row["scope"].__setitem__("installed", True))
        self.reject(lambda row: row["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda row: row["scope"].__setitem__("developer_id_or_notarization", True))


if __name__ == "__main__":
    unittest.main()
