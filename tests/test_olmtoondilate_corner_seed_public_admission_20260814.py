from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/emulation/test_olmtoondilate_corner_seed_public_candidate_20260814.py"
REPORT = ROOT / "refs/conformance/olmtoondilate_corner_seed_public_candidate_20260814.json"
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
EXPECTED_IDS = ["PF8_corner_seed", "PF16_corner_seed", "PF32_corner_seed"]


class ToonCornerSeedAdmission(unittest.TestCase):
    def test_checked_report_is_exact_and_production_bound(self):
        value = json.loads(REPORT.read_text())
        self.assertEqual(value["status"], "PASS_EXACT3_PAIRED_PUBLIC_OWNER")
        self.assertTrue(all(value["gates"].values()))
        self.assertEqual([row["id"] for row in value["paired_cells"]], EXPECTED_IDS)
        source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(value["identities"]["isolated_candidate_source_sha256"], source_sha)
        self.assertEqual(value["identities"]["production_source_current_sha256"], source_sha)
        self.assertEqual(value["identities"]["production_source_pre_admission_sha256"],
                         "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b")
        for row in value["paired_cells"]:
            self.assertTrue(row["windows_exported_smart_raw_exact"])
            self.assertTrue(row["mac_public_effectmain_raw_exact"])
            self.assertTrue(row["padding_guards_headers_input_immutable"])

    def test_fresh_public_replay_is_byte_stable(self):
        before = hashlib.sha256(REPORT.read_bytes()).hexdigest()
        run = subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        fresh = json.loads(run.stdout)
        self.assertEqual(fresh, json.loads(REPORT.read_text()))
        self.assertEqual(hashlib.sha256(REPORT.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
