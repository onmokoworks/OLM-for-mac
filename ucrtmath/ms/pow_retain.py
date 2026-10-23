#!/usr/bin/env python3
"""Retain/verify measured pow qualification, failing closed on incomplete runs."""
import argparse, hashlib, json, shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'orchestra/state/F43c-ucrtmath-ms-pow'
OUT=ROOT/'ucrtmath/ms/results/pow'
OUT.mkdir(exist_ok=True)
for tag,count in [('random-1000000000',1_000_000_000),('ranges-100000000',100_000_000),('targeted',2_243_557)]:
 src=STATE/(tag+'.json');r=json.loads(src.read_text())
 assert r['count']==count and r['exits']==[0,0]
 assert len(r['modes'])==2 and all(m['mismatches']==0 and m['mode']==i for i,m in enumerate(r['modes']))
 for path,digest in r['sha256'].items():
  if path.startswith('ucrtmath/') or path.startswith('tools/'):
   assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 if a.check:
  saved=json.loads((OUT/src.name).read_text())
  for k in ['function','count','modes','exits']:assert saved[k]==r[k],(tag,k)
 else:shutil.copyfile(src,OUT/src.name)
harness=json.loads((STATE/'harness.json').read_text())
assert len(harness)==7 and [r['exit'] for r in harness]==[0,2,2,2,1,1,2]
for name in ['targets-counts.json','harness.json']:
 if a.check:assert json.loads((STATE/name).read_text())==json.loads((OUT/name).read_text()),name
 else:shutil.copyfile(STATE/name,OUT/name)
if not a.check:
 # Preserve the observed initial NaN-sign failure, not a rejected candidate.
 shutil.copyfile(STATE/'random-1000000.json',OUT/'initial-nan-diagnostic.json')
print('3 qualification campaigns: both modes exact; source hashes and 7 harness checks verified')
