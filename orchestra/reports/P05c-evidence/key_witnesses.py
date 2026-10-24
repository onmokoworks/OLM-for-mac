"""Actual-AEX Lab key reuse witnesses; keep ordered per-pixel comparator mutation."""
import os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmcolorkey import Adapter
from core import evaluate,save_corpus
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance/key-witnesses';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',max_size=256,case_timeout=10,size_sampler='default'))
prov=a.prepare(S,time.monotonic()+300);prov['case_timeout_seconds']=10
out=ROOT/'tests/fuzz_corpus/olmcolorkey/P05c-lab-key-cache';out.mkdir(parents=True,exist_ok=True)
for depth in (8,16,32):
 for space in (3,4):
  for component in (0,1):
   for count in (2,25):
    c=a.generate(20261024,0);w,h=9,7;c.update(geometry=[w,h],depth=depth,profile='sdr',input_padding=7,output_padding=7)
    params={p['slot']:p for p in a.defaults(w,h)}
    for slot,value in {1:1,2:0,4:0,5:space,7:0,8:component,9:0,10:0,11:0,14:0,18:0,22:count,23:0}.items():params[slot]['value']=value
    palette=[]
    for i in range(count):
     color=[255,(i*79+204)%256,(i*59+38)%256,(i*31+26)%256];palette.append(color)
     params[24+8*i]['value']=int(i%3!=1);params[26+8*i]['value']=color
    c['parameters']=list(params.values())
    pixels=[palette[(x+y*3)%count] for y in range(h) for x in range(w)]
    c['pixels']=b''.join(bytes(v) if depth==8 else struct.pack('<4H',*[(x*32768+127)//255 for x in v]) if depth==16 else struct.pack('<4f',*[x/255 for x in v]) for v in pixels)
    r=evaluate(a,c,S,time.monotonic()+60,{})
    assert r['routes']['smart']['status']=='exact',r
    path=out/f'PF{depth}-space{space}-component{component}-count{count}.json'
    save_corpus(path,a,c,c,r,dict(accepted=[],label='P05c repeated palette with disabled and later keys'),prov)
    print(path.name,r['routes']['smart']['status'],flush=True)
