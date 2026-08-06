#!/usr/bin/env python3
"""Actual-AEX GLOBAL/PARAMS_SETUP parity for OLMToonDilate."""
from __future__ import annotations
import hashlib,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"tools/emulation"))
from aex_loader import AexLoader  # noqa:E402
AEX=ROOT/"aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex";SHA="c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3";ENTRY=0x1801ABC00
REPORT=ROOT/"refs/conformance/olmtoondilate_ui_setup_actual_aex_20260806.json"
def q(l,a,v):l.write_bytes(a,struct.pack("<Q",v))
def row(b):
 r={"raw_hex":b.hex(),"disk_id":struct.unpack_from("<I",b,0)[0],"ui_flags":struct.unpack_from("<I",b,4)[0],"ui_width":struct.unpack_from("<H",b,8)[0],"ui_height":struct.unpack_from("<H",b,10)[0],"param_type":struct.unpack_from("<I",b,12)[0],"name":b[16:48].split(b"\0",1)[0].decode("ascii"),"flags":struct.unpack_from("<I",b,48)[0]}
 r["float_slider"]={"value":struct.unpack_from("<d",b,56)[0],"phase":struct.unpack_from("<d",b,64)[0],"value_desc":b[72:104].split(b"\0",1)[0].decode("ascii"),"valid_min":struct.unpack_from("<f",b,104)[0],"valid_max":struct.unpack_from("<f",b,108)[0],"slider_min":struct.unpack_from("<f",b,112)[0],"slider_max":struct.unpack_from("<f",b,116)[0],"default":struct.unpack_from("<f",b,120)[0],"precision":struct.unpack_from("<h",b,124)[0],"display_flags":struct.unpack_from("<h",b,126)[0],"fs_flags":struct.unpack_from("<I",b,128)[0],"curve_tolerance":struct.unpack_from("<f",b,132)[0]}
 return r
def actual():
 l=AexLoader(str(AEX),verbose=False,fast=True);alloc={};acquisitions=[]
 def cb(n,f):return l.install_callback(n,f)
 def new(c,a):p=c.host_alloc(max(1,a[0]),align=16);c.write_bytes(p,b"\0"*max(1,a[0]));alloc[p]=a[0];return p
 zero=lambda c,a:0
 handles=l.host_alloc(0x30);l.write_bytes(handles,struct.pack("<6Q",cb("new",new),cb("lock",lambda c,a:a[0]),cb("unlock",zero),cb("dispose",zero),cb("size",lambda c,a:alloc.get(a[0],0)),cb("resize",zero)))
 utility=l.host_alloc(0x60);l.write_bytes(utility,b"\0"*0x60);q(l,utility+0x48,cb("register",lambda c,a:c.write_bytes(a[2],struct.pack("<i",77)) or 0))
 def cstr(p):return l.read_bytes(p,128).split(b"\0",1)[0].decode(errors="replace")
 def acquire(c,a):
  name=cstr(a[0]);acquisitions.append([name,a[1]]);q(c,a[2],utility if name=="AEGP Utility Suite" else handles);return 0
 basic=l.host_alloc(16);q(l,basic,cb("acquire",acquire));q(l,basic+8,cb("release",zero))
 inp=l.host_alloc(0x220);out=l.host_alloc(0x300);l.write_bytes(inp,b"\0"*0x220);l.write_bytes(out,b"\0"*0x300);q(l,inp+0x180,basic);q(l,inp+0xb8,0x1234)
 global_result=l.call_function(ENTRY,[1,inp,out,0,0,0],max_instructions=3_000_000);handle=struct.unpack("<Q",l.read_bytes(out+0x28,8))[0];q(l,inp+0x138,handle)
 global_row={"return_code":global_result["rax"],"my_version":struct.unpack("<I",l.read_bytes(out,4))[0],"out_flags":struct.unpack("<I",l.read_bytes(out+0x60,4))[0],"out_flags2":struct.unpack("<I",l.read_bytes(out+0x190,4))[0]}
 def copy(c,a):v=c.read_bytes(a[1],256).split(b"\0",1)[0];c.write_bytes(a[0],v+b"\0");return a[0]
 utils=l.host_alloc(0x160);l.write_bytes(utils,b"\0"*0x160);q(l,utils+0x150,cb("copy",copy));q(l,inp+0xb0,utils);q(l,inp+0x28,cb("pixel_formats",zero))
 raw=[];q(l,inp+0x10,cb("add_param",lambda c,a:raw.append(c.read_bytes(a[2],0xb0)) or 0))
 setup=l.call_function(ENTRY,[4,inp,out,0,0,0],max_instructions=5_000_000)
 return global_row,[row(x) for x in raw],{"return_code":setup["rax"],"num_params":struct.unpack("<I",l.read_bytes(out+0x30,4))[0],"suite_acquisitions":acquisitions}
