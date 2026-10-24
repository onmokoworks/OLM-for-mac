#!/usr/bin/env python3
"""Bounded negotiated-output probe; no candidate admission or qualification claim."""
import importlib,json,time
from pathlib import Path
from types import SimpleNamespace
from core import sha
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns/oracle'

def main():
 S.mkdir(parents=True,exist_ok=True);rows=[]
 for plugin in ('colorkeep','olmdistancegradation','olmkirakira','radialblur','olmtoondilate','olmsmoother2','olmsmoother','olmblur'):
  a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=16,case_timeout=10))
  a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
  case=a.generate(1,0);case.update(geometry=[7,5],depth=8,parameters=a.defaults(7,5),pixels=bytes([255,32,64,128])*35)
  for rect in (([0,0,7,5],) if plugin=='olmsmoother' else ([0,0,7,5],[-2,-1,9,7],[2,1,4,3],[20,20,21,21])):
   case.update(geometry_sampler='realistic-v1',full_geometry=[7,5],downsample=[[1,1],[1,1]],rowbytes_padding=0,extent_hint=[0,0,7,5],request_rect=rect,pixel_aspect=[1,1])
   observed=[]
   a.session_observed=lambda out,err:observed.append(dict(stdout_bytes=len(out),stderr=err.decode(errors='replace')))
   result,raw=a.oracle(case,S,time.monotonic()+15,'classic' if plugin=='olmsmoother' else 'smart')
   rows.append(dict(plugin=plugin,request=rect,result=result,output_bytes=len(raw),sha256=sha(raw),observed=observed))
  (S/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps([dict(plugin=r['plugin'],request=r['request'],status=r['result']['status'],bytes=r['output_bytes'],diagnostic=r['result'].get('diagnostic',''),negotiated=r['observed'][0]['stderr']) for r in rows],indent=2))
if __name__=='__main__':main()
