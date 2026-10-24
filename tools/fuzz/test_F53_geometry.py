#!/usr/bin/env python3
"""Check backwards-compatible generation and v2 procedural corpus replay."""
import subprocess,types,tempfile,time
from pathlib import Path
from geometry import sample
from core import save_corpus,load_corpus
from adapters.olmdirectionalblur import Adapter
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
old=types.ModuleType('old_geometry')
exec(subprocess.check_output(['git','show','d0bc511591bd92b0bc3e0a28d038dd41f3bec8ed:tools/fuzz/geometry.py']),old.__dict__)
a=Adapter(types.SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
s=ROOT/'orchestra/state/F53-oracle-cropped-checkout';s.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(dir=s) as td:
 for i in range(100):
  c=a.generate(1,i)
  for mode in ('default','realistic','realistic-v1'):assert sample(c,mode)==old.sample(c,mode)
  v=sample(c,'realistic-v2');w,h=v['geometry'];assert len(v['pixels'])==w*h*v['depth']//8*4
  path=Path(td)/'case.json'
  save_corpus(path,a,v,v,{},dict(accepted=[]),{})
  loaded=load_corpus(path,a)
  # load_corpus returns case plus its persisted metadata.
  assert loaded[0]==v
print('PASS: 300 unchanged default/v1 cases; 100 v2 payloads and corpus replays')
