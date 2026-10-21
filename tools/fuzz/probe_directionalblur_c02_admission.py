#!/usr/bin/env python3
"""Scratch-only C02 PF8 feature gate experiment; never edits production files."""
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
from verify_directionalblur_c02 import Build
from core import sha, raw_diff

GUARD='''    if (info.noise_variation != 0.0 ||
        (info.size_variation != 0.0 &&
            (info.front_alpha_fade != 0 || info.back_alpha_fade != 0))) return false;'''


class Gate(Build):
    def __init__(self,args,**kwargs):
        super().__init__(args,**kwargs)
        self.source_ref=args.baseline

    def compile(self,argv,deadline):
        argv=list(argv)
        if argv[0]=='clang++':
            host=Path(next(str(x) for x in argv if str(x).endswith('/host.cpp')))
            body=subprocess.check_output(['git','show',f'{self.source_ref}:{SOURCE.relative_to(ROOT)}'],cwd=ROOT).decode()
            body=replace_once(body,GUARD,'    // C02 scratch gate-off experiment.')
            body=body.replace('#include "../../core/',f'#include "{ROOT}/core/')
            body=body.replace('#include "OLMDirectionalBlur.h"',f'#include "{SOURCE.with_suffix(".h")}"')
            target=host.with_name('gate.cpp');target.write_text(body)
            host.write_text(replace_once(host.read_text(),str(SOURCE),str(target)))
        return super().compile(argv,deadline)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--seeds',nargs='+',type=int,default=[1,2])
    p.add_argument('--baseline',default='08216d532f12921d9d3fce1352a772d717336650')
    args=p.parse_args();args.main,args.max_size,args.case_timeout=ROOT.parent.parent,256,30
    scratch=ROOT/'orchestra/state/C02-dblur-smart';scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch))
    tempfile.tempdir=str(scratch);deadline=time.monotonic()+1800
    report={'cases':[],'builds':[],'baseline':args.baseline}
    with tempfile.TemporaryDirectory(prefix='admission_',dir=scratch) as tmp:
        tmp=Path(tmp);adapters=[Build(args,baseline=True),Gate(args),Gate(args,sanitizer=True)]
        for i,a in enumerate(adapters):
            d=tmp/str(i);d.mkdir();report['builds'].append(a.prepare(d,deadline))
        def run(item):
            seed,index=item;case=adapters[0].generate(seed,index)
            with tempfile.TemporaryDirectory(prefix='case_',dir=tmp) as d:
                d=Path(d);results=[];raws=[]
                for adapter in adapters:
                    result,raw,_=adapter.candidate(case,d,'smart',deadline)
                    if result['status']=='ok': result['raw_sha256']=sha(raw)
                    results.append(result);raws.append(raw)
                assert results[1]==results[2],(seed,index,results)
                row={'seed':seed,'index':index,'before':results[0],'gate':results[1],
                    'sanitizer_same':True,'changed':results[0]!=results[1]}
                if row['changed']:
                    oracle,reference=adapters[0].oracle(case,d,deadline,'smart')
                    row.update(oracle=oracle,parameters=case['parameters'],geometry=case['geometry'])
                    if oracle['status']=='ok' and results[1]['status']=='ok':
                        row['exact']=reference==raws[1]
                        row['diff']=raw_diff(reference,raws[1],case['depth'])
                        row['oracle']['raw_sha256']=sha(reference)
                return row
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(run,[(s,i) for s in args.seeds for i in range(300)]):
                report['cases'].append(row)
                if row['changed']: print('CHANGED',row['seed'],row['index'],row['gate']['status'],row.get('exact'),row.get('diff'),flush=True)
        report['commands']=[getattr(a,'commands',[]) for a in adapters]
    report['probe_sha256']=sha(Path(__file__).read_bytes())
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['cases']),flush=True)


if __name__=='__main__':main()
