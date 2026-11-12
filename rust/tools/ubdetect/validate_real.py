#!/usr/bin/env python3
"""Reproducible local validation; only writes under the requested fresh output."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import shutil

import ubdetect as u

ROOT = Path(__file__).resolve().parents[3]


def refresh_case(src, dst, candidate=None):
    src=src.resolve()
    m=u.read_json(src/'case.json')
    m['ubdetect_provenance']={'source':str(src),'source_case_sha256':u.oracle.sha256(src/'case.json'),
        'historical_identities':{k:m[k] for k in ('harness','reference','candidate')}}
    dst.mkdir(parents=True,exist_ok=False)
    for relative,digest in m['assets'].items():
        asset=(src/relative).resolve()
        if not asset.is_relative_to(src) or u.oracle.sha256(asset)!=digest:
            raise ValueError('invalid historical asset')
        (dst/relative).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(asset,dst/relative)
    if candidate:
        m['candidate']={'path':str(candidate)}
    for k in ('harness','reference','candidate'):
        m[k]=u.oracle.identity(m[k]['path'])
    u.oracle.write_json(dst/'case.json',m)
    return dst


def resource(dst, source):
    """Copy only PiPL bytes from our Rust candidate, never an original binary."""
    import pefile
    pe=pefile.PE(str(source))
    try:
        t=next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if str(e.name).upper()=='PIPL')
        lang=t.directory.entries[0].directory.entries[0]
        item=lang.data.struct
        payload=pe.get_data(item.OffsetToData,item.Size)
    finally:
        pe.close()
    k=c.WinDLL('kernel32',use_last_error=True)
    k.BeginUpdateResourceW.argtypes=[w.LPCWSTR,w.BOOL];k.BeginUpdateResourceW.restype=w.HANDLE
    k.UpdateResourceW.argtypes=[w.HANDLE,w.LPCWSTR,c.c_void_p,w.WORD,c.c_void_p,w.DWORD]
    k.EndUpdateResourceW.argtypes=[w.HANDLE,w.BOOL]
    handle=k.BeginUpdateResourceW(str(dst),False)
    if not handle: raise c.WinError(c.get_last_error())
    ok=False
    try:
        buf=c.create_string_buffer(payload)
        if not k.UpdateResourceW(handle,'PiPL',16000,lang.id,buf,len(payload)):
            raise c.WinError(c.get_last_error())
        ok=True
    finally:
        if not k.EndUpdateResourceW(handle,not ok): raise c.WinError(c.get_last_error())


def build_bug(out,forward):
    results={}
    for name,flags in [('forward',[]),('bug',['--cfg','deliberate_bug'])]:
        target=out/(name+'.aex')
        command=['rustc',str(u.HERE/'bug_fixture.rs'),'--crate-type','cdylib','--edition','2021',
                 '-C','opt-level=2','-o',str(target),*flags]
        result=u.oracle.run_process(command,120,{'UBDETECT_FORWARD_AEX':str(forward.resolve())})
        u.oracle.write_json(out/(name+'-build.json'),result)
        if result['returncode']: raise RuntimeError(result['stderr'])
        resource(target,forward)
        results[name]=target
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    staged=ROOT/'rust/local/integration/staged-final/OLMSmoother.aex'
    wrappers=build_bug(out,staged)
    base=ROOT/'rust/local/integration/cross-check-final'
    cases=[
      ('distance',ROOT/'rust/tools/oracle/runs/dg-serial-replay',None,'original_ub'),
      ('directional',ROOT/'rust/plugins/olm-directional-blur/validation/final-seed-20261112/case-0003-smart8',None,'original_ub'),
      ('radial',base/'OLMRadialBlur/render/case-0017-smart32',None,'original_ub'),
      ('exact-blur8',base/'OLMBlur/render/case-0003-smart8',None,'inconclusive'),
      ('exact-directional16',base/'OLMDirectionalBlur/render/case-0000-smart16',None,'inconclusive'),
      ('exact-radial32',base/'OLMRadialBlur/render/case-0000-smart32',None,'inconclusive'),
      ('exact-rust-forward',base/'OLMSmoother/render/case-0003-classic8',wrappers['forward'],'inconclusive'),
      ('rust-bug',base/'OLMSmoother/render/case-0003-classic8',wrappers['bug'],'stable_mismatch'),
      ('host-suite-fill',base/'OLMRadialBlur/render/case-0017-smart32',None,'inconclusive'),
    ]
    results=[]
    for name,source,candidate,expected in cases:
        case=refresh_case(source,out/'cases'/name,candidate)
        profile='auto'
        if name=='host-suite-fill':
            # Offset is the ONLY changed parameter; preserve the noisy lattice
            # so both host-suite allocation hooks execute, without table OOB.
            m=u.read_json(case/'case.json')
            for side in ('reference','candidate'):
                path=case/'requests'/(side+'.json');req=u.read_json(path)
                for a in req['assignments']:
                    if a['slot']==28:a['components']=[0]
                u.oracle.write_json(path,req)
            for a in m['case']['assignments']:
                if a['slot']==28:a['components']=[0]
            m['assets']={k:u.oracle.sha256(case/k) for k in m['assets']}
            m['ubdetect_provenance']['control']='Only Noise Offset slot 28 changed to zero'
            u.oracle.write_json(case/'case.json',m)
            profile=u.HERE/'profiles/radial-host.json'
        r=u.classify(case,out=out/name,repeats=3,profile=profile,progress=lambda s:print(name,s,flush=True))
        passed=r['verdict']==expected and r['complete']
        if name.startswith('exact') or name=='host-suite-fill':
            passed &= r['reason']=='no_mismatch'
        if name in ('distance','directional','radial'):
            passed &= r['poison']['pattern_dependence_proven']
        if name in ('directional','radial'):
            passed &= bool(r['poison']['oob_reads'])
        if name=='host-suite-fill':
            passed &= not r['poison']['unobserved_hooks']
        results.append({'name':name,'expected':expected,'passed':bool(passed),
            **{k:r[k] for k in ('verdict','reason','reference','candidate','cleanup_verified','route')},
            'poison_proven':r['poison']['pattern_dependence_proven'],
            'poison_difference':r['poison']['between_pattern_difference'],
            'oob_read_count':len(r['poison']['oob_reads']),
            'evidence':str(Path(r['output'])/'verdict.json'),
            'verdict_sha256':u.oracle.sha256(Path(r['output'])/'verdict.json')})
        u.oracle.write_json(out/'validation.json',{'results':results,'passed':all(x['passed'] for x in results)})
    return 0 if all(x['passed'] for x in results) else 1


if __name__=='__main__':
    raise SystemExit(main())
