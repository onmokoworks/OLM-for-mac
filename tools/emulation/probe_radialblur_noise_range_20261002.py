#!/usr/bin/env python3
"""Legal Noise percentage and zero Type2 admission; original mixing unchanged."""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_size_enabled_20261002 as enabled
public=enabled.public
BEFORE=public.ROOT/'reports/radialblur_size_enabled_public_20261002.json'
BEFORE_REVISION='a4cfa436b407de1ce17ce23a9ca1dc78a18afcf3'
ENV=enabled.ranges.ENV


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    old='if (info.noise_variation != 25.0 && info.noise_variation != 100.0) return false;';assert source.count(old)==1
    source=source.replace(old,'if (!std::isfinite(info.noise_variation) || info.noise_variation < 0.0 || info.noise_variation > 100.0) return false;')
    old='if (info.noise_variation == 0.0) return info.noise_type == 1;';assert source.count(old)==1
    source=source.replace(old,'if (info.noise_variation == 0.0) return info.noise_type == 1 || info.noise_type == 2;')
    start=source.index('static bool IsGenericSizeNoiseControlProfile(');end=source.index('static bool IsGenericRadialControlProfile(',start);part=source[start:end]
    old='(info.noise_variation == 25.0 || info.noise_variation == 100.0)';assert part.count(old)==1
    return source[:start]+part.replace(old,'(std::isfinite(info.noise_variation) && info.noise_variation >= 0.0 && info.noise_variation <= 100.0)')+source[end:]


def independent_cases():
    cases=[]
    def add(family,depth,noise_type,nv,sv,changes=None,group='integer'):
        params=public.initial.settings(family,17,15)
        changes={22:sv,24:nv,25:noise_type,29:3 if noise_type==1 else 10,**(changes or {})}
        for q in params:
            if q['slot'] in changes:q['value']=changes[q['slot']]
        cases.append(dict(family=family,geometry=[17,15],pattern='diagonal',depth=depth,state=group,parameters=params,group=group,matrix='noise_range',row_index=len(cases)))
    for family in [1,2]:
        for noise_type in [1,2]:
            for value in range(1,101):add(family,32,noise_type,value,37.5)
            for value in [*enabled.values(),33.3,50.000003814697266,99.99999237060547]:
                for size in [0,37.5]:
                    for depth in [8,16,32]:add(family,depth,noise_type,value,size,{7:37,10:3,13:37},'fraction_dual_fade')
    assert len(cases)==952
    return cases


def retained_cases():
    return enabled.ranges.retained_cases(json.loads(enabled.ranges.BEFORE.read_text()))+json.loads(enabled.BEFORE.read_text())['independent_rows']+json.loads(BEFORE.read_text())['independent_rows']


def passive_source(source):
    helper='''static void ProbeNoiseScalarDump(const char *name, const std::vector<float>& plane, size_t count)
{
    const char *directory=std::getenv("NOISE_SCALAR_PROBE_DIRECTORY");
    if (!directory) return;
    char path[1024]; std::snprintf(path,sizeof(path),"%s/%s.f32",directory,name);
    FILE *file=std::fopen(path,"wb");
    if (!file) std::abort();
    if (plane.size()<count || std::fwrite(plane.data(),sizeof(float),count,file)!=count) std::abort();
    std::fclose(file);
}

'''
    start=source.index('template <typename PixelT>\nstatic PF_Err RenderZoomTyped(');end=source.index('static PF_Err RenderZoom8(',start);part=source[start:end]
    marker='\t\t\tif ((use_generic_baseline && info.noise_variation != 0.0) || use_generic_size_noise ||';assert part.count(marker)==1
    part=part.replace(marker,'\t\tProbeNoiseScalarDump("base",source_factor_with_guard,(size_t)w*h);\n'+marker)
    marker='\tconst float cx_f = (float)cx;';assert part.count(marker)==1
    part=part.replace(marker,'\tProbeNoiseScalarDump("mixed",source_factor_with_guard,(size_t)w*h);\n'+marker)
    return source[:start]+helper+part+source[end:]


