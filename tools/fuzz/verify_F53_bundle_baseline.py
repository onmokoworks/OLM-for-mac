#!/usr/bin/env python3
"""Identify whether ColorKeep bundle iterate limitation predates F53."""
import json,os,time
from pathlib import Path
from types import SimpleNamespace
from adapters.plugin_bundle import Adapter
from geometry import sample,require_host
from run import main_checkout
from verify_F53 import ROOT
S=ROOT/'orchestra/state/F53-oracle-cropped-checkout/bundle-baseline';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
a=Adapter(SimpleNamespace(plugin='colorkeep',plugin_bundle=Path.home()/'.cache/olm-emu/P00b/xcode/ColorKeep/products/ColorKeep.plugin',main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker',max_size=256,case_timeout=10))
rows=[]
for version in ('realistic-v1','realistic-v2'):
 c=sample(a.generate(1,0),version);require_host(a,c)
 p=a.prepare(S,time.monotonic()+30)
 result=a.candidate(c,S,'smart',time.monotonic()+15)
 rows.append(dict(version=version,provenance=p,status=result[0]))
(ROOT/'orchestra/reports/F53-evidence/bundle-baseline.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['status']['status']=='harness_error' and 'callback: iterate' in r['status']['diagnostic'] for r in rows)
print('CONFIRMED: F52c and F53 bundle hosts both reject ColorKeep iterate callback')
