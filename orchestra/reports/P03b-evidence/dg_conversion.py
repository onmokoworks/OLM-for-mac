"""Original cvConvertScale boundary values and reached conversion instructions."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'tools/emulation'))
import capstone,numpy as np
from unicorn import UC_HOOK_CODE
from aex_loader import AexLoader
from cv_bridge import build_ipl,read_ipl
from windows_runtime import WindowsOpenCVRuntime
p=Path('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex')
ld=AexLoader(str(p),verbose=False,fast=True)
ld.register_libm_impls(max_threads=1);WindowsOpenCVRuntime(ld).install();ld.enable_crt_initializer_imports()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);seen=set();instructions={}
def trace(uc,address,size,user):
 if address in seen:return
 seen.add(address)
 for i in md.disasm(bytes(uc.mem_read(address,size)),address):
  if i.mnemonic.startswith('cvt'):instructions[f'{address:x}']=i.mnemonic+' '+i.op_str
hook=ld.uc.hook_add(UC_HOOK_CODE,trace)
words=[0,0x80000000,0x3bc0c0bf,0x3bc0c0c0,0x3bc0c0c1,0x3f000000,0x3f800000,0x7f800000,0xff800000,0x7fc12345,0xff812346,0x4b00807f,0x4b008080,0x4b008081,0x7f7fffff,0xff7fffff,1]
rows=[]
for width in (1,7,17):
 for start in range(0,len(words),width):
  bits=words[start:start+width]
  src=np.array(bits,dtype='<u4').view('<f4').reshape(1,-1)
  ip=build_ipl(ld,src);op=build_ipl(ld,np.zeros(src.shape,dtype=np.uint8))
  ld.call_function(0x18117c580,[ip,op],float_args={2:(255.,'d'),3:(0.,'d')})
  actual=read_ipl(ld,op).reshape(-1).tolist()
  with np.errstate(over='ignore',invalid='ignore'):
   scaled=src.reshape(-1)*np.float32(255)
  expected=[bool(x>=1.5 and x<2147483648.) for x in scaled]
  assert [x>1 for x in actual]==expected
  rows.append(dict(width=len(bits),input=[f'{x:08x}' for x in bits],converted=actual,owned=expected))
ld.uc.hook_del(hook)
print(json.dumps(dict(rows=rows,reached_conversion_instructions=instructions),indent=2))
