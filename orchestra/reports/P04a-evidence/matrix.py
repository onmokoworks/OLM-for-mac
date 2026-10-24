"""Explicit builder-state corpus, preserved verbatim by standard replay."""
import sys,os,time,json,struct,shutil
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3]; S=R/'orchestra/state/P04a-distancegradation-default-pf32';sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import evaluate,save_corpus
S.mkdir(exist_ok=True);os.environ['TMPDIR']=str(S)
A=Adapter(SimpleNamespace(max_size=64,case_timeout=30,main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'))
d=S/'matrix';d.mkdir(exist_ok=True);prov=A.prepare(d,time.monotonic()+300)
corpus=R/'tests/fuzz_corpus/olmdistancegradation_P04a';corpus.mkdir(exist_ok=True)
rows=[]
# Zero is the sole out-of-range captured builder default. -1/4/int limits
# are diagnostic popup states, not claimed reachable from the normal menu.
for i in range(72):
 depth=(8,16,32)[i%3]; variant=i//3
 c=A.generate(10424,i);w,h=(7,5) if variant%2 else (17,11)
 c.update(geometry=[w,h],depth=depth,input_padding=0,output_padding=0,parameters=A.real_defaults(w,h),profile='sdr')
 overrides={} if variant<4 else {2:(0,-1,4,-2147483648,2147483647)[variant%5],1:variant%2,5:1+variant%2,6:(variant//2)%2,9:1+variant%4,10:2.25,11:1+variant%5,12:0 if variant%3==0 else 1}
 for p in c['parameters']:
  if p['slot'] in overrides:p['value']=overrides[p['slot']]
 vals=[(1. if variant==0 else 0. if variant==1 else (0.,.5,1.)[(x+y)%3],(x%9)/9,(y%7)/7,.5) for y in range(h) for x in range(w)]
 c['pixels']=b''.join(struct.pack('<4f',*v) if depth==32 else struct.pack('<4B' if depth==8 else '<4H',*[int(t*(255 if depth==8 else 32768)) for t in v]) for v in vals)
 attr={};res=evaluate(A,c,d,time.monotonic()+100,attr)
 rows.append(dict(index=i,depth=depth,overrides=overrides,result=res,attribution=attr))
 save_corpus(corpus/f'P04a_builder_{i:03}.json',A,c,c,res,dict(accepted=[],attempts=0,bounded=True,minimality_claimed=False),prov)
 print(i,{k:v['status'] for k,v in res['routes'].items()},flush=True)
(S/'matrix.json').write_text(json.dumps(dict(provenance=prov,rows=rows),indent=2))
# Retain the fractional-Power + vector Bilateral refusal as a negative control.
assert all(r['result']['routes']['smart']['status']==('refusal' if r['index']==59 else 'exact') for r in rows)
shutil.rmtree(d)
