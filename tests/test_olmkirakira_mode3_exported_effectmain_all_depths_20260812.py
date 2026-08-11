import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode3_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_length50_exported_effectmain_all_depths_20260812.json"


class KiraMode3ExportedOwnerTest(unittest.TestCase):
    def test_gaussian_length50_all_depths_exact(self):
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["fixture"]["length"], 50)
        self.assertEqual([row["depth"] for row in report["rows"]], ["PF8", "PF16", "PF32"])
        self.assertTrue(all(row["exact"] and row["guards_intact"] for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
