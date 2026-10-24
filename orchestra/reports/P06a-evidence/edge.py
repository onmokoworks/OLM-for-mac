import copy,json,os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
S=R/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch/edge';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
import adapters.olmdirectionalblur as module
from baseline import cores
cores(module,R,S,divisor=True,wrap=True)
from adapters.olmdirectionalblur import Adapter
from core import evaluate,load_corpus,save_corpus
from geometry import require_host
from run import main_checkout
ad=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));ad.routes=('smart',)
if '--sanitize' in sys.argv:
 compile_original=ad.compile
 def compile_sanitized(argv,deadline):
  if argv[0]=='clang++':argv=list(argv)+['-fsanitize=address,undefined','-fno-omit-frame-pointer']
  return compile_original(argv,deadline)
 ad.compile=compile_sanitized
require_host(ad,{'geometry_sampler':'realistic-v1'});deadline=time.monotonic()+300;p=ad.prepare(S,deadline)
c,_=load_corpus(R/'orchestra/reports/P06a-evidence/reduced.json',ad)
rows=[]
for w,h in ([(101,1),(201,1)] if '--large' in sys.argv else [(1,1),(3,1),(7,5)]):
 for fade in (1,2,3,10):
  t=copy.deepcopy(c);t.update(geometry=[w,h],full_geometry=[w,h],request_rect=[0,0,w,h],extent_hint=[0,0,w,h],downsample=[[1,1],[1,1]],pixels=struct.pack('<4f',-1,.25,.5,1)*(w*h))
  for param in t['parameters']:
   if param['slot']==11:param['value']=fade
  r=evaluate(ad,t,S,deadline);rows.append(dict(geometry=[w,h],fade=fade,result=r));print(w,h,fade,r['routes']['smart']['status'],flush=True)
  if r['routes']['smart']['status']!='exact':save_corpus(S/f'edge-{w}-{h}-{fade}.json',ad,t,t,r,dict(accepted=[],attempts=0),p)
(R/'orchestra/reports/P06a-evidence'/('edge-large.json' if '--large' in sys.argv else 'edge-sanitized.json' if '--sanitize' in sys.argv else 'edge.json')).write_text(json.dumps(rows,indent=2)+'\n')
