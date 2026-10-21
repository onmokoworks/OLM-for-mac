#!/usr/bin/env python3
"""Paired original-AEX/Mac stages for reproducible C04 independent witnesses."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode=True
from trace_kirakira_numeric_F09 import (ROOT, build_mac, original_trace, load_corpus,
    olmkirakira, main_checkout, default_worker, raw_diff, sha)
from verify_kirakira_smart_C04 import cases


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--source',type=Path,default=olmkirakira.SOURCE)
    p.add_argument('--family',default='pf8-flat')
    p.add_argument('--index',type=int,default=72)
    p.add_argument('--corpus-index',type=int)
    p.add_argument('--production',action='store_true')
    p.add_argument('--require-exact',action='store_true')
    args=p.parse_args(); scratch=args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state')
    scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),
        OLM_KK_PROCESS_ATTACH_DIAGNOSTIC='1',OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC='1')
    deadline=time.monotonic()+3600
    options=SimpleNamespace(max_size=256,case_timeout=180,main=main_checkout(),worker=default_worker())
    adapter=build_mac(args.source,scratch/'build',options,deadline,not args.production)
    if args.corpus_index is not None:
        path=next((ROOT/'tests/fuzz_corpus/olmkirakira_gate_off_T06').glob(f'seed1_case{args.corpus_index:06}_*.json'))
        case,_=load_corpus(path,adapter)
    else: case=next(c for c in cases(adapter,args.family) if c['index']==args.index)
    directory=scratch/'case';directory.mkdir(exist_ok=True)
    adapter.env['F09_TRACE']=str(directory)
    try:
        oracle,reference=adapter.oracle(case,directory,deadline,'smart')
        candidate,raw,*_=adapter.candidate(case,directory,'smart',deadline)
        original=original_trace(case,adapter.aex)
        stages=original['stages'];paired={}
        for name in ('source','seed','ray0','ray1','ray2','ray3','ray4','glow','composed'):
            aex=bytes.fromhex(stages[name]);mac=(directory/(name+'.raw')).read_bytes()
            paired[name]=dict(exact=aex==mac,aex_sha256=sha(aex),mac_sha256=sha(mac),
                diff=None if aex==mac else raw_diff(aex,mac,32))
        bound=oracle['status']=='ok' and bytes.fromhex(stages['output'])==reference
        report=dict(schema='olm-kira-C04-trace/1',case={k:v for k,v in case.items() if k!='pixels'},
            input_sha256=sha(case['pixels']),source_sha256=sha(args.source.read_bytes()),
            aex_sha256=sha(adapter.aex.read_bytes()),worker_sha256=sha(adapter.worker.read_bytes()),
            oracle=oracle,candidate=candidate,public_bound=bound,paired=paired,
            first_divergent_stage=next((k for k,v in paired.items() if not v['exact']),None),
            output_exact=raw==reference,output_sha256=sha(raw),aex_output_sha256=sha(reference),
            final_diff=None if raw==reference else raw_diff(reference,raw,case['depth']),
            aex_geometry=original['geometry'],abi_leaf_exact=True,
            contract='Original full caller, original reader/writer; retained TLS/CRT/allocator/Python libm scaffolding; no numerical detours. Mac Smart, optional final tuple bypass.')
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        assert bound,(oracle,original.get('error'))
        assert candidate['status']=='ok',candidate
        if args.require_exact: assert raw==reference and all(v['exact'] for v in paired.values()),report['first_divergent_stage']
        print('bound',bound,'first',report['first_divergent_stage'],'output exact',report['output_exact'])
    finally:
        shutil.rmtree(scratch/'build',ignore_errors=True)
        shutil.rmtree(directory,ignore_errors=True)

if __name__=='__main__': main()
