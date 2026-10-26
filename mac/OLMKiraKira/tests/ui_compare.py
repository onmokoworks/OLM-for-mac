#!/usr/bin/env python3
"""Replay original U03 EVENT preconditions through the production Mac SDK entrypoint.

Original setup metadata is not asserted to be Mac setup metadata. Only the first
before snapshot seeds each session; subsequent state is exclusively Mac-owned.
Raw flatten bytes are retained and inactive capacity differences reported apart.
"""
import argparse, gzip, hashlib, itertools, json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
HERE=Path(__file__).resolve().parent
COMPILED=[HERE/'ui_host.mm',*[HERE.parent/name for name in ('OLMKiraKira.cpp','OLMKiraKira.h','OLMKiraKira_Strings.cpp','OLMKiraKira_Strings.h','RampEditor.h','RampPresets.h')],ROOT/'tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp']
COMPILED += sorted(HERE.parent.glob('Kira*.inc'))
def source_hashes():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in COMPILED}


def first(a,b,path=''):
    if type(a)!=type(b): return (path,a,b)
    if isinstance(a,dict):
        if a.keys()!=b.keys(): return (path+'/keys',sorted(a),sorted(b))
        for k in a:
            d=first(a[k],b[k],path+'/'+k)
            if d:return d
    elif isinstance(a,list):
        for i,(x,y) in enumerate(zip(a,b)):
            d=first(x,y,path+'/'+str(i))
            if d:return d
        if len(a)!=len(b):return(path+'/length',len(a),len(b))
    elif a!=b:return(path,a,b)

def active(row):
    row=json.loads(json.dumps(row))
    for side in ['before','after']:
        for p in row[side]:
            if p['value'] and 'flat_bytes' in p['value']:
                b=p['value']['flat_bytes'];n=int.from_bytes(bytes(b[1:5]),'little')
                assert len(b)==325 and b[0]==1 and n<=16
                p['value']['flat_bytes']=b[:5+20*n]
    return row

def check_comparator():
    with gzip.open(ROOT/'tests/ui_oracle/witnesses/KiraKira-draw-click.jsonl.gz','rt') as f:
        original=json.loads(next(f))['event']
    for label,path in [('active',('after',13,'value','flat_bytes',5)),
                       ('draw',('calls',8,'point_bits',0)),
                       ('inactive',('after',13,'value','flat_bytes',324))]:
        changed=json.loads(json.dumps(original));value=changed
        for key in path[:-1]:value=value[key]
        value[path[-1]]^=1
        assert bool(first(active(original),active(changed)))==(label!='inactive')
        assert first(original,changed), 'raw differences must remain visible'

