"""Read-only instruction/operand traces of original radius-two IPP filtering."""
import gzip,json,os,sys,struct
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals'
os.environ['TMPDIR']=str(S);sys.path.insert(0,str(R/'tools/emulation'))
import numpy as np
from aex_loader import AexLoader
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from unicorn import UC_HOOK_CODE
import unicorn.x86_const as xc
E=R/'orchestra/reports/N03-evidence'
for name,w,h in [('witness',6,17),('vector',17,9)]:
 if name=='witness':
  t=json.load(gzip.open(E/'e3f919696d05b1dee9a48046-trace.json.gz'))
  data=bytes.fromhex(next(v['before']['hex'] for v in t['memory_witnesses'] if v['watch_id']=='input'))
 else:data=np.random.default_rng(26026).random((h,w),dtype=np.float32).tobytes()
 ld=AexLoader('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex',verbose=False,fast=True)
 src=ld.bump_alloc(len(data)+128,align=64)+64;ld.write_bytes(src,data)
 dst=ld.bump_alloc(len(data)+128,align=64)+64
 spec=ld.bump_alloc(1024*1024,align=64);scratch=ld.bump_alloc(8*1024*1024,align=64)
 assert ld.call_function(0x18000c280,[100,w|(h<<32),2,13,1,2,0x3f800000,0x3f800000,spec])['rax']==0
 cs=Cs(CS_ARCH_X86,CS_MODE_64);instructions={}
 for lo,hi in [(0x1806b7240,0x1806b7d40),(0x1806bd9a0,0x1806be1e0)]:
  for i in cs.disasm(ld.read_bytes(lo,hi-lo),lo):instructions[i.address]=(i.mnemonic,i.op_str)
 events=[];counts={};sums=[];tile={};stream=gzip.open(E/f'{name}-all-arithmetic.jsonl.gz','wt')
 def hook(uc,address,size,user):
  if address in (0x1806b7240,0x1806bd9a0):
   roi=struct.unpack("<Q",uc.mem_read(uc.reg_read(xc.UC_X86_REG_RSP)+0x28,8))[0]
   tile.update(base=uc.reg_read(xc.UC_X86_REG_R8),stride=uc.reg_read(xc.UC_X86_REG_R9),width=roi&0xffffffff)
  ins=instructions.get(address)
  if ins is None:return
  mnemonic,operands=ins
  if mnemonic not in ('mulps','addps','subps','divps','mulss','addss','subss','divss'):return
  counts[address]=counts.get(address,0)+1
  regs={f'xmm{i}':uc.reg_read(getattr(xc,f'UC_X86_REG_XMM{i}')).to_bytes(16,'little').hex() for i in range(16)}
  stream.write(json.dumps(dict(pc=hex(address),occurrence=counts[address],mnemonic=mnemonic,operands=operands,xmm=regs))+'\n')
  if counts[address]==1:events.append(dict(pc=hex(address),mnemonic=mnemonic,operands=operands,xmm=regs))
  if mnemonic.startswith('div'):
   target=uc.reg_read(xc.UC_X86_REG_RSI) if mnemonic=='divps' else uc.reg_read(xc.UC_X86_REG_R12)+uc.reg_read(xc.UC_X86_REG_RBP)
   column=((target-tile['base'])%tile['stride'])//4
   sums.append(dict(pc=hex(address),valid_lanes=min(4 if mnemonic=='divps' else 1,tile['width']-column),xmm=regs))
 for lo,hi in [(0x1806b7240,0x1806b7d3f),(0x1806bd9a0,0x1806be1df)]:ld.uc.hook_add(UC_HOOK_CODE,hook,begin=lo,end=hi)
 result=ld.call_function(0x18000c2f0,[src,w*4,dst,w*4,w|(h<<32),1,0,spec,scratch],max_instructions=200000000)
 assert result['rax']==0
 stream.close()
 out=dict(w=w,h=h,input_hex=data.hex(),output_hex=ld.read_bytes(dst,len(data)).hex(),events=events,sums=sums,instructions=result['instructions'])
 with gzip.open(E/f'{name}-leaf.json.gz','wt') as f:json.dump(out,f)
 print(name,'events',len(events),'divisions',len(sums),'instructions',result['instructions'])
