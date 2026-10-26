"""Release payload contract, independent of Xcode and historical AE requests."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_mac_plugin_package import EXPECTED_PLUGINS, verify_layout, single_package_root


class Layout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'OLM_for_Mac'
        self.root.mkdir()
        for name in EXPECTED_PLUGINS:
            (self.root / (name + '.plugin')).mkdir()
        for lang, dest in [('JA', 'README.md'), ('EN', 'README.en.md')]:
            shutil.copyfile(ROOT / 'docs' / f'PACKAGE_README_{lang}.md', self.root / dest)
        shutil.copyfile(ROOT / 'LICENSE', self.root / 'LICENSE')

    def test_exact_layout(self):
        verify_layout(self.root)
        self.assertEqual(len(list(self.root.iterdir())), 13)
        self.assertEqual(single_package_root(self.root.parent), self.root)

    def test_reject_old_payload_and_missing_bundle(self):
        for name in ['manifest.json', 'INSTALL.txt', 'AE_PIXEL_VALIDATION', 'docs']:
            extra = self.root / name
            extra.touch()
            with self.assertRaises(ValueError):
                verify_layout(self.root)
            extra.unlink()
        (self.root / (EXPECTED_PLUGINS[0] + '.plugin')).rmdir()
        with self.assertRaises(ValueError):
            verify_layout(self.root)

    def test_broken_readme_link(self):
        with (self.root / 'README.md').open('a') as f:
            f.write('\n[missing](docs/INSTALL_JA.md)\n')
        with self.assertRaisesRegex(ValueError, 'broken README link'):
            verify_layout(self.root)

    def test_extra_outer_file(self):
        (self.root.parent / 'manifest.json').touch()
        with self.assertRaises(ValueError):
            single_package_root(self.root.parent)


if __name__ == '__main__':
    unittest.main()
