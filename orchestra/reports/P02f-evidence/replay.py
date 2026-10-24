"""Replay all Smoother2 corpora with F52c; preserve each saved route set."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmsmoother2 import Adapter
from core import evaluate,load_corpus
from geometry import require_host
from run import main_checkout
s=ROOT/'orchestra/state/P02f-smoother2-geometry/replay';s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));deadline=time.monotonic()+3600
(s/'provenance.json').write_text(json.dumps(a.prepare(s,deadline),indent=2)+'\n');rows=[]
for folder in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
 for path in sorted(folder.glob('*.json')):
  data=json.loads(path.read_text())
  if data.get('plugin')!='olmsmoother2':continue
  a.max_size=data['max_size'];a.routes=tuple(data['result']['routes']);a.oracle_routes={r:r for r in a.routes}
  c,saved=load_corpus(path,a);require_host(a,c);r=evaluate(a,c,s,deadline)
  rows.append(dict(path=str(path.relative_to(ROOT)),result=r,matches_saved=r==saved['result']))
  print(path.name,rows[-1]['matches_saved'],flush=True)
(s/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('matched',sum(r['matches_saved'] for r in rows),'/',len(rows))
