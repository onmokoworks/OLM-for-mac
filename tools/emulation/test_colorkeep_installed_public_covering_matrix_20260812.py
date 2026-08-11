#!/usr/bin/env python3
"""Bind the current installed ColorKeep EffectMain to a six-cell AEX oracle."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from olm_installed_identity import verified_binary  # noqa: E402
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle  # noqa: E402
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import (  # noqa: E402
    DEPTHS as INTEGER_SPECS,
    quantize,
)

REPORT = ROOT / "refs/conformance/colorkeep_installed_public_covering_matrix_20260812.json"
WIDTH, HEIGHT, PADDING = 11, 7, 12


def palette() -> tuple[tuple[float, float, float, float], ...]:
    values = [
        (0.5, ((i * 29 + 11) % 251) / 255.0,
         ((i * 47 + 17) % 251) / 255.0,
         ((i * 71 + 23) % 251) / 255.0)
        for i in range(100)
    ]
    values[3] = (0.0, 0.2, 0.4, 0.6)       # retained zero-alpha hidden RGB
    values[4] = (0.25, 0.75, 0.0, 0.5)     # count=5 last enabled
    values[5] = (0.75, 0.125, 0.875, 0.375) # count=5 first disabled
    values[98] = (0.625, 0.875, 0.25, 0.125)
    values[99] = (0.25, 0.625, 0.0, 0.375)  # count=100 last enabled
    assert len(set(values)) == 100
    return tuple(values)


PALETTE = palette()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def cases(depth: str, count: int):
    if depth != "PF32":
        keys = tuple(quantize(c, INTEGER_SPECS[depth]) for c in PALETTE)
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


def aex_frame(entry: int, fmt: str, rows, count: int) -> bytes:
    old = oracle.WIDTH, oracle.HEIGHT, oracle.PADDING, oracle.COLORS
    try:
        oracle.WIDTH, oracle.HEIGHT, oracle.PADDING = WIDTH, HEIGHT, PADDING
        oracle.COLORS = PALETTE[:count]
        return oracle.actual_frame(entry, fmt, tuple(row[1] for row in rows))
    finally:
        oracle.WIDTH, oracle.HEIGHT, oracle.PADDING, oracle.COLORS = old


def byte_array(name: str, data: bytes) -> str:
    return f"static const unsigned char {name}[]={{{','.join(map(str, data))}}};"


def execute_installed(binary: Path, inputs: dict[tuple[str, int], bytes]) -> bytes:
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
static PF_Iterate8Suite2 s8{}; static PF_iterate16Suite2 s16{}; static PF_iterateFloatSuite2 sf{}; static PF_ColorParamSuite1 sc{};
static PF_EffectWorld *gin,*gout; static int gcount, checks, layer_hits, output_hits, checkin_hits;
''' + "\n".join(arrays) + r'''
template<class P,class F> static PF_Err iter(PF_InData*,A_long,A_long,PF_EffectWorld*src,const PF_Rect*,void*ref,F fn,PF_EffectWorld*dst){
  for(int y=0;y<dst->height;y++)for(int x=0;x<dst->width;x++){auto*a=(P*)((char*)src->data+y*src->rowbytes+x*sizeof(P));auto*b=(P*)((char*)dst->data+y*dst->rowbytes+x*sizeof(P));PF_Err e=fn(ref,x,y,a,b);if(e)return e;}return 0;}
static PF_Err i8(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel8Func g,PF_EffectWorld*h){return iter<PF_Pixel8>(a,b,c,d,e,f,g,h);}
static PF_Err i16(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel16Func g,PF_EffectWorld*h){return iter<PF_Pixel16>(a,b,c,d,e,f,g,h);}
static PF_Err iff(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixelFloatFunc g,PF_EffectWorld*h){return iter<PF_PixelFloat>(a,b,c,d,e,f,g,h);}
static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){int n=p->u.cd.value.red;if(n<0||n>=100)return 91;std::memcpy(out,colors+n*16,16);return 0;}
static SPErr acquire(const char*n,int32 v,const void**p){
 if(!std::strcmp(n,kPFIterate8Suite)&&v==kPFIterate8SuiteVersion2){*p=&s8;return 0;}if(!std::strcmp(n,kPFIterate16Suite)&&v==kPFIterate16SuiteVersion2){*p=&s16;return 0;}if(!std::strcmp(n,kPFIterateFloatSuite)&&v==kPFIterateFloatSuiteVersion2){*p=&sf;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){*p=&sc;return 0;}return 92;}
static SPErr release(const char*,int32){return 0;}
static PF_Err checkout(PF_ProgPtr,PF_ParamIndex n,A_long,A_long,A_u_long,PF_ParamDef*p){std::memset(p,0,sizeof(*p));checks++;if(n==1)p->u.sd.value=gcount;else if(n>=2&&n<102)p->u.cd.value.red=n-2;else return 93;return 0;}
static PF_Err check_param(PF_ProgPtr,PF_ParamDef*){return 0;}
static PF_Err pre(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest*r,A_long,A_long,A_u_long,PF_CheckoutResult*o){if(r->preserve_rgb_of_zero_alpha)return 94;o->result_rect={0,0,11,7};o->max_result_rect=o->result_rect;return 0;}
static PF_Err pixels(PF_ProgPtr,A_long,PF_EffectWorld**w){*w=gin;layer_hits++;return 0;}static PF_Err output(PF_ProgPtr,PF_EffectWorld**w){*w=gout;output_hits++;return 0;}static PF_Err checkin(PF_ProgPtr,A_long){checkin_hits++;return 0;}
template<class P>static bool run(Effect effect,const unsigned char*raw,int depth,int count,bool smart){constexpr int W=11,H=7,PAD=12;const int rb=W*sizeof(P)+PAD;unsigned char src[H*(W*sizeof(P)+PAD)],dst[H*(W*sizeof(P)+PAD)];std::memcpy(src,raw,sizeof(src));std::memset(dst,0xEE,sizeof(dst));PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)src;iw.rowbytes=rb;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)dst;ow.rowbytes=rb;ow.width=W;ow.height=H;if(depth==16){iw.world_flags=PF_WorldFlag_DEEP;ow.world_flags=PF_WorldFlag_DEEP;}gin=&iw;gout=&ow;gcount=count;checks=layer_hits=output_hits=checkin_hits=0;PF_InData in{};PF_OutData out{};SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;in.pica_basicP=&basic;in.effect_ref=(PF_ProgPtr)0x1234;in.inter.checkout_param=checkout;in.inter.checkin_param=check_param;PF_ParamDef defs[102]{};PF_ParamDef*pp[102];for(int n=0;n<102;n++)pp[n]=&defs[n];defs[0].u.ld=iw;defs[1].u.sd.value=count;for(int n=0;n<100;n++)defs[n+2].u.cd.value.red=n;PF_Err err=0;if(!smart){err=effect(PF_Cmd_RENDER,&in,&out,pp,&ow,nullptr);}else{PF_PreRenderInput pi{};PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre;PF_PreRenderExtra px{&pi,&po,&pcb};err=effect(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&px);PF_SmartRenderInput si{};si.bitdepth=depth;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=pixels;cb.checkout_output=output;cb.checkin_layer_pixels=checkin;PF_SmartRenderExtra sx{&si,&cb};if(!err)err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&sx);if(checks!=101||layer_hits!=1||output_hits!=1||checkin_hits!=1)return false;}if(err)return false;std::fwrite(dst,1,sizeof(dst),stdout);return true;}
int main(int argc,char**argv){s8.iterate=i8;s16.iterate=i16;sf.iterate=iff;sc.PF_GetFloatingPointColorFromColorDef=color;void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h)return 2;auto effect=(Effect)dlsym(h,"EffectMain");if(!effect)return 3;bool ok=true;ok&=run<PF_Pixel8>(effect,in_PF8_5,8,5,false);ok&=run<PF_Pixel16>(effect,in_PF16_5,16,5,false);ok&=run<PF_PixelFloat>(effect,in_PF32_5,32,5,true);ok&=run<PF_Pixel8>(effect,in_PF8_100,8,100,false);ok&=run<PF_Pixel16>(effect,in_PF16_100,16,100,false);ok&=run<PF_PixelFloat>(effect,in_PF32_100,32,100,true);return ok?0:4;}
'''
    compiler = shutil.which("clang++")
    assert compiler, "clang++ unavailable"
    with tempfile.TemporaryDirectory(prefix="colorkeep_installed_matrix_") as raw:
        directory = Path(raw); source = directory / "probe.cpp"; executable = directory / "probe"
        source.write_text(code, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([compiler, "-std=c++17", "-arch", "arm64", "-isysroot", sdk,
                                "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources",
                                str(source), "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable), str(binary)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, f"probe rc={run.returncode}: {run.stderr.decode(errors='replace')}"
        return run.stdout


def main() -> int:
    binary, identity = verified_binary("ColorKeep")
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == identity["sha256"]
    entries = {"PF8": (0x180001580, "<4B"), "PF16": (0x180001280, "<4H"), "PF32": (0x180001850, "<4f")}
    inputs, expected, cells = {}, [], []
    for count in (5, 100):
        for depth in ("PF8", "PF16", "PF32"):
            entry, fmt = entries[depth]; rows = cases(depth, count)
            source = input_frame(fmt, rows); oracle_blob = aex_frame(entry, fmt, rows, count)
            inputs[(depth, count)] = source; expected.append(oracle_blob)
            size = struct.calcsize(fmt); rowbytes = WIDTH * size + PADDING
            assert all(oracle_blob[y * rowbytes + WIDTH * size:(y + 1) * rowbytes] == b"\xEE" * PADDING for y in range(HEIGHT))
            cells.append({"depth": depth, "enabled_count": count,
                          "path": "PF_Cmd_RENDER" if depth != "PF32" else "PF_Cmd_SMART_PRE_RENDER->PF_Cmd_SMART_RENDER",
                          "cases": [name for name, _, _ in rows], "oracle_sha256": hashlib.sha256(oracle_blob).hexdigest()})
    expected_blob = b"".join(expected)
    observed = execute_installed(binary, inputs)
    assert observed == expected_blob
    report = {
        "status": "installed_public_six_cell_raw_exact", "actual_aex_sha256": oracle.AEX_SHA256,
        "installed_binary": str(binary), "installed_binary_sha256": identity["sha256"],
        "identity_manifest": "refs/conformance/olm_installed_identity_manifest_20260806.json",
        "fixture": {"width": WIDTH, "height": HEIGHT, "padding_per_row": PADDING,
                    "contracts": ["retained/rejected semitransparent", "retained alpha-zero hidden RGB", "last enabled key", "first disabled key at count 5"]},
        "cells": cells, "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "raw_exact": True, "active_and_padding_exact": True,
        "claim_boundary": "Current installed arm64 public EffectMain under focused AE-free callbacks, PF8/PF16 legacy and PF32 Smart, counts 5/100, fixed 11x7 fixture only.",
        "not_proven": ["native After Effects suite behavior", "other parameter combinations or geometries", "cross-host AE export raw equality"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
