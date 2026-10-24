#!/usr/bin/env python3
"""Serial T15 prerequisite qualification, regression, and reduced witnesses.

Host delivery qualification is independent of production numerical acceptance.
All scratch is ticket-local. No reference worker or installed plug-in is rebuilt.
"""
import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import time
from types import SimpleNamespace

from core import evaluate, save_corpus, sha, shrink, proposals, apply_operation
from geometry import sample, require_host
from run import ROOT, main_checkout

S = ROOT / 'orchestra/state/T15-odd-even-random-comp-sweep'
E = ROOT / 'orchestra/reports/T15-evidence'
NAMES = ('olmcolorkey', 'olmdirectionalblur')


def adapter(name, scratch, before=False):
    a = importlib.import_module('adapters.' + name).Adapter(SimpleNamespace(
        main=main_checkout(), worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',
        max_size=256, case_timeout=10))
    a.env.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    if before and name == 'olmcolorkey':
        compile_sdk = a.compile_sdk
        def old_host(directory, body, source, deadline, cores=()):
            body = body.replace('PF_PreRenderInput pi{}; pi.bitdepth = depth;', 'PF_PreRenderInput pi{};')
            return compile_sdk(directory, body, source, deadline, cores)
        a.compile_sdk = old_host
    return a


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n', type=int, default=20)
    args = ap.parse_args()
    S.mkdir(parents=True, exist_ok=True)
    E.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S))
    summary = {}
    for name in NAMES:
        stage = S / ('qualification-' + name)
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        a = adapter(name, stage)
        deadline = time.monotonic() + 1800
        provenance = a.prepare(stage, deadline)
        provenance['case_timeout_seconds'] = 10
        write(E/(name+'-provenance.json'), provenance)
        defaults = []
        for i in range(10):
            defaults.append(evaluate(a, a.generate(2026,i), stage, deadline))
        rows = []
        first = {}
        for i in range(args.n):
            c = sample(a.generate(2026,i), 'realistic')
            require_host(a,c)
            attr = {}
            r = evaluate(a,c,stage,deadline,attr)
            expected = [*c['full_geometry'], *c['downsample'][0], *c['downsample'][1], *c['pixel_aspect'], c['rowbytes_padding']]
            for route, v in r['routes'].items():
                observed = list(map(int,v.get('metadata',{}).get('GEOMETRY_INPUT','').split()))
                assert observed == expected, (name,i,route,v)
            rows.append(dict(case={k:v for k,v in c.items() if k!='pixels'}, input_sha256=sha(c['pixels']), result=r, refusals=attr))
            v = r['routes']['smart']
            oracle = r.get('oracles',{}).get('smart',r['oracle'])
            if oracle['status']=='ok' and v['status'] in ('mismatch','refusal'):
                kind = 'refusal' if v['status']=='refusal' else 'rectangle' if 'geometry_diff' in v else 'pixels'
                first.setdefault(kind,c)
            print(name,i,{route:v['status'] for route,v in r['routes'].items()},flush=True)
        write(E/(name+'-qualification.json'),rows)
        # The one host correction must leave all default result objects identical.
        olddir = stage/'before';olddir.mkdir()
        old = adapter(name,olddir,before=True)
        old.prepare(olddir,deadline)
        olddefaults = [evaluate(old,old.generate(2026,i),olddir,deadline) for i in range(10)]
        assert defaults == olddefaults, name+' default regression'
        before = []
        for i in range(5):
            c=sample(old.generate(2026,i),'realistic')
            before.append(evaluate(old,c,olddir,deadline))
        write(E/(name+'-before.json'),before)
        write(E/(name+'-default.json'),dict(before=olddefaults,after=defaults,identical=True))
        witnesses=[]
        for kind, original in first.items():
            # Reduce only the contract route; save both routes for standard replay.
            single=copy.copy(a);single.routes=('smart',);single.oracle_routes={'smart':'smart'}
            r=evaluate(single,original,stage,deadline)
            if kind!='refusal':
                reduced,_,reduction=shrink(single,original,r,stage,min(deadline,time.monotonic()+90),80)
            else:
                reduced=original;accepted=[];attempts=0
                for _ in range(8):
                    improved=False
                    for op in proposals(single,reduced):
                        if attempts>=80:break
                        c=apply_operation(single,reduced,op)
                        if c==reduced:continue
                        attempts+=1
                        rr=evaluate(single,c,stage,deadline)
                        if rr['oracle']['status']=='ok' and rr['routes']['smart']['status']=='refusal':
                            reduced=c;accepted.append(op);improved=True;break
                    if not improved:break
                reduction=dict(attempts=attempts,accepted=accepted,bounded=True,minimality_claimed=False)
            attr={};result=evaluate(a,reduced,stage,deadline,attr)
            assert all(v['status']=='ok' for v in result.get('oracles',{'smart':result['oracle']}).values())
            corpus=ROOT/'tests/fuzz_corpus'/name/'T15-prerequisite-realistic'
            corpus.mkdir(parents=True,exist_ok=True)
            path=corpus/(kind+'.json')
            save_corpus(path,a,original,reduced,result,reduction,provenance)
            witnesses.append(dict(kind=kind,path=str(path.relative_to(ROOT)),geometry=reduced['geometry'],result=result,refusals=attr,reduction=reduction))
        summary[name]=dict(default_identical=True,default_cases=10,delivery_checks=args.n*2,witnesses=witnesses)
        write(E/'qualification-summary.json',summary)
        shutil.rmtree(stage)
    print('Transport qualified; consult saved results for numerical failures.',flush=True)

if __name__=='__main__':
    main()
