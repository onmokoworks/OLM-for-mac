#!/usr/bin/env python3
"""Isolated-process fallback: preserve abort evidence and continue the corpus.
Also identify the first import reached by F27's independent non-FMA emulator.
"""
import argparse,json,pathlib,struct,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from probe import Probe,DEFAULT_DLL
import unicorn
from unicorn import x86_const as x
CASES={
 'expf':[(0,0),(0x42b00000,0),(0x42c80000,0),(0xc2c80000,0),(0x7f800000,0),(0x7fc00001,0)],
 'atan2f':[(0,0),(1,0x7f7fffff),(0x7f800000,0x7f800000),(0x7fc00001,0x3f800000)],
 'sinf':[(0,0),(0x7f7fffff,0),(0x7f800000,0),(0x7fc00001,0),(0x7f800001,0)],
 'cosf':[(0,0),(0x7f7fffff,0),(0x7f800000,0),(0x7fc00001,0),(0x7f800001,0)],
 'powf':[(0x3f800000,0x40000000),(0xbf800000,0x3f000000),(0,0xbf800000),(0x40000000,0x43000000),(0x7fc00001,0x3f800000)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--oracle',required=True);ap.add_argument('--out',required=True,type=pathlib.Path);args=ap.parse_args();rows=[]
 for fn,cases in CASES.items():
  for a,b in cases:
   row=dict(function=fn,a=f'{a:08x}',b=f'{b:08x}',native=[])
   for mode in (0,1):
    r=subprocess.run([args.oracle,str(DEFAULT_DLL),str(mode),fn],input=f'{a:08x} {b:08x}\n',text=True,capture_output=True)
    row['native'].append(dict(mode=mode,exit=r.returncode,stdout=r.stdout.strip(),stderr=r.stderr.strip()))
   p=Probe();p.set_mode(0);traps={};observed=[]
   # Bind emulator IATs to distinct unmapped-call sentinels, then trap before
   # any stub instruction executes. No host math/OS implementation is supplied.
   trap=0x72000000;p.uc.mem_map(trap,0x10000)
   for i,(slot,name) in enumerate(p.imports.items()):
    addr=trap+i*16;traps[addr]=name;p.uc.mem_write(slot,struct.pack('<Q',addr))
   def hook(uc,addr,size,data):
    if addr in traps:observed.append(traps[addr]);uc.emu_stop()
   p.uc.hook_add(unicorn.UC_HOOK_CODE,hook,begin=trap,end=trap+0xffff)
   try:row['unicorn_result']=f'{p.call(fn,(a,b)):08x}'
   except RuntimeError as e:row['unicorn_failure']=str(e)
   row['unicorn_imports']=observed;rows.append(row)
 args.out.write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps(dict(cases=len(rows),native_calls=2*len(rows),native_aborts=sum(n['exit']==86 for r in rows for n in r['native']),unicorn_import_cases=sum(bool(r['unicorn_imports']) for r in rows))))
if __name__=='__main__':main()
