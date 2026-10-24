#!/usr/bin/env python3
"""Rebuild final source and compare retained original-AEX hashes (no oracle rebuild)."""
import argparse,collections,copy,json,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from core import sha,save_corpus
from geometry import sample
from run import main_checkout,default_worker
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,default=ROOT/'orchestra/reports/P02b-evidence');p.add_argument('--save-corpus',action='store_true');p.add_argument('--sanitize',action='store_true');args=p.parse_args()
S=ROOT/'orchestra/state/P02b-distancegradation-geometry'/('retained-san' if args.sanitize else 'retained');S.mkdir(exist_ok=True,parents=True)
class Host(Adapter):
 def compile(self,argv,deadline):
  if args.sanitize and str(argv[0])=='clang++':argv=[*argv,'-fsanitize=address,undefined','-fno-sanitize-recover=all']
  return super().compile(argv,deadline)
a=Host(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10));a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S));deadline=time.monotonic()+1200
if args.sanitize:a.routes=('smart',)
a.geometry_active=True
provenance=a.prepare(S,deadline);(S/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
counts=collections.Counter();failures=[]
with (S/'results.jsonl').open('w') as out:
 for name in ('seed1','seed20261024'):
  for row in map(json.loads,(args.evidence/(name+'.jsonl')).read_text().splitlines()):
   c=sample(a.generate(row['case']['seed'],row['case']['index']),'realistic');r=copy.deepcopy(row['result'])
   assert sha(c['pixels'])==row['input_sha256']
   for route in a.routes:
    expected=r['oracles'][route];observed,raw,_=a.candidate(c,S,route,deadline)
    if expected['status']!='ok':status='unavailable'
    elif observed['status']!='ok':status='refusal'
    elif sha(raw)==expected['raw_sha256'] and observed.get('output_rect')==expected.get('output_rect'):status='exact'
    else:status='mismatch'
    counts[(name,route,status)]+=1
    if route=='smart' and status not in ('exact','unavailable'):failures.append([name,c['index'],route,status])
    if observed['status']=='ok':observed['raw_sha256']=sha(raw)
    if status=='mismatch' and sha(raw)==r['routes'][route].get('raw_sha256'):
     for key in ('diff','geometry_diff'):
      if key in r['routes'][route]:observed[key]=r['routes'][route][key]
    observed['status']=status if status!='unavailable' else ('uncompared' if observed['status']=='ok' else observed['status'])
    r['routes'][route]=observed
   out.write(json.dumps(dict(seed=c['seed'],index=c['index'],result=r))+'\n');out.flush()
   if args.save_corpus:
    folder=ROOT/'tests/fuzz_corpus/olmdistancegradation_realistic_P02b';folder.mkdir(exist_ok=True)
    path=folder/f"seed{c['seed']}_case{c['index']:06d}.json"
    if r['oracles']['smart']['status']=='ok':
     save_corpus(path,a,c,c,r,{'accepted':[],'attempts':0,'label':'P02b realistic-v1'},provenance)
    else:path.unlink(missing_ok=True)
 for row in map(json.loads,(args.evidence/'default.jsonl').read_text().splitlines()):
  c=a.generate(1,row['index']);assert sha(c['pixels'])==row['input_sha256']
  for route in a.routes:
   observed,raw,_=a.candidate(c,S,route,deadline);old=row['routes'][route]
   # Exact-to-non-exact is checked against the baseline original-AEX match.
   same=sha(raw)==old['before_sha256']
   status='retained' if same else 'changed'
   counts[('default',route,status)]+=1
   if old['before']=='exact' and (not same or observed['status']!='ok'):failures.append(['default',row['index'],route,'regression'])
summary=dict(counts={str(k):v for k,v in counts.items()},failures=failures,
 source_sha256=sha((ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.cpp').read_bytes()),
 fieldgen_sha256=sha((ROOT/'core/olmdistancegradation_fieldgen.cpp').read_bytes()),binary_sha256=sha(a.binary.read_bytes()))
(S/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));assert not failures,failures
