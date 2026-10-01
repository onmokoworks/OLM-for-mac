#!/usr/bin/env python3
"""General component factors replace obsolete1/4/9 fixture-only Size admission."""
import argparse
import copy
import inspect
import json
import os
from pathlib import Path
import struct
import subprocess

import probe_radialblur_zoom_fade_20261002 as zoom
import probe_radialblur_rotation_neutral_20261001 as rotation
public=zoom.public
writer=zoom.writer
BEFORE=public.ROOT/'reports/radialblur_zoom_fade_public_20261002.json'
BEFORE_REVISION='5817585181571ac132344ed07a0dffbbed3534b5'
RETAINED=[public.ROOT/'reports/radialblur_rotation_size_noise_independent_20261001.json',
          public.ROOT/'reports/radialblur_zoom_fade_outer_public_20261002.json']
ENV=zoom.ENV


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    pairs=[('use_generic_baseline && info.size_variation != 0.0 && !source_components_area_profile','use_generic_baseline && info.size_variation != 0.0 && !source_general_topology'),
           ('(use_generic_baseline && source_components_area_profile)','(use_generic_baseline && source_general_topology)')]
    for old,new in pairs:
        assert source.count(old)==2
        source=source.replace(old,new)
    start=source.index('static FloatImage BuildZoomAEXOuterOnlyPolar(');end=source.index('#if defined(OLM_RADIALBLUR_TEST_SEAM)',start)
    part=source[start:end];old='if (denominator == 0.0f) {';assert part.count(old)==1
    source=source[:start]+part.replace(old,'if (max_alpha[cell] == 0.0f) {')+source[end:]
    start=source.index('struct RadialZoomPixelTraits<PF_PixelFloat>');end=source.index('template <typename PixelT>',start);part=source[start:end]
    old='\t\tWrite(pixel, state, use_fft);';assert part.count(old)==1
    replacement='\t\t// The common PF32 caller applies MINSS after gain before17490.\n\t\tRadialBlurOuterSampleState bounded = state;\n\t\tfor (int c = 0; c < 3; ++c) bounded.final_rgb[c] = state.final_rgb[c] < 1.0f ? state.final_rgb[c] : 1.0f;\n\t\tWrite(pixel, bounded, use_fft);'
    source=source[:start]+part.replace(old,replacement)+source[end:]
    start=source.index('\t\t\tif constexpr (std::is_same<PixelT, PF_PixelFloat>::value) {\n\t\t\t\tif ((use_aex_typed_zoom_offcenter_brightness')
    end=source.index('\n\t\t\tPixelT *out',start)
    source=source[:start]+source[end:]
    return source


