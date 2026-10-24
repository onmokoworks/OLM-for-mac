"""Retain baseline outcomes for reduced signed-alpha regression witnesses."""
import copy,json,os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
S=R/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch/corpus';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
import adapters.olmdirectionalblur as module
from baseline import cores
cores(module,R,S)
from adapters.olmdirectionalblur import Adapter
from core import evaluate,load_corpus,save_corpus
from geometry import require_host
from run import main_checkout
ad=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
require_host(ad,{'geometry_sampler':'realistic-v1'});deadline=time.monotonic()+300;provenance=ad.prepare(S,deadline)
c,d=load_corpus(R/'orchestra/reports/P06a-evidence/reduced.json',ad)
old=R/'tests/fuzz_corpus/olmdirectionalblur/P05a-performance/preexisting-realistic-v1-seed2053-case9.json'
original,od=load_corpus(old,ad)
C=R/'tests/fuzz_corpus/olmdirectionalblur/P06a-investigation';C.mkdir(exist_ok=True)
cases=[('reduced',c,d['reduction']),('original-cropped',original,dict(accepted=[],attempts=0))]
for alpha in (-1.0,0.0,1.0):
 t=copy.deepcopy(c);t['pixels']=struct.pack('<4f',alpha,.25,.5,1.0);cases.append((f'alpha-{alpha}',t,dict(accepted=[],attempts=0)))
for name,case,reduction in cases:
 result=evaluate(ad,case,S,deadline)
 saved=save_corpus(C/(name+'.json'),ad,original,case,result,reduction,provenance)
 print(name,result['routes']['smart']['status'],flush=True)
