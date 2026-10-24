"""Serial ColorKey geometry regression; run with before/after argument."""
import sys, os, json, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmcolorkey import Adapter
from core import evaluate, load_corpus
from geometry import sample
from run import main_checkout
phase=sys.argv[1]
s=ROOT/'orchestra/state/P02i-colorkey-geometry'/phase
s.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(s),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
deadline=time.monotonic()+7200
p=a.prepare(s,deadline)
e=Path(__file__).parent
(e/(phase+'-provenance.json')).write_text(json.dumps(p,indent=2)+'\n')
with (e/(phase+'.jsonl')).open('w') as f:
 def run(label,c):
  attr={};r=evaluate(a,c,s,deadline,attr)
  f.write(json.dumps(dict(label=label,result=r,refusals=attr))+'\n');f.flush()
  print(label,{k:v['status'] for k,v in r['routes'].items()},flush=True)
 for path in sorted((ROOT/'tests/fuzz_corpus/olmcolorkey').rglob('*.json')):
  c,_=load_corpus(path,a);run(str(path.relative_to(ROOT)),c)
 for geometry,seed,n in [('realistic',1,100),('realistic',20261024,100),('default',1,300)]:
  for i in range(n):run(f'{geometry}/{seed}/{i}',sample(a.generate(seed,i),geometry))
