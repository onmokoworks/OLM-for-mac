#!/usr/bin/env python3
"""DirectionalBlur cropped-checkout witnesses using the retained F53 oracle."""
import argparse,importlib,json,os,sys,time,shutil,subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/fuzz'))
from core import evaluate,sha,save_corpus
from geometry import sample,require_host
from run import main_checkout
ROOT=Path(__file__).resolve().parents[3]
PLUGINS=('olmdirectionalblur',)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--jobs',type=int,choices=(1,),default=1);ap.add_argument('--survey',action='store_true');ap.add_argument('--corpus',action='store_true');ap.add_argument('--bundle',action='store_true');ap.add_argument('--n',type=int,default=100);ap.add_argument('--label',default='witness');ap.add_argument('--plugin',choices=PLUGINS);a=ap.parse_args()
 scratch=ROOT/'orchestra/state/P04b2-directionalblur-cropped-checkout'/a.label;scratch.mkdir(parents=True,exist_ok=True)
 evidence=ROOT/'orchestra/reports/P04b2-evidence';evidence.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
 summary={}
 for plugin in ((a.plugin,) if a.plugin else PLUGINS if a.survey else PLUGINS):
  s=scratch/plugin;s.mkdir(exist_ok=True);deadline=time.monotonic()+3600
  adapter=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=256,case_timeout=10))
  if a.bundle:
   from adapters.plugin_bundle import Adapter as BundleAdapter
   name={'radialblur':'OLMRadialBlur','olmdistancegradation':'OLMDistanceGradation'}.get(plugin,getattr(adapter,'aex_name',None))
   adapter=BundleAdapter(SimpleNamespace(plugin=plugin,plugin_bundle=Path.home()/'.cache/olm-emu/P00b/xcode'/name/'products'/(name+'.plugin'),main=main_checkout(),worker=adapter.worker,max_size=256,case_timeout=10))
  require_host(adapter,{'geometry_sampler':'realistic-v2'})
  adapter.routes=('classic','smart') if a.corpus else ('classic',) if plugin=='olmsmoother' else ('smart',)
  provenance=adapter.prepare(s,deadline)
  (evidence/(a.label+'-'+plugin+'-provenance.json')).write_text(json.dumps(provenance,indent=2)+'\n')
  counts=Counter();original=Counter();mac=Counter();tags=Counter()
  with (evidence/(a.label+'-'+plugin+'.jsonl')).open('w') as out:
   for i in range(a.n if a.survey else 4):
    c=sample(adapter.generate(1,i),'realistic-v2')
    if not a.survey:
     rect=[0,0,20,15] if i<2 else [3,4,23,19]
     c.update(geometry=[20,15],full_geometry=[40,30],downsample=[[1,1],[1,1]],checkout_rect=rect,
        request_rect=rect,extent_hint=[0,0,20,15],depth=8,pixels=bytes((j*17+31)%256 for j in range(1200)),
        parameters=adapter.defaults(20,15),pixel_aspect=[1,1],rowbytes_padding=0,input_padding=0,output_padding=0)
     if plugin=='olmdirectionalblur':
      for p in c['parameters']:
       if p['slot']==5:p['value']=5
     if i%2:
      del c['checkout_rect'];c['geometry']=[40,30];c['pixels']=bytes((j*17+31)%256 for j in range(4800));c['extent_hint']=[0,0,40,30]
    observed=[];adapter.session_observed=lambda o,e:observed.append(e.decode(errors='replace'))
    attribution={};result=evaluate(adapter,c,s,deadline,attribution)
    if a.corpus:
     corpus=ROOT/'tests/fuzz_corpus/olmdirectionalblur/P04b2-cropped-checkout';corpus.mkdir(parents=True,exist_ok=True)
     save_corpus(corpus/f'witness-{i}.json',adapter,c,c,result,dict(accepted=[],attempts=0),provenance)
    for route,v in result['routes'].items():
     counts[v['status']]+=1
     oracle=result.get('oracles',{}).get(route,result['oracle'])
     if oracle['status']!='ok':original[oracle['status']]+=1
     if v['status']=='refusal' and oracle['status']=='ok':mac['refusal']+=1
    tags.update(t for ts in attribution.values() for t in ts)
    out.write(json.dumps(dict(index=i,case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),result=result,refusals=attribution,oracle_stderr=observed))+'\n');out.flush()
    print(plugin,i,{r:v['status'] for r,v in result['routes'].items()},flush=True)
  summary[plugin]=dict(counts=dict(counts),original_non_ok=dict(original),mac_only_refusals=dict(mac),tags=dict(tags))
  (evidence/(a.label+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n')
  # Only disposable host artifacts live here; committed logs retain all observations.
  shutil.rmtree(s)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
