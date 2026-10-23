#!/usr/bin/env python3
"""Capture the first failing numeric cell via unchanged legacy harness functions.

Run with MAIN's emulator Python and TMPDIR set to the R03 scratch directory.
The full, unchanged fixture commands are recorded separately by R03-rerun.py.
"""
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/R03-harness-ucrt-link'
sys.path.insert(0,str(ROOT/'tools/emulation'))
index=int(sys.argv[1])
rows=[r for r in json.loads((ROOT/'orchestra/reports/I03-classification.json').read_text())['failures']
      if r['category']=='a: UCRT link dependency' or r['category'].startswith('mixed:')]
module=importlib.import_module(Path(rows[index]['command'][-1]).stem)
if index==39:
    cell={'noise_variation':0.0}
    expected=module.capture(0.0)
    module.pf32.NOISE_VARIATION=0.0
    actual=module.pf32.mac_production(expected)
elif index==41:
    cell={'ratio':2.0,'angle':0.0}
    rc,expected=module.isolated('actual',2.0,0.0)
    assert rc==0
    rc,actual=module.isolated('production',2.0,0.0,expected)
    assert rc==0
elif index==42:
    cell={'effect':'rotation','ratio':2.0,'angle':0.0}
    rc,expected=module.isolated('rotation','actual',2.0,0.0)
    assert rc==0
    rc,actual=module.isolated('rotation','production',2.0,0.0,expected)
    assert rc==0
elif index==43:
    cell={'noise_variation':25.0,'outer_strength':5}
    expected=module.actual_at(25.0)
    actual=module.production_at(25.0,expected)
elif index==44:
    cell={'offset':2,'noise_variation':25.0}
    expected=module.actual_at(2,25.0)
    actual=module.production_at(2,25.0,expected)
elif index==45:
    cell={'inner_strength':50.0,'noise_variation':0.0}
    expected=module.actual(50.0,0.0)
    actual=module.production(50.0,0.0,expected)
elif index in (55,56):
    value=50 if index==55 else 'size50'
    cell={'kind':'outer','value':value}
    expected=module.actual('outer',value)
    actual=module.production('outer',value,expected)
else:
    raise SystemExit(f'No supplemental cell requested for index {index}')
comparisons=[]
for name in sorted(expected.keys() & actual.keys()):
    a,b=expected[name],actual[name]
    if not isinstance(a,bytes) or not isinstance(b,bytes):continue
    first=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
    if first is None and len(a)!=len(b):first=min(len(a),len(b))
    row=dict(plane=name,expected_bytes=len(a),actual_bytes=len(b),first_byte=first,
             differing_bytes=sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b)),
             expected_sha256=hashlib.sha256(a).hexdigest(),actual_sha256=hashlib.sha256(b).hexdigest())
    if first is not None:
        start=first//4*4
        row.update(expected_word=a[start:start+4].hex(),actual_word=b[start:start+4].hex())
    comparisons.append(row)
out=S/'diagnostics'/str(index);out.mkdir(parents=True,exist_ok=True)
(out/'first-differences.json').write_text(json.dumps(dict(key=rows[index]['key'],cell=cell,comparisons=comparisons),indent=2)+'\n')
print(json.dumps(dict(index=index,cell=cell,different_planes=[r['plane'] for r in comparisons if r['first_byte'] is not None])))
