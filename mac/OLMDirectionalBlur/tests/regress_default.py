#!/usr/bin/env python3
"""Serial default-generation comparison: original AEX, base source, changed source."""
import argparse, collections, json, re, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter, SOURCE
from core import sha, raw_diff
from run import main_checkout, default_worker
p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=2000)
p.add_argument('--base',default='22f8f8023645f6299abe6a19f2f596eae7157148');args=p.parse_args()
S=ROOT/'orchestra/state/P01b-directionalblur-downsample/default-regression';S.mkdir(parents=True,exist_ok=True)
def original(path):
    text=subprocess.check_output(['git','show',f'{args.base}:{path.relative_to(ROOT)}'],cwd=ROOT,text=True)
    return re.sub(r'#include "([^"]+)"',lambda m:'#include "'+str((path.parent/m[1]).resolve())+'"',text)
budget=S/'base-budget.h';budget.write_text(original(ROOT/'core/dblur_generic_budget.h'))
base=S/'base.cpp';base.write_text(original(SOURCE).replace(str(ROOT/'core/dblur_generic_budget.h'),str(budget)))
class Before(Adapter):
    def geometry_host(self, body):
        return super().geometry_host(body).replace('#include "'+str(SOURCE)+'"','#include "'+str(base)+'"')
options=SimpleNamespace(max_size=256,case_timeout=10,main=main_checkout(),worker=default_worker())
before=Before(options);after=Adapter(options);deadline=time.monotonic()+1800
for a,name in ((before,'before'),(after,'after')):
    folder=S/name;folder.mkdir(exist_ok=True);a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
    a.binary,_=a.build(folder,deadline)
counts=collections.Counter(); regressions=[]
with (S/'results.jsonl').open('w') as out:
  for i in range(args.n):
    case=after.generate(1,i);row={'seed':1,'index':i,'input_sha256':sha(case['pixels']),'routes':{}}
    for route in ('classic','smart'):
      ref,raw=after.oracle(case,S,deadline,route)
      old,oldraw,_=before.candidate(case,S,route,deadline)
      new,newraw,_=after.candidate(case,S,route,deadline)
      def status(r,b):
        return 'uncompared' if ref['status']!='ok' else ('refusal' if r['status']!='ok' else ('exact' if b==raw else 'mismatch'))
      oldstatus,newstatus=status(old,oldraw),status(new,newraw)
      counts[(route,oldstatus,newstatus)]+=1
      row['routes'][route]=dict(before=oldstatus,after=newstatus,oracle=ref,
          before_sha256=sha(oldraw),after_sha256=sha(newraw))
      if oldstatus=='exact' and newstatus!='exact':
        regressions.append([i,route]);row['routes'][route]['diff']=raw_diff(raw,newraw,case['depth'])
    out.write(json.dumps(row)+'\n');out.flush()
    if i%100==99:print(i+1,dict(counts),flush=True)
summary=dict(n=args.n,seed=1,base=args.base,counts={str(k):v for k,v in counts.items()},regressions=regressions,
    before_sha256=sha(before.binary.read_bytes()),after_sha256=sha(after.binary.read_bytes()),
    aex_sha256=sha(after.aex.read_bytes()),worker_sha256=sha(after.worker.read_bytes()))
(S/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary,flush=True)
assert not regressions,regressions
