#!/usr/bin/env python3
"""Seeded, budgeted public-path differential fuzzing. See README.md."""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import traceback
import threading

sys.dont_write_bytecode = True
from core import evaluate, load_corpus, mismatch_routes, save_corpus, sha, shrink, signature, unresolved_cleanup

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRATCH = ROOT/'orchestra/state/T02-fuzz-framework-radialblur'
CORPUS_LOCK = threading.Lock()
DEFAULT_CASE_TIMEOUT = 10


def main_checkout():
    if ROOT.parent.name == 'worktrees':
        return ROOT.parent.parent
    return ROOT


def default_worker():
    configured = os.environ.get('OLM_AEX_WORKER')
    if configured:
        return Path(configured)
    # F46: F45 plus imported UCRT double pow in default FMA mode.
    # F45 and older workers remain selectable with --worker / OLM_AEX_WORKER.
    retained = Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'
    return retained if retained.is_file() else None



def options():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plugin', required=True)
    p.add_argument('--color-sampler', choices=('default', 'float-v1'), default='default',
                   help='Smoother2 opt-in independent float colour fixture (S02 worker required)')
    p.add_argument('--reference-build', action='store_true', help='Build the faithful scalar/sequential implementation')
    p.add_argument('--geometry', choices=('default', 'realistic', 'realistic-v2'), default='default',
                   help='Opt-in sampler; requires a geometry-qualified candidate host')
    p.add_argument('--size-sampler', choices=('default', 'odd-even-v1'), default='default',
                   help='Opt-in independently sampled full-comp width/height parity')
    p.add_argument('--size-max-height', type=int, help='Opt-in height ceiling; otherwise --max-size')
    p.add_argument('--candidate', choices=('source', 'plugin-bundle'), default='source')
    p.add_argument('--plugin-bundle', type=Path)
    p.add_argument('--n', type=int, default=2000)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--budget-minutes', type=float, default=30)
    p.add_argument('--case-timeout', type=float,
                   help='Override corpus timeout on replay; otherwise default to 10 seconds')
    p.add_argument('--shrink-attempts', type=int, default=32)
    p.add_argument('--shrink-seconds', type=float, default=10)
    p.add_argument('--max-size', type=int, default=256)
    p.add_argument('--worker', type=Path,
                   help='Override the hash-bound corpus worker on replay')
    p.add_argument('--main', type=Path, default=main_checkout())
    p.add_argument('--scratch', type=Path, default=DEFAULT_SCRATCH)
    p.add_argument('--report', type=Path)
    p.add_argument('--corpus', type=Path)
    p.add_argument('--corpus-max-bytes', type=int, default=2_000_000)
    p.add_argument('--replay', type=Path, help='Replay a corpus JSON or directory; generation and shrinking are disabled')
    args = p.parse_args()
    if args.color_sampler != 'default' and args.plugin != 'olmsmoother2':
        p.error('--color-sampler float-v1 currently requires olmsmoother2')
    if args.reference_build and args.candidate != 'source':
        p.error('--reference-build compiles source hosts; it cannot change a supplied bundle')
    if args.candidate == 'plugin-bundle' and (not args.plugin_bundle or args.jobs != 1):
        p.error('plugin-bundle requires --plugin-bundle PATH --jobs 1')
    if not args.plugin.isidentifier():
        p.error('plugin must be an adapter module name')
    if not (args.n > 0 and 1 <= args.jobs <= 32 and args.budget_minutes > 0
            and (args.case_timeout is None or (math.isfinite(args.case_timeout) and args.case_timeout > 0))
            and args.corpus_max_bytes >= 0 and 1 <= args.max_size <= (256 if args.size_sampler == "default" else 4096) and args.shrink_attempts >= 0 and args.shrink_seconds >= 0):
        p.error('invalid count, jobs, time budget, shrink budget or size')
    if args.size_max_height is not None and (args.size_sampler == 'default' or not 1 <= args.size_max_height <= 4096):
        p.error('--size-max-height requires opt-in sampling and a bound in 1..4096')
    if not args.replay:
        args.worker = args.worker or (Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker' if args.geometry=='realistic-v2' else None) or (Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker' if args.geometry=='realistic' else default_worker())
        args.case_timeout = args.case_timeout if args.case_timeout is not None else DEFAULT_CASE_TIMEOUT
    if (args.worker is None and not args.replay) or (args.worker is not None and not args.worker.is_file()):
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


