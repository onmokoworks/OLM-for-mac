import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olmkirakira_windows_boundary_mac_ae_20260806.py"


class KiraBoundaryMacRunnerTest(unittest.TestCase):
    def test_preflight_is_hash_bound_and_non_launching(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olmkira-boundary-preflight-") as temp:
            report = Path(temp) / "report.json"
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--report", str(report)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "preflight_ready")
            self.assertIs(data["checks"]["depths_exact"], True)
            self.assertIs(data["checks"]["windows_members_complete"], True)
            self.assertEqual(len(data["request_zip"]["sha256"]), 64)
            self.assertEqual(len(data["return_zip"]["sha256"]), 64)
            self.assertEqual(data["rows"], [])


if __name__ == "__main__":
    unittest.main()
