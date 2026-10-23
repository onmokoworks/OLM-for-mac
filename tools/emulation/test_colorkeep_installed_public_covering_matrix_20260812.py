#!/usr/bin/env python3
"""Bind the installed ColorKeep public owner to six exported-AEXCompat cells."""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from olm_installed_identity import verified_binary  # noqa: E402
REPORT = ROOT / "refs/conformance/colorkeep_installed_public_covering_matrix_20260812.json"
WIDTH, HEIGHT, PADDING = 11, 7, 12
AEX = resolve_asset(ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex")
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")
WORKER_SHA256 = "16c329a481aef88c00fd6016e79996eecaabf7a588cff084e866b6bd15d411fc"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def palette8() -> tuple[tuple[int, int, int, int], ...]:
    """ARGB8 public color parameters, in slot order."""
    values = [
        (128, (i * 29 + 11) % 251, (i * 47 + 17) % 251, (i * 71 + 23) % 251)
        for i in range(100)
    ]
    values[3] = (0, 51, 102, 153)       # retained zero-alpha hidden RGB
    values[4] = (64, 191, 0, 128)       # count=5 last enabled
    values[5] = (191, 32, 223, 96)      # count=5 first disabled
    values[98] = (159, 223, 64, 32)
    values[99] = (64, 159, 0, 96)       # count=100 last enabled
    assert len(set(values)) == 100
    return tuple(values)


PALETTE8 = palette8()
PALETTE = tuple(tuple(f32(v / 255.0) for v in color) for color in PALETTE8)


def promote(color: tuple[int, int, int, int], depth: str):
    if depth == "PF8":
        return color
    if depth == "PF16":
        return tuple((v * 32768 + 127) // 255 for v in color)
    return tuple(f32(v / 255.0) for v in color)


def cases(depth: str, count: int):
    if depth != "PF32":
        keys = tuple(promote(c, depth) for c in PALETTE8)
        last = keys[count - 1]
        rejected = list(last); rejected[1] += 1
        semitransparent_miss = list(keys[1]); semitransparent_miss[3] ^= 3
        rows = [
            ("retained_semitransparent", keys[0], True),
            ("rejected_semitransparent", tuple(semitransparent_miss), False),
            ("retained_alpha0_hidden_rgb", keys[3], True),
            ("last_enabled", last, True),
            ("last_enabled_near_miss", tuple(rejected), False),
        ]
        rows.append(("first_disabled", keys[5], False) if count == 5 else
                    ("penultimate_enabled", keys[98], True))
        return rows
    last = PALETTE[count - 1]
    rejected = (last[0], f32(last[1] + 0.0001001), last[2], last[3])
    semi_miss = (PALETTE[1][0], PALETTE[1][1], PALETTE[1][2], f32(PALETTE[1][3] + 0.001))
    rows = [
        ("retained_semitransparent", PALETTE[0], True),
        ("rejected_semitransparent", semi_miss, False),
        ("retained_alpha0_hidden_rgb", PALETTE[3], True),
        ("last_enabled", last, True),
        ("last_enabled_near_miss", rejected, False),
    ]
    rows.append(("first_disabled", PALETTE[5], False) if count == 5 else
                ("penultimate_enabled", PALETTE[98], True))
    return rows


def input_frame(fmt: str, rows) -> bytes:
    size = struct.calcsize(fmt)
    blob = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            blob += struct.pack(fmt, *rows[(y * WIDTH + x) % len(rows)][1])
        blob += b"\xCC" * PADDING
    assert len(blob) == HEIGHT * (WIDTH * size + PADDING)
    return bytes(blob)


def source_rgba8(rows) -> tuple[tuple[int, int, int, int], ...]:
    pixels = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            alpha, red, green, blue = rows[(y * WIDTH + x) % len(rows)][1]
            pixels.append((red, green, blue, alpha))
    return tuple(pixels)


def aex_owner(depth: str, rows, count: int, directory: Path) -> dict:
    input_png = directory / f"input_{count}.png"
    if not input_png.exists():
        image = Image.new("RGBA", (WIDTH, HEIGHT))
        image.putdata(source_rgba8(cases("PF8", count)))
        image.save(input_png)
    output_png = directory / f"output_{depth}_{count}.png"
    pixel_format = {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}[depth]
    params = [f"Enabled Color Num={count}"]
    params += [f"Color@{i + 2}={a},{r},{g},{b}" for i, (a, r, g, b) in enumerate(PALETTE8)]
    result = subprocess.run([str(WORKER), "render-png", str(AEX), str(input_png),
                             str(output_png), "--pixel-format", pixel_format, *params],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["render_error"] == 0
    assert payload["raw_pixel_bytes"] == WIDTH * HEIGHT * struct.calcsize(
        {"PF8": "<4B", "PF16": "<4H", "PF32": "<4f"}[depth])
    assert payload["gpu"]["pre_render"]["completed"]
    assert payload["gpu"]["render"]["completed"]
    assert not payload["unsupported_suite_calls"]
    assert payload["dropped_unsupported_suite_calls"] == 0
    return payload


def byte_array(name: str, data: bytes) -> str:
    return f"static const unsigned char {name}[]={{{','.join(map(str, data))}}};"


def execute_installed(binary: Path, inputs: dict[tuple[str, int], bytes],
                      include_classic: bool = False,
                      arch: str = "arm64") -> bytes:
    if arch not in {"arm64", "x86_64"}:
        raise ValueError(f"unsupported architecture: {arch}")
    colors = b"".join(struct.pack("<4f", *c) for c in PALETTE)
    arrays = [byte_array("colors", colors)]
    for count in (5, 100):
        for depth in ("PF8", "PF16", "PF32"):
            arrays.append(byte_array(f"in_{depth}_{count}", inputs[(depth, count)]))
    code = r'''
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"
using Effect=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
static PF_Iterate8Suite2 s8{}; static PF_iterate16Suite2 s16{}; static PF_iterateFloatSuite2 sf{}; static PF_ColorParamSuite1 sc{}; static PF_WorldSuite2 sw{};
static PF_EffectWorld *gin,*gout; static int gdepth,gcount,checks,param_checkins,layer_hits,output_hits,checkin_hits,pre_hits; static int order[101];
''' + "\n".join(arrays) + r'''
template<class P,class F> static PF_Err iter(PF_InData*,A_long,A_long,PF_EffectWorld*src,const PF_Rect*,void*ref,F fn,PF_EffectWorld*dst){
  for(int y=0;y<dst->height;y++)for(int x=0;x<dst->width;x++){auto*a=(P*)((char*)src->data+y*src->rowbytes+x*sizeof(P));auto*b=(P*)((char*)dst->data+y*dst->rowbytes+x*sizeof(P));PF_Err e=fn(ref,x,y,a,b);if(e)return e;}return 0;}
static PF_Err i8(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel8Func g,PF_EffectWorld*h){return iter<PF_Pixel8>(a,b,c,d,e,f,g,h);}
static PF_Err i16(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel16Func g,PF_EffectWorld*h){return iter<PF_Pixel16>(a,b,c,d,e,f,g,h);}
static PF_Err iff(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixelFloatFunc g,PF_EffectWorld*h){return iter<PF_PixelFloat>(a,b,c,d,e,f,g,h);}
static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){int n=p->u.cd.value.red;if(n<0||n>=100)return 91;std::memcpy(out,colors+n*16,16);return 0;}
static PF_Err worldfmt(const PF_EffectWorld*w,PF_PixelFormat*f){if(w!=gin&&w!=gout)return 95;*f=gdepth==8?PF_PixelFormat_ARGB32:gdepth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;return 0;}
static SPErr acquire(const char*n,int32 v,const void**p){
 if(!std::strcmp(n,kPFIterate8Suite)&&v==kPFIterate8SuiteVersion2){*p=&s8;return 0;}if(!std::strcmp(n,kPFIterate16Suite)&&v==kPFIterate16SuiteVersion2){*p=&s16;return 0;}if(!std::strcmp(n,kPFIterateFloatSuite)&&v==kPFIterateFloatSuiteVersion2){*p=&sf;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){*p=&sc;return 0;}if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){*p=&sw;return 0;}return 92;}
static SPErr release(const char*,int32){return 0;}
static PF_Err checkout(PF_ProgPtr,PF_ParamIndex n,A_long,A_long,A_u_long,PF_ParamDef*p){std::memset(p,0,sizeof(*p));if(checks<101)order[checks]=n;checks++;if(n==1)p->u.sd.value=gcount;else if(n>=2&&n<102)p->u.cd.value.red=n-2;else return 93;return 0;}
static PF_Err check_param(PF_ProgPtr,PF_ParamDef*){param_checkins++;return 0;}
static PF_Err pre(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*r,A_long,A_long,A_u_long,PF_CheckoutResult*o){pre_hits++;if(r->preserve_rgb_of_zero_alpha)return 94;o->result_rect={0,0,11,7};o->max_result_rect=o->result_rect;return 0;}
static PF_Err pixels(PF_ProgPtr,A_long,PF_EffectWorld**w){*w=gin;layer_hits++;return 0;}static PF_Err output(PF_ProgPtr,PF_EffectWorld**w){*w=gout;output_hits++;return 0;}static PF_Err checkin(PF_ProgPtr,A_long){checkin_hits++;return 0;}
template<class P>static bool run(Effect effect,const unsigned char*raw,int depth,int count,bool smart){constexpr int W=11,H=7,PAD=12;const int rb=W*sizeof(P)+PAD;alignas(P) unsigned char src[H*(W*sizeof(P)+PAD)],dst[H*(W*sizeof(P)+PAD)];std::memcpy(src,raw,sizeof(src));unsigned char before[sizeof(src)];std::memcpy(before,src,sizeof(src));std::memset(dst,0xEE,sizeof(dst));PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)src;iw.rowbytes=rb;iw.width=W;iw.height=H;iw.extent_hint={0,0,W,H};ow.data=(PF_PixelPtr)dst;ow.rowbytes=rb;ow.width=W;ow.height=H;ow.extent_hint={0,0,W,H};if(depth!=8){iw.world_flags=PF_WorldFlag_DEEP;ow.world_flags=PF_WorldFlag_DEEP;}PF_EffectWorld iw_before=iw,ow_before=ow;gin=&iw;gout=&ow;gdepth=depth;gcount=count;checks=param_checkins=layer_hits=output_hits=checkin_hits=pre_hits=0;PF_InData in{};PF_OutData out{};SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;in.pica_basicP=&basic;in.effect_ref=(PF_ProgPtr)0x1234;in.inter.checkout_param=checkout;in.inter.checkin_param=check_param;PF_Err err=0;bool ordered=true;if(smart){PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre;PF_PreRenderExtra px{&pi,&po,&pcb};err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&px);PF_SmartRenderInput si{};si.bitdepth=depth;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=pixels;cb.checkout_output=output;cb.checkin_layer_pixels=checkin;PF_SmartRenderExtra sx{&si,&cb};if(!err)err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&sx);ordered=checks==101;for(int n=0;n<101&&ordered;n++)ordered=order[n]==n+1;}else{PF_ParamDef defs[102]{};PF_ParamDef*pp[102];for(int n=0;n<102;n++){pp[n]=&defs[n];if(n>=2)defs[n].u.cd.value.red=n-2;}defs[0].u.ld=iw;defs[1].u.sd.value=count;gin=&defs[0].u.ld;err=effect(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);iw=defs[0].u.ld;}bool pads=true;for(int y=0;y<H;y++)for(int x=W*sizeof(P);x<rb;x++)pads&=src[y*rb+x]==0xCC&&dst[y*rb+x]==0xEE;bool life=smart?(pre_hits==1&&checks==101&&param_checkins==101&&ordered&&layer_hits==1&&output_hits==1&&checkin_hits==1):(checks==0&&param_checkins==0&&layer_hits==0&&output_hits==0&&checkin_hits==0);bool gates=!err&&life&&std::memcmp(src,before,sizeof(src))==0&&std::memcmp(&iw,&iw_before,sizeof(iw))==0&&std::memcmp(&ow,&ow_before,sizeof(ow))==0&&pads;if(!gates)return false;std::fwrite(dst,1,sizeof(dst),stdout);return true;}
int main(int argc,char**argv){s8.iterate=i8;s16.iterate=i16;sf.iterate=iff;sc.PF_GetFloatingPointColorFromColorDef=color;sw.PF_GetPixelFormat=worldfmt;void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h)return 2;auto effect=(Effect)dlsym(h,"EffectMain");if(!effect)return 3;bool ok=true;ok&=run<PF_Pixel8>(effect,in_PF8_5,8,5,true);ok&=run<PF_Pixel16>(effect,in_PF16_5,16,5,true);ok&=run<PF_PixelFloat>(effect,in_PF32_5,32,5,true);ok&=run<PF_Pixel8>(effect,in_PF8_100,8,100,true);ok&=run<PF_Pixel16>(effect,in_PF16_100,16,100,true);ok&=run<PF_PixelFloat>(effect,in_PF32_100,32,100,true);''' + (r'''ok&=run<PF_Pixel8>(effect,in_PF8_5,8,5,false);ok&=run<PF_Pixel16>(effect,in_PF16_5,16,5,false);ok&=run<PF_Pixel8>(effect,in_PF8_100,8,100,false);ok&=run<PF_Pixel16>(effect,in_PF16_100,16,100,false);''' if include_classic else "") + r'''return ok?0:4;}
'''
    compiler = shutil.which("clang++")
    assert compiler, "clang++ unavailable"
    with tempfile.TemporaryDirectory(prefix="colorkeep_installed_matrix_") as raw:
        directory = Path(raw); source = directory / "probe.cpp"; executable = directory / "probe"
        source.write_text(code, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([_UCRT_CXX, "--compiler", compiler, "-std=c++17", "-arch", arch, "-isysroot", sdk,
                                "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources",
                                str(source), "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable), str(binary)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, f"probe rc={run.returncode}: {run.stderr.decode(errors='replace')}"
        return run.stdout


def main() -> int:
    binary, identity = verified_binary("ColorKeep")
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == identity["sha256"]
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    assert hashlib.sha256(WORKER.read_bytes()).hexdigest() == WORKER_SHA256
    inputs, owner_rows, cells = {}, [], []
    with tempfile.TemporaryDirectory(prefix="colorkeep_owner_matrix_") as raw:
        directory = Path(raw)
        for count in (5, 100):
            source_rows8 = cases("PF8", count)
            for depth, fmt in (("PF8", "<4B"), ("PF16", "<4H"), ("PF32", "<4f")):
                rows = [(name, promote(value, depth), matched)
                        for name, value, matched in source_rows8]
                inputs[(depth, count)] = input_frame(fmt, rows)
                owner = aex_owner(depth, rows, count, directory)
                owner_rows.append(owner)
                cells.append({
                    "depth": depth, "enabled_count": count,
                    "windows_path": "exported SmartPreRender->SmartRender",
                    "mac_path": "dlsym EffectMain->SmartPreRender->SmartRender",
                    "cases": [name for name, _, _ in rows],
                    "actual_exported_owner_sha256": owner["raw_pixel_sha256"],
                    "raw_pixel_bytes": owner["raw_pixel_bytes"],
                    "smart_pre_render": owner["gpu"]["pre_render"],
                    "smart_render": owner["gpu"]["render"],
                    "suite_requests": owner["suite_requests"],
                })
    observed = execute_installed(binary, inputs)
    offset = 0
    active_parts = []
    for cell in cells:
        pixel_size = {"PF8": 4, "PF16": 8, "PF32": 16}[cell["depth"]]
        rowbytes = WIDTH * pixel_size + PADDING
        full_size = rowbytes * HEIGHT
        full = observed[offset:offset + full_size]
        offset += full_size
        active = b"".join(full[y * rowbytes:y * rowbytes + WIDTH * pixel_size]
                           for y in range(HEIGHT))
        assert all(full[y * rowbytes + WIDTH * pixel_size:(y + 1) * rowbytes] == b"\xEE" * PADDING
                   for y in range(HEIGHT))
        digest = hashlib.sha256(active).hexdigest()
        assert digest == cell["actual_exported_owner_sha256"]
        cell["installed_active_sha256"] = digest
        cell["status"] = "raw_exact"
        active_parts.append(active)
    assert offset == len(observed)
    worker_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=WORKER.parents[3], text=True).strip()
    report = {
        "schema": "colorkeep.installed-public-owner-covering/2",
        "status": "installed_public_six_cell_raw_exact", "actual_aex_sha256": AEX_SHA256,
        "aexcompat_worker": {"path": str(WORKER), "sha256": WORKER_SHA256,
                              "commit": worker_commit, "modified_by_this_task": False},
        "installed_binary": str(binary), "installed_binary_sha256": identity["sha256"],
        "identity_manifest": "refs/conformance/olm_installed_identity_manifest_20260806.json",
        "fixture": {"width": WIDTH, "height": HEIGHT, "padding_per_row": PADDING,
                    "palette_argb8": [list(color) for color in PALETTE8],
                    "contracts": ["retained/rejected semitransparent", "retained alpha-zero hidden RGB", "last enabled key", "first disabled key at count 5"]},
        "cells": cells, "combined_active_output_sha256": hashlib.sha256(b"".join(active_parts)).hexdigest(),
        "raw_exact": True, "input_complete_buffer_unchanged": True,
        "input_padding_preserved": True, "output_padding_preserved": True,
        "world_headers_unchanged": True,
        "mac_lifecycle_per_cell": {"pre_render": 1, "checkout_layer_pixels": 1,
                                   "checkout_output": 1, "checkin_layer_pixels": 1,
                                   "parameter_checkouts": 101, "parameter_checkins": 101,
                                   "ordered_parameter_slots": [1, 101]},
        "claim_boundary": "Current installed arm64 public EffectMain under focused AE-free callbacks and actual exported Windows Smart owner under pinned AEXCompat, PF8/PF16/PF32, counts 5/100, fixed public palette and 11x7 fixture only.",
        "not_proven": ["native After Effects suite behavior", "other parameter combinations or geometries", "cross-host AE export raw equality"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
