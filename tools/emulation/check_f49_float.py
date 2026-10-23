#!/usr/bin/env python3
"""Compare portable SSE helpers with literal SSE via macOS Rosetta, not Windows."""
import json,os,struct,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/F49-dblur-nonfinite-pf32'
CPP=r'''
#include "x86_float.h"
#include <cstdio>
int main() {
 unsigned v[3];
 while (std::fread(v,4,3,stdin)==3) {
  float a,b;std::memcpy(&a,v+1,4);std::memcpy(&b,v+2,4);
#ifdef SSE
  switch(v[0]) {
   case 0:asm("addss %1,%0":"+x"(a):"x"(b));break;
   case 1:asm("subss %1,%0":"+x"(a):"x"(b));break;
   case 2:asm("mulss %1,%0":"+x"(a):"x"(b));break;
   case 3:asm("divss %1,%0":"+x"(a):"x"(b));break;
   case 4:asm("minss %1,%0":"+x"(a):"x"(b));break;
   case 5:asm("maxss %1,%0":"+x"(a):"x"(b));break;
  }
#else
  using namespace olm::x86_float;
  switch(v[0]) {
   case 0:a=sse_add(a,b);break;case 1:a=sse_sub(a,b);break;
   case 2:a=sse_mul(a,b);break;case 3:a=sse_div(a,b);break;
   case 4:a=sse_min(a,b);break;case 5:a=sse_max(a,b);break;
  }
#endif
  std::fwrite(&a,4,1,stdout);
 }
}
'''
def main():
 S.mkdir(parents=True,exist_ok=True);os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
 values=[0,0x80000000,0x3f800000,0xbf800000,1,0x80000001,0x7f7fffff,0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7fc12345,0xffc12346,0x7f812345,0xff812346]
 payload=b''.join(struct.pack('<III',op,a,b) for op in range(6) for a in values for b in values)
 commands=[];results=[]
 with tempfile.TemporaryDirectory(prefix='float_',dir=S) as tmp:
  d=Path(tmp);src=d/'test.cpp';src.write_text(CPP)
  for arch,flags in [('x86_64',['-DSSE']),('arm64',[]),('arm64',['-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
   binary=d/f'probe{len(results)}'
   cmd=['clang++','-std=c++17','-arch',arch,'-O2','-fno-fast-math','-ffp-contract=off','-I',str(ROOT/'core'),str(src),'-o',str(binary),*flags];commands.append(cmd);subprocess.run(cmd,check=True,capture_output=True)
   cmd=['/usr/bin/arch','-'+arch,str(binary)];commands.append(cmd)
   results.append(subprocess.run(cmd,input=payload,check=True,capture_output=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')).stdout)
 rows=[]
 for mode,result in zip(['arm64','sanitized'],results[1:]):
  mismatches=[]
  for i in range(len(payload)//12):
   if result[i*4:i*4+4]!=results[0][i*4:i*4+4]:mismatches.append(dict(input=payload[i*12:i*12+12].hex(),expected=results[0][i*4:i*4+4].hex(),actual=result[i*4:i*4+4].hex()))
  rows.append(dict(mode=mode,count=len(payload)//12,mismatches=mismatches))
 report=dict(scope='macOS Rosetta literal SSE versus arm64 helpers',results=rows,commands=commands)
 (S/'float.json').write_text(json.dumps(report,indent=2)+'\n');print([(r['mode'],r['count'],len(r['mismatches'])) for r in rows]);assert not any(r['mismatches'] for r in rows)
if __name__=='__main__':main()
