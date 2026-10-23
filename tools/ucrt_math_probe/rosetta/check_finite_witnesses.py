#!/usr/bin/env python3
"""MPFR references for newly exposed finite expf/atan2f boundaries."""
import argparse,json,pathlib,struct,subprocess
import gmpy2 as g
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
s=a.state.resolve();dll=str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll');g.get_context().precision=200
rows=[]
for fn,x,y in [('expf','c2890f89','00000000'),('atan2f','803c1252','0686decf')]:
 vals=[g.mpfr(struct.unpack('<f',struct.pack('<I',int(t,16)))[0]) for t in (x,y)]
 ref=g.exp(vals[0]) if fn=='expf' else g.atan2(*vals)
 with g.context(g.ieee(32)):rounded=+ref
 bits=f'{struct.unpack("<I",struct.pack("<f",float(rounded)))[0]:08x}'
 cmds=[[str(s/'oracle'),dll,str(mode),fn] for mode in (0,1)]+[[str(s/'apple'),fn]]+[[str(s/'apple'),fn,str(s/'amd'/f'amd-{mode}.dylib')] for mode in ['off','fma']]
 out={name:subprocess.run(cmd,input=f'{x} {y}\n',capture_output=True,text=True,check=True).stdout.strip() for name,cmd in zip(['ucrt0','ucrt1','apple','amd-off','amd-fma'],cmds)}
 rows.append(dict(function=fn,a=x,b=y,mpfr_binary32=bits,outputs=out))
a.out.write_text(json.dumps(dict(mpfr=g.mpfr_version(),precision=200,cases=rows),indent=2)+'\n');print(json.dumps(rows))
