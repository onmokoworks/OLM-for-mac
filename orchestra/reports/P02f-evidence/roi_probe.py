"""Reproduce F52c's Smoother2 output-allocation boundary without rebuilding it."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmsmoother2 import Adapter
from core import sha
from run import main_checkout
s=ROOT/'orchestra/state/P02f-smoother2-geometry/roi';s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=16,case_timeout=10));a.env.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s));rows=[]
c=a.generate(1,0);c.update(geometry=[7,5],depth=8,parameters=a.defaults(7,5),pixels=bytes([255,32,64,128])*35,geometry_sampler='realistic-v1',full_geometry=[7,5],downsample=[[1,1],[1,1]],rowbytes_padding=0,extent_hint=[0,0,7,5],pixel_aspect=[1,1])
for rect in ([0,0,7,5],[-2,-1,9,7],[2,1,4,3],[20,20,21,21]):
 c['request_rect']=rect;observed=[];a.session_observed=lambda out,err:observed.append(err.decode(errors='replace'))
 r,raw=a.oracle(c,s,time.monotonic()+15,'smart');rows.append(dict(request=rect,result=r,output_bytes=len(raw),sha256=sha(raw),diagnostics=observed))
(s/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print([(r['request'],r['result']['status'],r['output_bytes']) for r in rows])
