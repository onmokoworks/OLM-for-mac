#!/usr/bin/env python3
"""Source-execute the Mac OLMDirectionalBlur PF-world adapter boundary."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CORE = ROOT / "core"
WIDTH = HEIGHT = 16
ROWBYTES = 76
EXTENT = [2, 1, 14, 15]
PIXEL_BYTES = 4
INPUT_PAD = 0xA5
OUTPUT_PAD = 0xEE


def _compile_probe(directory: Path) -> tuple[Path, dict]:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    if not compiler:
        raise RuntimeError(f"fail closed: compiler not found: {compiler_name}")
    probe = directory / "dblur_mac_host_adapter_probe.cpp"
    executable = directory / "dblur_mac_host_adapter_probe"
    production = str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')
    probe.write_text(
        f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace {{
constexpr int kWidth = 16;
constexpr int kHeight = 16;
constexpr int kRowbytes = 76;
constexpr int kExtent[4] = {{2, 1, 14, 15}};
constexpr std::uint8_t kInputPad = 0xA5;
constexpr std::uint8_t kOutputPad = 0xEE;

std::uint8_t *pixel(std::array<std::uint8_t, kRowbytes * kHeight> &world, int x, int y) {{
    return world.data() + y * kRowbytes + x * 4;
}}
const std::uint8_t *pixel(const std::array<std::uint8_t, kRowbytes * kHeight> &world, int x, int y) {{
    return world.data() + y * kRowbytes + x * 4;
}}
void fill_input(std::array<std::uint8_t, kRowbytes * kHeight> &world) {{
    world.fill(kInputPad);
    for (int y = 0; y < kHeight; ++y) for (int x = 0; x < kWidth; ++x) {{
        std::uint8_t *p = pixel(world, x, y);
        p[0] = static_cast<std::uint8_t>((x * 17 + y * 3 + 11) & 255);
        p[1] = static_cast<std::uint8_t>((x * 5 + y * 19 + 37) & 255);
        p[2] = static_cast<std::uint8_t>((x * 23 + y * 7 + 71) & 255);
        p[3] = static_cast<std::uint8_t>(80 + ((x * 13 + y * 29) & 127));
    }}
}}
bool padding_is(const std::array<std::uint8_t, kRowbytes * kHeight> &world, std::uint8_t value) {{
    for (int y = 0; y < kHeight; ++y) for (int i = kWidth * 4; i < kRowbytes; ++i)
        if (world[static_cast<std::size_t>(y) * kRowbytes + i] != value) return false;
    return true;
}}
std::string sha(const std::array<std::uint8_t, kRowbytes * kHeight> &world) {{
    // The probe reports a stable digest without introducing a hashing dependency.
    std::uint64_t a = 1469598103934665603ULL;
    for (std::uint8_t byte : world) a = (a ^ byte) * 1099511628211ULL;
    char text[32]; std::snprintf(text, sizeof(text), "%016llx", static_cast<unsigned long long>(a));
    return text;
}}
}}

int main() {{
    std::array<std::uint8_t, kRowbytes * kHeight> input{{}};
    fill_input(input);
    std::array<std::uint8_t, kRowbytes * kHeight> input_before = input;
    PF_EffectWorld in{{}};
    in.data = reinterpret_cast<PF_PixelPtr>(input.data());
    in.rowbytes = kRowbytes; in.width = kWidth; in.height = kHeight;
    in.extent_hint = {{kExtent[0], kExtent[1], kExtent[2], kExtent[3]}};
    OLMDirectionalBlurInfo info{{}};
    info.brightness_gain = 1.0;
    info.front_strength = 48;
    info.front_alpha_fade = 0;
    info.render_scale_x = info.render_scale_y = 1.0;

    std::printf("{{\\"status\\":\\"ok\\",\\"cases\\":[");
    for (int case_index = 0; case_index < 2; ++case_index) {{
        const float angle = case_index == 0 ? 0.0f : 45.0f;
        info.angle_deg = angle;
        std::array<std::uint8_t, kWidth * kHeight * 4> source{{}};
        std::array<std::uint8_t, kWidth * kHeight * 4> expected{{}};
        for (int y = 0; y < kHeight; ++y) for (int x = 0; x < kWidth; ++x) {{
            const std::uint8_t *p = pixel(input, x, y);
            std::uint8_t *q = source.data() + (y * kWidth + x) * 4;
            q[0] = p[1]; q[1] = p[2]; q[2] = p[3]; q[3] = p[0];
        }}
        if (olm_dblur_frontonly_rgba8(source.data(), expected.data(), kWidth, kHeight,
                                       angle, 1.0f, 48, 0) != 0) return 11;
        std::array<std::uint8_t, kRowbytes * kHeight> output{{}};
        output.fill(kOutputPad);
        PF_EffectWorld out{{}};
        out.data = reinterpret_cast<PF_PixelPtr>(output.data());
        out.rowbytes = kRowbytes; out.width = kWidth; out.height = kHeight;
        out.extent_hint = {{kExtent[0], kExtent[1], kExtent[2], kExtent[3]}};
        int used_exact = 0;
        if (OLMDirectionalBlurTestRenderWorld(&in, &out, &info, 8, &used_exact) != PF_Err_NONE)
            return 12;
        bool pixels_match = true;
        for (int y = 0; y < kHeight; ++y) for (int x = 0; x < kWidth; ++x) {{
            const std::uint8_t *p = pixel(output, x, y);
            const std::uint8_t *q = expected.data() + (y * kWidth + x) * 4;
            pixels_match &= p[0] == q[3] && p[1] == q[0] && p[2] == q[1] && p[3] == q[2];
        }}
        if (used_exact != 1 || !pixels_match || input != input_before || !padding_is(input, kInputPad) || !padding_is(output, kOutputPad))
            return 20 + case_index;
        if (case_index) std::printf(",");
        std::printf("{{\\"angle\\":%.1f,\\"used_exact\\":%d,\\"pixels_match\\":true,\\"input_unchanged\\":true,\\"input_padding_unchanged\\":true,\\"output_padding_unchanged\\":true,\\"output_digest\\":\\"%s\\"}}", angle, used_exact, sha(output).c_str());
    }}
    std::printf("],\\"gates\\":[");
    struct Gate {{ const char *name; OLMDirectionalBlurInfo mutate; }};
    const Gate gates[] = {{
        {{"size_variation", []{{ OLMDirectionalBlurInfo x{{}}; x.size_variation = 1.0; return x; }}()}},
        {{"front_alpha_fade", []{{ OLMDirectionalBlurInfo x{{}}; x.front_alpha_fade = 1; return x; }}()}},
        {{"back_alpha_fade", []{{ OLMDirectionalBlurInfo x{{}}; x.back_alpha_fade = 1; return x; }}()}},
        {{"front_sharp_tail", []{{ OLMDirectionalBlurInfo x{{}}; x.front_sharp_tail = 1.0; return x; }}()}},
        {{"back_strength", []{{ OLMDirectionalBlurInfo x{{}}; x.back_strength = 1; return x; }}()}},
        {{"noise", []{{ OLMDirectionalBlurInfo x{{}}; x.noise_variation = 1.0; return x; }}()}},
        {{"downsample", []{{ OLMDirectionalBlurInfo x{{}}; x.render_scale_x = 0.5; return x; }}()}},
        {{"dimension_mismatch", []{{ OLMDirectionalBlurInfo x{{}}; return x; }}()}},
    }};
    for (std::size_t i = 0; i < sizeof(gates) / sizeof(gates[0]); ++i) {{
        OLMDirectionalBlurInfo gated = info;
        gated.size_variation = gates[i].mutate.size_variation;
        gated.front_alpha_fade = gates[i].mutate.front_alpha_fade;
        gated.back_alpha_fade = gates[i].mutate.back_alpha_fade;
        gated.front_sharp_tail = gates[i].mutate.front_sharp_tail;
        gated.back_strength = gates[i].mutate.back_strength;
        gated.noise_variation = gates[i].mutate.noise_variation;
        gated.render_scale_x = gates[i].mutate.render_scale_x ? gates[i].mutate.render_scale_x : 1.0;
        PF_EffectWorld gate_out{{}};
        gate_out.data = reinterpret_cast<PF_PixelPtr>(input.data());
        gate_out.rowbytes = kRowbytes; gate_out.width = kWidth; gate_out.height = kHeight;
        gate_out.extent_hint = {{kExtent[0], kExtent[1], kExtent[2], kExtent[3]}};
        if (std::strcmp(gates[i].name, "dimension_mismatch") == 0) gate_out.width = 15;
        int used_exact = 1;
        if (OLMDirectionalBlurTestRenderWorld(&in, &gate_out, &gated, 8, &used_exact) != PF_Err_NONE || used_exact != 0)
            return 40 + static_cast<int>(i);
        if (i) std::printf(",");
        std::printf("{{\\"name\\":\\"%s\\",\\"used_exact\\":0}}", gates[i].name);
    }}
    std::printf("]}}\\n");
    return 0;
}}
''', encoding="utf-8")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-ffunction-sections", "-fdata-sections", "-Wno-unused-function", "-Wno-unused-parameter",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
               str(probe), str(CORE / "dblur_frontonly.cpp"), str(CORE / "dblur_rotate.cpp"), str(CORE / "dblur_rowdriver.cpp"),
               "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"fail closed: source-included adapter probe did not compile\n{build.stderr}")
    return executable, {"compiler": compiler, "arch": "arm64", "flags": command[1:]}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_mac_host_adapter_") as name:
        executable, build = _compile_probe(Path(name))
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"adapter probe failed ({run.returncode}): {run.stderr}")
    report = json.loads(run.stdout)
    report["build"] = build
    report["world"] = {"dimensions": [WIDTH, HEIGHT], "rowbytes": ROWBYTES, "extent_hint": EXTENT,
                        "input_padding": hex(INPUT_PAD), "output_padding": hex(OUTPUT_PAD)}
    report["production_source"] = str(PRODUCTION.relative_to(ROOT))
    report["reference_path"] = "olm_dblur_frontonly_rgba8"
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
