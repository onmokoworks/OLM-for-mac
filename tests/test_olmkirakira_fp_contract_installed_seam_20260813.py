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
GENERATOR = ROOT / "tools/emulation/test_olmkirakira_fp_contract_installed_seam_20260813.py"
REPORT = ROOT / "refs/conformance/olmkirakira_fp_contract_installed_seam_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "a419e6644a2ee6e3712139c11ec75be052d13812dfa9e8de4a384016b2ec6ab6"
REPORT_SHA256 = "1b49976eb359ec9e4bc0f99dd18452acf93bb84cde368eb2da1c01e9f008f7f4"
MARKDOWN_SHA256 = "ffcb92d38dbf92e54fd03fb51d923439a5af80d7e98c26962436131df97ee58d"
EXPECTED_CENSUS = {
    "m1_h7_r0": (3, 2),
    "m1_h7_r1": (9, 2),
    "m3_h50_r0": (5, 1),
    "m3_h50_r1": (6, 1),
    "m4_multiray": (5, 1),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("kira_installed_fp_seam", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class KiraInstalledFpContractSeamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load()
        cls.report = json.loads(REPORT.read_text())

    def reject(self, mutation) -> None:
        changed = copy.deepcopy(self.report)
        mutation(changed)
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)

    def test_default_live_read_only(self) -> None:
        before = (REPORT.read_bytes(), MARKDOWN.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(self.generator.STATUS, run.stdout)
        self.assertEqual(before, (REPORT.read_bytes(), MARKDOWN.read_bytes()))

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_exact_old_and_current_counts(self) -> None:
        self.assertEqual(
            self.report["summary"],
            {
                "row_count": 42,
                "old_oracle_exact": 37,
                "old_oracle_mismatched": 5,
                "current_oracle_exact": 42,
                "mismatch_keys": [[name, 32] for name in sorted(EXPECTED_CENSUS)],
            },
        )
        census = {
            row["tuple"]: (row["old_pf32_word_differences"], row["old_pf32_max_ulp"])
            for row in self.report["rows"] if not row["old_oracle_exact"]
        }
        self.assertEqual(census, EXPECTED_CENSUS)

    def test_recanonicalized_row_tamper_rejected(self) -> None:
        def mutate(report):
            report["rows"][0]["old_installed_sha256"] = "0" * 64
            report["rows_sha256"] = hashlib.sha256(
                json.dumps(report["rows"], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        self.reject(mutate)

    def test_mismatch_census_and_schema_tamper_rejected(self) -> None:
        self.reject(lambda report: report["rows"][2].__setitem__("old_pf32_max_ulp", 99))
        self.reject(lambda report: report["rows"][0].__setitem__("extra", True))
        self.reject(lambda report: report["summary"].__setitem__("old_oracle_exact", 38))

    def test_authority_and_scope_tamper_rejected(self) -> None:
        self.reject(lambda report: report["authorities"].__setitem__("old_binary", "0" * 64))
        self.reject(lambda report: report["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda report: report.__setitem__("extra", True))


if __name__ == "__main__":
    unittest.main()
