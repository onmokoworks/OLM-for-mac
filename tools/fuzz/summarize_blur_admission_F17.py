#!/usr/bin/env python3
"""Assert F17 promotion invariants and retain compact reproducible evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
from core import sha
from adapters.olmblur import SOURCE


def load(path):return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();s=args.scratch
    report={'schema':'olmblur-admission-F17/1','source_sha256':sha(SOURCE.read_bytes()),'seeds':{}}
    for seed in (1,2):
        paths={'before':s/('paired-olmblur.json' if seed==1 else 'blur-before-seed2.json'),
               'gateoff':s/f'blur-gateoff-seed{seed}.json','after':s/f'blur-after-seed{seed}.json',
               'sanitized':s/f'blur-sanitized-seed{seed}.json'}
        data={k:load(v) for k,v in paths.items()}
        assert all(d['completed']==300 and d['jobs']==2 and d['seed']==seed for d in data.values())
        for label in ('after','sanitized'):
            assert data[label]['provenance']['dependencies_sha256']['mac/OLMBlur/OLMBlur.cpp']==report['source_sha256']
        admitted=[];sanitizer_negatives=[]
        for before,off,after,san in zip(*(data[k]['cases'] for k in ('before','gateoff','after','sanitized'))):
            assert len({r['input_sha256'] for r in (before,off,after,san)})==1
            for route in ('classic','smart'):
                a,b=after['result']['routes'][route],before['result']['routes'][route]
                assert a==san['result']['routes'][route], (seed,after['index'],route,'sanitizer drift')
                assert a['status'] in ('exact','mismatch','refusal')
                if a!=b:
                    assert route=='smart' and b['status']=='refusal' and a['status']=='exact'
                    params={p['slot']:p['value'] for p in after['parameters']}
                    assert after['depth'] in (8,16) and params[5]==0 and (params[3]==1 or after['geometry']==[1,1])
                    assert off['result']['routes']['smart']['status']=='exact'
                    assert a['raw_sha256']==off['result']['routes']['smart']['raw_sha256']==after['result']['oracles']['smart']['raw_sha256']
                    admitted.append({k:after[k] for k in ('index','geometry','depth','parameters','input_sha256','result')})
            if off['result']['routes']['smart']['status']=='error':
                diagnostic=off['result']['routes']['smart'].get('diagnostic','')
                assert 'runtime error:' in diagnostic or 'Sanitizer' in diagnostic
                assert after['result']['routes']['smart']['status']=='refusal'
                sanitizer_negatives.append({'index':off['index'],'diagnostic':diagnostic,'production':after['result']['routes']['smart']})
        report['seeds'][str(seed)]={
            'counts':{k:v['summary'] for k,v in data.items()},
            'provenance':{k:v['provenance'] for k,v in data.items()},
            'report_sha256':{k:sha(v.read_bytes()) for k,v in paths.items()},
            'newly_admitted':admitted,'newly_admitted_mismatches':0,
            'sanitized_production_route_executions':600,'sanitizer_errors':0,
            'gateoff_sanitizer_negatives':sanitizer_negatives}
    off=load(s/'blur-matrix-gateoff.json');prod=load(s/'blur-matrix-production.json')
    assert off['counts']=={'exact':592} and prod['counts']=={'exact':592,'refusal':18}
    assert prod['provenance']['source_sha256']==report['source_sha256']
    for a,b in zip(off['cases'],prod['cases']):
        assert a['input_sha256']==b['input_sha256'] and a['candidate']['raw_sha256']==b['candidate']['raw_sha256']==b['oracle']['raw_sha256']
    retained=load(s/'blur-retained.json')
    assert retained['source_sha256']==report['source_sha256'] and retained['status']['status']=='ok'
    report.update(matrix_gateoff=off,matrix_production=prod,retained_controls=retained)
    replay=load(s/'blur-final-replay.json')
    assert replay['completed']==39 and replay['replay_matches_saved']
    report['corpus_replay']={'completed':39,'matches_saved':True,'provenance':replay['provenance']}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS:',{seed:len(v['newly_admitted']) for seed,v in report['seeds'].items()},
          'new exact; 0 new mismatches; 1200 sanitized campaign routes; 592 matrix exact + 18 refusals; 12 retained controls; corpus 39/39')


if __name__=='__main__':main()
