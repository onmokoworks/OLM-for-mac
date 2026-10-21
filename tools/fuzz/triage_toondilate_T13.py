#!/usr/bin/env python3
"""T13: bounded ToonDilate triage; all diagnostic source/builds stay in scratch.

Requires MAIN's emulation venv for Unicorn. No production numerical edits.
Run the normal campaign and replay first (see ticket report).
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/emulation'))
from adapters.olmtoondilate import Adapter, SOURCE
from adapters.public import PublicAdapter, replace_once
from core import command, load_corpus, raw_diff, sha
from aex_loader import AexLoader
from aex_witness import leaf_check
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import alloc, context_and_suite
from unicorn.x86_const import UC_X86_REG_RSP, UC_X86_REG_EDX


class DiagnosticAdapter(Adapter):
    def __init__(self, options, source_text=None, sanitize=False):
        super().__init__(options)
        self.source_text = source_text
        self.sanitize = sanitize

    def compile_sdk(self, scratch, body, source, deadline, cores=()):
        if self.source_text is not None:
            candidate = scratch/'diagnostic.cpp'
            candidate.write_text(self.source_text.replace('#include "OLMToonDilate.h"',
                                 '#include "'+str(SOURCE.with_suffix('.h'))+'"', 1))
            body = replace_once(body, '#include "'+str(SOURCE)+'"', '#include "'+str(candidate)+'"')
        return super().compile_sdk(scratch, body, source, deadline, cores)

    def compile(self, argv, deadline):
        if self.sanitize and argv[0] == 'clang++':
            argv = [a for a in argv if a != '-O2'] + ['-O1', '-g', '-fsanitize=address,undefined',
                     '-fno-sanitize-recover=all', '-fno-omit-frame-pointer']
        return super().compile(argv, deadline)


def stats(expected, actual, case):
    result = raw_diff(expected, actual, case['depth']) if expected != actual else {'different_bytes':0,'different_words':0}
    unit = case['depth']//8
    words = [i//unit for i in range(0,len(expected),unit) if expected[i:i+unit] != actual[i:i+unit]]
    pixels = sorted(set(i//4 for i in words)); w,h = case['geometry']
    finite_diffs = []; nonfinite = 0
    fmt = {8:'B',16:'H',32:'f'}[case['depth']]
    for i in words:
        a,b = (struct.unpack_from('<'+fmt,raw,i*unit)[0] for raw in (expected,actual))
        if math.isfinite(a) and math.isfinite(b): finite_diffs.append(abs(a-b))
        else: nonfinite += 1
    result.update(max_abs_byte_diff=max((abs(a-b) for a,b in zip(expected,actual)),default=0),
                  max_abs_finite_sample_diff=max(finite_diffs,default=0),nonfinite_differing_samples=nonfinite,
                  channels=dict(Counter('ARGB'[i%4] for i in words)), differing_pixels=len(pixels),
                  pixel_coordinates=[[i%w,i//w] for i in pixels],
                  expected_sha256=sha(expected),actual_sha256=sha(actual))
    if len(expected)<=128: result.update(expected_hex=expected.hex(),actual_hex=actual.hex(),input_hex=case['pixels'].hex())
    return result


def original_stage(case, aex):
    """Execute the real PF32 worker and record mask stores before propagation."""
    loader = AexLoader(str(aex),verbose=False,fast=True)
    # Import-free 5th-stack-argument ABI control: ARGB -> separate RGBA words.
    source = alloc(loader, struct.pack('<4I',0x12345678,0x23456789,0x3456789a,0x456789ab))
    outputs = [alloc(loader,b'\xa5'*4) for _ in range(4)]
    leaf_check(loader,0x1801ac7a0,outputs+[source])
    assert b''.join(loader.read_bytes(p,4) for p in outputs)==struct.pack('<4I',0x23456789,0x3456789a,0x456789ab,0x12345678)
    w,h = case['geometry']; rb = w*16
    def world(payload):
        ptr=alloc(loader,payload); header=bytearray(0x40)
        struct.pack_into('<QiiiH',header,0x18,ptr,rb,w,h,128)
        return alloc(loader,bytes(header)),ptr
    iw,ip = world(case['pixels']); ow,op=world(b'\xee'*(rb*h))
    worlds={iw:dict(payload=ip,width=w,height=h,rowbytes=rb,pixel_size=16),
            ow:dict(payload=op,width=w,height=h,rowbytes=rb,pixel_size=16)}
    events=[]; context=context_and_suite(loader,events,worlds)
    radius=alloc(loader,struct.pack('<f',case['parameters'][0]['value']))
    stages=[]
    def on_store(current,address,size):
        rsp=current.uc.reg_read(UC_X86_REG_RSP)
        stages.append(dict(alpha_hex=current.read_bytes(rsp+0x34,4).hex(),
                           distance=current.uc.reg_read(UC_X86_REG_EDX)))
    loader.add_code_hook(0x1801a69a3,on_store)
    call=loader.call_function(0x1801a6800,int_args=[context,0,iw,ow,radius],max_instructions=10_000_000)
    assert len(stages)==w*h
    assert loader.read_bytes(ip,rb*h)==case['pixels']
    return stages,loader.read_bytes(op,rb*h),dict(abi_control=True,instructions=call['instructions'],
                  seed_constant_hex=loader.read_bytes(0x1803118a8,4).hex())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--jobs',type=int,choices=[2],required=True)
    p.add_argument('--corpus',type=Path,required=True)
    args=p.parse_args(); args.scratch=args.scratch.resolve()
    args.corpus=args.corpus.resolve(); args.report=args.report.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state')
    args.scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch),TMP=str(args.scratch),TEMP=str(args.scratch),PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir=str(args.scratch)
    options=SimpleNamespace(max_size=256,case_timeout=15,main=ROOT.parent.parent,
        worker=Path('/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker'))
    deadline=time.monotonic()+1200
    campaign=json.loads((args.scratch/'campaign.json').read_text())
    replay=json.loads((args.scratch/'replay.json').read_text())
    assert campaign['completed']==300 and replay['completed']==300 and replay['replay_matches_saved']
    stage_text=replace_once(SOURCE.read_text(),'\tif (!has_seed) return PF_Err_NONE;', '''
    if (const char *path = std::getenv("OLM_TOON_STAGE_TRACE")) {
        if (FILE *f = std::fopen(path, "w")) {
            for (uint32_t d : dist) std::fprintf(f, "%u\\n", d);
            std::fclose(f);
        }
    }
\tif (!has_seed) return PF_Err_NONE;''')
    with tempfile.TemporaryDirectory(prefix='triage_',dir=args.scratch) as td:
        work=Path(td)
        adapters={}
        for name,source,sanitize in [('production',None,False),('stage',stage_text,False),('sanitized',None,True),
                ('seed_experiment', replace_once(SOURCE.read_text(), 'return p.alpha >= 1.0f;',
                    '\n#ifdef OLM_TOON_EXPERIMENT_SEED\nreturn p.alpha == 1.0f || std::isnan(p.alpha);\n#else\nreturn p.alpha >= 1.0f;\n#endif\n'), True)]:
            d=work/name;d.mkdir(); a=DiagnosticAdapter(options,source,sanitize)
            if name=='seed_experiment': a.source_text='#define OLM_TOON_EXPERIMENT_SEED 1\n'+a.source_text
            prov=a.prepare(d,deadline)
            prov.update(diagnostic_source_sha256=sha((a.source_text or SOURCE.read_text()).encode()),
                        sanitizers='address,undefined; abort on error; leaks disabled' if sanitize else None)
            adapters[name]=(a,prov)
        a=adapters['production'][0]; traced=adapters['stage'][0]; sanitized=adapters['sanitized'][0]; experiment=adapters['seed_experiment'][0]
        def sanitize_row(row):
            case=a.generate(1,row['index']); outcomes={}
            with tempfile.TemporaryDirectory(dir=work) as d:
                for route in a.routes:
                    argv,data=sanitized.candidate_command(case,Path(d),route)
                    status,raw,err=command(argv,data=data,timeout=15,deadline=deadline,
                        env=dict(sanitized.env,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
                    diagnostics=[line for line in err.decode(errors='replace').splitlines() if any(s in line for s in ('Sanitizer','runtime error:'))]
                    outcomes[route]=dict(status=status,diagnostics=diagnostics,
                        same_raw=sha(raw)==row['result']['routes'][route]['raw_sha256'])
                    if route=='smart':
                        argv,data=experiment.candidate_command(case,Path(d),route)
                        status,raw,err=command(argv,data=data,timeout=15,deadline=deadline,
                            env=dict(experiment.env,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
                        outcomes['seed_experiment']=dict(status=status,
                            diagnostics=[line for line in err.decode(errors='replace').splitlines() if any(s in line for s in ('Sanitizer','runtime error:'))],
                            same_raw=sha(raw)==row['result']['oracles']['smart']['raw_sha256'])
            return dict(index=row['index'],routes=outcomes)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            sanitizer_rows=list(pool.map(sanitize_row,campaign['cases']))
        reduced=[]
        for path in sorted(args.corpus.glob('*.json')):
            case,saved=load_corpus(path,a)
            with tempfile.TemporaryDirectory(dir=work) as d:
                d=Path(d); oracle,expected=a.oracle(case,d,deadline,'smart')
                result,actual,guards=a.candidate(case,d,'smart',deadline)
                assert oracle['status']==result['status']=='ok' and not guards
                # Retain the exact saved verdict/hash, not just mismatch status.
                assert sha(expected)==saved['result']['oracles']['smart']['raw_sha256']
                assert sha(actual)==saved['result']['routes']['smart']['raw_sha256']
                stage_file=d/'stage.txt'
                sr,sraw,_=traced.candidate(case,d,'smart',deadline,env=dict(traced.env,OLM_TOON_STAGE_TRACE=str(stage_file)))
                assert sr==result and sraw==actual
                mac_mask=list(map(int,stage_file.read_text().splitlines()))
                original,worker_raw,control=original_stage(case,a.aex)
                assert worker_raw==expected, 'direct worker must equal matching public AEX output'
                differing=[i for i,(x,y) in enumerate(zip(original,mac_mask)) if x['distance']!=y]
                first=differing[0] if differing else None
                reduced.append(dict(path=str(path.relative_to(ROOT)),case=saved['case'],input_sha256=sha(case['pixels']),
                    diff=stats(expected,actual,case),first_differing_stage='seed mask' if differing else None,
                    first_seed_index=first,seed_disagreements=len(differing),
                    first_seed=dict(original[first],mac_distance=mac_mask[first]) if differing else None,
                    original_mask=original,mac_mask=mac_mask,worker_control=control))
        # Force one actual guard to prove tracing operates and is byte/status neutral.
        invalid=copy.deepcopy(a.generate(1,0));invalid['parameters'][0]['value']=101.0
        with tempfile.TemporaryDirectory(dir=work) as d:
            d=Path(d)
            traced_result,traced_raw,guards=a.candidate(invalid,d,'smart',deadline)
            plain_result,plain_raw=PublicAdapter.candidate(a,invalid,d,'smart',deadline)
            assert traced_result==plain_result and traced_raw==plain_raw and len(guards)==1
            assert traced_result['error']==516 and 'prerender-radius' in guards[0]
            guard_control=dict(result=traced_result,guards=guards,trace_neutral=True,legal=False)
        # An unreadable trace destination must not turn a valid result into an error.
        with tempfile.TemporaryDirectory(dir=work) as d:
            d=Path(d)
            missing_result,missing_raw=PublicAdapter.candidate(a,invalid,d,'smart',deadline,env=dict(a.env,OLM_REFUSAL_TRACE=str(d/'absent'/'trace')))
            assert (missing_result,missing_raw)==(plain_result,plain_raw)
        historical=json.loads((ROOT/'reports/fuzz/olmtoondilate_20261021.json').read_text())
        historical_smart_unchanged=sum(old['result']['routes']['smart']==new['result']['routes']['smart']
            and old['result']['oracle']==new['result']['oracles']['smart']
            for old,new in zip(historical['cases'],campaign['cases']))
        assert historical_smart_unchanged==300
        old_clusters=[]
        for key,cluster in historical['clusters'].items():
            candidates=[]
            for f in cluster['corpus']:
                case,saved=load_corpus(ROOT/f,a)
                candidates.append((math.prod(case['geometry']),case['index'],f,saved))
            _,_,path,saved=min(candidates)
            old_clusters.append(dict(signature=key,historical_cases=cluster['count'],smallest_saved=path,
                case=saved['case'],paired_routes={r:v['status'] for r,v in saved['result']['routes'].items()},
                current_smart_mismatches=sum(1 for i in cluster['case_indices'] if campaign['cases'][i]['result']['routes']['smart']['status']=='mismatch')))
        production_runs=[v for row in sanitizer_rows for route,v in row['routes'].items() if route!='seed_experiment']
        experiment_runs=[row['routes']['seed_experiment'] for row in sanitizer_rows]
        def totals(rows):
            return dict(renders=len(rows), matching_hash=sum(v['same_raw'] for v in rows),
                errors=sum(v['status']['status']!='ok' for v in rows),
                sanitizer_errors=sum(bool(v['diagnostics']) for v in rows))
        summary=dict(historical_smart_unchanged=historical_smart_unchanged,
            production_sanitized=totals(production_runs), seed_experiment=totals(experiment_runs),
            schema='olm-toondilate-triage/1',jobs=args.jobs,
            campaign_summary=campaign['summary'],campaign_clusters={k:v['count'] for k,v in campaign['clusters'].items()},
            refusal_guard_counts=dict(Counter(g for row in campaign['cases'] for gs in row.get('refusal_guards',{}).values() for g in gs)),
            gate_off=dict(applicable=False,reason='No refused legal case in either route; no top guard to bypass',unblocked=0),
            replay=dict(completed=replay['completed'],matches_saved=sum(x['matches_saved'] for x in replay['replays'])),
            provenance={k:v[1] for k,v in adapters.items()},
            inputs_sha256={str(f.relative_to(ROOT)):sha(f.read_bytes()) for f in [SOURCE,Path(__file__),args.scratch/'campaign.json',args.scratch/'replay.json']},
            historical_clusters=old_clusters,reduced=reduced,guard_control=guard_control,
            sanitizer_summary=dict(routes=sum(len(x['routes']) for x in sanitizer_rows),
                same_raw=sum(v['same_raw'] for x in sanitizer_rows for v in x['routes'].values()),
                errors=sum(v['status']['status']!='ok' for x in sanitizer_rows for v in x['routes'].values()),
                diagnostics=sum(bool(v['diagnostics']) for x in sanitizer_rows for v in x['routes'].values())),
            sanitizer_failures=[x for x in sanitizer_rows if any(v['diagnostics'] or not v['same_raw'] or v['status']['status']!='ok' for v in x['routes'].values())])
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        print(json.dumps(dict(replay=summary['replay'],production_sanitized=summary['production_sanitized'],seed_experiment=summary['seed_experiment'],
            reduced=len(reduced),seed_stage_disagreements=sum(bool(x['seed_disagreements']) for x in reduced),guards=summary['refusal_guard_counts'])))


if __name__=='__main__': main()
