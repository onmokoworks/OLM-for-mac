import sys,os,time,json,struct
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3]; S=R/'orchestra/state/P04a-distancegradation-default-pf32';sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import evaluate
A=Adapter(SimpleNamespace(max_size=64,case_timeout=60,main=Path('/Users/onmk/Documents/Projects/Personal/OLM as'),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'))
d=S/sys.argv[1];d.mkdir(exist_ok=True);os.environ['TMPDIR']=str(S)
prov=A.prepare(d,time.monotonic()+300); rows=[]
for pattern in ('opaque','mixed'):
 for depth in (8,16,32):
  c=A.generate(1,0);c.update(geometry=[32,24],depth=depth,input_padding=0,output_padding=0,parameters=A.real_defaults(32,24))
  for p in c['parameters']:
   if p['slot']==2:p['value']=0
  vals=[(1 if pattern=='opaque' or (x+y)%3 else 0,(x%9)/9,(y%7)/7,.5) for y in range(24) for x in range(32)]
  c['pixels']=b''.join(struct.pack('<4f',*v) if depth==32 else struct.pack('<4B' if depth==8 else '<4H',*[int(t*(255 if depth==8 else 32768)) for t in v]) for v in vals)
  attr={};res=evaluate(A,c,d,time.monotonic()+180,attr);rows.append(dict(pattern=pattern,depth=depth,result=res,attribution=attr));print(pattern,depth,{k:v['status'] for k,v in res['routes'].items()},flush=True)
(d/'results.json').write_text(json.dumps(dict(provenance=prov,rows=rows),indent=2))
