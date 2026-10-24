#!/usr/bin/env python3
"""Retain measured realistic-v1 cases, one per depth/mode/padding combination."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmblur import Adapter
from core import save_corpus,sha
from geometry import sample
from run import main_checkout
E=ROOT/'orchestra/reports/P02h-evidence'
C=ROOT/'tests/fuzz_corpus/olmblur_realistic_P02h'
C.mkdir(parents=True,exist_ok=True)
a=Adapter(SimpleNamespace(main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker',max_size=256,case_timeout=10))
seen=set()
for seed in (1,20261025):
 report=json.loads((E/f'candidate-realistic-{seed}.json').read_text())
 for row in report['cases']:
  case=sample(a.generate(seed,row['index']),'realistic')
  key=(case['depth'],case['parameters'][4]['value'],case['input_padding'])
  if key in seen:continue
  assert row['input_sha256']==sha(case['pixels'])
  assert row['result']['routes']['smart']['status']=='exact'
  save_corpus(C/f'seed{seed}_case{case["index"]:06}.json',a,case,case,row['result'],{'accepted':[],'attempts':0},report['provenance'])
  seen.add(key)
print('Saved',len(seen),'realistic-v1 witnesses')
