#!/usr/bin/env python3
"""Compare a named git base, current Smart and ASan/UBSan on two seeds + corpus."""
import argparse, copy, json, os, subprocess, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from adapters.olmsmoother2 import Adapter, SOURCE, SHIM
from adapters.public import ROOT
from core import evaluate, load_corpus, sha


def main():
    p=argparse.ArgumentParser(); p.add_argument('--base',required=True); p.add_argument('--label',required=True)
    p.add_argument('--rebaseline',action='store_true')
    p.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state/C01-smoother2-smart')
    p.add_argument('--worker',type=Path)
    p.add_argument('--seeds',type=int,nargs='+',default=[1,2])
    p.add_argument('--jobs',type=int,default=1,choices=[1])
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    scratch=args.scratch.resolve()/args.label; scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
    worker=args.worker
    if worker is None:
        initial=json.loads((scratch.parent/'before.json').read_text())
        worker=Path(initial['provenance']['worker_path'])
    opts=argparse.Namespace(main=ROOT.parent.parent,worker=worker,max_size=256,case_timeout=30)
    prod=Adapter(opts); pd=scratch/'production'; pd.mkdir(exist_ok=True)
    deadline=time.monotonic()+1800; provenance=prod.prepare(pd,deadline)
    variants={}; source=subprocess.check_output(['git','show',args.base+':'+str(SOURCE.relative_to(ROOT))],text=True)
    for name,body,flags in [('base',source,[]),('sanitized',SOURCE.read_text(),['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'])]:
        d=scratch/name; d.mkdir(exist_ok=True); (d/'production_under_test.cpp').write_text(body)
        (d/'host.cpp').write_text((pd/'host.cpp').read_text())
        a=copy.copy(prod); a.binary=d/'mac'; a.env=dict(prod.env,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-Wno-deprecated-declarations',*flags,'-I',d,'-I',SHIM,'-I',SOURCE.parent,d/'host.cpp','-o',a.binary],deadline)
        variants[name]=a
    cases=[(f'seed{seed}',prod.generate(seed,i),None) for seed in args.seeds for i in range(300)]
    for path in sorted((ROOT/'tests/fuzz_corpus/olmsmoother2').glob('*.json')):
        case,data=load_corpus(path,prod); cases.append(('corpus',case,path))
    def run(item):
        group,case,path=item; d=scratch/f'{group}-{case["index"]}'; d.mkdir(exist_ok=True)
        original,ref=prod.oracle(case,d,deadline); assert original['status']=='ok',original
        row={'group':group,'index':case['index'],'input_sha256':sha(case['pixels']),'aex_sha256':sha(ref)}; raws={}
        for name,adapter in [('base',variants['base']),('current',prod),('sanitized',variants['sanitized'])]:
            status,raw,guards=adapter.candidate(case,d,'smart',deadline)
            assert status['status']=='ok', (group,case['index'],name,status)
            raws[name]=raw; row[name]={'sha256':sha(raw),'exact':raw==ref}
        assert raws['sanitized']==raws['current'],row
        assert not row['base']['exact'] or raws['base']==raws['current'],row
        # Preserve every base-exact case. For unresolved cases, permit a
        # proven earlier-stage correction only if both raw byte and typed-word
        # mismatch counts decrease; record the remaining mismatch explicitly.
        unit=case['depth']//8
        def errors(raw):
            return [sum(a!=b for a,b in zip(raw,ref)),
                    sum(raw[i:i+unit]!=ref[i:i+unit] for i in range(0,len(ref),unit))]
        row['errors_before']=errors(raws['base']); row['errors_after']=errors(raws['current'])
        if raws['base']!=raws['current']:
            assert all(a<=b for a,b in zip(row['errors_after'],row['errors_before'])),row
            assert row['errors_after']!=row['errors_before'],row
        row['changed_words']=sum(raws['base'][i:i+unit]!=raws['current'][i:i+unit] for i in range(0,len(ref),unit))
        if path and args.rebaseline and sha(raws['current']) != json.loads(path.read_text())['result']['routes']['smart']['raw_sha256']:
            data=json.loads(path.read_text()); result=evaluate(prod,case,d,deadline)
            data['result']=result; data['provenance']=provenance
            path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
        return row
    with ThreadPoolExecutor(max_workers=args.jobs) as pool: rows=list(pool.map(run,cases))
    counts={}
    for group in [*(f'seed{s}' for s in args.seeds),'corpus']:
        subset=[r for r in rows if r['group']==group]
        counts[group]={name:dict(Counter('exact' if r[name]['exact'] else 'mismatch' for r in subset)) for name in ('base','current','sanitized')}
        counts[group]['changed_cases']=sum(bool(r['changed_words']) for r in subset)
    report={'base':args.base,'base_source_sha256':sha(source.encode()),'source_sha256':sha(SOURCE.read_bytes()),
        'provenance':provenance,'counts':counts,'sanitizer_errors':0,'base_exact_changes':0,'changes_away_from_exact':0,'cases':rows}
    out=args.report or ROOT/'orchestra/reports'/f'C01-{args.label}.json'; out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(counts,sort_keys=True)); print(out)
if __name__=='__main__':main()
