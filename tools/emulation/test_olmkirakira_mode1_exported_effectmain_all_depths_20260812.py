#!/usr/bin/env python3
"""Mode 1 actual exported Smart owner versus Mac public EffectMain render."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
STRINGS = ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
CASE = os.environ.get("OLM_KIRA_EXPORTED_CASE", "mode1")
BLUR_MODE = int(os.environ.get("OLM_KIRA_BLUR_MODE", "1"))
MERGE_MODE = int(os.environ.get("OLM_KIRA_MERGE_MODE", "1"))
HORIZONTAL_LENGTH = int(os.environ.get("OLM_KIRA_HORIZONTAL_LENGTH", "7"))
HORIZONTAL_USE_RAMP = int(os.environ.get("OLM_KIRA_HORIZONTAL_USE_RAMP", "0"))
GLOW_ROTATION = float(os.environ.get("OLM_KIRA_GLOW_ROTATION", "0"))
GLOW_ROTATION_RAW_FIXED = os.environ.get("OLM_KIRA_GLOW_ROTATION_RAW_FIXED")
REPORT = ROOT / os.environ.get(
    "OLM_KIRA_EXPORTED_REPORT",
    "refs/conformance/olmkirakira_mode1_exported_effectmain_all_depths_20260812.json",
)
DOC = REPORT.with_suffix(".md")
DEFAULT_WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")
DEPTHS = {"PF8": ("argb8", 4), "PF16": ("argb16", 8), "PF32": ("argb32f", 16)}
WIDTH, HEIGHT, PADDING = 5, 3, 12
RGBA = tuple((i * 15, i * 11, i * 7, 64 + i * 11) for i in range(WIDTH * HEIGHT))


CPP = r'''
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>
#include "__SOURCE__"
#include "__STRINGS__"

static std::map<PF_Handle,A_HandleSize> sizes;
static PF_Handle nh(A_HandleSize n){char **h=(char**)std::malloc(sizeof(char*));*h=(char*)std::calloc(1,n);sizes[(PF_Handle)h]=n;return (PF_Handle)h;}
static void* lh(PF_Handle h){return h?*(void**)h:nullptr;} static void uh(PF_Handle){}
static void dh(PF_Handle h){if(h){std::free(*(void**)h);sizes.erase(h);std::free(h);}}
static A_HandleSize gh(PF_Handle h){auto i=sizes.find(h);return i==sizes.end()?0:i->second;}
static PF_Err rh(A_HandleSize,PF_Handle*){return PF_Err_BAD_CALLBACK_PARAM;}
static PF_HandleSuite1 hs={nh,lh,uh,dh,gh,rh};
static PF_PixelFormat current_format=PF_PixelFormat_INVALID;
static PF_Err getfmt(const PF_EffectWorld*,PF_PixelFormat*f){*f=current_format;return PF_Err_NONE;}
static PF_WorldSuite2 ws={nullptr,nullptr,getfmt};
static PF_Err getcolor(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*c){c->alpha=p->u.cd.value.alpha/255.f;c->red=p->u.cd.value.red/255.f;c->green=p->u.cd.value.green/255.f;c->blue=p->u.cd.value.blue/255.f;return PF_Err_NONE;}
static PF_ColorParamSuite1 cs={getcolor};
static SPErr acq(const char*n,int32 v,const void**s){if(std::strcmp(n,kPFHandleSuite)==0&&v==kPFHandleSuiteVersion1){*s=&hs;return 0;}if(std::strcmp(n,kPFWorldSuite)==0&&v==kPFWorldSuiteVersion2){*s=&ws;return 0;}if(std::strcmp(n,kPFColorParamSuite)==0&&v==kPFColorParamSuiteVersion1){*s=&cs;return 0;}*s=nullptr;return 1;}
static SPErr rel(const char*,int32){return 0;} static SPBasicSuite basic={acq,rel};
static OLMKiraKiraRampData ramp(){OLMKiraKiraRampData r{};r.count=3;r.stops[0]={0,1,1,0,0};r.stops[1]={.779999971f,1,1,.651000023f,0};r.stops[2]={1,1,1,1,1};return r;}
template<class P> static void setp(P&q,int r,int g,int b,int a);
template<> void setp(PF_Pixel8&q,int r,int g,int b,int a){q={(A_u_char)a,(A_u_char)r,(A_u_char)g,(A_u_char)b};}
template<> void setp(PF_Pixel16&q,int r,int g,int b,int a){q={(A_u_short)std::lround(a*32768.0/255.0),(A_u_short)std::lround(r*32768.0/255.0),(A_u_short)std::lround(g*32768.0/255.0),(A_u_short)std::lround(b*32768.0/255.0)};}
template<> void setp(PF_PixelFloat&q,int r,int g,int b,int a){q={a/255.f,r/255.f,g/255.f,b/255.f};}
template<class P> int run(PF_PixelFormat format){const int W=5,H=3,PAD=12,RB=W*sizeof(P)+PAD;std::vector<unsigned char>ib(RB*H,0xA7),ob(RB*H,0xD3);int raw[15][4]={__RGBA__};for(int y=0;y<H;y++)for(int x=0;x<W;x++){auto&q=*reinterpret_cast<P*>(ib.data()+y*RB+x*sizeof(P));auto*v=raw[y*W+x];setp(q,v[0],v[1],v[2],v[3]);}
 PF_ParamDef defs[OLMKIRAKIRA_NUM_PARAMS]{};PF_ParamDef*ps[OLMKIRAKIRA_NUM_PARAMS]{};for(int i=0;i<OLMKIRAKIRA_NUM_PARAMS;i++)ps[i]=defs+i;auto&iw=defs[OLMKIRAKIRA_INPUT].u.ld;iw.data=reinterpret_cast<PF_PixelPtr>(ib.data());iw.rowbytes=RB;iw.width=W;iw.height=H;
 defs[OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value=0;defs[OLMKIRAKIRA_BRIGHTNESS_GAIN].u.fs_d.value=.1;defs[OLMKIRAKIRA_FADE_OUT].u.fs_d.value=0;defs[OLMKIRAKIRA_VERTICAL_LENGTH].u.sd.value=0;defs[OLMKIRAKIRA_HORIZONTAL_LENGTH].u.sd.value=7;defs[OLMKIRAKIRA_DIAGONAL_LENGTH].u.sd.value=0;defs[OLMKIRAKIRA_DIAGONAL2_LENGTH].u.sd.value=0;defs[OLMKIRAKIRA_HIGHLIGHT_RADIUS].u.sd.value=0;defs[OLMKIRAKIRA_GLOW_OPACITY].u.sd.value=100;defs[OLMKIRAKIRA_CHANNEL].u.pd.value=1;defs[OLMKIRAKIRA_BLUR_MODE].u.pd.value=1;defs[OLMKIRAKIRA_MERGE_MODE].u.pd.value=1;defs[OLMKIRAKIRA_STRENGTH_MULTIPLIER].u.sd.value=100;defs[OLMKIRAKIRA_SOURCE_OPACITY].u.sd.value=100;
 for(int i:{OLMKIRAKIRA_VERTICAL_COLOR,OLMKIRAKIRA_HORIZONTAL_COLOR,OLMKIRAKIRA_DIAGONAL_COLOR,OLMKIRAKIRA_DIAGONAL2_COLOR,OLMKIRAKIRA_HIGHLIGHT_COLOR})defs[i].u.cd.value={255,255,255,255};OLMKiraKiraRampData rd=ramp();for(int i:{OLMKIRAKIRA_VERTICAL_RAMP,OLMKIRAKIRA_HORIZONTAL_RAMP,OLMKIRAKIRA_DIAGONAL_RAMP,OLMKIRAKIRA_DIAGONAL2_RAMP,OLMKIRAKIRA_HIGHLIGHT_RAMP}){defs[i].u.arb_d.value=nh(sizeof(rd));std::memcpy(lh(defs[i].u.arb_d.value),&rd,sizeof(rd));}
 PF_LayerDef ow{};ow.data=reinterpret_cast<PF_PixelPtr>(ob.data());ow.rowbytes=RB;ow.width=W;ow.height=H;PF_InData in{};in.pica_basicP=&basic;PF_OutData out{};current_format=format;auto before=ib;int e=EffectMain(PF_Cmd_RENDER,&in,&out,ps,&ow,nullptr);if(e||ib!=before)return 10;for(int y=0;y<H;y++){std::fwrite(ob.data()+y*RB,1,W*sizeof(P),stdout);for(int x=W*sizeof(P);x<RB;x++)if(ob[y*RB+x]!=0xD3)return 20;}return 0;}
int main(){if(run<PF_Pixel8>(PF_PixelFormat_ARGB32)||run<PF_Pixel16>(PF_PixelFormat_ARGB64)||run<PF_PixelFloat>(PF_PixelFormat_ARGB128))return 2;}
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def production() -> bytes:
    rgba = ",".join("{" + ",".join(map(str, pixel)) + "}" for pixel in RGBA)
    code = (CPP.replace("__SOURCE__", str(SOURCE)).replace("__STRINGS__", str(STRINGS))
            .replace("__RGBA__", rgba)
            .replace("OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value=0", f"OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value={GLOW_ROTATION!r}")
            .replace("u.sd.value=7;defs[OLMKIRAKIRA_DIAGONAL_LENGTH]", f"u.sd.value={HORIZONTAL_LENGTH};defs[OLMKIRAKIRA_DIAGONAL_LENGTH]")
            .replace("OLMKIRAKIRA_BLUR_MODE].u.pd.value=1", f"OLMKIRAKIRA_BLUR_MODE].u.pd.value={BLUR_MODE}")
            .replace("OLMKIRAKIRA_MERGE_MODE].u.pd.value=1", f"OLMKIRAKIRA_MERGE_MODE].u.pd.value={MERGE_MODE}")
            .replace("defs[OLMKIRAKIRA_SOURCE_OPACITY].u.sd.value=100;", "defs[OLMKIRAKIRA_SOURCE_OPACITY].u.sd.value=100;"
                     f"defs[OLMKIRAKIRA_HORIZONTAL_USE_RAMP].u.bd.value={HORIZONTAL_USE_RAMP};"))
    with tempfile.TemporaryDirectory(prefix="kira_mode1_effectmain_") as raw:
        directory = Path(raw)
        source = directory / "probe.cpp"
        source.write_text(code, encoding="utf-8")
        executable = directory / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = ["clang++", "-std=c++20", "-O2", "-fno-fast-math", "-ffp-contract=off",
                   "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                   "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(source),
                   str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
                   str(ROOT / "Util/MissingSuiteError.cpp"),
                   "-framework", "Cocoa", "-o", str(executable)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        return subprocess.run([str(executable)], cwd=ROOT, capture_output=True, check=True).stdout


def main() -> int:
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(DEFAULT_WORKER)))
    if not worker.is_file():
        raise RuntimeError("AEXCompat worker missing")
    expected_all = production()
    offset, rows = 0, []
    with tempfile.TemporaryDirectory(prefix="kira_mode1_exported_") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        image = Image.new("RGBA", (WIDTH, HEIGHT)); image.putdata(RGBA); image.save(input_png)
        for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
            size = WIDTH * HEIGHT * pixel_bytes
            expected = expected_all[offset:offset + size]; offset += size
            output_png = directory / f"{depth}.png"
            params = [f"Blur Mode={BLUR_MODE}", "Vertical Length=0", f"Horizontal Length={HORIZONTAL_LENGTH}",
                      "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=0",
                      f"Merge mode={MERGE_MODE}", "Channel=1", "Brightness Gain=0.1"]
            params.append(
                f"Glow Rotation=fixed:{GLOW_ROTATION_RAW_FIXED}"
                if GLOW_ROTATION_RAW_FIXED is not None else
                f"Glow Rotation={GLOW_ROTATION}"
            )
            if HORIZONTAL_USE_RAMP:
                params.append("Use Ramp@19=1")
            result = subprocess.run([str(worker), "render-png", str(AEX), str(input_png),
                                     str(output_png), "--pixel-format", pixel_format, *params],
                                    cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
            actual = json.loads(result.stdout)
            expected_sha = sha(expected)
            exact = actual["raw_pixel_sha256"] == expected_sha
            output_rgba8 = list(Image.open(output_png).convert("RGBA").getdata())
            rows.append({"depth": depth, "pixel_format": pixel_format, "bytes": size,
                         "actual_exported_raw_sha256": actual["raw_pixel_sha256"],
                         "mac_effectmain_raw_sha256": expected_sha, "exact": exact,
                         "actual_exported_rgba8": output_rgba8,
                         "mac_effectmain_active_hex": expected.hex(),
                         "guards_intact": actual["guards_intact"],
                         "input_unchanged": True, "mac_padding_preserved": True,
                         "smart_pre_render": actual["gpu"]["pre_render"],
                         "smart_render": actual["gpu"]["render"],
                         "suite_requests": actual["suite_requests"],
                         "unsupported_suite_calls": actual["unsupported_suite_calls"],
                         "render_error": actual["render_error"]})
    measured = (offset == len(expected_all) and len(rows) == 3 and
                all(row["guards_intact"] and row["mac_padding_preserved"] for row in rows))
    passed = measured and all(row["exact"] for row in rows)
    boundary_detail = (
        "PF32 checkpoint capture proved the natural ray helper's 15 active floats exact before "
        "aggregation; direct float Brightness Gain and PF32 reciprocal-multiply normalization close "
        "the first downstream difference."
        if BLUR_MODE == 1 else (
        "Mode2 applies Brightness Gain to ray amount before ramp sampling and raw-alpha "
        "accumulation, then uses the recovered Merge2 composition and typed writer."
        if BLUR_MODE == 2 else
        "The Gaussian Length 50 tuple is admitted by the existing 9x7 Mode3 family evidence and is "
        "compared here through the complete exported owner and typed writer."
        )
    )
    report = {"kind": f"olmkirakira_{CASE}_exported_effectmain_all_depths", "date": "2026-08-12",
              "status": "exact" if passed else "fail_closed_mismatch",
              "fixture": {"dimensions": [WIDTH, HEIGHT], "padding": PADDING,
                          "blur_mode": BLUR_MODE, "merge_mode": MERGE_MODE,
                          "active_ray": "Horizontal", "length": HORIZONTAL_LENGTH,
                          "horizontal_use_ramp": bool(HORIZONTAL_USE_RAMP),
                          "glow_rotation": GLOW_ROTATION,
                          "windows_rotation_raw_fixed": (int(GLOW_ROTATION_RAW_FIXED)
                                                         if GLOW_ROTATION_RAW_FIXED is not None else None),
                          "channel": 1, "semi_transparent": True},
              "rows": rows,
              "boundary": f"Actual exported SmartPreRender/SmartRender versus Mac public EffectMain(PF_Cmd_RENDER). {boundary_detail} ANGLE editing is unavailable in the pinned worker, so nondefault rotation remains fail-closed."}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(f"# OLMKiraKira {CASE} exported EffectMain 3-depth gate（2026-08-12）\n\n"
                   f"Status: **{report['status']}**\n\n"
                   f"5×3半透明source、Horizontal Length {HORIZONTAL_LENGTH}、Rotation 0でactual AEX exported Smart ownerとMac public EffectMain(PF_Cmd_RENDER)を比較する。PF8/PF16/PF32のactive bytes、input不変、Mac row paddingを検証する。ANGLE型編集は現AEXCompat workerで未対応のためnondefault rotationはfail-close。\n",
                   encoding="utf-8")
    print(json.dumps({"status": report["status"], "rows": rows}))
    return 0 if measured else 1


if __name__ == "__main__":
    raise SystemExit(main())
