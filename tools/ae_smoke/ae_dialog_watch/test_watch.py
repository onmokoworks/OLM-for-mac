#!/usr/bin/env python3
"""Offline policy + Vision fixture tests; never launches AE."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ae_dialog_watch.watcher import compile_tool, DialogWatcher, prepare_launch

ROOT = Path(__file__).resolve().parents[3]
BINARY = None
SCRATCH = None


def row(text, box=None, confidence=1):
    return dict(text=text, box=box or [.1, .8, .1, .05], confidence=confidence)


def policy(rows):
    return json.loads(subprocess.check_output([str(BINARY), 'policy'],
                      input=json.dumps(rows).encode()))


class PolicyTests(unittest.TestCase):
    def test_exact_allowlist(self):
        labels = ['OK', '続行', 'Continue', '閉じる', 'Close', '後で', 'Later',
                  'スキップ', 'Skip', '今はしない', 'Not Now']
        for label in labels:
            self.assertEqual([r['text'] for r in policy([row(label)])['candidates']], [label])
        for label in ['Not Now!', 'Continue and Delete', '繞行', '統行', 'continue', '保存しない', 'Reset', 'Buy']:
            self.assertEqual(policy([row(label)])['candidates'], [])

    def test_destructive_overlap(self):
        for label in ['Delete', '削除', "Don't Save", 'Don’t Save', '環境設定をリセット',
                      'Replace', 'アンインストール', '購入', 'Sign Out', 'セーフモードで開始']:
            self.assertEqual(policy([row('OK'), row(label)])['candidates'], [])
            self.assertEqual(len(policy([row('OK'), row(label, [.5,.8,.2,.05])])['candidates']), 1)

    def test_centres_nonzero_negative_origin(self):
        self.assertEqual(policy([row('OK', [.25,.5,.5,.2])])['centres'], [[300,410]])

    def test_low_confidence_and_invalid_geometry(self):
        for r in [row('OK',confidence=.3), row('OK',[-.1,0,.2,.1]), row('OK',[0,0,0,.1])]:
            self.assertEqual(policy([r])['candidates'], [])

    def test_context_required(self):
        self.assertFalse(policy([row('OK'),row('Delete project?')])['knownDialog'])
        self.assertTrue(policy([row('クラッシュ修復オプション')])['knownDialog'])

    def test_saved_a02d_screenshot(self):
        path = ROOT / 'orchestra/reports/A02d-evidence/blocked.png'
        result = json.loads(subprocess.check_output([str(BINARY), 'ocr', str(path)]))
        self.assertTrue(result['knownDialog'])
        # The retained reduced screenshot can misrecognize 続行. Never fuzzy-map it.
        self.assertTrue(any('リセット' in r['text'] for r in result['rows']))
        self.assertTrue(all(r['text'] == '続行' for r in result['candidates']))
        for r in result['candidates']:
            self.assertLess(r['box'][0], .25)
            self.assertGreater(r['box'][1], .75)


class LifecycleTests(unittest.TestCase):
    def test_disabled_prevention_never_accesses_preferences(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            with patch('ae_dialog_watch.watcher.subprocess.run') as run:
                result = prepare_launch(Path(tmp), disabled=True)
                self.assertEqual(result['changes'], [])
                run.assert_not_called()

    def test_premature_success_exit_is_failure_when_ae_alive(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            watcher = DialogWatcher(tmp, binary=BINARY)
            watcher.bind(42)
            watcher.proc = Mock(returncode=0)
            watcher.proc.poll.return_value = 0
            (watcher.directory/'dialogs.jsonl').write_text('{}')
            with patch.object(watcher, '_owned_alive', return_value=True):
                with self.assertRaises(RuntimeError):
                    watcher.check()
            with patch.object(watcher, '_owned_alive', return_value=False):
                watcher.check()

    def test_error_exit_never_passes_as_normal_shutdown(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            watcher = DialogWatcher(tmp, binary=BINARY)
            watcher.bind(42)
            watcher.proc = Mock(returncode=2)
            watcher.proc.poll.return_value = 2
            (watcher.directory/'dialogs.jsonl').write_text('blocked')
            with self.assertRaisesRegex(RuntimeError, 'blocked'):
                watcher.check()

    def test_stop_is_cooperative(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            watcher = DialogWatcher(tmp, binary=BINARY)
            watcher.proc = Mock()
            watcher.stop()
            self.assertTrue((watcher.directory/'stop').exists())
            watcher.proc.wait.assert_called_once_with(timeout=30)
            watcher.proc.terminate.assert_not_called()
            watcher.proc.kill.assert_not_called()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--binary', type=Path)
    args = p.parse_args()
    SCRATCH = args.scratch.resolve()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    BINARY = args.binary.resolve() if args.binary else compile_tool(args.scratch)
    unittest.main(argv=[sys.argv[0]])
