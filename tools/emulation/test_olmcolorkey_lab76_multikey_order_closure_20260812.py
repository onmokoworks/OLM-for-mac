#!/usr/bin/env python3
"""Close the bounded Lab76 destructive multi-key comparator seam."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as adapter  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
DISASM = ROOT / "disasm/OLMColorKey.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMColorKey.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json"
DOC = REPORT.with_suffix(".md")
WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))

EXPECTED = {
    "aex": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    "worker": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "worker_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
    "source": "8ee1ae7c8974f05ac48c32d6eba5c32cba0abc6d50c397599bf7b3022cb72e59",
    "disasm": "c9d4a8fe258d265e32433b6a38422ffa20dfd76e1bf688571377c9c87f0a8176",
    "decomp": "19a2a6b200dd68ae046bca69d471dd886415245aec533264e6f7bee8caa33ca8",
    "input_png": "fce316245a889eadf92820a0b590949f89ab0f78ea70d1370e5c5ef68a62b6b1",
    "record_after": "d7c9d9ea9dfa675ab55ae9571790279d6e7c998b51709621559f02cbe4472c67",
}
RAW_HASHES = {
    "declared": {
        "PF8": "bacce67eaa29aa6c18392a911495ddd87e21973ef3db86a116a7c6be74a1c474",
        "PF16": "1fe2dd593f9df058114b76fc1d4701bccaf7f461dae7e92e4e0da04dadae1e53",
        "PF32": "350e22668437e1322494faff9a7b7bf07325ca4a6a9fd775878faaa55c240b31",
    },
    "reverse": {
        "PF8": "315caf88910f1cc7edd25c90affec502e4654d0310504cfcb6d7469c68f93c93",
        "PF16": "31299a22989821a5c7205e886d8d2f6c0cc150ba97b46bdf46b4d4c0130fbf7a",
        "PF32": "176f964534c7f93884c8a90afc9459c6ece0ef38a7a65216b3db4af8fe480589",
    },
}
REGRESSION_STDOUT_HASHES = {
    "non_lab76": "a5410f440d44b3e7198594fccafa48cdb95c77cd17cede837c9a70c76b7f2f84",
    "edge_thin": "87b59e319aec6b6897fae1f57545ee712d16819cd7874b2062e6b5227eda2e92",
    "edge_blur": "33cfb38a77719f43227b261aed4980cea115558fbaf8f3ca4b67dd63e5420732",
    "replace_keep_premult": "99e4c2419426c2afa6884522236d681f036eaa55fb7a910fd767e7b9ecd7c24a",
    "replace_edge_composition": "dafd9f2def91498c3591bac4403789a35bacdca4c47293824dc6e9eea40b1ea6",
}
DEPTHS = {"PF8": ("argb8", 4), "PF16": ("argb16", 8), "PF32": ("argb32f", 16)}
KEYS = {
    "redish": (255, 204, 38, 26),
    "exact_cyan": (255, 26, 191, 204),
}
CLAIM = (
    "Raw exact only for the fixed 1x1 RGBA8 (26,191,204,255) public Lab76 scalar/global "
    "two-key tuple, declared and reversed key order, PF8/PF16/PF32, with Edge Thin, Edge "
    "Blur, and Replace disabled. The destructive mutation/Euclidean production rule is admitted "
    "only for those six cells; every one-away predicate rejects that rule. Invalid world layouts "
    "fail closed, and all valid outside tuples fail closed at the public entry. Per-component evidence records the native mutation but is "
    "not a production admission. This closure does not admit arbitrary colors, thresholds, "
    "geometry, AE-host execution, GPU, or installed binaries."
)


def sha_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_current_identities() -> bool:
    try:
        return (
            sha_path(AEX) == EXPECTED["aex"]
            and WORKER.is_file() and sha_path(WORKER) == EXPECTED["worker"]
            and sha_path(SOURCE) == EXPECTED["source"]
            and sha_path(DISASM) == EXPECTED["disasm"]
            and sha_path(DECOMP) == EXPECTED["decomp"]
        )
    except OSError:
        return False


def f32_bits(raw: bytes) -> list[str]:
    return [f"0x{word:08x}" for word in struct.unpack("<3I", raw)]


def owner_params(order: str) -> list[str]:
    colors = (KEYS["redish"], KEYS["exact_cyan"])
    if order == "reverse":
        colors = colors[::-1]
    return [
        "Color Keep=0", "Threshold=0.085", "Premultiplied Color=0", "Color Space=3",
        "Force Lower Precision=1", "Per Color=0", "Per Component=0",
        "Amount@14=0", "Distance Type@15=1", "Amount@18=0", "Distance Type@19=1",
        "Direction@20=2", "Number of Colors=2", "Enable Replace=0",
        "Use Color 1=1", f"Color 1={','.join(map(str, colors[0]))}",
        "Use Color 2=1", f"Color 2={','.join(map(str, colors[1]))}",
    ]


HARNESS = r'''
static std::vector<int> g_checkout_order; static int g_checkins=0; static int g_order=0;
static PF_Err color_from_def(PF_ProgPtr,PF_ParamDef*p,PF_PixelFloat*out){out->alpha=p->u.cd.value.alpha/255.f;out->red=p->u.cd.value.red/255.f;out->green=p->u.cd.value.green/255.f;out->blue=p->u.cd.value.blue/255.f;return 0;}
static PF_Err checkout_param(PF_InData*,A_long i,A_long,A_long,A_long,PF_ParamDef*p){std::memset(p,0,sizeof(*p));g_checkout_order.push_back(i);if(i==OLMCOLORKEY_THRESHOLD)p->u.fs_d.value=.085;else if(i==OLMCOLORKEY_COLOR_SPACE)p->u.pd.value=3;else if(i==OLMCOLORKEY_FORCE_LOWER_PRECISION)p->u.pd.value=1;else if(i==OLMCOLORKEY_NUMBER_OF_COLORS)p->u.sd.value=2;else if(i==OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE||i==OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE)p->u.pd.value=1;else if(i==OLMCOLORKEY_EDGE_BLUR_DIRECTION)p->u.pd.value=2;else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_USE_COLOR||i==OLMCOLORKEY_COLOR_FIRST+COLOR_PARAM_STRIDE+COLOR_OFFSET_USE_COLOR)p->u.bd.value=true;else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_COLOR)p->u.cd.value=g_order?PF_Pixel8{255,26,191,204}:PF_Pixel8{255,204,38,26};else if(i==OLMCOLORKEY_COLOR_FIRST+COLOR_PARAM_STRIDE+COLOR_OFFSET_COLOR)p->u.cd.value=g_order?PF_Pixel8{255,204,38,26}:PF_Pixel8{255,26,191,204};return 0;}
static void checkin_param(PF_InData*,PF_ParamDef*){g_checkins++;}
static PF_ColorParamSuite1 g_color_suite_instance={color_from_def}; static PF_ANSICallbacksSuite1 g_ansi_suite_instance={&std::sprintf};
namespace { struct State{PF_EffectWorld*input,*output;int pre=0,pixels=0,out=0,layer_checkin=0;bool preserve=true;}; State*st(PF_ProgPtr p){return static_cast<State*>(p);} PF_Err pre(PF_ProgPtr p,A_long,A_long,PF_RenderRequest*r,A_long,A_long,A_long,PF_CheckoutResult*o){st(p)->pre++;st(p)->preserve=r->preserve_rgb_of_zero_alpha;o->result_rect={0,0,1,1};o->max_result_rect=o->result_rect;return 0;} PF_Err pixels(PF_ProgPtr p,A_long,PF_EffectWorld**o){st(p)->pixels++;*o=st(p)->input;return 0;} PF_Err output(PF_ProgPtr p,PF_EffectWorld**o){st(p)->out++;*o=st(p)->output;return 0;} PF_Err layer_checkin(PF_ProgPtr p,A_long){st(p)->layer_checkin++;return 0;} }
static void valid_pixel(PF_Pixel8&p){p={255,26,191,204};}
static void valid_pixel(PF_Pixel16&p){p={32768,3341,24544,26214};}
static void valid_pixel(PF_PixelFloat&p){p={1,26/255.f,191/255.f,204/255.f};}
static OLMColorKeyInfo valid_info(){OLMColorKeyInfo i{};i.threshold=.085;i.color_space=3;i.force_lower_precision=1;i.edge_thin_distance_type=1;i.edge_blur_distance_type=1;i.edge_blur_direction=102;i.number_of_colors=2;i.use_color[0]=i.use_color[1]=true;i.colors8[0]={255,204,38,26};i.colors8[1]={255,26,191,204};i.colors[0]={1,204/255.f,38/255.f,26/255.f};i.colors[1]={1,26/255.f,191/255.f,204/255.f};return i;}
template<class P> static bool predicate_matrix(){constexpr int N=38;for(int m=0;m<N;m++){std::vector<std::uint8_t>ib(sizeof(P)+8,0),ob(sizeof(P)+8,0);valid_pixel(*reinterpret_cast<P*>(ib.data()));PF_EffectWorld in{ib.data(),(A_long)ib.size(),1,1,0,{0,0,1,1},0},out{ob.data(),(A_long)ob.size(),1,1,0,{0,0,1,1},0};OLMColorKeyInfo i=valid_info();switch(m){case 0:in.data=nullptr;break;case 1:out.data=nullptr;break;case 2:in.width=2;break;case 3:in.height=2;break;case 4:out.width=2;break;case 5:out.height=2;break;case 6:in.rowbytes++;break;case 7:out.rowbytes++;break;case 8:reinterpret_cast<P*>(ib.data())->alpha+=1;break;case 9:reinterpret_cast<P*>(ib.data())->red+=1;break;case 10:reinterpret_cast<P*>(ib.data())->green+=1;break;case 11:reinterpret_cast<P*>(ib.data())->blue+=1;break;case 12:i.color_keep=true;break;case 13:i.threshold=.086;break;case 14:i.premultiplied=true;break;case 15:i.color_space=4;break;case 16:i.force_lower_precision=2;break;case 17:i.per_color=true;break;case 18:i.per_component=true;break;case 19:i.edge_thin_amount=1;break;case 20:i.edge_thin_distance_type=2;break;case 21:i.edge_blur_amount=1;break;case 22:i.edge_blur_distance_type=2;break;case 23:i.edge_blur_direction=101;break;case 24:i.number_of_colors=1;break;case 25:i.enable_replace=true;break;case 26:i.use_color[0]=false;break;case 27:i.use_color[1]=false;break;case 28:i.colors[0].alpha=0;break;case 29:i.colors[0].red+=1.f/255;break;case 30:i.colors[0].green+=1.f/255;break;case 31:i.colors[0].blue+=1.f/255;break;case 32:i.colors[1].alpha=0;break;case 33:i.colors[1].red+=1.f/255;break;case 34:i.colors[1].green+=1.f/255;break;case 35:i.colors[1].blue+=1.f/255;break;}const PF_EffectWorld*ip=m==36?nullptr:&in;const PF_EffectWorld*op=m==37?nullptr:&out;if(IsBoundedLab76NativeTuple<P>(ip,op,i))return false;}std::vector<std::uint8_t>ib(sizeof(P)+8,0),ob(sizeof(P)+8,0);valid_pixel(*reinterpret_cast<P*>(ib.data()));PF_EffectWorld in{ib.data(),(A_long)ib.size(),1,1,0,{0,0,1,1},0},out{ob.data(),(A_long)ob.size(),1,1,0,{0,0,1,1},0};auto i=valid_info();if(!IsBoundedLab76NativeTuple<P>(&in,&out,i))return false;std::swap(i.colors8[0],i.colors8[1]);std::swap(i.colors[0],i.colors[1]);return IsBoundedLab76NativeTuple<P>(&in,&out,i);}
static bool classic_matrix(){constexpr int N=10;for(int m=0;m<N;m++){std::vector<std::uint8_t>ib(12,0),ob(12,0);PF_EffectWorld in{ib.data(),12,1,1,8,{0,0,1,1},0},out{ob.data(),13,1,1,8,{0,0,1,1},0};PF_PixelFormat inf=PF_PixelFormat_ARGB32,outf=PF_PixelFormat_ARGB32;switch(m){case 0:in.data=nullptr;break;case 1:out.data=nullptr;break;case 2:outf=PF_PixelFormat_ARGB64;break;case 3:in.width=0;break;case 4:in.height=0;break;case 5:out.width=2;break;case 6:out.height=2;break;case 7:in.rowbytes=3;break;case 8:out.rowbytes=3;break;case 9:inf=outf=PF_PixelFormat_INVALID;break;}if(ClassicWorldsMatch(&in,&out,inf,outf))return false;}std::vector<std::uint8_t>ib(12,0),ob(12,0);PF_EffectWorld in{ib.data(),12,1,1,8,{0,0,1,1},0},out{ob.data(),12,1,1,8,{0,0,1,1},0};return ClassicWorldsMatch(&in,&out,PF_PixelFormat_ARGB32,PF_PixelFormat_ARGB32);}
static bool classic_entry_matrix(){for(int depth:{8,16,32}){int ps=depth==8?4:depth==16?8:16;std::vector<std::uint8_t>ib(ps+8,0),ob(ps+8,0xCC);if(depth==8)valid_pixel(*reinterpret_cast<PF_Pixel8*>(ib.data()));else if(depth==16)valid_pixel(*reinterpret_cast<PF_Pixel16*>(ib.data()));else valid_pixel(*reinterpret_cast<PF_PixelFloat*>(ib.data()));PF_EffectWorld in{ib.data(),ps+8,1,1,(A_short)depth,{0,0,1,1},0},out{ob.data(),ps+8,1,1,(A_short)depth,{0,0,1,1},0};PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS]{};PF_ParamDef*params[OLMCOLORKEY_NUM_PARAMS];PF_InData id{nullptr,7,1,24,nullptr};PF_OutData od{};for(int j=0;j<OLMCOLORKEY_NUM_PARAMS;j++){params[j]=&defs[j];checkout_param(&id,j,0,0,0,&defs[j]);}defs[OLMCOLORKEY_INPUT].u.ld=in;if(EffectMain(PF_Cmd_RENDER,&id,&od,params,&out,nullptr))return false;}for(int m=0;m<7;m++){std::vector<std::uint8_t>ib(12,0),ob(12,0xCC);valid_pixel(*reinterpret_cast<PF_Pixel8*>(ib.data()));PF_EffectWorld in{ib.data(),12,1,1,8,{0,0,1,1},0},out{ob.data(),12,1,1,8,{0,0,1,1},0};PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS]{};PF_ParamDef*params[OLMCOLORKEY_NUM_PARAMS];PF_InData id{nullptr,7,1,24,nullptr};PF_OutData od{};for(int j=0;j<OLMCOLORKEY_NUM_PARAMS;j++){params[j]=&defs[j];checkout_param(&id,j,0,0,0,&defs[j]);}defs[OLMCOLORKEY_INPUT].u.ld=in;switch(m){case 0:defs[OLMCOLORKEY_INPUT].u.ld.data=nullptr;break;case 1:out.data=nullptr;break;case 2:out.bitdepth=16;break;case 3:out.width=2;break;case 4:out.height=2;break;case 5:defs[OLMCOLORKEY_INPUT].u.ld.rowbytes=3;break;case 6:out.rowbytes=3;break;}auto before=ob;PF_Err e=EffectMain(PF_Cmd_RENDER,&id,&od,params,&out,nullptr);if(e!=PF_Err_BAD_CALLBACK_PARAM||ob!=before)return false;}return true;}
static bool smart_null_matrix(){std::vector<std::uint8_t>ib(12,0),ob(12,0xCC);PF_EffectWorld in{ib.data(),12,1,1,8,{0,0,1,1},0},out{ob.data(),12,1,1,8,{0,0,1,1},0};for(int m=0;m<2;m++){State state{m?&in:nullptr,m?nullptr:&out};PF_InData id{&state,7,1,24,nullptr};PF_OutData od{};PF_SmartRenderInput sri{8,nullptr};PF_SmartRenderCallbacks src{pixels,output,layer_checkin};PF_SmartRenderExtra sre{&sri,&src};auto before=ob;PF_Err e=EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&sre);if(e!=PF_Err_BAD_CALLBACK_PARAM||state.pixels!=1||state.out!=m||state.layer_checkin!=1||ob!=before)return false;}return true;}
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;if(!predicate_matrix<PF_Pixel8>()||!predicate_matrix<PF_Pixel16>()||!predicate_matrix<PF_PixelFloat>())return 5;if(!classic_matrix())return 6;if(!classic_entry_matrix())return 7;if(!smart_null_matrix())return 8;constexpr int P=8;const std::vector<int>expected_order={1,2,4,5,6,7,8,9,10,11,14,15,18,19,20,22,23,26,28,29,30,31,24,25,27,34,36,37,38,39,32,33,35};for(g_order=0;g_order<2;g_order++)for(int depth:{8,16,32}){int ps=depth==8?4:depth==16?8:16,rb=ps+P;std::vector<std::uint8_t>inb(rb,0xA5),outb(rb,0xCC);if(depth==8)*reinterpret_cast<PF_Pixel8*>(inb.data())={255,26,191,204};else if(depth==16)*reinterpret_cast<PF_Pixel16*>(inb.data())={(A_u_short)std::lround(255*32768.0/255.0),(A_u_short)std::lround(26*32768.0/255.0),(A_u_short)std::lround(191*32768.0/255.0),(A_u_short)std::lround(204*32768.0/255.0)};else *reinterpret_cast<PF_PixelFloat*>(inb.data())={1,26/255.f,191/255.f,204/255.f};auto before=inb;PF_EffectWorld in{inb.data(),rb,1,1,(A_short)depth,{0,0,1,1},0},out{outb.data(),rb,1,1,(A_short)depth,{0,0,1,1},0};State state{&in,&out};PF_InData id{&state,7,1,24,nullptr};PF_OutData od{};PF_RenderRequest rr{false};PF_PreRenderInput pri{rr};PF_PreRenderOutput pro{};PF_PreRenderCallbacks prc{pre};PF_PreRenderExtra prex{&pri,&pro,&prc};g_checkout_order.clear();g_checkins=0;if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&prex))return 10;PF_SmartRenderInput sri{(A_short)depth,pro.pre_render_data};PF_SmartRenderCallbacks src{pixels,output,layer_checkin};PF_SmartRenderExtra sre{&sri,&src};if(EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&sre))return 11;bool input_same=inb==before,input_pad=true,output_pad=true;for(int i=ps;i<rb;i++){input_pad&=inb[i]==0xA5;output_pad&=outb[i]==0xCC;}bool order=g_checkout_order==expected_order;bool gates=state.pre==1&&state.pixels==1&&state.out==1&&state.layer_checkin==1&&!state.preserve&&g_checkins==33&&order&&input_same&&input_pad&&output_pad;if(!gates){std::fprintf(stderr,"gate order=%d depth=%d callbacks=%d/%d/%d/%d params=%zu/%d input=%d pads=%d/%d\n",g_order,depth,state.pre,state.pixels,state.out,state.layer_checkin,g_checkout_order.size(),g_checkins,input_same,input_pad,output_pad);return 20;}std::fwrite(outb.data(),1,ps,stdout);if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);}return 0;}
'''


def production_effectmain() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_lab76_order_prod_") as raw:
        directory = Path(raw)
        adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        generated = source.read_text(encoding="utf-8")
        generated = generated.replace(
            "#define PF_CHECKIN_PARAM(...) ((void)0)",
            "#define PF_CHECKIN_PARAM(in,p) checkin_param((in),(p))")
        generated = generated.replace(
            "OLMCOLORKEY_PREMULTIPLIED=3, OLMCOLORKEY_COLOR_SPACE=4, OLMCOLORKEY_FORCE_LOWER_PRECISION=5, OLMCOLORKEY_PER_COLOR=6, OLMCOLORKEY_PER_COMPONENT=7, OLMCOLORKEY_THRESHOLD_GROUP_START=8,",
            "OLMCOLORKEY_THRESHOLD_GROUP_START=3, OLMCOLORKEY_PREMULTIPLIED=4, OLMCOLORKEY_COLOR_SPACE=5, OLMCOLORKEY_FORCE_LOWER_PRECISION=6, OLMCOLORKEY_PER_COLOR=7, OLMCOLORKEY_PER_COMPONENT=8,")
        if "OLMCOLORKEY_THRESHOLD_GROUP_START=3, OLMCOLORKEY_PREMULTIPLIED=4" not in generated:
            raise RuntimeError("production parameter-enum patch anchor drifted")
        generated = generated.replace(
            "static PF_Err checkout_param(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*);",
            "static PF_Err checkout_param(PF_InData*,A_long,A_long,A_long,A_long,PF_ParamDef*); static void checkin_param(PF_InData*,PF_ParamDef*);")
        generated = generated.split("static std::vector<int> g_param_order", 1)[0] + HARNESS
        source.write_text(generated, encoding="utf-8")
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                             text=True, check=True).stdout.strip()
        executable = directory / "effectmain"
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
            "-framework", "Cocoa", "-o", str(executable),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def public_owner(directory: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    input_png = directory / "input.png"
    Image.new("RGBA", (1, 1), (26, 191, 204, 255)).save(input_png)
    if sha_path(input_png) != EXPECTED["input_png"]:
        raise AssertionError("fixture PNG serialization drift")
    rows = []
    for order in ("declared", "reverse"):
        for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
            output = directory / f"{order}-{depth}.png"
            result = subprocess.run([
                str(WORKER), "render-png", str(AEX), str(input_png), str(output),
                "--pixel-format", pixel_format, *owner_params(order),
            ], cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
            actual = json.loads(result.stdout)
            exact = (
                actual["render_error"] == 0 and actual["guards_intact"]
                and actual["raw_pixel_bytes"] == pixel_bytes
                and actual["raw_pixel_sha256"] == RAW_HASHES[order][depth]
                and actual["gpu"]["pre_render"]["completed"]
                and actual["gpu"]["render"]["completed"]
                and not actual["unsupported_suite_calls"]
                and actual["dropped_unsupported_suite_calls"] == 0
            )
            if not exact:
                raise AssertionError(f"public owner mismatch: {order}/{depth}: {actual}")
            rows.append({
                "order": order, "depth": depth, "pixel_format": pixel_format,
                "raw_pixel_bytes": pixel_bytes, "raw_pixel_sha256": actual["raw_pixel_sha256"],
                "smart_pre_render_completed": True, "smart_render_completed": True,
                "guards_intact": True, "unsupported_suite_calls": [], "status": "raw_exact",
            })

    trace_out = directory / "trace.png"
    trace_run = subprocess.run([
        str(WORKER), "render-trace-png", str(AEX), str(input_png), str(trace_out),
        "--pixel-format", "argb32f", "--watch", "function=0x9960,arg=stack5,size=1432",
        *owner_params("declared"),
    ], cwd=ROOT, capture_output=True, text=True)
    if trace_run.returncode:
        raise RuntimeError(trace_run.stderr)
    trace = json.loads(trace_run.stdout)
    smart = next(t for t in trace["execution_traces"] if t["selector"] == "SMART_RENDER")
    witness = smart["memory_witnesses"][0]
    record_hex = witness["after"]["hex"]
    record = bytes.fromhex(record_hex)
    semantic = {
        "depth_at_0x20": struct.unpack_from("<i", record, 0x20)[0],
        "color_space_at_0x30": struct.unpack_from("<i", record, 0x30)[0],
        "per_component_at_0x34": record[0x34], "per_color_at_0x35": record[0x35],
        "number_colors_at_0x38": struct.unpack_from("<i", record, 0x38)[0],
        "force_at_0x3c": struct.unpack_from("<i", record, 0x3C)[0],
        "threshold_f32_bits_at_0x50": f"0x{struct.unpack_from('<I', record, 0x50)[0]:08x}",
        "epsilon_f32_bits_at_0x54": f"0x{struct.unpack_from('<I', record, 0x54)[0]:08x}",
        "key1_argb_f32_bits_at_0x74": [f"0x{x:08x}" for x in struct.unpack_from("<4I", record, 0x74)],
        "key2_argb_f32_bits_at_0x84": [f"0x{x:08x}" for x in struct.unpack_from("<4I", record, 0x84)],
        "use_color_at_0x524_0x525": list(record[0x524:0x526]),
    }
    owner_record = {
        "watch": "function=0x9960,arg=stack5,size=1432", "function_rva": "0x9960",
        "pc_rva": f"0x{witness['pc_rva']:x}", "size": len(record),
        "after_sha256": witness["after"]["sha256"], "semantic_fields": semantic,
        "trace_guards_intact": trace["guards_intact"], "trace_truncated": smart["truncated"],
        "dropped_memory_witnesses": smart["dropped_memory_witnesses"],
    }
    if owner_record["after_sha256"] != EXPECTED["record_after"]:
        raise AssertionError("owner record drift")
    return rows, owner_record


def classifier_hook(per_component: bool = False) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    record = bytearray(0x598)
    struct.pack_into("<i", record, 0x20, 32)
    struct.pack_into("<i", record, 0x30, 3)
    record[0x34] = int(per_component)
    struct.pack_into("<i", record, 0x38, 2)
    struct.pack_into("<i", record, 0x3C, 1)
    struct.pack_into("<f", record, 0x50, 0.085)
    struct.pack_into("<f", record, 0x54, 1.0e-6)
    struct.pack_into("<3f", record, 0x58, 0.085, 0.085, 0.085)
    struct.pack_into("<4f", record, 0x74, 1.0, 204 / 255, 38 / 255, 26 / 255)
    struct.pack_into("<4f", record, 0x84, 1.0, 26 / 255, 191 / 255, 204 / 255)
    record[0x524] = record[0x525] = 1
    refcon = loader.host_alloc(len(record)); loader.write_bytes(refcon, bytes(record))
    source = loader.host_alloc(16); output = loader.host_alloc(16)
    loader.write_bytes(source, struct.pack("<4f", 1.0, 26 / 255, 191 / 255, 204 / 255))
    loader.write_bytes(output, b"\xA5" * 16)
    events: list[dict[str, object]] = []
    pointers: list[tuple[int, int]] = []

    def triple(address: int) -> dict[str, object]:
        raw = loader.read_bytes(address, 12)
        return {"f32_bits": f32_bits(raw), "values": list(struct.unpack("<3f", raw))}

    def hook(uc, address, _size, _user) -> None:
        if address == 0x1800043A0:
            key_ptr = uc.reg_read(UC_X86_REG_RCX)
            cmp_ptr = uc.reg_read(UC_X86_REG_RDX)
            pointers.append((key_ptr, cmp_ptr))
            events.append({"call": len(pointers) - 1, "point": "entry",
                           "key": triple(key_ptr), "comparison": triple(cmp_ptr)})
        else:
            key_ptr, cmp_ptr = pointers[-1]
            events.append({"call": len(pointers) - 1, "point": "post_mutation",
                           "key": triple(key_ptr), "comparison": triple(cmp_ptr)})

    loader.uc.hook_add(UC_HOOK_CODE, hook, begin=0x1800043A0, end=0x1800043A0)
    loader.uc.hook_add(UC_HOOK_CODE, hook, begin=0x180004404, end=0x180004404)
    call = loader.call_function(0x1800035D0,
                                int_args=[refcon, 0, 0, source, output],
                                max_instructions=500_000)
    return {
        "pixel_callback": "0x1800035d0", "classifier": "0x1800043a0",
        "post_mutation_hook": "0x180004404", "events": events,
        "per_component": per_component,
        "stage1_output_argb_f32_bits": [f"0x{x:08x}" for x in struct.unpack("<4I", loader.read_bytes(output, 16))],
        "instruction_count": call["instructions"],
        "interpretation": (
            "The PF32 stage-1 callback invokes the same classifier twice. Call 1 enters with the "
            "comparison triple already mutated by call 0; each local key is initially unmutated. "
            "The public final callback then applies Color Keep semantics."
        ),
    }


def run_regressions() -> dict[str, object]:
    commands = {
        "non_lab76": [sys.executable, "tools/emulation/test_olmcolorkey_colorspace_2_5_matrix_actual_aex_20260810.py"],
        "edge_thin": [sys.executable, "tools/emulation/test_olmcolorkey_edge_thin_family_actual_aex_20260810.py"],
        "edge_blur": [sys.executable, "tools/emulation/test_olmcolorkey_exported_owner_edge_blur_covering_20260812.py"],
        "replace_keep_premult": [sys.executable, "tools/emulation/test_olmcolorkey_keep_premult_replace_actual_aex_20260811.py"],
        "replace_edge_composition": [sys.executable, "tools/emulation/test_olmcolorkey_replace_edge_composition_actual_aex_20260811.py"],
    }
    results: dict[str, object] = {}
    for name, command in commands.items():
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"regression failed {name}: {run.stdout}\n{run.stderr}")
        results[name] = {
            "status": "pass", "command": command[1],
            "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
        }
    return results


EXPECTED_HOOK_EVENTS = [
    (0, "entry", ["0x42a5b69f", "0x43305df3", "0x42b8bece"], ["0x43460d86", "0xc3714b5d", "0xc30dce9a"]),
    (0, "post_mutation", ["0x42a5b69f", "0x439ab3b6", "0x437fdc55"], ["0x43460d86", "0xc2d883c8", "0x41ad72a0"]),
    (1, "entry", ["0x43460d86", "0xc3714b5d", "0xc30dce9a"], ["0x43460d86", "0xc2d883c8", "0x41ad72a0"]),
    (1, "post_mutation", ["0x43460d86", "0xc2d883c8", "0x41ad72a0"], ["0x43460d86", "0x41c63ca8", "0x43392b42"]),
]
EXPECTED_HOOK_VALUES = [
    ([82.85668182373047, 176.3669891357422, 92.37266540527344],
     [198.05282592773438, -241.2943878173828, -141.80703735351562]),
    ([82.85668182373047, 309.40399169921875, 255.8606719970703],
     [198.05282592773438, -108.25738525390625, 21.68096923828125]),
    ([198.05282592773438, -241.2943878173828, -141.80703735351562],
     [198.05282592773438, -108.25738525390625, 21.68096923828125]),
    ([198.05282592773438, -108.25738525390625, 21.68096923828125],
     [198.05282592773438, 24.779617309570312, 185.16897583007812]),
]
HOOK_INTERPRETATION = (
    "The PF32 stage-1 callback invokes the same classifier twice. Call 1 enters with the "
    "comparison triple already mutated by call 0; each local key is initially unmutated. "
    "The public final callback then applies Color Keep semantics."
)


def validate_report(report: dict[str, object]) -> bool:
    try:
        assert report["schema"] == "olmcolorkey.lab76-multikey-order-closure/1"
        assert report["status"] == "raw_exact" and report["claim_boundary"] == CLAIM
        identities = report["identities"]
        assert identities == {
            "aex_sha256": EXPECTED["aex"], "aexcompat_worker_sha256": EXPECTED["worker"],
            "aexcompat_commit": EXPECTED["worker_commit"], "production_source_sha256": EXPECTED["source"],
            "disasm_sha256": EXPECTED["disasm"], "decomp_sha256": EXPECTED["decomp"],
        }
        fixture = report["fixture"]
        assert fixture["dimensions"] == [1, 1] and fixture["rgba8"] == [26, 191, 204, 255]
        assert fixture["input_png_sha256"] == EXPECTED["input_png"]
        assert fixture["keys_declared_argb8"] == [list(KEYS["redish"]), list(KEYS["exact_cyan"])]
        assert fixture["parameters"] == owner_params("declared")
        assert fixture["row_padding_bytes"] == 8
        rows = report["public_owner"]
        assert len(rows) == 6
        assert {(row["order"], row["depth"]) for row in rows} == {
            (order, depth) for order in ("declared", "reverse") for depth in DEPTHS}
        for row in rows:
            assert row["status"] == "raw_exact"
            assert row["raw_pixel_sha256"] == RAW_HASHES[row["order"]][row["depth"]]
            assert row["raw_pixel_bytes"] == DEPTHS[row["depth"]][1]
            assert row["pixel_format"] == DEPTHS[row["depth"]][0]
            assert row["smart_pre_render_completed"] and row["smart_render_completed"]
            assert row["guards_intact"] and row["unsupported_suite_calls"] == []
        production = report["production_effectmain"]
        assert production["status"] == "raw_exact" and production["rows"] == rows
        assert production["chain"] == [
            "EffectMain SmartPreRender", "33 ordered parameter checkouts",
            "EffectMain SmartRender", "typed RenderWorld", "33 parameter checkins"]
        assert production["gates"] == {
            "smart_pre_render": 1, "checkout_layer_pixels": 1, "checkout_output": 1,
            "checkin_layer_pixels": 1, "parameter_checkouts": 33, "parameter_checkins": 33,
            "ordered_parameter_indices": True, "preserve_rgb_of_zero_alpha": False,
            "input_complete_buffer_unchanged": True, "input_padding_preserved": True,
            "output_padding_preserved": True, "row_padding_bytes": 8,
        }
        assert report["production_admission"] == {
            "new_rule_admitted_cells": 6,
            "orders": ["declared", "reverse"],
            "depths": ["PF8", "PF16", "PF32"],
            "predicate_one_away": {
                "mutations_per_depth": 38, "depths_tested": 3,
                "rejects": 114, "status": "all_rejected",
            },
            "classic_render_guard": {
                "valid_entries": {"PF8": 1, "PF16": 1, "PF32": 1},
                "valid_unequal_strides": True,
                "rejected_entry_mutations": 7, "rejected_helper_mutations": 10,
                "validates": ["input/output format", "data", "dimensions", "rowbytes"],
                "rejection_error": "PF_Err_BAD_CALLBACK_PARAM",
                "rejected_output_untouched": True,
            },
            "smart_null_world_guard": {
                "rejected_cases": ["null input world", "null output world"],
                "rejection_error": "PF_Err_BAD_CALLBACK_PARAM",
                "checkin_layer_pixels": 1,
                "output_untouched": True,
            },
            "outside_behavior": "valid outside tuples retain prior independently admitted behavior; invalid world layouts fail closed; neither admits destructive mutation/Euclidean behavior",
        }
        owner_record = report["owner_record"]
        assert owner_record["after_sha256"] == EXPECTED["record_after"] and owner_record["size"] == 1432
        assert owner_record["watch"] == "function=0x9960,arg=stack5,size=1432"
        assert owner_record["function_rva"] == "0x9960" and owner_record["pc_rva"] == "0x1a14"
        assert owner_record["trace_guards_intact"] is True
        assert owner_record["trace_truncated"] is False
        assert owner_record["dropped_memory_witnesses"] == 0
        semantic = owner_record["semantic_fields"]
        assert [semantic[k] for k in (
            "depth_at_0x20", "color_space_at_0x30", "per_component_at_0x34",
            "per_color_at_0x35", "number_colors_at_0x38", "force_at_0x3c",
        )] == [32, 3, 0, 0, 2, 1]
        assert semantic["threshold_f32_bits_at_0x50"] == "0x3dae147b"
        assert semantic["epsilon_f32_bits_at_0x54"] == "0x358637bd"
        assert semantic["key1_argb_f32_bits_at_0x74"] == [
            "0x3f800000", "0x3f4ccccd", "0x3e189899", "0x3dd0d0d1"]
        assert semantic["key2_argb_f32_bits_at_0x84"] == [
            "0x3f800000", "0x3dd0d0d1", "0x3f3fbfc0", "0x3f4ccccd"]
        assert semantic["use_color_at_0x524_0x525"] == [1, 1]
        assert report["classifier_hook"]["pixel_callback"] == "0x1800035d0"
        assert report["classifier_hook"]["classifier"] == "0x1800043a0"
        assert report["classifier_hook"]["post_mutation_hook"] == "0x180004404"
        assert report["classifier_hook"]["per_component"] is False
        events = report["classifier_hook"]["events"]
        assert len(events) == 4
        for event, expected, expected_values in zip(
                events, EXPECTED_HOOK_EVENTS, EXPECTED_HOOK_VALUES):
            call, point, key, comparison = expected
            assert event["call"] == call and event["point"] == point
            assert event["key"]["f32_bits"] == key
            assert event["comparison"]["f32_bits"] == comparison
            assert event["key"]["values"] == expected_values[0]
            assert event["comparison"]["values"] == expected_values[1]
        assert report["classifier_hook"]["instruction_count"] == 630
        assert report["classifier_hook"]["interpretation"] == HOOK_INTERPRETATION
        per_component = report["classifier_hook"]["per_component_witness"]
        assert per_component["per_component"] is True
        assert per_component["pixel_callback"] == "0x1800035d0"
        assert per_component["classifier"] == "0x1800043a0"
        assert per_component["post_mutation_hook"] == "0x180004404"
        assert per_component["instruction_count"] == 643
        assert per_component["interpretation"] == HOOK_INTERPRETATION
        assert per_component["stage1_output_argb_f32_bits"] == [
            "0x00000000", "0x3dd0d0d1", "0x3f3fbfc0", "0x3f4ccccd"]
        assert len(per_component["events"]) == 4
        for event, expected, expected_values in zip(
                per_component["events"], EXPECTED_HOOK_EVENTS, EXPECTED_HOOK_VALUES):
            call, point, key, comparison = expected
            assert event["call"] == call and event["point"] == point
            assert event["key"]["f32_bits"] == key
            assert event["comparison"]["f32_bits"] == comparison
            assert event["key"]["values"] == expected_values[0]
            assert event["comparison"]["values"] == expected_values[1]
        assert report["classifier_hook"]["stage1_output_argb_f32_bits"] == [
            "0x00000000", "0x3dd0d0d1", "0x3f3fbfc0", "0x3f4ccccd"]
        algorithm = report["native_algorithm"]
        assert algorithm["shared_mutation_ab"] == [133.03700256347656, 163.48800659179688]
        assert algorithm["scalar"] == "sqrt(dL*dL + da*da + db*db) <= ((threshold + epsilon) * 424.4352722167969f), FLOAT32 scalar order"
        assert algorithm["per_component_limits_retained"] == {
            "L": "threshold*151.300994873f + epsilon*2709.929931641f",
            "a": "threshold*264.367004394f + epsilon*578.713989258f",
            "b": "threshold*295.572998047f + epsilon*414.675994873f",
        }
        counter = report["counterfactuals"]
        assert counter["reverse_order_changes_all_three_raw_hashes"] is True
        assert counter["old_nonmutating_declared_hashes"] == RAW_HASHES["reverse"]
        assert counter["reason"] == "Without shared destructive mutation, the second exact-cyan key matches; reversing the native key order likewise makes it match before prior mutation."
        regressions = report["regressions"]
        expected_commands = {
            "non_lab76": "tools/emulation/test_olmcolorkey_colorspace_2_5_matrix_actual_aex_20260810.py",
            "edge_thin": "tools/emulation/test_olmcolorkey_edge_thin_family_actual_aex_20260810.py",
            "edge_blur": "tools/emulation/test_olmcolorkey_exported_owner_edge_blur_covering_20260812.py",
            "replace_keep_premult": "tools/emulation/test_olmcolorkey_keep_premult_replace_actual_aex_20260811.py",
            "replace_edge_composition": "tools/emulation/test_olmcolorkey_replace_edge_composition_actual_aex_20260811.py",
        }
        for name, command in expected_commands.items():
            assert regressions[name]["status"] == "pass"
            assert regressions[name]["command"] == command
            assert regressions[name]["stdout_sha256"] == REGRESSION_STDOUT_HASHES[name]
        assert set(regressions) == set(expected_commands)
        assert report["installation_status"] == {
            "status": "deferred_stale",
            "installed_binary_sha256": "350ed6eb00c078952ad512b621e3489e6e6ed47d9129e3c11748f547fc441230",
            "meaning": "The existing install smoke belongs to an earlier source and is not evidence for this tree; Universal rebuild/install and AE smoke are deferred to the parent task.",
        }
        assert report["fail_close"] == [
            "the new destructive mutation/Euclidean rule is not admitted outside the declared six cells; valid one-away tuples return to prior behavior and invalid layouts fail closed",
            "per-component output equivalence beyond the recorded mutation/limit ownership",
            "AE-host, GPU, current installed-plugin, or unpinned worker/AEX/source identity",
        ]
        return True
    except (AssertionError, KeyError, TypeError):
        return False


def main() -> int:
    actual_identities = {
        "aex_sha256": sha_path(AEX), "aexcompat_worker_sha256": sha_path(WORKER),
        "aexcompat_commit": EXPECTED["worker_commit"], "production_source_sha256": sha_path(SOURCE),
        "disasm_sha256": sha_path(DISASM), "decomp_sha256": sha_path(DECOMP),
    }
    expected_identities = {
        "aex_sha256": EXPECTED["aex"], "aexcompat_worker_sha256": EXPECTED["worker"],
        "aexcompat_commit": EXPECTED["worker_commit"], "production_source_sha256": EXPECTED["source"],
        "disasm_sha256": EXPECTED["disasm"], "decomp_sha256": EXPECTED["decomp"],
    }
    if actual_identities != expected_identities or not validate_current_identities():
        raise RuntimeError(f"pinned identity drift: {actual_identities}")

    production = production_effectmain()
    rows_from_production = []
    offset = 0
    for order in ("declared", "reverse"):
        for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
            raw = production[offset:offset + pixel_bytes]; offset += pixel_bytes
            digest = hashlib.sha256(raw).hexdigest()
            if digest != RAW_HASHES[order][depth]:
                raise AssertionError(f"production mismatch {order}/{depth}: {digest}")
            rows_from_production.append({
                "order": order, "depth": depth, "pixel_format": pixel_format,
                "raw_pixel_bytes": pixel_bytes, "raw_pixel_sha256": digest,
                "smart_pre_render_completed": True, "smart_render_completed": True,
                "guards_intact": True, "unsupported_suite_calls": [], "status": "raw_exact",
            })
    if offset != len(production):
        raise AssertionError("production output slicing drift")

    with tempfile.TemporaryDirectory(prefix="olmck_lab76_order_owner_") as raw:
        public_rows, owner_record = public_owner(Path(raw))
    if public_rows != rows_from_production:
        raise AssertionError("public/production row identity drift")
    hook = classifier_hook()
    hook["per_component_witness"] = classifier_hook(per_component=True)

    regressions = run_regressions()
    report = {
        "schema": "olmcolorkey.lab76-multikey-order-closure/1", "date": "2026-08-12",
        "status": "raw_exact", "claim_boundary": CLAIM, "identities": actual_identities,
        "fixture": {
            "dimensions": [1, 1], "rgba8": [26, 191, 204, 255],
            "input_png_sha256": EXPECTED["input_png"],
            "keys_declared_argb8": [list(KEYS["redish"]), list(KEYS["exact_cyan"])],
            "parameters": owner_params("declared"), "row_padding_bytes": 8,
        },
        "public_owner": public_rows,
        "production_effectmain": {
            "status": "raw_exact", "rows": rows_from_production,
            "chain": ["EffectMain SmartPreRender", "33 ordered parameter checkouts",
                      "EffectMain SmartRender", "typed RenderWorld", "33 parameter checkins"],
            "gates": {
                "smart_pre_render": 1, "checkout_layer_pixels": 1, "checkout_output": 1,
                "checkin_layer_pixels": 1, "parameter_checkouts": 33, "parameter_checkins": 33,
                "ordered_parameter_indices": True, "preserve_rgb_of_zero_alpha": False,
                "input_complete_buffer_unchanged": True, "input_padding_preserved": True,
                "output_padding_preserved": True, "row_padding_bytes": 8,
            },
        },
        "production_admission": {
            "new_rule_admitted_cells": 6,
            "orders": ["declared", "reverse"],
            "depths": ["PF8", "PF16", "PF32"],
            "predicate_one_away": {
                "mutations_per_depth": 38, "depths_tested": 3,
                "rejects": 114, "status": "all_rejected",
            },
            "classic_render_guard": {
                "valid_entries": {"PF8": 1, "PF16": 1, "PF32": 1},
                "valid_unequal_strides": True,
                "rejected_entry_mutations": 7, "rejected_helper_mutations": 10,
                "validates": ["input/output format", "data", "dimensions", "rowbytes"],
                "rejection_error": "PF_Err_BAD_CALLBACK_PARAM",
                "rejected_output_untouched": True,
            },
            "smart_null_world_guard": {
                "rejected_cases": ["null input world", "null output world"],
                "rejection_error": "PF_Err_BAD_CALLBACK_PARAM",
                "checkin_layer_pixels": 1,
                "output_untouched": True,
            },
            "outside_behavior": "valid outside tuples retain prior independently admitted behavior; invalid world layouts fail closed; neither admits destructive mutation/Euclidean behavior",
        },
        "owner_record": owner_record, "classifier_hook": hook,
        "native_algorithm": {
            "shared_mutation_ab": [133.03700256347656, 163.48800659179688],
            "scalar": "sqrt(dL*dL + da*da + db*db) <= ((threshold + epsilon) * 424.4352722167969f), FLOAT32 scalar order",
            "per_component_limits_retained": {
                "L": "threshold*151.300994873f + epsilon*2709.929931641f",
                "a": "threshold*264.367004394f + epsilon*578.713989258f",
                "b": "threshold*295.572998047f + epsilon*414.675994873f",
            },
        },
        "counterfactuals": {
            "reverse_order_changes_all_three_raw_hashes": True,
            "old_nonmutating_declared_hashes": RAW_HASHES["reverse"],
            "reason": "Without shared destructive mutation, the second exact-cyan key matches; reversing the native key order likewise makes it match before prior mutation.",
        },
        "regressions": regressions,
        "installation_status": {
            "status": "deferred_stale",
            "installed_binary_sha256": "350ed6eb00c078952ad512b621e3489e6e6ed47d9129e3c11748f547fc441230",
            "meaning": "The existing install smoke belongs to an earlier source and is not evidence for this tree; Universal rebuild/install and AE smoke are deferred to the parent task.",
        },
        "fail_close": [
            "the new destructive mutation/Euclidean rule is not admitted outside the declared six cells; valid one-away tuples return to prior behavior and invalid layouts fail closed",
            "per-component output equivalence beyond the recorded mutation/limit ownership",
            "AE-host, GPU, current installed-plugin, or unpinned worker/AEX/source identity",
        ],
    }
    if not validate_report(report):
        raise AssertionError("generated report failed closed validation")
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMColorKey Lab76 multi-key order closure\n\n"
        "Status: **raw exact**\n\n"
        "The actual exported Smart owner and Mac production EffectMain agree byte-for-byte for "
        "the declared and reversed 1x1 two-key tuple at PF8/PF16/PF32. The natural PF32 "
        "classifier hook records the destructive a/b mutation at each of two calls, including "
        "reuse of the first call's mutated comparison triple by the second call.\n\n"
        "Production also proves 33 ordered parameter checkouts/checkins, Smart lifecycle, input "
        "immutability, eight-byte input/output row-padding preservation, 114 one-away admission "
        "rejects, and classic input/output format/data/dimension/rowbytes guards. The current "
        "installed binary `350ed6eb...` is stale for this tree; rebuild/install and AE smoke are "
        "explicitly deferred. Smart null input/output worlds also reject with "
        "PF_Err_BAD_CALLBACK_PARAM after layer checkin.\n\n"
        f"Boundary: {CLAIM}\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "cells": len(public_rows), "report": str(REPORT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
