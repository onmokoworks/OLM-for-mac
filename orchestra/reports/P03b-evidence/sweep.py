"""Repeat a T15b campaign without modifying its historical evidence."""
import sys,os,json,time,importlib,shutil
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from core import evaluate,sha
from geometry import sample,require_host
from run import main_checkout
S=R/'orchestra/state/P03b-nonfinite-hdr-admission';name=sys.argv[1];D=S/('sweep-'+name);D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=1080 if name == 'olmkirakira' else 1920,size_max_height=1080,size_sampler='odd-even-v1',case_timeout=10))
require_host(a,{'geometry_sampler':'realistic-v1'});a.routes=('smart',);a.oracle_routes={'smart':'smart'}
p=a.prepare(D,time.monotonic()+300);counts=Counter()
with (S/('sweep-'+name+'.jsonl')).open('w') as out:
 for seed in (2026,2027):
  for i in range(150):
   c=sample(a.generate(seed,i),'realistic');attr={};r=evaluate(a,c,D,time.monotonic()+30,attr)
   k=r['routes']['smart']['status'] if r['oracle']['status']=='ok' else 'unavailable';counts[k]+=1
   out.write(json.dumps(dict(seed=seed,index=i,input_sha256=sha(c['pixels']),result=r,refusals=attr))+'\n');out.flush()
   if (i+1)%25==0:print(seed,i+1,dict(counts),flush=True)
(S/('sweep-'+name+'-summary.json')).write_text(json.dumps(dict(provenance=p,counts=counts),indent=2))
shutil.rmtree(D)
assert not counts['mismatch'] and not counts['refusal'], dict(counts)
