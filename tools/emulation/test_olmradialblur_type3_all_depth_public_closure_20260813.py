#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative

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
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as pf32
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as pf16
import test_olmradialblur_zoom_pf8_small_actual_aex_20260805 as pf8
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDI

SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_all_depth_public_closure_20260813.json"
DOC = REPORT.with_suffix(".md")
SOURCE_SHA256 = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_ROWS_SHA256 = "ac9651a8b544224bb619f4740cebb3cc4a06eedb4d11bba1bce83279174f94cf"
CONFIG = {
    8: dict(module=pf8, owner=0x180007520, setup=0x180007868, composed=0x180007AE3,
            returned=0x180007B12, cpp="PF_Pixel8", rb=44, pixel=4, format="PF_PixelFormat_ARGB32"),
    16: dict(module=pf16, owner=0x180006D10, setup=0x180007058, composed=0x1800072D3,
             returned=0x180007302, cpp="PF_Pixel16", rb=80, pixel=8, format="PF_PixelFormat_ARGB64"),
    32: dict(module=pf32, owner=0x180007D30, setup=0x180008078, composed=0x1800082F3,
             returned=0x180008322, cpp="PF_PixelFloat", rb=160, pixel=16, format="PF_PixelFormat_ARGB128"),
}
W, H = 9, 7
ORIG_ROT_BUILD_WORLD = pf16.fixture.build_world
ORIG_ROT_SOURCE_FRAME = pf16.fixture.source_frame


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def f32_census(left: bytes, right: bytes) -> dict[str, object]:
    count = min(len(left), len(right)) // 4
    a = struct.unpack(f"<{count}f", left[:count * 4])
    b = struct.unpack(f"<{count}f", right[:count * 4])
    indexes = [index for index, (x, y) in enumerate(zip(a, b)) if struct.pack("<f", x) != struct.pack("<f", y)]
    return {"words": count, "left_words": len(left)//4, "right_words": len(right)//4,
            "left_nonzero": sum(struct.pack("<f", x) != b"\0\0\0\0" for x in a),
            "right_nonzero": sum(struct.pack("<f", x) != b"\0\0\0\0" for x in b),
            "different": len(indexes), "first": indexes[0] if indexes else None,
            "actual_first16": list(a[:16]), "candidate_first16": list(b[:16])}


