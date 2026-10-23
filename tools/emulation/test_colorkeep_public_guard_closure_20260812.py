#!/usr/bin/env python3
"""Close ColorKeep's fixed public-owner lane and fail-closed world guards."""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
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
import test_colorkeep_installed_public_covering_matrix_20260812 as matrix  # noqa: E402

SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
OWNER_REPORT = ROOT / "refs/conformance/colorkeep_installed_public_covering_matrix_20260812.json"
REPORT = ROOT / "refs/conformance/colorkeep_public_guard_closure_20260812.json"
DOC = REPORT.with_suffix(".md")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_candidate() -> tuple[Path, dict]:
    durable_root = ROOT / "handoffs"
    durable_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="colorkeep_public_guard_candidate_20260812.",
                                      dir=durable_root))
    product = directory / "Product"
    command = [
        "xcodebuild", "-project", "mac/ColorKeep/Mac/ColorKeep.xcodeproj",
        "-target", "ColorKeep", "-configuration", "Release",
        "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO", "CODE_SIGNING_ALLOWED=NO",
        f"CONFIGURATION_BUILD_DIR={product}", f"OBJROOT={directory / 'Obj'}",
        f"SYMROOT={directory / 'Sym'}", "build",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    build_log = directory / "xcodebuild.log"
    build_log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(result.stdout[-4000:] + result.stderr[-4000:])
    bundle = product / "ColorKeep.plugin"
    binary = bundle / "Contents/MacOS/ColorKeep"
    if not binary.is_file():
        raise RuntimeError("candidate binary missing after xcodebuild")
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(bundle)],
                   check=True, capture_output=True, text=True)
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", "--verbose=2",
                             str(bundle)], capture_output=True, text=True)
    if verify.returncode:
        raise RuntimeError(verify.stderr)
    archs = subprocess.check_output(["lipo", "-archs", str(binary)], text=True).split()
    if set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"not Universal: {archs}")
    return binary, {
        "bundle": str(bundle), "binary": str(binary), "binary_sha256": sha(binary),
        "info_plist_sha256": sha(bundle / "Contents/Info.plist"),
        "resource_sha256": sha(bundle / "Contents/Resources/ColorKeep.rsrc"),
        "build_log": str(build_log), "build_log_sha256": sha(build_log),
        "architectures": archs, "codesign_verify": "pass",
        "build_command": command,
    }


def valid_inputs() -> dict[tuple[str, int], bytes]:
    inputs = {}
    for count in (5, 100):
        rows8 = matrix.cases("PF8", count)
        for depth, fmt in (("PF8", "<4B"), ("PF16", "<4H"), ("PF32", "<4f")):
            rows = [(name, matrix.promote(value, depth), matched)
                    for name, value, matched in rows8]
            inputs[(depth, count)] = matrix.input_frame(fmt, rows)
    return inputs


def active_parts(blob: bytes) -> list[bytes]:
    parts, offset = [], 0
    for count in (5, 100):
        for depth in ("PF8", "PF16", "PF32"):
            pixel_size = {"PF8": 4, "PF16": 8, "PF32": 16}[depth]
            rowbytes = matrix.WIDTH * pixel_size + matrix.PADDING
            size = rowbytes * matrix.HEIGHT
            full = blob[offset:offset + size]
            offset += size
            parts.append(b"".join(full[y * rowbytes:y * rowbytes + matrix.WIDTH * pixel_size]
                                  for y in range(matrix.HEIGHT)))
    if offset != len(blob):
        raise RuntimeError("candidate valid output framing drift")
    return parts


def classic_active_parts(blob: bytes) -> list[bytes]:
    smart_size = sum((matrix.WIDTH * pixel_size + matrix.PADDING) * matrix.HEIGHT
                     for _count in (5, 100) for pixel_size in (4, 8, 16))
    offset, parts = smart_size, []
    for _count in (5, 100):
        for pixel_size in (4, 8):
            rowbytes = matrix.WIDTH * pixel_size + matrix.PADDING
            size = rowbytes * matrix.HEIGHT
            full = blob[offset:offset + size]
            offset += size
            parts.append(b"".join(full[y * rowbytes:y * rowbytes + matrix.WIDTH * pixel_size]
                                  for y in range(matrix.HEIGHT)))
    if offset != len(blob):
        raise RuntimeError("candidate classic output framing drift")
    return parts


