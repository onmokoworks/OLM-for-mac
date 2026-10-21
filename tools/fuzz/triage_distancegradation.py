#!/usr/bin/env python3
"""T07: scratch-only gate experiments and retained-cluster raw-byte census.

No production gate switch is added. The generated translation unit has an
explicit compile-time switch and includes the worktree's unchanged headers.
All cases are baseline seed/index inputs or retained, hash-checked shrunk inputs.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import time

sys.dont_write_bytecode = True
from adapters.olmdistancegradation import Adapter, SOURCE, SHIM_DIR, FIELDGEN
from adapters.public import ROOT, replace_once
from core import load_corpus, raw_diff, sha

SCRATCH = ROOT/'orchestra/state/T07-triage-distancegradation'
BASELINE = ROOT/'reports/fuzz/olmdistancegradation_20261021.json'


def byte_stats(expected, actual, case):
    result = raw_diff(expected, actual, case['depth'])
    unit = case['depth']//8
    words = [i//unit for i in range(0, len(expected), unit)
             if expected[i:i+unit] != actual[i:i+unit]]
    pixels = sorted({i//4 for i in words})
    w,h = case['geometry']
    result.update(max_abs_byte_diff=max((abs(a-b) for a,b in zip(expected,actual)), default=0),
                  channels=dict(Counter('ARGB'[i%4] for i in words)),
                  different_pixels=len(pixels), total_pixels=w*h,
                  bbox=[min(p%w for p in pixels), min(p//w for p in pixels),
                        max(p%w for p in pixels), max(p//w for p in pixels)] if pixels else None,
                  first_xy_channel=[result['first_word']//4%w,result['first_word']//4//w,
                                    'ARGB'[result['first_word']%4]])
    fmt = {8:'B',16:'H',32:'f'}[case['depth']]
    pairs=list(zip(struct.unpack('<'+fmt*(len(expected)//unit),expected),
                   struct.unpack('<'+fmt*(len(actual)//unit),actual)))
    result['max_abs_finite_sample_diff']=max((abs(a-b) for a,b in pairs if math.isfinite(a) and math.isfinite(b)),default=None)
    result['nonfinite_sample_pairs']=sum(not(math.isfinite(a) and math.isfinite(b)) for a,b in pairs)
    return result


def outcome(adapter, case, directory, route, deadline, oracle, reference):
    status,raw,guards=adapter.candidate(case,directory,route,deadline)
    result=dict(status, guards=guards)
    if status['status']=='ok':
        result.update(status=('exact' if raw==reference else 'mismatch') if oracle['status']=='ok' else 'uncompared',raw_sha256=sha(raw))
        if result['status']=='mismatch': result['diff']=byte_stats(reference,raw,case)
    elif status['status']=='error':
        diag=status.get('diagnostic','')
        result['status']='sanitizer_error' if 'runtime error:' in diag or 'Sanitizer' in diag else 'crash' if status.get('returncode',0)<0 else 'harness_error'
    return result,raw


def build_variant(base, directory, name, flags, deadline):
    directory.mkdir()
    a=copy.copy(base); a.env=dict(base.env)
    a.binary,_=a.build(directory,deadline)
    body=(directory/'host.cpp').read_text()
    source=SOURCE.read_text()
    for old,new in [('#include "OLMDistanceGradation.h"', '#include "'+str(SOURCE.with_suffix('.h'))+'"'),
                    ('"../../core/', '"'+str(ROOT/'core')+'/')]:
        source=source.replace(old,new)
    source=replace_once(source,'if (!err && (in_result.ref_width != in_data->width ||',
                        'if (!OLM_DG_TRIAGE_GATE_OFF && !err && (in_result.ref_width != in_data->width ||')
    candidate=directory/'distance.cpp'; candidate.write_text(source)
    body=replace_once(body,str(SOURCE),str(candidate))
    body=replace_once(body,'result->result_rect = {0, 0, W, H};',
                      '#if OLM_DG_TRIAGE_HOST_FIX\n\tresult->ref_width = W; result->ref_height = H;\n#endif\n\tresult->result_rect = {0, 0, W, H};')
    host=directory/'host.cpp';host.write_text(body)
    a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',*flags,
               '-I',SHIM_DIR,host,FIELDGEN,'-o',a.binary],deadline)
    a.env.update(ASAN_OPTIONS='detect_leaks=0', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    return a,{'candidate_sha256':sha(a.binary.read_bytes()),'source_sha256':sha(candidate.read_bytes()),'flags':flags}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,choices=[2],required=True)
    parser.add_argument('--report',type=Path,default=SCRATCH/'triage.json')
    args=parser.parse_args()
    if not args.report.resolve().is_relative_to(ROOT): parser.error('report must be in worktree')
    SCRATCH.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH))
    baseline=json.loads(BASELINE.read_text())
    opts=argparse.Namespace(max_size=256,case_timeout=10,main=ROOT.parent.parent,
                            worker=Path(baseline['provenance']['worker_path']))
    adapter=Adapter(opts); deadline=time.monotonic()+1800
    report={'schema':'olm.distance-triage/1','jobs':args.jobs,'baseline_sha256':sha(BASELINE.read_bytes()),
            'paired_stage_support':False,'variants':{},'cases':[],'clusters':[]}
    with tempfile.TemporaryDirectory(prefix='experiment_',dir=SCRATCH) as td:
        directory=Path(td); prod=directory/'production';prod.mkdir()
        report['provenance']=adapter.prepare(prod,deadline)
        assert report['provenance']['worker_sha256']==baseline['provenance']['worker_sha256']
        variants={'production':adapter}
        for name,flags in {
            'ref_gate_off':['-DOLM_DG_TRIAGE_GATE_OFF=1','-DOLM_DG_TRIAGE_HOST_FIX=0'],
            'host_fix':['-DOLM_DG_TRIAGE_GATE_OFF=0','-DOLM_DG_TRIAGE_HOST_FIX=1'],
            'ref_gate_off_sanitized':['-DOLM_DG_TRIAGE_GATE_OFF=1','-DOLM_DG_TRIAGE_HOST_FIX=0',
                                      '-fsanitize=address,undefined','-fno-sanitize-recover=all'],
        }.items():
            variants[name],report['variants'][name]=build_variant(adapter,directory/name,name,flags,deadline)
        print('BUILT',flush=True)
        def run(row):
            case=adapter.generate(row['seed'],row['index'])
            assert sha(case['pixels'])==row['input_sha256']
            with tempfile.TemporaryDirectory(prefix='case_',dir=directory) as wd:
                work=Path(wd); oracle,reference=adapter.oracle(case,work,deadline)
                result={'index':row['index'],'depth':case['depth'],'profile':case['profile'],'oracle':oracle,'variants':{}}
                for name,a in variants.items():
                    result['variants'][name]=outcome(a,case,work,'smart',deadline,oracle,reference)[0]
                result['gate_equals_host_fix']=result['variants']['ref_gate_off']==result['variants']['host_fix']
                return result
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for i,row in enumerate(pool.map(run,baseline['cases'])):
                report['cases'].append(row)
                if (i+1)%25==0: print('CASES',i+1,flush=True)
        report['summary']={name:dict(Counter(r['variants'][name]['status'] for r in report['cases'])) for name in variants}
        report['guard_ranking']=dict(Counter(g.split('@')[0] for r in report['cases'] for g in r['variants']['production']['guards']))
        # Smallest retained by pixel count, then active bytes, then path. These
        # are bounded greedy shrinks, not a claim of globally minimal witnesses.
        for cluster,group in sorted(baseline['clusters'].items()):
            loaded=[(ROOT/p,*load_corpus(ROOT/p,adapter)) for p in group['corpus']]
            path,case,saved=min(loaded,key=lambda x:(math.prod(x[1]['geometry']),len(x[1]['pixels']),str(x[0])))
            with tempfile.TemporaryDirectory(prefix='cluster_',dir=directory) as wd:
                work=Path(wd); oracle,reference=adapter.oracle(case,work,deadline)
                result,raw=outcome(adapter,case,work,'classic',deadline,oracle,reference)
                # A route audit is diagnostic only; no comparator is changed.
                classic=copy.copy(adapter);classic.oracle_route='classic';classic.oracle_path='classic'
                cstatus,craw=classic.oracle(case,work,deadline)
                smart,_=outcome(variants['host_fix'],case,work,'smart',deadline,oracle,reference)
                report['clusters'].append(dict(cluster=cluster,count=group['count'],corpus=str(path.relative_to(ROOT)),
                    geometry=case['geometry'],depth=case['depth'],input_sha256=sha(case['pixels']),
                    parameters=case['parameters'],oracle=oracle,classic=result,smart_host_fix=smart,
                    aex_classic=cstatus,aex_classic_sha256=sha(craw) if cstatus['status']=='ok' else None,
                    mac_matches_aex_classic=raw==craw if cstatus['status']=='ok' else None))
        report['script_sha256']=sha(Path(__file__).read_bytes())
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print('RESULT',json.dumps(report['summary'],sort_keys=True),flush=True)
    return 0

if __name__=='__main__': sys.exit(main())
