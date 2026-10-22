#!/usr/bin/env python3
"""Independent C09 PF8 Size/Fade admission witnesses; no expected output constants."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import random
import tempfile
import time

from adapters.olmdirectionalblur import ROOT, SOURCE
from verify_directionalblur_c02 import Build
from probe_directionalblur_c09_admission import Gate
from core import raw_diff, sha


def cases(adapter):
    extended=('active-noise-fade','back-fade','back-fade-zero')
    for family in ('fade-only', 'noise-fade', 'plain-fade', *extended):
        for index in range(128 if family in extended else 64):
            rng = random.Random(f'C09-independent-{family}-{index}')
            w, h = [(1,1),(1,7),(7,1),(7,9),(17,11),(13,19),(19,13),(11,17)][index%8]
            params = adapter.defaults(w,h)
            strengths = [(0,0)] if family == 'fade-only' else [(7,0),(0,22),(11,17),(83,29)]
            front, back = strengths[index % len(strengths)]
            fades = [(53,0),(0,80),(17,92),(100,3)]
            ff, bf = fades[(index//4)%4]
            values = {1:rng.choice([0,15,45,-73,123]), 2:rng.choice([0.25,1,2.25]),
                3:rng.choice([1,7.5,35,100]), 5:front, 6:ff, 7:rng.choice([0,17,73]),
                10:back, 11:bf, 12:rng.choice([0,29,83]), 15:0,
                16:1+(index%2), 18:rng.choice([1,517,1000]),
                19:rng.choice([0,1,360,600]), 20:rng.choice([1,7.5,100])}
            if family=='noise-fade' or (family=='fade-only' and index%2):
                values[15]=rng.choice([1,33,100])
            if family in extended:
                values.update({5:rng.choice([0,2,7,22,83,1999,4000]),
                    10:rng.choice([0,2,11,29,100,3000]),
                    6:rng.randint(1,100), 11:rng.randint(1,100)})
                if family=='active-noise-fade':
                    if values[5]==values[10]==0: values[5]=1
                    values[15]=rng.choice([1,33,100])
                else:
                    values[6]=0
                    if family=='back-fade-zero': values[5]=values[10]=0
            for p in params: p['value']=values.get(p['slot'],p['value'])
            # ARGB8, with transparent and semitransparent group boundaries.
            pixels=bytes(v for i in range(w*h) for v in
                (rng.choice([0,1,63,127,254,255]),rng.randrange(256),rng.randrange(256),rng.randrange(256)))
            yield f'{family}:{index}', dict(geometry=[w,h], depth=8, parameters=params,
                pixels=pixels, input_padding=3, output_padding=5, profile='sdr', seed=909, index=index)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--baseline',required=True)
    p.add_argument('--production',action='store_true')
    p.add_argument('--families',nargs='+',default=['fade-only','noise-fade','plain-fade'])
    p.add_argument('--active-only',action='store_true',help='Require at least one nonzero scatter Strength')
    args=p.parse_args();args.main,args.max_size,args.case_timeout=ROOT.parent.parent,256,30
    scratch=args.scratch.resolve();scratch.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir=str(scratch);deadline=time.monotonic()+1800
    report={'baseline':args.baseline,'production':args.production,'active_only':args.active_only,
            'families':args.families,'cases':[],'builds':[]}
    with tempfile.TemporaryDirectory(prefix='matrix_',dir=scratch) as tmp:
        tmp=Path(tmp);kind=Build if args.production else Gate
        adapters=[Build(args,baseline=True),kind(args),kind(args,sanitizer=True)]
        for i,a in enumerate(adapters):
            d=tmp/str(i);d.mkdir();report['builds'].append(a.prepare(d,deadline))
        def run(item):
            name,case=item
            with tempfile.TemporaryDirectory(prefix='case_',dir=tmp) as d:
                d=Path(d);oracle,reference=adapters[0].oracle(case,d,deadline,'smart')
                assert oracle['status']=='ok',(name,oracle)
                oracle['raw_sha256']=sha(reference)
                row={'name':name,'geometry':case['geometry'],'parameters':case['parameters'],
                    'input_sha256':sha(case['pixels']),'oracle':oracle,'routes':{}}
                for route in ('classic','smart'):
                    results=[];raws=[]
                    for adapter in adapters:
                        result,raw,_=adapter.candidate(case,d,route,deadline)
                        if result['status']=='ok':result['raw_sha256']=sha(raw)
                        results.append(result);raws.append(raw)
                    assert results[1]==results[2],(name,route,results)
                    row['routes'][route]={'before':results[0],'after':results[1],'sanitizer_same':True}
                    if results[1]['status']=='ok':
                        row['routes'][route]['exact_smart_reference']=reference==raws[1]
                        row['routes'][route]['diff']=raw_diff(reference,raws[1],8)
                    if args.production:
                        assert reference==raws[1],(name,route,row['routes'][route])
                return row
        selected=[r for r in cases(adapters[0]) if r[0].split(':')[0] in args.families]
        if args.active_only:
            selected=[r for r in selected if any(p['slot'] in (5,10) and p['value']>0
                                                for p in r[1]['parameters'])]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(run,selected):
                report['cases'].append(row)
                if not row['routes']['smart'].get('exact_smart_reference'):
                    print('RESIDUAL',row['name'],row['routes']['smart'],flush=True)
        report['commands']=[a.commands for a in adapters]
    report['probe_sha256']=sha(Path(__file__).read_bytes())
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [SOURCE,*sorted((ROOT/'core').glob('dblur*'))]}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('COMPLETE',len(report['cases']),flush=True)


if __name__=='__main__':main()
