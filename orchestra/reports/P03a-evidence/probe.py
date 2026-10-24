"""Direct original AEX stage probe; no OpenCV operation detours."""
import sys,json,zlib,base64,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[3]; S=R/'orchestra/state/P03a-distancegradation-pf32-downsample-ulp'
sys.path.insert(0,str(R/'tools/emulation'))
import numpy as np
from aex_loader import AexLoader
from test_dg_fieldgen_p1b import setup_tls
import cv_bridge as cvb
M=R.parent.parent if R.parent.name=="worktrees" else R
j=json.loads((R/'tests/fuzz_corpus/olmdistancegradation/T15b-odd-even-realistic/seed2027-case118.json').read_text())
p=np.frombuffer(zlib.decompress(base64.b64decode(j['pixels_zlib_base64'])),dtype='<f4').reshape(8,12,4)
mask=(p[:,:,0]*np.float32(255)>=np.float32(1.5)).astype('uint8')
mask.tofile(S/'mask.bin')
aex=M/'plugins_2025/DistanceGradation.aex'
if not aex.exists():
 from olm_assets import resolve_asset
 aex=resolve_asset(aex)
from windows_runtime import WindowsOpenCVRuntime
ld=AexLoader(str(aex),verbose=False,fast=True);ld.register_libm_impls(max_threads=1)
WindowsOpenCVRuntime(ld).install()
from collections import Counter
hits=Counter()
asm=M/'disasm/DistanceGradation.aex.asm.txt'
for line in asm.open():
 if any(op in line for op in (' SQRTPS ', ' RSQRTPS ', ' SQRTSS ', ' RSQRTSS ')):
  addr=int(line.split()[0],16)
  def hook(loader,address,size): hits[hex(address)]+=1
  ld.add_code_hook(addr,hook)
from unicorn.x86_const import UC_X86_REG_XMM0,UC_X86_REG_XMM4,UC_X86_REG_R8,UC_X86_REG_RCX,UC_X86_REG_RDX
sqrt_calls=[]; reciprocal={}
def entry(loader,address,size):
 sqrt_calls.append([loader.uc.reg_read(r) for r in (UC_X86_REG_R8,UC_X86_REG_RCX,UC_X86_REG_RDX)])
def reciprocal_hook(loader,address,size):
 a=loader.uc.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')
 b=loader.uc.reg_read(UC_X86_REG_XMM4).to_bytes(16,'little')
 for i in range(0,16,4):reciprocal[a[i:i+4].hex()]=b[i:i+4].hex()
ld.add_code_hook(0x181449920,entry)
ld.add_code_hook(0x181449a22,reciprocal_hook)
src=cvb.build_ipl(ld,mask,align_step=4)
expanded=cvb.build_ipl(ld,np.zeros((64,96),dtype='uint8'),align_step=4)
dist=cvb.build_ipl(ld,np.zeros((64,96),dtype='float32'),align_step=16)
small=cvb.build_ipl(ld,np.zeros((8,12),dtype='float32'),align_step=16)
rows=[]
for name,addr,args,obj in [('expanded',0x1812aef70,[src,expanded,0],expanded),('distance',0x1812b15a0,[expanded,dist,2,0,0,0,0],dist),('resized',0x1812aef70,[dist,small,1],small)]:
 print('starting',name,flush=True)
 regs=ld.call_function(addr,int_args=args,max_instructions=100000000)
 a=cvb.read_ipl(ld,obj).copy();a.tofile(S/(name+'.bin'))
 rows.append(dict(stage=name,instructions=int(regs['instructions']),sha256=hashlib.sha256(a.tobytes()).hexdigest()))
 print(rows[-1],flush=True)
(S/'stages.json').write_text(json.dumps(rows,indent=2))

print('sqrt hits',dict(hits),flush=True)

(S/'sqrt-trace.json').write_text(json.dumps(dict(calls=sqrt_calls,reciprocal=reciprocal),indent=2))
