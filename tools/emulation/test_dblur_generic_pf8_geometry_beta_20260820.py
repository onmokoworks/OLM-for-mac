#!/usr/bin/env python3
"""Exercise the source-independent PF8 front-only beta lane at real geometries."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("C++ compiler not found")
    with tempfile.TemporaryDirectory(prefix="dblur_generic_pf8_") as tmp:
        source = Path(tmp) / "probe.cpp"
        binary = Path(tmp) / "probe"
        production = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
        source.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"
#include <cstring>
#include <cstdint>
#include <vector>

static int run(int width, int height, double angle, int strength, double scale,
               bool expect_success, bool check_determinism) {{
    const int input_rowbytes = width * 4 + 5;
    const int output_rowbytes = width * 4 + 17;
    std::vector<std::uint8_t> input((size_t)input_rowbytes * height, 0xa5);
    std::vector<std::uint8_t> output((size_t)output_rowbytes * height, 0xee);
    for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {{
        std::uint8_t *p = input.data() + (size_t)y * input_rowbytes + x * 4;
        p[0] = 255; p[1] = (x * 13 + y * 7) & 255;
        p[2] = (x * 3 + y * 17) & 255; p[3] = (x * 19 + y * 5) & 255;
    }}
    PF_EffectWorld in{{}}, out{{}};
    in.data = (PF_PixelPtr)input.data(); in.rowbytes = input_rowbytes;
    in.width = width; in.height = height; in.extent_hint = {{0, 0, width, height}};
    out.data = (PF_PixelPtr)output.data(); out.rowbytes = output_rowbytes;
    out.width = width; out.height = height; out.extent_hint = {{0, 0, width, height}};
    OLMDirectionalBlurInfo info{{}}; info.angle_deg = angle; info.brightness_gain = 1.0;
    info.front_strength = strength; info.render_scale_x = info.render_scale_y = scale;
    int exact = 0;
    const PF_Err err = OLMDirectionalBlurTestRenderWorld(&in, &out, &info, 8, &exact);
    if (!expect_success) return err == PF_Err_BAD_CALLBACK_PARAM ? 0 : 9;
    if (err != PF_Err_NONE || exact != 1) return 10;
    bool changed = false;
    for (int y = 0; y < height; ++y) {{
        for (int x = 0; x < width; ++x) {{
            const std::uint8_t expected[4] = {{255,
                static_cast<std::uint8_t>((x * 13 + y * 7) & 255),
                static_cast<std::uint8_t>((x * 3 + y * 17) & 255),
                static_cast<std::uint8_t>((x * 19 + y * 5) & 255)}};
            if (std::memcmp(input.data() + (size_t)y * input_rowbytes + x * 4,
                            expected, sizeof(expected))) return 11;
        }}
        for (int x = width * 4; x < input_rowbytes; ++x)
            if (input[(size_t)y * input_rowbytes + x] != 0xa5) return 12;
        for (int x = 0; x < width * 4; ++x)
            changed |= output[(size_t)y * output_rowbytes + x] != 0xee;
        for (int x = width * 4; x < output_rowbytes; ++x)
            if (output[(size_t)y * output_rowbytes + x] != 0xee) return 13;
    }}
    if (!changed) return 14;
    if (check_determinism) {{
        std::vector<std::uint8_t> second((size_t)output_rowbytes * height, 0xee);
        out.data = (PF_PixelPtr)second.data(); exact = 0;
        if (OLMDirectionalBlurTestRenderWorld(&in, &out, &info, 8, &exact) != PF_Err_NONE ||
            exact != 1 || second != output) return 15;
    }}
    return 0;
}}
int main() {{
    if (run(1, 1, 0.0, 1, 1.0, true, true)) return 1;
    if (run(1, 97, -179.5, 8, 0.5, true, true)) return 2;
    if (run(101, 1, 89.9, 2, 1.0, true, true)) return 3;
    if (run(37, 23, 45.0, 8, 1.0, true, true)) return 4;
    if (run(1280, 720, -45.0, 2, 0.5, true, false)) return 5;
    if (run(1920, 1080, 0.0, 2, 1.0, true, false)) return 6;
    if (run(3840, 2160, 0.0, 2, 1.0, true, false)) return 7;
    return 0;
}}
''', encoding="utf-8")
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], check=True, capture_output=True, text=True).stdout.strip()
        command = [compiler, "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                   "-ffunction-sections", "-fdata-sections", "-Wno-unused-function",
                   "-Wno-unused-parameter",
                   "-DOLM_DBLUR_TEST_SEAM=1", "-isysroot", sdk,
                   "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                   "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                   str(source), str(ROOT / "core/dblur_frontonly.cpp"),
                   str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
                   str(ROOT / "core/dblur_field.cpp"), "-Wl,-dead_strip",
                   "-framework", "Cocoa", "-o", str(binary)]
        if os.environ.get("OLM_DBLUR_SANITIZE") == "1":
            command[1:1] = ["-O1", "-g", "-fsanitize=address,undefined",
                            "-fno-omit-frame-pointer"]
        subprocess.run(command, cwd=ROOT, check=True)
        subprocess.run([str(binary)], cwd=ROOT, check=True, timeout=120)
    print("ok: PF8 generic 1D/odd/HD/4K, independent strides, boundaries, determinism")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
