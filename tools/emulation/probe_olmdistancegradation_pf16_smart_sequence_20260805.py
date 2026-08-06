#!/usr/bin/env python3
"""Natural outer Smart sequence probe through FUN_1811741a0."""
import hashlib,json,struct,sys,os,traceback
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RSP,UC_X86_REG_RAX,UC_X86_REG_RIP,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(H))
from aex_loader import AexLoader
A=R/'plugins_2025/DistanceGradation.aex';ENTRY=0x1811741a0;DISPATCH=0x181174bd0;RENDER=0x1811743b0;PF16_WRAPPER=0x181170280;PF8_WRAPPER=0x181170380
def main():
 depth=int(os.environ.get('OLM_DG_SMART_DEPTH','16'));assert depth in (8,16);pixel_size=8 if depth==16 else 4;typed_wrapper=PF16_WRAPPER if depth==16 else PF8_WRAPPER
 ld=AexLoader(str(A),fast=True);events=[];smart={'depth':depth};ind=ld.host_alloc(0x300);ld.write_bytes(ind,b'\0'*0x300);seq=ld.host_alloc(0x100);ld.write_bytes(seq,b'\0'*0x100);pre=ld.host_alloc(0x100);ld.write_bytes(pre,b'\0'*0x100);suite=ld.host_alloc(0x100);ld.write_bytes(suite,b'\0'*0x100)
 def checkout(l,args):
  rsp=l.uc.reg_read(UC_X86_REG_RSP);dest=struct.unpack('<Q',l.read_bytes(rsp+0x30,8))[0];slot=int(args[1]);l.write_bytes(dest,b'\0'*0xb0);value={1:1,2:1,3:4,4:4,5:1,6:1,9:2,10:1,11:1,12:0}.get(slot,0);l.write_bytes(dest+0x38,struct.pack('<i',value));events.append({'callback':'checkout','slot':slot,'dest':hex(dest),'value':value});return 0
 def checkin(l,args):events.append({'callback':'checkin'});return 0
 ld.write_bytes(ind,struct.pack('<2Q',ld.install_callback('smart.checkout',checkout),ld.install_callback('smart.checkin',checkin)))
 def out_rdx(l,args):l.write_bytes(int(args[1]),struct.pack('<Q',seq));events.append({'callback':'suite+0x00','out':hex(seq)});return 0
 def out_r8(l,args):l.write_bytes(int(args[2]),struct.pack('<Q',pre));events.append({'callback':'suite out R8','out':hex(pre)});return 0
 def noop(l,args):events.append({'callback':'suite noop'});return 0
 c0=ld.install_callback('smart.seq.out_rdx',out_rdx);c8=ld.install_callback('smart.seq.out_r8',out_r8);cn=ld.install_callback('smart.seq.noop',noop)
 for off,ptr in ((0,c0),(8,c8),(0x40,cn),(0x70,c8)):ld.write_bytes(suite+off,struct.pack('<Q',ptr))
 basic=ld.host_alloc(0x10)
 param_suite=ld.host_alloc(0x20);ld.write_bytes(param_suite,b'\0'*0x20)
 def param_utils(l,args):events.append({'callback':'ParamUtils','slot':int(args[1]),'param':hex(int(args[2]))});return 0
 ld.write_bytes(param_suite,struct.pack('<Q',ld.install_callback('smart.ParamUtils',param_utils)))
 iterate_suite=ld.host_alloc(8);ld.write_bytes(iterate_suite,b'\0'*8)
 def iterate16(l,args):
  rsp=l.uc.reg_read(UC_X86_REG_RSP);refcon=struct.unpack('<Q',l.read_bytes(rsp+0x30,8))[0];callback=struct.unpack('<Q',l.read_bytes(rsp+0x38,8))[0];out_world=struct.unpack('<Q',l.read_bytes(rsp+0x40,8))[0];events.append({'callback':'PF_Iterate16_enter','args':[hex(x) for x in args],'rsp':hex(rsp),'guest_callback':hex(callback),'refcon':hex(refcon),'output_world':hex(out_world)})
  width=smart['width'];height=int(args[2]);out_data=struct.unpack('<Q',l.read_bytes(out_world+0x18,8))[0];out_rb=struct.unpack('<I',l.read_bytes(out_world+0x20,4))[0]
  smart['refcon_hex']=l.read_bytes(refcon,0xd8).hex()
  saved=l.uc.context_save();count=0
  try:
   for y in range(height):
    for x in range(width):
     l.write_bytes(smart['pixel'],b'\xee'*pixel_size);l.write_bytes(smart['nested_stack'],struct.pack('<Q',smart['nested_return']));l.write_bytes(smart['nested_stack']+0x28,struct.pack('<Q',smart['pixel']))
     l.uc.reg_write(UC_X86_REG_RSP,smart['nested_stack']);l.uc.reg_write(UC_X86_REG_RCX,refcon);l.uc.reg_write(UC_X86_REG_RDX,x);l.uc.reg_write(UC_X86_REG_R8,y);l.uc.reg_write(UC_X86_REG_R9,0);l.uc.reg_write(UC_X86_REG_RIP,callback);l.uc.emu_start(callback,0,count=200000)
     px=l.read_bytes(smart['pixel'],pixel_size)
     if px==b'\xee'*pixel_size:raise RuntimeError(f'compose wrote no pixel at {x},{y}')
     l.write_bytes(out_data+y*out_rb+x*pixel_size,px);count+=1
  finally:l.uc.context_restore(saved)
  events.append({'callback':'PF_Iterate16' if depth==16 else 'PF_Iterate8','guest_callback':hex(callback),'refcon':hex(refcon),'pixels':count,'height':height});return 0
 ld.write_bytes(iterate_suite,struct.pack('<Q',ld.install_callback('smart.PF_IterateTyped',iterate16)))
 def acquire(l,args):
  raw=bytearray()
  for i in range(96):
   b=l.read_bytes(int(args[0])+i,1)
   if b==b'\0':break
   raw+=b
  name=raw.decode('ascii','replace');events.append({'callback':'AcquireSuite','name':name,'version':int(args[1])});chosen=iterate_suite if ('iterate16 Suite' in name or 'Iterate8 Suite' in name) else param_suite if 'Param Utils' in name else suite;l.write_bytes(int(args[2]),struct.pack('<Q',chosen));return 0
 def release(l,args):return 0
 ld.write_bytes(basic,struct.pack('<2Q',ld.install_callback('acquire',acquire),ld.install_callback('release',release)));ld.write_bytes(ind+0x180,struct.pack('<Q',basic))
 def render_gate(l,address,size):
  rsp=l.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',l.read_bytes(rsp,8))[0];events.append({'gate':'FUN_1811743b0','in_data':hex(l.uc.reg_read(UC_X86_REG_RCX)),'pre_render_handle':hex(pre),'pre_render_raw':l.read_bytes(pre,0x100).hex()});l.uc.reg_write(UC_X86_REG_RAX,0);l.uc.reg_write(UC_X86_REG_RSP,rsp+8);l.uc.reg_write(UC_X86_REG_RIP,ret)
 natural=os.environ.get('OLM_DG_SMART_RENDER')=='1'
 dispatch=os.environ.get('OLM_DG_SMART_DISPATCH')=='1'
 def wrapper_observe(l,address,size):
  rsp=l.uc.reg_read(UC_X86_REG_RSP)
  events.append({'gate':f'FUN_{address:x}','rcx':hex(l.uc.reg_read(UC_X86_REG_RCX)),'rdx':hex(l.uc.reg_read(UC_X86_REG_RDX)),'r8':hex(l.uc.reg_read(UC_X86_REG_R8)),'r9':hex(l.uc.reg_read(UC_X86_REG_R9)),'rsp':hex(rsp),'stack':l.read_bytes(rsp,0x60).hex()})
  if os.environ.get('OLM_DG_SMART_WRAPPER_GATE')=='1':
   ret=struct.unpack('<Q',l.read_bytes(rsp,8))[0];l.uc.reg_write(UC_X86_REG_RAX,0);l.uc.reg_write(UC_X86_REG_RSP,rsp+8);l.uc.reg_write(UC_X86_REG_RIP,ret)
 ld.add_code_hook(PF16_WRAPPER,wrapper_observe);ld.add_code_hook(PF8_WRAPPER,wrapper_observe)
 if not natural:ld.add_code_hook(RENDER,render_gate)
 failure=None
 try:regs=ld.call_function(ENTRY,int_args=[ind],max_instructions=1000000)
 except Exception as exc:failure={'type':type(exc).__name__,'message':str(exc),'trace_tail':traceback.format_exc().splitlines()[-5:]};regs={'instructions':0,'rax':0xffffffff}
 if dispatch and failure is None:
  outdata=ld.host_alloc(0x300);ld.write_bytes(outdata,b'\0'*0x300)
  width,height=17,11;in_rb=width*pixel_size+(10 if depth==16 else 7);out_rb=width*pixel_size+(14 if depth==16 else 11);sentinel=0xa5
  paramsbase=ld.host_alloc(0x200);ld.write_bytes(paramsbase,b'\0'*0x200);input_world=paramsbase+0x38
  input_data=ld.bump_alloc(in_rb*height,align=64);ld.write_bytes(input_data,bytes([sentinel])*(in_rb*height))
  for y in range(height):
   for x in range(width):
    if depth==16:
     a=(1024+x*1731+y*911)%32769;g=(x*1237+y*271)%32769;r=(x*719+y*1429)%32769;b=(x*1999+y*337)%32769;px=struct.pack('<4H',a,g,r,b)
    else:
     a=(7+x*17+y*11)%256;g=(x*13+y*3)%256;r=(x*7+y*19)%256;b=(x*23+y*5)%256;px=bytes((a,g,r,b))
    ld.write_bytes(input_data+y*in_rb+x*pixel_size,px)
  for off,data in ((0x18,struct.pack('<Q',input_data)),(0x20,struct.pack('<I',in_rb)),(0x24,struct.pack('<I',width)),(0x28,struct.pack('<I',height))):ld.write_bytes(input_world+off,data)
  param_owner=ld.host_alloc(8);ld.write_bytes(param_owner,struct.pack('<Q',paramsbase))
  request=ld.host_alloc(0x100);ld.write_bytes(request,b'\0'*0x100);output_data=ld.bump_alloc(out_rb*height,align=64);ld.write_bytes(output_data,bytes([sentinel])*(out_rb*height))
  seed=[]
  for y in range(height):
   for x in range(width):
    if depth==16:field=(x*2048+y*1024)%32769;px=struct.pack('<4H',32768,field,field,field)
    else:field=(x*16+y*8)%256;px=bytes((255,field,field,field))
    seed.append(px);ld.write_bytes(output_data+y*out_rb+x*pixel_size,px)
  for off,data in ((0x10,bytes([1 if depth==16 else 0])),(0x18,struct.pack('<Q',output_data)),(0x20,struct.pack('<I',out_rb)),(0x24,struct.pack('<I',width)),(0x28,struct.pack('<I',height)),(0x30,struct.pack('<i',0)),(0x38,struct.pack('<i',height))):ld.write_bytes(request+off,data)
  extra=ld.host_alloc(0x100);ld.write_bytes(extra,b'\0'*0x100)
  smart.update(width=width,height=height,input_world=input_world,output_world=request,pixel=ld.bump_alloc(8,align=16),nested_return=0x90001000,nested_stack=0xe080000)
  try:ld.uc.mem_map(0x90001000,0x1000)
  except Exception:pass
  try:ld.uc.mem_map(0xe000000,0x100000)
  except Exception:pass
  def stop_nested(uc,address,_size,_user):
   if address==smart['nested_return']:uc.emu_stop()
  ld.uc.hook_add(UC_HOOK_CODE,stop_nested,begin=smart['nested_return'],end=smart['nested_return'])
  try:
   dregs=ld.call_function(DISPATCH,int_args=[0xb,ind,outdata,param_owner,request,extra],max_instructions=1000000)
   events.append({'dispatch_return_eax':int(dregs['rax']&0xffffffff),'dispatch_instructions':int(dregs['instructions']),'request':hex(request),'params_base':hex(paramsbase)})
   active=b''.join(ld.read_bytes(output_data+y*out_rb,width*pixel_size) for y in range(height));in_padding=b''.join(ld.read_bytes(input_data+y*in_rb+width*pixel_size,in_rb-width*pixel_size) for y in range(height));out_padding=b''.join(ld.read_bytes(output_data+y*out_rb+width*pixel_size,out_rb-width*pixel_size) for y in range(height))
   smart.update(active_sha256=hashlib.sha256(active).hexdigest(),active_hex=active.hex(),input_active_hex=b''.join(ld.read_bytes(input_data+y*in_rb,width*pixel_size) for y in range(height)).hex(),field_seed_active_hex=b''.join(seed).hex(),input_padding_unchanged=all(b==sentinel for b in in_padding),output_padding_unchanged=all(b==sentinel for b in out_padding),input_rowbytes=in_rb,output_rowbytes=out_rb,result_rect=[0,0,width,height],max_result_rect=[0,0,width,height],pre_render_sha256=hashlib.sha256(ld.read_bytes(pre,0x100)).hexdigest(),pre_render_raw=ld.read_bytes(pre,0x100).hex())
  except Exception as exc:
   failure={'type':type(exc).__name__,'message':str(exc),'trace_tail':traceback.format_exc().splitlines()[-5:]}
 wrapper_reached=any(e.get('gate')==f'FUN_{typed_wrapper:x}' for e in events)
 status='natural_render_complete' if natural and failure is None else 'natural_render_next_dependency' if natural else 'outer_sequence_return_exact';report={'schema':f'olmdistancegradation.pf{depth}-smart-sequence-probe/1','status':status,'binary_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'entry':hex(ENTRY),'render_gate':hex(RENDER),'typed_wrapper':hex(typed_wrapper),'typed_wrapper_reached':wrapper_reached,'pf16_wrapper_reached':wrapper_reached if depth==16 else False,'events':events,'smart_capture':smart,'instructions':int(regs['instructions']),'return_eax':int(regs['rax']&0xffffffff),'failure':failure,'pre_render_handle':hex(pre),'sequence_handle':hex(seq)}
 if not natural:assert report['return_eax']==0 and any(e.get('gate')=='FUN_1811743b0' for e in events)
 if dispatch:assert wrapper_reached
 print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
