#!/usr/bin/env python3
"""Compare C45 zero reads with the pre-C45 build and default public AEX oracle."""
import argparse
from collections import Counter
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
from core import evaluate, save_corpus, sha
from run import default_worker, main_checkout

ROOT = Path(__file__).resolve().parents[2]
BASE = 'f4964bafa4286ea730f72310ca0fe74209d28d8f'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plugin', choices=['radialblur', 'olmdirectionalblur'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--seeds', nargs='+', type=int, default=[1, 45101, 45102])
    ap.add_argument('--n', type=int, default=300)
    ap.add_argument('--jobs', type=int, choices=[1], default=1)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C45-original-oob-noise-table')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_TEST_JOBS='1')
    tempfile.tempdir = str(out)
    mod = importlib.import_module('adapters.'+args.plugin)
    options = SimpleNamespace(main=main_checkout(), worker=default_worker(), max_size=256, case_timeout=10)
    deadline = time.monotonic()+6*3600
    # Snapshot only production dependencies; original binaries and SDK stay in MAIN.
    snapshot = out/'snapshot'
    for folder in ('core', 'mac'):
        shutil.copytree(ROOT/folder, snapshot/folder)
    (snapshot/'ucrtmath').symlink_to(ROOT/'ucrtmath', target_is_directory=True)
    old_header = subprocess.check_output(['git', 'show', BASE+':core/dblur_noise.h'], cwd=ROOT)
    (snapshot/'core/dblur_noise.h').write_bytes(old_header)
    baseline = mod.Adapter(options)
    build_before = out/'before'; build_before.mkdir()
    if args.plugin == 'radialblur':
        original = mod.public.SOURCE
        mod.public.SOURCE = snapshot/original.relative_to(ROOT)
        before_provenance = baseline.prepare(build_before, deadline)
        mod.public.SOURCE = original
    else:
        original, cores = mod.SOURCE, mod.CORES
        mod.SOURCE = snapshot/original.relative_to(ROOT)
        mod.CORES = [snapshot/p.relative_to(ROOT) for p in cores]
        before_provenance = baseline.prepare(build_before, deadline)
        mod.SOURCE, mod.CORES = original, cores
    before_provenance['noise_header_sha256'] = sha(old_header)
    if 'core_sha256' in before_provenance:
        before_provenance['core_sha256'] = sha(old_header)
    after = mod.Adapter(options)
    build_after = out/'after'; build_after.mkdir()
    provenance = after.prepare(build_after, deadline)
    provenance['noise_header_sha256'] = sha((ROOT/'core/dblur_noise.h').read_bytes())
    provenance['case_timeout_seconds'] = 10
    failures = False
    for seed in args.seeds:
        report = dict(plugin=args.plugin, seed=seed, requested=args.n, jobs=1,
                      baseline_ref=BASE, baseline_provenance=before_provenance,
                      provenance=provenance, cases=[], gains=[], lost_exact=[], mismatches=[])
        for index in range(args.n):
            case = after.generate(seed, index)
            with tempfile.TemporaryDirectory(dir=out) as name:
                directory = Path(name)
                attribution = {}
                result = evaluate(after, case, directory, deadline, attribution)
                before = {}
                for route in after.routes:
                    actual, raw, *guards = baseline.candidate(case, directory, route, deadline)
                    actual = dict(actual)
                    if actual['status'] == 'ok':
                        actual['raw_sha256'] = sha(raw)
                        oracle = result.get('oracles', {}).get(route, result['oracle'])
                        actual['status'] = ('exact' if sha(raw)==oracle['raw_sha256'] else 'mismatch') if oracle['status']=='ok' else 'uncompared'
                    before[route] = dict(result=actual, guards=guards)
                    observed = result['routes'][route]
                    if actual['status']=='exact' and (observed['status']!='exact' or actual['raw_sha256']!=observed['raw_sha256']):
                        report['lost_exact'].append([index,route])
                    if observed['status']=='mismatch':
                        report['mismatches'].append([index,route])
                    if actual['status']=='refusal' and observed['status']=='exact':
                        report['gains'].append([index,route])
                row = {k:v for k,v in case.items() if k!='pixels'}
                row.update(input_sha256=sha(case['pixels']), result=result, before=before, refusal_guards=attribution)
                report['cases'].append(row)
                if any(i==index for i,r in report['gains']):
                    witnesses = out/'witnesses'; witnesses.mkdir(exist_ok=True)
                    save_corpus(witnesses/f'C45_seed{seed}_case{index:06d}.json', after, case, case, result,
                                dict(accepted=[], attempts=0), dict(provenance, C45='Original out-of-range noise-table reads use deterministic zero in the port; refusal to exact.', baseline=before))
            if (index+1)%25==0:
                print(seed,index+1,'gains',len(report['gains']),'mismatches',len(report['mismatches']),'lost',report['lost_exact'],flush=True)
        report['counts'] = {r:dict(Counter(c['result']['routes'][r]['status'] for c in report['cases'])) for r in after.routes}
        report['new_mismatches'] = [[c['index'], r] for c in report['cases'] for r in after.routes if c['result']['routes'][r]['status']=='mismatch' and c['before'][r]['result']['status']!='mismatch']
        report['before_counts'] = {r:dict(Counter(c['before'][r]['result']['status'] for c in report['cases'])) for r in after.routes}
        (out/f'seed{seed}.json').write_text(json.dumps(report,indent=2)+'\n')
        failures |= bool(report['lost_exact'] or any(r == 'smart' for i, r in report['mismatches']))
        print('RESULT', seed, report['counts'],flush=True)
    for path in (snapshot, build_before, build_after):
        shutil.rmtree(path)
    return int(failures)


if __name__ == '__main__':
    raise SystemExit(main())
