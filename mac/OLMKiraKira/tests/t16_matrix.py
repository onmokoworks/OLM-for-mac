#!/usr/bin/env python3
"""Serial, exact original-AEX replay of the UI-typed T16 corpus (no AE claim).

Uses immutable external footage and workers; builds both revisions from source.
Every successful oracle must match Smart output byte for byte. Classic results
are recorded separately because this tuple's Classic refusal predates T16.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from t16_probe import ROOT, MAIN, TICKET, UIAdapter, audit, case, diff, sha
from t16_regression import baseline_source, module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--baseline', default='ac0e314c08827b96a4738ab47d83db7c577d14a4')
    p.add_argument('--only', help='Substring of corpus case name')
    args = p.parse_args()
    s = args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state'/TICKET)
    s.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(s), TMP=str(s), TEMP=str(s), PYTHONDONTWRITEBYTECODE='1')
    evidence = audit()
    corpus = json.loads(Path(__file__).with_name('t16_corpus.json').read_text())
    for key in ('requested_sha256', 'source_sha256'):
        assert evidence[key] == corpus['binding'][key], f'External fixture changed: {key}'
    baseline = baseline_source(s, args.baseline)
    original = module.SOURCE
    options = SimpleNamespace(main=MAIN, worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',
                              max_size=4096, case_timeout=180)
    adapters = []
    deadline = time.monotonic()+7200
    try:
        for name, source in [('before', baseline), ('after', original)]:
            module.SOURCE = source
            build = s/name
            build.mkdir(exist_ok=True)
            a = UIAdapter(options)
            a.binary, _ = a.build(build, deadline)
            adapters.append(a)
    finally:
        module.SOURCE = original
    binding = dict(fixture=evidence, baseline=args.baseline,
                   aex_sha256=sha(adapters[1].aex.read_bytes()),
                   worker_sha256=sha(options.worker.read_bytes()),
                   candidate_sha256={n:sha(a.binary.read_bytes()) for n,a in zip(('before','after'),adapters)},
                   source_sha256={f.name:sha(f.read_bytes()) for f in original.parent.iterdir()
                                  if f.suffix in ('.cpp','.inc','.h')})
    (s/'binding.json').write_text(json.dumps(binding, indent=2)+'\n')
    for key in ('worker_sha256', 'aex_sha256'):
        assert binding[key] == corpus['binding'][key], f'Oracle changed: {key}'
    results = []
    for spec in corpus['cases']:
        if args.only and args.only not in spec['name']:
            continue
        pressure = subprocess.check_output(['memory_pressure'], text=True)
        free = int(pressure.rsplit('System-wide memory free percentage: ',1)[1].split('%')[0])
        assert free >= 30, f'memory free {free}%'
        a = adapters[1]
        w,h = spec['geometry']
        config = SimpleNamespace(width=w,height=h,parameters=spec['parameters'],rotation='ui',
                                 rays=spec['rays'],set=[f'{k}={v}' for k,v in spec['overrides'].items()])
        c = case(a,config,evidence)
        work = s/'current'
        work.mkdir(exist_ok=True)
        oracle, ref = a.oracle(c,work,deadline,'smart')
        row = dict(name=spec['name'],scope=spec.get('scope','public-ui'),memory_free_percent=free,oracle=oracle,
                   case={k:v for k,v in c.items() if k!='pixels'},
                   input_sha256=sha(c['pixels']),oracle_sha256=sha(ref))
        for name, candidate in zip(('before','after'), adapters):
            result, raw, guards = candidate.candidate(c,work,'smart',deadline)
            row[name] = dict(result=result,guards=guards,sha256=sha(raw))
            if oracle['status']=='ok' and result['status']=='ok':
                row[name]['diff'] = diff(ref,raw,w)
        result, raw, guards = a.candidate(c,work,'classic',deadline)
        row['classic'] = dict(result=result,guards=guards,sha256=sha(raw))
        results.append(row)
        (s/(spec['name']+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        print(spec['name'],json.dumps({n:row[n].get('diff',row[n].get('result')) for n in ('before','after')}),flush=True)
    exact = [r for r in results if r['oracle']['status']=='ok'
             and r['after'].get('diff',{}).get('different_samples')==0]
    unchanged_refusals = [r for r in results if r['scope'].startswith('outside-ui:')
                         and r['oracle']['status']=='ok'
                         and all(r[n]['result'].get('error')==516 for n in ('before','after'))]
    failures = [r['name'] for r in results if r not in exact and r not in unchanged_refusals]
    summary = dict(cases=len(results),exact=len(exact),failures=failures,
                   outside_ui_unchanged_refusals=[r['name'] for r in unchanged_refusals],
                   before_mismatches=sum(r['before'].get('diff',{}).get('different_samples',0)>0 for r in results))
    (s/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
    return bool(failures)


if __name__=='__main__':
    sys.exit(main())
