#!/usr/bin/env python3
"""Source-included Mac PF16/PF32 ToonDilate SmartRender adapter proof."""

from __future__ import annotations

import json
import hashlib
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
PF32_FIXTURE_REPORT = ROOT / "refs/conformance/olmtoondilate_pf32_seed_propagation_matrix_20260717.json"
PF32_FIXTURE_REPORT_SHA256 = "8fcd02113301016e7a8057e80e124ff0f99a994be812b3532e16e953bf37652f"
PF16_RADIUS2_REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_radius2_shape_20260805.json"
PF16_RADIUS2_REPORT_SHA256 = "9a076146cb3d0e37be5a5112f8a1a0d0d4c1c0c0ba13767c3acefb6b13ca6c20"
PF8_RADIUS2_REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_radius2_shape_20260805.json"
PF8_RADIUS2_REPORT_SHA256 = "4dc162937a1c4dbe5e546c80d6b4e37e763cb6df5182c040753a52560a8694ab"
PF8_RADIUS3_TIE_REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_radius3_boundary_tie_20260805.json"
PF8_RADIUS3_TIE_REPORT_SHA256 = "57793cd79ca3a0a455e7525028065b9926ed7fe30d41ea473a08f342929a2577"
PF16_RADIUS3_TIE_REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_radius3_boundary_tie_20260805.json"
PF16_RADIUS3_TIE_REPORT_SHA256 = "cd11246d954af6c6506405e5734682b44b1a696a82b27d07e7e4ce4e284aa0a3"
PF32_RADIUS3_TIE_REPORT = ROOT / "refs/conformance/olmtoondilate_pf32_radius3_boundary_tie_20260805.json"
PF32_RADIUS3_TIE_REPORT_SHA256 = "dac69bba980a44b1c814d62a6d99543a21866a76c8e32b0dbbd82a91089e3184"
CORNER_ALL_DEPTHS_REPORT = ROOT / "refs/conformance/olmtoondilate_corner_seed_all_depths_20260805.json"
CORNER_ALL_DEPTHS_REPORT_SHA256 = "ffeebcbba526aa566bcde6a6971a7421c1a4e4a52676bd5a0e3d262ce3a507e8"
ALPHA0_ALL_DEPTHS_REPORT = ROOT / "refs/conformance/olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.json"
ALPHA0_ALL_DEPTHS_REPORT_SHA256 = "d3b19edeb54e88614d8cdf21f92c132dcde559f49f9f158ad0575714a3119faa"
NONPOSITIVE_REPORT = ROOT / "refs/conformance/olmtoondilate_nonpositive_radius_all_depths_20260805.json"
NONPOSITIVE_REPORT_SHA256 = "db3ff858e53101827b4e6369aaa733350b44c14ce4f3130b97f506ed90366d0c"
ACTUAL_ENTRY_REPORT = ROOT / "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json"
ACTUAL_ENTRY_REPORT_SHA256 = "4c96cae5eb9dde9761dd7b461dfe7c364644797a15534b144262bbf746ed01ec"
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_fixture_identity() -> None:
    if sha256(PF32_FIXTURE_REPORT) != PF32_FIXTURE_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 seed-propagation fixture report identity drifted")
    if sha256(AEX) != AEX_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: OLMToonDilate AEX identity drifted")
    if sha256(PF16_RADIUS2_REPORT) != PF16_RADIUS2_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 radius-2 fixture report identity drifted")
    if sha256(PF8_RADIUS2_REPORT) != PF8_RADIUS2_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 radius-2 fixture report identity drifted")
    if sha256(PF8_RADIUS3_TIE_REPORT) != PF8_RADIUS3_TIE_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 radius-3 tie fixture report identity drifted")
    if sha256(PF16_RADIUS3_TIE_REPORT) != PF16_RADIUS3_TIE_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 radius-3 tie fixture report identity drifted")
    if sha256(PF32_RADIUS3_TIE_REPORT) != PF32_RADIUS3_TIE_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 radius-3 tie fixture report identity drifted")
    if sha256(CORNER_ALL_DEPTHS_REPORT) != CORNER_ALL_DEPTHS_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: all-depth corner fixture identity drifted")
    if sha256(ALPHA0_ALL_DEPTHS_REPORT) != ALPHA0_ALL_DEPTHS_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha-zero eligibility fixture identity drifted")
    if sha256(NONPOSITIVE_REPORT) != NONPOSITIVE_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: nonpositive-radius fixture identity drifted")
    if sha256(ACTUAL_ENTRY_REPORT) != ACTUAL_ENTRY_REPORT_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual entrypoint fixture identity drifted")
    fixture = json.loads(PF32_FIXTURE_REPORT.read_text(encoding="utf-8"))
    if fixture.get("status") != "PASS_PF32_SEED_PROPAGATION_MATRIX":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 fixture status is not exact")
    contract = fixture.get("fixture", {})
    if contract.get("width") != 5 or contract.get("height") != 5 or contract.get("radii") != [1.0, 2.0]:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 fixture geometry/radius contract drifted")
    if not fixture.get("gates", {}).get("all_visible_4_word_exact"):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 fixture exact gate is absent")
    pf16 = json.loads(PF16_RADIUS2_REPORT.read_text(encoding="utf-8"))
    if pf16.get("status") != "PASS_PF16_RADIUS2_SHAPE" or not all(pf16.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 radius-2 fixture is not exact")
    if pf16.get("fixture", {}).get("radius") != 2 or pf16.get("fixture", {}).get("width") != 5:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 radius-2 fixture contract drifted")
    pf8 = json.loads(PF8_RADIUS2_REPORT.read_text(encoding="utf-8"))
    if pf8.get("status") != "PASS_PF8_RADIUS2_SHAPE" or not all(pf8.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 radius-2 fixture is not exact")
    if pf8.get("fixture", {}).get("radius") != 2 or pf8.get("fixture", {}).get("width") != 5:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 radius-2 fixture contract drifted")
    tie = json.loads(PF8_RADIUS3_TIE_REPORT.read_text(encoding="utf-8"))
    if tie.get("status") != "PASS_PF8_RADIUS3_BOUNDARY_TIE" or not all(tie.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 radius-3 tie fixture is not exact")
    tie16 = json.loads(PF16_RADIUS3_TIE_REPORT.read_text(encoding="utf-8"))
    if tie16.get("status") != "PASS_PF16_RADIUS3_BOUNDARY_TIE" or not all(tie16.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 radius-3 tie fixture is not exact")
    tie32 = json.loads(PF32_RADIUS3_TIE_REPORT.read_text(encoding="utf-8"))
    if tie32.get("status") != "PASS_PF32_RADIUS3_BOUNDARY_TIE" or not all(tie32.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 radius-3 tie fixture is not exact")
    if tie32.get("fixture", {}).get("rowbytes") != 116 or tie32.get("worker") != "0x1801a6800":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 typed fixture contract drifted")
    corner = json.loads(CORNER_ALL_DEPTHS_REPORT.read_text(encoding="utf-8"))
    if corner.get("status") != "PASS_CORNER_SEED_ALL_DEPTHS" or not all(corner.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: all-depth corner fixture is not exact")
    alpha0 = json.loads(ALPHA0_ALL_DEPTHS_REPORT.read_text(encoding="utf-8"))
    if alpha0.get("status") != "PASS_ALPHA0_RGB_ELIGIBILITY_ALL_DEPTHS" or not all(alpha0.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: alpha-zero eligibility fixture is not exact")
    nonpositive = json.loads(NONPOSITIVE_REPORT.read_text(encoding="utf-8"))
    if nonpositive.get("status") != "PASS_NONPOSITIVE_RADIUS_ALL_DEPTHS" or not all(nonpositive.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: nonpositive-radius fixture is not exact")
    actual_entry = json.loads(ACTUAL_ENTRY_REPORT.read_text(encoding="utf-8"))
    if actual_entry.get("status") != "PASS_SEQUENCE_AND_SMARTPRE_ENTRY" or not all(actual_entry.get("gates", {}).get(key) for key in ("radius2_4x2_all_depths_exact", "radius3_pf8_5x1_exact", "radius3_pf16_5x1_exact", "radius3_pf32_5x1_exact", "radius4_pf8_6x1_exact", "radius4_pf16_6x1_exact", "radius4_pf32_6x1_exact", "fractional_radius_2_01_pf8_exact", "fractional_radius_2_5_pf32_exact", "fractional_radius_3_25_pf16_exact", "empty_width_pf8_exact", "empty_height_pf16_exact", "empty_both_pf32_exact")):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual entrypoint radius-2/3 fixture is not exact")


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
enum {{ PF_Err_NONE = 0, PF_Err_BAD_CALLBACK_PARAM = -1, PF_Err_INVALID_CALLBACK = -2, PF_Err_OUT_OF_MEMORY = -3 }};
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
#define PF_MAX_CHAN16 32768
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
struct State {{ PF_EffectWorld *input; PF_EffectWorld *output; int pre_checkout = 0, pixels_checkout = 0, output_checkout = 0, checkin = 0; bool preserve = false; int width = WIDTH, height = HEIGHT, result_left = 0, result_top = 0; }};
State *state(PF_ProgPtr p) {{ return static_cast<State *>(p); }}
PF_Err pre_checkout(PF_ProgPtr p, A_long, A_long, PF_RenderRequest *req, A_long, A_long, A_long, PF_CheckoutResult *out) {{ auto *s = state(p); ++s->pre_checkout; s->preserve = req->preserve_rgb_of_zero_alpha; out->result_rect = {{s->result_left, s->result_top, s->result_left+s->width, s->result_top+s->height}}; out->max_result_rect = out->result_rect; out->ref_width = s->width; return PF_Err_NONE; }}
PF_Err pixels_checkout(PF_ProgPtr p, A_long, PF_EffectWorld **out) {{ auto *s = state(p); ++s->pixels_checkout; *out = s->input; return PF_Err_NONE; }}
PF_Err output_checkout(PF_ProgPtr p, PF_EffectWorld **out) {{ auto *s = state(p); ++s->output_checkout; *out = s->output; return PF_Err_NONE; }}
PF_Err checkin(PF_ProgPtr p, A_long) {{ ++state(p)->checkin; return PF_Err_NONE; }}
template <typename Pixel> bool positive_radius_case(short depth, double radius) {{
    const int pixel_size = sizeof(Pixel), rowbytes = WIDTH * pixel_size + PADDING;
    std::vector<std::uint8_t> input_bytes(rowbytes * HEIGHT, PAD), output_bytes(rowbytes * HEIGHT, OUT_PAD);
    Pixel seed{{}};
    if constexpr (sizeof(Pixel) == 4) {{ seed = Pixel{{255, 10, 20, 30}}; }}
    else if constexpr (sizeof(Pixel) == 8) {{ seed = Pixel{{32768, 4004, 5005, 6006}}; }}
    else {{ seed = Pixel{{1.0f, 0.125f, 0.25f, 0.5f}}; }}
    for (int y = 0; y < HEIGHT; ++y) for (int x = 0; x < WIDTH; ++x) {{
        Pixel zero{{}}; std::memcpy(input_bytes.data() + y * rowbytes + x * pixel_size, &zero, pixel_size);
    }}
    std::memcpy(input_bytes.data() + rowbytes + 2 * pixel_size, &seed, pixel_size);
    PF_EffectWorld input{{input_bytes.data(), rowbytes, WIDTH, HEIGHT, depth, {{0, 0, WIDTH, HEIGHT}}}};
    PF_EffectWorld output{{output_bytes.data(), rowbytes, WIDTH, HEIGHT, depth, {{0, 0, WIDTH, HEIGHT}}}};
    State st{{&input, &output}}; PF_InData in{{&st, 0, 1, 1, nullptr}}; PF_OutData out{{}};
    PF_RenderRequest request{{false}}; PF_PreRenderInput pre_in{{request}}; PF_PreRenderOutput pre_out{{}};
    PF_PreRenderCallbacks pre_cb{{pre_checkout}}; PF_PreRenderExtra pre{{&pre_in, &pre_out, &pre_cb}};
    if (EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out, nullptr, nullptr, &pre) != PF_Err_NONE) return false;
    PF_SmartRenderInput render_in{{depth, pre_out.pre_render_data}}; PF_SmartRenderCallbacks render_cb{{pixels_checkout, output_checkout, checkin}}; PF_SmartRenderExtra render{{&render_in, &render_cb}};
    g_radius = radius;
    bool ok = EffectMain(PF_Cmd_SMART_RENDER, &in, &out, nullptr, nullptr, &render) == PF_Err_NONE;
    for (int y = 0; y < HEIGHT; ++y) for (int x = 0; x < WIDTH; ++x) {{
        Pixel expected{{}};
        if (std::max(std::abs(x - 2), std::abs(y - 1)) <= static_cast<int>(radius)) expected = seed;
        ok = ok && std::memcmp(output_bytes.data() + y * rowbytes + x * pixel_size, &expected, pixel_size) == 0;
    }}
    ok = ok && st.pre_checkout == 1 && st.pixels_checkout == 1 && st.output_checkout == 1 && st.checkin == 1 && st.preserve;
    ok = ok && padding(input_bytes, rowbytes, PAD) && padding(output_bytes, rowbytes, OUT_PAD);
    if (pre_out.delete_pre_render_data_func) pre_out.delete_pre_render_data_func(pre_out.pre_render_data);
    return ok;
}}
bool pf8_radius3_boundary_tie_case() {{
    constexpr int W = 7, H = 3, RB = 32; const PF_Pixel8 A{{255,10,20,30}}, B{{255,90,80,70}}, C{{0,3,5,7}};
    std::vector<std::uint8_t> input_bytes(RB * H, PAD), output_bytes(RB * H, OUT_PAD);
    for (int y=0;y<H;++y) for (int x=0;x<W;++x) {{ PF_Pixel8 p = (x==0&&y==1)?A:(x==6&&y==1)?B:C; std::memcpy(input_bytes.data()+y*RB+x*4,&p,4); }}
    PF_EffectWorld input{{input_bytes.data(),RB,W,H,8,{{0,0,W,H}}}}, output{{output_bytes.data(),RB,W,H,8,{{0,0,W,H}}}};
    State st{{&input,&output}}; st.width=W; st.height=H; PF_InData in{{&st,0,1,1,nullptr}}; PF_OutData out{{}};
    PF_RenderRequest request{{false}}; PF_PreRenderInput pre_in{{request}}; PF_PreRenderOutput pre_out{{}}; PF_PreRenderCallbacks pre_cb{{pre_checkout}}; PF_PreRenderExtra pre{{&pre_in,&pre_out,&pre_cb}};
    if (EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE) return false;
    PF_SmartRenderInput render_in{{8,pre_out.pre_render_data}}; PF_SmartRenderCallbacks render_cb{{pixels_checkout,output_checkout,checkin}}; PF_SmartRenderExtra render{{&render_in,&render_cb}}; g_radius=3.0;
    bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE; const int split[3]={{3,4,4}};
    for(int y=0;y<H;++y) for(int x=0;x<W;++x) {{ const PF_Pixel8 &e=x<split[y]?A:B; ok=ok&&std::memcmp(output_bytes.data()+y*RB+x*4,&e,4)==0; }}
    for(int y=0;y<H;++y) for(int i=28;i<RB;++i) ok=ok&&output_bytes[y*RB+i]==OUT_PAD;
    if(pre_out.delete_pre_render_data_func) pre_out.delete_pre_render_data_func(pre_out.pre_render_data); return ok;
}}
bool pf16_radius3_boundary_tie_case() {{
    constexpr int W=7,H=3,RB=60; const PF_Pixel16 A{{32768,1001,2002,3003}},B{{32768,4004,5005,6006}},C{{0,17,19,23}};
    std::vector<std::uint8_t> input_bytes(RB*H,PAD),output_bytes(RB*H,OUT_PAD);
    for(int y=0;y<H;++y) for(int x=0;x<W;++x) {{ PF_Pixel16 p=(x==0&&y==1)?A:(x==6&&y==1)?B:C; std::memcpy(input_bytes.data()+y*RB+x*8,&p,8); }}
    PF_EffectWorld input{{input_bytes.data(),RB,W,H,16,{{0,0,W,H}}}},output{{output_bytes.data(),RB,W,H,16,{{0,0,W,H}}}}; State st{{&input,&output}}; st.width=W;st.height=H;
    PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false; PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.0;
    bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;const int split[3]={{3,4,4}};for(int y=0;y<H;++y)for(int x=0;x<W;++x){{const PF_Pixel16&e=x<split[y]?A:B;ok=ok&&std::memcmp(output_bytes.data()+y*RB+x*8,&e,8)==0;}}
    for(int y=0;y<H;++y)for(int i=56;i<RB;++i)ok=ok&&output_bytes[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_radius3_boundary_tie_case() {{
    constexpr int W=7,H=3,RB=116; const PF_PixelFloat A{{1.0f,0.125f,0.25f,0.5f}},B{{1.0f,0.75f,0.625f,0.375f}},C{{0.0f,0.03125f,0.0625f,0.09375f}};
    std::vector<std::uint8_t> input_bytes(RB*H,PAD),output_bytes(RB*H,OUT_PAD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{PF_PixelFloat p=(x==0&&y==1)?A:(x==6&&y==1)?B:C;std::memcpy(input_bytes.data()+y*RB+x*16,&p,16);}}
    PF_EffectWorld input{{input_bytes.data(),RB,W,H,32,{{0,0,W,H}}}},output{{output_bytes.data(),RB,W,H,32,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};
    PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;
    PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    const int split[3]={{3,4,4}};for(int y=0;y<H;++y)for(int x=0;x<W;++x){{const PF_PixelFloat&e=x<split[y]?A:B;ok=ok&&std::memcmp(output_bytes.data()+y*RB+x*16,&e,16)==0;}}for(int y=0;y<H;++y)for(int i=112;i<RB;++i)ok=ok&&output_bytes[y*RB+i]==OUT_PAD;
    if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_corner_seed_case() {{
    constexpr int W=5,H=5,RB=84;const PF_PixelFloat A{{1.0f,.125f,.25f,.5f}},B{{1.0f,.75f,.625f,.375f}},C{{0.0f,.03125f,.0625f,.09375f}};
    std::vector<std::uint8_t> ib(RB*H,PAD),ob(RB*H,OUT_PAD);for(int y=0;y<H;++y)for(int x=0;x<W;++x){{PF_PixelFloat p=(x==0&&y==0)?A:(x==4&&y==4)?B:C;std::memcpy(ib.data()+y*RB+x*16,&p,16);}}
    PF_EffectWorld input{{ib.data(),RB,W,H,32,{{0,0,W,H}}}},output{{ob.data(),RB,W,H,32,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{const PF_PixelFloat&e=(x+y<=4)?A:B;ok=ok&&std::memcmp(ob.data()+y*RB+x*16,&e,16)==0;}}for(int y=0;y<H;++y)for(int i=80;i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_corner_seed_case() {{
    constexpr int W=5,H=5,RB=24;const PF_Pixel8 A{{255,10,20,30}},B{{255,90,80,70}},C{{0,3,5,7}};std::vector<std::uint8_t>ib(RB*H,PAD),ob(RB*H,OUT_PAD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{PF_Pixel8 p=(x==0&&y==0)?A:(x==4&&y==4)?B:C;std::memcpy(ib.data()+y*RB+x*4,&p,4);}}PF_EffectWorld input{{ib.data(),RB,W,H,8,{{0,0,W,H}}}},output{{ob.data(),RB,W,H,8,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};
    PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{const PF_Pixel8&e=(x+y<=4)?A:B;ok=ok&&std::memcmp(ob.data()+y*RB+x*4,&e,4)==0;}}for(int y=0;y<H;++y)for(int i=20;i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_corner_seed_case() {{
    constexpr int W=5,H=5,RB=44;const PF_Pixel16 A{{32768,1001,2002,3003}},B{{32768,4004,5005,6006}},C{{0,17,19,23}};std::vector<std::uint8_t>ib(RB*H,PAD),ob(RB*H,OUT_PAD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{PF_Pixel16 p=(x==0&&y==0)?A:(x==4&&y==4)?B:C;std::memcpy(ib.data()+y*RB+x*8,&p,8);}}PF_EffectWorld input{{ib.data(),RB,W,H,16,{{0,0,W,H}}}},output{{ob.data(),RB,W,H,16,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};
    PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{const PF_Pixel16&e=(x+y<=4)?A:B;ok=ok&&std::memcmp(ob.data()+y*RB+x*8,&e,8)==0;}}for(int y=0;y<H;++y)for(int i=40;i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_alpha0_rgb_eligibility_case() {{
    constexpr int W=5,H=3,RB=84;const PF_PixelFloat T{{0.0f,.875f,.625f,.375f}},S{{1.0f,.125f,.25f,.5f}},C{{0,0,0,0}};std::vector<std::uint8_t>ib(RB*H,PAD),ob(RB*H,OUT_PAD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{PF_PixelFloat p=(x==0&&y==1)?T:(x==4&&y==1)?S:C;std::memcpy(ib.data()+y*RB+x*16,&p,16);}}PF_EffectWorld input{{ib.data(),RB,W,H,32,{{0,0,W,H}}}},output{{ob.data(),RB,W,H,32,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};
    PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y)for(int x=0;x<W;++x)ok=ok&&std::memcmp(ob.data()+y*RB+x*16,&S,16)==0;for(int y=0;y<H;++y)for(int i=80;i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
template <typename Pixel> bool nonpositive_radius_case(short depth,double radius) {{
    constexpr int W=3,H=2,P=4;const int RB=W*sizeof(Pixel)+P;std::vector<std::uint8_t>ib(RB*H,PAD),ob(RB*H,OUT_PAD);
    for(int y=0;y<H;++y)for(int x=0;x<W;++x){{Pixel p{{}};if constexpr(sizeof(Pixel)==4)p=Pixel{{static_cast<std::uint8_t>((x+y)%2?0:255),static_cast<std::uint8_t>(10+x),static_cast<std::uint8_t>(20+y),static_cast<std::uint8_t>(30+x+y)}};else if constexpr(sizeof(Pixel)==8)p=Pixel{{static_cast<std::uint16_t>((x+y)%2?0:32768),static_cast<std::uint16_t>(1001+x),static_cast<std::uint16_t>(2002+y),static_cast<std::uint16_t>(3003+x+y)}};else p=Pixel{{(x+y)%2?0.0f:1.0f,.125f+x,.25f+y,.5f+x+y}};std::memcpy(ib.data()+y*RB+x*sizeof(Pixel),&p,sizeof(Pixel));}}
    PF_EffectWorld input{{ib.data(),RB,W,H,depth,{{0,0,W,H}}}},output{{ob.data(),RB,W,H,depth,{{0,0,W,H}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{depth,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=radius;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y)ok=ok&&std::memcmp(ob.data()+y*RB,ib.data()+y*RB,W*sizeof(Pixel))==0;for(int y=0;y<H;++y)for(int i=RB-P;i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_nonzero_extent_buffer_local_case() {{
    constexpr int W=2,H=1,RB=12;const PF_Pixel8 S{{255,10,20,30}},C{{0,101,202,77}};std::vector<std::uint8_t>ib(RB,0xA5),ob(RB,OUT_PAD);std::memcpy(ib.data(),&S,4);std::memcpy(ib.data()+4,&C,4);
    PF_EffectWorld input{{ib.data(),RB,W,H,8,{{100,200,102,201}}}},output{{ob.data(),RB,W,H,8,{{300,400,302,401}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=10;st.result_top=20;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=1.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;ok=ok&&std::memcmp(ob.data(),&S,4)==0&&std::memcmp(ob.data()+4,&S,4)==0&&ob[8]==OUT_PAD&&ob[9]==OUT_PAD&&ob[10]==OUT_PAD&&ob[11]==OUT_PAD;ok=ok&&po.result_rect.left==10&&po.result_rect.top==20&&po.result_rect.right==12&&po.result_rect.bottom==21;ok=ok&&input.extent_hint.left==100&&output.extent_hint.left==300;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_nonzero_extent_buffer_local_case() {{
    constexpr int W=2,H=1,RB=20;const PF_Pixel16 S{{32768,1001,2002,3003}},C{{0,50001,40002,30003}};std::vector<std::uint8_t>ib(RB,0xA5),ob(RB,OUT_PAD);std::memcpy(ib.data(),&S,8);std::memcpy(ib.data()+8,&C,8);
    PF_EffectWorld input{{ib.data(),RB,W,H,16,{{160,161,162,162}}}},output{{ob.data(),RB,W,H,16,{{320,321,322,322}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=10;st.result_top=20;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=1.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;ok=ok&&std::memcmp(ob.data(),&S,8)==0&&std::memcmp(ob.data()+8,&S,8)==0;for(int i=16;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==160&&output.extent_hint.left==320&&po.result_rect.left==10;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_nonzero_extent_buffer_local_case() {{
    constexpr int W=2,H=1,RB=36;const PF_PixelFloat S{{1.0f,.125f,.25f,.5f}},C{{0.0f,.875f,.625f,.375f}};std::vector<std::uint8_t>ib(RB,0xA5),ob(RB,OUT_PAD);std::memcpy(ib.data(),&S,16);std::memcpy(ib.data()+16,&C,16);
    PF_EffectWorld input{{ib.data(),RB,W,H,32,{{320,321,322,322}}}},output{{ob.data(),RB,W,H,32,{{640,641,642,642}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=10;st.result_top=20;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=1.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;ok=ok&&std::memcmp(ob.data(),&S,16)==0&&std::memcmp(ob.data()+16,&S,16)==0;for(int i=32;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==320&&output.extent_hint.left==640&&po.result_rect.left==10;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
template <typename Pixel> bool mixed_3x2_partial_case(short depth) {{
    constexpr int W=3,H=2;const int RB=W*sizeof(Pixel)+8;Pixel S{{}},M{{}},C{{}};if constexpr(sizeof(Pixel)==4){{S=Pixel{{255,10,20,30}};M=Pixel{{128,81,41,21}};}}else if constexpr(sizeof(Pixel)==8){{S=Pixel{{32768,1001,2002,3003}};M=Pixel{{16384,8001,7002,6003}};}}else{{S=Pixel{{1.0f,.125f,.25f,.5f}};M=Pixel{{.5f,.8f,.4f,.2f}};}}
    std::vector<std::uint8_t>ib(RB*H,0xA5),ob(RB*H,OUT_PAD);Pixel src[6]={{M,S,M,C,M,C}};for(int y=0;y<H;++y)for(int x=0;x<W;++x)std::memcpy(ib.data()+y*RB+x*sizeof(Pixel),&src[y*W+x],sizeof(Pixel));int il=depth*30,it=il+1,ol=depth*40,ot=ol+1;
    PF_EffectWorld input{{ib.data(),RB,W,H,depth,{{il,it,il+3,it+2}}}},output{{ob.data(),RB,W,H,depth,{{ol,ot,ol+3,ot+2}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=10;st.result_top=20;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{depth,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=1.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y){{for(int x=0;x<W;++x)ok=ok&&std::memcmp(ob.data()+y*RB+x*sizeof(Pixel),&S,sizeof(Pixel))==0;for(int i=W*sizeof(Pixel);i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;}}ok=ok&&input.extent_hint.left==il&&output.extent_hint.left==ol;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
template <typename Pixel> bool mixed_radius2_4x2_partial_case(short depth) {{
    constexpr int W=4,H=2;const int RB=W*sizeof(Pixel)+12;Pixel S{{}},M{{}},C{{}};if constexpr(sizeof(Pixel)==4){{S=Pixel{{255,31,61,91}};M=Pixel{{96,7,17,27}};}}else if constexpr(sizeof(Pixel)==8){{S=Pixel{{32768,3101,6102,9103}};M=Pixel{{8192,701,1702,2703}};}}else{{S=Pixel{{1.0f,.31f,.61f,.91f}};M=Pixel{{.25f,.07f,.17f,.27f}};}}
    std::vector<std::uint8_t>ib(RB*H,0xB6),ob(RB*H,OUT_PAD);Pixel src[8]={{S,M,C,M,C,M,C,M}};for(int y=0;y<H;++y)for(int x=0;x<W;++x)std::memcpy(ib.data()+y*RB+x*sizeof(Pixel),&src[y*W+x],sizeof(Pixel));int il=depth*50+3,it=depth*50+5,ol=depth*60+7,ot=depth*60+9;
    PF_EffectWorld input{{ib.data(),RB,W,H,depth,{{il,it,il+4,it+2}}}},output{{ob.data(),RB,W,H,depth,{{ol,ot,ol+4,ot+2}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=14;st.result_top=24;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{depth,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=2.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int y=0;y<H;++y){{for(int x=0;x<3;++x)ok=ok&&std::memcmp(ob.data()+y*RB+x*sizeof(Pixel),&S,sizeof(Pixel))==0;ok=ok&&std::memcmp(ob.data()+y*RB+3*sizeof(Pixel),&M,sizeof(Pixel))==0;for(int i=W*sizeof(Pixel);i<RB;++i)ok=ok&&ob[y*RB+i]==OUT_PAD;}}ok=ok&&input.extent_hint.left==il&&input.extent_hint.top==it&&output.extent_hint.left==ol&&output.extent_hint.top==ot;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_radius3_5x1_partial_case() {{
    constexpr int W=5,H=1,RB=88;const PF_PixelFloat S{{1.0f,.13f,.37f,.73f}},M1{{.5f,.2f,.3f,.4f}},M2{{.25f,.4f,.3f,.2f}},M3{{.75f,.6f,.2f,.1f}},M4{{.125f,.9f,.8f,.7f}};std::vector<std::uint8_t>ib(RB,0xD7),ob(RB,OUT_PAD);PF_PixelFloat src[5]={{S,M1,M2,M3,M4}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_PixelFloat),&src[x],sizeof(PF_PixelFloat));
    PF_EffectWorld input{{ib.data(),RB,W,H,32,{{2301,2303,2306,2304}}}},output{{ob.data(),RB,W,H,32,{{3307,3309,3312,3310}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=18;st.result_top=28;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<4;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_PixelFloat),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+4*sizeof(PF_PixelFloat),&M4,sizeof(M4))==0;for(int i=80;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==2301&&output.extent_hint.left==3307;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_radius3_5x1_partial_case() {{
    constexpr int W=5,H=1,RB=48;const PF_Pixel16 S{{32768,1301,3702,7303}},M1{{16384,2001,3002,4003}},M2{{8192,4001,3002,2003}},M3{{24576,6001,2002,1003}},M4{{4096,9001,8002,7003}};std::vector<std::uint8_t>ib(RB,0xE3),ob(RB,OUT_PAD);PF_Pixel16 src[5]={{S,M1,M2,M3,M4}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel16),&src[x],sizeof(PF_Pixel16));
    PF_EffectWorld input{{ib.data(),RB,W,H,16,{{1201,1203,1206,1204}}}},output{{ob.data(),RB,W,H,16,{{1707,1709,1712,1710}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=19;st.result_top=29;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<4;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel16),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+4*sizeof(PF_Pixel16),&M4,sizeof(M4))==0;for(int i=40;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==1201&&output.extent_hint.left==1707;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_radius3_5x1_partial_case() {{
    constexpr int W=5,H=1,RB=28;const PF_Pixel8 S{{255,13,37,73}},M1{{128,20,30,40}},M2{{64,40,30,20}},M3{{192,60,20,10}},M4{{32,90,80,70}};std::vector<std::uint8_t>ib(RB,0xF1),ob(RB,OUT_PAD);PF_Pixel8 src[5]={{S,M1,M2,M3,M4}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel8),&src[x],sizeof(PF_Pixel8));
    PF_EffectWorld input{{ib.data(),RB,W,H,8,{{601,603,606,604}}}},output{{ob.data(),RB,W,H,8,{{907,909,912,910}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=20;st.result_top=30;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<4;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel8),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+4*sizeof(PF_Pixel8),&M4,sizeof(M4))==0;for(int i=20;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==601&&output.extent_hint.left==907;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_radius4_6x1_partial_case() {{
    constexpr int W=6,H=1,RB=32;const PF_Pixel8 S{{255,11,47,89}},M1{{128,21,31,41}},M2{{64,42,32,22}},M3{{192,63,23,13}},M4{{96,74,54,34}},M5{{16,95,85,75}};std::vector<std::uint8_t>ib(RB,0x9D),ob(RB,OUT_PAD);PF_Pixel8 src[6]={{S,M1,M2,M3,M4,M5}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel8),&src[x],sizeof(PF_Pixel8));
    PF_EffectWorld input{{ib.data(),RB,W,H,8,{{701,703,707,704}}}},output{{ob.data(),RB,W,H,8,{{1007,1009,1013,1010}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=21;st.result_top=31;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<5;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel8),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+5*sizeof(PF_Pixel8),&M5,sizeof(M5))==0;for(int i=24;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==701&&output.extent_hint.left==1007;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_radius4_6x1_partial_case() {{
    constexpr int W=6,H=1,RB=56;const PF_Pixel16 S{{32768,1101,4702,8903}},M1{{16384,2101,3102,4103}},M2{{8192,4201,3202,2203}},M3{{24576,6301,2302,1303}},M4{{12288,7401,5402,3403}},M5{{2048,9501,8502,7503}};std::vector<std::uint8_t>ib(RB,0x8B),ob(RB,OUT_PAD);PF_Pixel16 src[6]={{S,M1,M2,M3,M4,M5}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel16),&src[x],sizeof(PF_Pixel16));
    PF_EffectWorld input{{ib.data(),RB,W,H,16,{{1401,1403,1407,1404}}}},output{{ob.data(),RB,W,H,16,{{2007,2009,2013,2010}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=22;st.result_top=32;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<5;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel16),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+5*sizeof(PF_Pixel16),&M5,sizeof(M5))==0;for(int i=48;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==1401&&output.extent_hint.left==2007;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_radius4_6x1_partial_case() {{
    constexpr int W=6,H=1,RB=104;const PF_PixelFloat S{{1.0f,.11f,.47f,.89f}},M1{{.5f,.21f,.31f,.41f}},M2{{.25f,.42f,.32f,.22f}},M3{{.75f,.63f,.23f,.13f}},M4{{.375f,.74f,.54f,.34f}},M5{{.0625f,.95f,.85f,.75f}};std::vector<std::uint8_t>ib(RB,0xA7),ob(RB,OUT_PAD);PF_PixelFloat src[6]={{S,M1,M2,M3,M4,M5}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_PixelFloat),&src[x],sizeof(PF_PixelFloat));
    PF_EffectWorld input{{ib.data(),RB,W,H,32,{{2801,2803,2807,2804}}}},output{{ob.data(),RB,W,H,32,{{4007,4009,4013,4010}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=23;st.result_top=33;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<5;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_PixelFloat),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+5*sizeof(PF_PixelFloat),&M5,sizeof(M5))==0;for(int i=96;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==2801&&output.extent_hint.left==4007;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_fractional_radius_2_01_5x1_case() {{
    constexpr int W=5,H=1,RB=28;const PF_Pixel8 S{{255,17,43,97}},M1{{127,23,33,43}},M2{{63,44,34,24}},M3{{191,65,25,15}},M4{{31,96,86,76}};std::vector<std::uint8_t>ib(RB,0xC9),ob(RB,OUT_PAD);PF_Pixel8 src[5]={{S,M1,M2,M3,M4}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel8),&src[x],sizeof(PF_Pixel8));
    PF_EffectWorld input{{ib.data(),RB,W,H,8,{{801,803,806,804}}}},output{{ob.data(),RB,W,H,8,{{1107,1109,1112,1110}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=24;st.result_top=34;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=2.01;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<4;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel8),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+4*sizeof(PF_Pixel8),&M4,sizeof(M4))==0;for(int i=20;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==801&&output.extent_hint.left==1107;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_fractional_radius_2_5_5x1_case() {{
    constexpr int W=5,H=1,RB=88;const PF_PixelFloat S{{1.0f,.19f,.41f,.83f}},M1{{.5f,.27f,.37f,.47f}},M2{{.25f,.48f,.38f,.28f}},M3{{.75f,.69f,.29f,.19f}},M4{{.125f,.98f,.88f,.78f}};std::vector<std::uint8_t>ib(RB,0xD2),ob(RB,OUT_PAD);PF_PixelFloat src[5]={{S,M1,M2,M3,M4}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_PixelFloat),&src[x],sizeof(PF_PixelFloat));
    PF_EffectWorld input{{ib.data(),RB,W,H,32,{{2901,2903,2906,2904}}}},output{{ob.data(),RB,W,H,32,{{4107,4109,4112,4110}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=25;st.result_top=35;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=2.5;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<4;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_PixelFloat),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+4*sizeof(PF_PixelFloat),&M4,sizeof(M4))==0;for(int i=80;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==2901&&output.extent_hint.left==4107;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_fractional_radius_3_25_6x1_case() {{
    constexpr int W=6,H=1,RB=56;const PF_Pixel16 S{{32768,1501,5102,8703}},M1{{16384,2501,3502,4503}},M2{{8192,4601,3602,2603}},M3{{24576,6701,2702,1703}},M4{{12288,7801,5802,3803}},M5{{1024,9901,8902,7903}};std::vector<std::uint8_t>ib(RB,0xE6),ob(RB,OUT_PAD);PF_Pixel16 src[6]={{S,M1,M2,M3,M4,M5}};for(int x=0;x<W;++x)std::memcpy(ib.data()+x*sizeof(PF_Pixel16),&src[x],sizeof(PF_Pixel16));
    PF_EffectWorld input{{ib.data(),RB,W,H,16,{{1501,1503,1507,1504}}}},output{{ob.data(),RB,W,H,16,{{2107,2109,2113,2110}}}};State st{{&input,&output}};st.width=W;st.height=H;st.result_left=26;st.result_top=36;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=3.25;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;
    for(int x=0;x<5;++x)ok=ok&&std::memcmp(ob.data()+x*sizeof(PF_Pixel16),&S,sizeof(S))==0;ok=ok&&std::memcmp(ob.data()+5*sizeof(PF_Pixel16),&M5,sizeof(M5))==0;for(int i=48;i<RB;++i)ok=ok&&ob[i]==OUT_PAD;ok=ok&&input.extent_hint.left==1501&&output.extent_hint.left==2107;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf8_empty_width_case() {{
    constexpr int W=0,H=1,RB=8;std::vector<std::uint8_t>ib(RB,0xA3),ob(RB,0xB4);PF_EffectWorld input{{ib.data(),RB,W,H,8,{{951,953,951,954}}}},output{{ob.data(),RB,W,H,8,{{1257,1259,1257,1260}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{8,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;for(auto b:ob)ok=ok&&b==0xB4;ok=ok&&input.extent_hint.left==951&&output.extent_hint.left==1257;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf16_empty_height_case() {{
    constexpr int W=1,H=0,RB=16;std::vector<std::uint8_t>ib(RB,0xA8),ob(RB,0xBD);PF_EffectWorld input{{ib.data(),RB,W,H,16,{{1551,1553,1552,1553}}}},output{{ob.data(),RB,W,H,16,{{2157,2159,2158,2159}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{16,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;for(auto b:ob)ok=ok&&b==0xBD;ok=ok&&input.extent_hint.top==1553&&output.extent_hint.top==2159;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool pf32_empty_both_case() {{
    constexpr int W=0,H=0,RB=24;std::vector<std::uint8_t>ib(RB,0xAC),ob(RB,0xCE);PF_EffectWorld input{{ib.data(),RB,W,H,32,{{3051,3053,3051,3053}}}},output{{ob.data(),RB,W,H,32,{{4257,4259,4257,4259}}}};State st{{&input,&output}};st.width=W;st.height=H;PF_InData in{{&st,0,1,1,nullptr}};PF_OutData out{{}};PF_RenderRequest req{{false}};PF_PreRenderInput pi{{req}};PF_PreRenderOutput po{{}};PF_PreRenderCallbacks pcb{{pre_checkout}};PF_PreRenderExtra pre{{&pi,&po,&pcb}};
    if(EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre)!=PF_Err_NONE)return false;PF_SmartRenderInput ri{{32,po.pre_render_data}};PF_SmartRenderCallbacks rcb{{pixels_checkout,output_checkout,checkin}};PF_SmartRenderExtra render{{&ri,&rcb}};g_radius=4.0;bool ok=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&render)==PF_Err_NONE;for(auto b:ob)ok=ok&&b==0xCE;ok=ok&&input.extent_hint.left==3051&&input.extent_hint.top==3053&&output.extent_hint.left==4257&&output.extent_hint.top==4259;if(po.delete_pre_render_data_func)po.delete_pre_render_data_func(po.pre_render_data);return ok;
}}
bool malformed_world_guard_cases() {{
    std::uint8_t input_bytes[64]={{}},output_bytes[64]={{}};size_t count=999;
    PF_EffectWorld input{{input_bytes,16,2,2,32,{{0,0,2,2}}}},output{{output_bytes,32,2,2,32,{{0,0,2,2}}}};
    OLMToonDilateInfo info{{1.0,2.0}};
    bool ok=RenderWorld(nullptr,&output,info,32)==PF_Err_BAD_CALLBACK_PARAM;
    ok=ok&&RenderWorld(&input,nullptr,info,32)==PF_Err_BAD_CALLBACK_PARAM;
    ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    input.rowbytes=32;output.rowbytes=31;ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    output.rowbytes=32;input.data=nullptr;ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    input.data=input_bytes;input.width=1;ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    input.width=2;output.width=-1;ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    input.width=std::numeric_limits<A_long>::max();input.height=std::numeric_limits<A_long>::max();output=input;
    ok=ok&&ValidateWorlds<PF_PixelFloat>(&input,&output,&count)==PF_Err_BAD_CALLBACK_PARAM;
    PF_EffectWorld empty{{nullptr,0,0,1,32,{{0,0,0,1}}}};count=999;
    ok=ok&&ValidateWorlds<PF_PixelFloat>(&empty,&empty,&count)==PF_Err_NONE&&count==0;
    return ok;
}}
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
    bool positive8 = positive_radius_case<PF_Pixel8>(8, 1.0);
    bool positive16 = positive_radius_case<PF_Pixel16>(16, 1.0);
    bool positive32 = positive_radius_case<PF_PixelFloat>(32, 1.0);
    bool positive8Radius2 = positive_radius_case<PF_Pixel8>(8, 2.0);
    bool positive16Radius2 = positive_radius_case<PF_Pixel16>(16, 2.0);
    bool positive32Radius2 = positive_radius_case<PF_PixelFloat>(32, 2.0);
    bool pf8Radius3Tie = pf8_radius3_boundary_tie_case();
    bool pf16Radius3Tie = pf16_radius3_boundary_tie_case();
    bool pf32Radius3Tie = pf32_radius3_boundary_tie_case();
    bool pf32Corner = pf32_corner_seed_case();
    bool pf8Corner = pf8_corner_seed_case();
    bool pf16Corner = pf16_corner_seed_case();
    bool pf32Alpha0 = pf32_alpha0_rgb_eligibility_case();
    bool nonpositive=nonpositive_radius_case<PF_Pixel8>(8,0.0)&&nonpositive_radius_case<PF_Pixel8>(8,-1.0)&&nonpositive_radius_case<PF_Pixel16>(16,0.0)&&nonpositive_radius_case<PF_Pixel16>(16,-1.0)&&nonpositive_radius_case<PF_PixelFloat>(32,0.0)&&nonpositive_radius_case<PF_PixelFloat>(32,-1.0);
    bool nonzeroExtent=pf8_nonzero_extent_buffer_local_case();
    bool nonzeroExtent16=pf16_nonzero_extent_buffer_local_case();bool nonzeroExtent32=pf32_nonzero_extent_buffer_local_case();
    bool mixed3x2=mixed_3x2_partial_case<PF_Pixel8>(8)&&mixed_3x2_partial_case<PF_Pixel16>(16)&&mixed_3x2_partial_case<PF_PixelFloat>(32);
    bool mixedRadius2=mixed_radius2_4x2_partial_case<PF_Pixel8>(8)&&mixed_radius2_4x2_partial_case<PF_Pixel16>(16)&&mixed_radius2_4x2_partial_case<PF_PixelFloat>(32);
    bool pf32Radius3Partial=pf32_radius3_5x1_partial_case();
    bool pf16Radius3Partial=pf16_radius3_5x1_partial_case();
    bool pf8Radius3Partial=pf8_radius3_5x1_partial_case();
    bool pf8Radius4Partial=pf8_radius4_6x1_partial_case();
    bool pf16Radius4Partial=pf16_radius4_6x1_partial_case();
    bool pf32Radius4Partial=pf32_radius4_6x1_partial_case();
    bool pf8Fractional=pf8_fractional_radius_2_01_5x1_case();
    bool pf32Fractional=pf32_fractional_radius_2_5_5x1_case();
    bool pf16Fractional=pf16_fractional_radius_3_25_6x1_case();
    bool pf8Empty=pf8_empty_width_case();
    bool pf16EmptyHeight=pf16_empty_height_case();
    bool pf32EmptyBoth=pf32_empty_both_case();
    bool malformedWorldGuards=malformed_world_guard_cases();
    if (!(positive8 && positive16 && positive32 && positive8Radius2 && positive16Radius2 && positive32Radius2 && pf8Radius3Tie && pf16Radius3Tie && pf32Radius3Tie && pf8Corner && pf16Corner && pf32Corner && pf32Alpha0 && nonpositive && nonzeroExtent && nonzeroExtent16 && nonzeroExtent32 && mixed3x2 && mixedRadius2 && pf32Radius3Partial && pf16Radius3Partial && pf8Radius3Partial && pf8Radius4Partial && pf16Radius4Partial && pf32Radius4Partial && pf8Fractional && pf32Fractional && pf16Fractional && pf8Empty && pf16EmptyHeight && pf32EmptyBoth && malformedWorldGuards)) return 60;
    std::printf("],\\\"positive_radius_fixture\\\":{{\\\"radius\\\":1,\\\"PF8_exact\\\":true,\\\"PF16_exact\\\":true,\\\"PF32_exact\\\":true}},\\\"PF8_radius2_shape_fixture\\\":{{\\\"dimensions\\\":[5,3],\\\"radius\\\":2,\\\"visible_argb_exact\\\":true}},\\\"PF16_radius2_shape_fixture\\\":{{\\\"dimensions\\\":[5,3],\\\"radius\\\":2,\\\"visible_exact_4_word\\\":true}},\\\"PF32_radius2_shape_fixture\\\":{{\\\"dimensions\\\":[5,3],\\\"radius\\\":2,\\\"visible_exact_4_word\\\":true}},\\\"PF8_radius3_boundary_tie_fixture\\\":{{\\\"dimensions\\\":[7,3],\\\"radius\\\":3,\\\"scan_asymmetric_tie_exact\\\":true}},\\\"PF16_radius3_boundary_tie_fixture\\\":{{\\\"dimensions\\\":[7,3],\\\"radius\\\":3,\\\"scan_asymmetric_tie_exact\\\":true}},\\\"PF32_radius3_boundary_tie_fixture\\\":{{\\\"dimensions\\\":[7,3],\\\"radius\\\":3,\\\"raw_float32_exact\\\":true}}}}\\n"); return 0;
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
    verify_fixture_identity()
    with tempfile.TemporaryDirectory(prefix="olm_toondilate_mac_smartrender_") as name:
        executable, build = compile_probe(Path(name))
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: adapter probe exited {run.returncode}: {run.stderr.strip()}")
    report = json.loads(run.stdout)
    report["build"] = build
    report["production_source"] = str(SOURCE.relative_to(ROOT))
    report["corner_seed_production"] = {
        "dimensions": [5, 5],
        "radius": 4,
        "PF8_dynamic_effectmain_exact": True,
        "PF16_dynamic_effectmain_exact": True,
        "PF32_dynamic_effectmain_exact": True,
        "all_depths_padding_preserved": True,
    }
    report["nonpositive_radius_production"] = {"radii": [0.0, -1.0], "PF8_exact": True, "PF16_exact": True, "PF32_exact": True}
    report["nonzero_extent_pf8_production"] = {"input_extent": [100, 200, 102, 201], "output_extent": [300, 400, 302, 401], "smartpre_result_rect": [10, 20, 12, 21], "coordinate_contract": "buffer-local", "typed_bytes_exact": True}
    report["nonzero_extent_pf16_production"] = {"input_extent": [160, 161, 162, 162], "output_extent": [320, 321, 322, 322], "rowbytes": 20, "coordinate_contract": "buffer-local", "typed_bytes_exact": True}
    report["nonzero_extent_pf32_production"] = {"input_extent": [320, 321, 322, 322], "output_extent": [640, 641, 642, 642], "rowbytes": 36, "coordinate_contract": "buffer-local", "raw_float32_exact": True}
    report["mixed_3x2_partial_production"] = {"radius": 1, "dimensions": [3, 2], "PF8_rowbytes": 20, "PF16_rowbytes": 32, "PF32_rowbytes": 56, "mixed_alpha_frontier_propagated": True, "all_depths_typed_bytes_padding_exact": True}
    report["mixed_radius2_4x2_partial_production"] = {"radius": 2, "dimensions": [4, 2], "PF8_rowbytes": 28, "PF16_rowbytes": 44, "PF32_rowbytes": 76, "distance_2_frontier_propagated": True, "distance_3_mixed_rgba_preserved": True, "nonzero_extents_padding_all_depths_exact": True}
    report["pf32_radius3_5x1_partial_production"] = {"radius": 3, "dimensions": [5, 1], "rowbytes": 88, "distance_3_frontier_propagated": True, "distance_4_raw_float32_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf16_radius3_5x1_partial_production"] = {"radius": 3, "dimensions": [5, 1], "rowbytes": 48, "distance_3_frontier_propagated": True, "distance_4_raw_uint16_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf8_radius3_5x1_partial_production"] = {"radius": 3, "dimensions": [5, 1], "rowbytes": 28, "distance_3_frontier_propagated": True, "distance_4_raw_uint8_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf8_radius4_6x1_partial_production"] = {"radius": 4, "dimensions": [6, 1], "rowbytes": 32, "distance_4_frontier_propagated": True, "distance_5_raw_uint8_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf16_radius4_6x1_partial_production"] = {"radius": 4, "dimensions": [6, 1], "rowbytes": 56, "distance_4_frontier_propagated": True, "distance_5_raw_uint16_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf32_radius4_6x1_partial_production"] = {"radius": 4, "dimensions": [6, 1], "rowbytes": 104, "distance_4_frontier_propagated": True, "distance_5_raw_float32_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf8_fractional_radius_2_01_5x1_production"] = {"requested_radius": 2.01, "effective_radius": 3, "dimensions": [5, 1], "rowbytes": 28, "ceil_frontier_3_propagated": True, "distance_4_raw_uint8_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf32_fractional_radius_2_5_5x1_production"] = {"requested_radius": 2.5, "effective_radius": 3, "dimensions": [5, 1], "rowbytes": 88, "ceil_frontier_3_propagated": True, "distance_4_raw_float32_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf16_fractional_radius_3_25_6x1_production"] = {"requested_radius": 3.25, "effective_radius": 4, "dimensions": [6, 1], "rowbytes": 56, "ceil_frontier_4_propagated": True, "distance_5_raw_uint16_preserved": True, "nonzero_extents_padding_exact": True}
    report["pf8_empty_width_production"] = {"dimensions": [0, 1], "radius": 4, "rowbytes": 8, "empty_output_padding_unchanged": True, "nonzero_origin_zero_width_extents_unchanged": True}
    report["pf16_empty_height_production"] = {"dimensions": [1, 0], "radius": 4, "rowbytes": 16, "empty_output_backing_unchanged": True, "nonzero_origin_zero_height_extents_unchanged": True}
    report["pf32_empty_both_production"] = {"dimensions": [0, 0], "radius": 4, "rowbytes": 24, "empty_output_backing_unchanged": True, "nonzero_origin_zero_size_extents_unchanged": True}
    report["fixture_provenance"] = {
        "PF8": "refs/conformance/olmtoondilate_pf8_tie_break_20260717.json",
        "PF8_radius2": "refs/conformance/olmtoondilate_pf8_radius2_shape_20260805.json",
        "PF8_radius3_boundary_tie": "refs/conformance/olmtoondilate_pf8_radius3_boundary_tie_20260805.json",
        "PF16": "refs/conformance/olmtoondilate_pf16_2d_propagation_followup_20260716.json",
        "PF16_radius2": "refs/conformance/olmtoondilate_pf16_radius2_shape_20260805.json",
        "PF16_radius3_boundary_tie": "refs/conformance/olmtoondilate_pf16_radius3_boundary_tie_20260805.json",
        "PF32": "refs/conformance/olmtoondilate_pf32_seed_propagation_matrix_20260717.json",
        "PF32_radius3_boundary_tie": "refs/conformance/olmtoondilate_pf32_radius3_boundary_tie_20260805.json",
        "corner_seed_all_depths": "refs/conformance/olmtoondilate_corner_seed_all_depths_20260805.json",
        "alpha0_rgb_eligibility_all_depths": "refs/conformance/olmtoondilate_alpha0_rgb_eligibility_all_depths_20260805.json",
        "nonpositive_radius_all_depths": "refs/conformance/olmtoondilate_nonpositive_radius_all_depths_20260805.json",
        "actual_entry_radius2_mixed_4x2": "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json",
    }
    report["claim_boundary"] = (
        "Mac-local source-included SmartRender adapter proof. Positive-radius expected behavior is "
        "bounded by the cited actual-AEX typed worker fixtures; no Mac AE host-exact expansion claim."
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
