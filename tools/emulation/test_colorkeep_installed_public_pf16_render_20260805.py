#!/usr/bin/env python3
"""Installed EffectMain -> legacy PF16 dispatch -> worker/writer via synthetic suites."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from olm_installed_identity import verified_binary

ROOT = Path(__file__).resolve().parents[2]
INSTALLED, _IDENTITY = verified_binary("ColorKeep")
ACTUAL_RAW = ROOT / "refs/conformance/colorkeep_pf16_extended_range_actual_aex_20260805.argb16"
REPORT = ROOT / "refs/conformance/colorkeep_installed_public_pf16_render_20260805.json"

COLORS = ((1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 0.0), (0.5, 0.25, 0.75, 1.0))
PIXELS = (
    (32768, 32768, 32768, 32768), (32769, 32768, 32768, 32768),
    (32768, 32769, 32768, 32768), (32768, 32768, 32769, 32768),
    (32768, 32768, 32768, 32769), (65535, 65535, 65535, 65535),
    (0, 65535, 32769, 49152), (16384, 8192, 24576, 32768),
)


def execute_installed() -> bytes:
    path = str(INSTALLED).replace('"', '\\"')
    colors = ",".join(f"{{{a}f,{r}f,{g}f,{b}f}}" for a, r, g, b in COLORS)
    pixels = ",".join("{" + ",".join(str(value) for value in pixel) + "}" for pixel in PIXELS)
    code = f'''#include <cstdio>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include "mac/ColorKeep/ColorKeep.h"
using Main=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
static PF_Iterate16Suite2 iterate16_suite{{}};static PF_ColorParamSuite1 color_suite{{}};static int acquire_color,acquire_iter,release_color,release_iter,pixel_calls;
static PF_ParamDef defs[102];static PF_PixelFloat floating_colors[]={{{colors}}};
static SPErr acquire(const char*name,int32 version,const void**suite){{if(!std::strcmp(name,kPFColorParamSuite)&&version==kPFColorParamSuiteVersion1){{*suite=&color_suite;acquire_color++;return 0;}}if(!std::strcmp(name,kPFIterate16Suite)&&version==kPFIterate16SuiteVersion2){{*suite=&iterate16_suite;acquire_iter++;return 0;}}return 88;}}
static SPErr release(const char*name,int32 version){{if(!std::strcmp(name,kPFColorParamSuite)&&version==kPFColorParamSuiteVersion1)release_color++;else if(!std::strcmp(name,kPFIterate16Suite)&&version==kPFIterate16SuiteVersion2)release_iter++;else return 89;return 0;}}
static PF_Err color(PF_ProgPtr,const PF_ParamDef*p,PF_PixelFloat*out){{ptrdiff_t index=p-defs-2;if(index<0||index>=3)return 90;*out=floating_colors[index];return 0;}}
static PF_Err iterate(PF_InData*in,A_long base,A_long final,PF_EffectWorld*src,const PF_Rect*area,void*ref,PF_Err(*fn)(void*,A_long,A_long,PF_Pixel16*,PF_Pixel16*),PF_EffectWorld*dst){{if(base!=0||final!=3||area)return 91;for(int y=0;y<dst->height;y++)for(int x=0;x<dst->width;x++){{auto*s=(PF_Pixel16*)((char*)src->data+y*src->rowbytes+x*8);auto*d=(PF_Pixel16*)((char*)dst->data+y*dst->rowbytes+x*8);PF_Err e=fn(ref,x,y,s,d);if(e)return e;pixel_calls++;}}return 0;}}
int main(){{void*h=dlopen("{path}",RTLD_NOW|RTLD_LOCAL);if(!h)return 10;auto mainfn=(Main)dlsym(h,"EffectMain");if(!mainfn)return 11;SPBasicSuite basic{{}};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;color_suite.PF_GetFloatingPointColorFromColorDef=color;iterate16_suite.iterate=iterate;
PF_Pixel16 pattern[]={{{pixels}}};unsigned char input[120],output[120];std::memset(input,0xcc,sizeof(input));std::memset(output,0xee,sizeof(output));for(int i=0;i<12;i++)std::memcpy(input+(i/4)*40+(i%4)*8,&pattern[i%8],8);
PF_InData in{{}};PF_OutData out{{}};in.pica_basicP=&basic;in.effect_ref=(PF_ProgPtr)0x1234;PF_ParamDef*params[102];for(int i=0;i<102;i++)params[i]=&defs[i];defs[0].u.ld.data=reinterpret_cast<PF_PixelPtr>(input);defs[0].u.ld.rowbytes=40;defs[0].u.ld.width=4;defs[0].u.ld.height=3;defs[0].u.ld.world_flags=PF_WorldFlag_DEEP;defs[1].u.sd.value=3;
PF_LayerDef dst{{}};dst.data=reinterpret_cast<PF_PixelPtr>(output);dst.rowbytes=40;dst.width=4;dst.height=3;dst.world_flags=PF_WorldFlag_DEEP;PF_Err rc=mainfn(PF_Cmd_RENDER,&in,&out,params,&dst,nullptr);if(rc)return 12;if(acquire_color!=1||acquire_iter!=1||release_color!=1||release_iter!=1||pixel_calls!=12)return 13;std::fwrite(output,1,sizeof(output),stdout);return 0;}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_public_pf16_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        build = subprocess.run([
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp), "-o", str(exe),
        ], cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, f"exit={run.returncode} {run.stderr.decode(errors='replace')}"
        return run.stdout


def main() -> int:
    installed_hash = hashlib.sha256(INSTALLED.read_bytes()).hexdigest()
    assert installed_hash == _IDENTITY["sha256"]
    observed = execute_installed()
    expected = ACTUAL_RAW.read_bytes()
    assert observed == expected
    digest = hashlib.sha256(observed).hexdigest()
    report = {
        "status": "installed_public_entry_to_writer_exact",
        "installed_binary": str(INSTALLED),
        "installed_binary_sha256": installed_hash,
        "public_path": "dlopen installed bundle -> dlsym EffectMain -> PF_Cmd_RENDER -> CheckoutInfo -> PF iterate16 Suite v2 -> ColorKeep16Func -> output world",
        "synthetic_host_suites": {
            "PF ColorParamSuite v1": {"acquire": 1, "release": 1, "purpose": "three floating-point key colors"},
            "PF iterate16 Suite v2": {"acquire": 1, "release": 1, "purpose": "12 typed pixel callbacks and rowbytes-aware output writes"},
        },
        "fixture": "PF16 extended-range 4x3, rowbytes40, 8-byte input/output padding",
        "typed_pixel_callbacks": 12,
        "actual_aex_fixture": str(ACTUAL_RAW.relative_to(ROOT)),
        "actual_aex_fixture_sha256": hashlib.sha256(expected).hexdigest(),
        "installed_output_sha256": digest,
        "raw_exact": True,
        "padding_exact": "all three 8-byte output padding regions remain 0xee",
        "connection_closed": "The installed hash is now exercised through its public rendering entry, real legacy PF16 dispatch, internal worker, and writer in one call chain; no local-symbol shortcut or source recompilation supplies the behavior under test.",
        "remaining_boundary": "Synthetic suites prove the plugin-side call chain, not AE's suite implementation or AE loading/export of this hash.",
        "not_proven": ["native After Effects suite behavior", "After Effects loaded-module identity", "AE project export"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
