"""Actual-AEX witnesses for PF16 stack-frame specialization, with PF8 controls."""
import os,sys,time,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmsmoother import Adapter
from core import evaluate,save_corpus
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance/smooth-witnesses';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',max_size=256,case_timeout=10,size_sampler='default'))
prov=a.prepare(S,time.monotonic()+300);prov['case_timeout_seconds']=10
out=ROOT/'tests/fuzz_corpus/olmsmoother/P05c-stack-frames';out.mkdir(parents=True,exist_ok=True)
palette=[(255,255,255,255),(255,0,0,0),(128,128,128,128),(255,252,254,250)]
for depth in (8,16):
 for pattern in range(4):
  for key in (0,1):
   for tolerance in (0,6,255):
    w,h=17,19;c=a.generate(2026102505,pattern);c.update(geometry=[w,h],depth=depth,profile='sdr',input_padding=16,output_padding=16)
    params={p['slot']:p for p in a.defaults(w,h)}
    params[1]['value']=key;params[2]['value']=[255,255,255,255];params[3]['value']=tolerance;c['parameters']=list(params.values())
    pixels=[]
    for y in range(h):
     for x in range(w):
      index=(x//3 if pattern==0 else y//3 if pattern==1 else (x+y)//3 if pattern==2 else x//2+y//2)%4
      pixel=palette[index]
      pixels.append(bytes(pixel) if depth==8 else struct.pack('<4H',*[(v*32768+127)//255 for v in pixel]))
    c['pixels']=b''.join(pixels);r=evaluate(a,c,S,time.monotonic()+60,{})
    assert r['routes']['classic']['status']=='exact',r
    path=out/f'PF{depth}-pattern{pattern}-key{key}-tolerance{tolerance}.json'
    save_corpus(path,a,c,c,r,dict(accepted=[],label='P05c virtual stack frame: directional SDR patterns, key and tolerance boundaries'),prov)
    print(path.name,'classic exact',flush=True)
