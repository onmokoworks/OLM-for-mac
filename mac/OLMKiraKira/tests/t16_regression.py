#!/usr/bin/env python3
"""Compare all retained KiraKira corpus routes with the ticket's parent source.

This is a candidate-only monotonicity check. Run replay_corpora.py separately
for comparisons against the original-AEX workers bound by the saved corpora.
"""
import argparse
import collections
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters import olmkirakira as module
from core import load_corpus,sha
from geometry import require_host


def baseline_source(s, revision):
    tree=s/'baseline-tree';tree.mkdir(exist_ok=True)
    core=tree/'core'
    if not core.exists():core.symlink_to(ROOT/'core',target_is_directory=True)
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'mac/OLMKiraKira'],cwd=ROOT,text=True).splitlines()
    for name in names:
        if Path(name).suffix not in ('.h','.cpp','.inc'):continue
        target=tree/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT))
    return tree/'mac/OLMKiraKira/OLMKiraKira.cpp'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',default='ac0e314c08827b96a4738ab47d83db7c577d14a4')
    p.add_argument('--scratch',type=Path,required=True)
    args=p.parse_args();s=args.scratch.resolve();s.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1')
    pressure=subprocess.check_output(['memory_pressure'],text=True)
    (s/'memory-pressure.txt').write_text(pressure)
    assert int(pressure.rsplit('System-wide memory free percentage: ',1)[1].split('%')[0])>=30
    baseline=baseline_source(s,args.baseline)
    options=SimpleNamespace(main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',max_size=256,case_timeout=30)
    original=module.SOURCE;adapters=[];deadline=time.monotonic()+3600
    try:
        for name,source in [('before',baseline),('after',original)]:
            build=s/name;build.mkdir(exist_ok=True);module.SOURCE=source
            adapter=module.Adapter(options);adapter.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
            adapter.binary,_=adapter.build(build,deadline);adapters.append(adapter)
    finally:module.SOURCE=original
    counts=collections.Counter();different=[];cases=0;checks=0
    with (s/'results.jsonl').open('w') as out:
        for path in sorted((ROOT/'tests/fuzz_corpus').rglob('*.json')):
            record=json.loads(path.read_text())
            if record.get('plugin')!='olmkirakira':continue
            for a in adapters:
                a.max_size=record['max_size']
            case,_=load_corpus(path,adapters[1]);cases+=1
            for a in adapters:require_host(a,case)
            for route in ('classic','smart'):
                results=[]
                for name,a in zip(('before','after'),adapters):
                    d=s/(name+'-case');d.mkdir(exist_ok=True)
                    result,raw,guards=a.candidate(case,d,route,deadline)
                    # Source line movement is not a new refusal.
                    guards=[g.rsplit('@',1)[0] for g in guards]
                    results.append(dict(result=result,sha256=sha(raw),guards=guards))
                row=dict(path=str(path.relative_to(ROOT)),route=route,before=results[0],after=results[1])
                if results[0]!=results[1]:different.append(row)
                counts[(route,results[1]['result']['status'])]+=1;checks+=1
                out.write(json.dumps(row)+'\n');out.flush()
            if cases%50==0:print(cases,'cases;',len(different),'changed routes',flush=True)
    result=dict(baseline=args.baseline,cases=cases,route_checks=checks,
        candidate_sha256={k:sha(a.binary.read_bytes()) for k,a in zip(('before','after'),adapters)},
        counts={':'.join(k):v for k,v in counts.items()},differences=different)
    (s/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return bool(different)


if __name__=='__main__':sys.exit(main())
