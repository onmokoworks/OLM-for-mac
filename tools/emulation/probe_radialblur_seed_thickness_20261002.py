#!/usr/bin/env python3
"""Legal seed/thickness profiles and reciprocal-based original grid dimensions."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import re

import probe_radialblur_noise_range_20261002 as noise
public=noise.public
BEFORE=public.ROOT/'reports/radialblur_noise_range_public_20261002.json'
BEFORE_REVISION='a79c54d2df1e14e5fea585eb6fc77dad421bca42'
CORE=public.ROOT/'core/dblur_noise.h'
ENV=noise.ENV


def before_source():
    source=subprocess.check_output(['git','show',BEFORE_REVISION+':mac/OLMRadialBlur/OLMRadialBlur.cpp'],cwd=public.ROOT).decode()
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def before_core():
    return subprocess.check_output(['git','show',BEFORE_REVISION+':core/dblur_noise.h'],cwd=public.ROOT).decode()


def candidate_source(source):
    start=source.index('\tif (info.noise_type == 1 && info.quality == 5.0) {',source.index('static bool IsGenericProceduralNoiseProfile('));end=source.index('\n\treturn false;',start)
    return source[:start]+'''\treturn info.seed >= 1 && info.seed <= 1000 &&
        std::isfinite(info.thickness) && info.thickness >= 1.0 && info.thickness <= 100.0 &&
        ((info.noise_type == 1 && info.quality == 5.0) ||
         (info.noise_type == 2 && (info.quality == 5.0 ||
          (info.quality == 3.0 && info.seed == 1 && info.thickness == 10.0))));'''+source[end+len('\n\treturn false;'):]


def candidate_core(core):
    start=core.index('inline bool generate_radial_noise_plane(');part=core[start:]
    old='''    *plane_width = static_cast<int>(static_cast<float>(source_width) / cell_size + 3.0f);
    *plane_height = static_cast<int>(static_cast<float>(source_height) / cell_size + 3.0f);''';assert part.count(old)==1
    part=part.replace('                                        int* plane_height) {\n',
        '                                        int* plane_height) {\n#if defined(__clang__)\n#pragma clang fp contract(off)\n#endif\n')
    return core[:start]+part.replace(old,'''    // Original RadialBlur computes one FLOAT32 reciprocal before MULSS/ADDSS.
    const float inverse_cell_size = 1.0f / cell_size;
    *plane_width = static_cast<int>(static_cast<float>(source_width) * inverse_cell_size + 3.0f);
    *plane_height = static_cast<int>(static_cast<float>(source_height) * inverse_cell_size + 3.0f);''')


def default_contract_build(directory, source):
    """Same SDK harness with the ordinary O2 compiler contract setting."""
    directory.mkdir()
    body=re.sub(r'^#include "([^"]+)"',lambda m:'#include "'+str((public.SOURCE.parent/m.group(1)).resolve())+'"',source,flags=re.MULTILINE)
    (directory/'production_under_test.cpp').write_text(body)
    (directory/'harness.cpp').write_text(public.initial.HARNESS.read_text())
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
    binary=directory/'mac'
    command=['clang++','-std=c++17','-arch','arm64','-O2',
        '-ffunction-sections','-fdata-sections','-Wno-pragma-pack','-isysroot',sdk,
        *[arg for path in ('Headers','Headers/SP','Util','Resources') for arg in ('-I',str(public.ROOT/path))],
        str(directory/'harness.cpp'),str(public.SOURCE.parent/'OLMRadialBlur_Strings.cpp'),
        str(public.ROOT/'Util/AEGP_SuiteHandler.cpp'),str(public.ROOT/'Util/MissingSuiteError.cpp'),
        '-Wl,-dead_strip','-framework','Cocoa','-o',str(binary)]
    subprocess.run(command,check=True,capture_output=True)
    return binary


def independent_cases():
    cases=[]
    def add(family,nt,seed,thickness,depth=32,geometry=[17,15],group='seed',extra=None):
        params=public.initial.settings(family,*geometry);changes={22:37.5,24:33.3,25:nt,27:seed,29:thickness,**(extra or {})}
        for q in params:
            if q['slot'] in changes:q['value']=changes[q['slot']]
        cases.append(dict(family=family,geometry=geometry,pattern='diagonal',depth=depth,state=group,parameters=params,group=group,matrix='seed_thickness',row_index=len(cases)))
    for seed in range(1,1001):add(1 if seed%2 else 2,1 if seed%3 else 2,seed,[1,3.4,10,37.5,100][seed%5])
    for family in [1,2]:
        for nt in [1,2]:
            for thickness in range(1,101):add(family,nt,53,thickness,group='thickness_integer')
            for thickness in [1.0000001192092896,1.7000000476837158,1.888888955116272,1.9166667461395264,3.3333332538604736,3.4,3.833333730697632,7.666667461395264,12.3456789,33.3,99.99999237060547]:
                for depth in [8,16,32]:add(family,nt,997,thickness,depth,[23,13],'fraction_compound',{7:37,10:3,13:37})
    assert len(cases)==1532
    return cases


def retained_cases():
    return noise.retained_cases()+json.loads(BEFORE.read_text())['independent_rows']


def with_core(source,path):
    old='#include "../../core/dblur_noise.h"';assert source.count(old)==1
    return source.replace(old,'#include "'+str(path)+'"')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    before=json.loads(BEFORE.read_text());source=before_source();core=before_core();candidate=candidate_source(source);new_core=candidate_core(core)
    starting_source=public.sha(public.SOURCE.read_bytes());starting_core=public.sha(CORE.read_bytes())
    assert public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256'] and public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    private_core=args.output/'candidate_dblur_noise.h';private_core.write_text(new_core);private_before=args.output/'before_dblur_noise.h';private_before.write_text(core)
    binaries={name:public.build(args.output/name,with_core(candidate,private_core),name=='san') for name in ['o2','san']};old_binary=public.build(args.output/'before',with_core(source,private_before))
    retained=retained_cases();assert len(retained)==2807
    for index,case in enumerate(before['rows']+retained):
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata'],(index,case['family'],case['depth'])
        if (index+1)%500==0:print('SEED_THICKNESS_RETAINED',index+1,flush=True)
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
        if len(independent)%100==0:
            (args.output/'partial_independent.json').write_text(json.dumps(independent,indent=2)+'\n');print('SEED_THICKNESS_INDEPENDENT',len(independent),flush=True)
    assert public.sha(public.SOURCE.read_bytes())==starting_source and public.sha(CORE.read_bytes())==starting_core
    report=dict(schema='radialblur.seed-thickness-public/1',before_revision=BEFORE_REVISION,source_before_sha256=before['source_sha256'],source_sha256=public.sha(candidate.encode()),core_before_sha256=public.sha(core.encode()),core_sha256=public.sha(new_core.encode()),header_sha256=before['header_sha256'],aex_sha256=before['aex_sha256'],controlled_worker_sha256=before['controlled_worker_sha256'],window_worker_sha256=before['window_worker_sha256'],probe_start_source_sha256=starting_source,probe_start_core_sha256=starting_core,production_source_and_core_changed_during_probe=False,summary=before['summary'],rows=copy.deepcopy(before['rows']),independent_rows=independent,independent_summary=dict(case_count=1532,both_commands_exact=1532,before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent),before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent)),retained_independent_case_count=2807,candidate_public_replay_count=20132,directional_noise_functions_unchanged=core.split('inline bool generate_radial_noise_plane(')[0]==new_core.split('inline bool generate_radial_noise_plane(')[0],dependencies_sha256={str(path.relative_to(public.ROOT)):public.sha(path.read_bytes()) for path in [Path(__file__),Path(noise.__file__),BEFORE,noise.BEFORE,public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},claims_not_made=before['claims_not_made']+['Seed/thickness finite witnesses and original reciprocal rule do not prove all input/settings, negative phases, native Windows ISA/UCRT/AE or all-ten completion.'])
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('SEED_THICKNESS_PUBLIC_DONE',report['independent_summary'],flush=True)


if __name__=='__main__':main()
