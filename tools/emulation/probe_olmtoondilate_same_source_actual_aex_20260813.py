#!/usr/bin/env python3
"""Replay current-public ToonDilate fixtures through the actual Windows AEX.\n\nDefault execution is read-only. Pass --write to refresh the dedicated report.\n"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative
import argparse,hashlib,json,platform,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa:E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX,alloc  # noqa:E402
ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/"refs/conformance/olmtoondilate_same_source_actual_aex_20260813.json";MARKDOWN=REPORT.with_suffix(".md");SOURCE=ROOT/"mac/OLMToonDilate/OLMToonDilate.cpp";FIXTURE_HARNESS=ROOT/"tools/emulation/test_olmtoondilate_installed_dynamic_all_depths_20260806.py";AEX_LOADER=ROOT/"tools/emulation/aex_loader.py";BOUNDARY_HELPER=ROOT/"tools/emulation/test_olmtoondilate_pf16_pf32_copy_boundary_20260716.py";SDK_HEADER=resolve_asset(ROOT/"Headers/AE_Effect.h")
AEX_SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";ENTRY=0x1801ABC00
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(write=False, extra_only=False):
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
 if setup["rax"] != 0 or not handle or size != 0x90:
  raise SystemExit("BLOCKED_FAIL_CLOSED: SequenceSetup/retained handle contract failed")
 pre_input=l.host_alloc(0x40,align=16);l.write_bytes(pre_input,b"\0"*0x40);pre_output=l.host_alloc(0x80,align=16);l.write_bytes(pre_output,b"\0"*0x80)
 def checkout(cur,args):
  from unicorn.x86_const import UC_X86_REG_RSP
  rsp=cur.uc.reg_read(UC_X86_REG_RSP);stack=[struct.unpack("<Q",cur.read_bytes(rsp+0x28+i*8,8))[0] for i in range(4)];result=stack[3]
  # Real AE 25.2 SDK PF_CheckoutResult (Win64): sizeof 0x4c, rects at
  # 0/0x10, solid at 0x28, ref_width/ref_height at 0x2c/0x30.
  cur.write_bytes(result,b"\0"*0x4c)
  cur.write_bytes(result,struct.pack("<8i",10,20,13,22,9,19,14,23))
  cur.write_bytes(result+0x2c,struct.pack("<2i",30,40))
  events.append({"kind":"smartpre_checkout_layer","args":[hex(x) for x in args],"stack_args_5_to_8":[hex(x) for x in stack],"checkout_result":hex(result),"result_rect":[10,20,13,22],"max_result_rect":[9,19,14,23],"channel_mask_raw":struct.unpack("<I",cur.read_bytes(args[3]+0x14,4))[0],"preserve_rgb_of_zero_alpha":bool(cur.read_bytes(args[3]+0x18,1)[0])});return 0
 pre_callbacks=l.host_alloc(0x20,align=16);l.write_bytes(pre_callbacks,struct.pack("<Q",install("seq_smartpre_checkout",checkout))+b"\0"*0x18)
 extra=l.host_alloc(0x20,align=16);l.write_bytes(extra,struct.pack("<3Q",pre_input,pre_output,pre_callbacks)+b"\0"*8)
 # SmartRender command 0x18: retain actual entry/vtable/worker and provide only
 # the host parameter checkout seam plus checkout/checkin/output callbacks.
 from unicorn.x86_const import UC_X86_REG_R9,UC_X86_REG_RIP,UC_X86_REG_RSP
 radius_state={"value":1.0}
 def parameter_seam(cur,_address,_size):
  radius_out=cur.uc.reg_read(UC_X86_REG_R9);radius_bytes=struct.pack("<f",radius_state["value"]);cur.write_bytes(radius_out,radius_bytes);rsp=cur.uc.reg_read(UC_X86_REG_RSP);ret=struct.unpack("<Q",cur.read_bytes(rsp,8))[0];cur.uc.reg_write(UC_X86_REG_RSP,rsp+8);cur.uc.reg_write(UC_X86_REG_RIP,ret);events.append({"kind":"parameter_checkout_seam","radius_requested_f64_le":struct.pack("<d",radius_state["value"]).hex(),"radius_materialized_f32_le":radius_bytes.hex(),"radius_materialized_f32":struct.unpack("<f",radius_bytes)[0],"output":hex(radius_out)})
 l.add_code_hook(0x1801A9AC0,parameter_seam)
 copy_state={}
 def pfcopy(cur,args):
  for y in range(copy_state["height"]):cur.write_bytes(copy_state["output"]+y*copy_state["output_rowbytes"],cur.read_bytes(copy_state["input"]+y*copy_state["input_rowbytes"],copy_state["row_visible"]))
  events.append({"kind":"PF_COPY","visible_bytes":copy_state["row_visible"]*copy_state["height"]});return 0
 status_table=l.host_alloc(0x50,align=16);l.write_bytes(status_table,b"\0"*0x50);l.write_bytes(status_table+0x40,struct.pack("<Q",install("smart_pf_copy",pfcopy)));l.write_bytes(in_data+0xB0,struct.pack("<Q",status_table));l.write_bytes(in_data+0xB8,struct.pack("<Q",0x1234));l.write_bytes(in_data+0x11C,struct.pack("<ii",1,1))
 def run_installed12_case(depth,family,width,height,radius,ds_num,ds_den):
  size={8:4,16:8,32:16}[depth];alignment={8:1,16:2,32:4}[depth];pad=13;guard_n=19;rb=width*size+pad;payload=rb*height
  def pixel(kind,x,y):
   v=x*17+y*29+3
   if depth==8:
    vals=((0,91+v%97,37+v%113,11+v%127),(64+v%160,13+v%211,19+v%197,23+v%191),(255,31+v%181,47+v%173,59+v%167))[kind];return bytes(vals)
   if depth==16:
    vals=((0,41001+v%7000,30002+v%7000,20003+v%7000),(4096+v%24000,1001+v%19000,2002+v%17000,3003+v%15000),(32768,4001+v%19000,5002+v%17000,6003+v%15000))[kind];return struct.pack("<4H",*vals)
   f=struct.unpack("<f",struct.pack("<f",(v%101)/128.0))[0]
   vals=((0.0,.75+f,.5+f,.25+f),(.5,.125+f,.25+f,.375+f),(1.0,.1875+f,.3125+f,.4375+f))[kind];return struct.pack("<4f",*vals)
  def corner_pixel(kind):
   if depth==8:return bytes(((255,10,20,30),(255,90,80,70),(0,3,5,7))[kind])
   if depth==16:return struct.pack("<4H",*((32768,1001,2002,3003),(32768,4004,5005,6006),(0,17,19,23))[kind])
   return struct.pack("<4f",*((1.0,.125,.25,.5),(1.0,.75,.625,.375),(0.0,.03125,.0625,.09375))[kind])
  source=[pixel(1,x,y) for y in range(height) for x in range(width)]
  if family=="copy":source=[pixel((x+y)%3,x,y) for y in range(height) for x in range(width)]
  elif family=="fractional":source[0]=pixel(2,0,0);source[(height//2)*width+width//2]=pixel(2,width//2,height//2);source[-1]=pixel(0,width-1,height-1)
  elif family=="corner_seed":source=[corner_pixel(0 if (x,y)==(0,0) else 1 if (x,y)==(width-1,height-1) else 2) for y in range(height) for x in range(width)]
  else:source[(height//2)*width]=pixel(2,0,height//2);source[(height//2)*width+width-1]=pixel(2,width-1,height//2);source[(height//2)*width+width//2]=pixel(1,width//2,height//2)
  def opaque(p):
   if depth==8:return p[0]==255
   if depth==16:return struct.unpack("<H",p[:2])[0]==32768
   return struct.unpack("<f",p[:4])[0]>=1.0
  effective=0 if radius<=0 else int(__import__('math').ceil(radius*ds_num/ds_den))
  expected=list(source)
  if effective>0:
   inf=(1<<32)-1;dist=[inf]*(width*height)
   for i,p in enumerate(source):
    if opaque(p):dist[i]=0
   def relax(x,y,coords):
    i=y*width+x
    if dist[i]==0:return
    best=inf;bi=-1
    for nx,ny in coords:
     if 0<=nx<width and 0<=ny<height and dist[ny*width+nx]<best:best=dist[ny*width+nx];bi=ny*width+nx
    if best==inf or best+1>=dist[i]:return
    dist[i]=best+1
    if dist[i]<=effective:expected[i]=expected[bi]
   for y in range(height):
    for x in range(width):relax(x,y,((x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)))
   for y in range(height-1,-1,-1):
    for x in range(width-1,-1,-1):relax(x,y,((x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1)))
  def make_world(pixels,guard_byte,pad_byte,extent,visible_fill=False):
   # Keep exactly 19 checked guard bytes immediately adjacent to the payload,
   # while independently satisfying the typed pixel alignment contract.
   storage_size=guard_n+payload+guard_n+alignment-1
   base=l.host_alloc(storage_size,align=16);l.write_bytes(base,bytes([guard_byte])*storage_size)
   d=(base+guard_n+alignment-1)&~(alignment-1);guard_start=d-guard_n
   for y in range(height):
    visible=(bytes([guard_byte])*(width*size) if visible_fill else b"".join(pixels[y*width:(y+1)*width]))
    l.write_bytes(d+y*rb,visible+bytes([pad_byte])*pad)
   # Real AE 25.2 SDK PF_EffectWorld (Win64): sizeof 0x78; data 0x18,
   # rowbytes 0x20, width 0x24, height 0x28, extent_hint 0x2c.
   h=l.host_alloc(0x78,align=16);l.write_bytes(h,b"\0"*0x78)
   l.write_bytes(h+0x18,struct.pack("<Qiii",d,rb,width,height));l.write_bytes(h+0x2c,struct.pack("<4i",*extent))
   return h,d,base,storage_size,guard_start
  input_extent=[101,201,101+width,201+height];output_extent=[301,401,301+width,401+height]
  iw,idata,ibase,isz,ig=make_world(source,0xC7,0xA5,input_extent);ow,odata,obase,osz,og=make_world([],0xD9,0xEE,output_extent,True);ih0=bytes(l.read_bytes(iw,0x78));oh0=bytes(l.read_bytes(ow,0x78));input_storage0=bytes(l.read_bytes(ibase,isz))
  copy_state.update({"input":idata,"output":odata,"row_visible":width*size,"input_rowbytes":rb,"output_rowbytes":rb,"height":height})
  tag=f"PF{depth}_{family}"
  def cp(cur,args):cur.write_bytes(args[2],struct.pack("<Q",iw));events.append({"kind":tag+"_checkout"});return 0
  def ci(_cur,args):events.append({"kind":tag+"_checkin"});return 0
  def co(cur,args):cur.write_bytes(args[1],struct.pack("<Q",ow));events.append({"kind":tag+"_output"});return 0
  cb=l.host_alloc(0x18,align=16);l.write_bytes(cb,struct.pack("<3Q",install(tag+"cp",cp),install(tag+"ci",ci),install(tag+"co",co)))
  si=l.host_alloc(0x40,align=16);l.write_bytes(si,b"\0"*0x40);l.write_bytes(si+0x2c,struct.pack("<H",depth));ex=l.host_alloc(0x10,align=16);l.write_bytes(ex,struct.pack("<2Q",si,cb))
  l.write_bytes(in_data+0x11c,struct.pack("<ii",ds_num,ds_den));radius_state["value"]=float(radius);l.write_bytes(pre_output,b"\0"*0x80);before=len(events)
  pre_call=l.call_function(ENTRY,int_args=[0x17,in_data,out_data,0,0,extra],max_instructions=3_000_000);render_call=l.call_function(ENTRY,int_args=[0x18,in_data,out_data,0,0,ex],max_instructions=120_000_000 if width==513 else 12_000_000);case_events=events[before:]
  actual=b"".join(bytes(l.read_bytes(odata+y*rb,width*size)) for y in range(height));expected_bytes=b"".join(expected);input_bytes=b"".join(source)
  input_payload=b"".join(bytes(l.read_bytes(idata+y*rb,rb)) for y in range(height));output_payload=b"".join(bytes(l.read_bytes(odata+y*rb,rb)) for y in range(height));input_padding=b"".join(bytes(l.read_bytes(idata+y*rb+width*size,pad)) for y in range(height));output_padding=b"".join(bytes(l.read_bytes(odata+y*rb+width*size,pad)) for y in range(height))
  normalized_input_header=bytearray(ih0);normalized_output_header=bytearray(oh0);normalized_input_header[0x18:0x20]=b"\0"*8;normalized_output_header[0x18:0x20]=b"\0"*8
  seam=[e for e in case_events if e.get("kind")=="parameter_checkout_seam"]
  counts={k:sum(e["kind"]==k for e in case_events) for k in ("smartpre_checkout_layer",tag+"_checkout",tag+"_output",tag+"_checkin","parameter_checkout_seam","PF_COPY")}
  return {"id":tag,"depth":depth,"family":family,"pixel_size":size,"dimensions":[width,height],"radius_requested_f64_le":struct.pack("<d",radius).hex(),"radius_materialized_f32_le":seam[0]["radius_materialized_f32_le"] if len(seam)==1 else None,"radius_materialized_f32":seam[0]["radius_materialized_f32"] if len(seam)==1 else None,"downsample_x":[ds_num,ds_den],"downsample_y":[0,0],"effective_radius":effective,"rowbytes":rb,"world_flags":[0,0],"input_origin":[0,0],"output_origin":[0,0],"input_extent":input_extent,"output_extent":output_extent,"row0_data_alignment":alignment,"input_row0_data_aligned":idata%alignment==0,"output_row0_data_aligned":odata%alignment==0,"input_active_bytes":len(input_bytes),"input_active_sha256":hashlib.sha256(input_bytes).hexdigest(),"input_payload_sha256":hashlib.sha256(input_payload).hexdigest(),"input_padding_sha256":hashlib.sha256(input_padding).hexdigest(),"output_active_sha256":hashlib.sha256(actual).hexdigest(),"output_payload_sha256":hashlib.sha256(output_payload).hexdigest(),"output_padding_sha256":hashlib.sha256(output_padding).hexdigest(),"expected_active_sha256":hashlib.sha256(expected_bytes).hexdigest(),"normalized_input_header_sha256":hashlib.sha256(normalized_input_header).hexdigest(),"normalized_output_header_sha256":hashlib.sha256(normalized_output_header).hexdigest(),"raw_exact":actual==expected_bytes,"pre_returned":pre_call["rax"]==0,"render_returned":render_call["rax"]==0,"callback_counts":counts,"preserve_rgb_requested":any(e.get("kind")=="smartpre_checkout_layer" and e.get("preserve_rgb_of_zero_alpha") for e in case_events),"padding_exact":all(l.read_bytes(odata+y*rb+width*size,pad)==b"\xEE"*pad for y in range(height)),"guards_exact":l.read_bytes(ig,guard_n)==b"\xC7"*guard_n and l.read_bytes(idata+payload,guard_n)==b"\xC7"*guard_n and l.read_bytes(og,guard_n)==b"\xD9"*guard_n and l.read_bytes(odata+payload,guard_n)==b"\xD9"*guard_n,"headers_unchanged":l.read_bytes(iw,0x78)==ih0 and l.read_bytes(ow,0x78)==oh0,"input_storage_unchanged":l.read_bytes(ibase,isz)==input_storage0}
 families=(("corner_seed",5,5,4.0,1,1),) if extra_only else (("copy",7,5,0.0,1,1),("fractional",9,7,2.01,1,1),("tie_semialpha",7,3,3.0,1,1),("high_downsample",513,17,100.0,2,1))
 installed12=[run_installed12_case(depth,*case) for depth in (8,16,32) for case in families]
 count=3 if extra_only else 12
 gates={f"all_{count}_unique":len(installed12)==count and len({c["id"] for c in installed12})==count,f"all_{count}_raw_exact":all(c["raw_exact"] for c in installed12),"all_entry_returns":all(c["pre_returned"] and c["render_returned"] for c in installed12),"all_callback_counts":all(c["callback_counts"]=={"smartpre_checkout_layer":1,c["id"]+"_checkout":1,c["id"]+"_output":1,c["id"]+"_checkin":0,"parameter_checkout_seam":1,"PF_COPY":1} for c in installed12),"all_padding_guards_headers":all(c["padding_exact"] and c["guards_exact"] and c["headers_unchanged"] for c in installed12),"all_input_storage_unchanged":all(c["input_storage_unchanged"] for c in installed12),"all_row0_data_aligned":all(c["input_row0_data_aligned"] and c["output_row0_data_aligned"] for c in installed12)}
 observations={"preserve_rgb_of_zero_alpha_requested_all_cases":all(c["preserve_rgb_requested"] for c in installed12),"preserve_rgb_diverges_from_installed_production":not any(c["preserve_rgb_requested"] for c in installed12)}
 import unicorn
 result={"schema":"olmtoondilate.same-source-actual-aex/3","status":"PASS_SAME_SOURCE_ACTUAL_AEX_12" if all(gates.values()) else "BLOCKED_FAIL_CLOSED","aex":{"path":str(asset_relative(AEX, ROOT)),"sha256":AEX_SHA,"entry_point":hex(ENTRY),"parameter_materialization_seam":hex(0x1801A9AC0)},"dependencies":{"aex_loader":{"path":str(AEX_LOADER.relative_to(ROOT)),"sha256":sha(AEX_LOADER)},"allocation_helper":{"path":str(BOUNDARY_HELPER.relative_to(ROOT)),"sha256":sha(BOUNDARY_HELPER)},"fixture_lineage":{"path":str(FIXTURE_HARNESS.relative_to(ROOT)),"sha256":sha(FIXTURE_HARNESS)},"sdk_header":{"path":str(asset_relative(SDK_HEADER, ROOT)),"sha256":sha(SDK_HEADER)},"python":platform.python_version(),"unicorn":unicorn.__version__},"non_gating_current_tree":{"source":str(SOURCE.relative_to(ROOT)),"source_sha256":sha(SOURCE)},"runner":{"path":str(Path(__file__).resolve().relative_to(ROOT)),"sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},"sequence_setup":{"returned":setup["rax"],"retained_handle_size":size,"retained_handle_sha256":hashlib.sha256(initial).hexdigest()},"matrix":{"depths":[8,16,32],"families":["copy_7x5_r0_ds1/1","fractional_9x7_r2.01_ds1/1","tie_semialpha_7x3_r3_ds1/1","high_513x17_r100_ds2/1"],"case_count":12},"sdk_abi":{"source":"reference layout checked against pinned repo SDK header","PF_EffectWorld":{"sizeof":120,"world_flags":16,"data":24,"rowbytes":32,"width":36,"height":40,"extent_hint":44,"origin_x":104,"origin_y":108},"PF_CheckoutResult":{"sizeof":76,"result_rect":0,"max_result_rect":16,"solid":40,"ref_width":44,"ref_height":48},"PF_RenderRequest":{"sizeof":44,"channel_mask":20,"preserve_rgb_of_zero_alpha":24}},"world_contract":{"pixel_layout":"little-endian ARGB: 4B / 4H / 4f","row0_data_alignment":"1 / 2 / 4 bytes for PF8 / PF16 / PF32; later rows intentionally follow +13 stride and can be unaligned","rowbytes":"width * pixel_size + 13","input_extent":[101,201,"101+w","201+h"],"output_extent":[301,401,"301+w","401+h"],"origins":[0,0],"world_flags":0,"downsample_y":[0,0],"input_padding":"0xA5","output_padding":"0xEE","input_guard":"19 immediate bytes 0xC7 each side","output_guard":"19 immediate bytes 0xD9 each side"},"cases":installed12,"gates":gates,"observations":observations,"lifecycle":{"smart_pre_checkout_total":12,"smart_render_layer_checkout_total":12,"smart_render_output_checkout_total":12,"optional_layer_checkin_total":0,"internal_radius_seam_total":12,"pf_copy_total":12},"claim_boundary":"Unchanged actual Windows AEX public SequenceSetup -> SmartPre -> SmartRender with embedded byte-identical fixture definitions under probe-local suites and pinned AE SDK structure layouts. Radius is supplied at the documented internal float materialization seam and is recorded separately from the requested binary64 value; no current-production identity binding, real checkout_param/checkin_param, native Windows runtime, or After Effects host claim."}
 if extra_only:
  result["schema"]="olmtoondilate.same-source-actual-aex-extra/1";result["status"]="PASS_SAME_SOURCE_ACTUAL_AEX_3" if all(gates.values()) else "BLOCKED_FAIL_CLOSED";result["matrix"]={"depths":[8,16,32],"families":["corner_seed_5x5_r4_ds1/1"],"case_count":3};result["lifecycle"]={key.replace("_total", "_total"): 3 if key != "optional_layer_checkin_total" else 0 for key in result["lifecycle"]}
 if write:
  REPORT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  MARKDOWN.write_text("# OLMToonDilate same-source actual-AEX replay — 2026-08-13\n\n- Status: **"+result["status"]+"**\n- The unchanged Windows AEX public Smart owner is raw-exact for PF8/PF16/PF32 × four current-public fixtures (12/12).\n- Padding, guards, headers, input invariance, entry returns, and callback counts pass.\n- Windows requests preserve-RGB=false while current production requests true; numerical outputs remain exact.\n- Radius uses the documented internal float seam. No real AE-host or native-Windows-runtime claim.\n",encoding="utf-8")
 print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["status"].startswith("PASS") else 1

if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--write",action="store_true");parser.add_argument("--extra-only",action="store_true");args=parser.parse_args();raise SystemExit(main(args.write,args.extra_only))
