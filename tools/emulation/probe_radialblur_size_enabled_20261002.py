#!/usr/bin/env python3
"""Original Size enabled block and independent public threshold witnesses.

The prior legal-range epoch is retained unchanged. Tiny positive UI values do
not enable components until the rounded normalized FLOAT32 exceeds DOUBLE .0001.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import struct
import subprocess

from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RDI
import probe_radialblur_size_range_20261002 as ranges
public=ranges.public
BEFORE=public.ROOT/'reports/radialblur_size_range_public_20261002.json'
HARNESS=Path(__file__).with_name('radialblur_size_enabled_sdk_harness_20261002.cpp')


def before_source():
    source=ranges.candidate_source(ranges.before_source())
    assert public.sha(source.encode())==json.loads(BEFORE.read_text())['source_sha256']
    return source


def candidate_source(source):
    marker='template <typename PixelT>\nstatic bool BuildRadialSizeFactorPlaneAEX('
    helper='''// Original 885a MULSS, 8873 CVTPS2PD and 8876 COMISD set this flag.
static bool RadialSizeVariationEnabled(PF_FpLong percentage)
{
    const float normalized = RadialF32Mul((float)percentage, 0.01f);
    return (double)normalized > 0.0001;
}

'''
    assert source.count(marker)==1;source=source.replace(marker,helper+marker)
    start=source.index('static bool BuildRadialSizeFactorPlaneAEX(');end=source.index('static bool MatchesRadialSizeComponentFixture(',start);part=source[start:end]
    marker='\tconst size_t count = (size_t)w * h;';assert part.count(marker)==1
    part=part.replace(marker,marker+'''
    if (std::isfinite(size_variation_percent) && size_variation_percent >= 0.0f &&
        !RadialSizeVariationEnabled(size_variation_percent)) {
        factor_plane->assign(count + 1, 1.0f);
        factor_plane->back() = 0.0f;
        component_areas->clear();
        return true;
    }''')
    source=source[:start]+part+source[end:]
    old='const bool use_generic_size_fade = use_generic_baseline && info.size_variation != 0.0 &&';assert source.count(old)==2
    source=source.replace(old,'const bool use_generic_size_fade = use_generic_baseline && RadialSizeVariationEnabled(info.size_variation) &&')
    old='info.noise_variation != 0.0 && info.size_variation == 0.0,';assert source.count(old)==1
    source=source.replace(old,'info.noise_variation != 0.0 && !RadialSizeVariationEnabled(info.size_variation),')
    old='const float fade_factor = info.size_variation != 0.0';assert source.count(old)==1
    return source.replace(old,'const float fade_factor = RadialSizeVariationEnabled(info.size_variation)')


def values():
    base=struct.unpack('<I',struct.pack('<f',.01))[0]
    neighbors=[struct.unpack('<f',struct.pack('<I',base+i))[0] for i in [-2,-1,0,1,2]]
    midpoint=(neighbors[2]+neighbors[3])/2
    return [0,1e-300,1e-46,1e-44,1e-42,1e-39,1e-38,1e-20,1e-10,.001,.009,*neighbors,
            math.nextafter(midpoint,-math.inf),midpoint,math.nextafter(midpoint,math.inf),.1]


def independent_cases():
    cases=[]
    for family in [1,2]:
        for pattern in ['opaque','diagonal']:
            for depth in [8,16,32]:
                for state,changes in [('dual_fade',{7:37,10:3,13:37}),('dual_fade_noise1_seed2',{7:37,10:3,13:37,24:25,25:1,27:2}),('dual_fade_noise2',{7:37,10:3,13:37,24:25,25:2,29:3})]:
                    for value in values():
                        params=public.initial.settings(family,19,17)
                        for q in params:
                            if q['slot'] in {22:value,**changes}:q['value']={22:value,**changes}[q['slot']]
                        cases.append(dict(family=family,geometry=[19,17],pattern=pattern,depth=depth,state=state,parameters=params,group=state,matrix='size_enabled',row_index=len(cases)))
    return cases


def native_rows():
    loader=AexLoader(str(public.initial.AEX),verbose=False,fast=False)
    work=loader.bump_alloc(128);loader.add_code_hook(loader.image_base+0x8884,lambda ld,_address,_size:ld.uc.emu_stop())
    rows=[]
    assert loader.read_bytes(loader.image_base+0x21600,8)==struct.pack('<d',.0001)
    assert loader.read_bytes(loader.image_base+0x215f8,4)==struct.pack('<f',.01)
    for value in values():
        original=bytearray(b'\xa5'*128);original[0x40:0x44]=struct.pack('<f',value)
        loader.write_bytes(work,bytes(original));loader.uc.reg_write(UC_X86_REG_RDI,work)
        loader.call_function(loader.image_base+0x8851,max_instructions=32)
        actual=loader.read_bytes(work,128)
        assert not loader.import_log and actual[:0x40]==original[:0x40] and actual[0x45:]==original[0x45:]
        rows.append(dict(requested_double_word=f'{struct.unpack("<Q",struct.pack("<d",value))[0]:016x}',getter_float_word=f'{struct.unpack("<I",original[0x40:0x44])[0]:08x}',normalized_float_word=f'{struct.unpack("<I",actual[0x40:0x44])[0]:08x}',enabled=actual[0x44],import_calls=0,work_guards_intact=True))
    return rows


def sdk_replay(directory,source,rows):
    previous=public.initial.HARNESS
    try:
        public.initial.HARNESS=HARNESS
        for sanitize in [False,True]:
            binary=public.build(directory/('leaf_san' if sanitize else 'leaf_o2'),source,sanitize)
            run=subprocess.run([str(binary)],input=''.join(r['requested_double_word']+'\n' for r in rows),capture_output=True,text=True,check=True,env=ranges.ENV)
            assert not run.stderr and run.stdout.splitlines()==[r['getter_float_word']+' '+r['normalized_float_word']+' '+str(r['enabled']) for r in rows]
    finally:public.initial.HARNESS=previous
    return 2*len(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent-worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    before=json.loads(BEFORE.read_text());source=before_source();candidate=candidate_source(source);start_sha=public.sha(public.SOURCE.read_bytes())
    assert public.sha(args.parent_worker.read_bytes())==before['controlled_worker_sha256']
    assert public.sha(public.initial.AEX.read_bytes())==before['aex_sha256']
    leaf=native_rows();leaf_count=sdk_replay(args.output,candidate,leaf)
    old=public.build(args.output/'before',source);binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']}
    independent=[]
    for case in independent_cases():
        native,frame,_,close,_=public.native_render(args.parent_worker,args.output,case)
        assert not frame['render_error'] and frame['output']['guards_intact'] and close['session_clean'] and not close['unsupported_suite_calls']
        old_error,old_raw,_=public.mac_render(old,args.output,case,'classic',ranges.ENV)
        results={}
        for name,binary in binaries.items():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ranges.ENV)
                assert not error and raw==native,(case,error,len(raw),sum(a!=b for a,b in zip(raw,native)))
                result=dict(error=error,raw_sha256=public.sha(raw),raw_exact=True,metadata=metadata,before_error=old_error,before_raw_exact=not old_error and old_raw==native)
                if name=='o2':results[command]=result
                else:assert result==results[command]
        independent.append(dict(case,input_sha256=public.sha(public.fixture(case)),reference_raw_sha256=public.sha(native),results=results))
        if len(independent)%64==0:print('SIZE_ENABLED_INDEPENDENT',len(independent),flush=True)
    (args.output/'partial_independent.json').write_text(json.dumps(independent,indent=2)+'\n')
    retained=ranges.retained_cases(json.loads(ranges.BEFORE.read_text()))+before['independent_rows']
    for case in before['rows']+retained:
        for binary in binaries.values():
            for command in ['classic','smart']:
                error,raw,metadata=public.mac_render(binary,args.output,case,command,ranges.ENV);expected=case['results'][command]
                assert error==expected['error'] and public.sha(raw)==expected['raw_sha256'] and metadata==expected['metadata']
    assert public.sha(public.SOURCE.read_bytes())==start_sha
    rows=copy.deepcopy(before['rows'])
    for row in rows:
        for result in row['results'].values():result['before_raw_exact']=True;result['before_raw_unchanged']=True
    count=len(independent)
    report=dict(schema='radialblur.size-enabled-public/1',source_before_sha256=before['source_sha256'],source_sha256=public.sha(candidate.encode()),header_sha256=before['header_sha256'],aex_sha256=before['aex_sha256'],controlled_worker_sha256=before['controlled_worker_sha256'],window_worker_sha256=before['window_worker_sha256'],probe_start_source_sha256=start_sha,production_source_changed_during_probe=False,summary=before['summary'],rows=rows,independent_rows=independent,independent_summary=dict(case_count=count,both_commands_exact=count,before_different=sum(not r['results']['classic']['before_raw_exact'] and not r['results']['classic']['before_error'] for r in independent),before_rejected=sum(bool(r['results']['classic']['before_error']) for r in independent)),retained_independent_case_count=len(retained),candidate_public_replay_count=4*(len(rows)+len(retained)+count),native_enabled_rows=leaf,sdk_enabled_replays=leaf_count,native_code_range='8851-8884',native_code_sha256=public.sha(AexLoader(str(public.initial.AEX),verbose=False,fast=False).read_bytes(0x180008851,0x33)),abi='Enter original8851 with RDI pointing to guarded work. +40 contains rounded getter FLOAT32. Stop8884 before next getter. Compare +40 normalized FLOAT32 and +44 enabled byte; imports zero.',dependencies_sha256={str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),HARNESS,BEFORE,Path(ranges.__file__),public.SOURCE.with_suffix('.h'),public.initial.HARNESS]},claims_not_made=before['claims_not_made']+['Finite Size threshold cases do not prove all UI/settings/input combinations.'])
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('SIZE_ENABLED_DONE',report['independent_summary'],'REPLAYS',report['candidate_public_replay_count'],flush=True)


if __name__=='__main__':main()
