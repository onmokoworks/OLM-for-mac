#!/usr/bin/env python3
"""Offline policy + Vision fixture tests; never launches AE."""
import argparse
import json
import plistlib
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ae_dialog_watch.test_e2e import LaunchWait
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
    def test_script_progress_fixture(self):
        fixture = ROOT / 'orchestra/reports/A02e-evidence/priority-e2/dialogs'
        events = [json.loads(line) for line in (fixture / 'dialogs.jsonl').read_text().splitlines()]
        event = next(e for e in events if e.get('event') == 'unknown' and
                     e.get('window', {}).get('kCGWindowNumber') == 1825)
        title = event['window']['kCGWindowName']
        for text, expected in [(title, True), ('Running script launch.jsx...', True),
                               ('スクリプトエラー', False), ('Unknown dialog', False)]:
            result = json.loads(subprocess.check_output([str(BINARY), 'script-progress'], input=text.encode()))
            self.assertEqual(result['scriptProgress'], expected)
        ocr = json.loads(subprocess.check_output([str(BINARY), 'ocr', str(fixture / 'unknown-1825.png')]))
        self.assertEqual(ocr['candidates'], [])
        self.assertFalse(ocr['knownDialog'])

    def test_workspace_metadata_boundaries(self):
        def check(expected, **data):
            result = json.loads(subprocess.check_output([str(BINARY), 'workspace'],
                input=json.dumps(data).encode()))
            self.assertEqual(result['workspace'], expected, data)
        check(True, title='Adobe After Effects 2026 - Untitled *', width=1000, height=600)
        check(False, title='Adobe After Effects 2026', width=999, height=600)
        check(False, title='Adobe After Effects 2026', width=1000, height=599)
        check(False, title='Crash recovery', width=700, height=400)
        check(False, title='', width=3200, height=1743)
        check(True, title='', width=800, height=500, role='AXWindow', subrole='AXStandardWindow')
        check(False, title='', width=800, height=500, role='AXWindow', subrole='AXDialog')
        check(False, title='Adobe After Effects 2026', width=3200, height=1743, modal=True)

    def test_captured_workspaces_are_not_dialogs(self):
        # A03d retained window metadata + OCR; its PNG was not committed.
        captures = [('A03b-evidence/blocked-capture.jsonl', 1609),
                    ('A03d-evidence/live2/dialogs.jsonl', 1726)]
        for fixture, window_id in captures:
            events = [json.loads(line) for line in (ROOT / 'orchestra/reports' / fixture).read_text().splitlines()]
            event = next(e for e in events if e.get('window', {}).get('kCGWindowNumber') == window_id and 'ocr' in e)
            window = event['window']; bounds = window['kCGWindowBounds']
            result = json.loads(subprocess.check_output([str(BINARY), 'workspace'], input=json.dumps(dict(
                title=window['kCGWindowName'], width=bounds['Width'], height=bounds['Height'])).encode()))
            self.assertTrue(result['workspace'])
            self.assertFalse(policy(event['ocr'])['knownDialog'])
        image = ROOT / 'orchestra/reports/A03b-evidence/inspect-1609.png'
        ocr = json.loads(subprocess.check_output([str(BINARY), 'ocr', str(image)]))
        self.assertFalse(ocr['knownDialog'])
        self.assertEqual(ocr['layout'], [])

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

    def test_recovery_screenshots_and_negative_variants(self):
        import copy
        for fixture in ['A02d-evidence/blocked.png', 'A03c-evidence/no-safe-button-1670.png']:
            result = json.loads(subprocess.check_output([str(BINARY), 'ocr',
                str(ROOT / 'orchestra/reports' / fixture)]))
            rows = result['rows']
            self.assertEqual(len(result['layout']), 1, fixture)
            target = result['layout'][0]
            self.assertLess(target['box'][0], next(r['box'][0] for r in rows if r['text'] == 'プラグインを管理'))
            variants = []
            variants.append([r for r in rows if r['text'] != '環境設定をリセット'])
            variants.append(rows + [row('extra', [.01, target['box'][1], .02, target['box'][3]])])
            swapped = copy.deepcopy(rows)
            a, b = [next(r for r in swapped if r['text'] == label) for label in ['プラグインを管理', '環境設定をリセット']]
            a['box'], b['box'] = b['box'], a['box']
            variants.append(swapped)
            for title, confidence in [('別のタイトル', 1), ('クラッシュ修復オプション', .3)]:
                changed = copy.deepcopy(rows)
                heading = next(r for r in changed if r['text'] == 'クラッシュ修復オプション')
                heading.update(text=title, confidence=confidence)
                variants.append(changed)
            variants.append(rows + [row('overlap', target['box'])])
            for variant in variants:
                self.assertEqual(policy(variant)['layout'], [])


