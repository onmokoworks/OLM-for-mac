#!/usr/bin/env python3
"""Natural PF8 Zoom sampler/writer witnesses and nonzero-alpha restoration.

The original 9d80 sampler has row-major taps and normalizes finite nonzero
alpha. Keep native inputs, reference math and worker binaries unchanged.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess

from PIL import Image
import probe_radialblur_rotation_neutral_20261001 as neutral
public=neutral.public
writer=neutral.writer
BEFORE=public.ROOT/'reports/radialblur_rotation_size_noise_public_20261001.json'
BEFORE_REVISION='750399049261a3b3f8c9b1f9a568bef9b3e11435'
EXTRA=public.ROOT/'reports/radialblur_rotation_size_noise_independent_20261001.json'


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    old='static constexpr bool kStrictNonzeroAlpha = false;'
    assert source.count(old)==1
    source=source.replace(old,'static constexpr bool kStrictNonzeroAlpha = true;')
    replacements={
        'state.alpha = RadialF32Add(RadialF32Add(RadialF32Add(a00, a10), a01), a11);':
        '// Original Zoom 9d80 zeroes its output before accumulating 00,10,01,11.\n\t\tstate.alpha = RadialF32Add(RadialF32Add(RadialF32Add(RadialF32Add(0.0f, a00), a10), a01), a11);',
        'if (strict_nonzero_alpha ? state.alpha != 0.0f : state.alpha > 1.0e-8f) {\n\t\tconst float reciprocal_alpha = RadialF32Div(1.0f, state.alpha);':
        '// Zoom retains accumulated RGB when signed alpha cancels to zero;\n\t// the original sampler then skips only the reciprocal normalization.\n\tif (strict_nonzero_alpha ? (!aex_column_major_taps || state.alpha != 0.0f) : state.alpha > 1.0e-8f) {\n\t\tconst float reciprocal_alpha = state.alpha != 0.0f ? RadialF32Div(1.0f, state.alpha) : 1.0f;',
        'RadialF32Mul(sample(x0, y0, c), a00),\n\t\t\t\t\t\tRadialF32Mul(sample(x1, y0, c), a10))':
        'RadialF32Add(0.0f, RadialF32Mul(sample(x0, y0, c), a00)),\n\t\t\t\t\t\tRadialF32Mul(sample(x1, y0, c), a10))',
    }
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    return source


def affected(capture):
    rows=[r for r in capture['rows'] if r['matrix']=='topology' and r['family']==1 and r['depth']==8
          and not r['results']['classic']['error'] and not r['results']['classic']['raw_exact']]
    assert len(rows)==6
    return rows


def debug_samples(binary,directory,case,points):
    path=directory/'debug.txt';path.unlink(missing_ok=True)
    env=dict(os.environ,OLMRADIALBLUR_DEBUG_DUMP_PATH=str(path),OLMRADIALBLUR_DEBUG_POINTS=';'.join(f'{x},{y}' for x,y in points))
    error,raw,_=public.mac_render(binary,directory,case,'classic',env);assert not error
    result={}
    for line in path.read_text().splitlines():
        if not line.startswith('OLMRADIALBLUR_DEBUG_POINT kind=zoom '):continue
        x,y=map(int,re.search(r' x=(\d+) y=(\d+) ',line).groups())
        values={}
        for key in ['sample_rgba','accum_rgba','normalized_rgba']:
            values[key]=struct.pack('<4f',*[float.fromhex(x) for x in re.search(key+r'_hex=\(([^)]+)\)',line)[1].split(',')])
        values['input_signature']=line.split(' sample_rgba=',1)[0]+' '+line.split(' cell_valid=',1)[1]
        result[(x,y)]=values
    assert set(result)==set(points)
    return raw,result


def natural(worker,parent,directory,capture,before_binary,after_binary):
    results=[]
    for index,case in enumerate(affected(capture)):
        temp=directory/f'natural_{index}';temp.mkdir();w,h=case['geometry']
        native,frame,_,close,_=public.native_render(parent,temp,case)
        assert public.sha(native)==case['reference_raw_sha256'] and not frame['render_error'] and frame['output']['guards_intact']
        assert close['session_clean'] and not close['unsupported_suite_calls']
        error,before,_=public.mac_render(before_binary,temp,case,'classic');assert not error and public.sha(before)==case['results']['classic']['raw_sha256']
        differences=sorted(set(i//4 for i,(a,b) in enumerate(zip(native,before)) if a!=b));assert differences
        points=[(i%w,i//w) for i in differences[:2]]
        before_raw,before_samples=debug_samples(before_binary,temp,case,points);assert before_raw==before
        after_raw,after_samples=debug_samples(after_binary,temp,case,points);assert after_raw==native
        image=Image.new('RGBA',(w,h));image.putdata([(r,g,b,a) for a,r,g,b in public.initial.pixels(w,h,case['pattern'])]);image.save(temp/'input.png')
        assignments=[f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind']=='a' else '')+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])) for q in public.native_case(case)['parameters']]
        watches=[]
        for x,y in points:
            occurrence=y*w+x+1
            watches+=['--watch',f'function=0x9d80,arg=rdx,size=16,occurrence={occurrence}',
                      '--watch',f'function=0x17400,arg=stack5,size=4,occurrence={occurrence}']
        run=subprocess.run([str(worker),'render-trace-png',str(public.initial.AEX),str(temp/'input.png'),str(temp/'trace.png'),'--pixel-format','argb8',*watches,*assignments],capture_output=True,check=True)
        (temp/'trace.json').write_bytes(run.stdout);report=json.loads(run.stdout)
        assert report['raw_pixel_sha256']==public.sha(native) and not report['render_error'] and report['guards_intact']
        assert not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
        smart=next(q for q in report['execution_traces'] if q['selector']=='SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses'] and not smart['trace_configuration']['unhookable_watches']
        witnesses={q['watch_id']:q for q in smart['memory_witnesses']};assert len(witnesses)==2*len(points)
        selected=[]
        for point_index,(x,y) in enumerate(points):
            sample=witnesses[f'watch-{point_index*2+1}'];output=witnesses[f'watch-{point_index*2+2}']
            native_sample=bytes.fromhex(sample['after']['hex']);native_pixel=bytes.fromhex(output['after']['hex'])
            old=before_samples[(x,y)];new=after_samples[(x,y)];alpha=struct.unpack_from('<f',native_sample,12)[0]
            assert native_sample==new['sample_rgba']
            # The old threshold skips both RGB accumulation and normalization.
            # Compare the actual input taps/coordinates, rather than incorrectly
            # assuming its diagnostic accumulated RGB had been evaluated.
            assert old['input_signature']==new['input_signature']
            assert old['accum_rgba'][:12]==b'\0'*12
            assert old['sample_rgba'][:12]==b'\0'*12
            assert math.isfinite(alpha) and alpha!=0 and alpha<=1e-8
            offset=(y*w+x)*4;assert native_pixel==native[offset:offset+4] and native_sample[12:]==old['sample_rgba'][12:]
            assert sample['pc_rva']==0x5e68 and output['pc_rva']==0x7c14
            selected.append({'coordinate':[x,y],'alpha':alpha,'native_sampler_rgba_f32_le_hex':native_sample.hex(),
                             'before_sampler_rgba_f32_le_hex':old['sample_rgba'].hex(),'after_sampler_rgba_f32_le_hex':new['sample_rgba'].hex(),
                             'accum_rgba_f32_le_hex':new['accum_rgba'].hex(),'before_argb8_hex':before[offset:offset+4].hex(),
                             'native_writer_argb8_hex':native_pixel.hex(),'after_argb8_hex':after_raw[offset:offset+4].hex()})
        results.append({'case':case,'selected_points':selected,'before_raw_sha256':public.sha(before),'native_raw_sha256':public.sha(native),
                        'after_raw_sha256':public.sha(after_raw),'trace_sha256':public.sha(run.stdout),'guard_intact':True,'trace_resident_raw_exact':True,
                        'before_different_bytes':sum(a!=b for a,b in zip(native,before))})
        print('ZOOM_ALPHA_NATURAL',case['row_index'],[(q['coordinate'],q['alpha']) for q in selected],flush=True)
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--parent-worker',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    before=json.loads(BEFORE.read_text());extra=json.loads(EXTRA.read_text());source=before_source();candidate=candidate_source(source)
    start_source=public.sha(public.SOURCE.read_bytes());build=json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes())==build['worker_sha256'] and public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    before_binary=public.build(args.output/'before',source);binaries={'o2':public.build(args.output/'o2',candidate),'san':public.build(args.output/'san',candidate,True)}
    witnesses=natural(args.worker,args.parent_worker,args.output,before,before_binary,binaries['o2'])
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1');rows=[]
    for index,case in enumerate(before['rows']):
        results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,env);old=case['results'][command]
                assert error==old['error'] and metadata==old['metadata']
                result={'error':error,'raw_sha256':public.sha(raw) if not error else None,'raw_exact':not error and public.sha(raw)==case['reference_raw_sha256'],
                        'metadata':metadata,'before_raw_exact':old['raw_exact'],'before_raw_unchanged':(public.sha(raw) if not error else None)==old['raw_sha256']}
                if name=='o2':results[command]=result
                else:assert result==results[command]
        row={key:copy.deepcopy(case[key]) for key in ['family','geometry','depth','pattern','state','parameters','group','matrix','row_index','input_sha256','reference_raw_sha256','parent_raw_sha256']};row['results']=results;rows.append(row)
        if (index+1)%128==0:print('ZOOM_ALPHA_PUBLIC',index+1,flush=True)
    for case in extra['rows']:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,env);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    assert public.sha(public.SOURCE.read_bytes())==start_source
    summary=writer.summarize(rows);assert summary['lost_exact']==0
    import pefile
    pe=pefile.PE(str(public.initial.AEX))
    report={'schema':'radialblur.zoom-nonzero-alpha-public/1','before_revision':BEFORE_REVISION,'source_before_sha256':before['source_sha256'],'source_sha256':public.sha(candidate.encode()),
            'header_sha256':before['header_sha256'],'aex_sha256':before['aex_sha256'],'controlled_worker_sha256':before['controlled_worker_sha256'],'window_worker_sha256':build['worker_sha256'],
            'probe_start_source_sha256':start_source,'production_source_changed_during_probe':False,'summary':summary,'rows':rows,'natural_witnesses':witnesses,
            'public_replay_count':2776,'retained_independent_public_replay_count':384,'retained_independent_report_sha256':public.sha(EXTRA.read_bytes()),
            'matrix_summaries':{m:writer.summarize([r for r in rows if r['matrix']==m]) for m in before['matrix_summaries']},
            'native_sampler_rva':'0x9d80','native_zero_compare_code_sha256':public.sha(pe.get_data(0x9f67,0x31)),
            'native_sampler_callsite_code_sha256':public.sha(pe.get_data(0x5e43,0x2a)),
            'native_sampler_abi':'RCX RGBA plane, RDX output, R8 radius width, R9 angular height, stack5 float-word row stride, stack6/7 FLOAT32 radius/angular coordinates.',
            'dependencies_sha256':{str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),BEFORE,EXTRA,public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},
            'claims_not_made':['Finite nonzero-alpha/frames do not prove NaN/unordered, arbitrary inputs/settings, Zoom Inner Edge, Size25, native Windows ISA/RCPPS/general UCRT/AE/UI/save/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('ZOOM_ALPHA_DONE',summary,flush=True)


if __name__=='__main__':main()
