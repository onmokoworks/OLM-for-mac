#!/usr/bin/env python3
"""Original Zoom fade tables, natural worker fields and SDK public regressions.

Original AEX, workers and production remain unchanged during this probe. Binary
planes/traces stay private; public output records hashes/counts/scalar witnesses.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_rotation_fields_20261001 as fields
public=fields.public
import probe_radialblur_pf8_writer_20261001 as writer
BEFORE=public.ROOT/'reports/radialblur_zoom_alpha_public_20261002.json'
BEFORE_REVISION='ef3af48441a9701cca3493436fe07f457ca5937a'
EXTRA=public.ROOT/'reports/radialblur_rotation_size_noise_independent_20261001.json'
ENV=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    start=source.index('static PF_Err RenderZoomTyped(');end=source.index('static PF_Err RenderZoom8(',start);part=source[start:end]
    for kind in ['outer','inner']:
        old=f'? ZoomGaussianWeights({kind}_fade_span)';assert part.count(old)==1
        part=part.replace(old,f'? RotationFadeGaussianWeights({kind}_fade_span)')
    return source[:start]+part+source[end:]


def independent_cases():
    capture=json.loads(BEFORE.read_text());base=next(r for r in capture['rows'] if r['family']==1 and r['depth']==32 and r['state']=='inner_edge')
    cases=[]
    specs=[([20,14],'opaque',32,length) for length in range(1,101)]
    specs += [([23,13],pattern,depth,length) for pattern in ['opaque','ring','diagonal'] for depth in [8,16,32] for length in [1,4,5,10,13,19,37,50,51,64,100]]
    for index,(geometry,pattern,depth,length) in enumerate(specs):
        case={key:copy.deepcopy(base[key]) for key in ['family','parameters']}
        case.update(geometry=geometry,pattern=pattern,depth=depth,state=f'inner_fade_{length}',group='independent_zoom_fade',matrix='zoom_fade',row_index=index)
        for param in case['parameters']:
            if param['slot']==2:param['value']=[geometry[0]//2,geometry[1]//2]
            if param['slot']==13:param['value']=length
        cases.append(case)
    assert len(cases)==199
    return cases


def assignments(case):
    return [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind']=='a' else '')+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])) for q in public.native_case(case)['parameters']]


def trace(worker,directory,case):
    w,h=case['geometry'];image=Image.new('RGBA',(w,h));image.putdata([(r,g,b,a) for a,r,g,b in public.initial.pixels(w,h,case['pattern'])]);image.save(directory/'input.png')
    command=[str(worker),'render-trace-png',str(public.initial.AEX),str(directory/'input.png'),str(directory/'native.png'),'--pixel-format','argb32f']
    length=next(p['value'] for p in case['parameters'] if p['slot']==13)
    run=subprocess.run(command+['--watch','function=0xb150,arg=rcx,size=64,occurrence=1','--watch',f'function=0xb680,arg=rcx,size={length*4},occurrence=4']+assignments(case),capture_output=True,check=True)
    (directory/'config_trace.json').write_bytes(run.stdout);result=json.loads(run.stdout);assert result['raw_pixel_sha256']==case['reference_raw_sha256']
    smart=next(t for t in result['execution_traces'] if t['selector']=='SMART_RENDER');watches={q['watch_id']:q for q in smart['memory_witnesses']}
    config=bytes.fromhex(watches['watch-1']['before']['hex']);gaussian=bytes.fromhex(watches['watch-2']['after']['hex']);assert len(config)==64 and len(gaussian)==length*4
    minimum,maximum=struct.unpack_from('<2i',config,24);radial=maximum-minimum+1
    step=struct.unpack_from('<f',config,16)[0];angular=int(fields.f32(360/step));cells=radial*angular
    # Original 589c SUB then 589f INC makes Zoom max-min+1, unlike Rotation.
    planes=[('polar',0xb150,'rdx',None,cells*16,'before'),('eligible',0xa9d0,'stack5',None,cells,'before'),('span',0xa9d0,'r9',None,cells*4,'before'),
            ('preaccum',0xb150,'rcx',0x4210,cells*16,'after'),('premax',0xb150,'rcx',0x4218,cells*4,'after'),
            ('accum',0xa9d0,'rcx',0x4210,cells*16,'after'),('max',0xa9d0,'rcx',0x4218,cells*4,'after'),('normalized',0x9d80,'rcx',None,cells*16,'before')]
    specs=[];windows=[]
    for name,rva,arg,deref,size,when in planes:
        for offset in range(0,size,4096):
            count=min(4096,size-offset);spec=f'function={hex(rva)},arg={arg},size={count},offset={offset},occurrence=1'
            if deref is not None:spec+=f',deref={hex(deref)}'
            specs+=['--watch',spec];windows.append((name,count,when))
    run=subprocess.run(command+specs+assignments(case),capture_output=True,check=True);(directory/'native_trace.json').write_bytes(run.stdout);result=json.loads(run.stdout)
    assert result['raw_pixel_sha256']==case['reference_raw_sha256'] and not result['render_error'] and result['guards_intact']
    assert not result['unsupported_suite_calls'] and not result['dropped_unsupported_suite_calls']
    smart=next(t for t in result['execution_traces'] if t['selector']=='SMART_RENDER')
    assert not smart['truncated'] and not smart['dropped_memory_witnesses'] and not smart['trace_configuration']['unhookable_watches']
    watches={q['watch_id']:q for q in smart['memory_witnesses']};assert len(watches)==len(windows)
    native={}
    for name,*_ in planes:
        native[name]=b''.join(bytes.fromhex(watches[f'watch-{i+1}'][when]['hex']) for i,(nm,count,when) in enumerate(windows) if nm==name)
        assert len(native[name])==next(x[4] for x in planes if x[0]==name)
        (directory/('native_'+name+('.u8' if name=='eligible' else '.f32'))).write_bytes(native[name])
    return native,gaussian,{'native_dimensions':[radial,angular],'minimum_radius':minimum,'maximum_radius_inclusive':maximum,'trace_sha256':public.sha(run.stdout),'config_trace_sha256':public.sha(config),'window_count':len(windows),'guards_intact':True,'truncated':False}


def passive_source(source):
 marker='static FloatImage BuildZoomAEXOuterOnlyPolar('
 start=source.index(marker);end=source.index('#if defined(OLM_RADIALBLUR_TEST_SEAM)',start)
 decl='static std::vector<float> probe_polar,probe_span,probe_preaccum,probe_premax,probe_accum,probe_max,probe_normalized;\nstatic std::vector<A_u_char> probe_eligible;\nstatic int probe_dimensions[2];\n'
 part=source[start:end];mark='\tstd::vector<float> max_alpha(cell_count, 0.0f);'
 assert part.count(mark)==1
 part=part.replace(mark,mark+'\n\tprobe_preaccum.assign(cell_count*4,0.0f);probe_premax.assign(cell_count,0.0f);probe_accum.assign(cell_count*4,0.0f);probe_max.assign(cell_count,0.0f);')
 def capture(prefix):return '''
                for (A_long q=0;q<radius_count;++q) {
                    size_t cell=row_cell+q;
                    for(int c=0;c<3;++c) probe_PREFIX[cell*4+c]=normalized.rgba[cell*4+c];
                    probe_PREFIX[cell*4+3]=accum_alpha[cell];probe_MAX[cell]=max_alpha[cell];
                }
'''.replace('PREFIX',prefix+'accum').replace('MAX',prefix+'max')
 marker='\t\t\t\tfor (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {';assert part.count(marker)==1;part=part.replace(marker,capture('pre')+marker)
 pos=part.index('const float denominator = accum_alpha[cell];');pos=part.rfind('\t\t\t\tfor (A_long ri = 0;',0,pos);part=part[:pos]+capture('')+part[pos:]
 source=source[:start]+decl+part+source[end:]
 start=source.index('static PF_Err RenderZoomTyped(');end=source.index('static PF_Err RenderZoom8(',start);part=source[start:end]
 marker='\tbool use_fft_convolution = false;';assert part.count(marker)==1
 part=part.replace(marker,'\tprobe_polar=polar.rgba;probe_span=span_plane;probe_eligible=polar_valid;probe_dimensions[0]=radius_count;probe_dimensions[1]=angular_count;\n'+marker)
 marker='\n\tfor (A_long y = 0; y < h; ++y) {';pos=part.index(marker,part.index('bool use_fft_convolution'))
 part=part[:pos]+'\n\tprobe_normalized=blurred.rgba;\n'+part[pos:]
 return source[:start]+part+source[end:]


def plane_harness():
    harness=public.initial.HARNESS.read_text();marker='if(a!=before)return 67;';assert harness.count(marker)==1
    harness=harness.replace(marker,'''const char* dir=getenv("ZOOM_PROBE_DIRECTORY");
        if(dir){auto dump=[&](const char* name,const void* data,size_t size){std::ofstream f(std::string(dir)+"/"+name,std::ios::binary);f.write((const char*)data,size);};
        dump("polar.f32",probe_polar.data(),probe_polar.size()*4);dump("span.f32",probe_span.data(),probe_span.size()*4);dump("eligible.u8",probe_eligible.data(),probe_eligible.size());
        dump("preaccum.f32",probe_preaccum.data(),probe_preaccum.size()*4);dump("premax.f32",probe_premax.data(),probe_premax.size()*4);dump("accum.f32",probe_accum.data(),probe_accum.size()*4);dump("max.f32",probe_max.data(),probe_max.size()*4);dump("normalized.f32",probe_normalized.data(),probe_normalized.size()*4);dump("dimensions.i32",probe_dimensions,8);}
        '''+marker)
    return harness


def natural(worker,directory,cases,source,candidate):
    previous=public.initial.HARNESS;hp=directory/'planes.cpp';hp.write_text(plane_harness())
    try:
        public.initial.HARNESS=hp
        binaries={'before':public.build(directory/'before_planes',passive_source(source)),
                  'candidate':public.build(directory/'candidate_planes',passive_source(candidate))}
    finally:public.initial.HARNESS=previous
    rows=[]
    for index,case in enumerate(cases):
        temp=directory/f'natural_{index}';temp.mkdir();native,gaussian,witness=trace(worker,temp,case)
        comparisons={};raws={};tables={}
        # Zoom fade length37 is the same original B680 rule as Rotation fade.
        import probe_radialblur_rotation_fade_20261001 as fade
        model,_=fade.model(37);tables['candidate']=fields.compare_words(gaussian,model)
        assert tables['candidate']['different_words']==0
        for name,binary in binaries.items():
            out=temp/name;out.mkdir();error,raw,_=public.mac_render(binary,temp,case,'classic',dict(ENV,ZOOM_PROBE_DIRECTORY=str(out)));assert not error
            raws[name]=public.sha(raw);dimensions=list(struct.unpack('<2i',(out/'dimensions.i32').read_bytes()));assert dimensions==witness['native_dimensions']
            comparisons[name]={}
            for key,data in native.items():
                mac=(out/(key+('.u8' if key=='eligible' else '.f32'))).read_bytes();assert len(mac)==len(data)
                comparisons[name][key]=({'byte_count':len(data),'different_bytes':sum(a!=b for a,b in zip(data,mac)),'native_sha256':public.sha(data),'mac_sha256':public.sha(mac)} if key=='eligible' else fields.compare_words(data,mac))
            assert all(c.get('different_words',c.get('different_bytes'))==0 for c in comparisons[name].values()) if name=='candidate' else True
        rows.append({'case':case,'trace':witness,'field_comparisons':comparisons,'gaussian_comparison':tables['candidate'],'mac_raw_sha256':raws,'candidate_raw_exact':raws['candidate']==case['reference_raw_sha256']})
        print('ZOOM_FADE_NATURAL',case['geometry'],case['pattern'],rows[-1]['candidate_raw_exact'],flush=True)
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    args.output.mkdir(exist_ok=False,parents=True);before=json.loads(BEFORE.read_text());extra=json.loads(EXTRA.read_text());source=before_source();candidate=candidate_source(source);start=public.sha(public.SOURCE.read_bytes())
    window=json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes())==window['worker_sha256'] and public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']};old_binary=public.build(args.output/'before',source)
    rows=[]
    for index,case in enumerate(before['rows']):
        results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);old=case['results'][command];assert error==old['error'] and metadata==old['metadata']
                result={'error':error,'raw_sha256':public.sha(raw) if not error else None,'raw_exact':not error and public.sha(raw)==case['reference_raw_sha256'],'metadata':metadata,'before_raw_exact':old['raw_exact'],'before_raw_unchanged':(public.sha(raw) if not error else None)==old['raw_sha256']}
                if name=='o2':results[command]=result
                else:assert result==results[command]
        row={key:copy.deepcopy(case[key]) for key in ['family','geometry','depth','pattern','state','parameters','group','matrix','row_index','input_sha256','reference_raw_sha256','parent_raw_sha256']};row['results']=results;rows.append(row)
        if (index+1)%128==0:print('ZOOM_FADE_PUBLIC',index+1,flush=True)
    for case in extra['rows']:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command];assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    independent=[]
    for case in independent_cases():
        native,frame,_,close,_=public.native_render(args.parent_worker,args.output,case);assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        case=dict(case,input_sha256=public.sha(public.fixture(case)),reference_raw_sha256=public.sha(native));results={}
        old_error,old_raw,_=public.mac_render(old_binary,args.output,case,'classic',ENV);assert not old_error
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);assert not error
                result={'error':error,'raw_sha256':public.sha(raw),'raw_exact':raw==native,'metadata':metadata,'before_raw_exact':old_raw==native,'before_raw_unchanged':raw==old_raw}
                if name=='o2':results[command]=result
                else:assert result==results[command]
        independent.append(dict(case,results=results))
        if len(independent)%32==0:print('ZOOM_FADE_INDEPENDENT',len(independent),sum(r['results']['classic']['raw_exact'] for r in independent),flush=True)
    affected=[r for r in before['rows'] if r['family']==1 and r['depth']==32 and r['state']=='inner_edge']
    for pattern in ['ring','diagonal']:affected.append(next(r for r in independent if r['pattern']==pattern and r['depth']==32 and r['geometry']==[23,13] and r['state']=='inner_fade_37'))
    witnesses=natural(args.worker,args.output,affected,source,candidate)
    assert public.sha(public.SOURCE.read_bytes())==start
    summary=writer.summarize(rows);assert summary['lost_exact']==0
    report={'schema':'radialblur.zoom-fade-public/1','before_revision':BEFORE_REVISION,'source_before_sha256':before['source_sha256'],'source_sha256':public.sha(candidate.encode()),'header_sha256':before['header_sha256'],'aex_sha256':before['aex_sha256'],'controlled_worker_sha256':before['controlled_worker_sha256'],'window_worker_sha256':window['worker_sha256'],'probe_start_source_sha256':start,'production_source_changed_during_probe':False,'summary':summary,'rows':rows,'independent_rows':independent,'independent_summary':writer.summarize(independent),'natural_witnesses':witnesses,'public_replay_count':2776,'retained_independent_replay_count':384,'new_independent_replay_count':796,'new_independent_native_count':199,'natural_field_words':sum(c['word_count'] for w in witnesses for c in w['field_comparisons']['candidate'].values() if 'word_count' in c),'natural_eligibility_bytes':sum(w['field_comparisons']['candidate']['eligible']['byte_count'] for w in witnesses),'dependencies_sha256':{str(path.relative_to(public.ROOT)):public.sha(path.read_bytes()) for path in [Path(__file__),BEFORE,EXTRA,public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},'claims_not_made':['Finite cases do not prove arbitrary inputs/settings/all-ten completion. Size25, native Windows ISA/RCPPS/general UCRT/AE/UI/save/ROI/downsample remain open.','Three scalar fade-table words remain open; native Windows expf policy was not replaced with host Rust expf.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('ZOOM_FADE_DONE',summary,report['independent_summary'],flush=True)


if __name__=='__main__':main()
