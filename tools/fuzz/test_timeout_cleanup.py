"""F48: timeout signal races, PID fallback, and preservation of case rows."""
import argparse
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import run
from test_framework import Synthetic

SCRATCH = Path(os.environ.get('OLM_FUZZ_TEST_SCRATCH',
                             run.ROOT/'orchestra/state/F48-fuzz-killpg-permission'))


class CleanupTests(unittest.TestCase):
    def test_live_child_pid_fallback(self):
        real_killpg = os.killpg
        for error in (PermissionError(errno.EPERM, 'injected'),
                      ProcessLookupError(errno.ESRCH, 'injected')):
            children = []
            real_popen = subprocess.Popen

            def launch(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child

            def signal_group(pid, sig):
                if sig:
                    raise error
                return real_killpg(pid, sig)

            with self.subTest(error=type(error).__name__):
                try:
                    with patch.object(core.subprocess, 'Popen', side_effect=launch), \
                         patch.object(core.os, 'killpg', side_effect=signal_group):
                        result, _, _ = core.command(
                            [sys.executable, '-c', 'import time; time.sleep(60)'],
                            timeout=.05, deadline=time.monotonic()+2)
                    self.assertEqual(result['status'], 'budget')
                    self.assertEqual(result['cleanup']['status'], 'done')
                    self.assertEqual(children[0].returncode, -signal.SIGKILL)
                    with self.assertRaises(ProcessLookupError):
                        os.kill(children[0].pid, 0)
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                        child.wait(timeout=2)

    def test_timeout_kills_descendant_holding_pipes(self):
        # The group leader exits before communicate times out; its child keeps
        # stdout open. Cleanup must still signal the group after poll/reaping.
        script = ('import subprocess,sys; '
                  'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); '
                  'print(p.pid,flush=True)')
        result, out, _ = core.command([sys.executable, '-c', script],
                                     timeout=.2, deadline=time.monotonic()+3)
        pid = int(out.strip())
        try:
            self.assertEqual(result['status'], 'budget')
            until = time.monotonic()+2
            while time.monotonic() < until:
                state = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)],
                                       capture_output=True, text=True).stdout.strip()
                if not state or state.startswith('Z'):
                    break
                time.sleep(.01)
            self.assertTrue(not state or state.startswith('Z'), state)
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_already_gone_group(self):
        proc = Mock(pid=123, stdin=None, stdout=None, stderr=None)
        proc.poll.return_value = 0
        proc.communicate.return_value = (b'finished', b'')
        for failure in (PermissionError(errno.EPERM, 'race'), ProcessLookupError()):
            with patch.object(core.os, 'killpg', side_effect=[failure, ProcessLookupError()]):
                cleanup, out, _ = core.timeout_cleanup(proc)
            self.assertEqual(cleanup['status'], 'done')
            self.assertEqual(out, b'finished')
        proc.kill.assert_not_called()

    def test_exited_child_does_not_prove_group_is_gone(self):
        proc = Mock(pid=123, stdin=None, stdout=None, stderr=None)
        proc.poll.return_value = 0
        proc.communicate.return_value = (b'', b'')
        with patch.object(core.os, 'killpg', side_effect=[PermissionError(), None]):
            cleanup, _, _ = core.timeout_cleanup(proc)
        self.assertEqual(cleanup['status'], 'unresolved')
        self.assertTrue(cleanup['child_reaped'])
        self.assertFalse(cleanup['group_cleanup_confirmed'])

    def test_unconfirmed_cleanup_is_bounded(self):
        proc = Mock(pid=123)
        proc.poll.return_value = None
        proc.kill.side_effect = PermissionError(errno.EPERM, 'pid denied')
        proc.communicate.side_effect = subprocess.TimeoutExpired('child', 1, output=b'partial')
        with patch.object(core.os, 'killpg', side_effect=PermissionError(errno.EPERM, 'group denied')):
            cleanup, out, _ = core.timeout_cleanup(proc)
        self.assertEqual(cleanup['status'], 'unresolved')
        self.assertFalse(cleanup['child_reaped'])
        self.assertFalse(cleanup['group_cleanup_confirmed'])
        self.assertEqual(out, b'partial')
        proc.communicate.assert_called_once_with(timeout=core.CLEANUP_TIMEOUT)
        proc.wait.assert_not_called()
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            stream.close.assert_called_once()

    def test_shrink_cleanup_retains_original_result_and_case(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as name:
            directory = Path(name)
            adapter = Synthetic()
            original = core.evaluate(adapter, adapter.generate(105, 50), directory, time.monotonic()+5)
            failure = {'status': 'unresolved', 'errors': ['kill pid: denied']}
            timed_out = {'oracle': {'status': 'budget', 'cleanup': failure},
                         'routes': {r: {'status': 'uncompared'} for r in adapter.routes}}
            args = argparse.Namespace(shrink_seconds=1, shrink_attempts=2,
                                      corpus=directory, corpus_max_bytes=100000)
            with patch.object(core, 'evaluate', return_value=timed_out):
                row = run.run_one(adapter, 105, 50, directory, time.monotonic()+5, args, {})
            self.assertEqual(row['index'], 50)
            self.assertEqual(row['result'], original)
            self.assertEqual(row['status'], 'unresolved')
            self.assertEqual(row['unresolved_cleanup'], [failure])
            saved = json.loads(next(directory.glob('*.json')).read_text())
            self.assertEqual(saved['result'], original)
            self.assertEqual(saved['reduction']['unresolved_cleanup'], [failure])
            self.assertEqual(run.summarize([row])[0]['unresolved_cases'], 1)

    def test_completed_command_unchanged(self):
        result, out, err = core.command([sys.executable, '-c', 'print("ok")'],
                                      timeout=2, deadline=time.monotonic()+3)
        self.assertEqual(result, {'status': 'ok', 'returncode': 0})
        self.assertEqual((out, err), (b'ok\n', b''))


if __name__ == '__main__':
    unittest.main()