def build(scratch):
    host=(ROOT/'tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp').read_text().split('template <class Pixel> static void set_pixel',1)[0]
    host=f'#define KIRA_SOURCE "{HERE.parent}/OLMKiraKira.cpp"\n#define KIRA_STRINGS_SOURCE "{HERE.parent}/OLMKiraKira_Strings.cpp"\n'+host
    (scratch/'ui_host_base.cpp').write_text(host)
    env=dict(os.environ,TMPDIR=str(scratch))
    sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True,env=env).strip()
    cmd=['clang++','-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-Wno-deprecated-declarations','-Wno-pragma-pack','-isysroot',sdk,'-I',str(scratch),*[x for p in ('Headers','Headers/SP','Util','Resources') for x in ('-I',str(MAIN/p))],str(HERE/'ui_host.mm'),str(MAIN/'Util/AEGP_SuiteHandler.cpp'),str(MAIN/'Util/MissingSuiteError.cpp'),str(scratch/'ucrtmath/libucrtmath.a'),'-framework','Cocoa','-o',str(scratch/'ui_host')]
    with (scratch/'build.log').open('w') as log:
        subprocess.run(['sh',str(ROOT/'ucrtmath/build.sh'),str(scratch/'ucrtmath')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (scratch/'ui-build.json').write_text(json.dumps(dict(sources=source_hashes(),binary_sha256=hashlib.sha256((scratch/'ui_host').read_bytes()).hexdigest()),indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--no-build',action='store_true');ap.add_argument('--only');ap.add_argument('--scratch',type=Path);args=ap.parse_args()
    scratch=args.scratch or ROOT/'orchestra/state/U02b-kirakira-ui-vs-original';scratch.mkdir(parents=True,exist_ok=True)
    for directory in [ROOT/'tests/ui_oracle',HERE/'ui_witnesses']:
        manifest=json.loads((directory/'manifest.json').read_text())
        witnesses=directory/'witnesses' if (directory/'witnesses').exists() else directory
        for entry in manifest['sessions']:
            for suffix,key in [('.jsonl.gz','compressed_sha256'),('.request.json','request_sha256')]:
                assert hashlib.sha256((witnesses/(entry['name']+suffix)).read_bytes()).hexdigest()==entry[key]
    if not args.no_build:build(scratch)
    binding=json.loads((scratch/'ui-build.json').read_text())
    assert binding['sources']==source_hashes(), 'stale UI host sources; rebuild'
    assert binding['binary_sha256']==hashlib.sha256((scratch/'ui_host').read_bytes()).hexdigest()

    check_comparator()
    results=[]
    fixtures=list((ROOT/'tests/ui_oracle/witnesses').glob('KiraKira-*.jsonl.gz'))+list((HERE/'ui_witnesses').glob('KiraKira-*.jsonl.gz'))
    for fixture in sorted(fixtures):
        name=fixture.name.split('.')[0]
        if args.only and args.only!=name:continue
        with gzip.open(fixture,'rt') as f:initial=json.loads(next(f))
        request=json.loads(fixture.with_name(name+'.request.json').read_text())
        request['initial_parameters']=initial['event']['before']
        request['setup_parameters']=initial['setup']['parameters']
        if request.get('initial_state_u32'):
            assert set(request['initial_state_u32'])=={'25315688'}, 'unsupported original-image injection'
            request['rng']=request['initial_state_u32']['25315688']
        path=scratch/(name+'.input.json');path.write_text(json.dumps(request))
        output=scratch/(name+'.mac.jsonl')
        with output.open('w') as out,(scratch/(name+'.stderr')).open('w') as err:
            p=subprocess.run([str(scratch/'ui_host'),str(path)],stdout=out,stderr=err,env=dict(os.environ,TMPDIR=str(scratch)))
        mismatches=[];tails=[];actual_count=0;expected_count=0
        with gzip.open(fixture,'rt') as expected,output.open() as actual:
            for i,(eline,aline) in enumerate(itertools.zip_longest(expected,actual)):
                expected_count+=eline is not None;actual_count+=aline is not None
                if eline is None or aline is None:continue
                e=json.loads(eline);a=json.loads(aline)
                rb=a.pop('rng_before',None);ra=a.pop('rng_after',None)
                if e['state_before']:
                    assert rb==next(iter(e['state_before'].values())) and ra==next(iter(e['state_after'].values()))
                d=first(active(e['event']),active(a))
                if d:mismatches.append({'dispatch':i,'first':d})
                if any(p['value'] and 'flat_bytes' in p['value'] and p['value']['flat_bytes']!=q['value']['flat_bytes'] for side in ['before','after'] for p,q in zip(e['event'][side],a[side])):tails.append(i)
        result=dict(name=name,returncode=p.returncode,dispatches=actual_count,expected=expected_count,mismatches=mismatches,raw_different_dispatches=tails)
        results.append(result);print(json.dumps(result),flush=True)
    assert results, 'no sessions selected'
    (scratch/'comparison.json').write_text(json.dumps(results,indent=2)+'\n')
    return int(any(r['returncode'] or r['dispatches']!=r['expected'] or r['mismatches'] for r in results))
if __name__=='__main__':raise SystemExit(main())