def replay_groups(args):
    """Validate every corpus binding before building or running any replay."""
    paths = sorted(args.replay.glob('*.json')) if args.replay.is_dir() else [args.replay]
    if not paths:
        raise ValueError(f'Replay corpus is empty: {args.replay}')
    groups, hashes = {}, {}
    for path in paths:
        saved = json.loads(path.read_text())
        provenance = saved.get('provenance', {})
        if not isinstance(provenance, dict):
            provenance = {}
        if args.worker is not None:
            worker = args.worker.resolve()
        else:
            recorded = provenance.get('worker_path')
            expected = provenance.get('worker_sha256')
            if not isinstance(recorded, str) or not recorded or not isinstance(expected, str) or not expected:
                raise ValueError(f'{path}: missing provenance worker_path or worker_sha256; use --worker to override')
            worker = Path(recorded).resolve()
            if worker not in hashes:
                try:
                    with worker.open('rb') as stream:
                        hashes[worker] = hashlib.file_digest(stream, 'sha256').hexdigest()
                except OSError as exc:
                    raise ValueError(f'{path}: recorded worker unavailable: {worker}; use --worker to override') from exc
            if hashes[worker] != expected:
                raise ValueError(f'{path}: worker SHA-256 mismatch for {worker}: expected {expected}, '
                                 f'got {hashes[worker]}; use --worker to override')
        timeout = args.case_timeout
        if timeout is None:
            timeout = provenance.get('case_timeout_seconds', DEFAULT_CASE_TIMEOUT)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError(f'{path}: invalid case_timeout_seconds: {timeout!r}; use --case-timeout to override')
        groups.setdefault((worker, timeout), []).append(path)
    return groups


def prepare(adapter, scratch, deadline, timeout):
    provenance = adapter.prepare(scratch, deadline)
    provenance['case_timeout_seconds'] = timeout
    print('PREPARED', json.dumps({'calibration_matches':sum(c['matches_retained'] for c in provenance.get('calibration', [])),
                                  'worker':provenance.get('worker_sha256'),
                                  'case_timeout_seconds':timeout}), flush=True)
    return provenance


def replay(adapter_type, args, scratch, deadline, report):
    groups = replay_groups(args)
    report.update(replay=str(args.replay), replays=[], replay_groups=[],
                  requested=sum(len(paths) for paths in groups.values()))
    timeouts = {timeout for _, timeout in groups}
    report['case_timeout_seconds'] = next(iter(timeouts)) if len(timeouts) == 1 else None
    for (worker, timeout), paths in groups.items():
        if time.monotonic() >= deadline:
            break
        group_args = argparse.Namespace(**vars(args))
        group_args.worker, group_args.case_timeout = worker, timeout
        adapter = adapter_type(group_args)
        with tempfile.TemporaryDirectory(prefix='group_', dir=scratch) as name:
            directory = Path(name)
            provenance = prepare(adapter, directory, deadline, timeout)
            group_index = len(report['replay_groups'])
            report['replay_groups'].append({'provenance':provenance, 'paths':list(map(str, paths))})
            # Preserve the existing single-worker report interface without
            # claiming one group's provenance applies to a mixed replay.
            report['provenance'] = provenance if len(groups) == 1 else None
            for path in paths:
                if time.monotonic() >= deadline:
                    break
                case, saved = load_corpus(path, adapter)
                from geometry import require_host
                require_host(adapter, case)
                with tempfile.TemporaryDirectory(prefix='replay_', dir=directory) as name:
                    observed = evaluate(adapter, case, Path(name), deadline)
                report['replays'].append({'path':str(path), 'result':observed, 'group':group_index,
                                          'matches_saved':observed == saved['result']})
    report['replays'].sort(key=lambda row:row['path'])
    complete = len(report['replays']) == report['requested']
    matches = complete and all(row['matches_saved'] for row in report['replays'])
    report.update(replay_matches_saved=matches, completed=len(report['replays']),
                  status='replay_complete' if complete else 'budget_exhausted')
    return 0 if matches else 1


