#!/usr/bin/env python3
"""C02 before/current/sanitized Smart regression and route-aware corpus replay."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from adapters.olmdirectionalblur import Adapter, ROOT, SOURCE
from adapters.public import replace_once
from core import evaluate, load_corpus, sha


class Build(Adapter):
    def __init__(self,args,baseline=False,sanitizer=False):
        super().__init__(args)
        self.baseline=args.baseline if baseline else None
        self.sanitizer=sanitizer
        self.commands=[]
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')

    def compile(self,argv,deadline):
        argv=list(argv)
        if argv[0]=='clang++':
            host=Path(next(str(x) for x in argv if str(x).endswith('/host.cpp')))
            if self.baseline:
                for original in (SOURCE,ROOT/'core/dblur_frontonly.cpp',ROOT/'core/dblur_rowdriver.cpp'):
                    body=subprocess.check_output(['git','show',f'{self.baseline}:{original.relative_to(ROOT)}'],cwd=ROOT).decode()
                    target=host.with_name(original.name)
                    body=body.replace('#include "../../core/',f'#include "{ROOT}/core/')
                    body=body.replace('#include "OLMDirectionalBlur.h"',f'#include "{SOURCE.with_suffix(".h")}"')
                    target.write_text(body)
                    if original==SOURCE:
                        host.write_text(replace_once(host.read_text(),str(SOURCE),str(target)))
                    else: argv=[target if x==original else x for x in argv]
                argv+=['-I',ROOT/'core']
            if self.sanitizer:
                argv+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g']
        self.commands.append(list(map(str,argv)))
        return super().compile(argv,deadline)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',required=True)
    p.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state/C02-dblur-smart')
    p.add_argument('--worker',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='*',default=[1,2])
    p.add_argument('--n',type=int,default=300)
    p.add_argument('--corpus',action='store_true')
    p.add_argument('--rebaseline',action='store_true')
    args=p.parse_args()
    args.main,args.max_size,args.case_timeout=ROOT.parent.parent,256,10
    scratch=args.scratch.resolve();scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir=str(scratch)
    report={'baseline':args.baseline,'cases':[],'builds':[]}
    deadline=time.monotonic()+3600
    with tempfile.TemporaryDirectory(prefix='verify_',dir=scratch) as tmp:
        tmp=Path(tmp)
        adapters=[Build(args,baseline=True),Build(args),Build(args,sanitizer=True)]
        for i,a in enumerate(adapters):
            d=tmp/str(i);d.mkdir();report['builds'].append(a.prepare(d,deadline))
        cases=[(f'seed{s}:{i}',adapters[0].generate(s,i),None) for s in args.seeds for i in range(args.n)]
        if args.corpus:
            for path in sorted((ROOT/'tests/fuzz_corpus/olmdirectionalblur').glob('*.json')):
                case,saved=load_corpus(path,adapters[0]);cases.append((str(path.relative_to(ROOT)),case,saved))
        def run(item):
            name,case,saved=item
            with tempfile.TemporaryDirectory(prefix='case_',dir=tmp) as d:
                d=Path(d)
                after=evaluate(adapters[1],case,d,deadline)
                baseline,sanitized={},{}
                for route in adapters[0].routes:
                    for a,dest in ((adapters[0],baseline),(adapters[2],sanitized)):
                        result,raw,_=a.candidate(case,d,route,deadline)
                        if result['status']=='ok':
                            result['raw_sha256']=sha(raw)
                            oracle=after['oracles'][route]
                            result['status']=('exact' if sha(raw)==oracle['raw_sha256'] else 'mismatch') if oracle['status']=='ok' else 'uncompared'
                        dest[route]=result
                    current={k:v for k,v in after['routes'][route].items() if k!='diff'}
                    assert current==sanitized[route],(name,route,current,sanitized[route])
                b,a=baseline['smart'],after['routes']['smart']
                if b['status']=='exact': assert a['status']=='exact' and b['raw_sha256']==a['raw_sha256'],name
                if b.get('raw_sha256')!=a.get('raw_sha256'): assert a['status'] in ('exact','uncompared'),name
                if saved:
                    assert saved['result']['routes']['smart']['raw_sha256'] in (
                        baseline['smart']['raw_sha256'],a['raw_sha256']),name
                    # Rebaseline only measured improvement, preserving all input/provenance history.
                    if saved['result']!=after:
                        assert a['status']=='exact',name
                        if args.rebaseline:
                            saved['result']=after
                            saved['c02_revalidated']={'baseline':args.baseline,'smart_before':b,'reason':'general operation restored against paired AEX stages'}
                            (ROOT/name).write_text(json.dumps(saved,indent=2,sort_keys=True)+'\n')
                return {'name':name,'before':baseline,'after':after,'sanitized':sanitized,'sanitizer_same':True}
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(run,cases):
                report['cases'].append(row)
                if len(report['cases'])%50==0:
                    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
                    print('VERIFIED',len(report['cases']),flush=True)
        report['commands']=[a.commands for a in adapters]
    report['probe_sha256']=sha(Path(__file__).read_bytes())
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [SOURCE,*sorted((ROOT/'core').glob('dblur*'))]}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS',len(report['cases']),'O2/sanitized and base-exact preservation',flush=True)


if __name__=='__main__': main()
