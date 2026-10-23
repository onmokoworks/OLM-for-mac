#!/usr/bin/env python3
"""Deterministic, streamed dense pow corpus; libm chooses inputs, never answers.
Usage: python3 ucrtmath/ms/pow_targets.py OUTPUT_DIRECTORY
"""
import collections, json, math, struct, sys
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
counts=collections.Counter()
def word(x):return struct.unpack('<Q',struct.pack('<d',x))[0]
def val(u):return struct.unpack('<d',struct.pack('<Q',u))[0]
with (out/'targets.txt').open('w') as f:
 def emit(family,a,b):
  f.write(f'{a:016x} {b:016x}\n');counts[family]+=1
 # All distinct finite first witnesses retained in F43 results.json.
 for a,b in [(0x4af491eedc5e5b0a,0xc0173ef560c4bc83),(0x17db023316630462,0x3f89997eeda3c17f),(0x300422d9a042d15f,0x3efb46f239a9a9c7)]:emit('F43',a,b)
 # Both signs, both NaN classes/payload extremes, signed zero, subnormals,
 # unit/tiny/large exponent shortcuts, and integer parity transitions.
 special=[0,1,0xfffffffffffff,0x10000000000000,word(1.),word(.5),word(2.),0x7fefffffffffffff,0x7ff0000000000000,0x7ff0000000000001,0x7ff7ffffffffffff,0x7ff8000000000001,0x7fffffffffffffff]
 for center in [2.**-65,2.**63,2.**52,2.**53,1.,3.]:special.extend(word(center)+d for d in [-1,0,1])
 special=sorted(set(special+[x|(1<<63) for x in special]))
 for a in special:
  for b in special:emit('special',a,b)
 # 8193 consecutive bases at one, all half integers in [-8,8], plus
 # adjacent exponents and near-one amplification by very large exponents.
 exps=[word(n*.5) for n in range(-16,17)]
 exps.extend(word(sign*2.**k) for k in [-66,-65,-64,20,40,52,62,63] for sign in [-1,1])
 for dx in range(-4096,4097):
  for b in exps:
   for dy in [-1,0,1]:
    bb=(b+dy)&((1<<64)-1)
    emit('near_one',word(1.)+dx,bb)
 # Dense integer and half integer exponents, independent range bases and
 # negative bases to exercise integer-domain and odd-sign decisions.
 for n in range(-64,65):
  center=word(n*.5)
  for d in range(-32,33):
   b=(center+d)&((1<<64)-1)
   for x in [2.**-1022,2.**-100,0.125,0.5,0.7,1.1,1.5,2.,3.,4.,2.**100,2.**1023]:
    for sign in [-1,1]:emit('integer_half',word(sign*x),b)
 # Output exponent boundaries: underflow halfway/first subnormal, min
 # normal, near overflow; scan y ulps for diverse x including near one.
 xs=[val(word(1.)+d) for d in [-4096,-32,-1,1,32,4096]]
 xs += [2.**k for k in [-1022,-100,-10,-1,1,2,10,100,1023]]+[.7,1.1,1.5,3.,4.]
 for x in xs:
  for boundary in [-1075.,-1074.,-1022.,1024.]:
   center=word(boundary/math.log2(x))
   for d in range(-2048,2049):emit('result_boundary',word(x),center+d)
 # Log table cell edges across exponent magnitudes, including normalization
 # and subnormal inputs; exponent choices include all plugin half integers.
 for k in [-1022,-100,-1,0,1,100,1023]:
  for j in range(129):
   x=(0x3fe6955500000000+(j<<45)+(k<<52))&((1<<64)-1)
   for d in range(-8,9):
    a=(x+d)&((1<<64)-1)
    if a<0x7ff0000000000000:
     for n in range(-16,17):emit('log_table_boundary',a,word(n*.5))
(out/'targets-counts.json').write_text(json.dumps(dict(counts,total=sum(counts.values())),indent=2)+'\n')
print(json.dumps(dict(counts,total=sum(counts.values()))))
