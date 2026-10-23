#!/usr/bin/env python3
"""Compare retained numerical evidence with a fresh run (no timing fields)."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
state=root/'orchestra/state/F28-ucrtmath-lib-amd'
expected=root/'ucrtmath/tests/results'
files=sorted(expected.glob('*.json'))
files=[p for p in files if p.name.startswith(('targeted-','full-','survey-'))]
assert files
for p in files:
 want=json.loads(p.read_text());got=json.loads((state/p.name).read_text())
 assert got==want,p.name
 if p.name.startswith(('targeted-','full-')):
  assert all(m['mismatches']==0 for m in got['modes']),p.name
 print('PASS',p.name,got['count'])
