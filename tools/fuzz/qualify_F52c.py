#!/usr/bin/env python3
"""Bounded per-adapter delivery checks, separate from numerical campaign status."""
import importlib,json,time,shutil
from pathlib import Path
from types import SimpleNamespace
from core import sha
from geometry import sample
from run import main_checkout
from measure_F52c import ROOT,S,PLUGINS

def main():
 rows=[]
 for name in PLUGINS:
  s=S/'qualification-hosts'/name
  if s.exists():shutil.rmtree(s)
  s.mkdir(parents=True)
  a=importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
  a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s));deadline=time.monotonic()+300
  provenance=a.prepare(s,deadline)
  for i in range(3):
   c=sample(a.generate(1,i),'realistic')
   for route in (('classic',) if name=='olmsmoother' else a.routes):
    r,raw,*_=a.candidate(c,s,route,deadline)
    expected=[*c['full_geometry'],*c['downsample'][0],*c['downsample'][1],*c['pixel_aspect'],c['rowbytes_padding']]
    observed=list(map(int,r.get('metadata',{}).get('GEOMETRY_INPUT','').split()))
    rows.append(dict(plugin=name,index=i,route=route,status=r['status'],expected=expected,observed=observed,candidate_sha256=provenance['candidate_sha256'],result=r))
    (S/'host-qualification.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert r['status'] in ('ok','refusal'), rows[-1]
    assert observed==expected,rows[-1]
  print(name,'delivery checks passed',flush=True)
 print('PASS',len(rows),'per-adapter delivery checks')
if __name__=='__main__':main()
