#!/usr/bin/env python3
"""Recapture all changed successful default/F29 oracle outputs; require NaN-only words."""
import json, os, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
import verify_replays_F29 as v
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/F30-oracle-worker-ucrtmath'
D=S/'nan-verify';D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(D),TMP=str(D),TEMP=str(D))
result=[]
for path in sorted(S.glob('default-*.json')):
 if not path.name.endswith(('-replay.json','-seed1.json')):continue
 a=json.loads(path.read_text());b=json.loads(path.with_name(path.name.replace('default-','f29-',1)).read_text())
 label=path.name.removeprefix('default-');plugin=a['plugin'];kind='replays' if '-replay.' in label else 'cases'
 for x,y in zip(a[kind],b[kind]):
  ax=x['result'];by=y['result']
  old=ax.get('oracles',{'smart':ax['oracle']});new=by.get('oracles',{'smart':by['oracle']})
  successful=[r for r in old if old[r]['status']==new[r]['status']=='ok' and old[r]['raw_sha256']!=new[r]['raw_sha256']]
  if not successful:continue
  if kind=='cases':
   case=v.adapter(plugin,v.WORKERS[0]).generate(1,x['index']);assert v.sha(case['pixels'])==x['input_sha256'];key=x['index']
  else:
   key=x['path'];p=ROOT/key;meta=json.loads(p.read_text());case,_=v.load_corpus(p,v.adapter(plugin,v.WORKERS[0],meta['max_size']))
  # Isolate successful routes from unrelated timing/status findings.
  lhs={'oracle':old['smart'],'oracles':{r:old[r] for r in successful}}
  rhs={'oracle':new['smart'],'oracles':{r:new[r] for r in successful}}
  with tempfile.TemporaryDirectory(dir=D) as td:
   detail=v.capture(case,plugin,lhs,rhs,Path(td))
  result.append({'label':label,'case':key,'detail':detail})
  print(label,key,'NaN-only',flush=True)
Path(__file__).with_name('F30-evidence').joinpath('nan-recaptures.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('verified',len(result),'changed cases',flush=True)
