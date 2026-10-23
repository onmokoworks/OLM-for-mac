#!/usr/bin/env python3
"""Two no-reduction witnesses isolate coefficient/polynomial differences."""
import argparse,json,pathlib,struct,subprocess
import gmpy2 as g
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();s=a.state.resolve()
def f(h):return struct.unpack('<f',struct.pack('<I',int(h,16)))[0]
def bits(x):return f'{struct.unpack("<I",struct.pack("<f",x))[0]:08x}'
def fma(x,y,z):
 with g.context(precision=53):return float(g.fma(g.mpfr(x),g.mpfr(y),g.mpfr(z)))
rows=[]
for h in ['3a1285ff','bee5220e']:
 x=f(h);q=x*x;r=x*q
 if abs(x)<2**-7:
  u=x-r*(1/6);d=fma(-r,f(bits(1/6)),x);region='small cubic: double 1/6 vs float32 1/6'
 else:
  c=[float.fromhex(v) for v in ['-0x1.5555555555555p-3','0x1.1111111111111p-7','-0x1.a01a01a01a01ap-13','0x1.71de3a556c734p-19']]
  u=x+r*((c[3]*q+c[2])*(q*q)+(c[1]*q+c[0]))
  c=[float.fromhex(v) for v in ['-0x1.5555529be884fp-3','0x1.110c219cff89cp-7','-0x1.9ac6d7159dfebp-13']]
  d=fma(r,(c[0]+c[1]*q)+(q*q)*c[2],x);region='direct sine: degree 9 vs degree 7'
 cmds=[[str(s/'oracle'),str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'),'0','sinf'],[str(s/'apple'),'sinf',str(s/'amd/amd-off.dylib')]]
 out=[subprocess.run(cmd,input=f'{h} 0\n',capture_output=True,text=True,check=True).stdout.strip() for cmd in cmds]
 assert out==[bits(u),bits(d)] and out[0]!=out[1]
 rows.append(dict(a=h,region=region,ucrt0=out[0],amd_off=out[1],diagnostic_matches_both=True))
a.out.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
