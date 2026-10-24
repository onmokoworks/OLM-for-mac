#!/usr/bin/env python3
"""Extract address-bounded original instructions; no claim from offset matches alone."""
import hashlib,json,re
from pathlib import Path
from run import main_checkout
from measure_F52c import S
RANGES={
 'ColorKeep': [('180001000','18000113f')],
 'DistanceGradation':[('18117176d','1811717bb'),('181171b90','181171be8')],
 'OLMKiraKira':[('18114cc88','18114cd32')],
 'OLMRadialBlur':[('180006dc8','180006e40')],
 'OLMToonDilate':[('1801a5ace','1801a5b2d')],
 'OLMSmoother2':[('180016870','1800168be')],
 'OLMSmoother':[('180001209','18000128b')],
 'OLMBlur':[('1800022ee','180002315')],
}
def main():
 result={}
 for name,ranges in RANGES.items():
  path=main_checkout()/'disasm'/(name+'.aex.asm.txt');sites=[];snippets=[];function=''
  with path.open() as f:
   for n,line in enumerate(f,1):
    if line.startswith('; ==='):function=line.strip()
    if re.search(r'\[(?!RSP|RBP)[A-Z0-9]+ \+ 0x11c\]',line):sites.append(dict(line=n,function=function,text=line.strip()))
    if any(lo<=line[:9]<=hi for lo,hi in ranges) and re.match('[0-9a-f]{9} ',line):snippets.append(dict(line=n,text=line.strip()))
  with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  result[name]=dict(path=str(path),sha256=digest,nonstack_0x11c_sites=sites,snippets=snippets)
 S.mkdir(parents=True,exist_ok=True);(S/'disassembly.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Extracted',len(result),'original disassemblies; offset scans are not proofs of caller semantics')
if __name__=='__main__':main()
