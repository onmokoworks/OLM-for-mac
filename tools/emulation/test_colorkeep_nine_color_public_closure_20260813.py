#!/usr/bin/env python3
"""Close ColorKeep's fixture-bound nine-color public EffectMain lane."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
LOADER = ROOT / "tools/emulation/aex_loader.py"
DISASM = ROOT / "decomp/ColorKeep.aex.c.txt"
ORACLE = ROOT / "tools/emulation/test_colorkeep_nine_color_effectmain_actual_aex_20260805.py"
REPORT = ROOT / "refs/conformance/colorkeep_nine_color_public_closure_20260813.json"
DOC = REPORT.with_suffix(".md")
AEX_SHA = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"

PALETTE8 = ((255,0,64,128),(191,64,128,191),(128,128,191,255),(64,191,255,0),(255,255,0,64),(223,32,96,159),(159,96,159,223),(96,159,223,32),(32,223,32,96))
COLORS = tuple(tuple(value / 255 for value in color) for color in PALETTE8)
EXPECTED = {
    "PF8": {"input_active": "fbe82d47b0fa833915c8c6bea78c65fb6668faa281a96b035d7e4e2006cb75fc", "input_padded": "6d394a2c03eff4004bfc1d3f48e8b8d50f11b8314546b6948a99b6dd80926b66", "output_active": "ad5a9e2d70f0adcc6318d340b3fa47ef4b5d89e79d9827554197da41d81da3dd", "output_padded": "bc984eb75602ef8035269dad5b09265663067aaa18b2567caf8245d8477c9851", "rowbytes": 24},
    "PF16": {"input_active": "c073b78ce8556a736edbdedf7bb846b5f63c3dbd31074af48be389260bc898ad", "input_padded": "3b5f1910edcc302024c13e3089adbef018fa5cd90ac3cc84157b2ba33410da08", "output_active": "67b738b61c8197b32885019e6395612b7d065b42c8efd5070fc0ab3e84637392", "output_padded": "b0d6e4297887986e4f6dfe934ac5546849e846dcd57d043b1cbe59d3d02f20fb", "rowbytes": 40},
    "PF32": {"input_active": "d90f3a04f99578c89b137512ff3efae9e9999b0e3276273cdf5e18102c7cb19d", "input_padded": "cdad725dd3e2380ae8d3257a8226453d0bbaea00d552f70df6acea714e83823d", "output_active": "5304a3f80f4ed6be0e210e9d925ac4fa7350feacb1035778a0adfc3edec9f469", "output_padded": "c606d31f09ac65a9e59e356df9140a63751c69526daab4f95a27930b563787ab", "rowbytes": 72},
}
SMART_MUTATIONS = tuple(m for m in range(1, 37) if m not in (6, 7, 8, 9, 19))
CLASSIC_MUTATIONS = (1,2,3,4,5,10,12,14,18,20,21,22,23,24,25,26,27,28,32,35,36)
MUTATION_NAMES = {1:"count8",2:"count10",3:"source_first",4:"source_middle",5:"source_last",10:"palette0",11:"palette1",12:"palette2",13:"palette3",14:"palette4",15:"palette5",16:"palette6",17:"palette7",18:"palette8",20:"input_width",21:"output_height",22:"input_rowbytes",23:"output_rowbytes",24:"input_extent",25:"output_origin",26:"input_flags",27:"alias",28:"partial_overlap",29:"param_checkout_mid",30:"color_convert_mid",31:"param_checkin_mid",32:"iterate_failure",33:"inactive_tail_first",34:"inactive_tail_last",35:"input_format",36:"output_format",37:"classic_pf32"}
NEGATIVE_CASES = [
    {"path":path,"depth":depth,"case":MUTATION_NAMES[mutation],"stage":"iterate" if mutation==32 else "pre-iterate","return":"PF_Err_BAD_CALLBACK_PARAM" if mutation in (33,34,35,36) else "nonzero","iterate_hits":1 if mutation==32 else 0,"input_bytes_untouched":True,"destination_and_padding_untouched":True}
    for path, mutations, depths in (("Smart",SMART_MUTATIONS,("PF8","PF16","PF32")),("Classic",CLASSIC_MUTATIONS,("PF8","PF16")))
    for mutation in mutations for depth in depths
] + [{"path":"Classic","depth":"PF32","case":"classic_pf32","stage":"pre-iterate","return":"PF_Err_BAD_CALLBACK_PARAM","iterate_hits":0,"input_bytes_untouched":True,"destination_and_padding_untouched":True}]
assert len(NEGATIVE_CASES) == 136
NEGATIVE_CASES_SHA256 = hashlib.sha256(json.dumps(
    NEGATIVE_CASES, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
NEGATIVE_CATEGORY_EVIDENCE = {
    "active_palette_index2": {"paths": ["Smart", "Classic"], "depths": ["PF8", "PF16", "PF32"], "classic_pf32_excluded": True},
    "smart_inactive_tail_first_last": {"depths": ["PF8", "PF16", "PF32"], "callback_counts": [101, 100, 101], "pixel_checkin": 0},
    "smart_format_input_output": {"depths": ["PF8", "PF16", "PF32"], "callback_counts": [1, 0, 1], "pixel_checkin": 0},
    "classic_format_input_output": {"depths": ["PF8", "PF16"], "color_conversions": 0},
    "classic_pf32": {"depths": ["PF32"], "color_conversions": 0},
    "smart_pre_render_request_unchanged": True,
    "world_headers_unchanged": True,
}
WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")
WORKER_SHA = "16c329a481aef88c00fd6016e79996eecaabf7a588cff084e866b6bd15d411fc"
WORKER_COMMIT = "0ee278943751b968ea2b0d5a0e0f483b70c0090d"
LOADER_SHA = "f277dbecd70c4c495aa05e6495d80fdc5ce07c5df51b9076be331c232e26c9ab"
DISASM_SHA = "805e298cc7619d2b10591e6dfac5131a5c31faa9b9532915dd7a0feb4ab9075a"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value: bytes) -> str: return hashlib.sha256(value).hexdigest()

def oracle_module():
    spec = importlib.util.spec_from_file_location("ck9_oracle", ORACLE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def fresh_oracle() -> tuple[dict[str, bytes], dict[str, bytes], list[dict]]:
    selected=(0,3,4,7,8); argb=tuple(PALETTE8[i] for i in selected)+((32,222,32,96),)
    pixels=(argb*2)[:12]; inputs={};outputs={}
    for depth in EXPECTED:
        def pack(value):
            if depth=="PF8": return bytes(value)
            if depth=="PF16": return struct.pack("<4H",*((x*32768+127)//255 for x in value))
            return struct.pack("<4f",*(x/255 for x in value))
        active=b"".join(pack(p) for p in pixels)
        out=b"".join(pack(((0,)+p[1:]) if i%6==5 else p) for i,p in enumerate(pixels))
        ps=len(active)//12;inputs[depth]=b"".join(active[y*4*ps:(y+1)*4*ps]+b"\xcc"*8 for y in range(3));outputs[depth]=b"".join(out[y*4*ps:(y+1)*4*ps]+b"\xee"*8 for y in range(3))
        assert digest(active)==EXPECTED[depth]["input_active"] and digest(inputs[depth])==EXPECTED[depth]["input_padded"]
        assert digest(out)==EXPECTED[depth]["output_active"] and digest(outputs[depth])==EXPECTED[depth]["output_padded"]
    rows=[]
    with tempfile.TemporaryDirectory(prefix="ck9_exported_owner.") as raw:
        d=Path(raw); image=Image.new("RGBA",(4,3));image.putdata([(r,g,b,a) for a,r,g,b in pixels]);png=d/"input.png";image.save(png)
        params=["Enabled Color Num=9"]+[f"Color@{i+2}={a},{r},{g},{b}" for i,(a,r,g,b) in enumerate(PALETTE8)]
        for depth,fmt,suite in (("PF8","argb8","PF Iterate8 Suite v1"),("PF16","argb16","PF iterate16 Suite v1"),("PF32","argb32f","PF iterateFloat Suite v1")):
            run=subprocess.run([str(WORKER),"render-png",str(AEX),str(png),str(d/(depth+".png")),"--pixel-format",fmt,*params],cwd=ROOT,capture_output=True,text=True)
            if run.returncode: raise RuntimeError(run.stderr)
            value=json.loads(run.stdout)
            if value["raw_pixel_sha256"]!=EXPECTED[depth]["output_active"] or value["suite_requests"]!=["AEGP Utility Suite v7","PF ColorParamSuite v1",suite] or value["render_error"]!=0 or not value["gpu"]["pre_render"]["completed"] or not value["gpu"]["render"]["completed"]: raise RuntimeError(depth+" exported owner")
            rows.append({"depth":depth,"raw_sha256":value["raw_pixel_sha256"],"suite_requests":value["suite_requests"],"pre_render_complete":True,"smart_render_complete":True})
    return inputs,outputs,rows

def build_candidate() -> tuple[Path, dict]:
    durable = ROOT / "handoffs"; durable.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="colorkeep_nine_candidate_20260813.", dir=durable))
    product = directory / "Product"
    command = ["xcodebuild", "-project", "mac/ColorKeep/Mac/ColorKeep.xcodeproj", "-target", "ColorKeep", "-configuration", "Release", "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO", "CODE_SIGNING_ALLOWED=NO", f"CONFIGURATION_BUILD_DIR={product}", f"OBJROOT={directory/'Obj'}", f"SYMROOT={directory/'Sym'}", "build"]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    log = directory / "xcodebuild.log"; log.write_text(run.stdout + run.stderr)
    if run.returncode: raise RuntimeError((run.stdout + run.stderr)[-5000:])
    bundle = product / "ColorKeep.plugin"; binary = bundle / "Contents/MacOS/ColorKeep"
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(bundle)], check=True, capture_output=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)], check=True, capture_output=True)
    archs = subprocess.check_output(["lipo", "-archs", str(binary)], text=True).split()
    if set(archs) != {"arm64", "x86_64"}: raise RuntimeError("candidate not Universal")
    return binary, {"bundle": str(bundle), "binary": str(binary), "binary_sha256": sha(binary), "architectures": archs, "codesign": "pass", "build_log": str(log), "build_log_sha256": sha(log)}

def array(name: str, value: bytes) -> str:
    return f"static const unsigned char {name}[]={{" + ",".join(map(str, value)) + "};"

def probe(binary: Path, inputs: dict[str, bytes]) -> tuple[bytes, dict]:
    palette = b"".join(struct.pack("<4f", *c) for c in COLORS) + struct.pack("<4f", 1., 0., 0., 0.) * 91
    code = r'''#include <cstdint>
#include <cmath>
#include <initializer_list>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"
using Effect=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
static PF_Iterate8Suite2 s8{};static PF_iterate16Suite2 s16{};static PF_iterateFloatSuite2 sf{};static PF_ColorParamSuite1 sc{};static PF_WorldSuite2 sw{};static PF_EffectWorld*gin,*gout;static int gd,gcount,co,ci,cc,lh,oh,li,ph,ih,phase_bad,fail_checkout,fail_color,fail_checkin,fail_iter,palette_mut,fmt_mut,gsmart;static int order[101];
''' + array("colors", palette) + array("raw8", inputs["PF8"]) + array("raw16", inputs["PF16"]) + array("raw32", inputs["PF32"]) + r'''
template<class P,class F>static PF_Err iter(PF_InData*,A_long a,A_long b,PF_EffectWorld*i,const PF_Rect*,void*r,F f,PF_EffectWorld*o){ih++;if(a!=0||b!=3)phase_bad=1;if(fail_iter)return 81;for(int y=0;y<3;y++)for(int x=0;x<4;x++){PF_Err e=f(r,x,y,(P*)((char*)i->data+y*i->rowbytes+x*sizeof(P)),(P*)((char*)o->data+y*o->rowbytes+x*sizeof(P)));if(e)return e;}return 0;}
static PF_Err i8(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel8Func g,PF_EffectWorld*h){return iter<PF_Pixel8>(a,b,c,d,e,f,g,h);}static PF_Err i16(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel16Func g,PF_EffectWorld*h){return iter<PF_Pixel16>(a,b,c,d,e,f,g,h);}static PF_Err iff(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixelFloatFunc g,PF_EffectWorld*h){return iter<PF_PixelFloat>(a,b,c,d,e,f,g,h);}
static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){if(gsmart&&(co!=101||ci))phase_bad=1;cc++;if(cc==fail_color)return 79;int n=p->u.cd.value.red;std::memcpy(out,colors+n*16,16);if(palette_mut==n)out->blue=std::nextafter(out->blue,out->blue==1.0f?0.0f:1.0f);return 0;}
static PF_Err fmt(const PF_EffectWorld*w,PF_PixelFormat*f){PF_PixelFormat expected=gd==8?PF_PixelFormat_ARGB32:gd==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;*f=((w==gin&&fmt_mut==1)||(w==gout&&fmt_mut==2))?(gd==8?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB32):expected;return(w==gin||w==gout)?0:95;}
static SPErr acq(const char*n,int32 v,const void**p){if(!std::strcmp(n,kPFIterate8Suite)&&v==2){*p=&s8;return 0;}if(!std::strcmp(n,kPFIterate16Suite)&&v==2){*p=&s16;return 0;}if(!std::strcmp(n,kPFIterateFloatSuite)&&v==2){*p=&sf;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==1){*p=&sc;return 0;}if(!std::strcmp(n,kPFWorldSuite)&&v==2){*p=&sw;return 0;}return 92;}static SPErr rel(const char*,int32){return 0;}
static PF_Err checkout(PF_ProgPtr,PF_ParamIndex n,A_long,A_long,A_u_long,PF_ParamDef*p){if(ci||cc)phase_bad=1;if(co<101)order[co]=n;co++;if(n==fail_checkout)return 77;std::memset(p,0,sizeof(*p));if(n==1)p->u.sd.value=gcount;else p->u.cd.value.red=n-2;return 0;}static PF_Err checkp(PF_ProgPtr,PF_ParamDef*){if(co!=101||cc!=100)phase_bad=1;ci++;return ci==fail_checkin?78:0;}
static PF_Err pre(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*r,A_long,A_long,A_u_long,PF_CheckoutResult*o){ph++;if(!r->preserve_rgb_of_zero_alpha)phase_bad=1;o->result_rect={0,0,4,3};o->max_result_rect={-1,-2,5,4};return 0;}static PF_Err layer(PF_ProgPtr,A_long,PF_EffectWorld**w){lh++;*w=gin;return 0;}static PF_Err output(PF_ProgPtr,PF_EffectWorld**w){oh++;*w=gout;return 0;}static PF_Err checklayer(PF_ProgPtr,A_long){li++;return 0;}
template<class P>static bool run(Effect e,const unsigned char*raw,int depth,bool smart,int mutation){constexpr int W=4,H=3,PAD=8;const int rb=W*sizeof(P)+PAD,sz=rb*H;alignas(P)unsigned char src[sz+32],dst[sz+32];std::memcpy(src,raw,sz);unsigned char before[sz];std::memcpy(before,src,sz);std::memset(dst,0xee,sizeof(dst));PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)src;iw.rowbytes=rb;iw.width=W;iw.height=H;iw.extent_hint={0,0,W,H};ow.data=(PF_PixelPtr)dst;ow.rowbytes=rb;ow.width=W;ow.height=H;ow.extent_hint={0,0,W,H};if(depth==16)iw.world_flags=ow.world_flags=PF_WorldFlag_DEEP;if(mutation==1)gcount=8;if(mutation==2)gcount=10;if(mutation==3)src[0]^=1;if(mutation==4)src[W*sizeof(P)+PAD+W*sizeof(P)/2]^=1;if(mutation==5)src[sz-PAD-1]^=1;if(mutation>=10&&mutation<19)palette_mut=mutation-10;if(mutation==20)iw.width=3;if(mutation==21)ow.height=2;if(mutation==22)iw.rowbytes=rb-1;if(mutation==23)ow.rowbytes=rb+1;if(mutation==24)iw.extent_hint.right=3;if(mutation==25)ow.origin_x=1;if(mutation==26)iw.world_flags^=PF_WorldFlag_DEEP;if(mutation==27)ow.data=iw.data;if(mutation==28)ow.data=(PF_PixelPtr)(src+1);PF_EffectWorld ib=iw,ob=ow;gin=&iw;gout=&ow;gd=depth;gcount=mutation==1?8:mutation==2?10:9;co=ci=cc=lh=oh=li=ph=ih=phase_bad=fail_checkout=fail_color=fail_checkin=fail_iter=fmt_mut=0;if(mutation==29)fail_checkout=51;if(mutation==30)fail_color=51;if(mutation==31)fail_checkin=51;if(mutation==32)fail_iter=1;palette_mut=mutation==33?9:mutation==34?99:(mutation>=10&&mutation<19?mutation-10:-1);if(mutation==35)fmt_mut=1;if(mutation==36)fmt_mut=2;PF_InData in{};PF_OutData out{};SPBasicSuite b{};b.AcquireSuite=acq;b.ReleaseSuite=rel;in.pica_basicP=&b;in.inter.checkout_param=checkout;in.inter.checkin_param=checkp;PF_Err rc=0;bool request_unchanged=true;if(smart){PF_PreRenderInput pi{};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;PF_RenderRequest request_before=pi.output_request;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre;PF_PreRenderExtra px{&pi,&po,&pcb};rc=e(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&px);request_unchanged=std::memcmp(&pi.output_request,&request_before,sizeof(request_before))==0;PF_SmartRenderInput si{};si.bitdepth=depth;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=layer;cb.checkout_output=output;cb.checkin_layer_pixels=checklayer;PF_SmartRenderExtra sx{&si,&cb};if(!rc)rc=e(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&sx);}else{PF_ParamDef defs[102]{};PF_ParamDef*pp[102];for(int n=0;n<102;n++){pp[n]=&defs[n];if(n>=2)defs[n].u.cd.value.red=n-2;}defs[0].u.ld=iw;defs[1].u.sd.value=gcount;gin=&defs[0].u.ld;rc=e(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);iw=defs[0].u.ld;}bool pads=true;for(int y=0;y<H;y++)for(int x=W*sizeof(P);x<rb;x++)pads&=src[y*rb+x]==raw[y*rb+x]&&dst[y*rb+x]==0xee;bool unchanged=std::memcmp(src,before,sz)==0&&std::memcmp(&iw,&ib,sizeof(iw))==0&&std::memcmp(&ow,&ob,sizeof(ow))==0;if(mutation){bool noout=true;for(int i=0;i<sz;i++)noout&=dst[i]==0xee;bool exact_bad=mutation>=33&&mutation<=37;bool category_life=true;if(smart&&(mutation==33||mutation==34))category_life=co==101&&cc==100&&ci==101&&li==0&&!phase_bad;if(smart&&(mutation==35||mutation==36))category_life=co==1&&cc==0&&ci==1&&li==0;if(!smart&&(mutation==35||mutation==36||mutation==37))category_life=co==0&&cc==0&&ci==0&&li==0;return (!exact_bad||rc==PF_Err_BAD_CALLBACK_PARAM)&&rc!=0&&ih==(mutation==32?1:0)&&noout&&pads&&unchanged&&request_unchanged&&category_life;}bool life=smart?(ph==1&&lh==1&&oh==1&&li==0&&co==101&&cc==100&&ci==101):(co==0&&cc==100&&ci==0&&lh==0&&oh==0);if(rc||!life||phase_bad||!pads||!unchanged||!request_unchanged||ih!=1)return false;std::fwrite(dst,1,sz,stdout);return true;}
int main(int c,char**v){s8.iterate=i8;s16.iterate=i16;sf.iterate=iff;sc.PF_GetFloatingPointColorFromColorDef=color;sw.PF_GetPixelFormat=fmt;void*h=dlopen(v[1],RTLD_NOW|RTLD_LOCAL);auto e=(Effect)dlsym(h,"EffectMain");if(!e)return 2;if(c>2){int ok=0;for(int m=1;m<=36;m++){if(m==6||m==7||m==8||m==9||m==19)continue;ok+=run<PF_Pixel8>(e,raw8,8,true,m);ok+=run<PF_Pixel16>(e,raw16,16,true,m);ok+=run<PF_PixelFloat>(e,raw32,32,true,m);}for(int m:{1,2,3,4,5,10,12,14,18,20,21,22,23,24,25,26,27,28,32,35,36}){ok+=run<PF_Pixel8>(e,raw8,8,false,m);ok+=run<PF_Pixel16>(e,raw16,16,false,m);}ok+=run<PF_PixelFloat>(e,raw32,32,false,37);std::printf("%d\n",ok);return ok==136?0:3;}bool ok=true;ok&=run<PF_Pixel8>(e,raw8,8,false,0);ok&=run<PF_Pixel16>(e,raw16,16,false,0);ok&=run<PF_Pixel8>(e,raw8,8,true,0);ok&=run<PF_Pixel16>(e,raw16,16,true,0);ok&=run<PF_PixelFloat>(e,raw32,32,true,0);return ok?0:4;}
'''
    replacements = (
        ("unsigned char before[sz];std::memcpy(before,src,sz);std::memset(dst,0xee",
         "unsigned char before[sz];std::memset(dst,0xee"),
        ("if(mutation==28)ow.data=(PF_PixelPtr)(src+1);PF_EffectWorld ib=iw",
         "if(mutation==28)ow.data=(PF_PixelPtr)(src+1);std::memcpy(before,src,sz);PF_EffectWorld ib=iw"),
        ("gin=&iw;gout=&ow;gd=depth;", "gin=&iw;gout=&ow;gd=depth;gsmart=smart;"),
        ("(co==0&&cc==100&&ci==0&&lh==0&&oh==0)", "(co==0&&cc==9&&ci==0&&lh==0&&oh==0)"),
    )
    for target, replacement in replacements:
        if code.count(target) != 1:
            raise RuntimeError(f"generated probe rewrite target drift: {target}")
        code = code.replace(target, replacement)
    if "unsigned char before[sz];std::memset" not in code or \
       "std::memcpy(before,src,sz);PF_EffectWorld ib=iw" not in code:
        raise RuntimeError("generated probe source snapshot is not initialized after mutations")
    with tempfile.TemporaryDirectory(prefix="ck9_probe.") as raw:
        d=Path(raw); cpp=d/"probe.cpp"; exe=d/"probe"; cpp.write_text(code)
        sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-isysroot",sdk,"-IHeaders","-IHeaders/SP","-IUtil","-IResources",str(cpp),"-o",str(exe)]
        build=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        if build.returncode: raise RuntimeError(build.stderr)
        positive=subprocess.run([str(exe),str(binary)],cwd=ROOT,capture_output=True)
        if positive.returncode: raise RuntimeError(f"positive rc={positive.returncode} {positive.stderr.decode(errors='replace')}")
        negative=subprocess.run([str(exe),str(binary),"negative"],cwd=ROOT,capture_output=True,text=True)
        if negative.returncode: raise RuntimeError(f"negative rc={negative.returncode} {negative.stdout} {negative.stderr}")
    return positive.stdout, {"rejects": int(negative.stdout), "all_precommit_atomic": True}

def validate(report: dict) -> None:
    if set(report) != {"schema","status","identity","oracle","public_paths","negative","candidate","claim_boundary"}: raise RuntimeError("fields")
    if report["schema"] != "colorkeep.nine-color-public-closure/1" or report["status"] != "exact_bounded_public_owner": raise RuntimeError("header")
    ids=report["identity"]
    worker_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=WORKER.parents[3],text=True).strip()
    expected_ids={"aex_sha256":sha(AEX),"loader_sha256":sha(LOADER),"disassembly_sha256":sha(DISASM),"worker_sha256":sha(WORKER),"worker_commit":worker_commit,"production_sha256":sha(SOURCE),"generator_sha256":sha(Path(__file__))}
    if ids != expected_ids or ids["aex_sha256"] != AEX_SHA or ids["worker_sha256"] != WORKER_SHA or ids["worker_commit"] != WORKER_COMMIT or ids["loader_sha256"] != LOADER_SHA or ids["disassembly_sha256"] != DISASM_SHA: raise RuntimeError("identity")
    oracle=report["oracle"]
    if set(oracle)!={"palette_sha256","depths","typed_entries","classic_static_anchors","smart_static_anchors","exported_smart_owner"} or oracle["palette_sha256"]!=digest(b"".join(struct.pack("<4f",*c) for c in COLORS)) or oracle["depths"]!=EXPECTED or oracle["typed_entries"]!={"PF8":"0x180001580","PF16":"0x180001280","PF32":"0x180001850"} or oracle["classic_static_anchors"]!={"selector":"0x0b","dispatcher":"0x180001140/0x180001000","PF8":"0x180001580","PF16":"0x180001280"} or oracle["smart_static_anchors"]!={"parameter_owner":"FUN_180001a90: enabled + 100 checkout; 100 ColorSuite; enabled + 100 checkin","pixel_owner":"FUN_180001ca0: checkout callbacks +0 and +0x10; no +0x8 pixel checkin","pre_render":"selector 0x17: request byte-copy; preserve flag not mutated"}: raise RuntimeError("oracle")
    if [row["depth"] for row in oracle["exported_smart_owner"]] != ["PF8","PF16","PF32"]: raise RuntimeError("exported rows")
    for row in oracle["exported_smart_owner"]:
        suites={"PF8":["AEGP Utility Suite v7","PF ColorParamSuite v1","PF Iterate8 Suite v1"],"PF16":["AEGP Utility Suite v7","PF ColorParamSuite v1","PF iterate16 Suite v1"],"PF32":["AEGP Utility Suite v7","PF ColorParamSuite v1","PF iterateFloat Suite v1"]}[row["depth"]]
        if set(row)!={"depth","raw_sha256","suite_requests","pre_render_complete","smart_render_complete"} or row["raw_sha256"]!=EXPECTED[row["depth"]]["output_active"] or row["suite_requests"]!=suites or not row["pre_render_complete"] or not row["smart_render_complete"]: raise RuntimeError("exported row")
    expected_paths=[]
    for path,depth in (("Classic","PF8"),("Classic","PF16"),("Smart","PF8"),("Smart","PF16"),("Smart","PF32")):
        expected_paths.append({"path":path,"depth":depth,"output_padded_sha256":EXPECTED[depth]["output_padded"],"output_active_sha256":EXPECTED[depth]["output_active"],"input_immutable":True,"headers_immutable":True,"input_output_padding_immutable":True,"iterate_range":[0,3],"parameter_checkout_checkin":[0,0] if path=="Classic" else [101,101],"color_conversions":9 if path=="Classic" else 100,"inactive_tail_dependency":"not read" if path=="Classic" else "91 default opaque-black colors","smart_layer_checkin":0 if path=="Smart" else None})
    if report["public_paths"] != expected_paths: raise RuntimeError("paths")
    if report["negative"] != {"rejects":136,"cases":NEGATIVE_CASES,"cases_sha256":NEGATIVE_CASES_SHA256,"category_evidence":NEGATIVE_CATEGORY_EVIDENCE,"other_failure_lifecycle_not_claimed":True}: raise RuntimeError("negative")
    if report["claim_boundary"] != "Only count9 + exact 4x3/padding8 worlds + exact typed active source + exact nine active colors; Smart additionally binds the 91-color default opaque-black inactive tail, while Classic does not read it. Existing 11x7 count5/100 lanes remain separate.": raise RuntimeError("claim")
    build=report["candidate"]
    if set(build)!={"bundle","binary","binary_sha256","architectures","codesign","build_log","build_log_sha256"}: raise RuntimeError("candidate fields")
    binary=Path(build["binary"]); bundle=Path(build["bundle"])
    actual_archs=subprocess.check_output(["lipo","-archs",str(binary)],text=True).split()
    if sha(binary)!=build["binary_sha256"] or set(actual_archs)!={"arm64","x86_64"} or actual_archs!=build["architectures"] or build["codesign"]!="pass" or sha(Path(build["build_log"]))!=build["build_log_sha256"]: raise RuntimeError("candidate")
    subprocess.run(["codesign","--verify","--deep","--strict",str(bundle)],check=True,capture_output=True)

def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("--write",action="store_true");parser.add_argument("--validate-only",action="store_true");args=parser.parse_args()
    if not args.write: validate(json.loads(REPORT.read_text())); print("PASS_COLORKEEP_NINE_COLOR_CLOSURE_VALIDATE"); return 0
    inputs,outputs,owner_rows=fresh_oracle(); binary,candidate=build_candidate(); observed,negative=probe(binary,inputs)
    sizes=[len(outputs["PF8"]),len(outputs["PF16"]),len(outputs["PF8"]),len(outputs["PF16"]),len(outputs["PF32"])]
    offset=0; paths=[]
    for (path,depth),size in zip((("Classic","PF8"),("Classic","PF16"),("Smart","PF8"),("Smart","PF16"),("Smart","PF32")),sizes):
        part=observed[offset:offset+size];offset+=size
        if digest(part)!=EXPECTED[depth]["output_padded"]: raise RuntimeError(f"{path} {depth} mismatch")
        paths.append({"path":path,"depth":depth,"output_padded_sha256":digest(part),"output_active_sha256":EXPECTED[depth]["output_active"],"input_immutable":True,"headers_immutable":True,"input_output_padding_immutable":True,"iterate_range":[0,3],"parameter_checkout_checkin":[0,0] if path=="Classic" else [101,101],"color_conversions":9 if path=="Classic" else 100,"inactive_tail_dependency":"not read" if path=="Classic" else "91 default opaque-black colors","smart_layer_checkin":0 if path=="Smart" else None})
    worker_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=WORKER.parents[3],text=True).strip()
    negative={"rejects":negative["rejects"],"cases":NEGATIVE_CASES,"cases_sha256":NEGATIVE_CASES_SHA256,"category_evidence":NEGATIVE_CATEGORY_EVIDENCE,"other_failure_lifecycle_not_claimed":True}
    report={"schema":"colorkeep.nine-color-public-closure/1","status":"exact_bounded_public_owner","identity":{"aex_sha256":sha(AEX),"loader_sha256":sha(LOADER),"disassembly_sha256":sha(DISASM),"worker_sha256":sha(WORKER),"worker_commit":worker_commit,"production_sha256":sha(SOURCE),"generator_sha256":sha(Path(__file__))},"oracle":{"palette_sha256":digest(b"".join(struct.pack("<4f",*c) for c in COLORS)),"depths":EXPECTED,"typed_entries":{"PF8":"0x180001580","PF16":"0x180001280","PF32":"0x180001850"},"classic_static_anchors":{"selector":"0x0b","dispatcher":"0x180001140/0x180001000","PF8":"0x180001580","PF16":"0x180001280"},"smart_static_anchors":{"parameter_owner":"FUN_180001a90: enabled + 100 checkout; 100 ColorSuite; enabled + 100 checkin","pixel_owner":"FUN_180001ca0: checkout callbacks +0 and +0x10; no +0x8 pixel checkin","pre_render":"selector 0x17: request byte-copy; preserve flag not mutated"},"exported_smart_owner":owner_rows},"public_paths":paths,"negative":negative,"candidate":candidate,"claim_boundary":"Only count9 + exact 4x3/padding8 worlds + exact typed active source + exact nine active colors; Smart additionally binds the 91-color default opaque-black inactive tail, while Classic does not read it. Existing 11x7 count5/100 lanes remain separate."}
    validate(report);REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text("# ColorKeep nine-color bounded public closure — 2026-08-13\n\nWindows exported Smart PF8/PF16/PF32 is raw-exact under the pinned AEXCompat worker. Windows Classic PF8/PF16 ownership is statically bound from selector `0x0b` through the typed callbacks; the Mac Classic paths are raw-exact to those typed owner hashes. The lane is limited to count 9, exact 4×3 active source, exact public palette, and 8-byte Mac padding. Smart lifecycle uses 101 checkout, 100 conversion, and 101 checkin calls; the old report's hard-coded count 10 is superseded. The Smart request is passed through unchanged and the actual success path does not call pixel checkin. Mac padding is invariant; the tight Windows worker plane makes no padding claim. Count9 output is staged and committed only after successful execution. The 136-case canonical reject matrix includes every active palette key, Smart inactive-tail endpoints, Smart and Classic input/output format substitutions, and Classic PF32; those cases bind exact error/iteration and complete padded-buffer/header immutability, with callback counts only for the named categories recorded in JSON. Unlisted source, palette, count, geometry, layout, and Classic PF32 remain fail-closed. The Universal candidate is isolated and not installed.\n")
    print("PASS_COLORKEEP_NINE_COLOR_CLOSURE paths=5 rejects=136 Universal=arm64+x86_64");return 0

if __name__=="__main__": raise SystemExit(main())
