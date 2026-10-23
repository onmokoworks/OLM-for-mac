#!/usr/bin/env python3
"""MPFR/IEEE class qualification, plus recorded (not IEEE-mandated) NaN bits."""
import argparse,json,pathlib,subprocess
import gmpy2 as g
p=argparse.ArgumentParser();p.add_argument('--oracle',required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
dll=pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
g.get_context().precision=200
cases=[('expf','42c80000','00000000',g.exp(g.mpfr(100))),
 ('sinf','7f800000','00000000',g.sin(g.mpfr('inf'))),
 ('cosf','7f800000','00000000',g.cos(g.mpfr('inf'))),
 ('powf','bf800000','3f000000',g.mpfr(-1)**g.mpfr('0.5')),
 ('powf','00000000','bf800000',g.mpfr(0)**g.mpfr(-1))]
rows=[]
for fn,x,y,ref in cases:
 for mode in (0,1):
  r=subprocess.run([a.oracle,str(dll),str(mode),fn],input=f'{x} {y}\n',text=True,capture_output=True,check=True)
  bits=int(r.stdout,16)
  if g.is_nan(ref):
   assert bits&0x7f800000==0x7f800000 and bits&0x7fffff
   expected='NaN (IEEE does not prescribe sign/payload)'
  else:
   assert ref>=(g.mpfr(2)**128-g.mpfr(2)**103) and bits==0x7f800000
   expected='+infinity after binary32 round-to-nearest overflow or pole'
  rows.append(dict(function=fn,a=x,b=y,mode=mode,expected=expected,bits=f'{bits:08x}',sign=bits>>31,payload=f'{bits&0x7fffff:06x}',stub_hits=r.stderr.strip()))
a.out.write_text(json.dumps(dict(mpfr=g.mpfr_version(),precision=200,passed=len(rows),cases=rows),indent=2)+'\n')
print(f'PASS: {len(rows)} previously aborting mode/input calls satisfy MPFR/IEEE classes')
