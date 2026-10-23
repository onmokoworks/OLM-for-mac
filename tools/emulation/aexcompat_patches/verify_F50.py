#!/usr/bin/env python3
"""Serial byte comparisons of F46/F50, S01 unresolved cases and seed-1 campaigns.

Uses an explicit 3600-second external watchdog, never changes fuzz defaults.
Writes each completed observation durably; --resume skips only completed rows.
"""
import argparse
from collections import Counter
import gzip
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

ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/F50-oracle-execution-limit'
E = ROOT/'orchestra/reports/F50-evidence'
CACHE = Path.home()/'.cache/olm-emu'
sys.path.insert(0, str(ROOT/'tools/fuzz'))
sys.dont_write_bytecode = True
from core import evaluate, load_corpus, raw_diff, sha
WORKERS = {'F46': CACHE/'worker-F46-pow/aex-guest-worker', 'F50': CACHE/'worker-F50-budget/aex-guest-worker'}
TIMEOUT = 3600

def adapter(plugin, version, max_size=256):
    return importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(
        main=ROOT.parent.parent, worker=WORKERS[version], max_size=max_size, case_timeout=TIMEOUT))

def existing(path):
    return {r['key']: r for r in map(json.loads, path.read_text().splitlines())} if path.exists() else {}

def append(path, row):
    with path.open('a') as out:
        out.write(json.dumps(row, sort_keys=True)+'\n')
        out.flush()
        os.fsync(out.fileno())
    print(row['key'], row.get('comparison', row.get('result', {}).get('routes', {})), flush=True)

def pair(case, plugin, directory, route):
    outputs, results = [], []
    for version in WORKERS:
        a = adapter(plugin, version)
        started = time.monotonic()
        result, raw = a.oracle(case, directory, time.monotonic()+TIMEOUT+60, route)
        results.append(dict(version=version, result=result, raw_sha256=sha(raw) if result['status']=='ok' else None,
                            elapsed_seconds=time.monotonic()-started))
        outputs.append(raw)
    successful = all(r['result']['status']=='ok' for r in results)
    comparison = 'identical' if successful and outputs[0]==outputs[1] else 'different' if successful else 'uncompared'
    return dict(comparison=comparison, observations=results,
                first_difference=raw_diff(*outputs, case['depth']) if comparison=='different' else None)

def corpus():
    path = E/'corpus.jsonl'
    known = existing(path)
    for corpus in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
        for source in sorted(corpus.glob('*.json')):
            data = json.loads(source.read_text())
            a = adapter(data['plugin'], 'F50', data['max_size'])
            case, _ = load_corpus(source, a)
            for route in dict.fromkeys(getattr(a, 'oracle_routes', {'smart':'smart'}).values()):
                key = str(source.relative_to(ROOT))+':'+str(route)
                if key in known:
                    assert known[key]['corpus_sha256']==sha(source.read_bytes())
                    continue
                with tempfile.TemporaryDirectory(dir=S, prefix='pair_') as td:
                    row = pair(case, a.name, Path(td), route)
                append(path, dict(key=key, plugin=a.name, corpus=corpus.name, route=route,
                                 corpus_sha256=sha(source.read_bytes()), input_sha256=sha(case['pixels']), **row))
    counts = Counter(r['comparison'] for r in existing(path).values())
    print('Corpus counts', dict(counts), flush=True)

def slow():
    path = E/'s01.jsonl'
    known = existing(path)
    for plugin in ('radialblur', 'olmdistancegradation'):
        with tempfile.TemporaryDirectory(dir=S, prefix='s01_build_') as td:
            directory = Path(td)
            a = adapter(plugin, 'F50')
            provenance = a.prepare(directory, time.monotonic()+TIMEOUT)
            (E/(plugin+'-s01-provenance.json')).write_text(json.dumps(provenance, indent=2)+'\n')
            for seed in range(101,106):
                source = ROOT/f'orchestra/reports/S01-wide-mismatch-sweep/{plugin}_seed{seed}.json.gz'
                baseline = json.loads(gzip.decompress(source.read_bytes()))
                for old in baseline['cases']:
                    if 'result' not in old:
                        continue
                    oracle = old['result'].get('oracles', {}).get('smart', old['result']['oracle'])
                    if oracle['status']=='ok':
                        continue
                    key = f'{plugin}:{seed}:{old["index"]}'
                    if key in known:
                        continue
                    case = a.generate(seed, old['index'])
                    assert sha(case['pixels'])==old['input_sha256']
                    with tempfile.TemporaryDirectory(dir=directory, prefix='case_') as cd:
                        result = evaluate(a, case, Path(cd), time.monotonic()+TIMEOUT*4+60)
                    append(path, dict(key=key, input_sha256=sha(case['pixels']), original=old['result'],
                                     baseline_sha256=sha(source.read_bytes()), result=result))

def campaigns():
    for plugin in ('radialblur', 'olmdistancegradation'):
        for version, worker in WORKERS.items():
            label = f'{plugin}-seed1-{version}'
            report = S/(label+'.json')
            if report.exists() and json.loads(report.read_text()).get('status')=='complete':
                continue
            cmd = [sys.executable, str(ROOT/'tools/fuzz/run.py'), '--plugin',plugin,'--n','300',
                   '--seed','1','--jobs','1','--shrink-attempts','0','--budget-minutes','1440',
                   '--case-timeout',str(TIMEOUT),'--worker',str(worker),'--scratch',str(S/'campaign'),
                   '--report',str(report),'--corpus',str(S/'generated-corpus')]
            with (S/(label+'.log')).open('w') as log:
                proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            print(label, 'exit', proc.returncode, flush=True)
            assert report.exists(), label
            data = report.read_bytes()
            with gzip.open(E/(label+'.json.gz'), 'wb') as f:
                f.write(data)
            assert json.loads(data)['completed']==300, label

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=('corpus','slow','campaigns','smoke'))
    args = ap.parse_args()
    S.mkdir(parents=True, exist_ok=True)
    E.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_TEST_JOBS='1', OLM_UCRT_FMA='1', PYTHONDONTWRITEBYTECODE='1')
    identities = {k:sha(v.read_bytes()) for k,v in WORKERS.items()}
    binding = E/'worker-identities.json'
    if binding.exists():
        assert json.loads(binding.read_text())==identities
    else:
        binding.write_text(json.dumps(identities,indent=2)+'\n')
    if args.mode=='smoke':
        for name in ('C49_seed1_case000117.json','C46_seed1_case000280.json'):
            source = ROOT/'tests/fuzz_corpus/radialblur'/name
            case,_ = load_corpus(source, adapter('radialblur','F50'))
            with tempfile.TemporaryDirectory(dir=S, prefix='smoke_') as td:
                row=pair(case, 'radialblur', Path(td), 'smart')
            append(E/'smoke.jsonl', dict(key=name, **row))
    else:
        globals()[args.mode]()

if __name__ == '__main__':
    main()
