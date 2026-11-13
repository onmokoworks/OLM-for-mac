import tempfile
from pathlib import Path
import unittest
import button_scaffold as b
class ButtonScaffoldTests(unittest.TestCase):
    def test_changed_anchor_fails_closed(self):
        for source in ('none','x x'):
            with self.assertRaises(ValueError):b.replace_once(source,'x','y')
    def test_button_labels_are_admitted_and_probe_is_derived_only(self):
        module=b.load_scaffold()
        self.assertIsNotNone(module)
        source=b.TOOLS/'scaffold/probe/src/lib.rs'
        before=source.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'probe';b.prepare_probe(out)
            generated=(out/'src/lib.rs').read_text()
            self.assertIn('PF_Param_BUTTON =>',generated)
            self.assertIn('u.button_d.u.namesptr',generated)
            self.assertTrue((out/'source-provenance.json').is_file())
            with self.assertRaises(FileExistsError):b.prepare_probe(out)
        self.assertEqual(before,source.read_bytes())
