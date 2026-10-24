#!/usr/bin/env python3
"""Independent Smart geometry witnesses, including reverse-asymmetric scales."""
import argparse,collections,json,struct,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import evaluate,save_corpus,sha
from run import main_checkout
p=argparse.ArgumentParser();p.add_argument('--sanitize',action='store_true');args=p.parse_args()
S=ROOT/'orchestra/state/P02b-distancegradation-geometry'/('witnesses-san' if args.sanitize else 'witnesses');S.mkdir(exist_ok=True,parents=True)
class Host(Adapter):
 def compile(self,argv,deadline):
  if args.sanitize and str(argv[0])=='clang++':argv=[*argv,'-fsanitize=address,undefined','-fno-sanitize-recover=all']
  return super().compile(argv,deadline)
a=Host(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
if args.sanitize:a.routes=('smart',);a.oracle_routes={'smart':'smart'}
a.geometry_active=True
a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S));deadline=time.monotonic()+1200
provenance=a.prepare(S,deadline);(S/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
corpus=ROOT/'tests/fuzz_corpus/olmdistancegradation_realistic_P02b';corpus.mkdir(exist_ok=True)
counts=collections.Counter();failures=[]
with (S/'results.jsonl').open('w') as out:
 for depth in (8,16,32):
  for mode,size in ((2,1),(2,3),(3,1),(3,3),(3,1700)):
   for request in ('roi','expanded'):
    w,h=(1,1) if size==1700 else (5,7)
    params=a.defaults(w,h)
    for q in params:
     if q['slot'] in (2,9,11,12):q['value']={2:3,9:2,11:mode,12:size}[q['slot']]
    pixels=b''
    for y in range(h):
     for x in range(w):
      rgba=[0 if (x+3*y)%5==0 else 1,0.25,0.5,0.75]
      if depth==32:pixels+=struct.pack('<4f',*rgba)
      else:pixels+=struct.pack('<4B' if depth==8 else '<4H',*[int(v*(255 if depth==8 else 32768)) for v in rgba])
    index=sum(counts.values())
    c=dict(seed=20261024,index=10000+index,geometry=[w,h],depth=depth,profile='sdr',parameters=params,
     full_geometry=[w*3-1,h*2-1],downsample=[[1,3],[1,2]],geometry_sampler='realistic-v1',
     extent_hint=[0,0,1,1],request_rect=[0,0,1,1] if request=='roi' else [-2,-3,w+4,h+5],
     pixel_aspect=[4,3],rowbytes_padding=7,input_padding=7,output_padding=7,pixels=pixels)
    attr={};r=evaluate(a,c,S,deadline,attr)
    status=r['routes']['smart']['status'] if r['oracle']['status']=='ok' else 'unavailable'
    counts[status]+=1
    if status not in ('exact','unavailable'):failures.append(index)
    row=dict(case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(pixels),result=r,refusals=attr)
    out.write(json.dumps(row)+'\n');out.flush();print(index,status,flush=True)
    if not args.sanitize:save_corpus(corpus/f'witness{index:03d}.json',a,c,c,r,{'accepted':[],'attempts':0,'label':'P02b independent reverse-asymmetric / expanded request'},provenance)
(S/'summary.json').write_text(json.dumps(dict(counts=counts,failures=failures),indent=2)+'\n');print(dict(counts),failures)
assert not failures,failures
