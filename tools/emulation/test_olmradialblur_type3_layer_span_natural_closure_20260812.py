#!/usr/bin/env python3
"""Hash-bound direct-owner closure for the bounded PF32 Zoom Type-3 layer lane."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as pf32  # noqa:E402
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDI  # noqa:E402

SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_layer_span_natural_closure_20260812.json"
DOC = REPORT.with_suffix(".md")
AEX_SHA = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
PRODUCTION_SOURCE_SHA256 = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
EXPECTED = {
    "source_span": "3bc2f042adbd8104b13cd61202b2f126e28904d95ceccd91d54376aed3b77e8f",
    "pre_blur": "65468046f663d30ac544be430c965ee2c305193561e09d4bf9753747e4cb24ff",
    "post_blur": "ab78b5eeb2bdc90834825d8b3db5e8c913bc3fc0ecfd70c2082210dde125756a",
    "output": "f6c99a9da495437861ef06d96b6188f52c783d41977885b475fabfa89c8ea1a7",
}
# Canonical JSON digest of the ordered ten-row projection
# (name, source kind/hash, layer hash, and the complete actual plane hash map).
# This binds every actual row independently of its matching production copy, so
# changing both sides of a non-canonical row cannot preserve validation.
EXPECTED_ROW_BINDING_SHA256 = "d004b0e4507cbe741d859a57ea40ba01489d37e17cd7fc662efcb743d6d11b33"
W, H, RB, ACTIVE = 9, 7, 160, 144


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def row_binding_sha256(rows: list[dict]) -> str:
    bound = [
        {key: row[key] for key in
         ("name", "source_kind", "source_sha256", "layer_sha256", "actual",
          "smart_output_sha256", "smart_matches_actual", "smart_matches_classic",
          "smart_padding_exact")}
        for row in rows
    ]
    canonical = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()
    return sha(canonical)


def layer_frame(inverse: bool = False) -> bytes:
    raw = bytearray(RB * H)
    for y in range(H):
        for x in range(W):
            values = (1.0, x / 8.0, y / 6.0, (x + y) / 14.0)
            if inverse:
                values = (0.75, 1.0 - x / 8.0, 1.0 - y / 6.0, 1.0 - (x + y) / 14.0)
            struct.pack_into("<4f", raw, y * RB + x * 16, *values)
    return bytes(raw)


def source_frame(kind: str = "canonical") -> bytes:
    if kind == "canonical":
        return pf32.source_frame()
    raw = bytearray(RB * H)
    for y in range(H):
        for x in range(W):
            if kind == "zero": values = (0.0, 0.0, 0.0, 0.0)
            elif kind == "constant": values = (0.75, 0.25, 0.5, 0.875)
            elif kind == "impulse": values = (1.0, 0.9, 0.2, 0.6) if (x, y) == (4, 3) else (0.0, 0.0, 0.0, 0.0)
            elif kind == "checker": values = (1.0, 0.8, 0.1, 0.6) if (x + y) % 2 else (0.5, 0.1, 0.7, 0.2)
            else: raise ValueError(kind)
            struct.pack_into("<4f", raw, y * RB + x * 16, *values)
        raw[y * RB + ACTIVE:(y + 1) * RB] = bytes([0xA0 + y]) * (RB - ACTIVE)
    return bytes(raw)


def actual_owner(layer: bytes, source: bytes) -> dict[str, bytes]:
    fixture = pf32.fixture
    base = fixture.zoom.fixture
    params = base.m4.load_case0010_params()
    params.update({"Blur Type": 1, "Center": (4.0, 3.0), "Quality": 5.0,
                   "Ratio": 1.0, "Angle": 0, "Outer Strength": 4,
                   "Outer Offset Mode": 1, "Outer Offset": 0,
                   "Inner Strength": 0, "Noise Variation": 0.0,
                   "Noise Type": 1, "Brightness Gain": 1.0, "Size Variation": 0.0})
    ld = base.AexLoader(str(base.m4.AEX_PATH), fast=True)
    ld.register_libm_impls(max_threads=1)
    sp = base.m4.build_host_suites(ld)
    render_ctx = base.m4.build_render_context(ld, sp)
    iw, _ = fixture.build_world(ld, source)
    seed = pf32.source_frame(True)
    ow, output_data = fixture.build_world(ld, seed)
    nw, _ = fixture.build_world(ld, layer)
    param = base.m4.build_param_block(ld)
    base.m4.install_reader_detours(ld, params)
    captured: dict[str, object] = {}

    def setup(cur, _address, _size):
        owner = cur.uc.reg_read(UC_X86_REG_RBX)
        render = cur.uc.reg_read(UC_X86_REG_RDI)
        cur.write_bytes(owner + 0x50, struct.pack("<I", 3))
        cur.write_bytes(owner + 0x3C, struct.pack("<f", 0.25))
        cur.write_bytes(owner + 0xA8, struct.pack("<Q", nw))
        cur.write_bytes(render + 0xFC, struct.pack("<i", W))
        cur.write_bytes(render + 0x100, struct.pack("<i", H))

    def composed(cur, _address, _size):
        owner = cur.uc.reg_read(UC_X86_REG_RBX)
        ptr = struct.unpack("<Q", cur.read_bytes(owner + 0x90, 8))[0]
        captured["source_span"] = cur.read_bytes(ptr, W * H * 4)

    def zoom_entry(cur, _address, _size):
        captured["zoom_work"] = cur.uc.reg_read(UC_X86_REG_RCX)

    def collapse(cur, _address, _size):
        if "pre_blur" in captured:
            return
        work = int(captured["zoom_work"])
        min_r = struct.unpack("<i", cur.read_bytes(work + 0x18, 4))[0]
        max_r = struct.unpack("<i", cur.read_bytes(work + 0x1C, 4))[0]
        step = struct.unpack("<f", cur.read_bytes(work + 0x14, 4))[0]
        angular = round(6.283185307179586 / step)
        cells = (max_r - min_r + 1) * angular
        captured["geometry"] = struct.pack("<II", angular, max_r - min_r + 1)
        ptr = struct.unpack("<Q", cur.read_bytes(work + 0x38, 8))[0]
        captured["pre_blur"] = cur.read_bytes(ptr, cells * 16)

    def returned(cur, _address, _size):
        work = int(captured["zoom_work"])
        ptr = struct.unpack("<Q", cur.read_bytes(work + 0x38, 8))[0]
        captured["post_blur"] = cur.read_bytes(ptr, len(captured["pre_blur"]))
        captured["returned"] = True

    for address, hook in ((0x180008078, setup), (0x1800082F3, composed),
                          (0x1800056F0, zoom_entry), (0x180005C9F, collapse),
                          (0x180008322, returned)):
        ld.add_code_hook(address, hook)
    ld.call_function(base.m4.FUN_180008690,
                     int_args=[0, 0, 0, param, render_ctx], max_instructions=5_000_000)
    try:
        ld.call_function(0x180007D30,
                         int_args=[render_ctx, 0, iw, ow, param], max_instructions=500_000_000)
    except RuntimeError:
        if not captured.get("returned"):
            raise
    captured["output"] = ld.read_bytes(output_data, RB * H)
    return {k: v for k, v in captured.items() if isinstance(v, bytes)}


def production(layer: bytes, source_bytes: bytes, geometry: bytes) -> dict[str, bytes]:
    angular, radius = struct.unpack("<II", geometry)
    cells = angular * radius
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial-type3-natural-") as raw:
        td = Path(raw)
        (td / "source.bin").write_bytes(source_bytes)
        (td / "layer.bin").write_bytes(layer)
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
static void put(const char*p,const void*d,size_t n){{std::ofstream(p,std::ios::binary).write((const char*)d,n);}}
static PF_Err get_format(const PF_EffectWorld*,PF_PixelFormat*f){{*f=PF_PixelFormat_ARGB128;return PF_Err_NONE;}}
static PF_WorldSuite2 world_suite{{nullptr,nullptr,get_format}};
static SPErr acquire(const char*,int32,const void**s){{*s=&world_suite;return kSPNoError;}}
static SPErr release(const char*,int32){{return kSPNoError;}}
static SPBasicSuite basic{{acquire,release}};
static void fill_param(A_long n,PF_ParamDef&p,PF_EffectWorld*iw=nullptr,PF_EffectWorld*nw=nullptr){{AEFX_CLR_STRUCT(p);if(n==OLMRADIALBLUR_INPUT&&iw)p.u.ld=*iw;if(n==OLMRADIALBLUR_NOISE_LAYER&&nw){{p.u.ld=*nw;p.u.ld.dephault=2;}}
 if(n==OLMRADIALBLUR_BLUR_TYPE)p.u.pd.value=1;if(n==OLMRADIALBLUR_CENTER){{p.u.td.x_value=4*65536;p.u.td.y_value=3*65536;}}if(n==OLMRADIALBLUR_OUTER_STRENGTH)p.u.sd.value=4;if(n==OLMRADIALBLUR_OUTER_OFFSET_MODE)p.u.pd.value=1;if(n==OLMRADIALBLUR_INNER_OFFSET_MODE)p.u.pd.value=1;if(n==OLMRADIALBLUR_REPEAT_BORDER)p.u.bd.value=TRUE;if(n==OLMRADIALBLUR_RATIO)p.u.fs_d.value=1;if(n==OLMRADIALBLUR_QUALITY)p.u.fs_d.value=5;if(n==OLMRADIALBLUR_BRIGHTNESS_GAIN)p.u.fs_d.value=1;if(n==OLMRADIALBLUR_NOISE_VARIATION)p.u.fs_d.value=25;if(n==OLMRADIALBLUR_NOISE_TYPE)p.u.pd.value=3;if(n==OLMRADIALBLUR_SEED)p.u.sd.value=1;if(n==OLMRADIALBLUR_THICKNESS)p.u.fs_d.value=3;}}
static PF_Err public_render(PF_EffectWorld&iw,PF_EffectWorld&nw,PF_EffectWorld&ow){{
 PF_ParamDef p[OLMRADIALBLUR_NUM_PARAMS]{{}};PF_ParamDef*pp[OLMRADIALBLUR_NUM_PARAMS]{{}};for(int n=0;n<OLMRADIALBLUR_NUM_PARAMS;n++){{pp[n]=&p[n];fill_param(n,p[n],&iw,&nw);}}
 PF_InData in{{}};in.pica_basicP=&basic;PF_OutData out{{}};return EffectMain(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);
}}
struct SmartHost{{PF_EffectWorld*iw,*nw,*ow;int pre_input=0,pre_noise=0,pixel_input=0,pixel_noise=0,output=0,layer_checkin=0,param_checkout=0,param_checkin=0;}};
static PF_Err checkout_param(PF_ProgPtr q,A_long n,A_long,A_long,A_u_long,PF_ParamDef*p){{auto*h=(SmartHost*)q;++h->param_checkout;fill_param(n,*p,h->iw,h->nw);return PF_Err_NONE;}}
static PF_Err checkin_param(PF_ProgPtr q,PF_ParamDef*){{++((SmartHost*)q)->param_checkin;return PF_Err_NONE;}}
static PF_Err pre_layer(PF_ProgPtr q,PF_ParamIndex n,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){{auto*h=(SmartHost*)q;if(n==OLMRADIALBLUR_INPUT)++h->pre_input;else if(n==OLMRADIALBLUR_NOISE_LAYER)++h->pre_noise;else return PF_Err_BAD_CALLBACK_PARAM;AEFX_CLR_STRUCT(*r);r->result_rect={{0,0,9,7}};r->max_result_rect=r->result_rect;r->ref_width=9;r->ref_height=7;return PF_Err_NONE;}}
static PF_Err pixel_layer(PF_ProgPtr q,A_long n,PF_EffectWorld**w){{auto*h=(SmartHost*)q;if(n==OLMRADIALBLUR_INPUT){{++h->pixel_input;*w=h->iw;}}else if(n==OLMRADIALBLUR_NOISE_LAYER){{++h->pixel_noise;*w=h->nw;}}else return PF_Err_BAD_CALLBACK_PARAM;return PF_Err_NONE;}}
static PF_Err pixel_checkin(PF_ProgPtr q,A_long){{++((SmartHost*)q)->layer_checkin;return PF_Err_NONE;}}
static PF_Err checkout_output(PF_ProgPtr q,PF_EffectWorld**w){{auto*h=(SmartHost*)q;++h->output;*w=h->ow;return PF_Err_NONE;}}
static PF_Err public_smart(PF_EffectWorld&iw,PF_EffectWorld&nw,PF_EffectWorld&ow){{SmartHost h{{&iw,&nw,&ow}};PF_InData in{{}};in.effect_ref=(PF_ProgPtr)&h;in.current_time=0;in.time_step=1;in.time_scale=1;in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;PF_OutData out{{}};PF_PreRenderInput pri{{}};PF_PreRenderOutput pro{{}};PF_PreRenderCallbacks prc{{pre_layer,nullptr}};PF_PreRenderExtra pre{{&pri,&pro,&prc}};PF_Err err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre);if(err)return err;PF_SmartRenderInput sri{{}};sri.bitdepth=32;sri.pre_render_data=pro.pre_render_data;PF_SmartRenderCallbacks src{{pixel_layer,pixel_checkin,checkout_output}};PF_SmartRenderExtra smart{{&sri,&src}};err=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&smart);if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);if(err)return err;return h.pre_input==1&&h.pre_noise==1&&h.pixel_input==1&&h.pixel_noise==1&&h.output==1&&h.layer_checkin==2&&h.param_checkout==32&&h.param_checkin==32?PF_Err_NONE:PF_Err_BAD_CALLBACK_PARAM;}}
int main(int argc,char**argv){{constexpr int W=9,H=7,RB=160,C={cells};
std::vector<unsigned char> ib(RB*H),lb(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());std::ifstream(argv[2],std::ios::binary).read((char*)lb.data(),lb.size());
auto input_before=ib,layer_before=lb;for(int y=0;y<H;y++)for(int x=144;x<RB;x++)ob[y*RB+x]=(unsigned char)(0xA0+y);
PF_EffectWorld iw{{}},ow{{}},nw{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;iw.extent_hint={{0,0,W,H}};ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;ow.extent_hint={{0,0,W,H}};nw.data=(PF_PixelPtr)lb.data();nw.rowbytes=RB;nw.width=W;nw.height=H;nw.extent_hint={{0,0,W,H}};
OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x=4;i.center_y=3;i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation=25;i.noise_type=3;i.noise_layer=2;i.seed=1;i.thickness=3;i.comp_width=W;i.comp_height=H;
std::vector<float> pre(C*4),post(C*4),source_span(W*H,1.0f);RadialBlurTestPolarCapture cap{{}};cap.pre_blur_rgba=pre.data();cap.post_blur_rgba=post.data();cap.capacity_floats=C*4;cap.capacity_cells=C;
if(ComposeType3LayerSpanAEX<PF_PixelFloat>(&iw,&nw,0.25f,source_span.data(),source_span.data(),W*H))return 2;
auto e=RenderZoomTyped<PF_PixelFloat>(&iw,&ow,i,&cap,&nw);if(e||cap.written_floats!=C*4)return 3;put(argv[4],source_span.data(),source_span.size()*4);put(argv[5],pre.data(),pre.size()*4);put(argv[6],post.data(),post.size()*4);
ob.assign(RB*H,0);for(int y=0;y<H;y++)for(int x=144;x<RB;x++)ob[y*RB+x]=(unsigned char)(0xA0+y);if(public_render(iw,nw,ow))return 4;if(ib!=input_before||lb!=layer_before)return 5;put(argv[3],ob.data(),ob.size());
auto classic_output=ob;ob.assign(RB*H,0);for(int y=0;y<H;y++)for(int x=144;x<RB;x++)ob[y*RB+x]=(unsigned char)(0xA0+y);if(public_smart(iw,nw,ow))return 6;if(ib!=input_before||lb!=layer_before||ob!=classic_output)return 7;put(argv[8],ob.data(),ob.size());
auto reject=[&](PF_EffectWorld*layer,short depth){{ob.assign(RB*H,0x5a);auto before=ob;return OLMRadialBlurTestRenderWorldWithNoiseLayer(&iw,&ow,layer,&i,depth)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;}};auto base=i;
if(!reject(nullptr,32))return 10;nw.width=8;if(!reject(&nw,32))return 11;nw.width=9;nw.extent_hint.left=1;if(!reject(&nw,32))return 12;nw.extent_hint.left=0;nw.rowbytes=159;if(!reject(&nw,32))return 13;nw.rowbytes=160;nw.data=nullptr;if(!reject(&nw,32))return 14;nw.data=(PF_PixelPtr)lb.data();
iw.width=8;if(!reject(&nw,32))return 15;iw.width=9;iw.rowbytes=159;if(!reject(&nw,32))return 16;iw.rowbytes=160;iw.data=nullptr;if(!reject(&nw,32))return 17;iw.data=(PF_PixelPtr)ib.data();ow.height=6;if(!reject(&nw,32))return 18;ow.height=7;ow.rowbytes=159;if(!reject(&nw,32))return 19;ow.rowbytes=160;if(!reject(&nw,16))return 20;
i=base;i.blur_type=2;if(!reject(&nw,32))return 21;i=base;i.center_x=5;if(!reject(&nw,32))return 22;i=base;i.center_y=4;if(!reject(&nw,32))return 23;i=base;i.outer_strength=5;if(!reject(&nw,32))return 24;i=base;i.outer_edge_fade=1;if(!reject(&nw,32))return 25;i=base;i.outer_offset_mode=2;if(!reject(&nw,32))return 26;i=base;i.outer_offset=1;if(!reject(&nw,32))return 27;i=base;i.inner_strength=1;if(!reject(&nw,32))return 28;i=base;i.inner_edge_fade=1;if(!reject(&nw,32))return 29;i=base;i.inner_offset_mode=2;if(!reject(&nw,32))return 30;i=base;i.inner_offset=1;if(!reject(&nw,32))return 31;
i=base;i.repeat_border=FALSE;if(!reject(&nw,32))return 32;i=base;i.ratio=2;if(!reject(&nw,32))return 33;i=base;i.angle_deg=1;if(!reject(&nw,32))return 34;i=base;i.quality=4;if(!reject(&nw,32))return 35;i=base;i.brightness_gain=2;if(!reject(&nw,32))return 36;i=base;i.size_variation=1;if(!reject(&nw,32))return 37;i=base;i.noise_variation=26;if(!reject(&nw,32))return 38;i=base;i.noise_variation=0;if(!reject(nullptr,32))return 39;i=base;i.noise_type=2;if(!reject(&nw,32))return 40;i=base;i.seed=2;if(!reject(&nw,32))return 41;i=base;i.noise_offset=1;if(!reject(&nw,32))return 42;i=base;i.thickness=4;if(!reject(&nw,32))return 43;i=base;i.comp_width=8;if(!reject(&nw,32))return 44;i=base;i.comp_height=6;if(!reject(&nw,32))return 45;
std::ofstream(argv[7])<<"null_layer,layer_size,layer_origin,layer_rowbytes,layer_data,input_size,input_rowbytes,input_data,output_size,output_rowbytes,depth,blur_type,center_x,center_y,outer_strength,outer_fade,outer_mode,outer_offset,inner_strength,inner_fade,inner_mode,inner_offset,repeat,ratio,angle,quality,brightness,size_variation,nv26,nv0,noise_type,seed,noise_offset,thickness,comp_width,comp_height";return 0;}}
''')
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        cmd = [_UCRT_CXX, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
               "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")),
               "-I", str(resolve_asset(ROOT / "Util")), "-I", str(resolve_asset(ROOT / "Resources")), str(cpp),
               str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
               str(resolve_asset(ROOT / str(resolve_asset("Util/AEGP_SuiteHandler.cpp")))), str(resolve_asset(ROOT / str(resolve_asset("Util/MissingSuiteError.cpp")))),
               "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        names = ("output", "source_span", "pre_blur", "post_blur", "fail_close", "smart_output")
        paths = [td / f"{name}.bin" for name in names]
        subprocess.run([str(exe), str(td / "source.bin"), str(td / "layer.bin"),
                        *(str(path) for path in paths)], cwd=ROOT, check=True)
        return {name: path.read_bytes() for name, path in zip(names, paths)}


def static_and_regression_gates() -> dict:
    source = SOURCE.read_text()
    required = ["use_aex_typed_zoom_type3_layer_span_small", "noise_world->rowbytes == input->rowbytes",
                "ComposeType3LayerSpanAEX<PixelT>", "info.noise_variation == 25.0",
                "info.thickness == 3.0", "if (bitdepth == 16) return RenderZoom16"]
    missing = [token for token in required if token not in source]
    host = subprocess.run([sys.executable, str(HERE / "test_olmradialblur_type3_host_plumbing_20260811.py")],
                          cwd=ROOT, capture_output=True, text=True)
    return {"production_tokens_complete": not missing, "missing": missing,
            "host_layer_checkout_checkin_regression_pass": host.returncode == 0,
            "host_stdout_sha256": sha(host.stdout.encode())}


def generate() -> dict:
    if sha(pf32.fixture.zoom.fixture.m4.AEX_PATH.read_bytes()) != AEX_SHA:
        raise AssertionError("AEX identity drift")
    if sha(SOURCE.read_bytes()) != PRODUCTION_SOURCE_SHA256:
        raise AssertionError("production source identity drift")
    rows = []
    captures = {}
    matrix = [(source_kind, inverse) for source_kind in
              ("canonical", "zero", "constant", "impulse", "checker")
              for inverse in (False, True)]
    for source_kind, inverse in matrix:
        name = source_kind + ("_inverse_layer" if inverse else "_canonical_layer")
        layer = layer_frame(inverse); source_bytes = source_frame(source_kind)
        actual = actual_owner(layer, source_bytes)
        mac = production(layer, source_bytes, actual["geometry"])
        matches = {plane: actual[plane] == mac[plane] for plane in EXPECTED}
        padding = all(mac["output"][y * RB + ACTIVE:(y + 1) * RB] ==
                      bytes([0xA0 + y]) * (RB - ACTIVE) for y in range(H))
        smart_padding = all(mac["smart_output"][y * RB + ACTIVE:(y + 1) * RB] ==
                            bytes([0xA0 + y]) * (RB - ACTIVE) for y in range(H))
        rows.append({"name": name, "source_kind": source_kind,
                     "source_sha256": sha(source_bytes), "layer_sha256": sha(layer),
                     "actual": {plane: sha(actual[plane]) for plane in EXPECTED},
                     "production": {plane: sha(mac[plane]) for plane in EXPECTED},
                     "matches": matches, "padding_exact": padding,
                     "smart_output_sha256": sha(mac["smart_output"]),
                     "smart_matches_actual": mac["smart_output"] == actual["output"],
                     "smart_matches_classic": mac["smart_output"] == mac["output"],
                     "smart_padding_exact": smart_padding,
                     "production_entry": "EffectMain(PF_Cmd_RENDER)",
                     "fail_close_checks": mac["fail_close"].decode().split(",")})
        captures[name] = actual
    canonical_hash_bound = row_binding_sha256(rows) == EXPECTED_ROW_BINDING_SHA256
    counterfactual_effective = (
        captures["canonical_canonical_layer"]["source_span"] != captures["canonical_inverse_layer"]["source_span"] and
        captures["canonical_canonical_layer"]["post_blur"] != captures["canonical_inverse_layer"]["post_blur"])
    gates = static_and_regression_gates()
    exact = (canonical_hash_bound and counterfactual_effective and
             all(all(row["matches"].values()) and row["padding_exact"] and
                 len(row["fail_close_checks"]) == 36 for row in rows) and
             gates["production_tokens_complete"] and gates["host_layer_checkout_checkin_regression_pass"])
    report = {
        "kind": "olmradialblur_type3_layer_span_natural_closure_20260812",
        "status": "exact" if exact else "mismatch",
        "scope": "PF32 Zoom only; 9x7; rowbytes 160; same-origin/same-size Type-3 Layer; center(4,3), Outer4, Inner/Size0, NV25, Repeat on, Ratio1, Angle0, Quality5, Brightness1, Seed1, Offset0, Thickness3.",
        "aex": {"sha256": AEX_SHA, "owner": "0x180007d30", "composer": "0x180006aa0", "zoom_core": "0x1800056f0",
                "execution": "direct internal owner; Type3/NV25/Layer pointer injected at owner setup hook after public parameter setup"},
        "expected_canonical_hashes": EXPECTED,
        "rows": rows,
        "content_basis": {"source": ["canonical", "zero", "constant", "impulse", "checker"],
                          "layer": ["canonical_gradient", "inverse_gradient"], "cross_product_rows": 10},
        "gates": {**gates, "canonical_hash_bound": canonical_hash_bound,
                  "counterfactual_layer_changes_span_and_post_blur": counterfactual_effective,
                  "input_and_layer_invariant": True},
        "lifecycle": {"classic_public_numerical_entry": "EffectMain(PF_Cmd_RENDER), exact for all 10 content-basis rows",
                      "smart_public_numerical_entry": "EffectMain(PF_Cmd_SMART_PRE_RENDER) -> EffectMain(PF_Cmd_SMART_RENDER), exact for all 10 content-basis rows",
                      "smart_success_counts": {"pre_layer_checkout": 2, "pixel_checkout": 2, "output_checkout": 1, "pixel_checkin": 2, "parameter_checkout": 32, "parameter_checkin": 32},
                      "checkout_order": ["Input", "Noise Layer"],
                      "checkin_order": ["Noise Layer", "Input"],
                      "public_dispatch": "EffectMain(PF_Cmd_RENDER) -> Render -> RenderWorld -> RenderZoomFloat -> exact composer/worker"},
        "fail_closed": ["null Layer", "Layer format mismatch at host boundary", "Layer origin/size mismatch",
                        "unlisted PF8/PF16 source or Layer", "other Type3 geometry/rowbytes", "other Type3 parameter tuple or Noise Variation"],
        "unowned_control": "noise_layer selector value is host-owned and intentionally not used by numerical admission; the checked-out noise_world identity is authoritative",
        "source_sha256": PRODUCTION_SOURCE_SHA256,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur PF32 Type-3 Layer natural closure — 2026-08-12\n\n"
                   f"Status: **{report['status']}**.\n\n"
                   "The fixed 9×7 PF32 Zoom/NV25 tuple connects the public Layer world to the exact Type-3 composer and Zoom worker. Direct internal actual-owner execution, public Mac classic `EffectMain(PF_Cmd_RENDER)`, and public Mac `SMART_PRE_RENDER -> SMART_RENDER` match raw-exact for source span, pre/post polar planes, padded output, and canonical/zero/constant/impulse/checker sources crossed with normal/inverse Layer gradients (10 rows). Input and Layer storage remain unchanged. Smart success checks out two pre-render layers, two pixel worlds, one output and 32 parameters, then balances both pixel and all parameter checkins before atomic commit.\n\n"
                   "PF8/PF16 states outside the separately bound all-depth source/Layer tuple, other Type-3 geometry, rowbytes, origin, null/mismatched Layer, and unlisted Type-3 parameters remain fail-closed. This is not an install or native-AE pixel claim.\n")
    return report


def validate(report: dict) -> None:
    assert report["kind"] == "olmradialblur_type3_layer_span_natural_closure_20260812"
    assert report["status"] == "exact"
    assert report["scope"] == "PF32 Zoom only; 9x7; rowbytes 160; same-origin/same-size Type-3 Layer; center(4,3), Outer4, Inner/Size0, NV25, Repeat on, Ratio1, Angle0, Quality5, Brightness1, Seed1, Offset0, Thickness3."
    assert report["aex"] == {"sha256": AEX_SHA, "owner": "0x180007d30",
                             "composer": "0x180006aa0", "zoom_core": "0x1800056f0",
                             "execution": "direct internal owner; Type3/NV25/Layer pointer injected at owner setup hook after public parameter setup"}
    assert report["expected_canonical_hashes"] == EXPECTED
    assert report["source_sha256"] == PRODUCTION_SOURCE_SHA256
    assert sha(SOURCE.read_bytes()) == PRODUCTION_SOURCE_SHA256
    assert len(report["rows"]) == 10
    assert report["rows"][0]["actual"] == EXPECTED
    assert row_binding_sha256(report["rows"]) == EXPECTED_ROW_BINDING_SHA256
    expected_rejects = "null_layer,layer_size,layer_origin,layer_rowbytes,layer_data,input_size,input_rowbytes,input_data,output_size,output_rowbytes,depth,blur_type,center_x,center_y,outer_strength,outer_fade,outer_mode,outer_offset,inner_strength,inner_fade,inner_mode,inner_offset,repeat,ratio,angle,quality,brightness,size_variation,nv26,nv0,noise_type,seed,noise_offset,thickness,comp_width,comp_height".split(",")
    assert report["content_basis"] == {"source": ["canonical", "zero", "constant", "impulse", "checker"],
                                        "layer": ["canonical_gradient", "inverse_gradient"], "cross_product_rows": 10}
    matrix = [(source_kind, inverse) for source_kind in
              ("canonical", "zero", "constant", "impulse", "checker") for inverse in (False, True)]
    for row, (source_kind, inverse) in zip(report["rows"], matrix):
        name = source_kind + ("_inverse_layer" if inverse else "_canonical_layer")
        assert row["name"] == name and row["source_kind"] == source_kind
        assert row["source_sha256"] == sha(source_frame(source_kind))
        assert row["layer_sha256"] == sha(layer_frame(inverse))
        assert row["actual"] == row["production"]
        assert set(row["actual"]) == set(EXPECTED) and all(
            isinstance(value, str) and len(value) == 64 for value in row["actual"].values())
        assert row["matches"] == {plane: True for plane in EXPECTED}
        assert row["padding_exact"] and row["production_entry"] == "EffectMain(PF_Cmd_RENDER)"
        assert row["smart_output_sha256"] == row["actual"]["output"]
        assert row["smart_matches_actual"] and row["smart_matches_classic"]
        assert row["smart_padding_exact"]
        assert row["fail_close_checks"] == expected_rejects
    assert all(report["gates"][key] for key in ("canonical_hash_bound",
               "counterfactual_layer_changes_span_and_post_blur", "input_and_layer_invariant",
               "production_tokens_complete", "host_layer_checkout_checkin_regression_pass"))
    assert report["gates"]["missing"] == []
    assert report["fail_closed"] == ["null Layer", "Layer format mismatch at host boundary",
        "Layer origin/size mismatch", "unlisted PF8/PF16 source or Layer", "other Type3 geometry/rowbytes",
        "other Type3 parameter tuple or Noise Variation"]
    assert report["unowned_control"] == "noise_layer selector value is host-owned and intentionally not used by numerical admission; the checked-out noise_world identity is authoritative"
    assert report["lifecycle"] == {
        "classic_public_numerical_entry": "EffectMain(PF_Cmd_RENDER), exact for all 10 content-basis rows",
        "smart_public_numerical_entry": "EffectMain(PF_Cmd_SMART_PRE_RENDER) -> EffectMain(PF_Cmd_SMART_RENDER), exact for all 10 content-basis rows",
        "smart_success_counts": {"pre_layer_checkout": 2, "pixel_checkout": 2,
            "output_checkout": 1, "pixel_checkin": 2, "parameter_checkout": 32,
            "parameter_checkin": 32},
        "checkout_order": ["Input", "Noise Layer"], "checkin_order": ["Noise Layer", "Input"],
        "public_dispatch": "EffectMain(PF_Cmd_RENDER) -> Render -> RenderWorld -> RenderZoomFloat -> exact composer/worker"}
    current_gates = static_and_regression_gates()
    assert report["gates"]["host_stdout_sha256"] == current_gates["host_stdout_sha256"]


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true",
                      help="regenerate the checked-in report and documentation")
    mode.add_argument("--validate-only", action="store_true",
                      help="validate checked-in artifacts (the default)")
    args = parser.parse_args()
    report = generate() if args.write else json.loads(REPORT.read_text())
    validate(report)
    print(json.dumps({"status": report["status"], "rows": len(report["rows"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
