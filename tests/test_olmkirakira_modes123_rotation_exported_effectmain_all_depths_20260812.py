import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_modes123_rotation_exported_effectmain_all_depths_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_modes123_rotation_exported_effectmain_all_depths_20260812.json"


class KiraModes123RotationOwnerTest(unittest.TestCase):
    def test_nine_rotation_rows_are_exact(self):
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "exact")
        self.assertEqual(report["rotation_degrees"], 1.0)
        self.assertEqual(report["windows_raw_fixed"], 1)
        self.assertEqual(len(report["rows"]), 9)
        self.assertTrue(all(row["exact"] for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
