#!/usr/bin/env python3
"""Source-included Mac PF16/PF32 ToonDilate SmartRender adapter proof."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
WIDTH, HEIGHT = 5, 3
PIXELS = WIDTH * HEIGHT
PADDING = 4
PAD = 0xA5
OUT_PAD = 0xEE


def compile_probe(directory: Path) -> tuple[Path, dict[str, object]]:
    compiler_name = os.environ.get("CXX", "clang++")
    compiler = shutil.which(compiler_name)
    if not compiler:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: compiler not found: {compiler_name}")
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe = directory / "toondilate_mac_smartrender_adapter_probe.cpp"
    executable = directory / "toondilate_mac_smartrender_adapter_probe"
    probe.write_text(
        f'''#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

using A_long = std::int32_t;
using A_u_long = std::uint32_t;
using PF_ProgPtr = void *;
using PF_PixelPtr = void *;
using PF_PluginDataPtr = void *;
using PF_PluginDataCB2 = void *;
struct SPBasicSuite;
using PF_Err = A_long;
using PF_FpLong = double;
constexpr int WIDTH = 5, HEIGHT = 3, PADDING = 4, PAD = 0xA5, OUT_PAD = 0xEE;
enum {{ PF_Err_NONE = 0, PF_Err_BAD_CALLBACK_PARAM = -1, PF_Err_INVALID_CALLBACK = -2 }};
enum PF_Cmd {{ PF_Cmd_ABOUT = 0, PF_Cmd_GLOBAL_SETUP, PF_Cmd_PARAMS_SETUP,
               PF_Cmd_RENDER, PF_Cmd_SMART_PRE_RENDER, PF_Cmd_SMART_RENDER }};
enum PF_PixelFormat {{ PF_PixelFormat_INVALID, PF_PixelFormat_ARGB32,
                       PF_PixelFormat_ARGB64, PF_PixelFormat_ARGB128 }};
struct PF_Pixel8 {{ std::uint8_t alpha, red, green, blue; }};
struct PF_Pixel16 {{ std::uint16_t alpha, red, green, blue; }};
struct PF_PixelFloat {{ float alpha, red, green, blue; }};
struct PF_LRect {{ A_long left, top, right, bottom; }};
struct PF_EffectWorld {{ PF_PixelPtr data; A_long rowbytes, width, height; short bitdepth; PF_LRect extent_hint; }};
using PF_LayerDef = PF_EffectWorld;
struct PF_FloatSlider {{ PF_FpLong value; }};
struct PF_ParamDef {{ union {{ PF_FloatSlider fs_d; PF_LayerDef ld; }} u; }};
struct PF_InData {{ PF_ProgPtr effect_ref; A_long current_time, time_step, time_scale; void *pica_basicP; }};
struct PF_OutData {{ char return_msg[256]; A_u_long my_version, out_flags, out_flags2; A_long num_params; }};
struct PF_RenderRequest {{ bool preserve_rgb_of_zero_alpha; }};
struct PF_CheckoutResult {{ PF_LRect result_rect, max_result_rect; A_long ref_width; }};
struct PF_PreRenderInput {{ PF_RenderRequest output_request; }};
struct PF_PreRenderOutput {{ PF_LRect result_rect, max_result_rect; void *pre_render_data; void (*delete_pre_render_data_func)(void *); }};
struct PF_PreRenderCallbacks {{ PF_Err (*checkout_layer)(PF_ProgPtr, A_long, A_long, PF_RenderRequest *, A_long, A_long, A_long, PF_CheckoutResult *); }};
struct PF_PreRenderExtra {{ PF_PreRenderInput *input; PF_PreRenderOutput *output; PF_PreRenderCallbacks *cb; }};
struct PF_SmartRenderInput {{ short bitdepth; void *pre_render_data; }};
struct PF_SmartRenderCallbacks {{ PF_Err (*checkout_layer_pixels)(PF_ProgPtr, A_long, PF_EffectWorld **); PF_Err (*checkout_output)(PF_ProgPtr, PF_EffectWorld **); PF_Err (*checkin_layer_pixels)(PF_ProgPtr, A_long); }};
struct PF_SmartRenderExtra {{ PF_SmartRenderInput *input; PF_SmartRenderCallbacks *cb; }};
struct PF_WorldSuite2 {{ PF_Err PF_GetPixelFormat(PF_LayerDef *w, PF_PixelFormat *f) {{ *f = w->bitdepth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128; return PF_Err_NONE; }} }};
struct PF_ColorParamSuite1 {{}};
struct PF_ANSICallbacksSuite1 {{ int (*sprintf)(char *, const char *, ...); }};
struct AEGP_SuiteHandler {{ explicit AEGP_SuiteHandler(void *) {{}} PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() {{ static PF_ANSICallbacksSuite1 s{{&std::sprintf}}; return &s; }} }};
template <typename T> struct AEFX_SuiteScoper {{ T suite; AEFX_SuiteScoper(PF_InData *, const char *, A_long, PF_OutData *) {{}} T *operator->() {{ return &suite; }} }};
static constexpr const char *kPFWorldSuite = "PF World Suite"; static constexpr A_long kPFWorldSuiteVersion2 = 2;
static PF_FpLong g_radius = 0.0; static int g_render_fallbacks = 0;
static PF_Err checkout_param(PF_InData *, A_long, A_long, A_long, A_long, PF_ParamDef *p) {{ std::memset(p, 0, sizeof(*p)); p->u.fs_d.value = g_radius; return PF_Err_NONE; }}
static inline const char *GetStringPtr(int) {{ return ""; }}
static PF_Err register_effect(...) {{ return PF_Err_NONE; }}
#define OLMTOONDILATE_H
#define AEFX_SUITE_HELPER_H
#define AE_OS_MAC 1
#define DllExport
#define PF_Stage_DEVELOP 0
#define PF_VERSION(...) 0u
#define PF_OutFlag2_SUPPORTS_SMART_RENDER 1u
#define PF_OutFlag2_FLOAT_COLOR_AWARE 2u
#define PF_OutFlag2_SUPPORTS_GET_FLATTENED_SEQUENCE_DATA 4u
#define PF_Precision_TENTHS 0
#define AEFX_CLR_STRUCT(x) std::memset(&(x), 0, sizeof(x))
#define ERR(x) do {{ if (err == PF_Err_NONE) err = (x); }} while (0)
#define PF_CHECKOUT_PARAM(in, index, t, step, scale, out) checkout_param((in), (index), (t), (step), (scale), (out))
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_REGISTER_EFFECT_EXT2(...) register_effect()
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
enum {{ StrID_NONE, StrID_Name, StrID_Description, StrID_SearchRadius_Param_Name, StrID_NUMTYPES }};
enum {{ OLMTOONDILATE_INPUT = 0, OLMTOONDILATE_SEARCH_RADIUS, OLMTOONDILATE_NUM_PARAMS }};
struct OLMToonDilateInfo {{ PF_FpLong search_radius; PF_FpLong comp_width; }};
#define MAJOR_VERSION 1
#define MINOR_VERSION 1
#define BUG_VERSION 1
#define PF_MAX_CHAN8 255
#define PF_MAX_CHAN16 65535
#define TRUE true
#include "{source}"

namespace {{
constexpr int kRowbytes16 = WIDTH * 8 + PADDING;
constexpr int kRowbytes32 = WIDTH * 16 + PADDING;
std::uint8_t *bytes(PF_EffectWorld &w) {{ return static_cast<std::uint8_t *>(w.data); }}
void fill(std::vector<std::uint8_t> &v, int pixel_size) {{
    std::fill(v.begin(), v.end(), PAD);
    for (int y = 0; y < HEIGHT; ++y) for (int x = 0; x < WIDTH; ++x) {{
        auto *p = v.data() + y * (WIDTH * pixel_size + PADDING) + x * pixel_size;
        if (pixel_size == 8) {{ auto *q = reinterpret_cast<std::uint16_t *>(p); q[0] = (x == 2 && y == 1) ? 0 : 65535; q[1] = 0x1234 + x; q[2] = 0x2345 + y; q[3] = 0x3456 + x + y; }}
        else {{ auto *q = reinterpret_cast<float *>(p); q[0] = (x == 2 && y == 1) ? 0.0f : 1.0f; q[1] = 0.125f + x; q[2] = 0.25f + y; q[3] = 0.5f + x + y; }}
    }}
}}
bool padding(const std::vector<std::uint8_t> &v, int rowbytes, std::uint8_t value) {{ for (int y = 0; y < HEIGHT; ++y) for (int i = rowbytes - PADDING; i < rowbytes; ++i) if (v[y * rowbytes + i] != value) return false; return true; }}
struct State {{ PF_EffectWorld *input; PF_EffectWorld *output; int pre_checkout = 0, pixels_checkout = 0, output_checkout = 0, checkin = 0; bool preserve = false; }};
State *state(PF_ProgPtr p) {{ return static_cast<State *>(p); }}
PF_Err pre_checkout(PF_ProgPtr p, A_long, A_long, PF_RenderRequest *req, A_long, A_long, A_long, PF_CheckoutResult *out) {{ auto *s = state(p); ++s->pre_checkout; s->preserve = req->preserve_rgb_of_zero_alpha; out->result_rect = {{0, 0, WIDTH, HEIGHT}}; out->max_result_rect = out->result_rect; out->ref_width = WIDTH; return PF_Err_NONE; }}
PF_Err pixels_checkout(PF_ProgPtr p, A_long, PF_EffectWorld **out) {{ auto *s = state(p); ++s->pixels_checkout; *out = s->input; return PF_Err_NONE; }}
PF_Err output_checkout(PF_ProgPtr p, PF_EffectWorld **out) {{ auto *s = state(p); ++s->output_checkout; *out = s->output; return PF_Err_NONE; }}
PF_Err checkin(PF_ProgPtr p, A_long) {{ ++state(p)->checkin; return PF_Err_NONE; }}
}}

int main() {{
    std::printf("{{\\"status\\":\\"ok\\",\\"cases\\":["); bool first = true;
    for (short depth : {{16, 32}}) {{
        const int pixel_size = depth == 16 ? 8 : 16; const int rowbytes = WIDTH * pixel_size + PADDING;
        std::vector<std::uint8_t> input_bytes(rowbytes * HEIGHT), output_bytes(rowbytes * HEIGHT, OUT_PAD), before;
        fill(input_bytes, pixel_size); before = input_bytes;
        PF_EffectWorld input{{input_bytes.data(), rowbytes, WIDTH, HEIGHT, depth, {{0, 0, WIDTH, HEIGHT}}}};
        PF_EffectWorld output{{output_bytes.data(), rowbytes, WIDTH, HEIGHT, depth, {{0, 0, WIDTH, HEIGHT}}}};
        State st{{&input, &output}}; PF_InData in{{&st, 0, 1, 1, nullptr}}; PF_OutData out{{}};
        PF_RenderRequest request{{false}}; PF_PreRenderInput pre_in{{request}}; PF_PreRenderOutput pre_out{{}};
        PF_PreRenderCallbacks pre_cb{{pre_checkout}}; PF_PreRenderExtra pre{{&pre_in, &pre_out, &pre_cb}};
        if (EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre) != PF_Err_NONE) return 10;
        PF_SmartRenderInput render_in{{depth, pre_out.pre_render_data}}; PF_SmartRenderCallbacks render_cb{{pixels_checkout, output_checkout, checkin}}; PF_SmartRenderExtra render{{&render_in, &render_cb}};
        if (EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &render) != PF_Err_NONE) return 11;
        bool visible = true; for (int y = 0; y < HEIGHT; ++y) visible = visible && std::memcmp(output_bytes.data() + y * rowbytes, before.data() + y * rowbytes, WIDTH * pixel_size) == 0;
        bool gates = st.pre_checkout == 1 && st.pixels_checkout == 1 && st.output_checkout == 1 && st.checkin == 1 && st.preserve && visible && padding(output_bytes, rowbytes, OUT_PAD) && padding(input_bytes, rowbytes, PAD) && input_bytes == before && g_render_fallbacks == 0;
        if (!gates) return 20 + depth;
        if (!first) std::printf(","); first = false;
        std::printf("{{\\"pixel_format\\":\\"PF%d\\",\\"bitdepth\\":%d,\\"search_radius\\":0,\\"preserve_rgb_of_zero_alpha\\":true,\\"checkout_layer_once\\":true,\\"checkout_layer_pixels_once\\":true,\\"checkout_output_once\\":true,\\"checkin_layer_pixels_once\\":true,\\"visible_output_bit_identical\\":true,\\"zero_alpha_rgb_preserved\\":true,\\"input_padding_preserved\\":true,\\"output_padding_preserved\\":true,\\"pf_cmd_render_fallbacks\\":0}}", depth, depth);
        if (pre_out.delete_pre_render_data_func) pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
    }}
    std::printf("]}}\\n"); return 0;
}}
''', encoding="utf-8")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=False)
    if sdk.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: xcrun --show-sdk-path failed: {sdk.stderr.strip()}")
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-isysroot", sdk.stdout.strip(), "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(probe), "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: source-included adapter did not compile\n{build.stderr}")
    return executable, {"compiler": compiler, "arch": "arm64", "flags": command[1:]}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_toondilate_mac_smartrender_") as name:
        executable, build = compile_probe(Path(name))
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: adapter probe exited {run.returncode}: {run.stderr.strip()}")
    report = json.loads(run.stdout)
    report["build"] = build
    report["production_source"] = str(SOURCE.relative_to(ROOT))
    report["claim_boundary"] = "Mac-local source-included PF adapter proof; no AE exact or Windows claim"
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
