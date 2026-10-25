"""Offline byte-preservation, backup, restore and busy refusal checks."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ae_dialog_watch.prefs import enable_bytes, scripting_prefs


class PrefTests(unittest.TestCase):
    def test_newlines_and_existing_value(self):
        for nl in (b'\r', b'\n', b'\r\n'):
            for value in (None, b'00', b'01'):
                head = b'["Main Pref Section v2"]' + nl
                entry = b'\t"Pref_SCRIPTING_FILE_NETWORK_SECURITY" = '
                rest = b'\t"unrelated" = 99' + nl + b'["Other"]' + nl
                original = head + (entry + value + nl if value else b'') + rest
                changed, before = enable_bytes(original)
                self.assertEqual(before, value.decode() if value else None)
                self.assertEqual(changed, head + entry + b'01' + nl + rest)

    def test_ambiguous_refused(self):
        for data in (b'["Other"]\r', b'["Main Pref Section v2"]\r["Other"]\r"Pref_SCRIPTING_FILE_NETWORK_SECURITY" = 00\r'):
            with self.assertRaises(RuntimeError):
                enable_bytes(data)

    def test_round_trip_and_busy_refusal(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            root = Path(tmp)
            source = root / 'source.txt'
            original = b'["Main Pref Section v2"]\r\t"unrelated" = 99\r'
            source.write_bytes(original)
            with patch('ae_dialog_watch.prefs.subprocess.check_output', return_value=''):
                result = scripting_prefs(root / 'backup', source=source)
                self.assertEqual(result['before_sha256'], result['backup_sha256'])
                with self.assertRaises(RuntimeError):
                    scripting_prefs(root / 'backup', source=source)
            with patch('ae_dialog_watch.prefs.subprocess.check_output', return_value='/Applications/X/Contents/MacOS/After Effects\n'):
                with self.assertRaises(RuntimeError):
                    scripting_prefs(root / 'backup', restore=True)
                self.assertNotEqual(source.read_bytes(), original)
            with patch('ae_dialog_watch.prefs.subprocess.check_output', return_value=''):
                result = scripting_prefs(root / 'backup', restore=True)
                self.assertTrue(result['restored'])
                self.assertEqual(source.read_bytes(), original)


if __name__ == '__main__':
    SCRATCH = Path(sys.argv.pop()).resolve()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    unittest.main()
