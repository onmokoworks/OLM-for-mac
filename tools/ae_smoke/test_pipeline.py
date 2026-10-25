#!/usr/bin/env python3
"""Offline checks; these do not establish any AE pixel result."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import plistlib
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import run_ae_smoke as runner


class PipelineTests(unittest.TestCase):
    def test_lock_state_accepts_ioreg_root_and_rejects_missing_evidence(self):
        for locked in (True,):
            root = {'IOConsoleUsers': [{'CGSSessionScreenIsLocked': locked}]}
            for document in (root, [root]):
                with patch.object(runner.subprocess, 'check_output', return_value=plistlib.dumps(document)):
                    self.assertEqual(runner.screen_locked(), locked)
        with patch.object(runner.subprocess, 'check_output', return_value=plistlib.dumps({})):
            with self.assertRaises(RuntimeError):
                runner.screen_locked()

    def test_absent_lock_key_requires_logged_in_console(self):
        console = {'kCGSSessionOnConsoleKey': True, 'kCGSessionLoginDoneKey': True}
        for users, expected in [([console], False), ([{}, console], False),
                                ([{}], None), ([], None),
                                ([dict(console, CGSSessionScreenIsLocked=False)], None),
                                ([dict(console, CGSSessionScreenIsLocked='true')], None),
                                ([dict(console, kCGSessionLoginDoneKey=False)], None),
                                ([console, {'CGSSessionScreenIsLocked': True}], True)]:
            with self.subTest(users=users), patch.object(
                    runner.subprocess, 'check_output',
                    return_value=plistlib.dumps({'IOConsoleUsers': users})):
                if expected is None:
                    with self.assertRaises(RuntimeError):
                        runner.screen_locked()
                else:
                    self.assertIs(runner.screen_locked(), expected)

    def test_lock_wait_resume_does_not_restart_twelve_hour_deadline(self):
        state = MagicMock()
        log = state.__truediv__.return_value
        log.exists.return_value = True
        log.open = mock_open(read_data='100.000 locked=True\n')
        with patch.object(runner, 'screen_locked', return_value=True), \
             patch.object(runner.time, 'time', return_value=43301), \
             patch.object(runner.time, 'monotonic', return_value=10), \
             patch.object(runner.time, 'sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError, '12 hours'):
                runner.wait_unlocked(state)
            sleep.assert_not_called()

    def test_main_executable_check_excludes_helpers_and_includes_versions(self):
        listing = ('1 /Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects\n'
                   '2 /Applications/Adobe After Effects 2025/Adobe After Effects 2025.app/Contents/MacOS/After Effects\n'
                   '3 /Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/crashpad_handler\n')
        with patch.object(runner, 'capture', return_value=listing) as call:
            self.assertEqual(runner.running(), ['1', '2'])
            self.assertEqual(call.call_args.args[0], ['ps', '-axo', 'pid=,comm='])

    def test_ae16_file_encoding_inverse_for_every_sdr_value(self):
        source = np.arange(32769, dtype=np.uint64)
        encoded = source * 65535 // 32768
        decoded = (encoded * 32768 + 32767) // 65535
        self.assertTrue(np.array_equal(source, decoded))

    def test_workspace_dispatch_and_unknown_dialog_cleanup(self):
        scratch = Path(os.environ.get('TMPDIR', str(runner.ROOT / 'orchestra/state/A02e-real-ae-retest-downsample')))
        scratch.mkdir(parents=True, exist_ok=True)
        for unknown in (False, True):
            with self.subTest(unknown=unknown), TemporaryDirectory(dir=scratch) as tmp:
                state = Path(tmp)
                wrapper, out = state / 'launch.jsx', state / 'build.json'
                wrapper.touch()
                out.write_text(json.dumps({'phase': 'complete'}))
                watcher = MagicMock()
                watcher.directory = state
                (state / 'workspace-ready').touch()
                if unknown:
                    watcher.check.side_effect = [None, RuntimeError('unknown dialog')]
                ae, dispatch = MagicMock(), MagicMock()
                ae.pid = 42
                ae.poll.return_value = None
                with patch.object(runner, 'preflight'), \
                     patch.object(runner, 'screen_locked', return_value=False), \
                     patch.object(runner, 'running', side_effect=[['42'], []]), \
                     patch.object(runner.subprocess, 'Popen', side_effect=[ae, dispatch]) as popen, \
                     patch.object(runner, 'quit_once') as quit_once:
                    if unknown:
                        with self.assertRaisesRegex(RuntimeError, 'unknown dialog'):
                            runner._build_owned(state, wrapper, out, watcher)
                        quit_once.assert_called_once_with(state)
                        watcher.capture_owned.assert_called_once_with(42)
                        self.assertEqual(popen.call_count, 1)
                    else:
                        runner._build_owned(state, wrapper, out, watcher)
                        quit_once.assert_not_called()
                        self.assertEqual(popen.call_count, 2)
                        self.assertEqual(popen.call_args_list[0].args[0],
                                         [str(runner.APP / 'Contents/MacOS/After Effects')])
                        self.assertEqual(popen.call_args_list[1].args[0], [
                            'osascript', '-e', 'tell application ' + json.dumps(str(runner.APP)) +
                            ' to DoScriptFile POSIX file ' + json.dumps(str(wrapper))])
                        dispatch.wait.assert_called_once_with(timeout=30)

    def test_only_2026_full_path_is_used(self):
        self.assertEqual(str(runner.APP), '/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app')


if __name__ == '__main__':
    unittest.main()
