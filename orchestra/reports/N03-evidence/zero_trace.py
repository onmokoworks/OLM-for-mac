"""Capture the zero-field nightly witnesses' scalar kernels and final sums.

The public F54b captures establish zero input for these cases. AEX leaf replay
uses the same radius and replicated border; no arithmetic detours are installed.
The full spatial table is streamed to gzip, including zero taps.
"""
import argparse,gzip,json,math,os,struct,sys,tempfile,time,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
os.environ['TMPDIR']=str(S);sys.path[:0]=[str(R/'tools/emulation'),str(R/'tools/fuzz')]
from aex_loader import AexLoader,IMPORT_STUB_BASE,RETURN_TRAMPOLINE,CALLBACK_STUB_BASE,CALLBACK_STUB_SIZE
from unicorn import Uc
from unicorn import UC_HOOK_CODE
import unicorn.x86_const as xc
from adapters.olmdistancegradation import Adapter,SOURCE,FIELDGEN
from run import main_checkout
rows=[]
for radius in (1,2740):
 # The shared loader's fast hook has reversed bounds after its trampoline
 # relocation (0x90000000 > 0x82100000), causing an all-instruction hook.
 # Narrow only that diagnostic callback on this instance; no guest bytes change.
 hooks=[];original_hook=Uc.hook_add
 def track_hook(uc,kind,callback,*args,**kwargs):
  handle=original_hook(uc,kind,callback,*args,**kwargs)
  if getattr(callback,'__name__','')=='_on_code':hooks.append((uc,handle,callback))
  return handle
 Uc.hook_add=track_hook
 try:ld=AexLoader('/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex',verbose=False,fast=True)
 finally:Uc.hook_add=original_hook
 for uc,handle,callback in hooks:
  uc.hook_del(handle)
  uc.hook_add(UC_HOOK_CODE,callback,begin=IMPORT_STUB_BASE,end=RETURN_TRAMPOLINE)

 src=ld.bump_alloc(128,align=64)+64;ld.write_bytes(src,b'\0'*4);dst=ld.bump_alloc(128,align=64)+64
 spec=ld.bump_alloc(max(1048576,(2*radius+1)**2*8),align=64)
 scratch=ld.bump_alloc(max(8388608,(2*radius+9)**2*8),align=64)
 result=ld.call_function(0x18000c280,[100,1|(1<<32),radius,13,1,2,0x3f800000,0x3f800000,spec],max_instructions=4000000000);assert result['rax']==0 and ld.uc.reg_read(xc.UC_X86_REG_RIP)==RETURN_TRAMPOLINE
 row=dict(radius=radius,init_host_callback_count=result['instructions'])
 entry=0x1806bd600 if radius==1 else 0x1806be1e0
 div=0x1806bd8aa if radius==1 else 0x1806be45d
 def at_entry(uc,addr,size,user):
  ptr=struct.unpack('<Q',uc.mem_read(uc.reg_read(xc.UC_X86_REG_RSP)+0x38,8))[0]
  count=2 if radius==1 else 1+sum(2*math.isqrt(radius*radius-y*y)+1 for y in range(-radius,radius+1))
  nonzero=0;digest=hashlib.sha256()
  with gzip.open(E/f'zero-radius{radius}-kernel.raw.gz','wb') as f:
   for offset in range(0,count*4,65536):
    block=bytes(uc.mem_read(ptr+offset,min(65536,count*4-offset)));f.write(block);digest.update(block)
    nonzero+=sum(v!=0 for v, in struct.iter_unpack('<f',block))
  row.update(kernel_words=count,kernel_nonzero_words=nonzero,kernel_sha256=digest.hexdigest())
 def at_div(uc,addr,size,user):
  regs=(13,14) if radius==1 else (6,8)
  row['sums_hex']=[(uc.reg_read(getattr(xc,f'UC_X86_REG_XMM{i}'))&0xffffffff).to_bytes(4,'little').hex() for i in regs]
 row['range_weight_samples']=[]
 def range_hook(uc,addr,size,holder):
  row['range_weight_samples'].append(dict(pc=hex(addr),weight_hex=(uc.reg_read(xc.UC_X86_REG_XMM0)&0xffffffff).to_bytes(4,'little').hex()))
  uc.hook_del(holder[0])
 for pc in ([0x1806bd7d0,0x1806bd7f8,0x1806bd816,0x1806bd83e] if radius==1 else [0x1806be3d8]):
  holder=[];holder.append(ld.uc.hook_add(UC_HOOK_CODE,range_hook,user_data=holder,begin=pc,end=pc))
 ld.uc.hook_add(UC_HOOK_CODE,at_entry,begin=entry,end=entry)
 ld.uc.hook_add(UC_HOOK_CODE,at_div,begin=div,end=div)
 result=ld.call_function(0x18000c2f0,[src,4,dst,4,1|(1<<32),1,0,spec,scratch],max_instructions=4000000000);assert result['rax']==0 and ld.uc.reg_read(xc.UC_X86_REG_RIP)==RETURN_TRAMPOLINE
 row.update(output_hex=ld.read_bytes(dst,4).hex(),filter_host_callback_count=result['instructions']);rows.append(row);print(row,flush=True)
 del ld
args=argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker')
a=Adapter(args);deadline=time.monotonic()+600
with tempfile.TemporaryDirectory(dir=S) as td:
 hd=Path(td);a.binary,_=a.build(hd,deadline);source=SOURCE.read_text()
 source=source.replace('mat[(size_t)y*w+x] = sum / weight_sum;', 'fwrite(&sum,4,1,stderr);fwrite(&weight_sum,4,1,stderr);mat[(size_t)y*w+x] = sum / weight_sum;')
 source=source.replace('mat[(size_t)y * w + x] = (sum + center) / (weight_sum + 1.0f);', 'float n=sum+center,d=weight_sum+1.0f;fwrite(&n,4,1,stderr);fwrite(&d,4,1,stderr);mat[(size_t)y * w + x] = n/d;')
 source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
 cpp=hd/'copy.cpp';cpp.write_text(source);host=hd/'host.cpp'
 host.write_text(host.read_text().replace(str(SOURCE),str(cpp)).replace('int main(int argc,char **argv)','int public_main(int argc,char **argv)')+'\nint main(int argc,char **argv){float f=0;int r=atoi(argv[1]);if(r==1)bilateral_blur_opencv455_f32x4(&f,1,1);else bilateral_blur_ipp_scalar(&f,1,1,r);fwrite(&f,4,1,stdout);}')
 a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
 for row in rows:
  native=subprocess.run([str(a.binary),str(row['radius'])],capture_output=True,check=True)
  row.update(mac_output_hex=native.stdout.hex(),mac_sums_hex=[native.stderr[:4].hex(),native.stderr[4:8].hex()])
  row['exact']=row['output_hex']==row['mac_output_hex'] and row.get('sums_hex')==row['mac_sums_hex']
(E/'zero-trace.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['exact'] for r in rows)
