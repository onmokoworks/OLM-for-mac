#!/usr/bin/env python3
"""Bind the installed ColorKeep PF8 worker to the 4x3 host/actual-AEX fixture."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin/Contents/MacOS/ColorKeep"
EXPECTED_INSTALLED_SHA256 = "ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce"
INPUT = ROOT / "refs/mac_validation_fixtures/colorkeep_pf8_20260805/colorkeep_pf8_input.png"
EXPECTED = ROOT / "refs/mac_validation_fixtures/colorkeep_pf8_20260805/colorkeep_pf8_expected_actual_aex.argb8"
EXPECTED_AEX_SHA256 = "29f9080b90d73404359c07439727d3e85b32ea185fe7fde4edd669310ed8a05b"
REPORT = ROOT / "refs/conformance/colorkeep_installed_pf8_host_fixture_20260806.json"
KEYS_RGBA8 = ((255,0,0,255),(0,255,0,255),(0,0,255,255),(128,128,128,255),(255,255,0,255))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbol_offset(architecture: str) -> tuple[int, str]:
    run = subprocess.run(["nm", "-arch", architecture, str(INSTALLED)], capture_output=True, text=True, check=True)
    matches=[]
    for line in run.stdout.splitlines():
        if "ColorKeep8Func" in line:
            match=re.match(r"([0-9a-fA-F]+)\s+[A-Za-z]\s+(.+)",line.strip())
            if match: matches.append((int(match.group(1),16),match.group(2)))
    assert len(matches)==1,matches
    return matches[0]


def execute_installed_worker(worker_offset: int) -> bytes:
    rgba=list(Image.open(INPUT).convert("RGBA").get_flattened_data())
    argb=[(a,r,g,b) for r,g,b,a in rgba]
    pixels=",".join("{"+",".join(str(v) for v in pixel)+"}" for pixel in argb)
    colors=",".join("{"+",".join(f"{v / 255.0:.17f}f" for v in (a,r,g,b))+"}" for r,g,b,a in KEYS_RGBA8)
    binary=str(INSTALLED).replace('"','\\"')
    code=f'''#include <cstdio>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include "mac/ColorKeep/ColorKeep.h"
using Main=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
using Worker=PF_Err(*)(void*,A_long,A_long,PF_Pixel8*,PF_Pixel8*);
int main(){{void*h=dlopen("{binary}",RTLD_NOW|RTLD_LOCAL);if(!h)return 10;auto mainfn=(Main)dlsym(h,"EffectMain");if(!mainfn)return 11;Dl_info di{{}};if(!dladdr((void*)mainfn,&di)||!di.dli_fbase)return 12;
ColorKeepInfo info{{}};info.count=5;PF_PixelFloat colors[]={{{colors}}};std::memcpy(info.colors,colors,sizeof(colors));PF_Pixel8 input[]={{{pixels}}};PF_Pixel8 output[12];std::memset(output,0xa5,sizeof(output));auto worker=(Worker)((uintptr_t)di.dli_fbase+0x{worker_offset:x});for(int i=0;i<12;i++)if(worker(&info,i%4,i/4,&input[i],&output[i]))return 13;std::fwrite(output,1,sizeof(output),stdout);return 0;}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_installed_pf8_") as raw:
        directory=Path(raw); cpp=directory/"probe.cpp"; exe=directory/"probe"; cpp.write_text(code,encoding="utf-8")
        build=subprocess.run(["xcrun","clang++","-std=c++17","-O2","-D__MACH__","-Wno-pragma-pack","-I.","-IHeaders","-IHeaders/SP","-IUtil","-IResources",str(cpp),"-o",str(exe)],cwd=ROOT,capture_output=True,text=True)
        assert build.returncode==0,build.stderr
        run=subprocess.run([str(exe)],cwd=ROOT,capture_output=True)
        assert run.returncode==0,run.stderr.decode(errors="replace")
        return run.stdout


def main() -> int:
    assert sha256(INSTALLED)==EXPECTED_INSTALLED_SHA256
    assert sha256(EXPECTED)==EXPECTED_AEX_SHA256
    architecture=platform.machine(); assert architecture in ("arm64","x86_64")
    offset,symbol=symbol_offset(architecture)
    observed=execute_installed_worker(offset); expected=EXPECTED.read_bytes()
    assert len(observed)==48 and observed==expected
    report={
        "kind":"colorkeep_installed_pf8_host_fixture",
        "status":"installed_hash_bound_raw_argb8_exact",
        "installed_binary":str(INSTALLED),
        "installed_binary_sha256":EXPECTED_INSTALLED_SHA256,
        "executed_architecture":architecture,
        "worker_symbol":symbol,
        "worker_image_offset":f"0x{offset:x}",
        "fixture":{"dimensions":[4,3],"enabled_color_count":5,"input":str(INPUT.relative_to(ROOT)),"actual_aex_raw":str(EXPECTED.relative_to(ROOT)),"actual_aex_raw_sha256":EXPECTED_AEX_SHA256},
        "observed_raw_argb8_sha256":hashlib.sha256(observed).hexdigest(),
        "byte_count":len(observed),
        "mismatched_bytes":0,
        "hidden_rgb_at_alpha_zero_compared":True,
        "evidence_boundary":"Direct execution of the PF8 worker inside the exact installed Mach-O; AE suite dispatch/export is proven separately by the host runner."
    }
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
