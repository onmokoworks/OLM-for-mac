#!/usr/bin/env python3
"""Sanitized production-estimator and fail-closed dispatch boundaries."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cxx = shutil.which(os.environ.get("CXX", "clang++"))
    if not cxx:
        raise RuntimeError("C++ compiler not found")
    with tempfile.TemporaryDirectory(prefix="dblur_generic_budget_") as raw:
        directory = Path(raw)
        source = directory / "probe.cpp"
        executable = directory / "probe"
        source.write_text(
            f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{ROOT / 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'}"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>

namespace generic = olm::dblur::generic;

static int fail(int code, const char *label) {{
    std::fprintf(stderr, "failure %d: %s\\n", code, label);
    return code;
}}

static bool admitted(int w, int h, short depth, int strength,
                     std::size_t smart_bytes = 0,
                     OLMDirectionalBlurGenericEstimate *out = nullptr) {{
    OLMDirectionalBlurGenericEstimate local = {{}};
    return OLMDirectionalBlurTestGenericEstimate(
        w, h, depth, strength, smart_bytes, out ? out : &local) == 1;
}}

static bool admitted_sides(int w, int h, short depth, int front, int back,
                           std::size_t smart_bytes = 0,
                           OLMDirectionalBlurGenericEstimate *out = nullptr) {{
    OLMDirectionalBlurGenericEstimate local = {{}};
    return OLMDirectionalBlurTestGenericEstimateSides(
        w, h, depth, front, back, smart_bytes, out ? out : &local) == 1;
}}

static OLMDirectionalBlurInfo neutral() {{
    OLMDirectionalBlurInfo info = {{}};
    info.angle_deg = 37.25;
    info.brightness_gain = 0.75;
    info.front_strength = 2;
    info.render_scale_x = 1.0;
    info.render_scale_y = 1.0;
    return info;
}}

template <typename Pixel>
static bool rejected_world_is_atomic(short depth, int width, int height,
                                     int rowbytes, int front_strength,
                                     int back_strength = 0) {{
    // Rejected predicates must run before any pixel access.  A tiny guarded
    // payload is deliberate even when the declared geometry is large.
    std::vector<std::uint8_t> input(64, 0xa5), output(64, 0xee);
    const auto input_before = input;
    const auto output_before = output;
    PF_EffectWorld in = {{}}, out = {{}};
    in.data = reinterpret_cast<PF_PixelPtr>(input.data());
    out.data = reinterpret_cast<PF_PixelPtr>(output.data());
    in.width = out.width = width;
    in.height = out.height = height;
    in.rowbytes = out.rowbytes = rowbytes;
    OLMDirectionalBlurInfo info = neutral();
    info.front_strength = front_strength;
    info.back_strength = back_strength;
    int exact = -1;
    const PF_Err err = OLMDirectionalBlurTestRenderWorld(
        &in, &out, &info, depth, &exact);
    return err == PF_Err_BAD_CALLBACK_PARAM && input == input_before &&
           output == output_before;
}}

template <typename Pixel>
static bool invalid_ui_is_atomic(short depth) {{
    constexpr int width = 37, height = 23;
    const int rowbytes = width * static_cast<int>(sizeof(Pixel)) + 3;
    std::vector<std::uint8_t> input(static_cast<std::size_t>(rowbytes) * height, 0xa5);
    std::vector<std::uint8_t> output(static_cast<std::size_t>(rowbytes) * height, 0xee);
    const auto input_before = input;
    const auto output_before = output;
    PF_EffectWorld in = {{}}, out = {{}};
    in.data = reinterpret_cast<PF_PixelPtr>(input.data());
    out.data = reinterpret_cast<PF_PixelPtr>(output.data());
    in.width = out.width = width;
    in.height = out.height = height;
    in.rowbytes = out.rowbytes = rowbytes;
    OLMDirectionalBlurInfo info = neutral();
    info.front_strength = 4001;
    int exact = -1;
    const PF_Err err = OLMDirectionalBlurTestRenderWorld(
        &in, &out, &info, depth, &exact);
    return err == PF_Err_BAD_CALLBACK_PARAM && input == input_before &&
           output == output_before;
}}

int main() {{
    // Orientation-neutral source geometry and the area boundary.
    const int accepted[][2] = {{
        {{1, 1}}, {{720, 480}}, {{4096, 2160}}, {{2160, 4096}},
        {{4096, 1}}, {{1, 4096}}, {{821, 4019}}, {{2974, 2974}}
    }};
    for (const auto &g : accepted) if (!admitted(g[0], g[1], 8, 1))
        return fail(1, "supported geometry rejected");
    const int rejected[][2] = {{
        {{0, 1080}}, {{-1, 1}}, {{4097, 1}}, {{1, 4097}},
        {{4096, 2161}}, {{2161, 4096}}, {{2975, 2975}}, {{3000, 3000}}
    }};
    for (const auto &g : rejected) if (admitted(g[0], g[1], 8, 1))
        return fail(2, "unsupported geometry admitted");

    generic::WorkGeometry work = {{}};
    if (!generic::ComputeWorkGeometry(3611, 2029, &work) ||
        work.width != 4147 || work.height != 4147)
        return fail(3, "float diagonal rounding sentinel 3611x2029");
    if (!generic::ComputeWorkGeometry(821, 4019, &work) ||
        work.width != 4107 || work.height != 4107)
        return fail(4, "float diagonal rounding sentinel 821x4019");

    // The work cap retains the full Strength UI at SD, while production 4K
    // boundaries follow the edge-clamped rowdriver estimate.
    OLMDirectionalBlurGenericEstimate estimate = {{}};
    if (!admitted(720, 480, 32, 4000, 0, &estimate) ||
        estimate.operation_units != 331884140ull)
        return fail(5, "SD full Strength range");
    if (!admitted(4096, 2160, 32, 9, 0, &estimate) ||
        estimate.operation_units != 343379400ull ||
        admitted(4096, 2160, 32, 10))
        return fail(6, "DCI 4K operation boundary");
    if (!admitted(3840, 2160, 32, 11, 0, &estimate) ||
        estimate.operation_units != 349461832ull ||
        admitted(3840, 2160, 32, 12))
        return fail(7, "UHD operation boundary");

    // Dual-side admission adds both scatter loops while sharing the fixed
    // passes and workspace.  These are exact production-estimator borders.
    if (!admitted_sides(720, 480, 32, 272, 272, 0, &estimate) ||
        estimate.operation_units != 349930728ull ||
        admitted_sides(720, 480, 32, 273, 273))
        return fail(71, "SD dual operation boundary");
    if (!admitted_sides(4096, 2160, 32, 5, 5, 0, &estimate) ||
        estimate.operation_units != 343453544ull ||
        estimate.weight_bytes != 48ull ||
        admitted_sides(4096, 2160, 32, 6, 6))
        return fail(72, "DCI 4K dual operation boundary");
    if (!admitted_sides(3840, 2160, 32, 6, 6, 0, &estimate) ||
        estimate.operation_units != 349572032ull ||
        admitted_sides(3840, 2160, 32, 7, 7))
        return fail(73, "UHD dual operation boundary");
    if (!admitted_sides(3840, 2160, 32, 2, 8, 0, &estimate) ||
        estimate.operation_units != 310724328ull)
        return fail(74, "asymmetric dual operation sum");

    // Per-depth wrapper accounting and exact per-render Smart byte boundary.
    std::uint64_t previous_wrapper = 0;
    for (short depth : {{8, 16, 32}}) {{
        OLMDirectionalBlurGenericEstimate classic = {{}};
        if (!admitted(4096, 2160, depth, 2, 0, &classic) ||
            classic.work_width != 4634 || classic.work_height != 4634 ||
            classic.work_pixels != 21473956ull ||
            classic.core_workspace_bytes != 1202541536ull ||
            classic.weight_bytes != 16ull)
            return fail(8, "classic allocation breakdown");
        if (previous_wrapper && classic.wrapper_bytes != previous_wrapper * 2)
            return fail(9, "per-depth wrapper multiplier");
        previous_wrapper = classic.wrapper_bytes;
        const std::size_t remaining = static_cast<std::size_t>(
            generic::kPluginOwnedLiveLimitBytes - classic.plugin_owned_live_bytes);
        OLMDirectionalBlurGenericEstimate at_limit = {{}};
        if (!admitted(4096, 2160, depth, 2, remaining, &at_limit) ||
            at_limit.plugin_owned_live_bytes != generic::kPluginOwnedLiveLimitBytes ||
            admitted(4096, 2160, depth, 2, remaining + 1))
            return fail(10, "Smart allocation byte boundary");
        const std::size_t tight = static_cast<std::size_t>(4096) * 2160 * (depth / 2);
        OLMDirectionalBlurGenericEstimate landscape = {{}}, portrait = {{}};
        if (!admitted(4096, 2160, depth, 2, tight, &landscape) ||
            !admitted(2160, 4096, depth, 2, tight, &portrait) ||
            landscape.plugin_owned_live_bytes != portrait.plugin_owned_live_bytes)
            return fail(11, "Smart orientation/tight stage");
    }}

    // UI and float-narrowing bounds use the same parameter helper as dispatch.
    OLMDirectionalBlurInfo info = neutral();
    int effective = 0;
    info.angle_deg = -32768.0;
    info.brightness_gain = 0.0;
    info.front_strength = 4000;
    if (!OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective) ||
        effective != 4000)
        return fail(12, "lower angle/gain and upper Strength bounds");
    info.angle_deg = 32767.9999847412109375;
    info.brightness_gain = 10.0;
    if (!OLMDirectionalBlurTestGenericEffectiveStrength(&info, 32, &effective))
        return fail(13, "upper angle/gain bounds");
    const double invalid_values[] = {{
        std::numeric_limits<double>::infinity(),
        -std::numeric_limits<double>::infinity(),
        std::numeric_limits<double>::quiet_NaN(), 32768.0
    }};
    for (double value : invalid_values) {{
        info = neutral(); info.angle_deg = value;
        if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective))
            return fail(14, "invalid angle admitted");
    }}
    info = neutral(); info.brightness_gain = 10.0001;
    if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective))
        return fail(15, "invalid gain admitted");
    info = neutral(); info.front_strength = -1;
    if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective))
        return fail(15, "negative Strength admitted");
    info = neutral(); info.render_scale_x = 1.0001;
    if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective))
        return fail(16, "upscale admitted");
    info = neutral(); info.front_strength = 1; info.render_scale_x = 0.5;
    if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective))
        return fail(17, "zero effective Strength admitted");
    info = neutral(); info.render_scale_x = 0.5;
    if (OLMDirectionalBlurTestGenericEffectiveStrength(&info, 16, &effective))
        return fail(18, "deep downsample admitted");
    int effective_front = 0, effective_back = 0;
    info = neutral(); info.front_strength = 8; info.back_strength = 4;
    info.render_scale_x = 0.5; info.render_scale_y = 0.5;
    if (!OLMDirectionalBlurTestGenericEffectiveStrengths(
            &info, 8, &effective_front, &effective_back) ||
        effective_front != 4 || effective_back != 2)
        return fail(181, "dual PF8 projected strengths");
    info.front_strength = 1;
    if (OLMDirectionalBlurTestGenericEffectiveStrengths(
            &info, 8, &effective_front, &effective_back))
        return fail(182, "dual PF8 zero projected side admitted");
    info = neutral(); info.front_strength = 2; info.back_strength = -1;
    if (OLMDirectionalBlurTestGenericEffectiveStrengths(
            &info, 32, &effective_front, &effective_back))
        return fail(183, "negative dual side admitted");

    // Real production dispatcher: operation/geometry/UI rejection is atomic
    // for every depth and cannot fall through to a legacy renderer.
    if (!rejected_world_is_atomic<PF_Pixel8>(8, 4096, 2160, 4096 * 4, 10) ||
        !rejected_world_is_atomic<PF_Pixel16>(16, 4096, 2160, 4096 * 8, 10) ||
        !rejected_world_is_atomic<PF_PixelFloat>(32, 4096, 2160, 4096 * 16, 10))
        return fail(19, "operation reject output atomicity");
    if (!rejected_world_is_atomic<PF_Pixel8>(8, 4096, 2160, 4096 * 4, 6, 6) ||
        !rejected_world_is_atomic<PF_Pixel16>(16, 4096, 2160, 4096 * 8, 6, 6) ||
        !rejected_world_is_atomic<PF_PixelFloat>(32, 4096, 2160, 4096 * 16, 6, 6))
        return fail(191, "dual operation reject output atomicity");
    if (!rejected_world_is_atomic<PF_Pixel8>(8, 4097, 1, 4097 * 4, 2) ||
        !rejected_world_is_atomic<PF_Pixel16>(16, 4097, 1, 4097 * 8, 2) ||
        !rejected_world_is_atomic<PF_PixelFloat>(32, 4097, 1, 4097 * 16, 2))
        return fail(20, "geometry reject output atomicity");
    if (!invalid_ui_is_atomic<PF_Pixel8>(8) ||
        !invalid_ui_is_atomic<PF_Pixel16>(16) ||
        !invalid_ui_is_atomic<PF_PixelFloat>(32))
        return fail(21, "UI reject output atomicity");

    std::printf(
        "PASS_DBLUR_GENERIC_BUDGET geometry=4096x2160/portrait "
        "operation=350000000 memory=3221225472 per-render\\n");
    return 0;
}}
''',
            encoding="utf-8",
        )
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], check=True, capture_output=True, text=True
        ).stdout.strip()
        command = [
            cxx, "-std=c++17", "-O1", "-g", "-fno-fast-math", "-ffp-contract=off",
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-isysroot", sdk,
            "-ffunction-sections", "-fdata-sections",
            "-Wno-unused-function", "-Wno-unused-parameter", "-Wno-pragma-pack",
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(source), str(ROOT / "core/dblur_frontonly.cpp"),
            str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
            str(ROOT / "core/dblur_field.cpp"), "-Wl,-dead_strip",
            "-framework", "Cocoa", "-o", str(executable),
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        environment = os.environ.copy()
        environment.setdefault("ASAN_OPTIONS", "halt_on_error=1:detect_leaks=0")
        environment.setdefault("UBSAN_OPTIONS", "halt_on_error=1:print_stacktrace=1")
        subprocess.run([str(executable)], cwd=ROOT, env=environment, check=True, timeout=60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