class LifecycleTests(unittest.TestCase):
    def test_marker_deadline_starts_at_workspace(self):
        wait = LaunchWait(0)
        wait.observe(170, True, False)
        self.assertEqual(wait.deadline, 350)
        self.assertEqual(wait.phase, 'JSX marker')
        wait.observe(300, True, False)
        self.assertEqual(wait.deadline, 350)
        wait.observe(340, True, True)
        self.assertEqual(wait.deadline, 400)
        self.assertEqual(wait.phase, 'quit')
        wait.observe(399, True, True)
        self.assertEqual(wait.deadline, 400)

    def test_late_workspace_does_not_extend_quit(self):
        wait = LaunchWait(0)
        wait.observe(10, False, True)
        wait.observe(20, True, True)
        self.assertEqual(wait.deadline, 70)

    def test_disabled_prevention_never_accesses_preferences(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            with patch('ae_dialog_watch.watcher.subprocess.run') as run:
                result = prepare_launch(Path(tmp), disabled=True)
                self.assertEqual(result['changes'], [])
                run.assert_not_called()

    def test_prevention_backs_up_before_writing_only_two_flags(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            root = Path(tmp)
            app = root / 'AE.app'
            (app / 'Contents').mkdir(parents=True)
            (app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleShortVersionString': '26.3'}))
            prefs = {'CrashOccurred': True, 'ForceQuitOccured': True, 'untouched': 'keep'}
            source = root / 'Library/Preferences/com.Adobe.After Effects.26.3.plist'
            source.parent.mkdir(parents=True)
            original = plistlib.dumps(prefs)
            source.write_bytes(original)
            writes = []
            def run(cmd, **kwargs):
                if cmd[1] == 'export':
                    Path(cmd[3]).write_bytes(plistlib.dumps(prefs))
                else:
                    self.assertEqual(cmd[:3], ['defaults', 'write', 'com.Adobe.After Effects.26.3'])
                    self.assertEqual(cmd[4:], ['-bool', 'false'])
                    copies = list((root/'state').glob('preferences-*/on-disk.plist'))
                    self.assertEqual(copies[0].read_bytes(), original)
                    writes.append(cmd[3])
                    prefs[cmd[3]] = False
            def output(cmd, **kwargs):
                return '' if cmd[0] == 'ps' else str(int(prefs[cmd[-1]])) + '\n'
            with patch('ae_dialog_watch.watcher.APP', app), patch('pathlib.Path.home', return_value=root), \
                 patch('ae_dialog_watch.watcher.subprocess.run', side_effect=run), \
                 patch('ae_dialog_watch.watcher.subprocess.check_output', side_effect=output):
                result = prepare_launch(root/'state')
            self.assertEqual(writes, ['CrashOccurred', 'ForceQuitOccured'])
            self.assertEqual(result['before'], dict.fromkeys(writes, '1'))
            self.assertEqual(result['after'], dict.fromkeys(writes, '0'))
            self.assertEqual(prefs['untouched'], 'keep')
            self.assertEqual(len(result['backups']), 2)

    def test_busy_prevention_refuses_before_backup_or_write(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            with patch('ae_dialog_watch.watcher.subprocess.check_output',
                       return_value='/Applications/AE.app/Contents/MacOS/After Effects\n'), \
                 patch('ae_dialog_watch.watcher.subprocess.run') as run:
                with self.assertRaisesRegex(RuntimeError, 'AE busy'):
                    prepare_launch(tmp)
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
