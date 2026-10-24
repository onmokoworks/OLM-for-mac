#!/usr/bin/env python3
import argparse,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from core import evaluate
from geometry import sample,require_host
from run import main_checkout
ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=1);ap.add_argument('--n',type=int,default=2);ap.add_argument('--label',required=True);args=ap.parse_args()
s=ROOT/'orchestra/state/P04b-directionalblur-cropped-checkout'/args.label;s.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));a.routes=('smart',)
deadline=time.monotonic()+3600
require_host(a,sample(a.generate(args.seed,0),'realistic'))
p=a.prepare(s,deadline)
e=ROOT/'orchestra/reports/P04b-evidence'
(e/(args.label+'-provenance.json')).write_text(json.dumps(p,indent=2)+'\n')
counts=Counter()
with (e/(args.label+'-results.jsonl')).open('w') as f:
 for i in range(args.n):
  c=sample(a.generate(args.seed,i),'realistic')
  c.update(geometry=[20,15], full_geometry=([20,15] if i==0 else [40,30]),
           downsample=[[1,1],[1,1]], request_rect=[0,0,20,15], extent_hint=[0,0,20,15],
           depth=8, pixels=bytes((j*17+31)%256 for j in range(1200)),
           parameters=a.defaults(20,15), pixel_aspect=[1,1],
           rowbytes_padding=0,input_padding=0,output_padding=0)
  for control in c['parameters']:
   if control['slot']==5: control['value']=5
  attr={};r=evaluate(a,c,s,deadline,attr)
  status=r['routes']['smart']['status'];counts[status]+=1
  f.write(json.dumps(dict(case={k:v for k,v in c.items() if k!='pixels'},result=r,refusals=attr))+'\n');f.flush()
  print(i,status,flush=True)
(e/(args.label+'-summary.json')).write_text(json.dumps(dict(counts),indent=2)+'\n')
print(dict(counts))