def production():
 code=r'''#include <cstdio>\n#include <cstring>\n#include "mac/OLMToonDilate/OLMToonDilate.cpp"\nstatic PF_Err add(PF_ProgPtr,PF_ParamIndex,PF_ParamDefPtr d){fwrite(d,1,sizeof(*d),stdout);return 0;}\nint main(){PF_InData i{};PF_OutData o{};i.inter.add_param=add;if(EffectMain(PF_Cmd_GLOBAL_SETUP,&i,&o,nullptr,nullptr,nullptr))return 2;fwrite(&o.my_version,4,1,stderr);fwrite(&o.out_flags,4,1,stderr);fwrite(&o.out_flags2,4,1,stderr);if(EffectMain(PF_Cmd_PARAMS_SETUP,&i,&o,nullptr,nullptr,nullptr))return 3;return o.num_params==2?0:4;}'''.replace('\\n','\n')
 with tempfile.TemporaryDirectory(prefix="toon_ui_") as d:
  p=Path(d);cpp=p/"p.cpp";exe=p/"p";cpp.write_text(code);cmd=["xcrun","clang++","-std=c++17","-O2","-D__MACH__","-Wno-pragma-pack","-I.","-IHeaders","-IHeaders/SP","-IUtil","-IResources",str(cpp),"mac/OLMToonDilate/OLMToonDilate_Strings.cpp","Util/AEGP_SuiteHandler.cpp","Util/MissingSuiteError.cpp","-framework","Cocoa","-o",str(exe)];b=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);assert b.returncode==0,b.stderr;r=subprocess.run([str(exe)],capture_output=True);assert r.returncode==0,r.stderr;return struct.unpack("<III",r.stderr),row(r.stdout)
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
 ag,ar,meta=actual();pg,pr=production();assert len(ar)==1 and meta["num_params"]==2
 assert (ag["my_version"],ag["out_flags"],ag["out_flags2"])==pg and ar[0]==pr
 pipl=(ROOT/"mac/OLMToonDilate/OLMToonDilatePiPL.r").read_text();assert "AE_Effect_Global_OutFlags { 0x02000044 }" in pipl and "AE_Effect_Global_OutFlags_2 { 0x08021400 }" in pipl
 report={"schema":"olmtoondilate-ui-setup-actual-aex/1","status":"exact","aex_sha256":SHA,"entry_point":hex(ENTRY),"global_setup":ag,"params_setup":{"meta":meta,"rows":ar},"production":{"global_setup":{"my_version":pg[0],"out_flags":pg[1],"out_flags2":pg[2]},"rows":[pr],"pipl_capabilities_exact":True},"fixed_mismatches":["out_flags missing PF_OutFlag_NON_PARAM_VARY","out_flags2 advertised flattened-sequence instead of actual automatic-wide-time/threaded-rendering bits","float-slider curve_tolerance was 0.05 instead of raw actual 0.0"],"claim_boundary":"Hostless actual-AEX public GLOBAL_SETUP/PARAMS_SETUP raw structure versus source-included production; native AE control layout is not claimed."};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");REPORT.with_suffix('.md').write_text(f"# OLMToonDilate UI setup actual AEX — 2026-08-06\n\n- Status: **exact**\n- GLOBAL_SETUP and the complete one-row Search Radius PARAMS_SETUP surface match actual AEX raw fields.\n- PiPL capability literals match the captured global payload.\n- Native AE control layout remains outside this hostless claim.\n");print(json.dumps(report,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