def guard_probe(binary: Path) -> dict:
    colors = b"".join(struct.pack("<4f", *color) for color in matrix.PALETTE)
    source = matrix.input_frame("<4B", matrix.cases("PF8", 5))
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
static PF_EffectWorld *gin,*gout; static PF_PixelFormat gifmt,gofmt; static int gcount,co,ci,color_calls,worldfmt_calls,lh,oh,li,iter_hits,fail_layer,fail_output,fail_param,fail_checkin,fail_color,fail_worldfmt,fail_suite,palette_bad,phase,phase_bad;
''' + matrix.byte_array("colors", colors) + matrix.byte_array("source8", source) + r'''
template<class P,class F>static PF_Err iter(PF_InData*,A_long,A_long,PF_EffectWorld*a,const PF_Rect*,void*r,F f,PF_EffectWorld*b){iter_hits++;for(int y=0;y<b->height;y++)for(int x=0;x<b->width;x++){P*i=(P*)((char*)a->data+y*a->rowbytes+x*sizeof(P));P*o=(P*)((char*)b->data+y*b->rowbytes+x*sizeof(P));PF_Err e=f(r,x,y,i,o);if(e)return e;}return 0;}
static PF_Err i8(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel8Func g,PF_EffectWorld*h){return iter<PF_Pixel8>(a,b,c,d,e,f,g,h);}static PF_Err i16(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixel16Func g,PF_EffectWorld*h){return iter<PF_Pixel16>(a,b,c,d,e,f,g,h);}static PF_Err iff(PF_InData*a,A_long b,A_long c,PF_EffectWorld*d,const PF_Rect*e,void*f,PF_IteratePixelFloatFunc g,PF_EffectWorld*h){return iter<PF_PixelFloat>(a,b,c,d,e,f,g,h);}
static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){if(phase>1||co!=101)phase_bad=1;phase=1;color_calls++;if(color_calls==fail_color)return 79;int n=p->u.cd.value.red;if(n<0||n>=100)return 90;std::memcpy(out,colors+n*16,16);if(palette_bad&&n==0)out->blue+=0.01f;return 0;}
static PF_Err worldfmt(const PF_EffectWorld*w,PF_PixelFormat*f){worldfmt_calls++;if(worldfmt_calls==fail_worldfmt)return 80;if(w==gin){*f=gifmt;return 0;}if(w==gout){*f=gofmt;return 0;}return 91;}
static SPErr acquire(const char*n,int32 v,const void**p){if(fail_suite==1&&!std::strcmp(n,kPFWorldSuite))return 92;if(fail_suite==2&&!std::strcmp(n,kPFColorParamSuite))return 92;if(fail_suite==3&&(!std::strcmp(n,kPFIterate8Suite)||!std::strcmp(n,kPFIterate16Suite)||!std::strcmp(n,kPFIterateFloatSuite)))return 92;if(!std::strcmp(n,kPFIterate8Suite)&&v==kPFIterate8SuiteVersion2){*p=&s8;return 0;}if(!std::strcmp(n,kPFIterate16Suite)&&v==kPFIterate16SuiteVersion2){*p=&s16;return 0;}if(!std::strcmp(n,kPFIterateFloatSuite)&&v==kPFIterateFloatSuiteVersion2){*p=&sf;return 0;}if(!std::strcmp(n,kPFColorParamSuite)&&v==kPFColorParamSuiteVersion1){*p=&sc;return 0;}if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){*p=&sw;return 0;}return 92;}static SPErr release(const char*,int32){return 0;}
static PF_Err checkout(PF_ProgPtr,PF_ParamIndex n,A_long,A_long,A_u_long,PF_ParamDef*p){if(phase!=0)phase_bad=1;co++;if(n==fail_param)return 77;std::memset(p,0,sizeof(*p));if(n==1)p->u.sd.value=gcount;else if(n>=2&&n<102)p->u.cd.value.red=n-2;else return 93;return 0;}static PF_Err checkparam(PF_ProgPtr,PF_ParamDef*){if(phase>2)phase_bad=1;phase=2;ci++;return ci==fail_checkin?78:0;}
static PF_Err layer(PF_ProgPtr,A_long,PF_EffectWorld**w){lh++;if(fail_layer)return 75;*w=gin;return 0;}static PF_Err output(PF_ProgPtr,PF_EffectWorld**w){oh++;if(fail_output)return 76;*w=gout;return 0;}static PF_Err checkin(PF_ProgPtr,A_long){li++;return 0;}
static bool untouched(const unsigned char*p,size_t n,unsigned char v){for(size_t i=0;i<n;i++)if(p[i]!=v)return false;return true;}
enum{OK=0,BITDEPTH,IN_NULL,OUT_NULL,IN_W,OUT_W,IN_H,OUT_H,IN_RB,OUT_RB,IN_EXT,OUT_EXT,IN_DEEP,OUT_DEEP,IN_WRITEABLE,OUT_WRITEABLE,IN_ORIGIN,OUT_ORIGIN,ALIAS,COUNT4,COUNT99,PALETTE,IN_FMT,OUT_FMT,FAIL_WORLD_FMT,FAIL_LAYER,FAIL_OUTPUT,FAIL_PARAM,FAIL_CHECKIN,FAIL_COLOR,FAIL_SUITE_WORLD,FAIL_SUITE_COLOR,FAIL_SUITE_ITER,NULL_EXTRA,NULL_INPUT,NULL_CB,NULL_LAYER_CB,NULL_OUTPUT_CB,NULL_CHECKIN_CB};
static bool smart(Effect e,int variant){constexpr int W=11,H=7,RB=56,SZ=RB*H;alignas(16)unsigned char ss[SZ+16],dd[SZ+16];std::memcpy(ss,source8,SZ);unsigned char before[SZ];std::memcpy(before,ss,SZ);std::memset(dd,0xEE,sizeof(dd));PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)ss;iw.rowbytes=RB;iw.width=W;iw.height=H;iw.extent_hint={0,0,W,H};ow.data=(PF_PixelPtr)dd;ow.rowbytes=RB;ow.width=W;ow.height=H;ow.extent_hint={0,0,W,H};int depth=8;gcount=5;palette_bad=fail_layer=fail_output=fail_param=fail_checkin=fail_color=fail_worldfmt=fail_suite=0;if(variant==BITDEPTH)depth=7;if(variant==IN_NULL)iw.data=nullptr;if(variant==OUT_NULL)ow.data=nullptr;if(variant==IN_W)iw.width=10;if(variant==OUT_W)ow.width=10;if(variant==IN_H)iw.height=6;if(variant==OUT_H)ow.height=6;if(variant==IN_RB)iw.rowbytes=55;if(variant==OUT_RB)ow.rowbytes=55;if(variant==IN_EXT)iw.extent_hint.right=10;if(variant==OUT_EXT)ow.extent_hint.bottom=6;if(variant==IN_DEEP)iw.world_flags=PF_WorldFlag_DEEP;if(variant==OUT_DEEP)ow.world_flags=PF_WorldFlag_DEEP;if(variant==IN_WRITEABLE)iw.world_flags=PF_WorldFlag_WRITEABLE;if(variant==OUT_WRITEABLE)ow.world_flags=PF_WorldFlag_WRITEABLE;if(variant==IN_ORIGIN)iw.origin_x=1;if(variant==OUT_ORIGIN)ow.origin_y=-1;if(variant==ALIAS)ow.data=iw.data;if(variant==COUNT4)gcount=4;if(variant==COUNT99)gcount=99;if(variant==PALETTE)palette_bad=1;if(variant==FAIL_LAYER)fail_layer=1;if(variant==FAIL_OUTPUT)fail_output=1;if(variant==FAIL_PARAM)fail_param=50;if(variant==FAIL_CHECKIN)fail_checkin=17;if(variant==FAIL_COLOR)fail_color=17;if(variant==FAIL_WORLD_FMT)fail_worldfmt=2;if(variant==FAIL_SUITE_WORLD)fail_suite=1;if(variant==FAIL_SUITE_COLOR)fail_suite=2;if(variant==FAIL_SUITE_ITER)fail_suite=3;gin=&iw;gout=&ow;gifmt=gofmt=PF_PixelFormat_ARGB32;if(variant==IN_FMT)gifmt=PF_PixelFormat_ARGB64;if(variant==OUT_FMT)gofmt=PF_PixelFormat_ARGB64;PF_EffectWorld ib=iw,ob=ow;co=ci=color_calls=worldfmt_calls=lh=oh=li=iter_hits=phase=phase_bad=0;PF_InData in{};PF_OutData out{};SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;in.pica_basicP=&basic;in.inter.checkout_param=checkout;in.inter.checkin_param=checkparam;PF_SmartRenderInput si{};si.bitdepth=depth;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=layer;cb.checkout_output=output;cb.checkin_layer_pixels=checkin;PF_SmartRenderExtra sx{&si,&cb};PF_SmartRenderExtra*ep=&sx;if(variant==NULL_EXTRA)ep=nullptr;if(variant==NULL_INPUT)sx.input=nullptr;if(variant==NULL_CB)sx.cb=nullptr;if(variant==NULL_LAYER_CB)cb.checkout_layer_pixels=nullptr;if(variant==NULL_OUTPUT_CB)cb.checkout_output=nullptr;if(variant==NULL_CHECKIN_CB)cb.checkin_layer_pixels=nullptr;PF_Err rc=e(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,ep);PF_Err expected=PF_Err_BAD_CALLBACK_PARAM;if(variant==FAIL_LAYER)expected=75;else if(variant==FAIL_OUTPUT)expected=76;else if(variant==FAIL_PARAM)expected=77;else if(variant==FAIL_CHECKIN)expected=78;else if(variant==FAIL_COLOR)expected=79;else if(variant==FAIL_WORLD_FMT)expected=80;else if(variant==FAIL_SUITE_WORLD)expected=A_Err_MISSING_SUITE;bool no_write=std::memcmp(ss,before,SZ)==0&&(variant==ALIAS||untouched(dd,sizeof(dd),0xEE));bool headers=std::memcmp(&iw,&ib,sizeof(iw))==0&&std::memcmp(&ow,&ob,sizeof(ow))==0;bool life=true;if(variant==FAIL_LAYER)life=lh==1&&oh==0&&li==0;else if(variant==FAIL_OUTPUT)life=lh==1&&oh==1&&li==1;else if(variant==NULL_CHECKIN_CB)life=lh==1&&oh==1&&li==0&&co==1&&color_calls==0&&ci==1;else if(variant>=NULL_EXTRA)life=lh==0&&oh==0&&li==0;else life=lh==1&&oh==1&&li==1;if(variant==FAIL_PARAM)life&=co==50&&color_calls==0&&ci==49;if(variant==FAIL_CHECKIN)life&=co==101&&color_calls==100&&ci==101;if(variant==FAIL_COLOR)life&=co==101&&color_calls==17&&ci==101;if(variant==FAIL_SUITE_WORLD)life&=co==0&&color_calls==0&&ci==0;if(variant==FAIL_SUITE_COLOR)life&=co==101&&color_calls==0&&ci==101;if(variant==FAIL_SUITE_ITER)life&=co==101&&color_calls==100&&ci==101;return rc==expected&&iter_hits==0&&no_write&&headers&&life&&!phase_bad;}
enum{C_IN_NULL=1,C_OUT_NULL,C_IN_W,C_OUT_W,C_IN_H,C_OUT_H,C_IN_RB,C_OUT_RB,C_IN_EXT,C_OUT_EXT,C_IN_DEEP,C_OUT_DEEP,C_IN_WRITEABLE,C_OUT_WRITEABLE,C_IN_ORIGIN,C_OUT_ORIGIN,C_ALIAS,C_COUNT4,C_COUNT99,C_PALETTE,C_PF32,C_FMT_MISMATCH,C_NULL_PARAMS,C_NULL_OUTPUT};
static bool classic(Effect e,int v){constexpr int W=11,H=7,RB=56,SZ=RB*H;alignas(16)unsigned char ss[SZ],dd[SZ];std::memcpy(ss,source8,SZ);unsigned char before[SZ];std::memcpy(before,ss,SZ);std::memset(dd,0xEE,SZ);PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)ss;iw.rowbytes=RB;iw.width=W;iw.height=H;iw.extent_hint={0,0,W,H};ow.data=(PF_PixelPtr)dd;ow.rowbytes=RB;ow.width=W;ow.height=H;ow.extent_hint={0,0,W,H};gifmt=gofmt=PF_PixelFormat_ARGB32;gcount=5;palette_bad=0;if(v==C_IN_NULL)iw.data=nullptr;if(v==C_OUT_NULL)ow.data=nullptr;if(v==C_IN_W)iw.width=10;if(v==C_OUT_W)ow.width=10;if(v==C_IN_H)iw.height=6;if(v==C_OUT_H)ow.height=6;if(v==C_IN_RB)iw.rowbytes=55;if(v==C_OUT_RB)ow.rowbytes=55;if(v==C_IN_EXT)iw.extent_hint.right=10;if(v==C_OUT_EXT)ow.extent_hint.bottom=6;if(v==C_IN_DEEP)iw.world_flags=PF_WorldFlag_DEEP;if(v==C_OUT_DEEP)ow.world_flags=PF_WorldFlag_DEEP;if(v==C_IN_WRITEABLE)iw.world_flags=PF_WorldFlag_WRITEABLE;if(v==C_OUT_WRITEABLE)ow.world_flags=PF_WorldFlag_WRITEABLE;if(v==C_IN_ORIGIN)iw.origin_x=1;if(v==C_OUT_ORIGIN)ow.origin_y=-1;if(v==C_ALIAS)ow.data=iw.data;if(v==C_COUNT4)gcount=4;if(v==C_COUNT99)gcount=99;if(v==C_PALETTE)palette_bad=1;if(v==C_PF32){gifmt=gofmt=PF_PixelFormat_ARGB128;iw.world_flags=ow.world_flags=PF_WorldFlag_DEEP;}if(v==C_FMT_MISMATCH)gofmt=PF_PixelFormat_ARGB64;PF_EffectWorld ob=ow;PF_ParamDef defs[102]{};PF_ParamDef*pp[102];for(int n=0;n<102;n++){pp[n]=&defs[n];if(n>=2)defs[n].u.cd.value.red=n-2;}defs[0].u.ld=iw;defs[1].u.sd.value=gcount;PF_EffectWorld ib=defs[0].u.ld;gin=&defs[0].u.ld;gout=&ow;SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;iter_hits=0;PF_Err rc=e(PF_Cmd_RENDER,&in,&out,v==C_NULL_PARAMS?nullptr:pp,v==C_NULL_OUTPUT?nullptr:&ow,nullptr);return rc==PF_Err_BAD_CALLBACK_PARAM&&iter_hits==0&&std::memcmp(ss,before,SZ)==0&&(v==C_ALIAS||untouched(dd,SZ,0xEE))&&std::memcmp(&defs[0].u.ld,&ib,sizeof(ib))==0&&std::memcmp(&ow,&ob,sizeof(ow))==0;}
int main(int c,char**v){s8.iterate=i8;s16.iterate=i16;sf.iterate=iff;sc.PF_GetFloatingPointColorFromColorDef=color;sw.PF_GetPixelFormat=worldfmt;void*h=dlopen(v[1],RTLD_NOW|RTLD_LOCAL);if(!h)return 2;auto e=(Effect)dlsym(h,"EffectMain");if(!e)return 3;int smart_ok=0,classic_ok=0;for(int x=BITDEPTH;x<=NULL_CHECKIN_CB;x++){if(!smart(e,x)){std::fprintf(stderr,"smart guard %d failed\n",x);return 10+x;}smart_ok++;}for(int x=C_IN_NULL;x<=C_NULL_OUTPUT;x++){if(!classic(e,x)){std::fprintf(stderr,"classic guard %d failed\n",x);return 60+x;}classic_ok++;}std::printf("%d %d\n",smart_ok,classic_ok);return 0;}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_guard_probe.") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([_UCRT_CXX, "-std=c++17", "-arch", "arm64", "-isysroot", sdk,
                                "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources",
                                str(cpp), "-o", str(exe)], cwd=ROOT,
                               capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(exe), str(binary)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"guard probe rc={run.returncode}: {run.stderr}")
        smart_count, classic_count = map(int, run.stdout.split())
    return {
        "smart_one_away_rejects": smart_count,
        "classic_one_away_rejects": classic_count,
        "total_rejects": smart_count + classic_count,
        "all_rejected_before_iteration": True,
        "input_and_headers_unchanged": True,
        "output_unchanged": True,
        "checkout_failure_lifecycle": {
            "input_checkout_failure": "no output checkout or layer checkin",
            "output_checkout_failure": "one input layer checkin",
            "validation_parameter_or_palette_failure": "one input layer checkin",
        },
        "smart_parameter_phases": {
            "order": "checkout_all_then_convert_all_then_checkin_all",
            "full_path_counts": [101, 100, 101],
            "first_checkin_error": {
                "error_position": 17,
                "first_error_preserved": True,
                "counts": [101, 100, 101],
            },
            "color_error": {
                "error_position": 17,
                "first_error_preserved": True,
                "counts": [101, 17, 101],
            },
            "missing_color_suite_cleanup_counts": [101, 0, 101],
        },
    }


