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
TOOL = ROOT / "tools/emulation/audit_olm_hostless_batch4_transaction_readiness_20260813.py"
REPORT = ROOT / "refs/conformance/olm_hostless_batch4_transaction_readiness_20260813.json"
TOOL_SHA256 = "f0fbeb86113e4357b5595e5436e71910e8ac920cfa2029d3800f8dac722aec36"
REPORT_SHA256 = "45974ed0e98e227721ccbb014244c56e02fc9faa1f5eefdb82ce5e05a4156d2d"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("batch4_transaction_readiness", TOOL)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class Batch4TransactionReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(REPORT.read_text())

    def test_external_identities(self) -> None:
        self.assertEqual(sha256(TOOL), TOOL_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)

    def test_default_is_read_only_and_live(self) -> None:
        before = REPORT.read_bytes()
        subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, check=True)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_live_validation(self) -> None:
        audit.validate(copy.deepcopy(self.data))

    def test_recanonicalized_tamper_rejected(self) -> None:
        mutations = (
            lambda d: d.update(extra=True),
            lambda d: d["identities"]["installer"].update(sha256="0" * 64),
            lambda d: d["dry_run"].update(transaction_artifact_state="prepared"),
            lambda d: d.update(bound_bytes_before_after_exact=False),
            lambda d: d["sandbox_proof"].update(tests=4),
            lambda d: d["sandbox_proof"].update(third_swap_failure_restores_all_four_and_identity=False),
            lambda d: d["scope"].update(prepared=True),
            lambda d: d["scope"].update(after_effects_launched=True),
        )
        for mutation in mutations:
            changed = copy.deepcopy(self.data); mutation(changed)
            with self.subTest(changed=changed):
                with self.assertRaises((ValueError, RuntimeError)):
                    audit.validate(changed)


if __name__ == "__main__":
    unittest.main()
