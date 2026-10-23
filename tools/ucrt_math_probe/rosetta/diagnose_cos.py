#!/usr/bin/env python3
"""No-reduction cosine witness: UCRT SSE polynomial vs FMA/AMD quadratic."""
import argparse,json,pathlib,struct,subprocess
import gmpy2 as g
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();s=a.state.resolve()
x=struct.unpack('<f',struct.pack('<I',0x3a544395))[0];q=x*x
c=[float.fromhex(v) for v in ['0x1.5555555555555p-5','-0x1.6c16c16c16c16p-10','0x1.a01a01a01a019p-16','-0x1.27e4fb7789f5cp-22']]
u=(1+(-0.5*q))+(((c[3]*q+c[2])*(q*q)+(c[1]*q+c[0]))*(q*q))
with g.context(precision=53):d=float(g.fma(g.mpfr(-0.5*x),g.mpfr(x),g.mpfr(1)))
model=[f'{struct.unpack("<I",struct.pack("<f",v))[0]:08x}' for v in [u,d,d]]
dll=str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll')
cmds=[[str(s/'oracle'),dll,str(mode),'cosf'] for mode in (0,1)]+[[str(s/'apple'),'cosf',str(s/'amd/amd-off.dylib')]]
out=[subprocess.run(cmd,input='3a544395 0\n',capture_output=True,text=True,check=True).stdout.strip() for cmd in cmds]
assert out==model and out[0]!=out[1]
a.out.write_text(json.dumps(dict(a='3a544395',ucrt0=out[0],ucrt1=out[1],amd_off=out[2],diagnostic_matches_all=True,region='no reduction: UCRT0 full cosine polynomial; UCRT1/AMD 1-x*x/2'),indent=2)+'\n')
print('PASS: cosine small-input diagnostic reproduces all three outputs')
