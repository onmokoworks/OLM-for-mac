#!/usr/bin/env python3
"""Recheck default timeout and the no-op ROI boundary with a 60-second oracle cap."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.radialblur import Adapter
from geometry import sample,require_host
from core import evaluate
from run import main_checkout
s=ROOT/'orchestra/state/P02d-radialblur-geometry/boundaries';s.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=60));a.routes=('smart',)
deadline=time.monotonic()+600;p=a.prepare(s,deadline);rows=[]
for seed,index,mode in [(1,62,'default'),(20261024,38,'realistic')]:
 c=sample(a.generate(seed,index),mode);require_host(a,c);r=evaluate(a,c,s,deadline)
 rows.append(dict(seed=seed,index=index,mode=mode,result=r));print(seed,index,r['routes']['smart']['status'],flush=True)
(ROOT/'orchestra/reports/P02d-evidence/boundaries.json').write_text(json.dumps(dict(provenance=p,cases=rows),indent=2)+'\n')
assert all(r['result']['routes']['smart']['status']=='exact' for r in rows)
