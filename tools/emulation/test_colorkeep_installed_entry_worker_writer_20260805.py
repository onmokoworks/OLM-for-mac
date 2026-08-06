#!/usr/bin/env python3
"""Bind the installed ColorKeep hash to its public entry and PF16 writer."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin/Contents/MacOS/ColorKeep"
ACTUAL_RAW = ROOT / "refs/conformance/colorkeep_pf16_extended_range_actual_aex_20260805.argb16"
REPORT = ROOT / "refs/conformance/colorkeep_installed_entry_worker_writer_20260805.json"
EXPECTED_HASH = "ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce"

COLORS = (
    (1.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.5, 0.25, 0.75, 1.0),
)
PIXELS = (
    (32768, 32768, 32768, 32768), (32769, 32768, 32768, 32768),
    (32768, 32769, 32768, 32768), (32768, 32768, 32769, 32768),
    (32768, 32768, 32768, 32769), (65535, 65535, 65535, 65535),
    (0, 65535, 32769, 49152), (16384, 8192, 24576, 32768),
)


def symbol_offset(architecture: str, pattern: str) -> tuple[int, str]:
    run = subprocess.run(["nm", "-arch", architecture, str(INSTALLED)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    matches = []
    for line in run.stdout.splitlines():
        if pattern in line:
            match = re.match(r"([0-9a-fA-F]+)\s+[A-Za-z]\s+(.+)", line.strip())
            if match:
                matches.append((int(match.group(1), 16), match.group(2)))
    assert len(matches) == 1, matches
    return matches[0]


def installed_frame(worker_offset: int) -> tuple[bytes, bytes]:
    colors = ",".join(f"{{{a}f,{r}f,{g}f,{b}f}}" for a, r, g, b in COLORS)
    pixels = ",".join("{" + ",".join(str(value) for value in pixel) + "}" for pixel in PIXELS)
    path = str(INSTALLED).replace('"', '\\"')
    code = f'''#include <cstdio>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include "mac/ColorKeep/ColorKeep.h"
using Main=PF_Err(*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
using Worker=PF_Err(*)(void*,A_long,A_long,PF_Pixel16*,PF_Pixel16*);
int main(){{void*h=dlopen("{path}",RTLD_NOW|RTLD_LOCAL);if(!h)return 10;auto mainfn=(Main)dlsym(h,"EffectMain");if(!mainfn)return 11;
Dl_info di{{}};if(!dladdr((void*)mainfn,&di)||!di.dli_fbase)return 12;PF_InData in{{}};PF_OutData out{{}};if(mainfn(PF_Cmd_GLOBAL_SETUP,&in,&out,nullptr,nullptr,nullptr))return 13;
uint32_t entry[3]={{uint32_t(out.my_version),uint32_t(out.out_flags),uint32_t(out.out_flags2)}};std::fwrite(entry,1,sizeof(entry),stderr);
auto worker=(Worker)((uintptr_t)di.dli_fbase+0x{worker_offset:x});ColorKeepInfo info{{}};info.count=3;PF_PixelFloat colors[]={{{colors}}};std::memcpy(info.colors,colors,sizeof(colors));
PF_Pixel16 pixels[]={{{pixels}}};unsigned char output[120];std::memset(output,0xee,sizeof(output));for(int i=0;i<12;i++){{int y=i/4,x=i%4;PF_Pixel16 source=pixels[i%8];if(worker(&info,x,y,&source,(PF_Pixel16*)(output+y*40+x*8)))return 14;}}std::fwrite(output,1,sizeof(output),stdout);return 0;}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep_installed_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(code, encoding="utf-8")
        build = subprocess.run([
            "xcrun", "clang++", "-std=c++17", "-O2", "-D__MACH__", "-Wno-pragma-pack",
            "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp), "-o", str(exe),
        ], cwd=ROOT, capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout, run.stderr


def main() -> int:
    digest = hashlib.sha256(INSTALLED.read_bytes()).hexdigest()
    assert digest == EXPECTED_HASH
    architecture = platform.machine()
    assert architecture in ("arm64", "x86_64")
    effect_offset, effect_symbol = symbol_offset(architecture, "_EffectMain")
    worker_offset, worker_symbol = symbol_offset(architecture, "ColorKeep16Func")
    observed, entry_payload = installed_frame(worker_offset)
    expected = ACTUAL_RAW.read_bytes()
    assert observed == expected
    assert struct.unpack("<III", entry_payload) == (0x00080800, 0x02000040, 0x08001400)
    report = {
        "status": "installed_hash_bound_exact",
        "installed_binary": str(INSTALLED),
        "installed_binary_sha256": digest,
        "installed_architectures": ["x86_64", "arm64"],
        "executed_architecture": architecture,
        "loading": "dlopen(RTLD_NOW|RTLD_LOCAL) of the installed MediaCore Mach-O succeeded",
        "public_entry": {"symbol": effect_symbol, "image_offset": f"0x{effect_offset:x}", "resolution": "dlsym(EffectMain)", "executed_command": "PF_Cmd_GLOBAL_SETUP", "payload_hex": entry_payload.hex()},
        "worker_writer": {"symbol": worker_symbol, "image_offset": f"0x{worker_offset:x}", "resolution": "local Mach-O symbol offset plus dladdr image base", "fixture": "PF16 extended-range 4x3, rowbytes40, padding8", "observed_sha256": hashlib.sha256(observed).hexdigest()},
        "actual_aex_fixture": str(ACTUAL_RAW.relative_to(ROOT)),
        "actual_aex_fixture_sha256": hashlib.sha256(expected).hexdigest(),
        "raw_exact": True,
        "connection_closed": "The exact on-disk hash now has an executable public EffectMain identity and a bit-exact PF16 worker/writer result tied to an existing actual-AEX fixture; this no longer relies only on recompiling ColorKeep.cpp in a temporary harness.",
        "remaining_boundary": "The installed Smart/legacy host adapter was not invoked because doing so requires AE host suites. AE process loading and export remain intentionally unclaimed.",
        "not_proven": ["After Effects loading of this hash", "AE suite dispatch from EffectMain into the worker", "AE project render/export"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
