"""Save separately labelled fixed geometry regressions from measured witnesses."""
import sys,os,json,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmcolorkey import Adapter
from core import evaluate,load_corpus,save_corpus
from geometry import sample
from run import main_checkout
s=ROOT/'orchestra/state/P02i-colorkey-geometry/witnesses';s.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(s),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
deadline=time.monotonic()+600;p=a.prepare(s,deadline)
out=ROOT/'tests/fuzz_corpus/olmcolorkey/P02i-realistic';out.mkdir(exist_ok=True)
cases=[]
for name in ('pixels','refusal'):
 c,_=load_corpus(ROOT/f'tests/fuzz_corpus/olmcolorkey/T15-prerequisite-realistic/{name}.json',a)
 cases.append(('T15-'+name,c))
seen=set()
for r in map(json.loads,(Path(__file__).parent/'before.jsonl').open()):
 parts=r['label'].split('/')
 if parts[0]!='realistic' or r['result']['oracles']['smart']['status']!='ok':continue
 status=r['result']['routes']['smart']['status']
 if status not in ('refusal','mismatch'):continue
 c=sample(a.generate(int(parts[1]),int(parts[2])),'realistic');key=(status,c['depth'])
 if key in seen:continue
 seen.add(key);cases.append((f'{status}-PF{c["depth"]}-seed{parts[1]}-i{parts[2]}',c))
for name,c in cases:
 r=evaluate(a,c,s,deadline);assert r['routes']['smart']['status']=='exact',(name,r)
 save_corpus(out/(name+'.json'),a,c,c,r,{'accepted':[]},p)
 print(name,'smart exact')
