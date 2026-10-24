#!/usr/bin/env python3
"""Input-only boundary probes; no candidate/source edits or weakened admission."""
import copy, importlib, json, math, os, shutil, struct, time
from types import SimpleNamespace
from core import evaluate, load_corpus, sha
from geometry import require_host
from run import main_checkout
from sweep_T15b import ROOT,S,E,WORKER,write

def main():
 name='olmdistancegradation';stage=S/'distance-boundaries';stage.mkdir(parents=True,exist_ok=True)
 os.environ.update(TMPDIR=str(stage),TMP=str(stage),TEMP=str(stage))
 summary=json.loads((E/(name+'-summary.json')).read_text())
 a=importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=WORKER,max_size=summary['maximum'],case_timeout=10))
 require_host(a,{'geometry_sampler':'realistic-v1'});a.routes=('smart',);a.oracle_routes={'smart':'smart'}
 provenance=a.prepare(stage,time.monotonic()+300);rows=[]
 for w in summary['witnesses']:
  c,_=load_corpus(ROOT/w['path'],a);cc=copy.deepcopy(c)
  if w['failure_class'].startswith('pixels'):
   cc['downsample']=[[1,1],[1,1]];cc['full_geometry']=list(cc['geometry'])
   op='unit downsample and matching full geometry; same sampled pixels, parameters, ROI and padding'
  elif w['first_seed']==2026:
   next(p for p in cc['parameters'] if p['slot']==10)['value']=1.0
   op='Power exponent 1, triggering the existing Linear normalization; same HDR pixels, Gaussian size, geometry and padding'
  else:
   vals=[v[0] for v in struct.iter_unpack('<f',cc['pixels'])]
   cc['pixels']=b''.join(struct.pack('<f',v if math.isfinite(v) else 0.5) for v in vals)
   op='nonfinite pixel lanes replaced by 0.5; same Bilateral-0 parameters, geometry and padding'
  before=evaluate(a,c,stage,time.monotonic()+30);after=evaluate(a,cc,stage,time.monotonic()+30)
  rows.append(dict(witness=w['path'],operation=op,before=before,after=after,before_input_sha256=sha(c['pixels']),after_input_sha256=sha(cc['pixels'])))
  print(w['first_seed'],w['first_index'],before['routes']['smart']['status'],'->',after['routes']['smart']['status'],flush=True)
 write(E/'olmdistancegradation-boundaries.json',dict(provenance=provenance,rows=rows))
 shutil.rmtree(stage)
if __name__=='__main__':main()
