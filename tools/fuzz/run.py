#!/usr/bin/env python3
"""Seeded, budgeted public-path differential fuzzing. See README.md."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import traceback

sys.dont_write_bytecode = True
from core import evaluate, load_corpus, mismatch_routes, save_corpus, sha, shrink, signature

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRATCH = ROOT/'orchestra/state/T02-fuzz-framework-radialblur'


def main_checkout():
    if ROOT.parent.name == 'worktrees':
        return ROOT.parent.parent
    return ROOT


def default_worker():
    configured = os.environ.get('OLM_AEX_WORKER') or shutil.which('aex-guest-worker')
    if configured:
        return Path(configured)
    # Retained local worker discovered on this workstation; always hash-bound.
    retained = Path.home()/'Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker'
    return retained if retained.is_file() else None


def options():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plugin', required=True)
    p.add_argument('--n', type=int, default=2000)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--budget-minutes', type=float, default=30)
    p.add_argument('--case-timeout', type=float, default=10)
    p.add_argument('--shrink-attempts', type=int, default=32)
    p.add_argument('--shrink-seconds', type=float, default=10)
    p.add_argument('--max-size', type=int, default=256)
    p.add_argument('--worker', type=Path, default=default_worker())
    p.add_argument('--main', type=Path, default=main_checkout())
    p.add_argument('--scratch', type=Path, default=DEFAULT_SCRATCH)
    p.add_argument('--report', type=Path)
    p.add_argument('--corpus', type=Path)
    p.add_argument('--replay', type=Path, help='Replay a corpus JSON or directory; generation and shrinking are disabled')
    args = p.parse_args()
    if not args.plugin.isidentifier():
        p.error('plugin must be an adapter module name')
    if not (args.n > 0 and 1 <= args.jobs <= 32 and args.budget_minutes > 0 and args.case_timeout > 0
            and 1 <= args.max_size <= 256 and args.shrink_attempts >= 0 and args.shrink_seconds >= 0):
        p.error('invalid count, jobs, time budget, shrink budget or size')
    if args.worker is None or not args.worker.is_file():
        p.error('set --worker or OLM_AEX_WORKER to the retained AEXCompat executable')
    args.scratch = args.scratch.resolve()
    if not args.scratch.is_relative_to(ROOT/'orchestra/state'):
        p.error('scratch must be inside this worktree/orchestra/state')
    date = datetime.now().strftime('%Y%m%d')
    suffix = '_replay' if args.replay else ''
    args.report = (args.report or ROOT/f'reports/fuzz/{args.plugin}{suffix}_{date}.json').resolve()
    args.corpus = (args.corpus or ROOT/f'tests/fuzz_corpus/{args.plugin}').resolve()
    for path in (args.report, args.corpus):
        if not path.is_relative_to(ROOT):
            p.error('report and corpus must stay inside this worktree')
    return args


def disk_bytes(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and not p.is_symlink())


def run_one(adapter, seed, index, scratch, deadline, args, provenance):
    started = time.monotonic()
    case = adapter.generate(seed, index)
    with tempfile.TemporaryDirectory(prefix=f'case_{index}_', dir=scratch) as name:
        directory = Path(name)
        attribution = {}
        original = evaluate(adapter, case, directory, deadline, attribution)
        row = {k:v for k,v in case.items() if k != 'pixels'}
        row.update(input_sha256=sha(case['pixels']), result=original)
        if attribution:
            row['refusal_guards'] = attribution
        if mismatch_routes(original):
            reduced, observed, reduction = shrink(adapter, case, original, directory,
                min(deadline, time.monotonic()+args.shrink_seconds), args.shrink_attempts)
            key = signature(adapter, reduced, observed)
            filename = f'seed{seed}_case{index:06d}_{sha(key.encode())[:12]}.json'
            path = args.corpus/filename
            save_corpus(path, adapter, case, reduced, observed, reduction, provenance)
            row.update(cluster=key, corpus=str(path.relative_to(ROOT)),
                       shrunk_geometry=reduced['geometry'], shrink_attempts=reduction['attempts'],
                       shrink_accepted=len(reduction['accepted']))
        row['elapsed_seconds'] = round(time.monotonic()-started, 4)
        return row


def summarize(rows):
    counts = Counter()
    clusters = {}
    for row in rows:
        if 'worker_error' in row:
            counts['framework_error'] += 1
            continue
        result = row['result']
        counts['aex_'+result['oracle']['status']] += 1
        statuses = [r['status'] for r in result['routes'].values()]
        counts['both_routes_exact'] += all(s=='exact' for s in statuses)
        counts['pixel_mismatch_cases'] += 'mismatch' in statuses
        for route, value in result['routes'].items():
            counts[route+'_'+value['status']] += 1
        if 'cluster' in row:
            cluster = clusters.setdefault(row['cluster'], {'count':0, 'case_indices':[], 'corpus':[]})
            cluster['count'] += 1
            cluster['case_indices'].append(row['index'])
            cluster['corpus'].append(row['corpus'])
    return dict(counts), clusters


def main():
    args = options()
    started = time.monotonic()
    deadline = started + args.budget_minutes*60
    args.scratch.mkdir(parents=True, exist_ok=True)
    if disk_bytes(args.scratch) > 4*1024**3:
        raise SystemExit('Scratch already exceeds 4 GiB; remove regenerable outputs before running')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.corpus.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch),
                      PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(args.scratch)
    adapter = importlib.import_module('adapters.'+args.plugin).Adapter(args)
    report = {'schema':'olm-fuzz-report/1', 'plugin':args.plugin, 'generator_version':adapter.generator_version,
              'started_utc':datetime.now(timezone.utc).isoformat(),
              'seed':args.seed, 'requested':args.n, 'jobs':args.jobs,
              'budget_minutes':args.budget_minutes, 'case_timeout_seconds':args.case_timeout,
              'max_size':args.max_size, 'shrink_attempts':args.shrink_attempts,
              'shrink_seconds':args.shrink_seconds, 'cases':[],
              'claims_not_made':['Signature clusters are not proven root causes.',
                                 'Finite random coverage is not all-input compatibility.',
                                 'This is CPU AEX emulation vs a fake SDK host, not native AE/Windows UCRT validation.',
                                 'AEX packed strides vs Mac random padding does not establish AEX odd-stride support.']}
    exitcode = 0
    with tempfile.TemporaryDirectory(prefix='run_', dir=args.scratch) as name:
        scratch = Path(name)
        try:
            report['provenance'] = adapter.prepare(scratch, deadline)
            print('PREPARED', json.dumps({'calibration_matches':sum(c['matches_retained'] for c in report['provenance'].get('calibration', [])),
                                          'worker':report['provenance'].get('worker_sha256')}), flush=True)
            if args.replay:
                paths = sorted(args.replay.glob('*.json')) if args.replay.is_dir() else [args.replay]
                if not paths:
                    raise ValueError('Replay corpus is empty')
                replays = []
                for path in paths:
                    if time.monotonic() >= deadline:
                        break
                    case, saved = load_corpus(path, adapter)
                    with tempfile.TemporaryDirectory(prefix='replay_',dir=scratch) as directory:
                        observed = evaluate(adapter, case, Path(directory), deadline)
                    replays.append({'path':str(path), 'result':observed,
                                    'matches_saved':observed == saved['result']})
                matches = len(replays)==len(paths) and all(row['matches_saved'] for row in replays)
                report.update(replay=str(args.replay), replays=replays, replay_matches_saved=matches,
                              completed=len(replays), requested=len(paths),
                              status='replay_complete' if len(replays)==len(paths) else 'budget_exhausted')
                exitcode = 0 if matches else 1
            else:
                next_index = 0
                with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                    pending = {}
                    while next_index < args.n or pending:
                        while len(pending) < args.jobs and next_index < args.n and time.monotonic() < deadline:
                            future = pool.submit(run_one, adapter, args.seed, next_index, scratch,
                                                 deadline, args, report['provenance'])
                            pending[future] = next_index
                            next_index += 1
                        if not pending:
                            break
                        ready, _ = wait(pending, timeout=.25, return_when=FIRST_COMPLETED)
                        for future in ready:
                            index = pending.pop(future)
                            try:
                                report['cases'].append(future.result())
                            except Exception:
                                report['cases'].append({'index':index, 'worker_error':traceback.format_exc()[-3000:]})
                                exitcode = 2
                            n = len(report['cases'])
                            if n % 25 == 0 or n == args.n:
                                counts, clusters = summarize(report['cases'])
                                print('PROGRESS', n, json.dumps(counts, sort_keys=True), 'clusters', len(clusters), flush=True)
                report['cases'].sort(key=lambda row:row['index'])
                report['completed'] = len(report['cases'])
                report['summary'], report['clusters'] = summarize(report['cases'])
                report['cluster_count'] = len(report['clusters'])
                report['status'] = 'complete' if len(report['cases']) == args.n else 'budget_exhausted'
        except Exception:
            report.update(status='setup_error', error=traceback.format_exc()[-6000:])
            exitcode = 2
        report['elapsed_seconds'] = round(time.monotonic()-started, 4)
        report['deadline_reached'] = time.monotonic() >= deadline
        report['scratch_bytes_before_cleanup'] = disk_bytes(args.scratch)
        report['framework_sha256'] = {str(p.relative_to(ROOT)):sha(p.read_bytes())
                                      for p in sorted((ROOT/'tools/fuzz').rglob('*.py'))}
        args.report.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print('RESULT', report['status'], report.get('summary',{}), 'report', args.report, flush=True)
    return exitcode


if __name__ == '__main__':
    sys.exit(main())
