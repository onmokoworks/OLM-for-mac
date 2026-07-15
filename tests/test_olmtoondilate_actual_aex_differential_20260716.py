import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools/emulation/test_olmtoondilate_actual_aex_differential_20260716.py"
REPORT = ROOT / "tools/emulation/OLMTOONDILATE_ACTUAL_AEX_DIFFERENTIAL_20260716_REPORT.md"


class ActualAexDifferentialArtifactTests(unittest.TestCase):
    def test_new_harness_and_report_are_present(self):
        self.assertTrue(HARNESS.is_file())
        self.assertTrue(REPORT.is_file())
        text = REPORT.read_text(encoding="utf-8")
        self.assertIn("actual-AEX worker differential", text)
        self.assertIn("no AE-exact claim", text)


if __name__ == "__main__":
    unittest.main()
