"""Independent exceptional-lane probes; keep the reduced witness geometry."""
import copy, importlib, json, os, shutil, struct, sys, time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from core import evaluate,load_corpus,sha
from geometry import require_host
from run import main_checkout
S=R/'orchestra/state/P03b-nonfinite-hdr-admission';D=S/'directional-matrix';D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=importlib.import_module('adapters.olmdirectionalblur').Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=1920,case_timeout=10))
require_host(a,{'geometry_sampler':'realistic-v1'});a.routes=('smart',);a.oracle_routes={'smart':'smart'}
p=a.prepare(D,time.monotonic()+300)
c,_=load_corpus(R/'tests/fuzz_corpus/olmdirectionalblur/T15b-odd-even-realistic/f34b941132e9.json',a)
rows=[]
for lane in range(4):
 for word in [0,0x80000000,0x7f800000,0xff800000,0x7fc12345,0xffc54321,0x7f812345,0x7f7fffff,0xff7fffff]:
  cc=copy.deepcopy(c);values=[0x3f000000]*(len(c['pixels'])//4)
  values[4*(len(values)//8)+lane]=word
  cc['pixels']=struct.pack('<'+'I'*len(values),*values)
  r=evaluate(a,cc,D,time.monotonic()+30)
  rows.append(dict(lane=lane,word=f'{word:08x}',input_sha256=sha(cc['pixels']),result=r))
  print(lane,f'{word:08x}',r['routes']['smart']['status'],flush=True)
(S/'directional-matrix.json').write_text(json.dumps(dict(provenance=p,rows=rows),indent=2))
shutil.rmtree(D)