def run_one(adapter, seed, index, scratch, deadline, args, provenance):
    started = time.monotonic()
    from geometry import sample, require_host
    case = sample(adapter.generate(seed, index), getattr(args, 'geometry', 'default'))
    require_host(adapter, case)
    with tempfile.TemporaryDirectory(prefix=f'case_{index}_', dir=scratch) as name:
        directory = Path(name)
        attribution = {}
        original = evaluate(adapter, case, directory, deadline, attribution)
        row = {k:v for k,v in case.items() if k != 'pixels'}
        row.update(input_sha256=sha(case['pixels']), result=original)
        cleanup_failures = unresolved_cleanup(original)
        if attribution:
            row['refusal_guards'] = attribution
        if mismatch_routes(original):
            reduced, observed, reduction = shrink(adapter, case, original, directory,
                min(deadline, time.monotonic()+args.shrink_seconds), args.shrink_attempts)
            cleanup_failures.extend(reduction.get('unresolved_cleanup', []))
            key = signature(adapter, reduced, observed)
            filename = f'seed{seed}_case{index:06d}_{sha(key.encode())[:12]}.json'
            path = args.corpus/filename
            staged = directory/filename
            save_corpus(staged, adapter, case, reduced, observed, reduction, provenance)
            with CORPUS_LOCK:
                prior_size = path.stat().st_size if path.exists() else 0
                retained = disk_bytes(args.corpus) - prior_size + staged.stat().st_size <= args.corpus_max_bytes
                if retained:
                    staged.replace(path)
            row.update(cluster=key, corpus=str(path.relative_to(ROOT)) if retained else None,
                       corpus_retained=retained, corpus_omission=None if retained else 'byte cap',
                       shrunk_geometry=reduced['geometry'], shrink_attempts=reduction['attempts'],
                       shrink_accepted=len(reduction['accepted']))
        if cleanup_failures:
            row.update(status='unresolved', reason='timeout cleanup could not be confirmed',
                       unresolved_cleanup=cleanup_failures)
        row['elapsed_seconds'] = round(time.monotonic()-started, 4)
        return row


def summarize(rows):
    counts = Counter()
    clusters = {}
    for row in rows:
        if 'worker_error' in row:
            counts['framework_error'] += 1
            continue
        if row.get('status') == 'unresolved':
            counts['unresolved_cases'] += 1
        result = row['result']
        counts['aex_'+result['oracle']['status']] += 1
        for route, oracle in result.get('oracles', {}).items():
            counts['aex_'+route+'_'+oracle['status']] += 1
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
    adapter_type = importlib.import_module('adapters.'+('plugin_bundle' if args.candidate == 'plugin-bundle' else args.plugin)).Adapter
    report = {'schema':'olm-fuzz-report/1', 'plugin':args.plugin, 'generator_version':adapter_type.generator_version,
              'started_utc':datetime.now(timezone.utc).isoformat(),
              'seed':args.seed, 'requested':args.n, 'jobs':args.jobs,
              'budget_minutes':args.budget_minutes, 'case_timeout_seconds':args.case_timeout,
              'max_size':args.max_size, 'color_sampler':args.color_sampler, 'size_sampler':args.size_sampler, 'size_max_height':args.size_max_height, 'shrink_attempts':args.shrink_attempts,
              'shrink_seconds':args.shrink_seconds, 'corpus_max_bytes':args.corpus_max_bytes, 'cases':[],
              'claims_not_made':['Signature clusters are not proven root causes.',
                                 'Finite random coverage is not all-input compatibility.',
                                 'This is CPU AEX emulation vs a fake SDK host, not native AE/Windows UCRT validation.',
                                 'AEX packed strides vs Mac random padding does not establish AEX odd-stride support.']}
    exitcode = 0
    with tempfile.TemporaryDirectory(prefix='run_', dir=args.scratch) as name:
        scratch = Path(name)
        try:
            if args.replay:
                exitcode = replay(adapter_type, args, scratch, deadline, report)
            else:
                adapter = adapter_type(args)
                if args.geometry != 'default':
                    from geometry import require_host, VERSION
                    require_host(adapter, {'geometry_sampler': 'realistic-v2' if args.geometry=='realistic-v2' else VERSION})
                report['provenance'] = prepare(adapter, scratch, deadline, args.case_timeout)
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
        except Exception as exc:
            report.update(status='setup_error', error=traceback.format_exc()[-6000:])
            print(f'ERROR: {exc}', file=sys.stderr, flush=True)
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
