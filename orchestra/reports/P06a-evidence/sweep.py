"""PF32-only downsampled cropped requests, rejection sampling of versioned generators."""
import json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/fuzz'))
S=R/'orchestra/state/P06a-directionalblur-pf32-cropped-mismatch/sweep';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1')
from adapters.olmdirectionalblur import Adapter
from core import evaluate,save_corpus
from geometry import require_host,sample
from run import main_checkout
for mode,worker in [('realistic-v1','F52c'),('realistic-v2','F53')]:
 ad=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/f'.cache/olm-emu/worker-{worker}-geom/aex-guest-worker',max_size=256,case_timeout=10));ad.routes=('smart',)
 require_host(ad,{'geometry_sampler':mode});deadline=time.monotonic()+1800;provenance=ad.prepare(S,deadline)
 for seed in (1,2053,2069):
  rows=[];i=0
  while len(rows)<100:
   c=sample(ad.generate(seed,i),mode);i+=1
   w,h=c['geometry'];l,t,r,b=c['request_rect']
   if c['depth']!=32 or c['downsample'][0][1]==1 or (r-l)*(b-t)==w*h:continue
   result=evaluate(ad,c,S,deadline)
   rows.append(dict(index=c['index'],profile=c['profile'],geometry=c['geometry'],downsample=c['downsample'],request=c['request_rect'],result=result))
   if result['routes']['smart']['status']!='exact':
    target=S/f'{mode}-{seed}-{i}.json';save_corpus(target,ad,c,c,result,dict(accepted=[],attempts=0),provenance)
   if len(rows)%25==0:print(mode,seed,len(rows),flush=True)
  out=dict(seed=seed,sampler=mode,filter='depth32, downsample_x denominator>1, request area<input area',provenance=provenance,cases=rows)
  (R/f'orchestra/reports/P06a-evidence/sweep-{mode}-{seed}.json').write_text(json.dumps(out,indent=2)+'\n')
