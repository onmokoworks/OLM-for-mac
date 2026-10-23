#!/usr/bin/env python3
"""Read-only independent Unicorn checks for newly observed powf NaN branches."""
import json,pathlib,struct,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/ucrt_math_probe'))
from probe import Probe
cases=[(0x3f800000,0x7f800001),(0x3f800000,0xffbfffff),
       (0xff800001,0),(0xffbfffff,0x80000000),
       (0xffc00000,0x7f800001),(0x7fc00000,0x7f800001),
       (0x7fc00001,0xff800001),(0xffc00000,0x7fffffff)]
raw=subprocess.check_output([str(root/'orchestra/state/F28-ucrtmath-lib-amd/build/native'),'powf','file','0'],input=''.join(f'{a:08x} {b:08x}\n' for a,b in cases).encode())
rows=[]
for i,(a,b) in enumerate(cases):
 p=Probe();p.set_mode(0);row={'a':f'{a:08x}','b':f'{b:08x}'}
 candidate=struct.unpack_from('<IIII',raw,i*16)[2]
 row['candidate']=f'{candidate:08x}'
 try:
  value=p.call('powf',(a,b));row.update(unicorn=f'{value:08x}',match=value==candidate)
 except RuntimeError as e:
  d=json.loads(str(e));row['unicorn_failure']={'error':d['error'],'rva':d['rva']}
 rows.append(row)
print(json.dumps(rows,indent=2))
sys.exit(1 if any(r.get('match') is False for r in rows) else 0)