def scalar_maps(worker,directory,cases,source):
    binary=public.build(directory/'scalar_planes',passive_source(source));selected=[]
    for row in cases:
        if row['family']!=1 or row['depth']!=32 or row['group']!='fraction_dual_fade':continue
        value=next(q['value'] for q in row['parameters'] if q['slot']==24)
        if value in [0,enabled.values()[17],33.3,99.99999237060547]:selected.append(row)
    assert len(selected)==16
    results=[]
    for index,case in enumerate(selected):
        temp=directory/f'scalar_{index}';temp.mkdir();w,h=case['geometry']
        image=Image.new('RGBA',(w,h));image.putdata([(r,g,b,a) for a,r,g,b in public.initial.pixels(w,h,case['pattern'])]);image.save(temp/'input.png')
        assignments=enabled.ranges.zoom.assignments(case)
        specs=['function=0x6aa0,arg=rcx,size=256,occurrence=1',f'function=0x6aa0,arg=rcx,deref=0x88,size={w*h*4},occurrence=1',f'function=0x6aa0,arg=rcx,deref=0x90,size={w*h*4},occurrence=1']
        watches=[v for spec in specs for v in ['--watch',spec]]
        run=subprocess.run([str(worker),'render-trace-png',str(public.initial.AEX),str(temp/'input.png'),str(temp/'native.png'),'--pixel-format','argb32f',*watches,*assignments],capture_output=True,check=True)
        (temp/'trace.json').write_bytes(run.stdout);report=json.loads(run.stdout)
        assert not report['render_error'] and report['guards_intact'] and not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
        smart=next(t for t in report['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not smart['truncated'] and not smart['dropped_memory_witnesses'] and not smart['trace_configuration']['unhookable_watches']
        witness={q['watch_id']:q for q in smart['memory_witnesses']};assert len(witness)==3
        work=bytes.fromhex(witness['watch-1']['before']['hex']);base=bytes.fromhex(witness['watch-2']['before']['hex']);mixed=bytes.fromhex(witness['watch-3']['after']['hex'])
        error,raw,_=public.mac_render(binary,temp,case,'classic',dict(ENV,NOISE_SCALAR_PROBE_DIRECTORY=str(temp)))
        assert not error and public.sha(raw)==case['reference_raw_sha256']
        assert (temp/'base.f32').read_bytes()==base and (temp/'mixed.f32').read_bytes()==mixed
        results.append(dict(case=case,normalized_noise_float_word=f'{struct.unpack_from("<I",work,0x3c)[0]:08x}',native_noise_type=struct.unpack_from('<i',work,0x50)[0],smooth_flag=work[0xf8],base_sha256=public.sha(base),mixed_sha256=public.sha(mixed),word_count=w*h,trace_sha256=public.sha(run.stdout),guards_intact=True,base_and_mixed_exact=True))
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    before=json.loads(BEFORE.read_text());source=before_source();candidate=candidate_source(source);source_at_start=public.sha(public.SOURCE.read_bytes())
    assert public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256'] and public.sha(args.worker.read_bytes())==before['window_worker_sha256'] and public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']};old_binary=public.build(args.output/'before',source)
    retained=retained_cases();assert len(retained)==1855
    for case in before['rows']+retained:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    independent=[]
    for case in independent_cases():
        native,frame,_,close,_=public.native_render(args.parent_worker,args.output,case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        old_error,old_raw,_=public.mac_render(old_binary,args.output,case,'classic',ENV);results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);assert not error and raw==native,(case,error)
                result=dict(error=error,raw_sha256=public.sha(raw),raw_exact=True,metadata=metadata,before_error=old_error,before_raw_exact=not old_error and old_raw==native)
                if name=='o2':results[command]=result
                else:assert result==results[command]
        independent.append(dict(case,input_sha256=public.sha(public.fixture(case)),reference_raw_sha256=public.sha(native),results=results))
        if len(independent)%100==0:print('NOISE_RANGE_INDEPENDENT',len(independent),flush=True)
    (args.output/'partial_independent.json').write_text(json.dumps(independent,indent=2)+'\n')
    scalars=scalar_maps(args.worker,args.output,independent,candidate)
    assert public.sha(public.SOURCE.read_bytes())==source_at_start
    import pefile
    pe=pefile.PE(str(public.initial.AEX));rows=copy.deepcopy(before['rows'])
    report=dict(schema='radialblur.noise-range-public/1',before_revision=BEFORE_REVISION,source_before_sha256=before['source_sha256'],source_sha256=public.sha(candidate.encode()),header_sha256=before['header_sha256'],aex_sha256=before['aex_sha256'],controlled_worker_sha256=before['controlled_worker_sha256'],window_worker_sha256=before['window_worker_sha256'],probe_start_source_sha256=source_at_start,production_source_changed_during_probe=False,summary=before['summary'],rows=rows,independent_rows=independent,independent_summary=dict(case_count=952,both_commands_exact=952,before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent),before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent)),retained_independent_case_count=1855,candidate_public_replay_count=14004,scalar_maps=scalars,scalar_map_words=sum(r['word_count'] for r in scalars),native_normalization_code_sha256=public.sha(pe.get_data(0x8889,0x22)),native_procedural_mixer_code_sha256=public.sha(pe.get_data(0x6ca9,0x2b)),native_rule='Getter FLOAT32 times0.01f at8892. 6ca9-6ccf computes FLOAT32(noise*nv + (1-nv))*Size factor, including NV0 and Type2. No numerical mixer or RNG change in candidate.',dependencies_sha256={str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),Path(enabled.__file__),BEFORE,enabled.BEFORE,enabled.ranges.BEFORE,public.SOURCE.with_suffix('.h'),public.initial.HARNESS,public.ROOT/'core/dblur_noise.h']},claims_not_made=before['claims_not_made']+['Legal Noise percentage and the finite existing seed/thickness/offset profiles do not prove arbitrary Noise controls, Layer, all parameter combinations or native AE.'])
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('NOISE_RANGE_DONE',report['independent_summary'],'SCALAR_MAPS',len(scalars),'WORDS',report['scalar_map_words'],flush=True)


if __name__=='__main__':main()
