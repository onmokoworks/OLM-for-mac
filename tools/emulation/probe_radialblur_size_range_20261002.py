#!/usr/bin/env python3
"""Legal Size range and independent Size/Noise/Fade composition against AEX.

Keep the existing scalar-exp policy. A private host-exp counterfactual isolates
the known controlled-reference tail difference; it is never production code.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

import probe_radialblur_size_topology_20261002 as topology
import probe_radialblur_size_run_boundary_20261001 as runs
public=topology.public
zoom=topology.zoom
BEFORE=public.ROOT/'reports/radialblur_size_topology_public_20261002.json'
BEFORE_REVISION='ea3a16c5c308fdf6a41cfc5df931f332038fae27'
RETAINED=[topology.BEFORE,*topology.RETAINED]
ENV=topology.ENV


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    old='(info.size_variation == 0.0 || info.size_variation == 1.0 ||\n\t\t info.size_variation == 25.0 || info.size_variation == 100.0)'
    assert source.count(old)==1
    source=source.replace(old,'(std::isfinite(info.size_variation) && info.size_variation >= 0.0 && info.size_variation <= 100.0)')
    start=source.index('static bool IsGenericSizeNoiseControlProfile(');end=source.index('static bool IsGenericRadialControlProfile(',start)
    part=source[start:end];old='(info.size_variation == 25.0 || info.size_variation == 100.0)';assert part.count(old)==1
    source=source[:start]+part.replace(old,'(std::isfinite(info.size_variation) && info.size_variation > 0.0 && info.size_variation <= 100.0)')+source[end:]
    constraint='''\t\t(info.size_variation == 0.0 ||
\t\t (info.noise_variation == 0.0 && info.noise_type == 1 &&
\t\t  info.inner_strength == 0 && info.outer_edge_fade == 0 && info.inner_edge_fade == 0 &&
\t\t  info.outer_offset_mode == 1 && info.outer_offset == 0 &&
\t\t  info.inner_offset_mode == 1 && info.inner_offset == 0)) &&
'''
    assert source.count(constraint)==1;source=source.replace(constraint,'')
    start=source.index('static PF_Err RenderZoomTyped(');end=source.index('static PF_Err RenderZoom8(',start);part=source[start:end]
    marker='\tstd::vector<float> fade_factor_plane;';assert part.count(marker)==1
    part=part.replace(marker,'\tconst bool use_generic_size_fade = use_generic_baseline && info.size_variation != 0.0 &&\n\t\t(info.outer_edge_fade != 0 || info.inner_edge_fade != 0);\n'+marker)
    old='if (use_aex_typed_zoom_any_size_edge_noise_components_32x18) {';assert part.count(old)==2
    part=part.replace(old,'if (use_generic_size_fade || use_aex_typed_zoom_any_size_edge_noise_components_32x18) {')
    old='(use_aex_typed_zoom_dual_size_components_32x18 ||\n\t\t\t use_aex_typed_zoom_size_edge_components_32x18 ||';assert part.count(old)==1
    part=part.replace(old,'(use_generic_size_fade || use_aex_typed_zoom_dual_size_components_32x18 ||\n\t\t\t use_aex_typed_zoom_size_edge_components_32x18 ||')
    old='use_aex_typed_zoom_any_size_edge_noise_components_32x18 ? &fade_factor_plane : nullptr';assert part.count(old)==1
    part=part.replace(old,'(use_generic_size_fade || use_aex_typed_zoom_any_size_edge_noise_components_32x18) ? &fade_factor_plane : nullptr')
    old='(use_generic_size_noise ||\n\t\t\t\t\t\t (use_aex_typed_zoom_dual_size_components_32x18';assert part.count(old)==1
    part=part.replace(old,'((use_generic_baseline && info.size_variation != 0.0) || use_generic_size_noise ||\n\t\t\t\t\t\t (use_aex_typed_zoom_dual_size_components_32x18')
    source=source[:start]+part+source[end:]
    start=source.index('static PF_Err RenderRotationTyped(');end=source.index('static PF_Err RenderWorld(',start);part=source[start:end]
    marker='\tstd::vector<float> rotation_fade_source_with_guard;';assert part.count(marker)==1
    part=part.replace(marker,'\tconst bool use_generic_size_fade = use_generic_baseline && info.size_variation != 0.0 &&\n\t\t(info.outer_edge_fade != 0 || info.inner_edge_fade != 0);\n'+marker)
    old='if (use_aex_typed_rotation_any_size_edge_noise_components_32x18) {';assert part.count(old)==2
    part=part.replace(old,'if (use_generic_size_fade || use_aex_typed_rotation_any_size_edge_noise_components_32x18) {')
    old='? (use_aex_typed_rotation_any_size_edge_noise_components_32x18';assert part.count(old)==1
    part=part.replace(old,'? ((use_generic_size_fade || use_aex_typed_rotation_any_size_edge_noise_components_32x18)')
    old='(use_generic_size_noise || use_aex_typed_rotation_dual_size_noise_offset_components_32x18';assert part.count(old)==1
    part=part.replace(old,'((use_generic_baseline && info.size_variation != 0.0) || use_generic_size_noise || use_aex_typed_rotation_dual_size_noise_offset_components_32x18')
    return source[:start]+part+source[end:]


def independent_cases():
    cases=[]
    def add(family,geometry,pattern,depth,size,changes=None,group='range'):
        params=public.initial.settings(family,*geometry);changes={22:size,**(changes or {})}
        for q in params:
            if q['slot'] in changes:q['value']=changes[q['slot']]
        cases.append(dict(family=family,geometry=geometry,pattern=pattern,depth=depth,state=group,parameters=params,group=group,matrix='size_range',row_index=len(cases)))
    for family in [1,2]:
        for size in range(1,101):add(family,[23,13],'islands',32,size)
        for size in [.1,.5,12.3456789,24.999998092651367,25.000001907348633,33.3,50,50.000003814697266,99.99999237060547,100]:
            for pattern in ['diagonal','opaque']:
                for depth in [8,16,32]:add(family,[19,17],pattern,depth,size,group='fraction')
        for state,changes in [('outer_fade',{7:37}),('inner',{10:4,13:19}),('outer_offset',{5:2,6:4}),('noise1',{24:25,25:1}),('noise2',{24:100,25:2})]:
            for pattern in ['ring','diagonal']:
                for depth in [8,16,32]:add(family,[19,17],pattern,depth,37.5,changes,group=state)
    for family in [1,2]:
        for state,changes in [('outer_fade_noise1',{7:37,24:25,25:1,29:3}),('inner_fade_noise2',{10:4,13:37,24:100,25:2}),('dual_fade_noise2',{7:37,10:3,13:37,24:25,25:2}),('noise1_seed2',{24:25,25:1,27:2}),('ellipse_dual_fade',{17:2.25,18:45,7:37,10:3,13:37})]:
            for size in [1,37.5,100]:
                for pattern in ['ring','diagonal']:
                    for depth in [8,16,32]:add(family,[23,13],pattern,depth,size,changes,group=state)
    assert len(cases)==560
    return cases


def retained_cases(before):
    return before['independent_rows']+[r for path in RETAINED for r in json.loads(path.read_text()).get('independent_rows' if path==topology.BEFORE else 'rows',[])]


def private_reference_exp_source(source):
    start=source.index('static std::vector<float> RotationFadeGaussianWeights(');end=source.index('static std::vector<float> RotationGaussianWeights(',start);part=source[start:end]
    marker='    return weights;';assert part.count(marker)==1
    part=part.replace(marker,'''    for (A_long i = vector_end; i < length; ++i) {
        const float exponent = RadialF32Mul((float)(-((int)i * (int)i)), inverse);
        weights[(size_t)i] = std::exp(exponent);
    }
'''+marker)
    return source[:start]+part+source[end:]


def zoom_natural(worker,directory,cases,source,candidate):
    previous=public.initial.HARNESS
    try:
        hp=directory/'zoom_planes.cpp';hp.write_text(zoom.plane_harness());public.initial.HARNESS=hp
        binaries={name:public.build(directory/(name+'_planes'),zoom.passive_source(text)) for name,text in [('before',source),('candidate',candidate),('private_host_exp',private_reference_exp_source(candidate))]}
    finally:public.initial.HARNESS=previous
    selected=[r for r in cases if r['family']==1 and r['depth']==32 and r['group'] in ['outer_fade','inner']]
    rows=[]
    for index,case in enumerate(selected):
        temp=directory/f'zoom_natural_{index}';temp.mkdir();native,gaussian,trace=topology.zoom_trace(worker,temp,case);comparisons={};raw_hashes={}
        for name,binary in binaries.items():
            out=temp/name;out.mkdir();error,raw,_=public.mac_render(binary,temp,case,'classic',dict(ENV,ZOOM_PROBE_DIRECTORY=str(out)));assert not error
            raw_hashes[name]=public.sha(raw);comparisons[name]={}
            for key,data in native.items():
                mac=(out/(key+('.u8' if key=='eligible' else '.f32'))).read_bytes();assert len(mac)==len(data)
                comparisons[name][key]=({'byte_count':len(data),'different_bytes':sum(a!=b for a,b in zip(data,mac)),'native_sha256':public.sha(data),'mac_sha256':public.sha(mac)} if key=='eligible' else zoom.fields.compare_words(data,mac))
        assert raw_hashes['candidate']==case['reference_raw_sha256']
        assert all(v.get('different_words',v.get('different_bytes'))==0 for v in comparisons['private_host_exp'].values())
        exact=all(v.get('different_words',v.get('different_bytes'))==0 for v in comparisons['candidate'].values())
        length=next(q['value'] for q in case['parameters'] if q['slot']==13)
        if exact:table_comparison=None
        else:
            assert case['group']=='inner' and case['pattern']=='diagonal' and length==19
            import probe_radialblur_rotation_fade_20261001 as fade
            table_comparison=zoom.fields.compare_words(gaussian,fade.model(length)[0]);assert table_comparison['different_words']==1 and table_comparison['first_differences'][0]['word']==17
            expected={'polar':0,'eligible':0,'span':0,'preaccum':24,'premax':6,'accum':20,'max':7,'normalized':27}
            assert {k:v.get('different_words',v.get('different_bytes')) for k,v in comparisons['candidate'].items()}==expected
        rows.append(dict(case=case,trace=trace,field_comparisons=comparisons,mac_raw_sha256=raw_hashes,candidate_all_fields_exact=exact,gaussian_tail_reference_difference=table_comparison,private_host_exp_is_diagnostic_only=True))
        print('SIZE_RANGE_ZOOM_NATURAL',case['group'],case['pattern'],'FIELDS_EXACT',exact,flush=True)
    return rows


def factor_maps(worker,directory,source):
    cases=[]
    for seed in runs.fixtures():
        if seed['size']!=25 or seed['pattern'] not in ['empty','opaque','mixed_edges','two_floating_runs'] or seed['geometry']!=[7,5]:continue
        for size in [.1,37.5,99.99999237060547]:
            case=copy.deepcopy(seed);case['size']=size;case['row_index']=len(cases)
            next(q for q in case['parameters'] if q['slot']==22)['value']=size;cases.append(case)
    assert len(cases)==12
    previous=public.initial.HARNESS
    try:
        public.initial.HARNESS=Path(runs.__file__).with_name('radialblur_size_factor_sdk_harness_20261001.cpp')
        binaries={name:public.build(directory/('factor_'+name),source,name=='san') for name in ['o2','san']}
    finally:public.initial.HARNESS=previous
    rows=[]
    for index,case in enumerate(cases):
        temp=directory/f'factor_{index}';temp.mkdir();area,factor,maximum,trace=runs.trace(worker,temp,case)
        model_area,model_factor,model_maximum,areas=runs.component_model(*case['geometry'],case['mask'],case['size'])
        assert area==model_area and factor==model_factor and maximum==model_maximum
        for binary in binaries.values():
            for depth in [8,16,32]:
                ip=temp/f'input_{depth}.raw';ip.write_bytes(runs.source(case,depth))
                result=subprocess.run([str(binary),*map(str,case['geometry']),str(depth),str(case['size']),str(ip)],capture_output=True,check=True,env=ENV)
                assert result.stdout==factor and result.stderr.decode().strip()=='AREAS'+''.join(' '+str(a) for a in areas)
        rows.append(dict(case=case,trace=trace,maximum_area=maximum,component_areas=areas,area_sha256=public.sha(area),factor_sha256=public.sha(factor),word_count=len(factor)//4,typed_sdk_replays=6))
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    before=json.loads(BEFORE.read_text());source=before_source();candidate=candidate_source(source);source_start_sha256=public.sha(public.SOURCE.read_bytes())
    window=json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes())==window['worker_sha256'] and public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256'] and public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']};old_binary=public.build(args.output/'before',source);rows=[]
    for case in before['rows']:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
        row=copy.deepcopy(case)
        for result in row['results'].values():
            result['before_raw_exact']=True
            result['before_raw_unchanged']=True
        rows.append(row)
        if len(rows)%128==0:print('SIZE_RANGE_PUBLIC',len(rows),flush=True)
    retained=retained_cases(before);assert len(retained)==575
    for case in retained:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    independent=[];declarations=None
    for case in independent_cases():
        native,frame,_,close,decl=public.native_render(args.parent_worker,args.output,case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        if declarations is None:declarations=decl
        case=dict(case,input_sha256=public.sha(public.fixture(case)),reference_raw_sha256=public.sha(native));results={}
        old_error,old_raw,_=public.mac_render(old_binary,args.output,case,'classic',ENV)
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);assert not error and raw==native
                result=dict(error=error,raw_sha256=public.sha(raw),raw_exact=True,metadata=metadata,before_error=old_error,before_raw_exact=not old_error and old_raw==native)
                if name=='o2':results[command]=result
                else:assert result==results[command]
        independent.append(dict(case,results=results))
        if len(independent)%64==0:print('SIZE_RANGE_INDEPENDENT',len(independent),flush=True)
    (args.output/'partial_independent.json').write_text(json.dumps(independent,indent=2)+'\n')
    # Compare broad admission before wiring the fade plane, to retain causal evidence.
    connected_before=candidate
    marker='\tconst bool use_generic_size_fade = use_generic_baseline && info.size_variation != 0.0 &&\n\t\t(info.outer_edge_fade != 0 || info.inner_edge_fade != 0);'
    start=connected_before.index('static PF_Err RenderZoomTyped(');end=connected_before.index('static PF_Err RenderZoom8(',start);part=connected_before[start:end];assert part.count(marker)==1
    connected_before=connected_before[:start]+part.replace(marker,'\tconst bool use_generic_size_fade = false;')+connected_before[end:]
    natural=zoom_natural(args.worker,args.output,independent,connected_before,candidate)
    selected=[r for r in independent if r['depth']==32 and r['group']=='dual_fade_noise2' and r['pattern']=='diagonal' and next(q['value'] for q in r['parameters'] if q['slot']==22)==37.5]
    compound=topology.natural(args.worker,args.output,selected,candidate);assert len(compound)==2
    factors=factor_maps(args.worker,args.output,candidate)
    (args.output/'partial_natural.json').write_text(json.dumps({'zoom':natural,'compound':compound,'factor':factors},indent=2)+'\n')
    assert public.sha(public.SOURCE.read_bytes())==source_start_sha256
    report={'schema':'radialblur.size-range-public/1','before_revision':BEFORE_REVISION,'source_before_sha256':before['source_sha256'],'source_sha256':public.sha(candidate.encode()),'header_sha256':before['header_sha256'],'aex_sha256':before['aex_sha256'],'controlled_worker_sha256':before['controlled_worker_sha256'],'window_worker_sha256':window['worker_sha256'],'probe_start_source_sha256':source_start_sha256,'production_source_changed_during_probe':False,'summary':{'case_count':694,'both_commands_exact':694,'different':0,'mac_rejected':0,'became_exact':0,'lost_exact':0,'raw_changed':0},'rows':rows,'independent_rows':independent,'independent_summary':{'case_count':560,'both_commands_exact':560,'before_rejected':sum(r['results']['classic']['before_error']!=0 for r in independent),'before_exact':sum(r['results']['classic']['before_raw_exact'] for r in independent)},'retained_case_count':575,'candidate_public_replay_count':7316,'zoom_natural_witnesses':natural,'compound_natural_witnesses':compound,'factor_map_witnesses':factors,'native_parameter_declarations':declarations,'dependencies_sha256':{str(path.relative_to(public.ROOT)):public.sha(path.read_bytes()) for path in [Path(__file__),Path(topology.__file__),Path(zoom.__file__),Path(runs.__file__),BEFORE,*RETAINED,public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},'claims_not_made':['The known length19/index17 controlled expf tail mismatch remains open; private host expf changes are diagnostic only and never production.','Legal Size admission and finite composite settings do not prove arbitrary input/settings or all-ten completion.','Native Windows ISA/RCPPS/UCRT, allocator end guard, Rotation extra row and native AE/UI/save/ROI/downsample remain open.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('SIZE_RANGE_DONE',report['summary'],report['independent_summary'],flush=True)


if __name__=='__main__':main()
