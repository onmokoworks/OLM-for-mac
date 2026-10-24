#!/usr/bin/env python3
"""Compare F52c and F53 original output when --checkout-rect is absent."""
import importlib,json,os,time
from pathlib import Path
from types import SimpleNamespace
from geometry import sample
from run import main_checkout
from verify_F53 import PLUGINS,ROOT
from core import sha
S=ROOT/'orchestra/state/F53-oracle-cropped-checkout/legacy';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
rows=[]
for plugin in PLUGINS:
 a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=64,case_timeout=10))
 a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
 for mode in ('default','realistic'):
  for i in range(3):
   c=sample(a.generate(1,i),mode);observed=[]
   for worker in ('worker-F52c-geom','worker-F53-geom'):
    a.worker=Path.home()/'.cache/olm-emu'/worker/'aex-guest-worker'
    r,b=a.oracle(c,S,time.monotonic()+15,'classic' if plugin=='olmsmoother' else 'smart')
    observed.append(dict(status=r['status'],output_rect=r.get('output_rect'),sha256=sha(b),bytes=len(b)))
   rows.append(dict(plugin=plugin,mode=mode,index=i,equal=observed[0]==observed[1],observed=observed))
   print(plugin,mode,i,rows[-1]['equal'],flush=True)
p=ROOT/'orchestra/reports/F53-evidence/legacy.json';p.write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['equal'] for r in rows)
print('PASS',len(rows),'legacy oracle pairs;',sum(r['observed'][0]['status']=='ok' for r in rows),'successful byte comparisons')
