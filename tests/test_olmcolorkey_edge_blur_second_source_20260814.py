from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmcolorkey_exported_owner_edge_blur_second_source_20260814.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_second_source_20260814.json"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
EXPECTED = {
    "PF8": "99647b451957968e17cc26de8539a5dda304ab87700e345af7daf1c16cee058f",
    "PF16": "5bec7e489732bac740337674f30a25cb94980820b1a5f061b9bc66e9c167332e",
    "PF32": "d44ecf31c9817bfd4383974cad242c78f55c85f370ea66e328bbcff51176be08",
}


class ColorKeySecondFixedSource(unittest.TestCase):
    def test_exported_owner_and_public_smart_replay_exact(self) -> None:
        subprocess.run(["python3", str(TOOL)], cwd=ROOT, check=True)
        report = json.loads(REPORT.read_text())
        self.assertEqual(report["schema"], "olmcolorkey.exported-owner-edge-second-source/1")
        self.assertEqual(report["status"], "raw_exact")
        self.assertEqual(report["fixture"]["dimensions"], [48, 27])
        self.assertEqual(report["fixture"]["row_padding_bytes"], 8)
        self.assertEqual(
            report["tuple"], {"direction": 0, "distance_type": 3, "amount": 4.0},
        )
        self.assertEqual(len(report["cases"]), 3)
        for row in report["cases"]:
            expected = EXPECTED[row["depth"]]
            self.assertEqual(row["status"], "raw_exact")
            self.assertEqual(row["actual_exported_raw_sha256"], expected)
            self.assertEqual(row["mac_public_smart_raw_sha256"], expected)
        self.assertEqual(
            report["production_source_sha256"],
            hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        )

    def test_claim_is_one_source_tuple_and_three_depths_only(self) -> None:
        report = json.loads(REPORT.read_text())
        boundary = report["claim_boundary"]
        self.assertIn("fixed 48x27", boundary)
        self.assertIn("Direction 0 / Distance Type 3 / Amount 4", boundary)
        self.assertIn("PF8/PF16/PF32", boundary)
        self.assertIn("remain unclaimed", boundary)


if __name__ == "__main__":
    unittest.main()
