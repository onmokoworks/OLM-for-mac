#!/usr/bin/env python3
"""Execute the installed ToonDilate SmartRender entry at PF8/PF16/PF32."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin"
BINARY = BUNDLE / "Contents/MacOS/OLMToonDilate"
EXPECTED_SHA256 = "7d2c24d8ad0f7436ee7035e0d926a2abaac1a74bc9305a4223f76230c1fc5537"
REPORT = ROOT / "refs/conformance/olmtoondilate_installed_dynamic_all_depths_20260806.json"


PROBE = r'''
#include <dlfcn.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include "AE_Effect.h"

static PF_EffectWorld *g_input, *g_output;
static double g_radius = 1.0;
static int g_pre, g_pixels, g_output_hits, g_checkin, g_param;

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex, A_long, A_long, A_u_long, PF_ParamDef *p) {
    std::memset(p, 0, sizeof(*p)); p->u.fs_d.value = g_radius; ++g_param; return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) { return PF_Err_NONE; }
static PF_Err pre_checkout(PF_ProgPtr, PF_ParamIndex, A_long, const PF_RenderRequest *, A_long, A_long, A_u_long, PF_CheckoutResult *r) {
    std::memset(r, 0, sizeof(*r)); r->result_rect = {17, 23, 20, 25}; r->max_result_rect = r->result_rect;
    r->ref_width = 3; r->ref_height = 2; ++g_pre; return PF_Err_NONE;
}
static PF_Err pixels(PF_ProgPtr, A_long, PF_EffectWorld **w) { *w = g_input; ++g_pixels; return PF_Err_NONE; }
static PF_Err output(PF_ProgPtr, PF_EffectWorld **w) { *w = g_output; ++g_output_hits; return PF_Err_NONE; }
static PF_Err checkin(PF_ProgPtr, A_long) { ++g_checkin; return PF_Err_NONE; }

template <typename Pixel> static bool run_depth(PF_Err (*effect)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *), short depth) {
    constexpr int W = 3, H = 2, PAD = 8;
    const int rowbytes = W * static_cast<int>(sizeof(Pixel)) + PAD;
    unsigned char input_bytes[H * (W * sizeof(Pixel) + PAD)];
    unsigned char output_bytes[H * (W * sizeof(Pixel) + PAD)];
    std::memset(input_bytes, 0, sizeof(input_bytes)); std::memset(output_bytes, 0xEE, sizeof(output_bytes));
    Pixel seed{};
    if constexpr (sizeof(Pixel) == 4) seed = Pixel{255, 10, 20, 30};
    else if constexpr (sizeof(Pixel) == 8) seed = Pixel{32768, 1001, 2002, 3003};
    else seed = Pixel{1.0f, 0.125f, 0.25f, 0.5f};
    for (int y = 0; y < H; ++y) {
        std::memcpy(input_bytes + y * rowbytes + sizeof(Pixel), &seed, sizeof(seed));
        std::memset(input_bytes + y * rowbytes + W * sizeof(Pixel), 0xA5, PAD);
    }
    PF_EffectWorld input{}, destination{};
    input.data = reinterpret_cast<PF_PixelPtr>(input_bytes); input.rowbytes = rowbytes; input.width = W; input.height = H;
    input.extent_hint = {101, 201, 104, 203};
    destination.data = reinterpret_cast<PF_PixelPtr>(output_bytes); destination.rowbytes = rowbytes; destination.width = W; destination.height = H;
    destination.extent_hint = {301, 401, 304, 403};
    g_input = &input; g_output = &destination; g_pre = g_pixels = g_output_hits = g_checkin = g_param = 0;
    PF_InData in{}; PF_OutData out{}; in.inter.checkout_param = checkout_param; in.inter.checkin_param = checkin_param;
    PF_PreRenderInput pre_input{}; PF_PreRenderOutput pre_output{}; PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer = pre_checkout;
    PF_PreRenderExtra pre{&pre_input, &pre_output, &pre_cb};
    const PF_Err pre_err = effect(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre);
    PF_SmartRenderInput smart_input{}; smart_input.bitdepth = depth; smart_input.pre_render_data = pre_output.pre_render_data;
    PF_SmartRenderCallbacks smart_cb{}; smart_cb.checkout_layer_pixels = pixels; smart_cb.checkout_output = output; smart_cb.checkin_layer_pixels = checkin;
    PF_SmartRenderExtra smart{&smart_input, &smart_cb};
    const PF_Err render_err = effect(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &smart);
    bool exact = pre_err == PF_Err_NONE && render_err == PF_Err_NONE && g_pre == 1 && g_pixels == 1 && g_output_hits == 1 && g_checkin == 1 && g_param == 1;
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) exact = exact && std::memcmp(output_bytes + y * rowbytes + x * sizeof(Pixel), &seed, sizeof(seed)) == 0;
        for (int i = W * sizeof(Pixel); i < rowbytes; ++i) exact = exact && output_bytes[y * rowbytes + i] == 0xEE;
    }
    if (pre_output.delete_pre_render_data_func) pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
    return exact;
}

int main(int argc, char **argv) {
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL); if (!handle) { std::fprintf(stderr, "%s", dlerror()); return 2; }
    using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);
    auto effect = reinterpret_cast<Effect>(dlsym(handle, "EffectMain")); if (!effect) return 3;
    const bool pf8 = run_depth<PF_Pixel8>(effect, 8), pf16 = run_depth<PF_Pixel16>(effect, 16), pf32 = run_depth<PF_PixelFloat>(effect, 32);
    std::printf("{\"PF8\":%s,\"PF16\":%s,\"PF32\":%s}\n", pf8 ? "true" : "false", pf16 ? "true" : "false", pf32 ? "true" : "false");
    dlclose(handle); return pf8 && pf16 && pf32 ? 0 : 4;
}
'''


def main() -> int:
    actual_sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    if actual_sha != EXPECTED_SHA256:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: installed binary drifted: {actual_sha}")
    compiler = shutil.which("clang++")
    if not compiler:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: clang++ unavailable")
    with tempfile.TemporaryDirectory(prefix="toondilate_installed_all_depths_") as temp:
        temp_path = Path(temp)
        source = temp_path / "probe.cpp"
        executable = temp_path / "probe"
        source.write_text(PROBE, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        build = subprocess.run([
            compiler, "-std=c++17", "-arch", "arm64", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(source), "-o", str(executable),
        ], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: probe build failed\n{build.stderr}")
        run = subprocess.run([str(executable), str(BINARY)], capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: probe failed rc={run.returncode}\n{run.stdout}\n{run.stderr}")
    depths = json.loads(run.stdout)
    report = {
        "status": "PASS_INSTALLED_DYNAMIC_ALL_DEPTHS",
        "installed_binary": str(BINARY),
        "binary_sha256": actual_sha,
        "architecture": "arm64",
        "commands": ["PF_Cmd_SMART_PRE_RENDER", "PF_Cmd_SMART_RENDER"],
        "fixture": {"dimensions": [3, 2], "radius": 1, "padding": 8, "nonzero_extents": True},
        "gates": {"dlopen_effectmain": True, "PF8_exact": depths["PF8"], "PF16_exact": depths["PF16"], "PF32_bitwise_exact": depths["PF32"]},
        "claim_boundary": "Installed arm64 EffectMain under focused AE-free callbacks. No real AE host loading or rendering claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT.with_suffix(".md").write_text(
        "# OLMToonDilate installed dynamic all-depth entry — 2026-08-06\n\n"
        "- Status: **PASS_INSTALLED_DYNAMIC_ALL_DEPTHS**\n"
        f"- Installed arm64 binary SHA-256: `{actual_sha}`.\n"
        "- PF8, PF16, and PF32 independently execute SmartPreRender/SmartRender exactly, including padding and callback lifecycle.\n"
        "- This is an AE-free dynamic-load boundary; real AE loading/rendering remains unclaimed.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
