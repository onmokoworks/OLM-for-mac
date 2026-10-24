#!/usr/bin/env python3
"""Retry only unresolved Smart wall budgets; preserve original observations."""
import json,os,sys,time,shutil
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from core import evaluate,sha
from geometry import sample,require_host
from run import main_checkout
E=ROOT/'orchestra/reports/P04b2-evidence';S=ROOT/'orchestra/state/P04b2-directionalblur-cropped-checkout/retries';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
for label in sys.argv[1:]:
 d=json.loads((E/(label+'.json')).read_text());a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path(d['provenance']['worker_path']),max_size=d['max_size'],size_sampler=d['size_sampler'],size_max_height=d.get('size_max_height'),case_timeout=60))
 a.routes=('smart',);s=S/label;s.mkdir(exist_ok=True);provenance=a.prepare(s,time.monotonic()+300);rows=[]
 for row in d['cases']:
  r=row['result'];o=r.get('oracles',{}).get('smart',r['oracle'])
  if o['status']!='budget':continue
  sampler='realistic-v2' if label.startswith('realistic-v2') else 'realistic' if label.startswith(('realistic','odd-even')) else 'default'
  c=sample(a.generate(row['seed'],row['index']),sampler);assert sha(c['pixels'])==row['input_sha256'];require_host(a,c)
  observed=evaluate(a,c,s,time.monotonic()+180)
  rows.append(dict(index=row['index'],seed=row['seed'],input_sha256=sha(c['pixels']),result=observed))
  print(label,row['index'],observed['routes']['smart']['status'],flush=True)
  (E/(label+'-retry.json')).write_text(json.dumps(dict(provenance=provenance,case_timeout=60,rows=rows),indent=2)+'\n')
 shutil.rmtree(s)
