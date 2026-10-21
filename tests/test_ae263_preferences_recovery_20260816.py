import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_ae263_preferences_recovery_20260816.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ae263_recovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AE263PreferencesRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script()
        cls.source = SCRIPT.read_text(encoding="utf-8")

    def test_default_is_read_only_and_ae_free(self):
        before = self.module.state()
        value = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(value.returncode, 0, value.stdout + value.stderr)
        after = json.loads(value.stdout)
        self.assertEqual(after, before)
        self.assertEqual(after["ae_or_aerender_processes"], [])

    def test_mutations_are_explicit_and_separate(self):
        self.assertIn('modes.add_argument("--prepare"', self.source)
        self.assertIn('modes.add_argument("--reset"', self.source)
        self.assertIn('modes.add_argument("--restore"', self.source)
        self.assertNotIn("reset()\n    prepare()", self.source)
        self.assertIn("os.rename(PREFS, MOVED)", self.source)
        self.assertIn("os.rename(MOVED, PREFS)", self.source)

    def test_live_prepared_state_is_exact_when_present(self):
        current = self.module.state()
        if current["manifest_present"]:
            self.assertTrue(current["prepared_exact"])
            self.assertIn(current["status"], {"prepared_no_reset", "reset_applied", "restored"})


if __name__ == "__main__":
    unittest.main()
