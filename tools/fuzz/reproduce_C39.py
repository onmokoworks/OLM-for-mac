#!/usr/bin/env python3
"""Reproduce the two C39 known-red witnesses with the current default worker."""
import sys,os,json,time,importlib,argparse
from pathlib import Path
from types import SimpleNamespace
R=Path.cwd(); S=R/'orchestra/state/C39-seed45-residual-mismatches'
sys.path.insert(0,str(R/'tools/fuzz'))
from run import main_checkout,default_worker
from core import evaluate,save_corpus
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1')
p=argparse.ArgumentParser();p.add_argument('--plugin',choices=['olmdistancegradation','radialblur'],required=True);args=p.parse_args()
for plugin,index in [(args.plugin,2 if args.plugin=='olmdistancegradation' else 8)]:
 d=S/plugin;d.mkdir(exist_ok=True)
 a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=default_worker(),max_size=256,case_timeout=60))
 deadline=time.monotonic()+600;p=a.prepare(d,deadline);c=a.generate(45,index);result=evaluate(a,c,d,deadline)
 save_corpus(d/'witness.json',a,dict(seed=45,index=index),c,result,dict(accepted=[]),p)
 print(plugin,json.dumps({k:v for k,v in c.items() if k!='pixels'}),json.dumps(result),flush=True)
