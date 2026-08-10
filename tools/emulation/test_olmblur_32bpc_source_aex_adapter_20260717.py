#!/usr/bin/env python3
"""Mac-only production-source 32bpc adapter versus actual-AEX fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
EXPECTED_AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def probe_source() -> str:
    return r'''
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>
using A_long = std::int32_t; using A_u_long = std::uint32_t; using A_u_char = std::uint8_t;
using A_short = std::int16_t; using PF_FpLong = double; using PF_ProgPtr = void *;
using PF_PixelPtr = void *; using PF_PluginDataPtr = void *; using PF_PluginDataCB2 = void *;
struct SPBasicSuite;
using PF_Err = A_long;
enum { PF_Err_NONE = 0, PF_Err_OUT_OF_MEMORY = -3, PF_Err_INVALID_CALLBACK = -4 };
enum PF_Cmd { PF_Cmd_ABOUT, PF_Cmd_GLOBAL_SETUP, PF_Cmd_PARAMS_SETUP, PF_Cmd_RENDER,
              PF_Cmd_SMART_PRE_RENDER, PF_Cmd_SMART_RENDER };
struct PF_Pixel8 { std::uint8_t alpha, red, green, blue; };
struct PF_Pixel16 { std::uint16_t alpha, red, green, blue; };
struct PF_PixelFloat { float alpha, red, green, blue; };
struct PF_LRect { A_long left, top, right, bottom; };
struct PF_EffectWorld { PF_PixelPtr data; A_long rowbytes, width, height; A_short bitdepth; PF_LRect extent_hint; A_long dephault; };
using PF_LayerDef = PF_EffectWorld;
struct PF_FloatSlider { PF_FpLong value; }; struct PF_Fixed { A_long value; };
struct PF_Slider { A_long value; }; struct PF_Popup { A_long value; };
struct PF_Checkbox { struct { const char *nameptr; } u; A_long value, dephault; };
struct PF_ParamDef { A_long param_type; char name[32]; A_u_long flags; struct { A_long id; } uu;
  union { PF_FloatSlider fs_d; PF_Fixed fd; PF_Slider sd; PF_Popup pd; PF_Checkbox bd; PF_LayerDef ld; } u; };
struct PF_InData { PF_ProgPtr effect_ref; A_long current_time, time_step, time_scale;
  struct { A_long num, den; } downsample_x, downsample_y; void *pica_basicP; };
struct PF_OutData { char return_msg[256]; A_u_long my_version, out_flags, out_flags2; A_long num_params; };
struct PF_RenderRequest { bool preserve_rgb_of_zero_alpha; };
struct PF_CheckoutResult { PF_LRect result_rect, max_result_rect; A_long ref_width; };
struct PF_PreRenderInput { PF_RenderRequest output_request; };
struct PF_PreRenderOutput { PF_LRect result_rect, max_result_rect; bool solid; void *pre_render_data; A_u_long flags; };
struct PF_PreRenderCallbacks { PF_Err (*checkout_layer)(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*); };
struct PF_PreRenderExtra { PF_PreRenderInput *input; PF_PreRenderOutput *output; PF_PreRenderCallbacks *cb; };
struct PF_SmartRenderInput { A_short bitdepth; void *pre_render_data; };
struct PF_SmartRenderCallbacks { PF_Err (*checkout_layer_pixels)(PF_ProgPtr,A_long,PF_EffectWorld**);
  PF_Err (*checkout_output)(PF_ProgPtr,PF_EffectWorld**); PF_Err (*checkin_layer_pixels)(PF_ProgPtr,A_long); };
struct PF_SmartRenderExtra { PF_SmartRenderInput *input; PF_SmartRenderCallbacks *cb; };
struct PF_ANSICallbacksSuite1 { int (*sprintf)(char *, const char *, ...); };
struct AEGP_SuiteHandler { explicit AEGP_SuiteHandler(void*) {}
  PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() { static PF_ANSICallbacksSuite1 s{&std::sprintf}; return &s; } };
struct PF_WorldSuite2 { PF_Err PF_GetPixelFormat(PF_LayerDef*, int *format) { *format = 3; return PF_Err_NONE; } };
template <typename T> struct AEFX_SuiteScoper { T suite; AEFX_SuiteScoper(PF_InData*, const char*, A_long, PF_OutData*) {} T *operator->() { return &suite; } };
static PF_Err checkout_param(PF_InData*, A_long, A_long, A_long, A_long, PF_ParamDef*) { return PF_Err_NONE; }
static PF_Err register_effect(...) { return PF_Err_NONE; }
static inline const char *GetStringPtr(int) { return ""; }
#define OLMBLUR_H
#define AE_OS_MAC 1
#define DllExport
#define _H_AEFX_SUITE_HELPER_TEMPLATE
#define PF_VERSION(...) 0u
#define PF_Stage_DEVELOP 0
#define PF_Precision_TENTHS 0
#define PF_Precision_HUNDREDTHS 0
#define PF_OutFlag_NONE 0
#define PF_OutFlag2_SUPPORTS_SMART_RENDER 1u
#define PF_OutFlag2_FLOAT_COLOR_AWARE 2u
#define PF_OutFlag2_PARAM_GROUP_START_COLLAPSED 4u
#define TRUE true
#define FALSE false
#define AEFX_CLR_STRUCT(x) std::memset(&(x), 0, sizeof(x))
#define ERR(x) do { if (err == PF_Err_NONE) err = (x); } while (0)
#define PF_CHECKOUT_PARAM(...) checkout_param(__VA_ARGS__)
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_REGISTER_EFFECT_EXT2(...) register_effect()
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
#define PF_ADD_FIXED(...) ((void)0)
#define PF_ADD_SLIDER(...) ((void)0)
#define PF_ADD_POPUP(...) ((void)0)
#define PF_ADD_CHECKBOX(...) ((void)0)
#define PF_ADD_PARAM(...) PF_Err_NONE
#define PF_Param_CHECKBOX 1
#define PF_ParamFlag_USE_VALUE_FOR_OLD_PROJECTS 0x80u
#define PF_ValueDisplayFlag_PERCENT 1
#define PF_STRNNCPY(dst, src, size) std::snprintf((dst), (size), "%s", (src))
#define PF_COPY(in, out, a, b) (std::memcpy((out)->data, (in)->data, static_cast<std::size_t>((out)->rowbytes) * (out)->height), PF_Err_NONE)
#define PF_DEEP_COLOR_AWARE 1
#define MAJOR_VERSION 1
#define MINOR_VERSION 2
#define BUG_VERSION 1
#define StrID_Name 1
#define StrID_Description 2
#define StrID_BlurAmount_Param_Name 3
#define StrID_BlurSmoothness_Param_Name 4
#define StrID_Repeat_Param_Name 5
#define StrID_BiasDirection_Param_Name 6
#define StrID_BiasDirection_Choices 7
#define StrID_Legacy_Param_Name 8
#define BLUR_AMOUNT_DISK_ID 1
#define BLUR_SMOOTHNESS_DISK_ID 2
#define REPEAT_DISK_ID 3
#define BIAS_DIRECTION_DISK_ID 4
#define LEGACY_DISK_ID 5
#define OLMBLUR_INPUT 0
#define OLMBLUR_BLUR_AMOUNT 1
#define OLMBLUR_BLUR_SMOOTHNESS 2
#define OLMBLUR_REPEAT 3
#define OLMBLUR_BIAS_DIRECTION 4
#define OLMBLUR_LEGACY 5
#define OLMBLUR_NUM_PARAMS 6
#define BIAS_DIR_VERTICAL 1
#define BIAS_DIR_HORIZONTAL 2
#define PF_Err_INTERNAL_STRUCT_DAMAGED -2
#define PF_Err_BAD_CALLBACK_PARAM -1
#define PF_PixelFormat int
#define PF_PixelFormat_INVALID 0
#define PF_PixelFormat_ARGB32 1
#define PF_PixelFormat_ARGB64 2
#define PF_PixelFormat_ARGB128 3
#define kPFWorldSuite "PF World Suite"
#define kPFWorldSuiteVersion2 2
#include "__OLMBLUR_MAC_SOURCE__"

static std::vector<std::uint8_t> read_file(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(stream)), {});
}

int main(int argc, char **argv) {
  if (argc != 10) return 2;
  const int width = std::atoi(argv[1]), height = std::atoi(argv[2]);
  const float amount = std::strtof(argv[3], nullptr); const float smoothness = std::strtof(argv[4], nullptr);
  const int repeat = std::atoi(argv[5]); const int bias = std::atoi(argv[6]), legacy = std::atoi(argv[7]);
  const std::vector<std::uint8_t> source = read_file(argv[8]);
  const std::vector<std::uint8_t> expected = read_file(argv[9]);
  const int rowbytes = width * 16 + 32; const std::size_t active = static_cast<std::size_t>(width) * 16;
  if (source.size() != active * height || expected.size() != active * height) return 3;
  const std::uint8_t input_pad = 0xA5, output_pad = 0xEE;
  std::vector<std::uint8_t> input(rowbytes * height, input_pad), output(rowbytes * height, output_pad);
  for (int y = 0; y < height; ++y) std::memcpy(input.data() + y * rowbytes, source.data() + y * active, active);
  PF_EffectWorld in{input.data(), rowbytes, width, height, 32, {0, 0, width, height}, 0};
  PF_EffectWorld out{output.data(), rowbytes, width, height, 32, {0, 0, width, height}, 0};
  PF_InData in_data{}; in_data.downsample_x = {1, 1}; in_data.downsample_y = {1, 1};
  BlurParams params{amount, smoothness, repeat, bias, legacy};
  const PF_Err err = BlurRender(&in_data, &in, &out, 32, &params);
  if (err != PF_Err_NONE) { std::fprintf(stderr, "BlurRender returned %d\n", (int)err); return 4; }
  std::size_t mismatches = 0; std::size_t alpha_mismatches = 0; std::size_t padding_mismatches = 0;
  for (int y = 0; y < height; ++y) {
    const auto *actual = output.data() + y * rowbytes; const auto *want = expected.data() + y * active;
    for (std::size_t i = 0; i < active; ++i) if (actual[i] != want[i]) ++mismatches;
    for (int i = 0; i < 32; ++i) if (actual[active + i] != output_pad) ++padding_mismatches;
    for (int x = 0; x < width; ++x) if (std::memcmp(actual + x * 16, source.data() + y * active + x * 16, 4) != 0) ++alpha_mismatches;
  }
  std::printf("{\"status\":\"%s\",\"mismatched_bytes\":%zu,\"alpha_mismatches\":%zu,\"padding_mismatches\":%zu}\n",
              (mismatches || alpha_mismatches || padding_mismatches) ? "fail" : "pass",
              mismatches, alpha_mismatches, padding_mismatches);
  return (mismatches || alpha_mismatches || padding_mismatches) ? 5 : 0;
}
'''


def compile_probe(directory: Path) -> Path:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: clang++ is unavailable")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=False)
    if sdk.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: xcrun failed: {sdk.stderr.strip()}")
    source = directory / "olmblur_32bpc_source_aex_adapter_probe.cpp"
    executable = directory / "olmblur_32bpc_source_aex_adapter_probe"
    source.write_text(
        probe_source().replace(
            "__OLMBLUR_MAC_SOURCE__",
            str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace('\\', '\\\\').replace('"', '\\"'),
        ),
        encoding="utf-8",
    )
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2",
               "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1", "-fno-fast-math", "-ffp-contract=off",
               "-isysroot", sdk.stdout.strip(), "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), "-I", str(ROOT / "core"),
               str(source), str(ROOT / "core/olmblur_helper.cpp"), str(ROOT / "core/olmblur_fullworker_helper.cpp"),
               str(ROOT / "core/olmblur_worker16_nonlegacy.cpp"), str(ROOT / "core/olmblur_worker16_legacy.cpp"),
               str(ROOT / "core/olmblur_worker32_nonlegacy.cpp"), str(ROOT / "core/olmblur_worker32_legacy.cpp"),
               str(ROOT / "core/olmblur_worker8_legacy.cpp"), str(ROOT / "core/olmblur_worker_orchestration.cpp"),
               "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: production source probe did not compile\n{build.stderr}")
    return executable


def main() -> int:
    if not AEX.exists() or hashlib.sha256(AEX.read_bytes()).hexdigest() != EXPECTED_AEX_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual-AEX fixture hash drift or missing AEX")
    manifests = [
        ROOT / "tools/emulation/fixtures/olmblur_worker32_nonlegacy/manifest.json",
        ROOT / "tools/emulation/fixtures/olmblur_worker32_legacy/manifest.json",
    ]
    cases = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text())
        base = manifest_path.parent
        for case in manifest["cases"]:
            cases.append((manifest, base, case))
    with tempfile.TemporaryDirectory(prefix="olmblur_32bpc_source_aex_") as name:
        executable = compile_probe(Path(name))
        results = []
        for manifest, base, case in cases:
            source = base / case["id"] / "source_argb_f32.bin"
            expected = base / case["id"] / "expected_argb_f32.bin"
            run = subprocess.run([str(executable), str(case["width"]), str(case["height"]),
                                  str(case["blur_amount"]), str(case["smoothness"]),
                                  str(case["repeat"]), str(case["bias_direction"]),
                                  str(manifest["legacy"]), str(source), str(expected)],
                                 cwd=ROOT, capture_output=True, text=True, check=False)
            if run.returncode:
                raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {case['id']} exited {run.returncode}: {run.stderr.strip()} {run.stdout.strip()}")
            result = json.loads(run.stdout)
            result["id"] = case["id"]
            results.append(result)
    report = {"schema": "olmblur.mac-source-aex-adapter/1", "aex_sha256": EXPECTED_AEX_SHA256,
              "cases": results, "case_count": len(results),
              "status": "pass", "scope": "Mac production source BlurRender 32bpc dispatch versus actual-AEX float fixtures; no AE exact or Windows claim"}
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
