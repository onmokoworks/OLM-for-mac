import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode3_32x18_public_failclose_20260814.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_failclose_20260814.json"


class KiraMode332x18PublicFailCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = REPORT.read_bytes()
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.after = REPORT.read_bytes()
        cls.report = json.loads(cls.after)

    def test_live_public_probe_fails_closed_at_all_depths(self):
        self.assertEqual(self.report["status"], "exact_fail_closed_unlisted_source")
        self.assertEqual(self.report["depths"], ["PF8", "PF16", "PF32"])
        self.assertEqual(self.report["result"]["return"], "PF_Err_BAD_CALLBACK_PARAM")
        self.assertTrue(self.report["result"]["input_full_storage_unchanged"])
        self.assertTrue(self.report["result"]["output_full_storage_untouched"])

    def test_default_validation_is_read_only_and_scope_is_honest(self):
        self.assertEqual(self.before, self.after)
        self.assertFalse(self.report["ae_launched"])
        self.assertFalse(self.report["installed_or_production_modified"])
        self.assertIn("modulo-192-alpha source is not admitted", self.report["boundary"])
        self.assertIn("No numerical equality", self.report["boundary"])


if __name__ == "__main__":
    unittest.main()
