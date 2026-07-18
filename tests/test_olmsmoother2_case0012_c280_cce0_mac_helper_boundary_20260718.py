#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_cce0_mac_helper_boundary_20260718.py"


class Case0012C280Cce0MacHelperBoundaryTests(unittest.TestCase):
    def test_first_downstream_boundary_is_byte_grounded(self):
        with tempfile.TemporaryDirectory(prefix="olm_test_c280_cce0_20260718_") as temp:
            temp_path = Path(temp)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output-json", str(temp_path / "report.json"), "--output-md", str(temp_path / "report.md")],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((temp_path / "report.json").read_text())
            self.assertIn(report["verdict"], {"PASS_NO_C280_CCE0_MAC_HELPER_DIVERGENCE", "DIVERGENCE_AT_FIRST_C280_CCE0_FLOAT32_WORD"})
            self.assertEqual(report["boundary"]["descriptor"], [92, 841, 1, 92, 842, 2])
            self.assertEqual(report["boundary"]["actual_cce0_input_count"], 2)
            self.assertEqual(report["boundary"]["mac_helper_count"], 2)


if __name__ == "__main__":
    unittest.main()
