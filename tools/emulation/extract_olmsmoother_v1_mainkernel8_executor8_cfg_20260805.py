#!/usr/bin/env python3
"""Extract actual CFGs for the remaining PF8 interpolation stages."""
import hashlib,json
from pathlib import Path
import capstone,pefile
ROOT=Path(__file__).resolve().parents[2];AEX=ROOT/'plugins_2025/OLMSmoother.aex'
FUNCS=(('mainkernel8',0x180005570,0x180005edc),('executor8',0x180006270,0x18000656a))
def extract(pe,name,start,end):
 base=pe.OPTIONAL_HEADER.ImageBase;code=pe.get_memory_mapped_image()[start-base:end-base];cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);ins=list(cs.disasm(code,start));imap={i.address:i for i in ins};leaders={start};edges=[]
 for i in ins:
  nxt=i.address+i.size;m=i.mnemonic
  if m.startswith('j'):
   target=int(i.op_str,16);leaders.add(target)
   if m=='jmp':edges.append((i.address,target,'jump'))
   else:leaders.add(nxt);edges.extend(((i.address,target,'branch_true'),(i.address,nxt,'branch_false')))
 blocks=[]
 for a in sorted(x for x in leaders if start<=x<end):
  seq=[];p=a
  while p in imap:
   i=imap[p];seq.append({'address':hex(p),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str});p+=i.size
   if i.mnemonic.startswith('j') or i.mnemonic=='ret' or p in leaders:break
  blocks.append({'start':hex(a),'end_exclusive':hex(p),'instructions':seq})
 report={'schema_version':1,'status':'cfg_extracted','function':name,'aex_sha256':hashlib.sha256(AEX.read_bytes()).hexdigest(),'range':[hex(start),hex(end)],'instruction_count':len(ins),'block_count':len(blocks),'blocks':blocks,'edges':[{'from_instruction':hex(a),'to_block':hex(b),'kind':k} for a,b,k in edges]}
 out=ROOT/f'refs/conformance/olmsmoother_v1_{name}_cfg_20260805.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');return {'function':name,'instructions':len(ins),'blocks':len(blocks),'edges':len(edges),'last':hex(ins[-1].address)}
def main():
 pe=pefile.PE(str(AEX));print(json.dumps([extract(pe,*f) for f in FUNCS],indent=2))
if __name__=='__main__':main()
