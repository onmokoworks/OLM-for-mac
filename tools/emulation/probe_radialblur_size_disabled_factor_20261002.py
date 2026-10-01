#!/usr/bin/env python3
"""Read-only original disabled Size branch: no scanner and uniform factors."""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_size_enabled_20261002 as enabled
public=enabled.public
runs=enabled.ranges.runs
HARNESS=Path(runs.__file__).with_name('radialblur_size_factor_sdk_harness_20261001.cpp')


def trace(worker,directory,case):
    w,h=case['geometry'];image=Image.new('RGBA',(w,h))
    image.putdata([(r,g,b,a) for a,r,g,b in runs.pixels(case)]);image.save(directory/'input.png')
    assignments=[f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind']=='a' else '')+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])) for q in public.native_case(case)['parameters']]
    watches=[]
    for spec in ['function=0x6aa0,arg=rcx,size=80,occurrence=1',f'function=0x6aa0,arg=rcx,deref=0x88,size={w*h*4},occurrence=1','function=0x8930,arg=rcx,size=16,occurrence=1']:
        watches+=['--watch',spec]
    run=subprocess.run([str(worker),'render-trace-png',str(public.initial.AEX),str(directory/'input.png'),str(directory/'trace.png'),'--pixel-format','argb32f',*watches,*assignments],capture_output=True,check=True)
    (directory/'trace.json').write_bytes(run.stdout);report=json.loads(run.stdout)
    assert not report['render_error'] and report['guards_intact'] and not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
    smart=next(t for t in report['execution_traces'] if t['selector']=='SMART_RENDER')
    assert not smart['truncated'] and not smart['dropped_memory_witnesses'] and not smart['trace_configuration']['unhookable_watches']
    witness={q['watch_id']:q for q in smart['memory_witnesses']};assert set(witness)=={'watch-1','watch-2'}
    work=bytes.fromhex(witness['watch-1']['before']['hex']);factor=bytes.fromhex(witness['watch-2']['before']['hex'])
    assert len(work)==80 and work[0x44]==0 and factor==struct.pack('<f',1.0)*(w*h)
    (directory/'work.bin').write_bytes(work);(directory/'factor.bin').write_bytes(factor)
    return factor,dict(trace_sha256=public.sha(run.stdout),raw_sha256=report['raw_pixel_sha256'],witness_count=2,requested_watch_count=3,guards_intact=True,enabled=0,normalized_float_word=f'{struct.unpack_from("<I",work,0x40)[0]:08x}',component_scanner_reached=False)


def factor_maps(worker,directory,source):
    values=[enabled.values()[i] for i in [0,4,10,13,17]];cases=[]
    for seed in runs.fixtures():
        if seed['size']!=25 or seed['pattern'] not in ['empty','opaque','mixed_edges','two_floating_runs'] or seed['geometry']!=[7,5]:continue
        for value in values:
            case=copy.deepcopy(seed);case['size']=value;case['row_index']=len(cases)
            next(q for q in case['parameters'] if q['slot']==22)['value']=value;cases.append(case)
    assert len(cases)==20
    previous=public.initial.HARNESS
    try:
        public.initial.HARNESS=HARNESS
        binaries=[public.build(directory/('factor_san' if sanitize else 'factor_o2'),source,sanitize) for sanitize in [False,True]]
    finally:public.initial.HARNESS=previous
    rows=[]
    for case in cases:
        temp=directory/f"map_{case['row_index']}";temp.mkdir();factor,evidence=trace(worker,temp,case)
        for binary in binaries:
            for depth in [8,16,32]:
                ip=temp/f'input_{depth}.raw';ip.write_bytes(runs.source(case,depth))
                # This helper takes FLOAT32. Materialize the getter first;
                # direct strtof(requested DOUBLE text) skips its tie rounding.
                getter=struct.unpack('<f',struct.pack('<f',case['size']))[0]
                run=subprocess.run([str(binary),*map(str,case['geometry']),str(depth),str(getter),str(ip)],capture_output=True,check=True,env=enabled.ranges.ENV)
                assert run.stdout==factor and run.stderr==b'AREAS\n'
        rows.append(dict(case=case,trace=evidence,factor_sha256=public.sha(factor),word_count=len(factor)//4,component_areas=[],typed_sdk_replays=6))
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    source=enabled.candidate_source(enabled.before_source());before=json.loads(enabled.BEFORE.read_text());start=public.sha(public.SOURCE.read_bytes())
    assert public.sha(args.worker.read_bytes())==before['window_worker_sha256'] and public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    rows=factor_maps(args.worker,args.output,source);assert public.sha(public.SOURCE.read_bytes())==start
    report=dict(schema='radialblur.size-disabled-factor/1',source_sha256=public.sha(source.encode()),aex_sha256=before['aex_sha256'],window_worker_sha256=before['window_worker_sha256'],probe_start_source_sha256=start,production_source_changed_during_probe=False,summary=dict(native_disabled_maps=20,factor_words=700,typed_sdk_replays=120),rows=rows,dependencies_sha256={str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),Path(enabled.__file__),HARNESS,enabled.BEFORE]},claims_not_made=['Read-only local original factor planes and finite typed SDK cases do not prove native Windows AE/UCRT, arbitrary allocator/input/settings or all-ten completion.'])
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('SIZE_DISABLED_FACTOR_DONE',report['summary'],flush=True)


if __name__=='__main__':main()
