"""Recheck the two default cases whose oracle timeout availability changed."""
import importlib,json,os,shutil,sys,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from core import evaluate,sha
from run import main_checkout,default_worker
S=R/'orchestra/state/P03b-nonfinite-hdr-admission';D=S/'radial-availability';D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=importlib.import_module('adapters.radialblur').Adapter(SimpleNamespace(main=main_checkout(),worker=default_worker(),max_size=256,case_timeout=10))
a.routes=('smart',);a.oracle_routes={'smart':'smart'}
p=a.prepare(D,time.monotonic()+300);rows=[]
for i in (62,280):
 c=a.generate(1,i);r=evaluate(a,c,D,time.monotonic()+30)
 rows.append(dict(index=i,input_sha256=sha(c['pixels']),result=r))
 print(i,r['routes']['smart']['status'],flush=True)
(S/'radial-availability.json').write_text(json.dumps(dict(provenance=p,rows=rows),indent=2))
shutil.rmtree(D)
