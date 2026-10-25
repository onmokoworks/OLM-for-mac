#!/usr/bin/env python3
"""Lifecycle and retention checks; all temporary files remain in the worktree."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import nightly_summary as n

SCRATCH = n.ROOT/'orchestra/state/N01-nightly-fuzz-runner'


class NightlyTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.directory = Path(self.tmp.name)
        (self.directory/'witnesses').mkdir()
        self.old_temp = tempfile.tempdir
        self.old_env = {k: os.environ.get(k) for k in ('TMPDIR', 'TMP', 'TEMP')}

    def tearDown(self):
        tempfile.tempdir = self.old_temp
        for k, v in self.old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def test_classification(self):
        for oracle, candidate, expected in [('ok', 'exact', 'E'), ('ok', 'mismatch', 'M'),
                                              ('ok', 'refusal', 'R'), ('budget', 'refusal', 'U'),
                                              ('ok', 'budget', 'U')]:
            self.assertEqual(n.category(dict(oracle={'status':oracle}, routes={'smart':{'status':candidate}}), 'smart'), expected)

    def test_refusal_reduction_and_cleanup(self):
        class Adapter:
            name = 'olmcolorkey'
            generator_version = 'test'
            max_size = 256
            def prepare(self, directory, deadline):
                return {}
            def generate(self, seed, index):
                return dict(seed=seed, index=index, pixels=b'abcd', geometry=[1,1], depth=8, profile='sdr', parameters=[])
        result = dict(oracle={'status':'ok'}, routes={'smart':{'status':'refusal','error':516}})
        def apply(a, case, operation):
            return {**case, 'pixels':b'\0'*4}
        with patch.object(n.importlib, 'import_module', return_value=SimpleNamespace(Adapter=lambda args:Adapter())), \
             patch.object(n, 'require_host'), patch.object(n, 'sample', side_effect=lambda c,g:c), \
             patch.object(n, 'memory_ready', side_effect=[True, False]), \
             patch.object(n, 'evaluate', return_value=result), \
             patch.object(n, 'proposals', return_value=[{'kind':'zero'}]), \
             patch.object(n, 'apply_operation', side_effect=apply):
            n.campaign(self.directory, 0, 'olmcolorkey', 'default', 42, time.monotonic()+5)
        r = json.loads((self.directory/'run-000000.json').read_text())
        self.assertEqual(r['counts'], {'R':1})
        self.assertFalse((self.directory/'scratch').exists())
        w = json.loads(next((self.directory/'witnesses').glob('*.json')).read_text())
        self.assertEqual(w['reduction']['accepted'], [{'kind':'zero'}])
        self.assertEqual(w['result']['routes']['smart']['error'], 516)
        text = n.summary(self.directory)
        self.assertIn('| olmcolorkey | default | 0 | 0 | 1 | 0 |', text)
        self.assertIn('516', text)

    def test_memory_pause_deadline(self):
        with patch.object(n.subprocess, 'run', return_value=SimpleNamespace(stdout='System-wide memory free percentage: 29%')):
            self.assertFalse(n.memory_ready(time.monotonic()+0.02))

    @unittest.skipUnless(os.environ.get('OLM_NIGHTLY_INTEGRATION') == '1', 'opt-in real workers')
    def test_all_plugin_sampler_routes(self):
        # Exactly one fresh case per cell; not a numerical acceptance gate.
        for ordinal in range(len(n.PLUGINS)*len(n.SAMPLERS)):
            plugin = n.PLUGINS[ordinal % len(n.PLUGINS)]
            sampler = n.SAMPLERS[ordinal // len(n.PLUGINS)]
            with self.subTest(plugin=plugin, sampler=sampler):
                n.campaign(self.directory, ordinal, plugin, sampler, 20261025000+ordinal,
                           time.monotonic()+60, case_limit=1)
                r = json.loads((self.directory/f'run-{ordinal:06d}.json').read_text())
                self.assertEqual(sum(r['counts'].values()), 1)
                self.assertEqual(r['route'], 'classic' if plugin == 'olmsmoother' else 'smart')
                self.assertEqual(r['provenance']['oracle_routes'], {r['route']: r['route']})
                print('CELL', plugin, sampler, r['counts'], flush=True)

    def test_sigint_reaps_separate_child_group(self):
        marker = self.directory/'child.pid'
        code = '''import sys, signal, time
sys.path.insert(0, 'tools/fuzz')
from nightly_summary import interrupted
from core import command
signal.signal(signal.SIGINT, interrupted)
try:
    command([sys.executable, '-c', "import os,time,pathlib; pathlib.Path("+repr(sys.argv[1])+").write_text(str(os.getpid())); time.sleep(60)"], timeout=60, deadline=time.monotonic()+60)
except KeyboardInterrupt:
    pass
'''
        with (self.directory/'signal.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-c', code, str(marker)], cwd=n.ROOT,
                                       stdout=log, stderr=log, start_new_session=True)
            try:
                end = time.monotonic()+5
                while not marker.exists() and time.monotonic()<end:
                    time.sleep(.02)
                self.assertTrue(marker.exists())
                child = int(marker.read_text())
                process.send_signal(signal.SIGINT)
                self.assertEqual(process.wait(timeout=5), 0)
                with self.assertRaises(ProcessLookupError):
                    os.kill(child, 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if marker.exists():
                    try:
                        os.kill(int(marker.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == '__main__':
    unittest.main()
