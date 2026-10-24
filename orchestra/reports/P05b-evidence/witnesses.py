#!/usr/bin/env python3
"""Retain six fresh, original-AEX rotation witnesses for exact scatter changes."""
import json, os, struct, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from core import evaluate,save_corpus
from run import main_checkout
STATE=ROOT/'orchestra/state/P05b-radialblur-rotation-performance/witnesses'
STATE.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE),OLM_TEST_JOBS='1')
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=60))
deadline=time.monotonic()+1800
provenance=a.prepare(STATE,deadline)
provenance['P05b']='Original-AEX rotation scatter witnesses; independent channel payloads, quality extremes, forward/back scatter.'
rows=[]
for index,(depth,quality) in enumerate((d,q) for d in (8,16,32) for q in (1,50)):
 c=a.generate(505, index);w,h=3,2
 c.update(depth=depth,geometry=[w,h],profile='sdr',parameters=a.defaults(w,h),input_padding=0,output_padding=0)
 values={1:2,4:4,10:3,20:quality}
 for p in c['parameters']:
  if p['slot'] in values:p['value']=values[p['slot']]
 pixels=[(255,30,60,90),(128,250,30,20),(0,0,0,0),(255,200,90,10),(64,50,180,70),(255,10,200,240)]
 c['pixels']=b''.join(bytes(v) if depth==8 else struct.pack('<4H',*(round(x*32768/255) for x in v)) if depth==16 else struct.pack('<4f',*(x/255 for x in v)) for v in pixels)
 r=evaluate(a,c,STATE,deadline,{})
 rows.append(dict(depth=depth,quality=quality,result=r))
 (STATE/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 if r['routes']['smart']['status']!='exact':raise RuntimeError(rows[-1])
 dest=ROOT/'tests/fuzz_corpus/radialblur/P05b-rotation-performance';dest.mkdir(parents=True,exist_ok=True)
 save_corpus(dest/f'PF{depth}-quality{quality}.json',a,c,c,r,{'accepted':[]},provenance)
 print(depth,quality,'Smart exact',flush=True)
