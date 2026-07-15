import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools/emulation/test_olmtoondilate_actual_aex_differential_20260716_followup.py"
REPORT = ROOT / "tools/emulation/OLMTOONDILATE_ACTUAL_AEX_DIFFERENTIAL_20260716_followup.md"


class ToonDilateActualAexFollowupArtifactTests(unittest.TestCase):
    def test_followup_artifacts_are_new_and_scoped(self):
        self.assertTrue(HARNESS.is_file())
        self.assertTrue(REPORT.is_file())
        text = REPORT.read_text(encoding="utf-8")
        self.assertIn("context+0x180", text)
        self.assertIn("no AE-exact claim", text)
        self.assertIn("FACT", text)
        self.assertIn("INFERENCE", text)


if __name__ == "__main__":
    unittest.main()
