#!/usr/bin/env python3
"""Release-like ColorKeep generic Smart-worker HD/UHD performance driver."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
GEOMETRIES = {"hd": (1920, 1080), "uhd": (3840, 2160)}


def probe_source(width: int, height: int) -> str:
    return f'''#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "{SOURCE}"

template<class P, class F>
static bool run_case(const char *name, short depth, A_long count, F worker) {{
    constexpr A_long W={width}, H={height};
    const size_t input_rb=(size_t)W*sizeof(P)+64;
    const size_t output_rb=(size_t)W*sizeof(P)+16;
    std::vector<P> input_store((input_rb*H+sizeof(P)-1)/sizeof(P));
    std::vector<P> output_store((output_rb*H+sizeof(P)-1)/sizeof(P));
    auto *input=reinterpret_cast<unsigned char*>(input_store.data());
    auto *output=reinterpret_cast<unsigned char*>(output_store.data());
    std::memset(input,0x31,input_rb*H); std::memset(output,0xa5,output_rb*H);
    ColorKeepInfo info={{}}; info.count=count;
    for(A_long i=0;i<count;i++)
        info.colors[i]=PF_PixelFloat{{1.0f,(i+1)/101.0f,(i+2)/103.0f,(i+3)/107.0f}};
    const auto started=std::chrono::steady_clock::now();
    for(A_long y=0;y<H;y++) for(A_long x=0;x<W;x++)
        worker(&info,x,y,reinterpret_cast<P*>(input+y*input_rb+x*sizeof(P)),
               reinterpret_cast<P*>(output+y*output_rb+x*sizeof(P)));
    const auto elapsed=std::chrono::duration<double,std::milli>(
        std::chrono::steady_clock::now()-started).count();
    bool padding=true;
    for(A_long y=0;y<H;y++) for(size_t x=(size_t)W*sizeof(P);x<output_rb;x++)
        padding &= output[y*output_rb+x]==0xa5;
    std::printf("GENERIC %s depth=%d %ldx%ld legacy=0 ok=%d ms=%.3f count=%ld\\n",
                name,(int)depth,(long)W,(long)H,padding?1:0,elapsed,(long)count);
    return padding;
}}

int main() {{
    bool ok=true;
    for(A_long count:{{1,13,100}}) {{
        char name[64]; std::snprintf(name,sizeof(name),"smart_pf8_count%ld",(long)count);
        ok &= run_case<PF_Pixel8>(name,8,count,ColorKeep8Func);
        std::snprintf(name,sizeof(name),"smart_pf16_count%ld",(long)count);
        ok &= run_case<PF_Pixel16>(name,16,count,ColorKeep16Func);
        std::snprintf(name,sizeof(name),"smart_pf32_count%ld",(long)count);
        ok &= run_case<PF_PixelFloat>(name,32,count,ColorKeepFloatFunc);
    }}
    return ok?0:1;
}}
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", choices=GEOMETRIES, required=True)
    args = parser.parse_args()
    width, height = GEOMETRIES[args.geometry]
    with tempfile.TemporaryDirectory(prefix="colorkeep-perf-") as raw:
        directory = Path(raw)
        cpp, executable = directory / "probe.cpp", directory / "probe"
        cpp.write_text(probe_source(width, height), encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-DNDEBUG", "-arch", "arm64",
            "-isysroot", sdk, "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp),
            str(ROOT / "mac/ColorKeep/ColorKeep_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"), "-framework", "Cocoa",
            "-o", str(executable),
        ], cwd=ROOT, text=True, capture_output=True)
        if build.returncode:
            print(build.stderr, end="", file=__import__("sys").stderr)
            return build.returncode
        run = subprocess.run([str(executable)], cwd=ROOT, text=True, capture_output=True)
    print(run.stdout, end="")
    if run.stderr:
        print(run.stderr, end="", file=__import__("sys").stderr)
    cases = []
    for line in run.stdout.splitlines():
        if not line.startswith("GENERIC "):
            continue
        words = line.split()
        cases.append({
            "case": words[1], "depth": int(words[2].split("=")[1]),
            "dimensions": [int(value) for value in words[3].split("x")],
            "status": "passed" if "ok=1" in words else "failed",
            "milliseconds": float(words[6].split("=")[1]),
            "count": int(words[7].split("=")[1]),
        })
    print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
