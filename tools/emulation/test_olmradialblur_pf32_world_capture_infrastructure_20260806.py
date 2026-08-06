#!/usr/bin/env python3
"""Hostless proof for diagnostic-only PF32 SmartRender world capture."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def compile_probe(cpp: Path, exe: Path) -> None:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
               "-ffunction-sections", "-fdata-sections", str(cpp), "-Wl,-dead_strip",
               "-framework", "Cocoa", "-o", str(exe)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise AssertionError(built.stderr)


def main() -> int:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradial-capture-test-") as td_raw:
        td = Path(td_raw)
        capture = td / "capture"
        capture.mkdir()
        diagnostic_cpp, diagnostic_exe = td / "diagnostic.cpp", td / "diagnostic"
        diagnostic_cpp.write_text(f'''#define OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE 1
#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <vector>
int main(){{constexpr int W=1920,H=1080,RB=W*16+16;
std::vector<unsigned char> input((size_t)RB*H),output((size_t)RB*H);
for(size_t n=0;n<input.size();++n)input[n]=(unsigned char)(n*17+3);
for(size_t n=0;n<output.size();++n)output[n]=(unsigned char)(n*29+11);
PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=RB;iw.width=W;iw.height=H;iw.extent_hint={{1,2,1918,1077}};
ow.data=(PF_PixelPtr)output.data();ow.rowbytes=RB;ow.width=W;ow.height=H;ow.extent_hint={{3,4,1916,1075}};
OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x=960;i.center_y=540;i.outer_strength=1717;i.outer_offset_mode=1;
i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_type=1;
if(CaptureDiagnosticPF32World("input",&iw,i,32)!=PF_Err_NONE)return 2;
if(CaptureDiagnosticPF32World("output",&ow,i,32)!=PF_Err_NONE)return 3;
if(CaptureDiagnosticPF32World("input",&iw,i,32)!=PF_Err_BAD_CALLBACK_PARAM)return 4;
return 0;}}''', encoding="utf-8")
        compile_probe(diagnostic_cpp, diagnostic_exe)
        environment = os.environ.copy()
        environment["OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR"] = str(capture)
        subprocess.run([str(diagnostic_exe)], cwd=ROOT, env=environment, check=True)
        rb = 1920 * 16 + 16
        size = rb * 1080
        expected_input = bytes(((n * 17 + 3) & 255) for n in range(size))
        expected_output = bytes(((n * 29 + 11) & 255) for n in range(size))
        assert (capture / "input.argb128.rows").read_bytes() == expected_input
        assert (capture / "output.argb128.rows").read_bytes() == expected_output
        input_meta = json.loads((capture / "input.json").read_text())
        output_meta = json.loads((capture / "output.json").read_text())
        assert input_meta == {"schema": "olmradialblur-pf32-world-capture/1", "stage": "input",
                              "pixel_format": "PF_PixelFormat_ARGB128", "channel_memory_order": "ARGB",
                              "row_storage": "full_positive_rowbytes_including_padding", "width": 1920,
                              "height": 1080, "rowbytes": rb, "extent_hint": [1, 2, 1918, 1077], "raw_bytes": size}
        assert output_meta["extent_hint"] == [3, 4, 1916, 1075] and output_meta["raw_bytes"] == size

        normal_dir = td / "normal_capture"
        normal_dir.mkdir()
        normal_cpp, normal_exe = td / "normal.cpp", td / "normal"
        normal_cpp.write_text(f'''#include "{source}"
int main(){{
#if defined(OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE)
return 2;
#else
return 0;
#endif
}}''', encoding="utf-8")
        compile_probe(normal_cpp, normal_exe)
        normal_env = os.environ.copy()
        normal_env["OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR"] = str(normal_dir)
        subprocess.run([str(normal_exe)], cwd=ROOT, env=normal_env, check=True)
        symbols = subprocess.check_output(["nm", str(normal_exe)], text=True, errors="replace")
        assert "CaptureDiagnosticPF32World" not in symbols
        assert list(normal_dir.iterdir()) == []
    print("PASS_OLMRADIALBLUR_PF32_WORLD_CAPTURE_INFRASTRUCTURE_20260806 pre=exact post=exact padding=exact normal=absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
