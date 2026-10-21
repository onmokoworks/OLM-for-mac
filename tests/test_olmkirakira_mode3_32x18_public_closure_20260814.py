import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode3_32x18_public_closure_20260814.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json"


class KiraMode332x18PublicClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = REPORT.read_bytes()
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.after = REPORT.read_bytes()
        cls.report = json.loads(cls.after)

    def test_three_public_cells_are_raw_exact(self):
        self.assertEqual(
            self.report["status"], "raw_exact_bounded_public_classic_and_smart"
        )
        self.assertEqual([row["depth"] for row in self.report["positive_cells"]], [8, 16, 32])
        self.assertTrue(all(
            row["oracle_sha256"] == row["mac_smart_sha256"] == row["mac_classic_sha256"]
            for row in self.report["positive_cells"]
        ))

    def test_scope_and_negative_closure_are_bounded(self):
        self.assertEqual(self.before, self.after)
        self.assertEqual(len(self.report["parameter_lifecycle_failures"]), 50)
        self.assertEqual(
            {row["name"] for row in self.report["negative_rows"]},
            {"pre_request_unlisted", "rotation_one", "source_mutation", "input_width",
             "output_extent", "output_rowbytes_extra", "declared_depth"},
        )
        self.assertFalse(self.report["contract"]["ae_launched"])
        self.assertFalse(self.report["contract"]["installed"])


if __name__ == "__main__":
    unittest.main()
