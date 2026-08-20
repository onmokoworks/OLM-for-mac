#!/usr/bin/env python3
"""Hostless public SmartRender cleanup/atomic-commit regression."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py"


def load_base():
    spec = importlib.util.spec_from_file_location("dblur_smart_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("base adapter import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(directory: Path) -> Path:
    base = load_base()
    base.compile_probe(directory)
    cpp = directory / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text()
    old_params = """static int g_render_entry_calls = 0;
static PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p) { std::memset(p,0,sizeof(*p)); if(index==2)p->u.fs_d.value=1.0; else if(index==16)p->u.pd.value=1; else if(index==18)p->u.sd.value=1; else if(index==20)p->u.fs_d.value=10.0; return PF_Err_NONE; }
static PF_Err checkin_param() { return PF_Err_NONE; }"""
    new_params = """static int g_render_entry_calls=0,g_param_checkout=0,g_param_checkin=0,g_front_strength=0;
static int g_fail_param_checkout=0,g_fail_param_checkin=0,g_throw_param_checkout=0,g_throw_param_checkin=0;
static PF_Err checkout_param(PF_InData*,A_long index,A_long,A_long,A_long,PF_ParamDef *p){int n=++g_param_checkout;if(n==g_throw_param_checkout)throw "param checkout";if(n==g_fail_param_checkout)return -77;std::memset(p,0,sizeof(*p));if(index==2)p->u.fs_d.value=1.0;else if(index==5)p->u.sd.value=g_front_strength;else if(index==16)p->u.pd.value=1;else if(index==18)p->u.sd.value=1;else if(index==20)p->u.fs_d.value=10.0;return PF_Err_NONE;}
static PF_Err checkin_param(){int n=++g_param_checkin;if(n==g_throw_param_checkin)throw "param checkin";return n==g_fail_param_checkin?-78:PF_Err_NONE;}"""
    if old_params not in text:
        raise RuntimeError("parameter splice marker changed")
    text = text.replace(old_params, new_params)
    text = text.replace("#include <vector>", "#include <vector>\n#include <cstdlib>\n#include <new>", 1)
    ns_start = text.index("namespace { struct State")
    main_start = text.index("int main()")
    new_namespace = r'''static bool g_arm_alloc=false; static int g_armed_allocations=0;
void* operator new(std::size_t n){if(g_arm_alloc){++g_armed_allocations;throw std::bad_alloc();}if(void*p=std::malloc(n))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void*p)noexcept{std::free(p);} void operator delete[](void*p)noexcept{std::free(p);}
void operator delete(void*p,std::size_t)noexcept{std::free(p);} void operator delete[](void*p,std::size_t)noexcept{std::free(p);}
namespace { struct State { PF_EffectWorld *input,*output; int layer=0,out=0,checkin=0; int fail_output=0,throw_output=0,fail_checkin=0,throw_checkin=0; }; State *state(PF_ProgPtr p){return static_cast<State*>(p);}
PF_Err layer_checkout(PF_ProgPtr p,A_long index,PF_EffectWorld **o){auto*s=state(p);++s->layer;if(index==OLMDIRECTIONALBLUR_NOISE_LAYER){*o=nullptr;return PF_Err_BAD_CALLBACK_PARAM;}*o=s->input;return PF_Err_NONE;}
PF_Err output_checkout(PF_ProgPtr p,PF_EffectWorld **o){auto*s=state(p);++s->out;if(s->throw_output)throw "output checkout";if(s->fail_output)return -79;*o=s->output;return PF_Err_NONE;}
PF_Err checkin(PF_ProgPtr p,A_long index){auto*s=state(p);if(index==OLMDIRECTIONALBLUR_NOISE_LAYER)return PF_Err_NONE;++s->checkin;if(s->throw_checkin)throw "layer checkin";return s->fail_checkin?-80:PF_Err_NONE;}
void fill(std::vector<std::uint8_t>&b,int ps,int rb){std::fill(b.begin(),b.end(),PAD);for(int y=0;y<HEIGHT;++y)for(int x=0;x<WIDTH;++x){auto*q=reinterpret_cast<std::uint16_t*>(b.data()+y*rb+x*ps);q[0]=(x==1&&y==0)?0:65535;q[1]=0x1234+x;q[2]=0x2345+y;q[3]=0x3456+x+y;}}
bool all_value(const std::vector<std::uint8_t>&b,std::uint8_t v){return std::all_of(b.begin(),b.end(),[v](std::uint8_t x){return x==v;});}}
'''
    new_main = r'''int main(){constexpr short depth=16;const int ps=8,rb=WIDTH*ps+PADDING;int cases=0;
auto run=[&](int fc,int fi,int tc,int ti,int fo,int to,int fl,int tl,PF_Err expected,int expected_pc,int expected_pi){std::vector<std::uint8_t>inb(rb*HEIGHT),outb(rb*HEIGHT,OUT_PAD);fill(inb,ps,rb);auto before=inb;PF_EffectWorld in{inb.data(),rb,WIDTH,HEIGHT,depth,{0,0,WIDTH,HEIGHT}},out{outb.data(),rb,WIDTH,HEIGHT,depth,{0,0,WIDTH,HEIGHT}};State st{&in,&out};st.fail_output=fo;st.throw_output=to;st.fail_checkin=fl;st.throw_checkin=tl;g_param_checkout=g_param_checkin=0;g_fail_param_checkout=fc;g_fail_param_checkin=fi;g_throw_param_checkout=tc;g_throw_param_checkin=ti;PF_InData id{&st,0,1,1,{1,1},{1,1},nullptr};PF_OutData od{};PF_SmartRenderInput si{depth,nullptr};PF_SmartRenderCallbacks cb{layer_checkout,output_checkout,checkin};PF_SmartRenderExtra ex{&si,&cb};PF_Err err=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&ex);bool untouched=all_value(outb,OUT_PAD);if(err!=expected||g_param_checkout!=expected_pc||g_param_checkin!=expected_pi||st.checkin!=1||inb!=before||!untouched){std::fprintf(stderr,"case=%d err=%d/%d pc=%d/%d pi=%d/%d checkin=%d input=%d untouched=%d\n",cases,(int)err,(int)expected,g_param_checkout,expected_pc,g_param_checkin,expected_pi,st.checkin,inb==before,untouched);return false;}++cases;return true;};
for(int n:{1,10,21})if(!run(n,0,0,0,0,0,0,0,-77,n,n-1))return 10+n;
for(int n:{1,10,21})if(!run(0,n,0,0,0,0,0,0,-78,21,21))return 40+n;
for(int n:{1,10,21})if(!run(0,0,n,0,0,0,0,0,PF_Err_INTERNAL_STRUCT_DAMAGED,n,n-1))return 70+n;
for(int n:{1,10,21})if(!run(0,0,0,n,0,0,0,0,PF_Err_INTERNAL_STRUCT_DAMAGED,21,21))return 100+n;
if(!run(0,0,0,0,1,0,0,0,-79,0,0))return 130;
if(!run(0,0,0,0,0,1,0,0,PF_Err_INTERNAL_STRUCT_DAMAGED,0,0))return 131;
if(!run(0,0,0,0,0,0,1,0,-80,21,21))return 132;
if(!run(0,0,0,0,0,0,0,1,PF_Err_INTERNAL_STRUCT_DAMAGED,21,21))return 133;
{std::vector<std::uint8_t>outb(64,OUT_PAD);auto before=outb;PF_EffectWorld in{reinterpret_cast<void*>(0x100000000ull),16,1,2,32,{0,0,1,2}},out{outb.data(),1700000000,1,2,32,{0,0,1,2}};State st{&in,&out};g_param_checkout=g_param_checkin=0;g_fail_param_checkout=g_fail_param_checkin=g_throw_param_checkout=g_throw_param_checkin=0;g_front_strength=2;PF_InData id{&st,0,1,1,{1,1},{1,1},nullptr};PF_OutData od{};PF_SmartRenderInput si{32,nullptr};PF_SmartRenderCallbacks cb{layer_checkout,output_checkout,checkin};PF_SmartRenderExtra ex{&si,&cb};g_armed_allocations=0;g_arm_alloc=true;PF_Err err=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&ex);g_arm_alloc=false;g_front_strength=0;if(err!=PF_Err_BAD_CALLBACK_PARAM||g_armed_allocations!=0||outb!=before||st.layer!=2||st.out!=1||st.checkin!=1||g_param_checkout!=21||g_param_checkin!=21){std::fprintf(stderr,"budget err=%d alloc=%d output=%d layer=%d out=%d checkin=%d pc=%d pi=%d\n",(int)err,g_armed_allocations,outb==before,st.layer,st.out,st.checkin,g_param_checkout,g_param_checkin);return 134;}++cases;}
std::printf("PASS_OLMDIRECTIONALBLUR_SMART_CLEANUP_ATOMIC cases=%d\n",cases);return 0;}
'''
    text = text[:ns_start] + new_namespace + new_main
    cpp.write_text(text)
    exe = directory / "cleanup_probe"
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = [
        "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
        "-ffp-contract=off", "-isysroot", sdk,
        "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
        str(cpp), str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"), "-framework", "Cocoa", "-o", str(exe),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return exe


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_cleanup_") as raw:
        exe = build(Path(raw))
        result = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"cleanup probe rc={result.returncode}: {result.stderr}")
    print(result.stdout, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
