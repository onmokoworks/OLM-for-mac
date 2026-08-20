#!/usr/bin/env python3
"""Release-like OLMRadialBlur GenericBaseline geometry driver."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
GEOMETRIES = {"hd": (1920, 1080), "uhd": (3840, 2160)}
RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size\s*$", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", required=True, choices=GEOMETRIES)
    args = parser.parse_args()
    width, height = GEOMETRIES[args.geometry]
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_production_perf_") as name:
        temp = Path(name)
        cpp, executable = temp / "driver.cpp", temp / "driver"
        cpp.write_text(f'''#include "{source}"
#include <cstdlib>
#include <vector>
template<class P> int render(short depth,int type,int w,int h){{
 const int in_rb=w*(int)sizeof(P)+3*(int)sizeof(P),out_rb=w*(int)sizeof(P)+7*(int)sizeof(P);
 std::vector<unsigned char>a((size_t)in_rb*h),b((size_t)out_rb*h);
 PF_EffectWorld x{{}},y{{}};x.data=(PF_PixelPtr)a.data();x.rowbytes=in_rb;x.width=w;x.height=h;
 y.data=(PF_PixelPtr)b.data();y.rowbytes=out_rb;y.width=w;y.height=h;
 for(int j=0;j<h;++j)for(int i=0;i<w;++i){{P*p=(P*)(a.data()+(size_t)j*in_rb)+i;p->alpha=(decltype(p->alpha))1;p->red=(decltype(p->red))((i+j)%7);}}
 OLMRadialBlurInfo q{{}};q.blur_type=type;q.center_x=w*.23;q.center_y=h*.71;q.outer_strength=1;
 q.outer_offset_mode=1;q.inner_offset_mode=1;q.repeat_border=TRUE;q.ratio=2.25;q.angle_deg=-137.5;
 q.quality=1;q.brightness_gain=1;q.noise_type=1;q.seed=1;q.thickness=10;q.comp_width=w;q.comp_height=h;
 return OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)==PF_Err_NONE?0:1;
}}
int main(int c,char**v){{int w=atoi(v[1]),h=atoi(v[2]),type=atoi(v[3]),depth=atoi(v[4]);
 if(depth==8)return render<PF_Pixel8>(8,type,w,h);if(depth==16)return render<PF_Pixel16>(16,type,w,h);return render<PF_PixelFloat>(32,type,w,h);}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-DNDEBUG",
            "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
            "-DOLM_RADIALBLUR_TEST_SEAM", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(executable),
        ], cwd=ROOT, text=True, capture_output=True)
        if build.returncode:
            print(build.stderr)
            return build.returncode
        cases = []
        for family, blur_type in (("zoom", 1), ("rotation", 2)):
            for depth in (8, 16, 32):
                started = time.monotonic()
                run = subprocess.run(
                    ["/usr/bin/time", "-lp", str(executable), str(width), str(height),
                     str(blur_type), str(depth)], text=True, capture_output=True,
                )
                match = RSS.search(run.stderr)
                cases.append({
                    "family": family, "depth_bpc": depth,
                    "wall_seconds": round(time.monotonic() - started, 6),
                    "peak_rss_bytes": int(match.group(1)) if match else None,
                    "returncode": run.returncode,
                    "input_padding_pixels": 3, "output_padding_pixels": 7,
                })
                if run.returncode:
                    print(run.stderr)
                    return run.returncode
        print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