def validate_only() -> int:
    report = json.loads(REPORT.read_text())
    if report["production_source_sha256"] != sha(SOURCE):
        raise RuntimeError("production source drift")
    if report["owner_report_sha256"] != sha(OWNER_REPORT):
        raise RuntimeError("owner report drift")
    if report["status"] != "exact_bounded_public_owner_and_fail_closed_guards":
        raise RuntimeError("closure status drift")
    if report["generator_sha256"] != sha(Path(__file__)):
        raise RuntimeError("generator drift")
    if report["owner_generator_sha256"] != sha(
            ROOT / "tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py"):
        raise RuntimeError("owner generator drift")
    guards = report["guards"]
    if (guards["smart_one_away_rejects"], guards["classic_one_away_rejects"],
            guards["total_rejects"]) != (38, 24, 62):
        raise RuntimeError("guard cardinality drift")
    expected_phases = {
        "order": "checkout_all_then_convert_all_then_checkin_all",
        "full_path_counts": [101, 100, 101],
        "first_checkin_error": {
            "error_position": 17, "first_error_preserved": True,
            "counts": [101, 100, 101],
        },
        "color_error": {
            "error_position": 17, "first_error_preserved": True,
            "counts": [101, 17, 101],
        },
        "missing_color_suite_cleanup_counts": [101, 0, 101],
    }
    if guards["smart_parameter_phases"] != expected_phases:
        raise RuntimeError("Smart parameter phase/cleanup evidence drift")
    build = report["isolated_universal_build"]
    for key in ("bundle", "binary", "build_log"):
        if not Path(build[key]).is_file():
            if key != "bundle" or not Path(build[key]).is_dir():
                raise RuntimeError(f"durable artifact missing: {key}")
    bundle = Path(build["bundle"])
    binary = Path(build["binary"])
    info_plist = bundle / "Contents/Info.plist"
    resource = bundle / "Contents/Resources/ColorKeep.rsrc"
    if binary != bundle / "Contents/MacOS/ColorKeep":
        raise RuntimeError("candidate bundle/binary path drift")
    if build["binary_sha256"] != sha(Path(build["binary"])):
        raise RuntimeError("candidate binary drift")
    if build["info_plist_sha256"] != sha(info_plist):
        raise RuntimeError("candidate Info.plist drift")
    if build["resource_sha256"] != sha(resource):
        raise RuntimeError("candidate resource drift")
    if build["build_log_sha256"] != sha(Path(build["build_log"])):
        raise RuntimeError("build transcript drift")
    actual_archs = subprocess.check_output(["lipo", "-archs", str(binary)], text=True).split()
    if set(actual_archs) != {"arm64", "x86_64"} or actual_archs != build["architectures"]:
        raise RuntimeError("candidate architecture drift")
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", "--verbose=2",
                             str(bundle)], capture_output=True, text=True)
    if verify.returncode or build["codesign_verify"] != "pass":
        raise RuntimeError("candidate code signature drift")
    print("PASS: ColorKeep public guard closure validates")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        return validate_only()
    owner = json.loads(OWNER_REPORT.read_text())
    if owner["status"] != "installed_public_six_cell_raw_exact" or len(owner["cells"]) != 6:
        raise RuntimeError("installed/exported owner matrix is not closed")
    binary, build = build_candidate()
    candidate = matrix.execute_installed(binary, valid_inputs())
    parts = active_parts(candidate)
    for part, cell in zip(parts, owner["cells"]):
        if hashlib.sha256(part).hexdigest() != cell["actual_exported_owner_sha256"]:
            raise RuntimeError(f"candidate owner mismatch: {cell['depth']} count={cell['enabled_count']}")
    candidate_with_classic = matrix.execute_installed(binary, valid_inputs(), include_classic=True)
    classic_parts = classic_active_parts(candidate_with_classic)
    classic_owner_cells = [owner["cells"][index] for index in (0, 1, 3, 4)]
    for part, cell in zip(classic_parts, classic_owner_cells):
        if hashlib.sha256(part).hexdigest() != cell["actual_exported_owner_sha256"]:
            raise RuntimeError(f"candidate classic mismatch: {cell['depth']} count={cell['enabled_count']}")
    guards = guard_probe(binary)
    report = {
        "schema": "colorkeep.public-guard-closure/1",
        "status": "exact_bounded_public_owner_and_fail_closed_guards",
        "production_source": str(SOURCE.relative_to(ROOT)),
        "production_source_sha256": sha(SOURCE),
        "generator_sha256": sha(Path(__file__)),
        "owner_generator_sha256": sha(
            ROOT / "tools/emulation/test_colorkeep_installed_public_covering_matrix_20260812.py"),
        "owner_report": str(OWNER_REPORT.relative_to(ROOT)),
        "owner_report_sha256": sha(OWNER_REPORT),
        "owner_cells": 6,
        "candidate_active_sha256": [hashlib.sha256(part).hexdigest() for part in parts],
        "candidate_matches_actual_exported_owner": True,
        "candidate_classic_active_sha256": [hashlib.sha256(part).hexdigest()
                                             for part in classic_parts],
        "candidate_classic_matches_corresponding_exported_smart_owner": True,
        "candidate_input_padding_headers_lifecycle": "same public harness gates as installed owner matrix",
        "guards": guards,
        "isolated_universal_build": build,
        "admission": {
            "geometry": [11, 7], "row_padding_bytes": 12,
            "enabled_color_counts": [5, 100],
            "palette": "fixed 100-entry public ARGB8 palette in owner report",
            "smart_depths": [8, 16, 32], "classic_depths": [8, 16],
            "classic_pf32": "fail_closed",
        },
        "not_claimed": ["arbitrary geometry, rowbytes, palette, or enabled count",
                        "native Windows AE execution", "current Mac install changed by this closure",
                        "After Effects host load/render of the candidate"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# ColorKeep bounded public-owner guard closure — 2026-08-12\n\n"
        "The unchanged Windows AEX exported Smart owner under the pinned AEXCompat worker, "
        "the current installed Mac public `EffectMain`, and an isolated Universal candidate "
        "are raw exact for the six declared 11×7 cells: counts 5/100 × PF8/PF16/PF32. "
        "The candidate classic PF8/PF16 paths are also raw-identical to the four "
        "corresponding exported Smart-owner cells. "
        "The Mac public harness also pins complete input immutability, 12-byte input/output "
        "row padding, world headers, 101 ordered parameter checkout/checkins, and layer/output lifecycle.\n\n"
        f"The candidate rejects all {guards['total_rejects']} one-away Smart/classic guard cases "
        "before pixel iteration. Classic PF32 and every unlisted geometry, rowbytes, format, "
        "count, or palette remain fail-closed. Smart parameter work is phase-ordered as all 101 "
        "checkouts, then 100 color conversions, then all 101 checkins; a color or checkin error "
        "preserves its first error while cleanup continues through every successfully checked-out "
        "parameter. The build is isolated; the current install was not changed.\n"
    )
    print(json.dumps({"status": report["status"], "owner_cells": 6,
                      "guard_rejects": guards["total_rejects"],
                      "binary": str(binary)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
