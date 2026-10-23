#!/usr/bin/env python3
"""Run one integration command, logging five-second cross-PGID samples."""
import json, os, signal, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/I02-integration-finish'

def table():
    out = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,pgid=,rss=,command='], text=True)
    rows = {}
    for line in out.splitlines():
        p = line.split(None, 4)
        if len(p) == 5:
            rows[int(p[0])] = dict(pid=int(p[0]), ppid=int(p[1]), pgid=int(p[2]), rss_kib=int(p[3]), command=p[4])
    return rows

def descendants(rows, root):
    ids = {root}
    while True:
        new = ids | {p for p, r in rows.items() if r['ppid'] in ids}
        if new == ids:
            return ids - {root}
        ids = new

def main():
    stage, *cmd = sys.argv[1:]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OLM_TEST_JOBS='2', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
               TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH),
               OLM_FUZZ_INTEGRATION='1', OLM_FUZZ_TEST_SCRATCH=str(SCRATCH / 'framework'))
    known_groups = set()
    started = time.time()
    stopped = None
    with (SCRATCH / f'{stage}.log').open('w') as log, (SCRATCH / f'{stage}-samples.jsonl').open('w') as samples:
        proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        known_groups.add(proc.pid)
        try:
            while proc.poll() is None:
                rows = table()
                ids = descendants(rows, proc.pid) | {proc.pid}
                owned = [rows[p] for p in ids if p in rows]
                known_groups.update(r['pgid'] for r in owned)
                runners = [r for r in owned if 'run_olm_mac_fixed_fixture_regression_20260805.py' in r['command']]
                groups = {}
                for runner in runners:
                    result = subprocess.run(['pgrep', '-g', str(runner['pgid'])], capture_output=True, text=True)
                    groups[str(runner['pgid'])] = len(result.stdout.splitlines())
                record = dict(time=time.time(), elapsed=time.time()-started, processes=owned, runner_group_counts=groups)
                samples.write(json.dumps(record)+'\n'); samples.flush()
                if len(ids)-1 > 100:
                    stopped = 'more_than_100_descendants'
                    break
                time.sleep(5)
        finally:
            # Also reap escaped-session children and anything left after normal exit.
            rows = table()
            ids = descendants(rows, proc.pid) | {proc.pid}
            known_groups.update(rows[p]['pgid'] for p in ids if p in rows)
            for pgid in known_groups:
                if pgid == os.getpgrp():
                    continue
                try: os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError: pass
            time.sleep(1)
            for pgid in known_groups:
                if pgid == os.getpgrp(): continue
                try: os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError: pass
            proc.wait()
    result = dict(stage=stage, command=cmd, exit=proc.returncode, stop=stopped, elapsed=time.time()-started,
                  head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip())
    (SCRATCH / f'{stage}-result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
    return 1 if stopped else 0

if __name__ == '__main__':
    sys.exit(main())
