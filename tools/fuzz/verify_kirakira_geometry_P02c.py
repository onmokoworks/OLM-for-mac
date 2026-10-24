#!/usr/bin/env python3
"""Serial KiraKira geometry measurements; reports every unavailable reference."""
import argparse,json,os,time,struct,copy,subprocess
from pathlib import Path
from types import SimpleNamespace
from adapters.olmkirakira import Adapter
from core import evaluate,sha,save_corpus,load_corpus
from geometry import sample,require_host
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
def boundaries(a):
 index=0
 for depth in (8,16,32):
  for num,den in ((1,1),(1,3),(2,3)):
   w,h=(17*num+den-1)//den,(11*num+den-1)//den
   pixels=b''.join(struct.pack({8:'4B',16:'4H',32:'4f'}[depth], *([255,(x*17+y*11)%256,(x*3+y*29)%256,(x*53+y*7)%256] if depth==8 else [32768,(x*2311+y*601)%32769,(x*997+y*1901)%32769,(x*2003+y*1709)%32769] if depth==16 else [1.0,(x*17+y*11)%256/255,(x*3+y*29)%256/255,(x*53+y*7)%256/255])) for y in range(h) for x in range(w))
   for approx in (0,1):
    for rect in ([0,0,w,h],[1,1,w-1,h-1],[-3,-2,w+4,h+3],[w+1,h+1,w+2,h+2]):
     c=a.generate(77,index);c.update(geometry=[w,h],depth=depth,pixels=pixels,parameters=a.defaults(w,h),geometry_sampler='realistic-v1',full_geometry=[17,11],downsample=[[num,den],[num,den]],extent_hint=[1,1,w-1,h-1],request_rect=rect,pixel_aspect=[4,3],rowbytes_padding=7,input_padding=7,output_padding=7)
     for p in c['parameters']:
      if p['slot'] in (10,16,22,28):p['value']=6
      if p['slot']==34:p['value']=3
      if p['slot'] in (1,2):p['value']=1
      if p['slot']==4:p['value']=approx
     yield str(index),c
     index+=1

def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--seed',type=int,default=1);p.add_argument('--n',type=int,default=100);p.add_argument('--geometry',choices=['default','realistic'],default='realistic');p.add_argument('--replay',action='store_true');p.add_argument('--baseline',type=Path);p.add_argument('--baseline-revision');p.add_argument('--boundary',action='store_true');p.add_argument('--corpus',action='store_true');p.add_argument('--jobs',type=int,choices=[1],default=1);args=p.parse_args()
 s=ROOT/'orchestra/state/P02c-kirakira-geometry'/args.label;s.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s));deadline=time.monotonic()+7200
 a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=20))
 a.routes=('smart',);a.oracle_routes={'smart':'smart'}
 require_host(a,sample(a.generate(args.seed,0),args.geometry));prov=a.prepare(s,deadline)
 if args.baseline_revision:
  import adapters.olmkirakira as module
  saved_source=module.SOURCE
  source_dir=s/'baseline-source';source_dir.mkdir(exist_ok=True)
  for name in ('OLMKiraKira.cpp','OLMKiraKira.h','OLMKiraKira_Strings.cpp','OLMKiraKira_Strings.h'):
   body=subprocess.check_output(['git','show',args.baseline_revision+':mac/OLMKiraKira/'+name],cwd=ROOT).decode()
   body=body.replace('#include "../../', '#include "'+str(ROOT)+'/')
   (source_dir/name).write_text(body)
  build=s/'baseline-build';build.mkdir(exist_ok=True)
  try:
   module.SOURCE=source_dir/'OLMKiraKira.cpp'
   args.baseline,_=a.build(build,deadline)
  finally:module.SOURCE=saved_source
  prov['baseline_revision']=args.baseline_revision
  prov['baseline_candidate_sha256']=sha(args.baseline.read_bytes())
 (s/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
 cases=((str(i),sample(a.generate(args.seed,i),args.geometry)) for i in range(args.n))
 if args.boundary:cases=boundaries(a)
 if args.replay:
  cases=((str(f.relative_to(ROOT)),load_corpus(f,a)[0]) for d in sorted((ROOT/'tests/fuzz_corpus').glob('olmkirakira*')) for f in sorted(d.glob('*.json')))
 counts={};regressions=[];changes=[]
 with (s/'results.jsonl').open('w') as out:
  for name,c in cases:
   attr={};r=evaluate(a,c,s,deadline,attr)
   if args.baseline:
    old=copy.copy(a);old.binary=args.baseline.resolve()
    # Candidate-only regression: unchanged bytes/status need no extra oracle.
    old_result,old_raw,*_=old.candidate(c,s,'smart',deadline)
    new_result,new_raw,*_=a.candidate(c,s,'smart',deadline)
    if old_result['status']!=new_result['status'] or old_raw!=new_raw:
     oracle,ref=a.oracle(c,s,deadline,'smart')
     row=dict(name=name,before=old_result,after=new_result,oracle=oracle,before_sha256=sha(old_raw),after_sha256=sha(new_raw))
     changes.append(row)
     if oracle['status']=='ok' and old_result['status']=='ok' and old_raw==ref and not(new_result['status']=='ok' and new_raw==ref):regressions.append(row)
   status=r['routes']['smart']['status'] if r['oracle']['status']=='ok' else 'unavailable'
   counts[status]=counts.get(status,0)+1
   out.write(json.dumps(dict(name=name,case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),result=r,refusals=attr))+'\n');out.flush()
   if args.corpus:
    d=ROOT/'tests/fuzz_corpus/olmkirakira_realistic_P02c';d.mkdir(exist_ok=True)
    save_corpus(d/(f'boundary_{int(name):06d}.json' if args.boundary else f'seed{args.seed}_{int(name):06d}.json'),a,c,c,r,{'accepted':[]},prov)
   print(name,status,flush=True)
 (s/'summary.json').write_text(json.dumps(dict(counts=counts,changes=changes,regressions=regressions),indent=2)+'\n');print(counts,'regressions',len(regressions))
 if regressions or any(k not in ('exact','unavailable') for k in counts):raise SystemExit(1)
if __name__=='__main__':main()
