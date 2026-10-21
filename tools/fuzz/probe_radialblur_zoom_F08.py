#!/usr/bin/env python3
"""F08: reproduce T05 offset witnesses and capture passive Zoom planes.

No admission changes are promoted. Inputs use retained shrunk T05 witnesses;
--regenerate reconstructs and reduces the original seed/index cases.
All subprocess temporary files must remain under the supplied scratch directory.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/emulation'))
from adapters.radialblur import Adapter, public
from core import evaluate, shrink, sha
import probe_radialblur_zoom_fade_20261002 as zoom
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--indices', default='271,486')
    ap.add_argument('--cases-from', type=Path, default=ROOT/'tools/fuzz/fixtures/radialblur_zoom_F08.json')
    ap.add_argument('--regenerate', action='store_true')
    ap.add_argument('--revision', help='Read production source at this revision; never edit the checkout')
    ap.add_argument('--measure-only', action='store_true')
    ap.add_argument('--align-worlds', action='store_true')
    ap.add_argument('--sampler-only', action='store_true')
    ap.add_argument('--no-shrink', action='store_true')
    ap.add_argument('--legacy-trace-angles', action='store_true', help='Old trace CLI; only zero Angle controls are supported')
    ap.add_argument('--trace-worker', type=Path, default=Path('/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker'))
    args = ap.parse_args()
    if args.regenerate:
        args.cases_from = None
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/F08-radial-zoom-general-first-divergence')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    main = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    t05 = json.loads((ROOT/'reports/fuzz/radialblur_t05_bypass_zoom_profile_20261021.json').read_text())
    worker = Path(t05['provenance']['worker_path'])
    tracer = args.trace_worker
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=30, main=main, worker=worker))
    os.environ['OLM_RADIAL_CANDIDATE_BYPASS']='unadmitted-zoom-profile'
    deadline = time.monotonic()+1200
    if args.revision:
        snapshot=out/'baseline.cpp'
        snapshot.write_bytes(subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT))
        snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
        public.SOURCE=snapshot
    provenance = adapter.prepare(out, deadline)
    public.initial.ROOT = main
    public.initial.AEX = adapter.aex
    if not args.measure_only:
        source = '#define OLM_RADIAL_EXPERIMENT_BYPASS "unadmitted-zoom-profile"\n'+public.SOURCE.read_text()
        hp=out/'planes.cpp'; hp.write_text(zoom.plane_harness())
        old=public.initial.HARNESS; public.initial.HARNESS=hp
        binary=public.build(out/'planes_build',zoom.passive_source(source))
        public.initial.HARNESS=old
    rows=[]
    for index in map(int,args.indices.split(',')):
        directory=out/str(index);directory.mkdir()
        if args.cases_from:
            saved=next(r for r in json.loads(args.cases_from.read_text())['rows'] if r['index']==index)
            case=dict(saved['case'],pixels=bytes.fromhex(saved['input_hex']))
            if args.align_worlds:
                case.update(input_padding=0,output_padding=0)
            result=evaluate(adapter,case,directory,deadline)
            reduced=result; reduction={'replayed_saved_input':True}
        else:
            case=adapter.generate(1,index)
            result=evaluate(adapter,case,directory,deadline)
            if args.no_shrink:
                reduced=result; reduction={'not_shrunk':True}
            else:
                case,reduced,reduction=shrink(adapter,case,result,directory,deadline,64)
        if args.measure_only:
            row=dict(index=index,case={k:v for k,v in case.items() if k!='pixels'},input_hex=case['pixels'].hex(),original=result,reduced=reduced,reduction=reduction)
            rows.append(row)
            (out/'report.json').write_text(json.dumps(dict(provenance=provenance,rows=rows),indent=2)+'\n')
            print(index,case['geometry'],{k:v['status'] for k,v in reduced['routes'].items()},flush=True)
            continue
        (directory/'input.raw').write_bytes(case['pixels'])
        config=directory/'parameters.txt';config.write_text(public.initial.config_text(case))
        planes=directory/'mac';planes.mkdir()
        run=subprocess.run([str(binary),*map(str,case['geometry']),str(case['depth']),'classic',str(config)],input=case['pixels'],capture_output=True,check=True,timeout=60,env=dict(os.environ,ZOOM_PROBE_DIRECTORY=str(planes)))
        assert b'ERROR 0\n' in run.stderr,run.stderr
        row=dict(index=index,case={k:v for k,v in case.items() if k!='pixels'},input_hex=case['pixels'].hex(),original=result,reduced=reduced,reduction=reduction,mac_sha256=sha(run.stdout))
        assert case['depth']==8
        w,h=case['geometry'];image=Image.new('RGBA',(w,h));image.putdata([(r,g,b,a) for a,r,g,b in struct.iter_unpack('4B',case['pixels'])]);image.save(directory/'input.png')
        command=[str(tracer),'render-trace-png',str(adapter.aex),str(directory/'input.png'),str(directory/'trace.png'),'--pixel-format','argb8']
        assignments=zoom.assignments(case)
        if args.legacy_trace_angles:
            assert all(p['value']==0 for p in case['parameters'] if p['kind']=='a')
            assignments=[p for p in assignments if ':angle=' not in p]
        def trace(watches,name):
            run=subprocess.run(command+watches+assignments,capture_output=True,timeout=60)
            (directory/(name+'.stderr')).write_bytes(run.stderr)
            run.check_returncode()
            (directory/name).write_bytes(run.stdout)
            data=json.loads(run.stdout)
            assert not data['render_error'] and data['guards_intact']
            assert not data['unsupported_suite_calls'] and not data['dropped_unsupported_suite_calls']
            stage=next(t for t in data['execution_traces'] if t['selector']=='SMART_RENDER')
            assert not stage['truncated'] and not stage['dropped_memory_witnesses']
            return data,{q['watch_id']:q for q in stage['memory_witnesses']}
        data,watches=trace(['--watch','function=0xb150,arg=rcx,size=64,occurrence=1'],'config_trace.json')
        row['trace_raw_sha256']=data['raw_pixel_sha256']
        config=bytes.fromhex(watches['watch-1']['before']['hex'])
        minimum,maximum=struct.unpack_from('<2i',config,24);radial=maximum-minimum+1
        angular=int(zoom.fields.f32(360/struct.unpack_from('<f',config,16)[0]));cells=radial*angular
        row['native_dimensions']=[radial,angular];row['mac_dimensions']=list(struct.unpack('<2i',(planes/'dimensions.i32').read_bytes()))
        specs=[('polar',0xb150,'rdx',None,cells*16,'before'),('eligible',0xa9d0,'stack5',None,cells,'before'),('span',0xa9d0,'r9',None,cells*4,'before'),('preaccum',0xb150,'rcx',0x4210,cells*16,'after'),('premax',0xb150,'rcx',0x4218,cells*4,'after'),('accum',0xa9d0,'rcx',0x4210,cells*16,'after'),('max',0xa9d0,'rcx',0x4218,cells*4,'after'),('normalized',0x9d80,'rcx',None,cells*16,'before')]
        row['planes']={}
        if args.sampler_only:
            specs=[]
        # Separate runs keep each trace within the worker's witness limit.
        for name,rva,arg,deref,size,when in specs:
            options=[]
            for offset in range(0,size,4096):
                spec=f'function={hex(rva)},arg={arg},size={min(4096,size-offset)},offset={offset},occurrence=1'
                if deref is not None:spec+=f',deref={hex(deref)}'
                options+=['--watch',spec]
            data,watches=trace(options,name+'_trace.json')
            assert data['raw_pixel_sha256']==row['trace_raw_sha256']
            native=b''.join(bytes.fromhex(watches[f'watch-{i+1}'][when]['hex']) for i in range(len(options)//2))
            suffix='.u8' if name=='eligible' else '.f32';(directory/('native_'+name+suffix)).write_bytes(native)
            mac=(planes/(name+suffix)).read_bytes()
            if not mac:
                row['planes'][name]={'status':'not_executed_in_mac_path','native_sha256':sha(native)}
                continue
            assert len(native)==len(mac)
            row['planes'][name]=zoom.fields.compare_words(native,mac) if name!='eligible' else dict(different_bytes=sum(a!=b for a,b in zip(native,mac)))
        sample_options=[]
        for occurrence in range(1,w*h+1):
            sample_options+=['--watch',f'function=0x9d80,arg=rdx,size=16,occurrence={occurrence}']
        data,watches=trace(sample_options,'sampler_trace.json')
        row['sampler_rgba_hex']=[watches[f'watch-{i+1}']['after']['hex'] for i in range(w*h)]
        coordinates=[]
        for occurrence in range(1,w*h+1):
            coordinates+=['--watch',f'function=0xa850,arg=r9,size=4,occurrence={occurrence}',
                          '--watch',f'function=0xa850,arg=stack5,size=4,occurrence={occurrence}']
        data,watches=trace(coordinates,'coordinate_trace.json')
        row['coordinate_radius_angle_hex']=[watches[f'watch-{i+1}']['after']['hex'] for i in range(w*h*2)]
        rows.append(row)
        (out/'report.json').write_text(json.dumps(dict(provenance=provenance,tracer_sha256=sha(tracer.read_bytes()),rows=rows),indent=2)+'\n')
        print(index,case['geometry'],row['trace_raw_sha256']==reduced['oracle']['raw_sha256'],{k:v.get('different_words',v.get('different_bytes')) for k,v in row['planes'].items()},flush=True)

if __name__=='__main__':main()
