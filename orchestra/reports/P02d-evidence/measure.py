#!/usr/bin/env python3
import argparse,json,sys,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import evaluate,save_corpus
from geometry import sample,require_host
from run import main_checkout
ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=1);ap.add_argument('--n',type=int,default=100);ap.add_argument('--label',required=True);ap.add_argument('--save',action='store_true');args=ap.parse_args()
s=ROOT/'orchestra/state/P02d-radialblur-geometry'/args.label;s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));a.routes=('smart',)
deadline=time.monotonic()+3600
require_host(a,sample(a.generate(args.seed,0),'realistic'))
p=a.prepare(s,deadline)
e=ROOT/'orchestra/reports/P02d-evidence'
(e/(args.label+'-provenance.json')).write_text(json.dumps(p,indent=2)+'\n')
counts=Counter()
with (e/(args.label+'-results.jsonl')).open('w') as f:
 for i in range(args.n):
  c=sample(a.generate(args.seed,i),'realistic');attr={};r=evaluate(a,c,s,deadline,attr)
  status=r['routes']['smart']['status'];counts[status]+=1
  f.write(json.dumps(dict(case={k:v for k,v in c.items() if k!='pixels'},result=r,refusals=attr))+'\n');f.flush()
  print(i,status,flush=True)
  if args.save and status=='exact':
   dest=ROOT/'tests/fuzz_corpus/radialblur_realistic_P02d';dest.mkdir(exist_ok=True)
   save_corpus(dest/f'seed{args.seed}_{i:03d}.json',a,c,c,r,{'accepted':[]},p)
(e/(args.label+'-summary.json')).write_text(json.dumps(dict(counts),indent=2)+'\n')
print(dict(counts))