def source(depth: int, kind: str = "canonical") -> bytes:
    if kind != "canonical":
        cfg = CONFIG[depth]
        raw = bytearray(cfg["rb"] * H)
        maximum = 255 if depth == 8 else 32768 if depth == 16 else None
        for y in range(H):
            for x in range(W):
                if depth == 32:
                    if kind == "zero": values = (0.0, 0.0, 0.0, 0.0)
                    elif kind == "constant": values = (0.75, 0.25, 0.5, 0.875)
                    elif kind == "impulse": values = (1.0, 0.9, 0.2, 0.6) if (x, y) == (4, 3) else (0.0, 0.0, 0.0, 0.0)
                    elif kind == "checker": values = (1.0, 0.8, 0.1, 0.6) if (x + y) % 2 else (0.5, 0.1, 0.7, 0.2)
                    else: raise ValueError(kind)
                    struct.pack_into("<4f", raw, y * cfg["rb"] + x * 16, *values)
                else:
                    assert maximum is not None
                    if kind == "zero": values = (0, 0, 0, 0)
                    elif kind == "constant": values = (maximum * 3 // 4, maximum // 4, maximum // 2, maximum * 7 // 8)
                    elif kind == "impulse": values = ((maximum, maximum * 9 // 10, maximum // 5, maximum * 3 // 5)
                                                        if (x, y) == (4, 3) else (0, 0, 0, 0))
                    elif kind == "checker": values = ((maximum, maximum * 4 // 5, maximum // 10, maximum * 3 // 5)
                                                        if (x + y) % 2 else
                                                        (maximum // 2, maximum // 10, maximum * 7 // 10, maximum // 5))
                    else: raise ValueError(kind)
                    struct.pack_into("<4B" if depth == 8 else "<4H", raw,
                                     y * cfg["rb"] + x * cfg["pixel"], *values)
            active = W * cfg["pixel"]
            raw[y * cfg["rb"] + active:(y + 1) * cfg["rb"]] = bytes([0xA0 + y]) * (cfg["rb"] - active)
        return bytes(raw)
    if depth == 8:
        raw = bytearray(44 * H)
        for y in range(H):
            for x in range(W):
                struct.pack_into("<4B", raw, y * 44 + x * 4,
                                 255 if (x + y) % 5 else 127,
                                 (x * 31 + y * 7) % 256,
                                 (x * 11 + y * 29) % 256,
                                 (x * 47 + y * 13) % 256)
            raw[y * 44 + 36:(y + 1) * 44] = bytes([0xA0 + y]) * 8
        return bytes(raw)
    if depth == 16:
        raw = bytearray(80 * H)
        for y in range(H):
            for x in range(W):
                struct.pack_into("<4H", raw, y * 80 + x * 8,
                                 32768 if (x + y) % 5 else 16384,
                                 (x * 4093 + y * 257) % 32769,
                                 (x * 1237 + y * 3559) % 32769,
                                 (x * 7919 + y * 911) % 32769)
            raw[y * 80 + 72:(y + 1) * 80] = bytes([0xA0 + y]) * 8
        return bytes(raw)
    raw = bytearray(160 * H)
    for y in range(H):
        for x in range(W):
            struct.pack_into("<4f", raw, y * 160 + x * 16,
                             1.0 if (x + y) % 5 else 0.5,
                             ((x * 31 + y * 7) % 257) / 256.0,
                             ((x * 11 + y * 29) % 257) / 256.0,
                             ((x * 47 + y * 13) % 257) / 256.0)
        raw[y * 160 + 144:(y + 1) * 160] = bytes([0xA0 + y]) * 16
    return bytes(raw)


def layer(depth: int, family: str = "all_depth") -> bytes:
    cfg = CONFIG[depth]
    raw = bytearray(cfg["rb"] * H)
    for y in range(H):
        for x in range(W):
            if depth == 8:
                values = (255 if family == "natural" else 191,
                          (x * 255) // 8, (y * 255) // 6, ((x + y) * 255) // 14)
                if family == "inverse":
                    values = (191, 255 - (x * 255) // 8, 255 - (y * 255) // 6,
                              255 - ((x + y) * 255) // 14)
                struct.pack_into("<4B", raw, y * cfg["rb"] + x * 4, *values)
            elif depth == 16:
                values = (32768 if family == "natural" else 24575,
                          (x * 32768) // 8, (y * 32768) // 6, ((x + y) * 32768) // 14)
                if family == "inverse":
                    values = (24575, 32768 - (x * 32768) // 8, 32768 - (y * 32768) // 6,
                              32768 - ((x + y) * 32768) // 14)
                struct.pack_into("<4H", raw, y * cfg["rb"] + x * 8, *values)
            else:
                if family == "natural":
                    values = (1.0, x / 8.0, y / 6.0, (x + y) / 14.0)
                elif family == "inverse":
                    values = (0.75, 1.0 - x / 8.0, 1.0 - y / 6.0, 1.0 - (x + y) / 14.0)
                elif family == "all_depth":
                    values = (0.75, x / 8.0, y / 6.0, (x + y) / 14.0)
                else:
                    raise ValueError(family)
                struct.pack_into("<4f", raw, y * cfg["rb"] + x * 16, *values)
        active = W * cfg["pixel"]
        raw[y * cfg["rb"] + active:(y + 1) * cfg["rb"]] = bytes([0xA0 + y]) * (cfg["rb"] - active)
    return bytes(raw)


def seed(depth: int) -> bytes:
    cfg = CONFIG[depth]
    raw = bytearray(cfg["rb"] * H)
    for y in range(H):
        active = W * cfg["pixel"]
        raw[y * cfg["rb"] + active:(y + 1) * cfg["rb"]] = bytes([0xE0 + y]) * (cfg["rb"] - active)
    return bytes(raw)


def prepare_module(depth: int):
    cfg = CONFIG[depth]
    if depth == 8:
        pf8.W, pf8.H, pf8.ROWBYTES, pf8.VISIBLE = W, H, 44, 36
        pf8.BITDEPTH, pf8.PIXEL_CPP, pf8.PIXEL_BYTES = 8, "PF_Pixel8", 4
        pf8.OWNER, pf8.ZOOM_RETURN = CONFIG[8]["owner"], CONFIG[8]["returned"]
        pf8.configure()
        def build_pf8_world(loader, payload):
            data = loader.bump_alloc(len(payload), align=64)
            loader.write_bytes(data, payload)
            world = loader.host_alloc(0x80)
            loader.write_bytes(world, b"\0" * 0x80)
            loader.write_bytes(world + 0x18, struct.pack("<Q", data))
            loader.write_bytes(world + 0x20, struct.pack("<I", 44))
            loader.write_bytes(world + 0x24, struct.pack("<I", W))
            loader.write_bytes(world + 0x28, struct.pack("<I", H))
            loader.write_bytes(world + 0x2C, struct.pack("<H", 8))
            return world, data
        pf16.fixture.build_world = build_pf8_world
        fixture = pf16.fixture
    elif depth == 16:
        fixture = pf16.fixture
        fixture.build_world = ORIG_ROT_BUILD_WORLD
        fixture.source_frame = ORIG_ROT_SOURCE_FRAME
        fixture.OWNER = cfg["owner"]
        fixture.W, fixture.H = W, H
        fixture.ROWBYTES, fixture.VISIBLE = cfg["rb"], W * cfg["pixel"]
    else:
        pf32.fixture.W, pf32.fixture.H = W, H
        pf32.fixture.ROWBYTES, pf32.fixture.VISIBLE = 160, 144
        pf32.fixture.BITDEPTH = 32
        fixture = pf32.fixture
    return fixture


def actual(depth: int, source_bytes: bytes, layer_bytes: bytes) -> dict[str, bytes]:
    cfg = CONFIG[depth]
    fixture = prepare_module(depth)
    base = fixture.zoom.fixture if depth == 32 else fixture
    m4 = base.m4
    params = m4.load_case0010_params()
    params.update({"Blur Type": 1, "Center": ((4.5, 3.5) if depth == 8 else (4.0, 3.0)), "Quality": 5.0,
                   "Ratio": 1.0, "Angle": 0, "Outer Strength": 4,
                   "Outer Offset Mode": 1, "Outer Offset": 0,
                   "Inner Strength": 0, "Noise Variation": 0.0,
                   "Noise Type": 1, "Brightness Gain": 1.0, "Size Variation": 0.0})
    loader = base.AexLoader(str(m4.AEX_PATH), fast=True)
    loader.register_libm_impls(max_threads=1)
    sp = m4.build_host_suites(loader)
    render_ctx = m4.build_render_context(loader, sp)
    iw, _ = fixture.build_world(loader, source_bytes)
    ow, output_data = fixture.build_world(loader, seed(depth))
    nw, _ = fixture.build_world(loader, layer_bytes)
    param = m4.build_param_block(loader)
    m4.install_reader_detours(loader, params)
    captured: dict[str, object] = {"nw_before": loader.read_bytes(nw + 0x18, 0x58)}

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
        noise = struct.unpack("<Q", cur.read_bytes(owner + 0xA8, 8))[0]
        captured["noise_meta"] = cur.read_bytes(noise + 0x18, 0x58)
        ptr = struct.unpack("<Q", cur.read_bytes(owner + 0x90, 8))[0]
        captured["source_span"] = cur.read_bytes(ptr, W * H * 4)

    def zoom_entry(cur, _address, _size):
        captured["work"] = cur.uc.reg_read(UC_X86_REG_RCX)

    def collapse(cur, _address, _size):
        if "pre_blur" in captured:
            return
        work = int(captured["work"])
        lo = struct.unpack("<i", cur.read_bytes(work + 0x18, 4))[0]
        hi = struct.unpack("<i", cur.read_bytes(work + 0x1C, 4))[0]
        step = struct.unpack("<f", cur.read_bytes(work + 0x14, 4))[0]
        cells = (hi - lo + 1) * round(6.283185307179586 / step)
        captured["cells"] = cells
        ptr = struct.unpack("<Q", cur.read_bytes(work + 0x38, 8))[0]
        captured["pre_blur"] = cur.read_bytes(ptr, cells * 16)

    def returned(cur, _address, _size):
        work = int(captured["work"])
        ptr = struct.unpack("<Q", cur.read_bytes(work + 0x38, 8))[0]
        captured["post_blur"] = cur.read_bytes(ptr, int(captured["cells"]) * 16)
        captured["returned_ok"] = True

    for address, hook in ((cfg["setup"], setup), (cfg["composed"], composed),
                          (0x1800056F0, zoom_entry), (0x180005C9F, collapse),
                          (cfg["returned"], returned)):
        loader.add_code_hook(address, hook)
    loader.call_function(m4.FUN_180008690, int_args=[0, 0, 0, param, render_ctx], max_instructions=5_000_000)
    try:
        loader.call_function(cfg["owner"], int_args=[render_ctx, 0, iw, ow, param], max_instructions=500_000_000)
    except RuntimeError:
        # The direct owner attempts the optional host layer checkin after the
        # numerical writer.  The minimal AEX loader does not provide it; accept
        # that boundary only after the typed Zoom-return witness fired.
        if not captured.get("returned_ok"):
            raise
    captured["output"] = loader.read_bytes(output_data, cfg["rb"] * H)
    if not captured.get("returned_ok"):
        raise RuntimeError("typed owner did not return through zoom")
    return {key: value for key, value in captured.items() if isinstance(value, bytes)}


def candidate(depth: int, expected: dict[str, bytes], source_bytes: bytes, layer_bytes: bytes) -> dict[str, bytes]:
    cfg = CONFIG[depth]
    source_text = "#include <cstdio>\n" + SOURCE.read_text()
    with tempfile.TemporaryDirectory(prefix=f"radial-type3-{depth}-") as raw:
        td = Path(raw)
        altered = td / "candidate.cpp"
        altered.write_text(source_text)
        (td / "in.bin").write_bytes(source_bytes)
        (td / "layer.bin").write_bytes(layer_bytes)
        extra_payloads: list[bytes] = []
        if depth == 8:
            extra_payloads = []
            for payload in (source(8, "constant"), source(8, "impulse")):
                mutated = bytearray(payload)
                mutated[0] ^= 1
                extra_payloads.append(bytes(mutated))
            extra_code = (
                'std::ifstream(argv[9],std::ios::binary).read((char*)ib.data(),ib.size());'
                'if(!reject_classic(25)||!reject_smart(25))return 43;'
                'std::ifstream(argv[10],std::ios::binary).read((char*)ib.data(),ib.size());'
                'if(!reject_classic(25)||!reject_smart(25))return 44;'
            )
            explicit_unlisted = 2
        elif depth == 32:
            mutated = bytearray(source(32, "zero"))
            mutated[0] ^= 1
            extra_payloads = [bytes(mutated), layer(32, "all_depth")]
            extra_code = (
                'std::ifstream(argv[9],std::ios::binary).read((char*)ib.data(),ib.size());'
                'std::ifstream(argv[10],std::ios::binary).read((char*)nb.data(),nb.size());'
                'if(!reject_classic(25)||!reject_smart(25))return 43;'
            )
            explicit_unlisted = 1
        else:
            extra_code = ""
            explicit_unlisted = 0
        extra_paths = []
        for index, payload in enumerate(extra_payloads):
            path = td / f"negative_{index}.bin"
            path.write_bytes(payload)
            extra_paths.append(path)
        marker_argument = 9 + len(extra_paths)
        cells = 125000
        cpp = td / "probe.cpp"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{altered}"
#include <fstream>
#include <cstdio>
#include <vector>
static void put(const char*p,const void*d,size_t n){{std::ofstream(p,std::ios::binary).write((const char*)d,n);}}
static PF_Err get_format(const PF_EffectWorld*,PF_PixelFormat*f){{*f={cfg['format']};return PF_Err_NONE;}}
static PF_WorldSuite2 world_suite{{nullptr,nullptr,get_format}};
static SPErr acquire(const char*,int32,const void**s){{*s=&world_suite;return kSPNoError;}}
static SPErr release(const char*,int32){{return kSPNoError;}}
static SPBasicSuite basic{{acquire,release}};
static void fill_param(A_long n,PF_ParamDef&p,PF_EffectWorld*iw=nullptr,PF_EffectWorld*nw=nullptr){{AEFX_CLR_STRUCT(p);if(n==OLMRADIALBLUR_INPUT&&iw)p.u.ld=*iw;if(n==OLMRADIALBLUR_NOISE_LAYER&&nw){{p.u.ld=*nw;p.u.ld.dephault=2;}}
 if(n==OLMRADIALBLUR_BLUR_TYPE)p.u.pd.value=1;if(n==OLMRADIALBLUR_CENTER){{p.u.td.x_value=(A_long)({'4.5' if depth == 8 else '4'}*65536);p.u.td.y_value=(A_long)({'3.5' if depth == 8 else '3'}*65536);}}if(n==OLMRADIALBLUR_OUTER_STRENGTH)p.u.sd.value=4;if(n==OLMRADIALBLUR_OUTER_OFFSET_MODE)p.u.pd.value=1;if(n==OLMRADIALBLUR_INNER_OFFSET_MODE)p.u.pd.value=1;if(n==OLMRADIALBLUR_REPEAT_BORDER)p.u.bd.value=TRUE;if(n==OLMRADIALBLUR_RATIO)p.u.fs_d.value=1;if(n==OLMRADIALBLUR_QUALITY)p.u.fs_d.value=5;if(n==OLMRADIALBLUR_BRIGHTNESS_GAIN)p.u.fs_d.value=1;if(n==OLMRADIALBLUR_NOISE_VARIATION)p.u.fs_d.value=25;if(n==OLMRADIALBLUR_NOISE_TYPE)p.u.pd.value=3;if(n==OLMRADIALBLUR_SEED)p.u.sd.value=1;if(n==OLMRADIALBLUR_THICKNESS)p.u.fs_d.value=3;}}
static PF_Err classic(PF_EffectWorld&iw,PF_EffectWorld&nw,PF_EffectWorld&ow,double variation=25){{PF_ParamDef p[OLMRADIALBLUR_NUM_PARAMS]{{}};PF_ParamDef*pp[OLMRADIALBLUR_NUM_PARAMS]{{}};for(int n=0;n<OLMRADIALBLUR_NUM_PARAMS;n++){{pp[n]=&p[n];fill_param(n,p[n],&iw,&nw);}}p[OLMRADIALBLUR_NOISE_VARIATION].u.fs_d.value=variation;PF_InData in{{}};in.pica_basicP=&basic;PF_OutData out{{}};return EffectMain(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);}}
struct Host{{PF_EffectWorld*iw,*nw,*ow;double variation=25;int pre_input=0,pre_noise=0,pixel_input=0,pixel_noise=0,output=0,layer_checkin=0,param_checkout=0,param_checkin=0;}};
static PF_Err checkout_param(PF_ProgPtr q,A_long n,A_long,A_long,A_u_long,PF_ParamDef*p){{auto*h=(Host*)q;++h->param_checkout;fill_param(n,*p,h->iw,h->nw);if(n==OLMRADIALBLUR_NOISE_VARIATION)p->u.fs_d.value=h->variation;return PF_Err_NONE;}}
static PF_Err checkin_param(PF_ProgPtr q,PF_ParamDef*){{++((Host*)q)->param_checkin;return PF_Err_NONE;}}
static PF_Err pre_layer(PF_ProgPtr q,PF_ParamIndex n,A_long,const PF_RenderRequest*,A_long,A_long,A_u_long,PF_CheckoutResult*r){{auto*h=(Host*)q;if(n==OLMRADIALBLUR_INPUT)++h->pre_input;else if(n==OLMRADIALBLUR_NOISE_LAYER)++h->pre_noise;else return PF_Err_BAD_CALLBACK_PARAM;AEFX_CLR_STRUCT(*r);r->result_rect={{0,0,9,7}};r->max_result_rect=r->result_rect;r->ref_width=9;r->ref_height=7;return PF_Err_NONE;}}
static PF_Err pixel_layer(PF_ProgPtr q,A_long n,PF_EffectWorld**w){{auto*h=(Host*)q;if(n==OLMRADIALBLUR_INPUT){{++h->pixel_input;*w=h->iw;}}else if(n==OLMRADIALBLUR_NOISE_LAYER){{++h->pixel_noise;*w=h->nw;}}else return PF_Err_BAD_CALLBACK_PARAM;return PF_Err_NONE;}}
static PF_Err pixel_checkin(PF_ProgPtr q,A_long){{++((Host*)q)->layer_checkin;return PF_Err_NONE;}}
static PF_Err checkout_output(PF_ProgPtr q,PF_EffectWorld**w){{auto*h=(Host*)q;++h->output;*w=h->ow;return PF_Err_NONE;}}
static PF_Err smart(PF_EffectWorld&iw,PF_EffectWorld&nw,PF_EffectWorld&ow,double variation=25){{Host h{{&iw,&nw,&ow,variation}};PF_InData in{{}};in.effect_ref=(PF_ProgPtr)&h;in.current_time=0;in.time_step=1;in.time_scale=1;in.pica_basicP=&basic;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;PF_OutData out{{}};PF_PreRenderInput pri{{}};PF_PreRenderOutput pro{{}};PF_PreRenderCallbacks prc{{pre_layer,nullptr}};PF_PreRenderExtra pre{{&pri,&pro,&prc}};PF_Err err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre);if(err)return err;PF_SmartRenderInput sri{{}};sri.bitdepth={depth};sri.pre_render_data=pro.pre_render_data;PF_SmartRenderCallbacks src{{pixel_layer,pixel_checkin,checkout_output}};PF_SmartRenderExtra x{{&sri,&src}};err=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&x);if(pro.delete_pre_render_data_func)pro.delete_pre_render_data_func(pro.pre_render_data);if(err)return err;return h.pre_input==1&&h.pre_noise==1&&h.pixel_input==1&&h.pixel_noise==1&&h.output==1&&h.layer_checkin==2&&h.param_checkout==32&&h.param_checkin==32?PF_Err_NONE:PF_Err_BAD_CALLBACK_PARAM;}}
int main(int argc,char**argv){{constexpr int W=9,H=7,RB={cfg['rb']},C={cells};
std::vector<unsigned char>ib(RB*H),nb(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());std::ifstream(argv[2],std::ios::binary).read((char*)nb.data(),nb.size());
for(int y=0;y<H;y++)for(int x=W*{cfg['pixel']};x<RB;x++)ob[y*RB+x]=0xE0+y;
PF_EffectWorld iw{{}},nw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;nw.data=(PF_PixelPtr)nb.data();nw.rowbytes=RB;nw.width=W;nw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;
iw.extent_hint={{0,0,W,H}};nw.extent_hint={{0,0,W,H}};ow.extent_hint={{0,0,W,H}};
std::vector<float>span(W*H+1,1),pre(C*4),post(C*4);span.back()=0;RadialBlurTestPolarCapture cap{{}};cap.pre_blur_rgba=pre.data();cap.post_blur_rgba=post.data();cap.capacity_floats=C*4;
OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x={'4.5' if depth == 8 else '4'};i.center_y={'3.5' if depth == 8 else '3'};i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation=25;i.noise_type=3;i.seed=1;i.thickness=3;i.comp_width=W;i.comp_height=H;
if(ComposeType3LayerSpanAEX<{cfg['cpp']}>(&iw,&nw,0.25f,span.data(),span.data(),W*H))return 2;
auto e=RenderZoomTyped<{cfg['cpp']}>(&iw,&ow,i,&cap,&nw);if(e){{std::fprintf(stderr,"err=%d\\n",(int)e);return 10+e;}}
put(argv[3],span.data(),W*H*4);put(argv[4],pre.data(),cap.written_floats*4);put(argv[5],post.data(),cap.written_floats*4);put(argv[6],ob.data(),ob.size());auto direct=ob;
ob.assign(RB*H,0);for(int y=0;y<H;y++)for(int x=W*{cfg['pixel']};x<RB;x++)ob[y*RB+x]=0xE0+y;if(classic(iw,nw,ow)||ob!=direct)return 30;put(argv[7],ob.data(),ob.size());
ob.assign(RB*H,0);for(int y=0;y<H;y++)for(int x=W*{cfg['pixel']};x<RB;x++)ob[y*RB+x]=0xE0+y;if(smart(iw,nw,ow)||ob!=direct)return 31;put(argv[8],ob.data(),ob.size());
auto reject_classic=[&](double variation){{ob.assign(RB*H,0x5a);auto before=ob;return classic(iw,nw,ow,variation)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;}};
auto reject_smart=[&](double variation){{ob.assign(RB*H,0x5a);auto before=ob;return smart(iw,nw,ow,variation)==PF_Err_BAD_CALLBACK_PARAM&&ob==before;}};
if(!reject_classic(26)||!reject_smart(26))return 40;
{{ib[0]^=1;if(!reject_classic(25)||!reject_smart(25))return 41;ib[0]^=1;
nb[0]^=1;if(!reject_classic(25)||!reject_smart(25))return 42;nb[0]^=1;}}
{extra_code}
std::ofstream(argv[{marker_argument}])<<"nv_one_away,source_first_bit,layer_first_bit,explicit_unlisted="<<{explicit_unlisted};}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        exe = td / "probe"
        cmd = [_UCRT_CXX, "-std=c++17", "-arch", "arm64", "-O2", "-ffp-contract=off", "-isysroot", sdk,
               "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")), "-I", str(resolve_asset(ROOT / "Util")),
               "-I", str(resolve_asset(ROOT / "Resources")), "-I", str(ROOT / "mac/OLMRadialBlur"),
               str(cpp), str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),
               str(resolve_asset(ROOT / str(resolve_asset("Util/AEGP_SuiteHandler.cpp")))), str(resolve_asset(ROOT / str(resolve_asset("Util/MissingSuiteError.cpp")))),
               "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stderr)
        names = [td / name for name in ("span.bin", "pre.bin", "post.bin", "out.bin", "classic.bin", "smart.bin")]
        marker = td / "rejects.txt"
        ran = subprocess.run([str(exe), str(td / "in.bin"), str(td / "layer.bin"),
                              *map(str, names), *map(str, extra_paths), str(marker)])
        if ran.returncode:
            raise RuntimeError(f"candidate depth {depth} exit {ran.returncode}")
        result = dict(zip(("source_span", "pre_blur", "post_blur", "output", "classic_output", "smart_output"),
                          (p.read_bytes() for p in names)))
        result["reject_controls"] = marker.read_text()
        return result


def canonical_rows_sha256(rows: list[dict]) -> str:
    return sha(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())


def run_closure() -> dict:
    rows = []
    matrix = (
        [(8, kind, family) for kind in ("canonical", "zero", "constant", "impulse", "checker")
         for family in ("natural", "all_depth", "inverse")] +
        [(16, kind, family) for kind in ("canonical", "zero", "constant", "impulse", "checker")
         for family in ("natural", "all_depth", "inverse")] +
        [(32, kind, family) for kind in ("canonical", "zero", "constant", "impulse", "checker")
         for family in ("natural", "inverse")] +
        [(32, kind, "all_depth") for kind in ("canonical", "zero", "constant", "impulse", "checker")]
    )
    for depth, source_kind, layer_family in matrix:
        source_bytes = source(depth, source_kind)
        layer_bytes = layer(depth, layer_family)
        observed = actual(depth, source_bytes, layer_bytes)
        produced = candidate(depth, observed, source_bytes, layer_bytes)
        matches = {key: produced[key] == observed[key] for key in ("source_span", "pre_blur", "post_blur", "output")}
        matches["classic_output"] = produced["classic_output"] == observed["output"]
        matches["smart_output"] = produced["smart_output"] == observed["output"]
        actual_hashes = {key: sha(observed[key]) for key in ("source_span", "pre_blur", "post_blur", "output")}
        cfg = CONFIG[depth]
        active = W * cfg["pixel"]
        active_source = b"".join(source_bytes[y * cfg["rb"]:y * cfg["rb"] + active] for y in range(H))
        active_layer = b"".join(layer_bytes[y * cfg["rb"]:y * cfg["rb"] + active] for y in range(H))
        rows.append({"depth": depth, "source_kind": source_kind, "layer_family": layer_family,
                     "matches": matches, "source_sha256": sha(source_bytes),
                     "layer_sha256": sha(layer_bytes),
                     "active_source_sha256": sha(active_source),
                     "active_layer_sha256": sha(active_layer),
                     "actual": actual_hashes,
                     "noise_meta": ({"rowbytes": struct.unpack_from("<i", observed["noise_meta"], 8)[0],
                                      "width": struct.unpack_from("<i", observed["noise_meta"], 12)[0],
                                      "height": struct.unpack_from("<i", observed["noise_meta"], 16)[0],
                                      "extent": struct.unpack_from("<4i", observed["noise_meta"], 20)}
                                     if "noise_meta" in observed else None),
                     "candidate": {key: sha(produced[key]) for key in
                                   ("source_span", "pre_blur", "post_blur", "output", "classic_output", "smart_output")},
                     "reject_controls": produced["reject_controls"],
                     "source_span_census": f32_census(observed["source_span"], produced["source_span"]),
                     "pre_blur_census": f32_census(observed["pre_blur"], produced["pre_blur"]),
                     "output_different_bytes": sum(a != b for a, b in zip(observed["output"], produced["output"]))})
    return {
        "schema": "olmradialblur_type3_all_depth_public_closure_v2",
        "status": "pass" if all(all(row["matches"].values()) for row in rows) else "fail",
        "claim_boundary": {
            "positive": "exact 9x7 Zoom Type3/NV25 source+Layer pairs: PF8 15, PF16 15 and PF32 15; active internal planes and padded typed output are raw exact",
            "actual_owner": "pinned Windows AEX typed direct owners executed under the repository AexLoader/Unicorn environment",
            "production_owner": "current source-included direct typed owner plus public Classic EffectMain and SmartPreRender-to-SmartRender entries; every depth is exact source+Layer pair bounded",
            "excluded": ["native Windows AE", "macOS AE", "installed binary", "arbitrary Type3 source/layer/tuple", "optional host pixel-checkin equivalence"],
        },
        "identities": {
            "production_source": str(SOURCE.relative_to(ROOT)),
            "production_source_sha256": sha(SOURCE.read_bytes()),
            "aex": str(asset_relative(pf32.fixture.zoom.fixture.m4.AEX_PATH, ROOT)),
            "aex_sha256": sha(pf32.fixture.zoom.fixture.m4.AEX_PATH.read_bytes()),
        },
        "rows": rows,
        "rows_sha256": canonical_rows_sha256(rows),
    }


def validate_report(report: dict) -> None:
    if set(report) != {"schema", "status", "claim_boundary", "identities", "rows", "rows_sha256"}:
        raise AssertionError("unexpected top-level schema")
    if report["schema"] != "olmradialblur_type3_all_depth_public_closure_v2" or report["status"] != "pass":
        raise AssertionError("closure is not passing")
    identities = report["identities"]
    if SOURCE_SHA256 != "PENDING" and (identities["production_source_sha256"] != SOURCE_SHA256 or sha(SOURCE.read_bytes()) != SOURCE_SHA256):
        raise AssertionError("production source identity drift")
    if identities["aex_sha256"] != AEX_SHA256:
        raise AssertionError("stored AEX identity drift")
    aex_path = ROOT / identities["aex"]
    if sha(aex_path.read_bytes()) != AEX_SHA256:
        raise AssertionError("live AEX identity drift")
    rows = report["rows"]
    if [row["depth"] for row in rows] != [8] * 15 + [16] * 15 + [32] * 15:
        raise AssertionError("depth row set drift")
    if report["rows_sha256"] != canonical_rows_sha256(rows):
        raise AssertionError("stored row digest mismatch")
    if EXPECTED_ROWS_SHA256 != "PENDING" and report["rows_sha256"] != EXPECTED_ROWS_SHA256:
        raise AssertionError("canonical row digest mismatch")
    for row in rows:
        if set(row["matches"]) != {"source_span", "pre_blur", "post_blur", "output", "classic_output", "smart_output"} or not all(row["matches"].values()):
            raise AssertionError(f"non-exact row: {row['depth']}")
        for key in ("source_span", "pre_blur", "post_blur", "output"):
            if row["actual"][key] != row["candidate"][key]:
                raise AssertionError(f"paired plane mismatch: {row['depth']} {key}")
        if row["candidate"]["classic_output"] != row["actual"]["output"] or row["candidate"]["smart_output"] != row["actual"]["output"] or row["output_different_bytes"] != 0:
            raise AssertionError(f"paired plane mismatch: {row['depth']}")


def write_doc(report: dict) -> None:
    lines = ["# OLMRadialBlur Type3 all-depth bounded public closure", "",
             f"Status: `{report['status']}`", "",
             "Exact 9x7 Zoom Type3/NV25 source+Layer pairs are raw exact: PF8 15, PF16 15 and PF32 15.",
             "The Windows side is a pinned AEX typed direct owner under repository AexLoader/Unicorn; no native AE or installed-runtime claim is made.",
             "Classic EffectMain and SmartPreRender-to-SmartRender both reproduce the same padded typed output at all three depths.",
             "Every depth is exact source+Layer-pair bounded. Other Type3 states remain fail-closed.", "",
             f"Production source: `{report['identities']['production_source_sha256']}`", f"Rows: `{report['rows_sha256']}`", ""]
    DOC.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    if args.write or args.fresh:
        report = run_closure()
        validate_report(report)
        if args.write:
            REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            write_doc(report)
        print(f"PASS_OLMRADIALBLUR_TYPE3_ALL_DEPTH rows_sha256={report['rows_sha256']}")
        return 0
    report = json.loads(REPORT.read_text())
    validate_report(report)
    print(f"PASS_OLMRADIALBLUR_TYPE3_ALL_DEPTH_VALIDATE rows_sha256={report['rows_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
