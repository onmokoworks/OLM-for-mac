#!/usr/bin/env python3
"""Exercise the production Mac PF8 Layer-noise adapter against the exact core."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
REPORT = ROOT / "refs/conformance/dblur_mac_mode2_host_adapter_20260805.json"


def main() -> int:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("fail closed: C++ compiler not found")
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], capture_output=True, text=True,
        check=True).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="dblur_mac_mode2_adapter_") as name:
        directory = Path(name)
        probe = directory / "probe.cpp"
        executable = directory / "probe"
        production = str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')
        probe.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace {{
constexpr int W=16,H=16,RB=76;
using World=std::array<std::uint8_t,RB*H>;
std::uint8_t* px(World& w,int x,int y){{return w.data()+y*RB+x*4;}}
bool pad(const World&w,std::uint8_t v){{for(int y=0;y<H;++y)for(int i=W*4;i<RB;++i)if(w[y*RB+i]!=v)return false;return true;}}
void fill(World&w,int salt){{w.fill(0xA5);for(int y=0;y<H;++y)for(int x=0;x<W;++x){{auto*p=px(w,x,y);p[0]=static_cast<std::uint8_t>(64+((x*11+y*17+salt)&191));p[1]=static_cast<std::uint8_t>((x*29+y*3+salt)&255);p[2]=static_cast<std::uint8_t>((x*5+y*31+2*salt)&255);p[3]=static_cast<std::uint8_t>((x*19+y*7+3*salt)&255);}}}}
}}

int main(){{
 World input,noise,output;fill(input,13);fill(noise,47);output.fill(0xEE);auto input_before=input,noise_before=noise;
 PF_EffectWorld in{{}},nw{{}},out{{}};in.data=(PF_PixelPtr)input.data();nw.data=(PF_PixelPtr)noise.data();out.data=(PF_PixelPtr)output.data();
 for(auto*w:{{&in,&nw,&out}}){{w->rowbytes=RB;w->width=W;w->height=H;w->extent_hint={{0,0,W,H}};}}
 std::array<std::uint8_t,W*H*4> rgba{{}},expected{{}};
 for(int y=0;y<H;++y)for(int x=0;x<W;++x){{auto*p=px(input,x,y);auto*q=rgba.data()+(y*W+x)*4;q[0]=p[1];q[1]=p[2];q[2]=p[3];q[3]=p[0];}}
 OLMDirectionalBlurInfo info{{}};info.angle_deg=27;info.brightness_gain=1.125;info.size_variation=38;info.front_strength=37;info.front_alpha_fade=9;info.front_sharp_tail=23;info.back_strength=19;info.back_alpha_fade=7;info.back_sharp_tail=31;info.noise_variation=73;info.noise_type=3;info.render_scale_x=info.render_scale_y=1;
 if(olm_dblur_layer_mode2_rgba8(rgba.data(),expected.data(),W,H,27,1.125f,37,9,23,19,7,31,38,73,noise.data(),W,H,RB,0,0,0,0,1)!=0)return 10;
 int used=0;PF_Err err=OLMDirectionalBlurTestRenderWorldWithNoise(&in,&out,&nw,&info,8,&used);if(err||used!=1)return 11;
 bool exact=true;for(int y=0;y<H;++y)for(int x=0;x<W;++x){{auto*p=px(output,x,y);auto*q=expected.data()+(y*W+x)*4;exact=exact&&p[0]==q[3]&&p[1]==q[0]&&p[2]==q[1]&&p[3]==q[2];}}
 bool ownership=input==input_before&&noise==noise_before&&pad(input,0xA5)&&pad(noise,0xA5)&&pad(output,0xEE);
 PF_EffectWorld bad=nw;bad.width=W-1;int bad_used=1;PF_Err bad_err=OLMDirectionalBlurTestRenderWorldWithNoise(&in,&out,&bad,&info,8,&bad_used);
 bool fail_closed=bad_used==0&&bad_err==PF_Err_BAD_CALLBACK_PARAM;
 std::printf("{{\\\"status\\\":\\\"%s\\\",\\\"used_exact\\\":%d,\\\"pixels_match\\\":%s,\\\"ownership_preserved\\\":%s,\\\"dimension_mismatch_fail_closed\\\":%s}}\\n",exact&&ownership&&fail_closed?"pass":"fail",used,exact?"true":"false",ownership?"true":"false",fail_closed?"true":"false");
 return exact&&ownership&&fail_closed?0:12;
}}
''', encoding="utf-8")
        command = [
            compiler, "-std=c++17", "-arch", "arm64", "-O2",
            "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
            "-ffunction-sections", "-fdata-sections",
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(probe), str(ROOT / "core/dblur_frontonly.cpp"),
            str(ROOT / "core/dblur_rotate.cpp"),
            str(ROOT / "core/dblur_rowdriver.cpp"),
            str(ROOT / "core/dblur_field.cpp"), "-Wl,-dead_strip",
            "-framework", "Cocoa",
            "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=ROOT, check=False,
                               capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"adapter compile failed:\n{build.stderr}")
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True,
                             text=True, check=False)
        if run.returncode:
            raise RuntimeError(f"adapter failed ({run.returncode}): {run.stderr}")
        result = json.loads(run.stdout)
    report = {
        "schema": 1,
        "kind": "dblur_mac_mode2_host_adapter_20260805",
        **result,
        "scope": "arm64 source-included production PF8 adapter, equal 16x16 Layer worlds",
        "parameters": {"angle": 27, "front": 37, "back": 19,
                       "noise_variation": 73, "noise_type": 3},
        "claim_boundary": {"mac_adapter_exact": result["status"] == "pass",
                           "mac_ae_pixel_exact": False},
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": result,
                      "report": str(REPORT.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
