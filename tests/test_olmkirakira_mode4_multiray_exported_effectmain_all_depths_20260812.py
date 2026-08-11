import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode4_multiray_exported_effectmain_all_depths_20260812.py"
REPORTS = {
    "horizontal": (ROOT / "refs/conformance/olmkirakira_mode4_horizontal_solo_exported_effectmain_all_depths_20260812.json", [True, True, False]),
    "diagonal2": (ROOT / "refs/conformance/olmkirakira_mode4_diagonal2_solo_exported_effectmain_all_depths_20260812.json", [True, True, False]),
    "highlight": (ROOT / "refs/conformance/olmkirakira_mode4_highlight_solo_exported_effectmain_all_depths_20260812.json", [True, True, True]),
    "multiray": (ROOT / "refs/conformance/olmkirakira_mode4_multiray_exported_effectmain_all_depths_20260812.json", [False, False, False]),
}


class KiraMode4MultirayExportedOwnerTest(unittest.TestCase):
    def test_public_owner_admitted_subset_and_fail_closed_boundary(self):
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        for _, (path, expected) in REPORTS.items():
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual([row["depth"] for row in report["rows"]], ["PF8", "PF16", "PF32"])
            self.assertEqual([row["exact"] for row in report["rows"]], expected)
            self.assertTrue(all(row["guards_intact"] and row["input_unchanged"]
                                and row["mac_padding_preserved"] and row["render_error"] == 0
                                for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
