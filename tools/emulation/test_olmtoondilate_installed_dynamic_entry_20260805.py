#!/usr/bin/env python3
"""Load the installed OLMToonDilate bundle and execute SmartPre/SmartRender."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin"
BINARY=BUNDLE/"Contents/MacOS/OLMToonDilate"
REPORT=ROOT/"refs/conformance/olmtoondilate_installed_dynamic_entry_20260805.json"
EXPECTED_SHA="7d2c24d8ad0f7436ee7035e0d926a2abaac1a74bc9305a4223f76230c1fc5537"

def main():
 if hashlib.sha256(BINARY.read_bytes()).hexdigest()!=EXPECTED_SHA:raise RuntimeError("BLOCKED_FAIL_CLOSED: installed binary drifted")
 compiler=shutil.which("clang++");assert compiler
 with tempfile.TemporaryDirectory(prefix="toondilate_installed_dynamic_") as td:
  td=Path(td);src=td/"probe.cpp";exe=td/"probe"
  src.write_text(r'''#include <dlfcn.h>
#include <cstdio>
#include <cstring>
#include "AE_Effect.h"
static PF_EffectWorld *g_in,*g_out;static double g_radius=1.0;static int pre_hits,pixel_hits,out_hits,checkin_hits,param_hits;
static PF_Err checkout_param(PF_ProgPtr,PF_ParamIndex,A_long,A_long,A_u_long,PF_ParamDef*p){std::memset(p,0,sizeof(*p));p->u.fs_d.value=g_radius;++param_hits;return PF_Err_NONE;}
static PF_Err checkin_param(PF_ProgPtr,PF_ParamDef*){return PF_Err_NONE;}
static PF_Err pre_checkout(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){std::memset(r,0,sizeof(*r));r->result_rect={0,0,3,2};r->max_result_rect={0,0,3,2};r->ref_width=3;r->ref_height=2;++pre_hits;return PF_Err_NONE;}
static PF_Err pixels(PF_ProgPtr,A_long,PF_EffectWorld**w){*w=g_in;++pixel_hits;return PF_Err_NONE;}
static PF_Err checkin(PF_ProgPtr,A_long){++checkin_hits;return PF_Err_NONE;}
static PF_Err output(PF_ProgPtr,PF_EffectWorld**w){*w=g_out;++out_hits;return PF_Err_NONE;}
int main(int argc,char**argv){void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h){std::fprintf(stderr,"%s",dlerror());return 2;}using Fn=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef*[],PF_LayerDef*,void*);auto effect=(Fn)dlsym(h,"EffectMain");if(!effect)return 3;
 constexpr int W=3,H=2,RB=20;unsigned char ib[RB*H],ob[RB*H];std::memset(ib,0,RB*H);std::memset(ob,0xEE,RB*H);PF_Pixel8 S{255,10,20,30},M{128,81,41,21},C{0,0,0,0},srcp[6]={M,S,M,C,M,C};for(int y=0;y<H;++y)for(int x=0;x<W;++x)std::memcpy(ib+y*RB+x*4,&srcp[y*W+x],4);for(int y=0;y<H;++y)std::memset(ib+y*RB+12,0xA5,8);
 PF_EffectWorld inw{},outw{};inw.data=(PF_PixelPtr)ib;inw.rowbytes=RB;inw.width=W;inw.height=H;inw.extent_hint={101,201,104,203};outw.data=(PF_PixelPtr)ob;outw.rowbytes=RB;outw.width=W;outw.height=H;outw.extent_hint={301,401,304,403};g_in=&inw;g_out=&outw;
 PF_InData in{};PF_OutData out{};in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};auto a=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
 PF_SmartRenderInput si{};si.bitdepth=8;si.pre_render_data=po.pre_render_data;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=pixels;scb.checkin_layer_pixels=checkin;scb.checkout_output=output;PF_SmartRenderExtra se{&si,&scb};auto b=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);bool exact=a==0&&b==0&&pre_hits==1&&pixel_hits==1&&out_hits==1&&checkin_hits==1&&param_hits==1;for(int y=0;y<H;++y){for(int x=0;x<W;++x)exact=exact&&!std::memcmp(ob+y*RB+x*4,&S,4);for(int i=12;i<RB;++i)exact=exact&&ob[y*RB+i]==0xEE;}if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);std::printf("{\"exact\":%s,\"pre\":%d,\"pixels\":%d,\"output\":%d,\"checkin\":%d,\"param\":%d}\n",exact?"true":"false",pre_hits,pixel_hits,out_hits,checkin_hits,param_hits);dlclose(h);return exact?0:4;}
''')
  sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip();cmd=[compiler,"-std=c++17","-arch","arm64","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(src),"-o",str(exe)];build=subprocess.run(cmd,capture_output=True,text=True)
  if build.returncode:raise RuntimeError(build.stderr)
  run=subprocess.run([str(exe),str(BINARY)],capture_output=True,text=True)
  if run.returncode:raise RuntimeError(f"BLOCKED_FAIL_CLOSED dynamic entry: {run.stdout} {run.stderr}")
 result=json.loads(run.stdout);report={"status":"PASS_INSTALLED_DYNAMIC_ENTRY","installed_binary":str(BINARY),"binary_sha256":EXPECTED_SHA,"architecture":"arm64","entry_symbol":"EffectMain","commands":["PF_Cmd_SMART_PRE_RENDER","PF_Cmd_SMART_RENDER"],"fixture":{"depth":8,"dimensions":[3,2],"radius":1,"rowbytes":20,"nonzero_extents":True,"padding":8},"callbacks":result,"gates":{"dlopen_and_dlsym":True,"smartpre_to_smartrender_returned":True,"typed_writer_visible_exact":result["exact"],"padding_unchanged":True},"claim_boundary":"Installed arm64 slice dynamically loaded and executed AE-free with focused host callbacks; real AE execution remains unclaimed."};REPORT.write_text(json.dumps(report,indent=2)+"\n");REPORT.with_suffix(".md").write_text(f"# OLMToonDilate installed dynamic entry — 2026-08-05\n\n- Status: **{report['status']}**\n- The installed arm64 bundle was loaded with dlopen; EffectMain SmartPreRender and SmartRender executed a PF8 3x2 radius-1 fixture exactly, including padding and callback lifecycle.\n- Real AE execution remains unclaimed.\n");print(json.dumps(report,sort_keys=True))
 return 0
if __name__=="__main__":raise SystemExit(main())
