#!/usr/bin/env python3
"""C04 Smart-only admission probes and before/after audit. Never writes corpus expectations."""
import argparse
import copy
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from verify_kirakira_admission_F10 import (ROOT, adapter_class, matrix_case, observation,
    load_corpus, main_checkout, default_worker, olmkirakira, sha)
from probe_kirakira_tiny_owner_F04 import owner_source


def cases(adapter, family):
    if family.endswith('-boundary'):
        gaussian=family.startswith('gaussian')
        depths=(8,16,32) if gaussian else (8,)
        modes=(3,) if gaussian else (1,2)
        for i,(depth,mode,angle,length) in enumerate(itertools.product(depths,modes,
                (-2147483647,-3000000,0,45000000,2147483512),((2,1000) if gaussian else (1,1000)))):
            case=matrix_case(adapter,i,(9,7),depth,1+i%2,mode,1)
            values={5:1,6:100,8:100,9:100,40:angle/65536,
                    10:length,16:length,22:length,28:length,34:0 if gaussian else min(length,500)}
            for param in case['parameters']:
                if param['slot'] in values: param['value']=values[param['slot']]
            yield case
        return
    geometries = ((1, 1), (1, 9), (9, 1), (3, 3), (5, 3), (8, 6), (7, 11))
    if family.startswith('pf8') or family.startswith('gaussian'):
        geometries += ((9,7),(17,11),(31,23))
    if family == 'zero':
        for i, (g, d, m, c) in enumerate(itertools.product(geometries, (8,16,32), (1,2,3), (1,2,3,4,5,6))):
            yield matrix_case(adapter, i, g, d, 1+i%2, m, c)
    elif family in ('alpha', 'gaussian', 'gaussian-all', 'pf8', 'pf8-flat'):
        for i, (g, d, m, r) in enumerate(itertools.product(geometries, ((8,) if family.startswith('pf8') else ((8,16,32) if family == 'gaussian-all' else (16,32))), ((3,) if family.startswith('gaussian') else (1,2)), range(6))):
            case = matrix_case(adapter, i, g, d, 1+i%2, m, 1)
            values = {5: [1,1.25,7.5,100][i%4], 6:100, 8:100, 9:100,
                      40:[0,1,22,90,359,-31,137,45000000][i%8]/65536}
            for j, slot in enumerate((10,16,22,28,34)):
                values[slot] = ([2,3,7,15,50,300] if family.startswith('gaussian') else [1,2,7,15,50,300])[(i+j)%6] if r in (j,5) else 0
            if family.startswith('gaussian'): values[34] = 0
            if family == 'pf8-flat': values.update({s:0 for s in (13,19,25,31,37)})
            for p in case['parameters']:
                if p['slot'] in values: p['value'] = values[p['slot']]
            yield case
    else:
        raise ValueError(family)


