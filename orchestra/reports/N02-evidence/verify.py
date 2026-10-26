"""Serial N02 corpus and fresh-seed verification; all scratch is ticket-local."""
import collections,json,os,pathlib,shutil,sys,time
from types import SimpleNamespace
R=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmcolorkey import Adapter
from core import evaluate,load_corpus,save_corpus,sha
from geometry import sample,require_host
from run import main_checkout
S=R/'orchestra/state/N02-olmcolorkey-nightly-20261025';E=pathlib.Path(__file__).parent
S.mkdir(exist_ok=True,parents=True);os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
mode=sys.argv[1];D=S/mode;D.mkdir(exist_ok=True);cache={}
def adapter(worker):
 worker=str(worker)
 if worker not in cache:
  a=Adapter(SimpleNamespace(main=main_checkout(),worker=pathlib.Path(worker),max_size=256,case_timeout=10))
  b=D/sha(worker.encode())[:12];b.mkdir(exist_ok=True);p=a.prepare(b,time.monotonic()+300);cache[worker]=(a,p)
 return cache[worker]
out=(E/(mode+'.jsonl')).open('w')
def check(a,c,label):
 require_host(a,c);t=D/'case';t.mkdir(exist_ok=True)
 try:r=evaluate(a,c,t,time.monotonic()+60)
 finally:shutil.rmtree(t)
 out.write(json.dumps(dict(label=label,result=r))+'\n');out.flush();return r
counts={};changes=[]
if mode in ('witnesses','corpus'):
 paths=sorted((R/'orchestra/reports/nightly-20261025/witnesses').glob('*.json')) if mode=='witnesses' else sorted((R/'tests/fuzz_corpus/olmcolorkey').rglob('*.json'))
 for path in paths:
  saved=json.loads(path.read_text())
  if saved['plugin']!='olmcolorkey':continue
  worker=saved['provenance']['worker_path'];assert sha(pathlib.Path(worker).read_bytes())==saved['provenance']['worker_sha256']
  a,p=adapter(worker);a.max_size=saved['max_size'];c,_=load_corpus(path,a)
  a.routes=('classic','smart');a.oracle_routes={r:r for r in a.routes};r=check(a,c,str(path.relative_to(R)))
  if mode=='witnesses':
   target=R/'tests/fuzz_corpus/olmcolorkey/N02-nightly-20261025'/path.name;target.parent.mkdir(exist_ok=True)
   save_corpus(target,a,c,c,r,saved['reduction'],p)
   counts[path.stem]={k:v['status'] for k,v in r['routes'].items()}
   if r['routes']['smart']['status']!='exact':changes.append(path.name)
  else:
   # Historical files sometimes saved Smart only. Re-evaluate precisely their
   # route set, while retaining the full two-route observation above.
   a.routes=tuple(saved['result']['routes']);a.oracle_routes={r:r for r in a.routes}
   same=check(a,c,'historical:'+str(path.relative_to(R)))==saved['result'];counts[path.as_posix()]=same
   if not same:changes.append(path.name)
elif mode=='campaign':
 for geom,worker in [('default','worker-F46-pow'),('realistic','worker-F52c-geom'),('realistic-v2','worker-F53-geom')]:
  a,p=adapter(pathlib.Path.home()/'.cache/olm-emu'/worker/'aex-guest-worker');a.routes=('smart',);a.oracle_routes={'smart':'smart'}
  for seed,n in [(2026102601,200),(2026102602,200),(2026102603,200)]+([(1,300)] if geom=='default' else []):
   counter=collections.Counter()
   for i in range(n):
    c=sample(a.generate(seed,i),geom);r=check(a,c,f'{geom}:{seed}:{i}');counter[r['routes']['smart']['status']]+=1
   counts[f'{geom}:{seed}']=dict(counter);print(geom,seed,dict(counter),flush=True)
   if set(counter)-{'exact','uncompared'}:changes.append(f'{geom}:{seed}')
else:raise ValueError(mode)
(E/(mode+'-summary.json')).write_text(json.dumps(dict(counts=counts,changes=changes,provenance={k:v[1] for k,v in cache.items()}),indent=2)+'\n')
out.close();shutil.rmtree(D);print('changes',changes,flush=True);assert not changes
