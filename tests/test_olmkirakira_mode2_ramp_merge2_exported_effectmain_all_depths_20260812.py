import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode2_ramp_merge2_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_ramp_merge2_exported_effectmain_all_depths_20260812.json"


class KiraMode2RampMerge2ExportedOwnerTest(unittest.TestCase):
    def test_ramp_merge2_all_depths_exact(self):
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertTrue(report["fixture"]["horizontal_use_ramp"])
        self.assertEqual(report["fixture"]["merge_mode"], 2)
        self.assertEqual([row["depth"] for row in report["rows"]], ["PF8", "PF16", "PF32"])
        self.assertTrue(all(row["exact"] and row["guards_intact"] and
                            row["input_unchanged"] and row["mac_padding_preserved"]
                            for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
