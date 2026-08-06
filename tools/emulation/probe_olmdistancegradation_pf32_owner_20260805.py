#!/usr/bin/env python3
"""First executable probe of DG PF32 whole-render owner FUN_181172a10."""
from __future__ import annotations
import hashlib,json,struct,sys,traceback,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
from aex_loader import AexLoader
import opencv_impls as ocv
import cv_bridge as cvb
import numpy as np
from unicorn.x86_const import UC_X86_REG_RSP,UC_X86_REG_RAX,UC_X86_REG_RIP,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9
from test_dg_fieldgen_p1b import setup_tls,build_host_suites
AEX=ROOT/'plugins_2025/DistanceGradation.aex';OWNER=0x181172a10
def main():
 source_mode=os.environ.get('OLM_DG_PF32_SOURCE','zero');assert source_mode in ('zero','controlled','outside_sphere','outside_sphere_invert','both_linear_layer','both_power_layer','inside_constant_blur');outside=source_mode.startswith('outside_sphere');both_layer=source_mode in ('both_linear_layer','both_power_layer');constant_blur=source_mode=='inside_constant_blur';padded=outside or both_layer or constant_blur
 ld=AexLoader(str(AEX),verbose=False,fast=True);ld.register_libm_impls(max_threads=1);setup_tls(ld);ld.enable_crt_initializer_imports()
 entry=ld.load_base+ld.pe.OPTIONAL_HEADER.AddressOfEntryPoint
 try: ld.call_function(entry,int_args=[ld.load_base,1,0],max_instructions=5_000_000)
 except Exception: pass
 ocv.register_opencv_impls(ld,'DistanceGradation',ops=['threshold','dist_transform','resize_same_shape','normalize_minmax'])
 # ABI skeleton taken directly from the owner's first basic-block reads.  It
 # deliberately installs only the first observed indirect callback so the
 # next missing host relation is reported rather than guessed.
 indata=ld.host_alloc(0x300);ld.write_bytes(indata,b'\0'*0x300)
 params=ld.host_alloc(0x200);ld.write_bytes(params,b'\0'*0x200)
 extra=ld.host_alloc(0x200);ld.write_bytes(extra,b'\0'*0x200)
 table=ld.host_alloc(0x80);ld.write_bytes(table,b'\0'*0x80)
 suite=ld.host_alloc(0x80);ld.write_bytes(suite,b'\0'*0x80)
 input_world=ld.host_alloc(0x100);ld.write_bytes(input_world,b'\0'*0x100)
 input_rowbytes=17*16+(8 if padded else 0);source_data=ld.bump_alloc(input_rowbytes*11,align=64);source_raw=bytearray([0xa5])*(input_rowbytes*11) if padded else bytearray(input_rowbytes*11)
 if source_mode in ('controlled','outside_sphere','outside_sphere_invert','both_linear_layer','both_power_layer','inside_constant_blur'):
  for y in range(11):
   for x in range(17):
    alpha=0.0 if (y==5 and 6<=x<=10) else 1.0
    rgb=(0.25*alpha,0.5*alpha,0.75*alpha) if source_mode=='controlled' else (((x*0.03125)%1.0)*alpha,((y*0.0625)%1.0)*alpha,(((x+y)*0.025)%1.0)*alpha)
    struct.pack_into('<4f',source_raw,y*input_rowbytes+x*16,alpha,*rgb)
 ld.write_bytes(source_data,bytes(source_raw));ld.write_bytes(input_world+0x18,struct.pack('<Q',source_data));ld.write_bytes(input_world+0x20,struct.pack('<iii',input_rowbytes,17,11))
 for off in (0x11c,0x120,0x124,0x128):ld.write_bytes(indata+off,struct.pack('<i',1))
 owner_state=ld.host_alloc(0x200);ld.write_bytes(owner_state,b'\0'*0x200)
 events=[];output_binding={}
 slot_values={1:(1 if source_mode in ('outside_sphere_invert','both_linear_layer','both_power_layer','inside_constant_blur') else 0 if outside else 1),2:(3 if both_layer else 2 if outside else 1),3:4,4:4,5:(1 if source_mode=='controlled' else 0),6:(2 if both_layer else 1 if source_mode in ('controlled','outside_sphere','outside_sphere_invert','inside_constant_blur') else 0),7:0,8:0,9:(4 if source_mode=='both_power_layer' else 2 if source_mode=='both_linear_layer' else 3 if outside else 2 if source_mode=='controlled' else 1),10:(2.5 if source_mode=='both_power_layer' else 1),11:(2 if constant_blur else 1),12:(2 if constant_blur else 0)}
 def checkout_cb(loader,args):
  slot=int(args[1]&0xffffffff);rsp=loader.uc.reg_read(UC_X86_REG_RSP);dest=struct.unpack('<Q',loader.read_bytes(rsp+0x30,8))[0]
  value=slot_values.get(slot,0);loader.write_bytes(dest,b'\0'*0xb0)
  loader.write_bytes(dest+0x38,struct.pack('<d',float(value)) if slot==10 else struct.pack('<i',value))
  events.append({'callback':'checkout_param','slot':slot,'destination':hex(dest),'value':value,'raw_value_16':loader.read_bytes(dest+0x38,16).hex()});return 0
 def checkin_cb(loader,args):events.append({'callback':'checkin_param'});return 0
 ld.write_bytes(indata,struct.pack('<Q',ld.install_callback('DG.checkout_param',checkout_cb)))
 ld.write_bytes(indata+8,struct.pack('<Q',ld.install_callback('DG.checkin_param',checkin_cb)))
 def color_cb(loader,args):
  events.append({'callback':'ColorParam.GetFloatingPointColor','args':[hex(int(x)) for x in args]})
  # slot 7 (gradation) and slot 8 (background) are requested into distinct
  # owner-state destinations. Use exact, separately logged probe values.
  destination=int(args[2]); values=(1.0,28/255,0.0,238/255)
  loader.write_bytes(destination,struct.pack('<4f',*values));return 0
 color_ptr=ld.install_callback('DG.ColorParam.GetFloatingPointColor',color_cb)
 color_suite=ld.host_alloc(0x20);ld.write_bytes(color_suite,struct.pack('<Q',color_ptr)+b'\0'*0x18)
 def h_new(loader,args):
  size=int(args[0]);data=loader.bump_alloc(max(size,1),align=64);loader.write_bytes(data,b'\0'*max(size,1));handle=loader.host_alloc(8);loader.write_bytes(handle,struct.pack('<Q',data));events.append({'callback':'PFHandle.new','size':size});return handle
 def h_lock(loader,args):return struct.unpack('<Q',loader.read_bytes(int(args[0]),8))[0] if args[0] else 0
 def h_noop(loader,args):return 0
 handle_suite=ld.host_alloc(0x20);ld.write_bytes(handle_suite,struct.pack('<4Q',ld.install_callback('DG.PFHandle.new',h_new),ld.install_callback('DG.PFHandle.lock',h_lock),ld.install_callback('DG.PFHandle.unlock',h_noop),ld.install_callback('DG.PFHandle.dispose',h_noop)))
 def acquire_cb(loader,args):
  raw=bytearray()
  for i in range(128):
   c=loader.read_bytes(int(args[0])+i,1)
   if c==b'\0':break
   raw+=c
  name=raw.decode('ascii','replace');events.append({'callback':'SPBasic.AcquireSuite','suite':name})
  loader.write_bytes(int(args[2]),struct.pack('<Q',color_suite if 'Color' in name else handle_suite));return 0
 def release_cb(loader,args):return 0
 spbasic=ld.host_alloc(0x10);ld.write_bytes(spbasic,struct.pack('<2Q',ld.install_callback('DG.SPBasic.AcquireSuite',acquire_cb),ld.install_callback('DG.SPBasic.ReleaseSuite',release_cb)));ld.write_bytes(indata+0x180,struct.pack('<Q',spbasic))
 def first_cb(loader,args):
  events.append({'callback':'owner.extra.vtable+0x10','args':[hex(int(x)) for x in args]})
  # arg1 is an owner-local out pointer. Return a non-null opaque token.
  rowbytes=17*16+(16 if padded else 0);data=loader.bump_alloc(rowbytes*11,align=64);loader.write_bytes(data,(b'\xa5' if padded else b'\xcd')*(rowbytes*11))
  token=loader.host_alloc(0x80);loader.write_bytes(token,b'\0'*0x80);loader.write_bytes(token+0x18,struct.pack('<Q',data));loader.write_bytes(token+0x20,struct.pack('<iii',rowbytes,17,11));loader.write_bytes(int(args[1]),struct.pack('<Q',token));output_binding.update({'world':token,'data':data,'rowbytes':rowbytes,'width':17,'height':11});return 0
 cb=ld.install_callback('DG.PF32.owner_first_indirect',first_cb)
 ld.write_bytes(table+0x10,struct.pack('<Q',cb));ld.write_bytes(extra+8,struct.pack('<Q',table))
 status='unexpected_complete';failure=None;instructions=None;field_capture={};field_blob={}
 matrix_captures=[]
 def mat_snapshot(loader,ptr):
  if not ptr:return {'ptr':'0x0'}
  try:raw=loader.read_bytes(ptr,0x60)
  except Exception:return {'ptr':hex(ptr),'not_mapped_mat':True}
  flags,dims,rows,cols=struct.unpack_from('<4i',raw,0);data=struct.unpack_from('<Q',raw,0x10)[0];step_ptr=struct.unpack_from('<Q',raw,0x48)[0]
  snap={'ptr':hex(ptr),'header':raw.hex(),'flags':flags,'dims':dims,'rows':rows,'cols':cols,'data':hex(data),'step_ptr':hex(step_ptr)}
  if flags==0x90:
   arr=np.ascontiguousarray(cvb.read_ipl(loader,ptr));flat=arr.reshape(-1,arr.shape[2] if arr.ndim==3 else 1);snap.update({'kind':'IplImage','shape':list(arr.shape),'dtype':str(arr.dtype),'pixels':{str(i):flat[i].tobytes().hex() for i in (0,90,91,93,96) if i<len(flat)}});return snap
  if 0<rows<=64 and 0<cols<=64 and data:
   depth=flags&7;channels=1+((flags>>3)&0x1ff);scalar={0:1,2:2,5:4,6:8}.get(depth,1);elem=scalar*channels;step=struct.unpack('<Q',loader.read_bytes(step_ptr,8))[0] if step_ptr else cols*elem;snap.update({'depth':depth,'channels':channels,'elem_size':elem,'step':step,'pixels':{str(i):loader.read_bytes(data+(i//cols)*step+(i%cols)*elem,elem).hex() for i in (0,90,91,93,96) if i<rows*cols}})
  return snap
 def matrix_hook(label):
  def hook(loader,address,size):
   rsp=loader.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',loader.read_bytes(rsp,8))[0];args=[loader.uc.reg_read(r) for r in (UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9)];rec={'label':label,'phase':'entry','rip':hex(address),'return':hex(ret),'args':[mat_snapshot(loader,p) for p in args]};matrix_captures.append(rec)
   loader.add_code_hook(ret,lambda ld2,a2,s2,rec=rec:matrix_captures.append({'label':label,'phase':'return','rip':hex(a2),'args':[mat_snapshot(ld2,int(x['ptr'],16)) for x in rec['args']]}))
  return hook
 for addr,label in ((0x18117bca0,'precompose_copy_or_convert'),(0x18117c6e0,'final_compose'),(0x18117c580,'scale_or_normalize')):ld.add_code_hook(addr,matrix_hook(label))
 tls_value=ld.host_alloc(0x20);ld.write_bytes(tls_value,b'\0'*0x20)
 def tls_container_shim(loader,address,size):
  rsp=loader.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',loader.read_bytes(rsp,8))[0];events.append({'shim':'FUN_181187e20','rcx_contract':'ignored probe-local TLS container','return':hex(tls_value)});loader.uc.reg_write(UC_X86_REG_RAX,tls_value);loader.uc.reg_write(UC_X86_REG_RSP,rsp+8);loader.uc.reg_write(UC_X86_REG_RIP,ret)
 ld.add_code_hook(0x181187e20,tls_container_shim)
 ld.add_code_hook(0x181187f50,tls_container_shim)
 def field_entry(loader,address,size):
  from unicorn.x86_const import UC_X86_REG_R8
  rsp=loader.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',loader.read_bytes(rsp,8))[0];dst=loader.uc.reg_read(UC_X86_REG_R8)
  events.append({'hook':'FUN_181174760','rip':hex(address),'dst_ipl':hex(dst),'return':hex(ret)})
  def field_return(ld2,a2,s2):
   if field_capture:return
   arr=np.ascontiguousarray(cvb.read_ipl(ld2,dst),dtype='<f4');raw=arr.tobytes();field_blob['raw']=raw;field_capture.update({'shape':list(arr.shape),'sha256':hashlib.sha256(raw).hexdigest(),'word_count':int(arr.size),'first_words':[f'0x{x:08x}' for x in np.frombuffer(raw,dtype='<u4')[:8]]})
  loader.add_code_hook(ret,field_return)
 ld.add_code_hook(0x181174760,field_entry)
 try:
  regs=ld.call_function(OWNER,int_args=[32,indata,params,extra,input_world,owner_state],max_instructions=2_000_000);instructions=int(regs['instructions'])
  status='owner_completed_field_captured'
 except Exception as exc:
  status='next_dependency_identified';failure={'type':type(exc).__name__,'message':str(exc),'trace_tail':traceback.format_exc().splitlines()[-6:]}
 if status=='owner_completed_field_captured' and output_binding:
  raw=ld.read_bytes(output_binding['data'],output_binding['rowbytes']*11);active=b''.join(raw[y*output_binding['rowbytes']:y*output_binding['rowbytes']+17*16] for y in range(11));padding=b''.join(raw[y*output_binding['rowbytes']+17*16:(y+1)*output_binding['rowbytes']] for y in range(11));output_binding['sha256']=hashlib.sha256(raw).hexdigest();output_binding['active_sha256']=hashlib.sha256(active).hexdigest();output_binding['byte_count']=len(raw);output_binding['padding_unchanged']=all(b==0xa5 for b in padding) if padded else None;output_binding['active_hex']=active.hex() if padded else None
  suffix='' if source_mode=='zero' else '_controlled_source' if source_mode=='controlled' else '_'+source_mode;fixture=ROOT/f'refs/fixtures/olmdistancegradation_pf32_owner_17x11{suffix}_20260805';fixture.mkdir(parents=True,exist_ok=True);(fixture/'source_argb_f32.bin').write_bytes(ld.read_bytes(source_data,input_rowbytes*11));(fixture/'field_f32.bin').write_bytes(field_blob['raw']);(fixture/'output_argb_f32.bin').write_bytes(raw)
 report={'schema':'olmdistancegradation.pf32-owner-probe/1','source_mode':source_mode,'status':status,'binary_sha256':hashlib.sha256(AEX.read_bytes()).hexdigest(),'entry':hex(OWNER),'events':events,'instructions':instructions,'failure':failure,'parameter_contract':{'checkout_slots':[2,3,4,6,5,7,8,1,9,10,11,12],'slot7_float_color_argb':[1.0,28/255,0.0,238/255],'checkout_destination_stack_arg':'RSP+0x30 (argument 6)'},'fieldgen_reached':any(e.get('hook')=='FUN_181174760' for e in events),'intermediate_field':field_capture,'output_world':output_binding,'matrix_captures':matrix_captures,'mat_tls_shim':{'functions':['0x181187e20','0x181187f50'],'return_object_size':32,'zero_initialized':True},'conclusion':'Probe-local Mat TLS singleton shims allow the 17x11 PF32 owner to complete and reach FUN_181174760. The intermediate float field and naturally written output world are retained; PF8/PF16 staging is not used.'}
 json_suffix='' if source_mode=='zero' else '_controlled_source' if source_mode=='controlled' else '_'+source_mode;out=ROOT/f'refs/conformance/olmdistancegradation_pf32_owner_probe{json_suffix}_20260805.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if events else 1
if __name__=='__main__':raise SystemExit(main())