def build(source, scratch, options, deadline, gate_off):
    scratch.mkdir(parents=True)
    actual = source
    if gate_off:
        actual = scratch/'owner.cpp'
        body = source.read_text()
        if 'static bool IsSmartOwnerFullFrameDimensions(' not in body:
            body = owner_source(body)
        actual.write_text(body)
    adapter = adapter_class(actual, gate_off=gate_off)(options)
    adapter.binary, _ = adapter.build(scratch, deadline)
    return adapter


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--source', type=Path, default=olmkirakira.SOURCE)
    p.add_argument('--family', choices=('zero','alpha','gaussian','gaussian-all','pf8','pf8-flat','pf8-boundary','gaussian-boundary'))
    p.add_argument('--gate-off', action='store_true')
    p.add_argument('--before-source', type=Path)
    p.add_argument('--campaign-dir', type=Path)
    p.add_argument('--campaign-only', action='store_true')
    p.add_argument('--negatives', action='store_true')
    p.add_argument('--seeds', type=int, nargs='+', default=[1,4])
    args=p.parse_args()
    scratch=args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    deadline=time.monotonic()+7200
    options=SimpleNamespace(max_size=256,case_timeout=60,main=main_checkout(),worker=default_worker())
    report=dict(schema='olm-kira-smart-C04/1',status='running',family=args.family,
                gate_off=args.gate_off,source_sha256=sha(args.source.read_bytes()),
                worker_sha256=sha(options.worker.read_bytes()),
                aex_sha256=sha((options.main/'plugins_2025/OLMKiraKira.aex').read_bytes()),rows=[],corpus=[],campaigns={})
    def save():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    try:
        after=build(args.source,scratch/'after',options,deadline,args.gate_off)
        directory=scratch/'case';directory.mkdir(exist_ok=True)
        if args.family:
            for case in cases(after,args.family):
                oracle,reference=after.oracle(case,directory,deadline,'smart')
                result,raw=observation(after,case,directory,'smart',deadline,reference)
                row={k:v for k,v in case.items() if k!='pixels'}
                row.update(input_sha256=sha(case['pixels']),oracle=oracle,result=result)
                report['rows'].append(row)
                save()
                assert oracle['status']=='ok' and result['status']=='exact', row
                if len(report['rows'])%24==0: print('exact',len(report['rows']),flush=True)
        if args.negatives:
            base=next(cases(after,'alpha'))
            report['negatives']=[]
            variants=[]
            for slot,value in ((1,3),(2,3),(4,1),(6,99),(8,99),(9,99),(40,-2147483648/65536)):
                case=copy.deepcopy(base)
                for param in case['parameters']:
                    if param['slot']==slot: param['value']=value
                variants.append((f'slot{slot}',case))
            case=copy.deepcopy(base);case['pixels']=b'\xff'*len(case['pixels'])
            variants.append(('PF16-above-SDR',case))
            for label,case in variants:
                result,raw,*_=after.candidate(case,directory,'smart',deadline)
                report['negatives'].append(dict(label=label,result=result))
                save()
                assert result['status']=='refusal',(label,result)
        if args.before_source:
            before=build(args.before_source,scratch/'before',options,deadline,False)
            report['before_source_sha256']=sha(args.before_source.read_bytes())
            for corpus in (() if args.campaign_only else ('olmkirakira','olmkirakira_gate_off_T06')):
                for path in sorted((ROOT/'tests/fuzz_corpus'/corpus).glob('*.json')):
                    case,saved=load_corpus(path,after)
                    oracle,reference=after.oracle(case,directory,deadline,'smart')
                    assert oracle['status']=='ok',oracle
                    old,oldraw=observation(before,case,directory,'smart',deadline,reference)
                    new,newraw=observation(after,case,directory,'smart',deadline,reference)
                    assert new['status']==old['status'] and newraw==oldraw or old['status']=='refusal' and new['status']=='exact',(path,old,new)
                    report['corpus'].append(dict(path=str(path.relative_to(ROOT)),before=old,after=new))
                    save()
            if args.campaign_dir:
                for seed in args.seeds:
                    campaigns={kind:json.loads((args.campaign_dir/f'{kind}-seed{seed}.json').read_text()) for kind in ('before','after')}
                    assert all(v['status']=='complete' and v['completed']==300 for v in campaigns.values())
                    a,b=({r['index']:r for r in campaigns[k]['cases']} for k in ('before','after'))
                    changes=[]
                    for index in range(300):
                        old,new=(r[index]['result']['routes']['smart'] for r in (a,b))
                        assert a[index]['result']['oracle']==b[index]['result']['oracle']
                        assert old==new or old['status']=='refusal' and new['status'] in ('refusal','exact'),(seed,index,old,new)
                        case=after.generate(seed,index)
                        result,raw,*_=after.candidate(case,directory,'smart',deadline)
                        assert result['status']==('ok' if new['status']=='exact' else new['status']),(index,result,new)
                        if result['status']=='ok': assert sha(raw)==new['raw_sha256']
                        if old['status']!=new['status']: changes.append(index)
                    report['campaigns'][str(seed)]=dict(before=campaigns['before']['summary'],after=campaigns['after']['summary'],improved=changes,sanitized_routes=300)
                    save()
        report['status']='passed';save()
        print('PASS',len(report['rows']),'matrix;',len(report['corpus']),'corpus;',len(report['campaigns']),'campaigns',flush=True)
    except BaseException as exc:
        report.update(status='failed',error=repr(exc));save();raise
    finally:
        for name in ('after','before','case'): shutil.rmtree(scratch/name,ignore_errors=True)

if __name__=='__main__': main()
