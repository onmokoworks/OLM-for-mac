#!/usr/bin/env python3
"""Read-only first-parent merge bisection of the ColorKey ROI gate row."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'orchestra/state/I01-integration-check'
BASE = 'd027fd4d'
TEST = 'tests/test_olmcolorkey_generic_roi_tile.py'
GATE = 'scripts/run_olm_generic_beta_gate.py'
ADAPTER = 'tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py'
SOURCE = 'mac/OLMColorKey/OLMColorKey.cpp'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def main():
    STATE.mkdir(parents=True, exist_ok=True)
    snapshot = STATE / 'bisect-snapshot'
    env = dict(os.environ, TMPDIR=str(STATE), PYTHONDONTWRITEBYTECODE='1')
    commits = [git('rev-parse', BASE)] + git('rev-list', '--reverse', '--first-parent', '--merges', BASE+'..HEAD').splitlines()
    rows = []
    cache = {}
    def check(revision):
        if revision in cache:
            return cache[revision]
        shutil.rmtree(snapshot, ignore_errors=True)
        snapshot.mkdir()
        archive = subprocess.Popen(['git', 'archive', revision, 'core', 'mac/OLMColorKey', TEST, GATE, ADAPTER], cwd=ROOT, stdout=subprocess.PIPE)
        subprocess.run(['tar', '-xf', '-', '-C', str(snapshot)], stdin=archive.stdout, check=True)
        archive.stdout.close()
        if archive.wait():
            raise RuntimeError('git archive failed')
        log = STATE / ('bisect-'+revision[:12]+'.log')
        command = [sys.executable, str(snapshot/GATE), '--run-test-file', str(snapshot/TEST)]
        start = time.monotonic()
        with log.open('w') as output:
            rc = subprocess.run(command, cwd=snapshot, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=120).returncode
        errors = [line.strip() for line in log.read_text().splitlines() if 'error:' in line or 'AssertionError' in line or 'RuntimeError:' in line]
        row = dict(commit=revision, subject=git('show', '-s', '--format=%s', revision), returncode=rc,
                   command=command, seconds=round(time.monotonic()-start, 3), errors=errors,
                   log=str(log.relative_to(ROOT)), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                   source_sha256=hashlib.sha256((snapshot/SOURCE).read_bytes()).hexdigest())
        rows.append(row)
        (STATE/'bisect-results.json').write_text(json.dumps(dict(rows=rows), indent=2)+'\n')
        print(revision[:12], rc, errors[:1], flush=True)
        if rc and not any("undeclared identifier 'PF_OutFlag2_SUPPORTS_THREADED_RENDERING'" in e for e in errors):
            raise RuntimeError('unexpected failure; cannot treat as target regression')
        cache[revision] = rc != 0
        return cache[revision]
    try:
        if check(commits[0]) or not check(commits[-1]):
            raise RuntimeError('bisection endpoints not good/bad')
        lo, hi = 0, len(commits)-1
        while hi-lo > 1:
            mid = (lo+hi)//2
            if check(commits[mid]): hi = mid
            else: lo = mid
        bad = commits[hi]
        parent = git('rev-parse', bad+'^1')
        if check(parent) or not check(bad):
            raise RuntimeError('adjacent first-parent boundary not reproduced')
        result = dict(base=commits[0], head=git('rev-parse', 'HEAD'), merge_count=len(commits)-1,
                      first_bad_merge=bad, good_first_parent=parent, rows=rows)
        (STATE/'bisect-results.json').write_text(json.dumps(result, indent=2)+'\n')
        print('FIRST_BAD_MERGE', bad, 'GOOD_FIRST_PARENT', parent, flush=True)
    finally:
        shutil.rmtree(snapshot, ignore_errors=True)

if __name__ == '__main__':
    main()
