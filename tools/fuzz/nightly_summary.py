#!/usr/bin/env python3
"""Run bounded overnight campaigns, or summarize a nightly date directory."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from core import (apply_operation, evaluate, proposals, save_corpus, sha,
                  unresolved_cleanup)
from geometry import require_host, sample
from run import ROOT, default_worker, main_checkout, disk_bytes
from sweep_T15b import PLUGINS, category, failure_key

SAMPLERS = ('default', 'realistic', 'realistic-v2', 'odd-even-v1')
LIMIT = 1_800_000_000  # reserve 200 MB below the requested decimal 2 GB
STOP = False


def interrupted(signum, frame):
    # core.command catches BaseException and reaps its process group.
    global STOP
    STOP = True
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    raise KeyboardInterrupt


def write(path, value):
    stage = path.with_suffix('.writing')
    stage.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    stage.replace(path)


def memory_ready(deadline):
    while not STOP and time.monotonic() < deadline:
        result = subprocess.run(['/usr/bin/memory_pressure'], capture_output=True,
                                text=True, timeout=5, check=True)
        match = re.search(r'System-wide memory free percentage:\s*(\d+)%', result.stdout)
        if not match:
            raise RuntimeError('memory_pressure did not report a free percentage')
        if int(match[1]) >= 30:
            return True
        print('Memory below 30%; pausing', flush=True)
        time.sleep(min(5, max(0, deadline-time.monotonic())))
    return False


def summary(directory):
    counts = defaultdict(Counter)
    reports = sorted(directory.glob('run-*.json'))
    errors = []
    witnesses = []
    for path in reports:
        r = json.loads(path.read_text())
        counts[r['plugin'], r['sampler']].update(r['counts'])
        if r.get('error'):
            errors.append(f"{path.name}: {r['error']}")
        witnesses.extend(r.get('witnesses', []))
    lines = ['# Nightly fuzz summary', '',
             'E = exact; M = mismatch; R = Mac refusal with successful AEX; U = uncompared/unavailable.',
             'Zero rows mean no completed observations, not a pass. Counts exclude shrinking.', '',
             '| Plugin | Sampler | E | M | R | U |', '|---|---|---:|---:|---:|---:|']
    for plugin in PLUGINS:
        for sampler in SAMPLERS:
            c = counts[plugin, sampler]
            lines.append(f'| {plugin} | {sampler} | ' + ' | '.join(str(c[k]) for k in 'EMRU') + ' |')
    lines += ['', '## New witnesses', '',
              'New means first retained failure signature in this date directory; not necessarily new to the repository.']
    for w in witnesses:
        lines += ['', f"- `{w['path']}`: {w['failure_class']}; first difference/status: `{json.dumps(w['detail'], sort_keys=True)}`"]
    if not witnesses:
        lines += ['', 'None retained.']
    if errors:
        lines += ['', '## Errors', ''] + ['- '+e for e in errors]
    session_paths = sorted(directory.glob('session-*.json'))
    for path in session_paths:
        lines += ['', 'Session: `' + json.dumps(json.loads(path.read_text()), sort_keys=True) + '`']
    text = '\n'.join(lines) + '\n'
    (directory/'summary.md').write_text(text)
    return text


def campaign(directory, ordinal, plugin, sampler, seed, deadline, *, case_limit=100000):
    route = 'classic' if plugin == 'olmsmoother' else 'smart'
    report_path = directory/f'run-{ordinal:06d}.json'
    r = dict(plugin=plugin, sampler=sampler, seed=seed, route=route, counts={},
             witnesses=[], requested=case_limit, status='running')
    stage = directory/'scratch'
    stage.mkdir()
    os.environ.update(TMPDIR=str(stage), TMP=str(stage), TEMP=str(stage))
    tempfile.tempdir = str(stage)
    started = time.monotonic()
    try:
        geometry = 'realistic' if sampler == 'odd-even-v1' else sampler
        bound = json.loads((ROOT/f'orchestra/reports/T15b-evidence/{plugin}-summary.json').read_text())
        worker = (Path.home()/'.cache/olm-emu'/('worker-F53-geom' if geometry == 'realistic-v2' else 'worker-F52c-geom')/'aex-guest-worker') if geometry != 'default' else default_worker()
        args = SimpleNamespace(main=main_checkout(), worker=worker,
                               max_size=bound['maximum'] if sampler == 'odd-even-v1' else 256,
                               size_sampler='odd-even-v1' if sampler == 'odd-even-v1' else 'default',
                               size_max_height=bound.get('height_maximum') if sampler == 'odd-even-v1' else None,
                               case_timeout=10, reference_build=False)
        a = importlib.import_module('adapters.'+plugin).Adapter(args)
        require_host(a, {'geometry_sampler': 'realistic-v2' if geometry == 'realistic-v2' else 'realistic-v1'} if geometry != 'default' else {})
        a.routes = (route,)
        a.oracle_routes = {route: route}
        r['provenance'] = a.prepare(stage, deadline)
        r['provenance']['case_timeout_seconds'] = 10
        r.update(max_size=args.max_size, size_max_height=args.size_max_height,
                 worker=str(worker), jobs=1)
        write(report_path, r)
        for index in range(r['requested']):
            if STOP or time.monotonic() >= deadline or disk_bytes(directory) >= LIMIT:
                break
            if not memory_ready(deadline):
                break
            case = sample(a.generate(seed, index), geometry)
            require_host(a, case)
            a.routes = (route,)
            a.oracle_routes = {route: route}
            with tempfile.TemporaryDirectory(dir=stage) as name:
                case_dir = Path(name)
                attr = {}
                result = evaluate(a, case, case_dir, deadline, attr)
                k = category(result, route)
                r['counts'][k] = r['counts'].get(k, 0) + 1
                if unresolved_cleanup(result):
                    raise RuntimeError('unresolved child cleanup: '+str(unresolved_cleanup(result)))
                key = failure_key(result, route, attr, case)
                if key:
                    identifier = sha(f'{plugin}:{sampler}:{key}'.encode())[:24]
                    target = directory/'witnesses'/f'{identifier}.json'
                    if not target.exists():
                        reduced, observed, accepted, attempts = case, result, [], 0
                        until = min(deadline, time.monotonic()+20)
                        while attempts < 32 and time.monotonic() < until:
                            improved = False
                            for op in proposals(a, reduced):
                                if attempts >= 32 or time.monotonic() >= until:
                                    break
                                candidate = apply_operation(a, reduced, op)
                                if candidate == reduced:
                                    continue
                                attempts += 1
                                attrs = {}
                                rr = evaluate(a, candidate, case_dir, until, attrs)
                                if unresolved_cleanup(rr):
                                    raise RuntimeError('unresolved cleanup during shrinking')
                                if failure_key(rr, route, attrs, candidate) == key:
                                    reduced, observed = candidate, rr
                                    accepted.append(op)
                                    improved = True
                                    break
                            if not improved:
                                break
                        reduction = dict(attempts=attempts, accepted=accepted, bounded=True, minimality_claimed=False)
                        staged = case_dir/'witness.json'
                        save_corpus(staged, a, case, reduced, observed, reduction, r['provenance'])
                        staged.replace(target)
                        r['witnesses'].append(dict(path=str(target.relative_to(directory)), failure_class=key,
                                                   detail=observed['routes'][route]))
                # Atomic progress keeps completed counts on interruption.
                write(report_path, r)
        r['status'] = 'budget_exhausted' if time.monotonic() >= deadline else 'complete'
    except KeyboardInterrupt:
        r['status'] = 'interrupted'
        raise
    except Exception as exc:
        if time.monotonic() >= deadline:
            r.update(status='budget_exhausted', deadline_detail=f'{type(exc).__name__}: {exc}')
        else:
            r.update(status='error', error=f'{type(exc).__name__}: {exc}')
            raise
    finally:
        r['elapsed_seconds'] = round(time.monotonic()-started, 3)
        write(report_path, r)
        shutil.rmtree(stage)


def run(args):
    directory = ROOT/'orchestra/state/nightly'/datetime.now().strftime('%Y%m%d')
    directory.mkdir(parents=True, exist_ok=True)
    # A lock prevents concurrent invocations and accidental scratch deletion.
    import fcntl
    with (directory/'.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (directory/'scratch').exists():
            raise RuntimeError('scratch from an interrupted external kill exists; inspect processes before removing it')
        (directory/'witnesses').mkdir(exist_ok=True)
        signal.signal(signal.SIGINT, interrupted)
        signal.signal(signal.SIGTERM, interrupted)
        start = time.monotonic()
        deadline = start + args.hours*3600
        stamp = datetime.now().strftime('%Y%m%dT%H%M%S%f')
        session = dict(start=stamp, hours=args.hours, jobs_limit=args.jobs, actual_jobs=1, status='running')
        code = 0
        try:
            ordinal = max([int(p.stem.split('-')[1]) for p in directory.glob('run-*.json')], default=-1)+1
            while time.monotonic() < deadline:
                if disk_bytes(directory) >= LIMIT:
                    session['status'] = 'disk_limit'
                    break
                if not memory_ready(deadline):
                    break
                plugin = PLUGINS[ordinal % len(PLUGINS)]
                sampler = SAMPLERS[(ordinal//len(PLUGINS)) % len(SAMPLERS)]
                seed = int(sha(f'{stamp}:{ordinal}'.encode())[:15], 16)
                print(f'RUN {ordinal} {plugin} {sampler} seed={seed}', flush=True)
                campaign(directory, ordinal, plugin, sampler, seed, min(deadline, time.monotonic()+600))
                ordinal += 1
            if session['status'] == 'running':
                session['status'] = 'deadline'
        except KeyboardInterrupt:
            session['status'] = 'interrupted'
        except Exception as exc:
            session.update(status='error', error=f'{type(exc).__name__}: {exc}')
            code = 1
        finally:
            session['elapsed_seconds'] = round(time.monotonic()-start, 3)
            session['retained_bytes'] = disk_bytes(directory)
            write(directory/f'session-{stamp}.json', session)
            print(summary(directory), flush=True)
        return code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', nargs='?', type=Path)
    p.add_argument('--run', action='store_true')
    p.add_argument('--hours', type=float, default=7)
    p.add_argument('--jobs', type=int, default=1)
    args = p.parse_args()
    if not math.isfinite(args.hours) or args.hours <= 0 or args.jobs < 1:
        p.error('hours must be finite and positive; jobs must be positive')
    if args.run:
        return run(args)
    if args.directory is None:
        p.error('provide a nightly date directory, or --run')
    print(summary(args.directory))
    return 0


if __name__ == '__main__':
    sys.exit(main())
