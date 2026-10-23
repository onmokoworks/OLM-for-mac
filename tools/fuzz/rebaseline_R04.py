#!/usr/bin/env python3
"""Replay all Kira corpora; optionally migrate measured results with R04 history."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/R04-assertion-drift-and-corpus'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--use-reports', action='store_true', help='Use this checkout’s completed replay reports')
    args = parser.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH), OLM_TEST_JOBS='2')
    directories = sorted({p.parent for p in (ROOT/'tests/fuzz_corpus').rglob('*.json') if 'kirakira' in str(p)})
    changes = []
    counts = Counter()
    reports = []
    for directory in directories:
        report_path = SCRATCH/(directory.name+'.json')
        if not args.use_reports:
            command = [sys.executable, str(ROOT/'tools/fuzz/run.py'), '--plugin', 'olmkirakira',
                       '--replay', str(directory), '--jobs', '1', '--budget-minutes', '120',
                       '--scratch', str(SCRATCH/'replay-build'), '--report', str(report_path)]
            with (SCRATCH/(directory.name+'.log')).open('w') as log:
                rc = subprocess.call(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            if rc not in (0, 1):
                raise RuntimeError(f'replay exited {rc}: {report_path}')
        report = json.loads(report_path.read_text())
        assert report['status'] == 'replay_complete'
        assert report['completed'] == report['requested']
        for row in report['replays']:
            path = Path(row['path'])
            saved = json.loads(path.read_text())['result']
            observed = row['result']
            assert saved['oracle'] == observed['oracle'], path
            assert observed['routes']['smart']['status'] == 'exact', path
            assert 'oracles' in observed, path
            for route, before in saved['routes'].items():
                after = observed['routes'][route]
                counts[(route, before['status'], after['status'])] += 1
            if saved != observed:
                changes.append({'path':str(path.relative_to(ROOT)),
                                'before':saved, 'after':observed})
        reports.append((directory, report_path))
    # Validate the complete inventory before applying any directory.
    if args.apply:
        for directory, report_path in reports:
            with (SCRATCH/(directory.name+'-rebaseline.log')).open('w') as log:
                subprocess.run([sys.executable, str(ROOT/'tools/fuzz/rebaseline_corpus.py'),
                                '--plugin', 'olmkirakira', '--corpus', str(directory),
                                '--report', str(report_path), '--production-rebaseline', 'R04'],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    evidence = {'applied':args.apply, 'changes':changes,
                'transitions':[dict(route=k[0], before=k[1], after=k[2], count=v) for k,v in sorted(counts.items())],
                'reports':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for _,p in reports}}
    target = ROOT/'orchestra/reports/R04-corpus-transitions.json' if args.apply else SCRATCH/'corpus-audit.json'
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'changed':len(changes), 'transitions':evidence['transitions']}))


if __name__ == '__main__':
    main()
