#!/usr/bin/env python3
"""C06: shrink a Smart mismatch and compare passive original-AEX Zoom stages.

Reuses the F08/Zoom-fade plane instrumentation. A scratch source may select
experimental admission, but the retained AEX worker and raw comparison do not
change. Reports bind every traced original output to the public Smart oracle.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import shutil
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
import capstone
import pefile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--indices', default='163')
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--experiment', choices=('border-gate-only', 'legacy-radius'),
                    help='Create a scratch-only source experiment; never edit production')
    ap.add_argument('--cases-from', type=Path, default=None)
    ap.add_argument('--regenerate', action='store_true')
    ap.add_argument('--revision', help='Read production source at this revision; never edit the checkout')
    ap.add_argument('--measure-only', action='store_true')
    ap.add_argument('--align-worlds', action='store_true')
    ap.add_argument('--sampler-only', action='store_true')
    ap.add_argument('--prefix-only', action='store_true', help='F46-compatible 4096-byte polar/scatter/prepass prefixes; no full-plane claim')
    ap.add_argument('--no-shrink', action='store_true')
    ap.add_argument('--legacy-trace-angles', action='store_true', help='Old trace CLI; only zero Angle controls are supported')
    ap.add_argument('--trace-worker', type=Path, default=Path('/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker'))
    args = ap.parse_args()
    if args.regenerate:
        args.cases_from = None
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    main = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    worker = args.trace_worker
    public.SOURCE = args.source.resolve()
    tracer = args.trace_worker
    adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=30, main=main, worker=worker))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    os.environ.pop('OLM_RADIAL_CANDIDATE_BYPASS', None)
    deadline = time.monotonic()+1200
    if args.revision:
        snapshot=out/'baseline.cpp'
        snapshot.write_bytes(subprocess.check_output(['git','show',args.revision+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=ROOT))
        snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
        public.SOURCE=snapshot
    if args.experiment:
        source = public.SOURCE.read_text()
        if args.experiment == 'border-gate-only':
            old = 'info.repeat_border != FALSE && std::isfinite(info.ratio) &&'
            new = 'std::isfinite(info.ratio) &&'
        else:
            old = '\tif (use_native_zoom_baseline)\n\t\tZoomRadiusBoundsAEX(w, h, (float)cx, (float)cy, (float)ratio, &min_r, &max_r);'
            new = ''
        assert source.count(old) == 1, 'Experiment source boundary changed'
        snapshot = out/'experiment.cpp'
        snapshot.write_text(source.replace(old, new))
        snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
        public.SOURCE = snapshot
    provenance = adapter.prepare(out, deadline)
    pe = pefile.PE(str(adapter.aex))
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    aex_static = {}
    for name, start, end in [('rotation_sampler_dispatch', 0x49cc, 0x49ff),
                             ('zoom_sampler_dispatch', 0x5984, 0x59b6),
                             ('zoom_scalar_calls', 0x5ade, 0x5b3f),
                             ('zoom_no_repeat_scalar', 0xa550, 0xa6a0),
                             ('zoom_radius_caller', 0x5835, 0x5893),
                             ('zoom_radius_bounds', 0xa8f0, 0xa9c5)]:
        aex_static[name] = [dict(rva=hex(i.address-image_base), bytes=i.bytes.hex(),
                                 instruction=i.mnemonic+' '+i.op_str)
                            for i in decoder.disasm(pe.get_data(start, end-start), image_base+start)]
    public.initial.ROOT = main
    public.initial.AEX = adapter.aex
    if not args.measure_only:
        source = public.SOURCE.read_text()
        hp=out/'planes.cpp'
        body=zoom.plane_harness().replace('w>64||h>64', 'w>256||h>256')
        marker='dump("polar.f32",probe_polar.data(),probe_polar.size()*4);'
        assert body.count(marker)==1
        extra = 'dump("weights.f32",probe_weights.data(),probe_weights.size()*4);'
        if args.prefix_only:
            extra += 'dump("prepass_factor.f32",probe_factor.data(),probe_factor.size()*4);'
        hp.write_text(body.replace(marker,marker+extra))
        old=public.initial.HARNESS; public.initial.HARNESS=hp
        passive = zoom.passive_source(source)
        marker='static FloatImage BuildZoomAEXOuterOnlyPolar('
        start=passive.index(marker)
        pos=passive.index('const A_long radius_count = polar.width;',start)
        passive=passive[:pos]+'probe_weights=weights;\n\t'+passive[pos:]
        passive=passive[:start]+'static std::vector<float> probe_weights;\n'+passive[start:]
        if args.prefix_only:
            at=passive.index('static FloatImage BuildZoomAEXOuterOnlyPolar(')
            passive=passive[:at]+'static std::vector<float> probe_factor;\n'+passive[at:]
            old='std::atomic<A_long> next_row(0);'
            at=passive.index(old,passive.index('static FloatImage BuildZoomAEXOuterOnlyPolar('))
            passive=passive[:at]+'probe_factor.assign(cell_count,0.0f);\n\t'+passive[at:]
            old='float source_scalar = source_scalar_plane[cell];'
            at=passive.index(old,passive.index('static FloatImage BuildZoomAEXOuterOnlyPolar('))
            passive=passive[:at]+'probe_factor[cell]=factor;\n\t'+passive[at:]
        binary=public.build(out/'planes_build',passive)
        provenance['passive_source_sha256'] = sha(passive.encode())
        provenance['passive_binary_sha256'] = sha(binary.read_bytes())
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
            if saved.get('expected_smart_sha256'):
                assert result['oracle'].get('raw_sha256') == saved['expected_smart_sha256'], 'Saved original reference changed'
            reduced=result; reduction={'replayed_saved_input':True}
        else:
            case=adapter.generate(args.seed,index)
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
        run=subprocess.run([str(binary),*map(str,case['geometry']),str(case['depth']),'smart',str(config)],input=case['pixels'],capture_output=True,check=True,timeout=60,env=dict(os.environ,ZOOM_PROBE_DIRECTORY=str(planes)))
        assert b'ERROR 0\n' in run.stderr,run.stderr
        row=dict(index=index,case={k:v for k,v in case.items() if k!='pixels'},input_hex=case['pixels'].hex(),original=result,reduced=reduced,reduction=reduction,mac_sha256=sha(run.stdout))
        assert row['mac_sha256'] == reduced['routes']['smart']['raw_sha256'], 'Instrumentation changed Smart output'
        w,h=case['geometry'];image=Image.new('RGBA',(w,h))
        if case['depth'] == 8:
            packed = case['pixels']
        else:
            # The retained trace CLI accepts PNG, not raw typed input. Only
            # trace inputs whose conversion reproduces every original byte.
            fmt, scale = ('H',32768) if case['depth']==16 else ('f',1)
            values=[v for (v,) in struct.iter_unpack('<'+fmt,case['pixels'])]
            packed=bytes(round(v/scale*255) for v in values)
            restored=b''.join(struct.pack('<'+fmt, (v*32768+127)//255 if fmt=='H' else v/255) for v in packed)
            assert restored==case['pixels'], 'Typed input is not losslessly representable through PNG trace transport'
        image.putdata([(r,g,b,a) for a,r,g,b in struct.iter_unpack('4B',packed)]);image.save(directory/'input.png')
        command=[str(tracer),'render-trace-png',str(adapter.aex),str(directory/'input.png'),str(directory/'trace.png'),'--pixel-format',{8:'argb8',16:'argb16',32:'argb32f'}[case['depth']]]
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
        assert row['trace_raw_sha256'] == reduced['oracle']['raw_sha256'], 'Trace/public Smart reference split'
        config=bytes.fromhex(watches['watch-1']['before']['hex'])
        minimum,maximum=struct.unpack_from('<2i',config,24);radial=maximum-minimum+1
        angular=int(zoom.fields.f32(360/struct.unpack_from('<f',config,16)[0]));cells=radial*angular
        row['native_dimensions']=[radial,angular];row['mac_dimensions']=list(struct.unpack('<2i',(planes/'dimensions.i32').read_bytes()))
        weight_size=(planes/'weights.f32').stat().st_size
        data,weight_watches=trace(['--watch',f'function=0xb680,arg=rcx,size={weight_size},occurrence=1'],'weight_trace.json')
        native_weights=bytes.fromhex(weight_watches['watch-1']['after']['hex'])
        (directory/'native_weights.f32').write_bytes(native_weights)
        row['weights']=zoom.fields.compare_words(native_weights,(planes/'weights.f32').read_bytes())
        specs=[('polar',0xb150,'rdx',None,cells*16,'before'),('eligible',0xa9d0,'stack5',None,cells,'before'),('span',0xa9d0,'r9',None,cells*4,'before'),('preaccum',0xb150,'rcx',0x4210,cells*16,'after'),('premax',0xb150,'rcx',0x4218,cells*4,'after'),('accum',0xa9d0,'rcx',0x4210,cells*16,'after'),('max',0xa9d0,'rcx',0x4218,cells*4,'after'),('normalized',0x9d80,'rcx',None,cells*16,'before')]
        if args.prefix_only:
            specs=[('polar',0xb150,'rdx',None,min(cells*16,4096),'before'),
                   ('span',0xa9d0,'r9',None,min(cells*4,4096),'before'),
                   ('prepass_factor',0xb150,'r9',None,min(cells*4,4096),'before')]
            row['trace_scope']='first 4096 bytes per plane only'
        row['planes']={}
        if args.sampler_only:
            specs=[]
        # Separate runs keep each trace within the worker's witness limit.
        for name,rva,arg,deref,size,when in specs:
            options=[]
            for offset in range(0,size,4096):
                spec=f'function={hex(rva)},arg={arg},size={min(4096,size-offset)},offset={offset},occurrence=1'
                if deref is not None:spec+=f',deref={hex(deref)}'
                if args.prefix_only: spec=spec.replace(f',offset={offset}','')
                options+=['--watch',spec]
            data,watches=trace(options,name+'_trace.json')
            assert data['raw_pixel_sha256']==row['trace_raw_sha256']
            native=b''.join(bytes.fromhex(watches[f'watch-{i+1}'][when]['hex']) for i in range(len(options)//2))
            suffix='.u8' if name=='eligible' else '.f32';(directory/('native_'+name+suffix)).write_bytes(native)
            mac=(planes/(name+suffix)).read_bytes()
            if args.prefix_only: mac=mac[:size]
            if not mac:
                row['planes'][name]={'status':'not_executed_in_mac_path','native_sha256':sha(native)}
                continue
            if len(native)!=len(mac):
                row['planes'][name] = dict(status='dimensions_differ', native_bytes=len(native),
                                           mac_bytes=len(mac), native_sha256=sha(native), mac_sha256=sha(mac))
                continue
            row['planes'][name]=zoom.fields.compare_words(native,mac) if name!='eligible' else dict(different_bytes=sum(a!=b for a,b in zip(native,mac)))
        row['sampler_rgba_hex']=[]
        row['coordinate_radius_angle_hex']=[]
        # Keep large unshrunk witnesses below the retained worker's watch cap.
        for start in range(0,0 if args.prefix_only else w*h,128):
            count=min(128,w*h-start)
            sample_options=[]
            coordinates=[]
            for occurrence in range(start+1,start+count+1):
                sample_options+=['--watch',f'function=0x9d80,arg=rdx,size=16,occurrence={occurrence}']
                coordinates+=['--watch',f'function=0xa850,arg=r9,size=4,occurrence={occurrence}',
                              '--watch',f'function=0xa850,arg=stack5,size=4,occurrence={occurrence}']
            data,watches=trace(sample_options,f'sampler_trace_{start}.json')
            row['sampler_rgba_hex'] += [watches[f'watch-{i+1}']['after']['hex'] for i in range(count)]
            data,watches=trace(coordinates,f'coordinate_trace_{start}.json')
            row['coordinate_radius_angle_hex'] += [watches[f'watch-{i+1}']['after']['hex'] for i in range(count*2)]
        rows.append(row)
        (out/'report.json').write_text(json.dumps(dict(provenance=provenance,tracer_sha256=sha(tracer.read_bytes()),aex_static=aex_static,rows=rows),indent=2)+'\n')
        print(index,case['geometry'],row['trace_raw_sha256']==reduced['oracle']['raw_sha256'],{k:v.get('different_words',v.get('different_bytes')) for k,v in row['planes'].items()},flush=True)
    shutil.rmtree(out/'build', ignore_errors=True)
    shutil.rmtree(out/'planes_build', ignore_errors=True)

if __name__=='__main__':main()
