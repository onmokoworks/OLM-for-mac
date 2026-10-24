"""Serial Smoother2 Smart campaigns using the unchanged F52c geometry host."""
import argparse,json,sys,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmsmoother2 import Adapter
from geometry import sample,require_host
from core import evaluate,sha,save_corpus
from run import main_checkout
p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--seed',type=int,default=1);p.add_argument('--n',type=int,default=100);p.add_argument('--geometry',choices=['default','realistic'],default='realistic');p.add_argument('--save',action='store_true');args=p.parse_args()
s=ROOT/'orchestra/state/P02f-smoother2-geometry'/args.label;s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));a.routes=('smart',);a.oracle_routes={'smart':'smart'}
require_host(a,sample(a.generate(args.seed,0),args.geometry));deadline=time.monotonic()+7200
provenance=a.prepare(s,deadline);(s/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');counts=Counter()
with (s/'results.jsonl').open('w') as f:
 for i in range(args.n):
  c=sample(a.generate(args.seed,i),args.geometry);attr={};r=evaluate(a,c,s,deadline,attr)
  status=r['routes']['smart']['status'] if r['oracle']['status']=='ok' else 'unavailable';counts[status]+=1
  row=dict(case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),result=r,refusals=attr)
  f.write(json.dumps(row)+'\n');f.flush();print(i,status,flush=True)
  if args.save and status=='exact' and c.get('downsample')!=[[1,1],[1,1]]:
   corpus=ROOT/'tests/fuzz_corpus/olmsmoother2_realistic_P02f';corpus.mkdir(exist_ok=True)
   save_corpus(corpus/f'seed{args.seed}_case{i:06}.json',a,c,c,r,{'accepted':[],'attempts':0},{'worker_path':str(a.worker),'worker_sha256':sha(a.worker.read_bytes()),'case_timeout_seconds':10})
(s/'summary.json').write_text(json.dumps(dict(seed=args.seed,n=args.n,geometry=args.geometry,counts=counts),indent=2)+'\n')
print(dict(counts),flush=True)
