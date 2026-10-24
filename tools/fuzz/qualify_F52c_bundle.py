#!/usr/bin/env python3
"""Probe the cached A01 bundles with the isolated F52c geometry host."""
import json,time
from pathlib import Path
from types import SimpleNamespace
from core import sha
from geometry import sample
from run import main_checkout
from adapters.plugin_bundle import Adapter
from adapters.bundle_geometry import HOST
from measure_F52c import S,PLUGINS
NAMES=('ColorKeep','OLMDistanceGradation','OLMKiraKira','OLMRadialBlur','OLMToonDilate','OLMSmoother2','OLMSmoother','OLMBlur')
def main():
 rows=[];s=S/'bundle-qualification';s.mkdir(parents=True,exist_ok=True)
 for plugin,name in zip(PLUGINS,NAMES):
  a=Adapter(SimpleNamespace(plugin=plugin,plugin_bundle=Path.home()/'.cache/olm-emu/A01/xcode'/name/'products'/(name+'.plugin'),main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
  a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
  for i in range(3):
   c=sample(a.generate(1,i),'realistic');route='classic' if plugin=='olmsmoother' else 'smart'
   r,raw,*guards=a.candidate(c,s,route,time.monotonic()+30)
   rows.append(dict(plugin=plugin,index=i,route=route,result=r,guards=guards,raw_sha256=sha(raw),bundle_sha256=sha(a.executable.read_bytes()),host_sha256=sha(HOST.read_bytes())))
   (S/'bundle-qualification.json').write_text(json.dumps(rows,indent=2)+'\n')
   assert r['status'] in ('ok','refusal'),rows[-1]
   expected=[*c['full_geometry'],*c['downsample'][0],*c['downsample'][1],*c['pixel_aspect'],c['rowbytes_padding']]
   assert list(map(int,r['metadata']['GEOMETRY_INPUT'].split()))==expected,rows[-1]
  print(plugin,'bundle delivery passed',flush=True)
 print('PASS',len(rows),'bundle delivery probes')
if __name__=='__main__':main()
