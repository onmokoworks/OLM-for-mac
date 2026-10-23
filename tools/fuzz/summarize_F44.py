#!/usr/bin/env python3
"""Bind F44 measurements and check individual Smart exact preservation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F44-integrate-ms-float'
OUT=ROOT/'orchestra/reports/F44-evidence'
OUT.mkdir(exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def compact(r):
    return {'oracles':{route:{k:v for k,v in oracle.items() if k != 'diagnostic'} for route,oracle in r.get('oracles',{'smart':r['oracle']}).items()},'routes':r['routes']}
data={'campaigns':[],'corpora':[],'changes':[],'exact_losses':[],'oracle_changes':[],'reports':{},'residuals':[],'diagnostic_drift':[]}
for p in sorted(S.glob('*.json')):
    if p.name.startswith('before-') or not p.stem.endswith(('-seed1','-seed44','-replay')):continue
    before=S/('before-'+p.name)
    if not before.exists():raise RuntimeError('Missing '+str(before))
    a,b=(json.loads(x.read_text()) for x in (before,p))
    for path,d in [(before,a),(p,b)]:
        assert d['completed']==d['requested'],path
        assert d['status'] in ('complete','replay_complete'),path
        data['reports'][path.name]={'sha256':sha(path),'provenance':d.get('provenance'),'replay_groups':d.get('replay_groups')}
    replay=p.stem.endswith('-replay');key='replays' if replay else 'cases'
    assert len(a[key])==len(b[key])
    counts=[]
    for d in (a,b):counts.append(dict(Counter(x['result']['routes']['smart']['status'] for x in d[key])))
    row={'label':p.stem,'before':counts[0],'after':counts[1],'cases':len(b[key])}
    if replay:row['matches_saved']=sum(x['matches_saved'] for x in b[key])
    data['corpora' if replay else 'campaigns'].append(row)
    for x,y in zip(a[key],b[key]):
        ident=x.get('path',x.get('index'));assert ident==y.get('path',y.get('index'))
        if not replay:assert x['input_sha256']==y['input_sha256']
        old,new=compact(x['result']),compact(y['result'])
        for route,oracle in x['result'].get('oracles',{}).items():
            other=y['result']['oracles'][route]
            if oracle.get('diagnostic')!=other.get('diagnostic'):
                data['diagnostic_drift'].append({'label':p.stem,'case':ident,'route':route,'before_status':oracle['status'],'after_status':other['status'],'before_sha256':hashlib.sha256(oracle.get('diagnostic','').encode()).hexdigest(),'after_sha256':hashlib.sha256(other.get('diagnostic','').encode()).hexdigest()})
        if not replay and new['routes']['smart']['status']=='mismatch':
            data['residuals'].append({'label':p.stem,**{k:v for k,v in y.items() if k not in ('elapsed_seconds','corpus','refusal_guards')}})
        record={'label':p.stem,'case':ident,'before':old,'after':new}
        if old!=new:data['changes'].append(record)
        if old['oracles']!=new['oracles']:data['oracle_changes'].append(record)
        for route in old['routes']:
            if old['routes'][route]['status']=='exact' and new['routes'][route]['status']!='exact':data['exact_losses'].append(dict(record,route=route))
assert len(data['campaigns'])==20
assert len(data['corpora'])==sum(p.is_dir() and any(p.glob('*.json')) for p in (ROOT/'tests/fuzz_corpus').iterdir())
(OUT/'measurements.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
for row in data['campaigns']+data['corpora']:print(row)
print('exact losses',len(data['exact_losses']),'oracle changes',len(data['oracle_changes']))

assert not data["exact_losses"], "An individually exact route was lost; inspect measurements.json"
