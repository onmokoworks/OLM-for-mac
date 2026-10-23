#!/usr/bin/env python3
"""Deterministic inputs only; expected outputs always come from the PE oracle."""
import json,pathlib,struct,sys,gzip,csv
root=pathlib.Path(__file__).resolve().parents[2]
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
sets={f:set() for f in ('expf','atan2f','powf')}
for case in json.loads((root/'tools/ucrt_math_probe/rosetta/results-f27c/paper-inputs.json').read_text())['cases']:
 sets[case['function']].add(tuple(int(x,16) for x in case['bits']))
sets['expf'].add((0xc2890f89,0))
sets['atan2f'].add((0x803c1252,0x0686decf))
sets['atan2f'].add((0xffbd5d56,0x7fe6dcbc))
sets['powf'].add((0x56363937,0xc052da19))
special=[0,1,0x3fffff,0x7fffff,0x800000,0x800001,0x3f000000,0x3f700000,0x3f7fffff,0x3f800000,0x3f800001,0x3f880000,0x40000000,0x7f7fffff,0x7f800000,0x7f800001,0x7fc00001,0x7fffffff]
special += [x|0x80000000 for x in special]
for a in special:
 sets['expf'].add((a,0))
 for b in special:
  for fn in ('atan2f','powf'):sets[fn].add((a,b))
# Dense windows around 1, the normal/subnormal transition, and exp cutoffs.
for center in [0x3f800000,0x00800000,0x42b17218,0xc2cff1b4,0xc2ce8ed0]:
 for a in range(center-256,center+257):
  sets['expf'].add((a,0));sets['expf'].add((a|0x80000000,0))
  for y in [-151,-150,-149,-127,-126,-2,-1,-.5,0,.5,1,1.5,2,3,127,128,149,150]:
   sets['powf'].add((a,bits(y)));sets['powf'].add((a|0x80000000,bits(y)))
# Atan exponent gap transitions, both signs, with subnormal mantissas.
for a in [1,2,3,0x12345,0x3c1252,0x3fffff,0x7fffff,0x800000]:
 for e in range(1,32):
  for mant in [0,1,0x6decf,0x7fffff]:
   for s in [0,0x80000000]:
    for t in [0,0x80000000]:
     b=(e<<23)|mant|t;sets['atan2f'].add((a|s,b));sets['atan2f'].add((b,a|s))
for fn,cases in sets.items():
 with (out/(fn+'.txt')).open('w') as f:
  for a,b in sorted(cases):f.write(f'{a:08x} {b:08x}\n')
 print(fn,len(cases))