def independent_cases():
    before=json.loads(BEFORE.read_text());rows=[]
    for family in [1,2]:
        base=next(r for r in before['rows'] if r['family']==family and r['state']=='size25' and r['depth']==32)
        for geometry in [[23,13],[19,17]]:
            for pattern in ['islands','ring','diagonal','opaque','empty']:
                for size in [1,25,100]:
                    for depth in [8,16,32]:
                        case={k:copy.deepcopy(base[k]) for k in ['family','parameters']}
                        case.update(geometry=geometry,pattern=pattern,depth=depth,state=f'size{size}',group='independent_size_topology',matrix='size_topology',row_index=len(rows))
                        for p in case['parameters']:
                            if p['slot']==2:p['value']=[geometry[0]//2,geometry[1]//2]
                            if p['slot']==22:p['value']=size
                        rows.append(case)
    assert len(rows)==180
    return rows


# Original Zoom B680 is called even for zero fade lengths. Read one initialized
# workspace word in that case, but make no Gaussian-table claim from it.
_trace_source=inspect.getsource(zoom.trace).replace('def trace(', 'def zoom_trace(')
_trace_source=_trace_source.replace('size={length*4}','size={max(1,length)*4}').replace('len(gaussian)==length*4','len(gaussian)==max(1,length)*4')
exec(compile(_trace_source,'<passive-zero-fade-zoom-trace>','exec'),dict(zoom.__dict__,zoom_trace=None),_trace_namespace:={})
zoom_trace=_trace_namespace['zoom_trace']


def natural(worker,directory,cases,source):
    previous=public.initial.HARNESS;binaries={}
    try:
        for family in [1,2]:
            public.initial.HARNESS=previous
            hp=directory/f'planes_{family}.cpp';hp.write_text(zoom.plane_harness() if family==1 else rotation.fields.plane_harness());public.initial.HARNESS=hp
            binaries[family]=public.build(directory/f'planes_build_{family}',zoom.passive_source(source) if family==1 else source)
    finally:public.initial.HARNESS=previous
    rows=[]
    for index,case in enumerate(cases):
        temp=directory/f'natural_{index}';temp.mkdir()
        if case['family']==1:
            native,_,witness=zoom_trace(worker,temp,case);env=dict(ENV,ZOOM_PROBE_DIRECTORY=str(temp));dimension_name='dimensions.i32'
        else:
            native,witness=rotation.trace(worker,temp,case);env=dict(ENV,ROTATION_PLANES_DIRECTORY=str(temp));dimension_name='dimensions.i32'
        error,raw,_=public.mac_render(binaries[case['family']],temp,case,'classic',env);assert not error and public.sha(raw)==case['reference_raw_sha256']
        dimensions=list(struct.unpack('<2i',(temp/dimension_name).read_bytes()));comparisons={}
        for name,data in native.items():
            mac=(temp/(name+('.u8' if name=='eligible' else '.f32'))).read_bytes()[:len(data)];assert len(mac)==len(data)
            comparisons[name]=({'byte_count':len(data),'different_bytes':sum(a!=b for a,b in zip(data,mac)),'native_sha256':public.sha(data),'mac_sha256':public.sha(mac)} if name=='eligible' else zoom.fields.compare_words(data,mac))
        assert all(q.get('different_words',q.get('different_bytes'))==0 for q in comparisons.values())
        rows.append({'case':case,'trace':witness,'mac_dimensions':dimensions,'field_comparisons':comparisons,'mac_raw_sha256':public.sha(raw),'all_owned_fields_and_raw_exact':True})
        print('SIZE_TOPOLOGY_NATURAL',case['family'],case['geometry'],case['pattern'],flush=True)
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    before=json.loads(BEFORE.read_text());source=before_source();candidate=candidate_source(source);start=public.sha(public.SOURCE.read_bytes());window=json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes())==window['worker_sha256'] and public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256'] and public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']};rows=[]
    for index,case in enumerate(before['rows']):
        results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);old=case['results'][command]
                assert not error and metadata==old['metadata']
                result={'error':error,'raw_sha256':public.sha(raw),'raw_exact':public.sha(raw)==case['reference_raw_sha256'],'metadata':metadata,'before_raw_exact':old['raw_exact'],'before_raw_unchanged':public.sha(raw)==old['raw_sha256']}
                if name=='o2':results[command]=result
                else:assert result==results[command]
        row={key:copy.deepcopy(case[key]) for key in ['family','geometry','depth','pattern','state','parameters','group','matrix','row_index','input_sha256','reference_raw_sha256','parent_raw_sha256']};row['results']=results;rows.append(row)
        if (index+1)%128==0:print('SIZE_TOPOLOGY_PUBLIC',index+1,flush=True)
    (args.output/'partial_rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    retained=before['independent_rows']+[r for path in RETAINED for r in json.loads(path.read_text())['rows']]
    for case in retained:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    independent=[]
    for case in independent_cases():
        native,frame,_,close,_=public.native_render(args.parent_worker,args.output,case);assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        case=dict(case,input_sha256=public.sha(public.fixture(case)),reference_raw_sha256=public.sha(native));results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);assert not error
                result={'error':error,'raw_sha256':public.sha(raw),'raw_exact':raw==native,'metadata':metadata}
                if name=='o2':results[command]=result
                else:assert result==results[command]
        independent.append(dict(case,results=results))
        if len(independent)%30==0:print('SIZE_TOPOLOGY_INDEPENDENT',len(independent),sum(r['results']['classic']['raw_exact'] for r in independent),flush=True)
    (args.output/'partial_independent.json').write_text(json.dumps(independent,indent=2)+'\n')
    natural_cases=[next(r for r in before['rows'] if r['family']==family and r['depth']==32 and r['state']=='size25' and r['geometry']==geometry and r['pattern']==pattern) for family in [1,2] for geometry,pattern in [([20,14],'opaque'),([17,11],'islands'),([20,14],'diagonal')]]
    witnesses=natural(args.worker,args.output,natural_cases,candidate);summary=writer.summarize(rows);assert summary['lost_exact']==0
    assert public.sha(public.SOURCE.read_bytes())==start
    report={'schema':'radialblur.size-topology-public/1','before_revision':BEFORE_REVISION,'source_before_sha256':before['source_sha256'],'source_sha256':public.sha(candidate.encode()),'header_sha256':before['header_sha256'],'aex_sha256':before['aex_sha256'],'controlled_worker_sha256':before['controlled_worker_sha256'],'window_worker_sha256':window['worker_sha256'],'probe_start_source_sha256':start,'production_source_changed_during_probe':False,'summary':summary,'rows':rows,'independent_rows':independent,'independent_summary':{'case_count':180,'both_commands_exact':sum(all(v['raw_exact'] for v in r['results'].values()) for r in independent)},'retained_case_count':len(retained),'candidate_public_replay_count':2776+4*len(retained)+720,'natural_witnesses':witnesses,'natural_owned_field_words':sum(v['word_count'] for w in witnesses for v in w['field_comparisons'].values() if 'word_count' in v),'dependencies_sha256':{str(path.relative_to(public.ROOT)):public.sha(path.read_bytes()) for path in [Path(__file__),Path(zoom.__file__),Path(rotation.__file__),BEFORE,*RETAINED,public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},'claims_not_made':['Finite frames/size1,25,100 do not prove other legal Size values or arbitrary geometry/settings/all-ten completion.','Native Windows ISA/RCPPS/UCRT, three scalar fade words, Rotation extra radius row, allocator mask end guard and native AE/UI/save/ROI/downsample remain open.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('SIZE_TOPOLOGY_DONE',summary,report['independent_summary'],flush=True)


if __name__=='__main__':main()
