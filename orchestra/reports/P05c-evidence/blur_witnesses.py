"""Retain AEX witnesses on both sides of the Blur parallel size threshold."""
import os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmblur import Adapter
from core import evaluate,save_corpus
from geometry import require_host
from sweep_T15b import calibration_case
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance/witnesses'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=worker,max_size=1920,case_timeout=10,size_sampler='odd-even-v1'))
a.size_max_height=1080
prov=a.prepare(S,time.monotonic()+300);prov['case_timeout_seconds']=10
out=ROOT/'tests/fuzz_corpus/olmblur/P05c-parallel-boundary';out.mkdir(parents=True,exist_ok=True)
for w,h in ((255,257),(256,256),(257,259)):
 for depth in (8,16,32):
  for bias in (1,2):
   c=calibration_case(a,w,depth,h)
   values=[(255,51,102,153),(255,255,0,64),(255,0,0,0),(255,255,255,255)]
   raw=b''.join(bytes(v) if depth==8 else struct.pack('<4H',*[round(x*32768/255) for x in v]) if depth==16 else struct.pack('<4f',*[x/255 for x in v]) for v in values)
   c['pixels']=(raw*((w*h+3)//4))[:w*h*(depth//8*4)]
   c['parameters']=[dict(slot=1,kind='s',value=30),dict(slot=2,kind='f',value=100.0),dict(slot=3,kind='i',value=3),dict(slot=4,kind='u',value=bias),dict(slot=5,kind='b',value=0)]
   require_host(a,c)
   r=evaluate(a,c,S,time.monotonic()+60,{})
   assert r['routes']['smart']['status']=='exact',r
   path=out/f'{w}x{h}-PF{depth}-bias{bias}.json'
   save_corpus(path,a,c,c,r,dict(accepted=[],label='P05c parallel threshold, opaque repeated SDR pattern'),prov)
   print(path.name,r['routes']['smart']['status'],flush=True)
