"""Worktree asset precedence, explicit paths, and non-mutating lookup."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.emulation.olm_assets import main_assets, resolve_asset, asset_relative


class AssetsTest(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'orchestra/state/F36-fixture-runner-worktree-and-triage'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'worktree'
        self.main = Path(self.temp.name) / 'main'
        self.root.mkdir()
        self.main.mkdir()
        env = patch.dict(os.environ, OLM_MAIN_ASSETS=str(self.main))
        env.start()
        self.addCleanup(env.stop)
        main_assets.cache_clear()
        self.addCleanup(main_assets.cache_clear)

    def test_local_first_and_leaf_fallback(self):
        (self.root / 'refs').mkdir()
        (self.main / 'refs').mkdir()
        remote = self.main / 'refs/input.bin'
        remote.write_bytes(b'main')
        self.assertEqual(resolve_asset('refs/input.bin', self.root), remote)
        local = self.root / 'refs/input.bin'
        local.write_bytes(b'worktree')
        self.assertEqual(resolve_asset(local, self.root), local)
        self.assertEqual(remote.read_bytes(), b'main')

    def test_missing_and_external_are_preserved_without_writes(self):
        self.assertEqual(resolve_asset('missing/a.bin', self.root), self.root / 'missing/a.bin')
        self.assertFalse((self.root / 'missing').exists())
        explicit = Path(self.temp.name) / 'external'
        self.assertEqual(resolve_asset(explicit, self.root), explicit)
        self.assertEqual(list(self.main.iterdir()), [])

    def test_default_git_common_directory(self):
        with patch.dict(os.environ), patch('tools.emulation.olm_assets.subprocess.check_output', return_value=str(self.main / '.git') + '\n') as command:
            os.environ.pop('OLM_MAIN_ASSETS', None)
            self.assertEqual(main_assets(self.root), self.main)
            command.assert_called_once_with(['git', 'rev-parse', '--git-common-dir'], cwd=self.root, text=True)

    def test_evidence_labels(self):
        self.assertEqual(asset_relative(self.main / 'refs/input.bin', self.root), Path('refs/input.bin'))
        self.assertEqual(asset_relative(self.root / 'core/input.cpp', self.root), Path('core/input.cpp'))


if __name__ == '__main__':
    unittest.main()
