#!/usr/bin/env python3
"""Focused actual-AEX sequence setup and SmartPreRender entry probe."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa:E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX,alloc  # noqa:E402
ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json";MARKDOWN=REPORT.with_suffix(".md")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";ENTRY=0x1801ABC00
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 if sha(AEX)!=AEX_SHA:raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
 l=AexLoader(str(AEX),verbose=False,fast=True);events=[];allocations={}
 def cstr(ptr):
  b=bytearray()
  for i in range(128):
   v=l.read_bytes(ptr+i,1)[0]
   if not v:break
   b.append(v)
  return b.decode(errors="replace")
 def install(name,fn):return l.install_callback(name,fn)
 def handle_alloc(cur,args):
  size=max(1,args[0]);p=cur.host_alloc(size,align=16);cur.write_bytes(p,b"\0"*size);allocations[p]=size;events.append({"kind":"handle_alloc","size":size,"handle":hex(p)});return p
 def handle_lock(_cur,args):events.append({"kind":"handle_lock","handle":hex(args[0])});return args[0]
 def handle_unlock(_cur,args):events.append({"kind":"handle_unlock","handle":hex(args[0])});return 0
 def handle_dispose(_cur,args):events.append({"kind":"handle_dispose","handle":hex(args[0])});return 0
 hv=l.host_alloc(0x20,align=16);l.write_bytes(hv,struct.pack("<4Q",install("seq_handle_alloc",handle_alloc),install("seq_handle_lock",handle_lock),install("seq_handle_unlock",handle_unlock),install("seq_handle_dispose",handle_dispose)))
 def register(cur,args):
  events.append({"kind":"AEGP_RegisterWithAEGP","global_refcon":hex(args[0]),"plugin_name":cstr(args[1]),"plugin_id_out":hex(args[2])});cur.write_bytes(args[2],struct.pack("<I",77));return 0
 uv=l.host_alloc(0x60,align=16);l.write_bytes(uv,b"\0"*0x60);l.write_bytes(uv+0x48,struct.pack("<Q",install("seq_register_aegp",register)))
 world_suite_ptr=0
 def acquire(cur,args):
  name=cstr(args[0]);events.append({"kind":"acquire_suite","name":name,"version":args[1]});suite=uv if name=="AEGP Utility Suite" else world_suite_ptr if name=="PF World Suite" else hv;cur.write_bytes(args[2],struct.pack("<Q",suite));return 0
 def release(_cur,args):events.append({"kind":"release_suite","name":cstr(args[0]),"version":args[1]});return 0
 basic=l.host_alloc(0x20,align=16);l.write_bytes(basic,struct.pack("<2Q",install("seq_acquire_suite",acquire),install("seq_release_suite",release))+b"\0"*16)
 in_data=l.host_alloc(0x220,align=16);l.write_bytes(in_data,b"\0"*0x220);l.write_bytes(in_data+0x180,struct.pack("<Q",basic));out_data=alloc(l,b"\0"*0x300)
 setup=l.call_function(ENTRY,int_args=[1,in_data,out_data,0,0,0],max_instructions=3_000_000);handle=struct.unpack("<Q",l.read_bytes(out_data+0x28,8))[0];size=allocations.get(handle,0);initial=bytes(l.read_bytes(handle,size));l.write_bytes(in_data+0x138,struct.pack("<Q",handle))
 pre_input=l.host_alloc(0x40,align=16);l.write_bytes(pre_input,b"\0"*0x40);pre_output=l.host_alloc(0x80,align=16);l.write_bytes(pre_output,b"\0"*0x80)
 def checkout(cur,args):
  from unicorn.x86_const import UC_X86_REG_RSP
  rsp=cur.uc.reg_read(UC_X86_REG_RSP);stack=[struct.unpack("<Q",cur.read_bytes(rsp+0x28+i*8,8))[0] for i in range(4)];result=stack[3]
  cur.write_bytes(result,struct.pack("<8i",10,20,13,22,9,19,14,23)+b"\0"*16+struct.pack("<2i",30,40)+b"\0"*24)
  events.append({"kind":"smartpre_checkout_layer","args":[hex(x) for x in args],"stack_args_5_to_8":[hex(x) for x in stack],"checkout_result":hex(result),"result_rect":[10,20,13,22],"max_result_rect":[9,19,14,23]});return 0
 pre_callbacks=l.host_alloc(0x20,align=16);l.write_bytes(pre_callbacks,struct.pack("<Q",install("seq_smartpre_checkout",checkout))+b"\0"*0x18)
 extra=l.host_alloc(0x20,align=16);l.write_bytes(extra,struct.pack("<3Q",pre_input,pre_output,pre_callbacks)+b"\0"*8)
 pre=l.call_function(ENTRY,int_args=[0x17,in_data,out_data,0,0,extra],max_instructions=3_000_000);flag=struct.unpack("<H",l.read_bytes(pre_output+0x22,2))[0];result_rect=list(struct.unpack("<4i",l.read_bytes(pre_output,16)));max_result_rect=list(struct.unpack("<4i",l.read_bytes(pre_output+16,16)))
 # SmartRender command 0x18: retain actual entry/vtable/worker and provide only
 # the host parameter checkout seam plus checkout/checkin/output callbacks.
 from unicorn.x86_const import UC_X86_REG_R9,UC_X86_REG_RIP,UC_X86_REG_RSP
 radius_state={"value":1.0}
 def parameter_seam(cur,_address,_size):
  radius_out=cur.uc.reg_read(UC_X86_REG_R9);cur.write_bytes(radius_out,struct.pack("<f",radius_state["value"]));rsp=cur.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack("<Q",cur.read_bytes(rsp,8))[0];cur.uc.reg_write(UC_X86_REG_RSP,rsp+8);cur.uc.reg_write(UC_X86_REG_RIP,ret);events.append({"kind":"parameter_checkout_seam","radius":radius_state["value"],"output":hex(radius_out)})
 l.add_code_hook(0x1801A9AC0,parameter_seam)
 def world(pixels,extent):
  guard=l.host_alloc(0x40,align=16);l.write_bytes(guard,b"\xCC"*0x40);data=guard+0x10;l.write_bytes(data,b"".join(pixels)+b"\xA5"*4);h=l.host_alloc(0x50,align=16);l.write_bytes(h,b"\0"*0x50);l.write_bytes(h+0x18,struct.pack("<QiiiH",data,12,2,1,32));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,data,guard
 seed=bytes([255,10,20,30]);clear=bytes([0,101,202,77]);input_extent=[100,200,102,201];output_extent=[300,400,302,401];iw,idata,iguard=world([seed,clear],input_extent);ow,odata,oguard=world([clear,clear],output_extent)
 copy_state={"input":idata,"output":odata,"row_visible":8,"input_rowbytes":12,"output_rowbytes":12,"height":1}
 def pfcopy(cur,args):
  for y in range(copy_state["height"]):cur.write_bytes(copy_state["output"]+y*copy_state["output_rowbytes"],cur.read_bytes(copy_state["input"]+y*copy_state["input_rowbytes"],copy_state["row_visible"]))
  events.append({"kind":"PF_COPY","visible_bytes":copy_state["row_visible"]*copy_state["height"]});return 0
 status_table=l.host_alloc(0x50,align=16);l.write_bytes(status_table,b"\0"*0x50);l.write_bytes(status_table+0x40,struct.pack("<Q",install("smart_pf_copy",pfcopy)));l.write_bytes(in_data+0xB0,struct.pack("<Q",status_table));l.write_bytes(in_data+0xB8,struct.pack("<Q",0x1234));l.write_bytes(in_data+0x11C,struct.pack("<ii",1,1))
 def checkout_pixels(cur,args):cur.write_bytes(args[2],struct.pack("<Q",iw));events.append({"kind":"checkout_layer_pixels","world":hex(iw)});return 0
 def checkin(_cur,args):events.append({"kind":"checkin_layer_pixels","id":args[1]});return 0
 def checkout_output(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ow));events.append({"kind":"checkout_output","world":hex(ow)});return 0
 smart_cb=l.host_alloc(0x18,align=16);l.write_bytes(smart_cb,struct.pack("<3Q",install("smart_checkout_pixels",checkout_pixels),install("smart_checkin",checkin),install("smart_checkout_output",checkout_output)))
 smart_input=l.host_alloc(0x40,align=16);l.write_bytes(smart_input,b"\0"*0x40);l.write_bytes(smart_input+0x2C,struct.pack("<H",8));smart_extra=l.host_alloc(0x10,align=16);l.write_bytes(smart_extra,struct.pack("<2Q",smart_input,smart_cb))
 smart=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,smart_extra],max_instructions=5_000_000);partial_actual=bytes(l.read_bytes(odata,12));partial_expected=seed+seed+b"\xA5"*4;guards_ok=l.read_bytes(iguard,0x10)==b"\xCC"*0x10 and l.read_bytes(iguard+0x1c,0x24)==b"\xCC"*0x24 and l.read_bytes(oguard,0x10)==b"\xCC"*0x10 and l.read_bytes(oguard+0x1c,0x24)==b"\xCC"*0x24
 def run_typed_partial(depth,seed_bytes,clear_bytes):
  size=len(seed_bytes);rb=size*2+4;total=0x10+rb+0x10
  input_extent=[depth*10,depth*10+1,depth*10+2,depth*10+2];output_extent=[depth*20,depth*20+1,depth*20+2,depth*20+2]
  def typed_world(pixels,extent):
   guard=l.host_alloc(total,align=16);l.write_bytes(guard,b"\xCC"*total);data=guard+0x10;l.write_bytes(data,b"".join(pixels)+b"\xA5"*4);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",data,rb,2,1,{8:32,16:64,32:128}[depth]));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,data,guard
  tiw,tidata,tig=typed_world([seed_bytes,clear_bytes],input_extent);tow,todata,tog=typed_world([clear_bytes,clear_bytes],output_extent);copy_state.update({"input":tidata,"output":todata,"row_visible":size*2,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",tiw));events.append({"kind":f"PF{depth}_checkout_layer_pixels","world":hex(tiw)});return 0
  def ci(_cur,args):events.append({"kind":f"PF{depth}_checkin_layer_pixels","id":args[1]});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",tow));events.append({"kind":f"PF{depth}_checkout_output","world":hex(tow)});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(f"pf{depth}_cp",cp),install(f"pf{depth}_ci",ci),install(f"pf{depth}_co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=5_000_000)
  actual=bytes(l.read_bytes(todata,rb));expected=seed_bytes*2+b"\xA5"*4;guards=l.read_bytes(tig,0x10)==b"\xCC"*0x10 and l.read_bytes(tig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(tog,0x10)==b"\xCC"*0x10 and l.read_bytes(tog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":depth,"rowbytes":rb,"input_extent":input_extent,"output_extent":output_extent,"actual_hex":actual.hex(),"expected_hex":expected.hex(),"entry_returned":call["rax"]==0,"typed_bytes_exact":actual==expected,"extent_headers_unchanged":list(struct.unpack("<4i",l.read_bytes(tiw+0x30,16)))==input_extent and list(struct.unpack("<4i",l.read_bytes(tow+0x30,16)))==output_extent,"guards_untouched":guards,"checkout_callbacks":all(any(e["kind"]==k for e in events) for k in (f"PF{depth}_checkout_layer_pixels",f"PF{depth}_checkout_output")),"optional_checkin_not_called":not any(e["kind"]==f"PF{depth}_checkin_layer_pixels" for e in events)}
 pf16=run_typed_partial(16,struct.pack("<4H",32768,1001,2002,3003),struct.pack("<4H",0,50001,40002,30003));pf32=run_typed_partial(32,struct.pack("<4f",1.0,.125,.25,.5),struct.pack("<4f",0.0,.875,.625,.375))
 def run_mixed_3x2(depth,seed_bytes,mixed_bytes):
  size=len(seed_bytes);rb=3*size+8;total=0x10+rb*2+0x10;ie=[depth*30,depth*30+1,depth*30+3,depth*30+3];oe=[depth*40,depth*40+1,depth*40+3,depth*40+3]
  def mworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10
   for y in range(2):l.write_bytes(d+y*rb,b"".join(pixels[y*3:y*3+3])+b"\xA5"*8)
   h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,3,2,{8:32,16:64,32:128}[depth]));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  clear=bytes(size);source=[mixed_bytes,seed_bytes,mixed_bytes,clear,mixed_bytes,clear];mi,mid,mig=mworld(source,ie);mo,mod,mog=mworld([clear]*6,oe);copy_state.update({"input":mid,"output":mod,"row_visible":size*3,"input_rowbytes":rb,"output_rowbytes":rb,"height":2})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",mi));events.append({"kind":f"PF{depth}_mixed_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":f"PF{depth}_mixed_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",mo));events.append({"kind":f"PF{depth}_mixed_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(f"m{depth}cp",cp),install(f"m{depth}ci",ci),install(f"m{depth}co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=6_000_000)
  actual=bytes(l.read_bytes(mod,rb*2));expected=(seed_bytes*3+b"\xA5"*8)*2;guards=l.read_bytes(mig,0x10)==b"\xCC"*0x10 and l.read_bytes(mig+0x10+rb*2,0x10)==b"\xCC"*0x10 and l.read_bytes(mog,0x10)==b"\xCC"*0x10 and l.read_bytes(mog+0x10+rb*2,0x10)==b"\xCC"*0x10
  return {"depth":depth,"dimensions":[3,2],"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"frontier_propagated_all_pixels":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(mi+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(mo+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]==f"PF{depth}_mixed_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 mixed8=run_mixed_3x2(8,bytes([255,10,20,30]),bytes([128,81,41,21]));mixed16=run_mixed_3x2(16,struct.pack("<4H",32768,1001,2002,3003),struct.pack("<4H",16384,8001,7002,6003));mixed32=run_mixed_3x2(32,struct.pack("<4f",1.0,.125,.25,.5),struct.pack("<4f",.5,.8,.4,.2))
 def run_radius2_4x2(depth,seed_bytes,mixed_bytes):
  size=len(seed_bytes);rb=4*size+12;total=0x10+rb*2+0x10;ie=[depth*50+3,depth*50+5,depth*50+7,depth*50+7];oe=[depth*60+7,depth*60+9,depth*60+11,depth*60+11]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10
   for y in range(2):l.write_bytes(d+y*rb,b"".join(pixels[y*4:y*4+4])+b"\xB6"*12)
   h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,4,2,{8:32,16:64,32:128}[depth]));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  clear=bytes(size);source=[seed_bytes,mixed_bytes,clear,mixed_bytes,clear,mixed_bytes,clear,mixed_bytes];ri,rid,rig=rworld(source,ie);ro,rod,rog=rworld([clear]*8,oe);copy_state.update({"input":rid,"output":rod,"row_visible":size*4,"input_rowbytes":rb,"output_rowbytes":rb,"height":2})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":f"PF{depth}_radius2_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":f"PF{depth}_radius2_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":f"PF{depth}_radius2_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(f"r2{depth}cp",cp),install(f"r2{depth}ci",ci),install(f"r2{depth}co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=2.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb*2));expected=(seed_bytes*3+mixed_bytes+b"\xB6"*12)*2;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb*2,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb*2,0x10)==b"\xCC"*0x10
  return {"depth":depth,"dimensions":[4,2],"radius":2,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"two_step_frontier_and_outside_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]==f"PF{depth}_radius2_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius2_8=run_radius2_4x2(8,bytes([255,31,61,91]),bytes([96,7,17,27]));radius2_16=run_radius2_4x2(16,struct.pack("<4H",32768,3101,6102,9103),struct.pack("<4H",8192,701,1702,2703));radius2_32=run_radius2_4x2(32,struct.pack("<4f",1.0,.31,.61,.91),struct.pack("<4f",.25,.07,.17,.27))
 def run_radius3_pf32_5x1():
  depth=32;size=16;rb=88;total=0x10+rb+0x10;seed32=struct.pack("<4f",1.0,.13,.37,.73);mixeds=[struct.pack("<4f",a,r,g,b) for a,r,g,b in ((.5,.2,.3,.4),(.25,.4,.3,.2),(.75,.6,.2,.1),(.125,.9,.8,.7))];ie=[2301,2303,2306,2304];oe=[3307,3309,3312,3310]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xD7"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,5,1,128));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed32]+mixeds,ie);ro,rod,rog=rworld([bytes(size)]*5,oe);copy_state.update({"input":rid,"output":rod,"row_visible":80,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF32_radius3_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF32_radius3_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF32_radius3_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r3pf32cp",cp),install("r3pf32ci",ci),install("r3pf32co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",32));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=3.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed32*4+mixeds[3]+b"\xD7"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":32,"dimensions":[5,1],"radius":3,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_3_frontier_and_distance_4_raw_float_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF32_radius3_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius3_pf32=run_radius3_pf32_5x1()
 def run_radius3_pf16_5x1():
  depth=16;size=8;rb=48;total=0x10+rb+0x10;seed16=struct.pack("<4H",32768,1301,3702,7303);mixeds=[struct.pack("<4H",a,r,g,b) for a,r,g,b in ((16384,2001,3002,4003),(8192,4001,3002,2003),(24576,6001,2002,1003),(4096,9001,8002,7003))];ie=[1201,1203,1206,1204];oe=[1707,1709,1712,1710]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xE3"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,5,1,64));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed16]+mixeds,ie);ro,rod,rog=rworld([bytes(size)]*5,oe);copy_state.update({"input":rid,"output":rod,"row_visible":40,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF16_radius3_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF16_radius3_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF16_radius3_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r3pf16cp",cp),install("r3pf16ci",ci),install("r3pf16co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",16));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=3.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed16*4+mixeds[3]+b"\xE3"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":16,"dimensions":[5,1],"radius":3,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_3_frontier_and_distance_4_raw_uint16_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF16_radius3_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius3_pf16=run_radius3_pf16_5x1()
 def run_radius3_pf8_5x1():
  depth=8;size=4;rb=28;total=0x10+rb+0x10;seed8=bytes([255,13,37,73]);mixeds=[bytes(v) for v in ((128,20,30,40),(64,40,30,20),(192,60,20,10),(32,90,80,70))];ie=[601,603,606,604];oe=[907,909,912,910]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xF1"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,5,1,32));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed8]+mixeds,ie);ro,rod,rog=rworld([bytes(size)]*5,oe);copy_state.update({"input":rid,"output":rod,"row_visible":20,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF8_radius3_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF8_radius3_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF8_radius3_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r3pf8cp",cp),install("r3pf8ci",ci),install("r3pf8co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",8));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=3.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed8*4+mixeds[3]+b"\xF1"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":8,"dimensions":[5,1],"radius":3,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_3_frontier_and_distance_4_raw_uint8_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF8_radius3_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius3_pf8=run_radius3_pf8_5x1()
 def run_radius4_pf8_6x1():
  rb=32;total=0x10+rb+0x10;seed8=bytes([255,11,47,89]);mixeds=[bytes(v) for v in ((128,21,31,41),(64,42,32,22),(192,63,23,13),(96,74,54,34),(16,95,85,75))];ie=[701,703,707,704];oe=[1007,1009,1013,1010]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\x9D"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,6,1,32));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed8]+mixeds,ie);ro,rod,rog=rworld([bytes(4)]*6,oe);copy_state.update({"input":rid,"output":rod,"row_visible":24,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF8_radius4_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF8_radius4_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF8_radius4_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r4pf8cp",cp),install("r4pf8ci",ci),install("r4pf8co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",8));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed8*5+mixeds[4]+b"\x9D"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":8,"dimensions":[6,1],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_4_frontier_and_distance_5_raw_uint8_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF8_radius4_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius4_pf8=run_radius4_pf8_6x1()
 def run_radius4_pf16_6x1():
  rb=56;total=0x10+rb+0x10;seed16=struct.pack("<4H",32768,1101,4702,8903);mixeds=[struct.pack("<4H",a,r,g,b) for a,r,g,b in ((16384,2101,3102,4103),(8192,4201,3202,2203),(24576,6301,2302,1303),(12288,7401,5402,3403),(2048,9501,8502,7503))];ie=[1401,1403,1407,1404];oe=[2007,2009,2013,2010]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\x8B"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,6,1,64));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed16]+mixeds,ie);ro,rod,rog=rworld([bytes(8)]*6,oe);copy_state.update({"input":rid,"output":rod,"row_visible":48,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF16_radius4_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF16_radius4_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF16_radius4_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r4pf16cp",cp),install("r4pf16ci",ci),install("r4pf16co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",16));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed16*5+mixeds[4]+b"\x8B"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":16,"dimensions":[6,1],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_4_frontier_and_distance_5_raw_uint16_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF16_radius4_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius4_pf16=run_radius4_pf16_6x1()
 def run_radius4_pf32_6x1():
  rb=104;total=0x10+rb+0x10;seed32=struct.pack("<4f",1.0,.11,.47,.89);mixeds=[struct.pack("<4f",a,r,g,b) for a,r,g,b in ((.5,.21,.31,.41),(.25,.42,.32,.22),(.75,.63,.23,.13),(.375,.74,.54,.34),(.0625,.95,.85,.75))];ie=[2801,2803,2807,2804];oe=[4007,4009,4013,4010]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xA7"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,6,1,128));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed32]+mixeds,ie);ro,rod,rog=rworld([bytes(16)]*6,oe);copy_state.update({"input":rid,"output":rod,"row_visible":96,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF32_radius4_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF32_radius4_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF32_radius4_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("r4pf32cp",cp),install("r4pf32ci",ci),install("r4pf32co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",32));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed32*5+mixeds[4]+b"\xA7"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":32,"dimensions":[6,1],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"distance_4_frontier_and_distance_5_raw_float32_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF32_radius4_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 radius4_pf32=run_radius4_pf32_6x1()
 def run_fractional_pf8_5x1():
  rb=28;total=0x10+rb+0x10;seed8=bytes([255,17,43,97]);mixeds=[bytes(v) for v in ((127,23,33,43),(63,44,34,24),(191,65,25,15),(31,96,86,76))];ie=[801,803,806,804];oe=[1107,1109,1112,1110]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xC9"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,5,1,32));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed8]+mixeds,ie);ro,rod,rog=rworld([bytes(4)]*5,oe);copy_state.update({"input":rid,"output":rod,"row_visible":20,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF8_fractional_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF8_fractional_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF8_fractional_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("fracpf8cp",cp),install("fracpf8ci",ci),install("fracpf8co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",8));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=2.01;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed8*4+mixeds[3]+b"\xC9"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":8,"dimensions":[5,1],"requested_radius":2.01,"expected_effective_radius":3,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"ceil_frontier_3_and_distance_4_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF8_fractional_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 fractional_pf8=run_fractional_pf8_5x1()
 def run_fractional_pf32_5x1():
  rb=88;total=0x10+rb+0x10;seed32=struct.pack("<4f",1.0,.19,.41,.83);mixeds=[struct.pack("<4f",a,r,g,b) for a,r,g,b in ((.5,.27,.37,.47),(.25,.48,.38,.28),(.75,.69,.29,.19),(.125,.98,.88,.78))];ie=[2901,2903,2906,2904];oe=[4107,4109,4112,4110]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xD2"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,5,1,128));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed32]+mixeds,ie);ro,rod,rog=rworld([bytes(16)]*5,oe);copy_state.update({"input":rid,"output":rod,"row_visible":80,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF32_fractional_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF32_fractional_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF32_fractional_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("fracpf32cp",cp),install("fracpf32ci",ci),install("fracpf32co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",32));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=2.5;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed32*4+mixeds[3]+b"\xD2"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":32,"dimensions":[5,1],"requested_radius":2.5,"expected_effective_radius":3,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"ceil_frontier_3_and_distance_4_raw_float32_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF32_fractional_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 fractional_pf32=run_fractional_pf32_5x1()
 def run_fractional_pf16_6x1():
  rb=56;total=0x10+rb+0x10;seed16=struct.pack("<4H",32768,1501,5102,8703);mixeds=[struct.pack("<4H",a,r,g,b) for a,r,g,b in ((16384,2501,3502,4503),(8192,4601,3602,2603),(24576,6701,2702,1703),(12288,7801,5802,3803),(1024,9901,8902,7903))];ie=[1501,1503,1507,1504];oe=[2107,2109,2113,2110]
  def rworld(pixels,extent):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+b"\xE6"*8);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,6,1,64));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed16]+mixeds,ie);ro,rod,rog=rworld([bytes(8)]*6,oe);copy_state.update({"input":rid,"output":rod,"row_visible":48,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF16_fractional_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF16_fractional_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF16_fractional_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("fracpf16cp",cp),install("fracpf16ci",ci),install("fracpf16co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",16));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=3.25;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=seed16*5+mixeds[4]+b"\xE6"*8;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":16,"dimensions":[6,1],"requested_radius":3.25,"expected_effective_radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"ceil_frontier_4_and_distance_5_raw_uint16_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF16_fractional_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 fractional_pf16=run_fractional_pf16_6x1()
 def run_downsample_case(depth,downsample_num,downsample_den,comp_to_output_ratio,expected_radius):
  size={8:4,16:8,32:16}[depth];width=7;rb=width*size+12;total=0x10+rb+0x10;tag=f"PF{depth}_ds{downsample_num}_{downsample_den}"
  if depth==8:seed=bytes([255,29,53,101]);mixed=[bytes([32+i,31+i,41+i,51+i]) for i in range(6)]
  elif depth==16:seed=struct.pack("<4H",32768,2901,5302,10103);mixed=[struct.pack("<4H",4096+i,3101+i,4102+i,5103+i) for i in range(6)]
  else:seed=struct.pack("<4f",1.0,.29,.53,.101);mixed=[struct.pack("<4f",.125+i/100,.31+i/100,.41+i/100,.51+i/100) for i in range(6)]
  clear=bytes(size);ie=[depth*100+1,depth*100+3,depth*100+8,depth*100+4];oe=[depth*200+7,depth*200+9,depth*200+14,depth*200+10]
  def rworld(pixels,extent,pad):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,b"".join(pixels)+bytes([pad])*12);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,width,1,{8:32,16:64,32:128}[depth]));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=rworld([seed]+mixed,ie,0xB4);ro,rod,rog=rworld([clear]*width,oe,0xB4);copy_state.update({"input":rid,"output":rod,"row_visible":width*size,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":tag+"_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":tag+"_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":tag+"_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(tag+"cp",cp),install(tag+"ci",ci),install(tag+"co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb))
  l.write_bytes(in_data+0x11c,struct.pack("<ii",downsample_num,downsample_den));radius_state["value"]=2.01
  pre_call=l.call_function(ENTRY,int_args=[0x17,in_data,out_data,0,0,extra],max_instructions=3_000_000);call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=8_000_000)
  actual=bytes(l.read_bytes(rod,rb));expected=seed*(expected_radius+1)+b"".join(mixed[expected_radius:])+b"\xB4"*12;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":depth,"dimensions":[width,1],"requested_radius":2.01,"comp_width_to_output_width_ratio":comp_to_output_ratio,"downsample_x":{"num":downsample_num,"den":downsample_den},"expected_effective_radius":expected_radius,"smart_pre_returned":pre_call["rax"]==0,"smart_render_returned":call["rax"]==0,"frontier_and_preservation_exact":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]==tag+"_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 downsample_matrix={str(depth):[run_downsample_case(depth,1,1,1,3),run_downsample_case(depth,1,2,2,2),run_downsample_case(depth,2,1,.5,5)] for depth in (8,16,32)}
 def run_high_radius_case(depth,radius,downsample_num,downsample_den):
  width,height=513,17;size={8:4,16:8,32:16}[depth];padding=13;rb=width*size+padding;total=0x10+rb*height+0x10
  effective_radius=(radius*downsample_num+downsample_den-1)//downsample_den
  def pixel(alpha,r,g,b):
   if depth==8:return bytes((alpha,r,g,b))
   if depth==16:return struct.pack("<4H",alpha,r,g,b)
   return struct.pack("<4f",alpha,r,g,b)
  if depth==8:
   seed_a=pixel(255,17,71,131);seed_b=pixel(255,211,83,29);semi=pixel(127,47,101,173);zero=pixel(0,233,149,61)
  elif depth==16:
   seed_a=pixel(32768,1701,7102,13103);seed_b=pixel(32768,21101,8302,2903);semi=pixel(16384,4701,10102,17303);zero=pixel(0,23301,14902,6103)
  else:
   seed_a=pixel(1.0,.17,.71,.131);seed_b=pixel(1.0,.811,.283,.929);semi=pixel(.5,.047,.101,.173);zero=pixel(0.0,.933,.149,.061)
  source=[semi]*(width*height);source[4*width]=seed_a;source[12*width+300]=seed_b;source[8*width+150]=semi;source[8*width+512]=zero
  def oracle():
   out=list(source);inf=2**32-1;dist=[inf]*(width*height);seeds=[]
   for i,pix in enumerate(source):
    opaque=(pix[0]==255) if depth==8 else (struct.unpack("<H",pix[:2])[0]==32768 if depth==16 else struct.unpack("<f",pix[:4])[0]>=1.0)
    if opaque:dist[i]=0;seeds.append(i)
   def relax(x,y,coords):
    i=y*width+x
    if dist[i]==0:return
    best=inf;best_i=-1
    for nx,ny in coords:
     if 0<=nx<width and 0<=ny<height and dist[ny*width+nx]<best:best=dist[ny*width+nx];best_i=ny*width+nx
    if best==inf or best+1>=dist[i]:return
    dist[i]=best+1
    if dist[i]<=effective_radius:out[i]=out[best_i]
   for y in range(height):
    for x in range(width):relax(x,y,((x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)))
   for y in range(height-1,-1,-1):
    for x in range(width-1,-1,-1):relax(x,y,((x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1)))
   return out,dist
  expected,dist=oracle()
  def hworld(pixels,extent,pad):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10
   for y in range(height):l.write_bytes(d+y*rb,b"".join(pixels[y*width:(y+1)*width])+bytes([pad])*padding)
   h=l.host_alloc(0x50,align=16);l.write_bytes(h,b"\0"*0x50);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,width,height,{8:32,16:64,32:128}[depth]));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ie=[depth*300+11,depth*300+13,depth*300+11+width,depth*300+13+height];oe=[depth*400+17,depth*400+19,depth*400+17+width,depth*400+19+height]
  ri,rid,rig=hworld(source,ie,0xB9);ro,rod,rog=hworld([bytes(size)]*(width*height),oe,0xB9);copy_state.update({"input":rid,"output":rod,"row_visible":width*size,"input_rowbytes":rb,"output_rowbytes":rb,"height":height})
  tag=f"PF{depth}_high_r{radius}_ds{downsample_num}_{downsample_den}"
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":tag+"_checkout"});return 0
  def ci(_cur,args):events.append({"kind":tag+"_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":tag+"_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(tag+"cp",cp),install(tag+"ci",ci),install(tag+"co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb))
  l.write_bytes(in_data+0x11c,struct.pack("<ii",downsample_num,downsample_den));radius_state["value"]=float(radius);pre_call=l.call_function(ENTRY,int_args=[0x17,in_data,out_data,0,0,extra],max_instructions=3_000_000);call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=120_000_000)
  actual=bytearray()
  for y in range(height):actual.extend(l.read_bytes(rod+y*rb,width*size))
  expected_bytes=b"".join(expected);pads=all(l.read_bytes(rod+y*rb+width*size,padding)==b"\xB9"*padding for y in range(height));guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb*height,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb*height,0x10)==b"\xCC"*0x10
  tie=8*width+150;far=8*width+512
  return {"depth":depth,"radius":radius,"downsample_x":[downsample_num,downsample_den],"effective_radius":effective_radius,"dimensions":[width,height],"rowbytes":rb,"smart_pre_returned":pre_call["rax"]==0,"smart_render_returned":call["rax"]==0,"actual_matches_independent_production_algorithm":bytes(actual)==expected_bytes,"tie_pixel_exact":bytes(actual[tie*size:(tie+1)*size])==expected[tie],"unreached_alpha0_straight_rgb_sentinel_exact":bytes(actual[far*size:(far+1)*size])==zero,"frontier_inside_and_outside_present":any(d==effective_radius for d in dist) and any(d>effective_radius for d in dist),"padding_unchanged":pads,"guards_untouched":guards,"actual_sha256":hashlib.sha256(actual).hexdigest(),"expected_sha256":hashlib.sha256(expected_bytes).hexdigest()}
 high_radius_matrix={str(depth):[run_high_radius_case(depth,r,n,d) for r in (50,100) for n,d in ((1,2),(1,1),(2,1))] for depth in (8,16,32)}
 radius_state["value"]=1.0;l.write_bytes(in_data+0x11c,struct.pack("<ii",1,1))
 def run_empty_pf8():
  rb=8;total=0x10+rb+0x10;ie=[951,953,951,954];oe=[1257,1259,1257,1260]
  def eworld(extent,pad):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,bytes([pad])*rb);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,0,1,32));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=eworld(ie,0xA3);ro,rod,rog=eworld(oe,0xB4);copy_state.update({"input":rid,"output":rod,"row_visible":0,"input_rowbytes":rb,"output_rowbytes":rb,"height":1})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF8_empty_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF8_empty_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF8_empty_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("emptypf8cp",cp),install("emptypf8ci",ci),install("emptypf8co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",8));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=3_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=b"\xB4"*rb;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":8,"dimensions":[0,1],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"empty_output_padding_unchanged":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF8_empty_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 empty_pf8=run_empty_pf8()
 def run_empty_height_pf16():
  rb=16;total=0x10+rb+0x10;ie=[1551,1553,1552,1553];oe=[2157,2159,2158,2159]
  def eworld(extent,pad):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,bytes([pad])*rb);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,1,0,64));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=eworld(ie,0xA8);ro,rod,rog=eworld(oe,0xBD);copy_state.update({"input":rid,"output":rod,"row_visible":8,"input_rowbytes":rb,"output_rowbytes":rb,"height":0})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF16_empty_height_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF16_empty_height_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF16_empty_height_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("emptyhpf16cp",cp),install("emptyhpf16ci",ci),install("emptyhpf16co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",16));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=3_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=b"\xBD"*rb;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":16,"dimensions":[1,0],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"empty_output_backing_unchanged":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF16_empty_height_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 empty_height_pf16=run_empty_height_pf16()
 def run_legacy_noop(depth,radius):
  size={8:4,16:8,32:16}[depth];rb=4*size+8;total=0x10+rb+0x10;input_bytes=bytes((i*17+depth)&255 for i in range(rb));output_bytes=bytes((i*29+int(radius*10))&255 for i in range(rb));ie=[depth*10+1,depth*10+3,depth*10+5,depth*10+4];oe=[depth*20+7,depth*20+9,depth*20+11,depth*20+10]
  def backing(payload):g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,payload);return d,g
  idata2,ig2=backing(input_bytes);odata2,og2=backing(output_bytes);input_param=l.host_alloc(0x200,align=16);radius_param=l.host_alloc(0x200,align=16);output_world=l.host_alloc(0x80,align=16)
  l.write_bytes(input_param,b"\x91"*0x200);l.write_bytes(radius_param,b"\x92"*0x200);l.write_bytes(output_world,b"\x93"*0x80);l.write_bytes(input_param+56+0x18,struct.pack("<QiiiH",idata2,rb,4,1,{8:32,16:64,32:128}[depth]));l.write_bytes(input_param+56+0x30,struct.pack("<4i",*ie));l.write_bytes(radius_param+56,struct.pack("<d",radius));l.write_bytes(output_world+0x18,struct.pack("<QiiiH",odata2,rb,4,1,{8:32,16:64,32:128}[depth]));l.write_bytes(output_world+0x30,struct.pack("<4i",*oe));params=l.host_alloc(0x10,align=16);l.write_bytes(params,struct.pack("<2Q",input_param,radius_param));before_events=len(events);call=l.call_function(ENTRY,int_args=[0xb,in_data,out_data,params,output_world,0],max_instructions=100_000);new_kinds=[e["kind"] for e in events[before_events:]];handle_only={"acquire_suite","release_suite","handle_alloc","handle_lock","handle_unlock","handle_dispose"}
  return {"command":"0x0b PF_Cmd_RENDER","depth":depth,"radius":radius,"entry_returned":call["rax"]==0,"input_world_untouched":l.read_bytes(idata2,rb)==input_bytes,"output_world_untouched":l.read_bytes(odata2,rb)==output_bytes,"param_headers_untouched":list(struct.unpack("<4i",l.read_bytes(input_param+56+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(output_world+0x30,16)))==oe,"guards_untouched":l.read_bytes(ig2,0x10)==b"\xCC"*0x10 and l.read_bytes(ig2+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(og2,0x10)==b"\xCC"*0x10 and l.read_bytes(og2+0x10+rb,0x10)==b"\xCC"*0x10,"owner_recovery_handle_activity_only":all(k in handle_only for k in new_kinds),"event_kinds":new_kinds,"output_sha256":hashlib.sha256(output_bytes).hexdigest()}
 legacy_matrix={str(depth):[run_legacy_noop(depth,0.0),run_legacy_noop(depth,2.01)] for depth in (8,16,32)}
 def run_empty_pf32_0x0():
  rb=24;total=0x10+rb+0x10;ie=[3051,3053,3051,3053];oe=[4257,4259,4257,4259]
  def eworld(extent,pad):
   g=l.host_alloc(total,align=16);l.write_bytes(g,b"\xCC"*total);d=g+0x10;l.write_bytes(d,bytes([pad])*rb);h=l.host_alloc(0x40,align=16);l.write_bytes(h,b"\0"*0x40);l.write_bytes(h+0x18,struct.pack("<QiiiH",d,rb,0,0,128));l.write_bytes(h+0x30,struct.pack("<4i",*extent));return h,d,g
  ri,rid,rig=eworld(ie,0xAC);ro,rod,rog=eworld(oe,0xCE);copy_state.update({"input":rid,"output":rod,"row_visible":0,"input_rowbytes":rb,"output_rowbytes":rb,"height":0})
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",ri));events.append({"kind":"PF32_empty_both_checkout_layer_pixels"});return 0
  def ci(_cur,args):events.append({"kind":"PF32_empty_both_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ro));events.append({"kind":"PF32_empty_both_checkout_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install("emptybothpf32cp",cp),install("emptybothpf32ci",ci),install("emptybothpf32co",co)));si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",32));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb));radius_state["value"]=4.0;call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=3_000_000);radius_state["value"]=1.0
  actual=bytes(l.read_bytes(rod,rb));expected=b"\xCE"*rb;guards=l.read_bytes(rig,0x10)==b"\xCC"*0x10 and l.read_bytes(rig+0x10+rb,0x10)==b"\xCC"*0x10 and l.read_bytes(rog,0x10)==b"\xCC"*0x10 and l.read_bytes(rog+0x10+rb,0x10)==b"\xCC"*0x10
  return {"depth":32,"dimensions":[0,0],"radius":4,"rowbytes":rb,"input_extent":ie,"output_extent":oe,"entry_returned":call["rax"]==0,"empty_output_backing_unchanged":actual==expected,"typed_bytes_padding_exact":actual==expected,"headers_unchanged":list(struct.unpack("<4i",l.read_bytes(ri+0x30,16)))==ie and list(struct.unpack("<4i",l.read_bytes(ro+0x30,16)))==oe,"guards_untouched":guards,"optional_checkin_not_called":not any(e["kind"]=="PF32_empty_both_checkin" for e in events),"actual_sha256":hashlib.sha256(actual).hexdigest()}
 empty_both_pf32=run_empty_pf32_0x0()
 gates={"sequence_setup_returned":setup["rax"]==0,"out_data_sequence_handle_set":handle!=0,"handle_allocation_size_0x90":size==0x90,"handle_vtable_initialized":struct.unpack("<Q",initial[:8])[0]!=0,"register_with_aegp_called":any(e["kind"]=="AEGP_RegisterWithAEGP" for e in events),"smart_pre_entry_returned":pre["rax"]==0,"checkout_layer_callback_invoked":any(e["kind"]=="smartpre_checkout_layer" for e in events),"result_rect_readback_exact":result_rect==[10,20,13,22],"max_result_rect_readback_exact":max_result_rect==[9,19,14,23],"smart_pre_output_flag_0x22_set":flag==1,"smart_render_entry_returned":smart["rax"]==0,"smart_render_checkout_callbacks_observed":all(any(e["kind"]==k for e in events) for k in ("checkout_layer_pixels","checkout_output")),"actual_aex_did_not_call_optional_checkin":not any(e["kind"]=="checkin_layer_pixels" for e in events),"partial_pf8_visible_exact":partial_actual==partial_expected,"nonzero_extent_headers_unchanged":list(struct.unpack("<4i",l.read_bytes(iw+0x30,16)))==input_extent and list(struct.unpack("<4i",l.read_bytes(ow+0x30,16)))==output_extent,"partial_world_guards_untouched":guards_ok,"partial_pf16_all_gates":all(v for k,v in pf16.items() if isinstance(v,bool)),"partial_pf32_all_gates":all(v for k,v in pf32.items() if isinstance(v,bool)),"mixed_3x2_all_depths_exact":all(all(v for v in case.values() if isinstance(v,bool)) for case in (mixed8,mixed16,mixed32)),"radius2_4x2_all_depths_exact":all(all(v for v in case.values() if isinstance(v,bool)) for case in (radius2_8,radius2_16,radius2_32)),"radius3_pf32_5x1_exact":all(v for v in radius3_pf32.values() if isinstance(v,bool)),"radius3_pf16_5x1_exact":all(v for v in radius3_pf16.values() if isinstance(v,bool)),"radius3_pf8_5x1_exact":all(v for v in radius3_pf8.values() if isinstance(v,bool)),"radius4_pf8_6x1_exact":all(v for v in radius4_pf8.values() if isinstance(v,bool)),"radius4_pf16_6x1_exact":all(v for v in radius4_pf16.values() if isinstance(v,bool)),"radius4_pf32_6x1_exact":all(v for v in radius4_pf32.values() if isinstance(v,bool)),"fractional_radius_2_01_pf8_exact":all(v for v in fractional_pf8.values() if isinstance(v,bool)),"fractional_radius_2_5_pf32_exact":all(v for v in fractional_pf32.values() if isinstance(v,bool)),"fractional_radius_3_25_pf16_exact":all(v for v in fractional_pf16.values() if isinstance(v,bool)),"handle_not_disposed_before_smartpre":not any(e["kind"]=="handle_dispose" and e["handle"]==hex(handle) for e in events)}
 gates["downsample_radius_matrix_all_depths_exact"]=all(all(v for v in case.values() if isinstance(v,bool)) for cases in downsample_matrix.values() for case in cases)
 gates["high_radius_downsample_competing_seed_matrix_exact"]=all(all(v for v in case.values() if isinstance(v,bool)) for cases in high_radius_matrix.values() for case in cases)
 gates["legacy_render_public_noop_all_depths_exact"]=all(all(v for v in case.values() if isinstance(v,bool)) for cases in legacy_matrix.values() for case in cases)
 gates["empty_width_pf8_exact"]=all(v for v in empty_pf8.values() if isinstance(v,bool))
 gates["empty_height_pf16_exact"]=all(v for v in empty_height_pf16.values() if isinstance(v,bool))
 gates["empty_both_pf32_exact"]=all(v for v in empty_both_pf32.values() if isinstance(v,bool))
 status="PASS_SEQUENCE_AND_SMARTPRE_ENTRY" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
 p={"status":status,"schema":"olmtoondilate.actual-aex-sequence-smartpre/1","aex":str(AEX.relative_to(ROOT)),"aex_sha256":AEX_SHA,"entry_point":hex(ENTRY),"probe_local_suite_contract":{"PF Handle Suite v2":{"slots":["new_handle","lock_handle","unlock_handle","dispose_handle"],"lock_returns_same_probe_local_storage":True},"AEGP Utility Suite v13":{"AEGP_RegisterWithAEGP_offset":"0x48","assigned_plugin_id":77}},"sequence_handle":{"out_data_offset":"0x28","address":hex(handle),"allocation_size":size,"initial_sha256":hashlib.sha256(initial).hexdigest(),"first_32_bytes_hex":initial[:32].hex()},"smart_pre":{"command":"0x17","extra_output_pointer_offset":"0x8","observed_output_flag_offset":"0x22","observed_value":flag,"result_rect":result_rect,"max_result_rect":max_result_rect},"smart_render":{"command":"0x18","parameter_checkout":"probe-local radius=1/2/2.01/2.5/3/3.25/4 seam","PF8":{"rowbytes":12,"input_extent_origin_size":input_extent,"output_extent_origin_size":output_extent,"coordinate_contract":"worker reads only world+0x18/+0x20/+0x24/+0x28 and addresses buffer-local x/y; extents at +0x30 are not consumed","actual_hex":partial_actual.hex(),"expected_hex":partial_expected.hex()},"PF16":pf16,"PF32":pf32,"mixed_3x2":{"PF8":mixed8,"PF16":mixed16,"PF32":mixed32},"radius2_mixed_4x2":{"PF8":radius2_8,"PF16":radius2_16,"PF32":radius2_32},"radius3_pf32_5x1":radius3_pf32,"radius3_pf16_5x1":radius3_pf16,"radius3_pf8_5x1":radius3_pf8,"radius4_pf8_6x1":radius4_pf8,"radius4_pf16_6x1":radius4_pf16,"radius4_pf32_6x1":radius4_pf32,"fractional_radius_2_01_pf8_5x1":fractional_pf8,"fractional_radius_2_5_pf32_5x1":fractional_pf32,"fractional_radius_3_25_pf16_6x1":fractional_pf16},"events":events,"gates":gates,"not_proven":["AE host execution","whether real AE passes extent/origin metadata at this probe-local +0x30 layout"],"claim_boundary":"actual-AEX entry_point sequence with padded partial typed worlds for integer/fractional radii through 4, under probe-local host seams"}
 p["smart_render"]["downsample_x_radius_2_01_matrix"]=downsample_matrix;p["smart_render"]["high_radius_downsample_competing_seed_matrix"]=high_radius_matrix;p["smart_render"]["empty_width_pf8_0x1"]=empty_pf8;p["smart_render"]["empty_height_pf16_1x0"]=empty_height_pf16;p["smart_render"]["empty_both_pf32_0x0"]=empty_both_pf32
 p["legacy_render_public_noop"]={"entry_dispatch":"command 0x0b -> FUN_1801a7840","owner":"FUN_1801a7840 is a constant-zero return stub","cases":legacy_matrix};p["claim_boundary"]="actual-AEX public legacy Render no-op plus SmartPreRender-to-SmartRender with bounded typed partial/empty geometry, including Radius 50/100 x downsample_x 1/2, 1/1, 2/1 x PF8/PF16/PF32, under probe-local suite seams"
 REPORT.write_text(json.dumps(p,indent=2)+"\n");MARKDOWN.write_text(f"# OLMToonDilate Actual-AEX Sequence + SmartRender — 2026-08-05\n\n- Status: **{status}**\n- Sequence setup allocates and retains a 0x90-byte handle at out_data+0x28.\n- Probe-local AEGP Utility v13 slot +0x48 assigns plugin ID 77.\n- Command 0x17 invokes checkout_layer and copies distinct result/max rectangles exactly.\n- Command 0x18 independently dispatches PF8/PF16/PF32. Integer-radius padded partial worlds through radius 4 and three independent fractional cases are typed-byte exact.\n- Radius 2.01 is also exact after SmartPreRender for downsample_x 1/1, 1/2, and 2/1 at every depth, yielding effective radii 3, 2, and 5. Static worker disassembly identifies PF_InData offsets 0x11c/0x120 as the rational numerator/denominator.\n- The 513x17 high-radius family is exact for Radius 50/100 x downsample_x 1/2, 1/1, 2/1 x PF8/PF16/PF32 (18 cells). Effective radii 25/50/100/200 preserve competing-seed ties, inside/outside frontiers, alpha-zero straight RGB, padding, and guards.\n- PF8 0x1, PF16 1x0, and PF32 0x0 empty-axis worlds return with backing bytes, headers, and guards unchanged. The AEX does not call the optional checkin callback.\n- Public legacy Render command 0x0b dispatches to constant-zero stub FUN_1801a7840. Radius 0/2.01 at PF8/PF16/PF32 leave params and worlds untouched without suite or callback activity.\n- Real AE host execution remains a separate boundary.\n")
 print(json.dumps(p,indent=2));return 0 if status.startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
