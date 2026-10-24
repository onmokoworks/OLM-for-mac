"""Single exceptional-lane differentials on each reduced refusal's controls."""
import copy,importlib,json,math,os,shutil,struct,sys,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
from core import evaluate,load_corpus,sha
from geometry import require_host
from run import main_checkout
name=sys.argv[1];S=R/'orchestra/state/P03b-nonfinite-hdr-admission';D=S/('matrix-'+name);D.mkdir(exist_ok=True)
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1')
a=importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=1080 if name=='olmkirakira' else 1920,case_timeout=10))
require_host(a,{'geometry_sampler':'realistic-v1'});a.routes=('smart',);a.oracle_routes={'smart':'smart'}
p=a.prepare(D,time.monotonic()+300);rows=[]
summary=json.loads((R/'orchestra/reports/T15b-evidence'/f'{name}-summary.json').read_text())
for w in summary['witnesses']:
 if 'refus' not in w['failure_class']:continue
 c,_=load_corpus(R/w['path'],a)
 for lane in range(4):
  for word in [0,0x80000000,0x7f800000,0xff800000,0x7fc12345,0xffc54321,0x7f812345,0x40e00000,0xc0400000,0x7f7fffff,0xff7fffff]:
   cc=copy.deepcopy(c);values=[0x3f000000]*(len(c['pixels'])//4)
   values[4*(len(values)//8)+lane]=word
   cc['pixels']=struct.pack('<'+'I'*len(values),*values)
   r=evaluate(a,cc,D,time.monotonic()+30)
   rows.append(dict(witness=w['path'],lane=lane,word=f'{word:08x}',input_sha256=sha(cc['pixels']),result=r))
   print(Path(w['path']).stem,lane,f'{word:08x}',r['routes']['smart']['status'],flush=True)
(S/('matrix-'+name+'.json')).write_text(json.dumps(dict(provenance=p,rows=rows),indent=2))
shutil.rmtree(D)
assert not any(r['result']['routes']['smart']['status']=='mismatch' for r in rows)
