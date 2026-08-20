#!/usr/bin/env python3
"""Hostless real-SDK EffectMain gate for DirectionalBlur generic Back-only.

This compiles the production translation unit into a small fake AE host.  It
does not launch After Effects and does not enable the production test seam.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"


CPP = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <type_traits>
#include <vector>
#include <sys/mman.h>

#include "__PRODUCTION__"

#define REQUIRE(condition, code) do { if (!(condition)) { \
  std::fprintf(stderr, "FAIL code=%d line=%d\n", (code), __LINE__); return (code); \
} } while (0)

static constexpr std::uint8_t kInputCanary = 0xa5;
static constexpr std::uint8_t kOutputCanary = 0xee;
static constexpr PF_Err kCheckoutFailure = 710;
static constexpr PF_Err kCheckinFailure = 810;
static constexpr PF_Err kLayerCheckinFailure = 811;
static constexpr PF_Err kOutputFailure = 910;

struct HostState {
  PF_EffectWorld* input = nullptr;
  PF_EffectWorld* output = nullptr;
  PF_ParamDef* defs = nullptr;
  PF_PixelFormat format = PF_PixelFormat_INVALID;
  int pre_calls = 0;
  int pre_input_calls = 0;
  int pre_noise_calls = 0;
  int pixel_calls = 0;
  int pixel_input_calls = 0;
  int pixel_noise_calls = 0;
  int output_checkout = 0;
  int layer_checkin = 0;
  int param_checkout_attempts = 0;
  int param_checkin_attempts = 0;
  int acquire = 0;
  int release = 0;
  int world_calls = 0;
  int back_seen = -1;
  int fail_checkout_index = -1;
  int fail_checkin_id = -1;
  int fail_layer_checkin_id = -1;
  bool fail_output = false;
  bool preserve = true;
  bool full_request = true;
  std::vector<int> checkout_order;
  std::vector<int> checkin_order;
  std::vector<int> layer_checkin_order;
};

static HostState* g_host = nullptr;
static PF_WorldSuite2 g_world_suite = {};

static PF_Err GetPixelFormat(const PF_EffectWorld*, PF_PixelFormat* format) {
  if (!g_host || !format) return PF_Err_BAD_CALLBACK_PARAM;
  ++g_host->world_calls;
  *format = g_host->format;
  return PF_Err_NONE;
}

static SPErr AcquireSuite(const char* name, int32 version, const void** suite) {
  if (!g_host || !suite) return kSPBadParameterError;
  ++g_host->acquire;
  if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
    g_world_suite.PF_NewWorld = nullptr;
    g_world_suite.PF_DisposeWorld = nullptr;
    g_world_suite.PF_GetPixelFormat = GetPixelFormat;
    *suite = &g_world_suite;
    return kSPNoError;
  }
  *suite = nullptr;
  return kSPBadParameterError;
}

static SPErr ReleaseSuite(const char*, int32) {
  if (g_host) ++g_host->release;
  return kSPNoError;
}

static PF_Err CheckoutParam(PF_ProgPtr effect_ref, PF_ParamIndex index,
                            A_long, A_long, A_u_long, PF_ParamDef* param) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !param || index <= OLMDIRECTIONALBLUR_INPUT ||
      index >= OLMDIRECTIONALBLUR_NUM_PARAMS) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->param_checkout_attempts;
  if (index == state->fail_checkout_index) return kCheckoutFailure;
  *param = state->defs[index];
  state->checkout_order.push_back(index);
  if (index == OLMDIRECTIONALBLUR_BACK_STRENGTH) {
    state->back_seen = param->u.sd.value;
  }
  return PF_Err_NONE;
}

static PF_Err CheckinParam(PF_ProgPtr effect_ref, PF_ParamDef* param) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !param) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->param_checkin_attempts;
  state->checkin_order.push_back(param->uu.id);
  return param->uu.id == state->fail_checkin_id ? kCheckinFailure : PF_Err_NONE;
}

static PF_Err PreCheckout(PF_ProgPtr effect_ref, PF_ParamIndex index,
                          A_long checkout_id, const PF_RenderRequest* request,
                          A_long, A_long, A_u_long, PF_CheckoutResult* result) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !request || !result || index != checkout_id) {
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  ++state->pre_calls;
  state->preserve = state->preserve && request->preserve_rgb_of_zero_alpha;
  state->full_request = state->full_request && request->rect.left == 0 &&
    request->rect.top == 0 && request->rect.right == state->input->width &&
    request->rect.bottom == state->input->height;
  if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) {
    ++state->pre_noise_calls;
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  if (index != OLMDIRECTIONALBLUR_INPUT) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->pre_input_calls;
  std::memset(result, 0, sizeof(*result));
  result->result_rect = {0, 0, state->input->width, state->input->height};
  result->max_result_rect = result->result_rect;
  result->ref_width = state->input->width;
  result->ref_height = state->input->height;
  return PF_Err_NONE;
}

static PF_Err CheckoutPixels(PF_ProgPtr effect_ref, A_long checkout_id,
                             PF_EffectWorld** world) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !world) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->pixel_calls;
  if (checkout_id == OLMDIRECTIONALBLUR_INPUT) {
    ++state->pixel_input_calls;
    *world = state->input;
    return PF_Err_NONE;
  }
  if (checkout_id == OLMDIRECTIONALBLUR_NOISE_LAYER) {
    ++state->pixel_noise_calls;
    *world = nullptr;
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  return PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err CheckinPixels(PF_ProgPtr effect_ref, A_long checkout_id) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->layer_checkin;
  state->layer_checkin_order.push_back((int)checkout_id);
  if (checkout_id != OLMDIRECTIONALBLUR_INPUT) return PF_Err_BAD_CALLBACK_PARAM;
  return checkout_id == state->fail_layer_checkin_id
    ? kLayerCheckinFailure : PF_Err_NONE;
}

static PF_Err CheckoutOutput(PF_ProgPtr effect_ref, PF_EffectWorld** world) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !world) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->output_checkout;
  if (state->fail_output) return kOutputFailure;
  *world = state->output;
  return PF_Err_NONE;
}

static SPBasicSuite MakeBasic() {
  SPBasicSuite basic = {};
  basic.AcquireSuite = AcquireSuite;
  basic.ReleaseSuite = ReleaseSuite;
  return basic;
}

static PF_InData MakeInData(HostState* state, SPBasicSuite* basic) {
  PF_InData in = {};
  in.effect_ref = reinterpret_cast<PF_ProgPtr>(state);
  in.pica_basicP = basic;
  in.current_time = 7;
  in.time_step = 1;
  in.time_scale = 24;
  in.width = state->input->width;
  in.height = state->input->height;
  in.output_origin_x = 0;
  in.output_origin_y = 0;
  in.downsample_x = {1, 1};
  in.downsample_y = {1, 1};
  in.inter.checkout_param = CheckoutParam;
  in.inter.checkin_param = CheckinParam;
  return in;
}

static PF_EffectWorld MakeWorld(void* data, A_long rowbytes, A_long width,
                                A_long height, short depth) {
  PF_EffectWorld world = {};
  world.data = reinterpret_cast<PF_PixelPtr>(data);
  world.rowbytes = rowbytes;
  world.width = width;
  world.height = height;
  world.extent_hint = {0, 0, width, height};
  world.origin_x = 0;
  world.origin_y = 0;
  world.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
  return world;
}

static void InitParams(PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS],
                       PF_ParamDef* params[OLMDIRECTIONALBLUR_NUM_PARAMS],
                       const PF_EffectWorld& input, int back_strength) {
  std::memset(defs, 0, sizeof(PF_ParamDef) * OLMDIRECTIONALBLUR_NUM_PARAMS);
  for (int i = 0; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
    defs[i].uu.id = i;
    params[i] = &defs[i];
  }
  defs[OLMDIRECTIONALBLUR_INPUT].u.ld = input;
  defs[OLMDIRECTIONALBLUR_ANGLE].u.ad.value =
    static_cast<PF_Fixed>(std::lround(37.25 * 65536.0));
  defs[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value = 0.75;
  defs[OLMDIRECTIONALBLUR_SIZE_VARIATION].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value = 0;
  defs[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE].u.sd.value = 0;
  defs[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value = back_strength;
  defs[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE].u.sd.value = 0;
  defs[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_NOISE_VARIATION].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value = 1;
  defs[OLMDIRECTIONALBLUR_NOISE_LAYER].u.ld.dephault = FALSE;
  defs[OLMDIRECTIONALBLUR_SEED].u.sd.value = 1;
  defs[OLMDIRECTIONALBLUR_NOISE_OFFSET].u.ad.value = 0;
  defs[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value = 10.0;
}

static std::vector<int> ExpectedParams() {
  std::vector<int> result;
  for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) result.push_back(i);
  return result;
}

static PF_Err InvokeClassic(HostState* state, SPBasicSuite* basic,
                            PF_ParamDef* params[OLMDIRECTIONALBLUR_NUM_PARAMS]) {
  g_host = state;
  PF_InData in = MakeInData(state, basic);
  PF_OutData out = {};
  return EffectMain(PF_Cmd_RENDER, &in, &out, params, state->output, nullptr);
}

static PF_Err InvokeSmart(HostState* state, SPBasicSuite* basic, short depth,
                          bool full_request, PF_Err* pre_error = nullptr) {
  g_host = state;
  PF_InData in = MakeInData(state, basic);
  PF_OutData out = {};
  PF_PreRenderInput pre_input = {};
  pre_input.bitdepth = depth;
  pre_input.output_request.rect = full_request
    ? PF_LRect{0, 0, state->input->width, state->input->height}
    : PF_LRect{0, 0, state->input->width - 1, state->input->height};
  PF_PreRenderOutput pre_output = {};
  PF_PreRenderCallbacks pre_callbacks = {};
  pre_callbacks.checkout_layer = PreCheckout;
  PF_PreRenderExtra pre_extra = {&pre_input, &pre_output, &pre_callbacks};
  const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                    nullptr, nullptr, &pre_extra);
  if (pre_error) *pre_error = pre_err;
  if (pre_err) {
    if (pre_output.delete_pre_render_data_func && pre_output.pre_render_data) {
      pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
    }
    return pre_err;
  }
  PF_SmartRenderInput smart_input = {};
  smart_input.bitdepth = depth;
  smart_input.output_request = pre_input.output_request;
  smart_input.pre_render_data = pre_output.pre_render_data;
  PF_SmartRenderCallbacks smart_callbacks = {};
  smart_callbacks.checkout_layer_pixels = CheckoutPixels;
  smart_callbacks.checkin_layer_pixels = CheckinPixels;
  smart_callbacks.checkout_output = CheckoutOutput;
  PF_SmartRenderExtra smart_extra = {&smart_input, &smart_callbacks};
  const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                                      nullptr, nullptr, &smart_extra);
  if (pre_output.delete_pre_render_data_func && pre_output.pre_render_data) {
    pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
  }
  return smart_err;
}

template <class Pixel> struct Fixture {
  int width;
  int height;
  int active;
  int input_rowbytes;
  int classic_rowbytes;
  int smart_rowbytes;
  std::vector<std::uint8_t> input;
  std::vector<std::uint8_t> original;
  std::vector<std::uint8_t> classic;
  std::vector<std::uint8_t> smart;
  PF_EffectWorld input_world;
  PF_EffectWorld classic_world;
  PF_EffectWorld smart_world;

  Fixture(int w, int h, short depth)
      : width(w), height(h), active(w * (int)sizeof(Pixel)),
        input_rowbytes(active + 5), classic_rowbytes(active + 11),
        smart_rowbytes(active + 17),
        input((std::size_t)input_rowbytes * h, kInputCanary),
        classic((std::size_t)classic_rowbytes * h, kOutputCanary),
        smart((std::size_t)smart_rowbytes * h, kOutputCanary) {
    for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
      Pixel pixel = {};
      if constexpr (std::is_same_v<Pixel, PF_Pixel8>) {
        pixel = {static_cast<A_u_char>(96 + ((x * 3 + y * 5) % 160)),
                 static_cast<A_u_char>((x * 31 + y * 7 + 11) & 255),
                 static_cast<A_u_char>((x * 3 + y * 19 + 23) & 255),
                 static_cast<A_u_char>((x * 11 + y * 5 + 47) & 255)};
      } else if constexpr (std::is_same_v<Pixel, PF_Pixel16>) {
        pixel = {static_cast<A_u_short>(12000 + ((x * 97 + y * 53) % 20000)),
                 static_cast<A_u_short>((x * 919 + y * 211 + 1000) & 32767),
                 static_cast<A_u_short>((x * 101 + y * 677 + 2000) & 32767),
                 static_cast<A_u_short>((x * 431 + y * 307 + 3000) & 32767)};
      } else {
        pixel = {0.35f + float((x * 3 + y * 5) % 50) / 100.0f,
                 float((x * 31 + y * 7 + 11) & 255) / 255.0f,
                 float((x * 3 + y * 19 + 23) & 255) / 255.0f,
                 float((x * 11 + y * 5 + 47) & 255) / 255.0f};
      }
      std::memcpy(input.data() + (std::size_t)y * input_rowbytes +
                    (std::size_t)x * sizeof(Pixel), &pixel, sizeof(pixel));
    }
    original = input;
    input_world = MakeWorld(input.data(), input_rowbytes, width, height, depth);
    classic_world = MakeWorld(classic.data(), classic_rowbytes, width, height, depth);
    smart_world = MakeWorld(smart.data(), smart_rowbytes, width, height, depth);
  }

  void reset_classic() { std::fill(classic.begin(), classic.end(), kOutputCanary); }
  void reset_smart() { std::fill(smart.begin(), smart.end(), kOutputCanary); }

  bool input_unchanged() const { return input == original; }
  bool classic_padding() const {
    for (int y = 0; y < height; ++y) for (int x = active; x < classic_rowbytes; ++x)
      if (classic[(std::size_t)y * classic_rowbytes + x] != kOutputCanary) return false;
    return true;
  }
  bool smart_padding() const {
    for (int y = 0; y < height; ++y) for (int x = active; x < smart_rowbytes; ++x)
      if (smart[(std::size_t)y * smart_rowbytes + x] != kOutputCanary) return false;
    return true;
  }
  bool classic_changed() const {
    for (int y = 0; y < height; ++y) for (int x = 0; x < active; ++x)
      if (classic[(std::size_t)y * classic_rowbytes + x] != kOutputCanary) return true;
    return false;
  }
  bool smart_changed() const {
    for (int y = 0; y < height; ++y) for (int x = 0; x < active; ++x)
      if (smart[(std::size_t)y * smart_rowbytes + x] != kOutputCanary) return true;
    return false;
  }
  bool classic_untouched() const {
    return std::all_of(classic.begin(), classic.end(),
                       [](std::uint8_t v) { return v == kOutputCanary; });
  }
  bool smart_untouched() const {
    return std::all_of(smart.begin(), smart.end(),
                       [](std::uint8_t v) { return v == kOutputCanary; });
  }
  std::vector<std::uint8_t> packed_input() const {
    std::vector<std::uint8_t> result((std::size_t)active * height);
    for (int y = 0; y < height; ++y)
      std::memcpy(result.data() + (std::size_t)y * active,
                  input.data() + (std::size_t)y * input_rowbytes, active);
    return result;
  }
  std::vector<std::uint8_t> packed_classic() const {
    std::vector<std::uint8_t> result((std::size_t)active * height);
    for (int y = 0; y < height; ++y)
      std::memcpy(result.data() + (std::size_t)y * active,
                  classic.data() + (std::size_t)y * classic_rowbytes, active);
    return result;
  }
  std::vector<std::uint8_t> packed_smart() const {
    std::vector<std::uint8_t> result((std::size_t)active * height);
    for (int y = 0; y < height; ++y)
      std::memcpy(result.data() + (std::size_t)y * active,
                  smart.data() + (std::size_t)y * smart_rowbytes, active);
    return result;
  }
};

static bool HeaderSame(const PF_EffectWorld& left, const PF_EffectWorld& right) {
  return std::memcmp(&left, &right, sizeof(PF_EffectWorld)) == 0;
}

template <class Pixel>
static int PositiveDepth(short depth, PF_PixelFormat format) {
  std::vector<std::uint8_t> back_two_output;
  for (int back : {2, 8}) {
    Fixture<Pixel> frame(19, 11, depth);
    const PF_EffectWorld input_header = frame.input_world;
    const PF_EffectWorld classic_header = frame.classic_world;
    const PF_EffectWorld smart_header = frame.smart_world;
    std::vector<std::uint8_t> classic_first, smart_first;
    for (int repeat = 0; repeat < 2; ++repeat) {
      PF_ParamDef classic_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
      PF_ParamDef* classic_params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
      InitParams(classic_defs, classic_params, frame.input_world, back);
      const PF_EffectWorld classic_input_header =
        classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
      HostState classic_state;
      classic_state.input = &classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
      classic_state.output = &frame.classic_world;
      classic_state.defs = classic_defs;
      classic_state.format = format;
      SPBasicSuite classic_basic = MakeBasic();
      frame.reset_classic();
      REQUIRE(InvokeClassic(&classic_state, &classic_basic, classic_params) == PF_Err_NONE,
              1000 + depth + back + repeat);
      REQUIRE(classic_state.acquire == 1 && classic_state.release == 1 &&
              classic_state.world_calls == 1 && classic_state.param_checkout_attempts == 0 &&
              classic_state.param_checkin_attempts == 0, 1020 + depth + back);
      REQUIRE(frame.input_unchanged() && frame.classic_padding() && frame.classic_changed(),
              1040 + depth + back);
      REQUIRE(HeaderSame(classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld,
                         classic_input_header), 1050 + depth + back);
      const auto packed = frame.packed_classic();
      REQUIRE(packed != frame.packed_input(), 1055 + depth + back);
      if (repeat == 0) classic_first = packed;
      else REQUIRE(packed == classic_first, 1060 + depth + back);

      PF_ParamDef smart_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
      PF_ParamDef* unused_params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
      InitParams(smart_defs, unused_params, frame.input_world, back);
      HostState smart_state;
      smart_state.input = &frame.input_world;
      smart_state.output = &frame.smart_world;
      smart_state.defs = smart_defs;
      smart_state.format = format;
      SPBasicSuite smart_basic = MakeBasic();
      frame.reset_smart();
      PF_Err pre_err = -1;
      REQUIRE(InvokeSmart(&smart_state, &smart_basic, depth, true, &pre_err) == PF_Err_NONE &&
              pre_err == PF_Err_NONE, 1080 + depth + back + repeat);
      const auto expected = ExpectedParams();
      REQUIRE(smart_state.pre_calls == 2 && smart_state.pre_input_calls == 1 &&
              smart_state.pre_noise_calls == 1 && smart_state.preserve &&
              smart_state.full_request && smart_state.pixel_calls == 2 &&
              smart_state.pixel_input_calls == 1 && smart_state.pixel_noise_calls == 1 &&
              smart_state.output_checkout == 1 && smart_state.layer_checkin == 1 &&
              smart_state.layer_checkin_order == std::vector<int>{0}, 1100 + depth + back);
      REQUIRE(smart_state.param_checkout_attempts == 21 &&
              smart_state.param_checkin_attempts == 21 &&
              smart_state.checkout_order == expected && smart_state.checkin_order == expected &&
              smart_state.back_seen == back && smart_state.acquire == 1 &&
              smart_state.release == 1 && smart_state.world_calls == 2,
              1120 + depth + back);
      REQUIRE(frame.input_unchanged() && frame.smart_padding() && frame.smart_changed(),
              1140 + depth + back);
      const auto smart_packed = frame.packed_smart();
      REQUIRE(smart_packed == packed, 1160 + depth + back);
      if (repeat == 0) smart_first = smart_packed;
      else REQUIRE(smart_packed == smart_first, 1180 + depth + back);
    }
    if (back == 2) back_two_output = classic_first;
    else REQUIRE(classic_first != back_two_output, 1190 + depth);
    REQUIRE(HeaderSame(frame.input_world, input_header) &&
            HeaderSame(frame.classic_world, classic_header) &&
            HeaderSame(frame.smart_world, smart_header), 1200 + depth + back);
  }
  return 0;
}

static int RepresentativeHD() {
  Fixture<PF_Pixel8> frame(1280, 720, 8);
  const PF_EffectWorld input_header = frame.input_world;
  const PF_EffectWorld classic_header = frame.classic_world;
  const PF_EffectWorld smart_header = frame.smart_world;

  PF_ParamDef classic_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* classic_params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(classic_defs, classic_params, frame.input_world, 2);
  const PF_EffectWorld classic_input_header =
    classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
  HostState classic_state;
  classic_state.input = &classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
  classic_state.output = &frame.classic_world;
  classic_state.defs = classic_defs;
  classic_state.format = PF_PixelFormat_ARGB32;
  SPBasicSuite classic_basic = MakeBasic();
  REQUIRE(InvokeClassic(&classic_state, &classic_basic, classic_params) == PF_Err_NONE,
          1210);
  const auto classic = frame.packed_classic();
  REQUIRE(classic_state.acquire == 1 && classic_state.release == 1 &&
          classic_state.world_calls == 1 && frame.input_unchanged() &&
          frame.classic_padding() && frame.classic_changed() &&
          classic != frame.packed_input() &&
          HeaderSame(classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld,
                     classic_input_header), 1220);

  PF_ParamDef smart_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* unused[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(smart_defs, unused, frame.input_world, 2);
  HostState smart_state;
  smart_state.input = &frame.input_world;
  smart_state.output = &frame.smart_world;
  smart_state.defs = smart_defs;
  smart_state.format = PF_PixelFormat_ARGB32;
  SPBasicSuite smart_basic = MakeBasic();
  REQUIRE(InvokeSmart(&smart_state, &smart_basic, 8, true) == PF_Err_NONE, 1230);
  REQUIRE(frame.packed_smart() == classic && frame.input_unchanged() &&
          frame.smart_padding() && smart_state.checkout_order == ExpectedParams() &&
          smart_state.checkin_order == ExpectedParams() && smart_state.back_seen == 2 &&
          smart_state.layer_checkin_order == std::vector<int>{0}, 1240);
  REQUIRE(HeaderSame(frame.input_world, input_header) &&
          HeaderSame(frame.classic_world, classic_header) &&
          HeaderSame(frame.smart_world, smart_header), 1250);
  return 0;
}

template <class Pixel>
static int PartialReject(short depth, PF_PixelFormat format) {
  Fixture<Pixel> frame(19, 11, depth);
  PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(defs, params, frame.input_world, 2);
  HostState state;
  state.input = &frame.input_world;
  state.output = &frame.smart_world;
  state.defs = defs;
  state.format = format;
  SPBasicSuite basic = MakeBasic();
  const auto before = frame.smart;
  PF_Err pre_err = PF_Err_NONE;
  REQUIRE(InvokeSmart(&state, &basic, depth, false, &pre_err) ==
            PF_Err_BAD_CALLBACK_PARAM && pre_err == PF_Err_BAD_CALLBACK_PARAM,
          1300 + depth);
  REQUIRE(state.pre_calls == 0 && state.pixel_calls == 0 &&
          state.param_checkout_attempts == 0 && state.acquire == 0 &&
          frame.smart == before && frame.input_unchanged(), 1320 + depth);
  return 0;
}

template <class Pixel>
static int AtomicSDRReject(short depth, PF_PixelFormat format) {
  Fixture<Pixel> frame(19, 11, depth);
  Pixel poison = {};
  std::memcpy(&poison, frame.input.data(), sizeof(poison));
  if constexpr (std::is_same_v<Pixel, PF_Pixel16>) poison.red = 32769;
  else poison.red = 1.25f;
  std::memcpy(frame.input.data(), &poison, sizeof(poison));
  frame.original = frame.input;

  PF_ParamDef classic_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* classic_params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(classic_defs, classic_params, frame.input_world, 2);
  HostState classic_state;
  classic_state.input = &classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
  classic_state.output = &frame.classic_world;
  classic_state.defs = classic_defs;
  classic_state.format = format;
  SPBasicSuite classic_basic = MakeBasic();
  frame.reset_classic();
  REQUIRE(InvokeClassic(&classic_state, &classic_basic, classic_params) ==
            PF_Err_BAD_CALLBACK_PARAM && frame.classic_untouched(), 1400 + depth);
  REQUIRE(classic_state.acquire == 1 && classic_state.release == 1 &&
          classic_state.world_calls == 1 && frame.input_unchanged(), 1420 + depth);

  PF_ParamDef smart_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* unused[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(smart_defs, unused, frame.input_world, 2);
  HostState smart_state;
  smart_state.input = &frame.input_world;
  smart_state.output = &frame.smart_world;
  smart_state.defs = smart_defs;
  smart_state.format = format;
  SPBasicSuite smart_basic = MakeBasic();
  frame.reset_smart();
  REQUIRE(InvokeSmart(&smart_state, &smart_basic, depth, true) ==
            PF_Err_BAD_CALLBACK_PARAM && frame.smart_untouched(), 1440 + depth);
  REQUIRE(smart_state.checkout_order == ExpectedParams() &&
          smart_state.checkin_order == ExpectedParams() &&
          smart_state.layer_checkin == 1 && smart_state.acquire == 1 &&
          smart_state.release == 1 && smart_state.world_calls == 2 &&
          frame.input_unchanged(), 1460 + depth);
  return 0;
}

struct Mapping {
  void* data = MAP_FAILED;
  std::size_t size = 0;
  explicit Mapping(std::size_t bytes) : size(bytes) {
    data = mmap(nullptr, bytes, PROT_READ | PROT_WRITE,
                MAP_PRIVATE | MAP_ANON, -1, 0);
  }
  ~Mapping() { if (data != MAP_FAILED) munmap(data, size); }
  bool valid() const { return data != MAP_FAILED; }
  std::uint8_t* bytes() { return reinterpret_cast<std::uint8_t*>(data); }
};

static bool Guarded(const Mapping& mapping, std::uint8_t value) {
  const auto* bytes = reinterpret_cast<const std::uint8_t*>(mapping.data);
  for (std::size_t i = 0; i < 64; ++i) {
    if (bytes[i] != value || bytes[mapping.size - 64 + i] != value) return false;
  }
  return true;
}

static void SetGuards(Mapping* mapping, std::uint8_t value) {
  std::memset(mapping->bytes(), value, 64);
  std::memset(mapping->bytes() + mapping->size - 64, value, 64);
}

static std::uint8_t ValidInputCanary(short depth) {
  return depth == 8 ? 0xa5 : (depth == 16 ? 0x7f : 0x3f);
}

template <class Pixel>
static int OperationBudgetReject(short depth, PF_PixelFormat format) {
  constexpr int width = 3840, height = 2160;
  const A_long rowbytes = width * (A_long)sizeof(Pixel);
  const std::size_t span = (std::size_t)rowbytes * height;
  Mapping input(span), output(span);
  REQUIRE(input.valid() && output.valid(), 1500 + depth);
  const std::uint8_t input_canary = ValidInputCanary(depth);
  SetGuards(&input, input_canary);
  SetGuards(&output, kOutputCanary);
  PF_EffectWorld input_world = MakeWorld(input.data, rowbytes, width, height, depth);
  PF_EffectWorld output_world = MakeWorld(output.data, rowbytes, width, height, depth);

  PF_ParamDef classic_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* classic_params[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(classic_defs, classic_params, input_world, 12);
  HostState classic_state;
  classic_state.input = &classic_defs[OLMDIRECTIONALBLUR_INPUT].u.ld;
  classic_state.output = &output_world;
  classic_state.defs = classic_defs;
  classic_state.format = format;
  SPBasicSuite classic_basic = MakeBasic();
  REQUIRE(InvokeClassic(&classic_state, &classic_basic, classic_params) ==
            PF_Err_BAD_CALLBACK_PARAM, 1520 + depth);
  REQUIRE(Guarded(input, input_canary) && Guarded(output, kOutputCanary), 1540 + depth);

  SetGuards(&output, kOutputCanary);
  PF_ParamDef smart_defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* unused[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(smart_defs, unused, input_world, 12);
  HostState smart_state;
  smart_state.input = &input_world;
  smart_state.output = &output_world;
  smart_state.defs = smart_defs;
  smart_state.format = format;
  SPBasicSuite smart_basic = MakeBasic();
  REQUIRE(InvokeSmart(&smart_state, &smart_basic, depth, true) ==
            PF_Err_BAD_CALLBACK_PARAM, 1560 + depth);
  REQUIRE(smart_state.checkout_order == ExpectedParams() &&
          smart_state.checkin_order == ExpectedParams() &&
          smart_state.layer_checkin == 1 && Guarded(input, input_canary) &&
          Guarded(output, kOutputCanary), 1580 + depth);
  return 0;
}

template <class Pixel>
static int SmartMemoryBudgetReject(short depth, PF_PixelFormat format) {
  constexpr int width = 19, height = 2;
  const A_long input_rowbytes = width * (A_long)sizeof(Pixel) + 5;
  const std::uint8_t input_canary = ValidInputCanary(depth);
  std::vector<std::uint8_t> input((std::size_t)input_rowbytes * height, input_canary);
  const auto original = input;
  constexpr A_long output_rowbytes = 1536 * 1024 * 1024;
  const std::size_t output_span = (std::size_t)output_rowbytes * height;
  Mapping output(output_span);
  REQUIRE(output.valid(), 1600 + depth);
  SetGuards(&output, kOutputCanary);
  PF_EffectWorld input_world = MakeWorld(input.data(), input_rowbytes, width, height, depth);
  PF_EffectWorld output_world = MakeWorld(output.data, output_rowbytes, width, height, depth);
  PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  PF_ParamDef* unused[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
  InitParams(defs, unused, input_world, 2);
  HostState state;
  state.input = &input_world;
  state.output = &output_world;
  state.defs = defs;
  state.format = format;
  SPBasicSuite basic = MakeBasic();
  REQUIRE(InvokeSmart(&state, &basic, depth, true) == PF_Err_BAD_CALLBACK_PARAM,
          1620 + depth);
  REQUIRE(state.checkout_order == ExpectedParams() &&
          state.checkin_order == ExpectedParams() && state.layer_checkin == 1 &&
          input == original && Guarded(output, kOutputCanary), 1640 + depth);
  return 0;
}

template <class Pixel>
static int CallbackAtomic(short depth, PF_PixelFormat format) {
  for (int mode = 0; mode < 4; ++mode) {
    Fixture<Pixel> frame(19, 11, depth);
    PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
    PF_ParamDef* unused[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
    InitParams(defs, unused, frame.input_world, 2);
    HostState state;
    state.input = &frame.input_world;
    state.output = &frame.smart_world;
    state.defs = defs;
    state.format = format;
    if (mode == 0) state.fail_checkout_index = OLMDIRECTIONALBLUR_BACK_STRENGTH;
    if (mode == 1) state.fail_checkin_id = OLMDIRECTIONALBLUR_BACK_STRENGTH;
    if (mode == 2) state.fail_output = true;
    if (mode == 3) state.fail_layer_checkin_id = OLMDIRECTIONALBLUR_INPUT;
    SPBasicSuite basic = MakeBasic();
    const PF_Err expected = mode == 0 ? kCheckoutFailure :
                            (mode == 1 ? kCheckinFailure :
                             (mode == 2 ? kOutputFailure : kLayerCheckinFailure));
    REQUIRE(InvokeSmart(&state, &basic, depth, true) == expected,
            1700 + depth + mode);
    REQUIRE(frame.smart_untouched() && frame.input_unchanged() &&
            frame.smart_padding(), 1720 + depth + mode);
    if (mode == 0) {
      std::vector<int> first_nine;
      for (int i = 1; i < OLMDIRECTIONALBLUR_BACK_STRENGTH; ++i)
        first_nine.push_back(i);
      REQUIRE(state.param_checkout_attempts == 10 &&
              state.checkout_order == first_nine && state.checkin_order == first_nine &&
              state.param_checkin_attempts == 9 && state.layer_checkin == 1,
              1740 + depth);
    } else if (mode == 1) {
      REQUIRE(state.checkout_order == ExpectedParams() &&
              state.checkin_order == ExpectedParams() &&
              state.param_checkout_attempts == 21 && state.param_checkin_attempts == 21 &&
              state.layer_checkin == 1, 1760 + depth);
    } else if (mode == 2) {
      REQUIRE(state.output_checkout == 1 && state.param_checkout_attempts == 0 &&
              state.param_checkin_attempts == 0 && state.acquire == 0 &&
              state.layer_checkin == 1, 1780 + depth);
    } else {
      REQUIRE(state.checkout_order == ExpectedParams() &&
              state.checkin_order == ExpectedParams() &&
              state.param_checkout_attempts == 21 && state.param_checkin_attempts == 21 &&
              state.layer_checkin == 1 &&
              state.layer_checkin_order == std::vector<int>{0}, 1800 + depth);
    }
  }
  return 0;
}

int main() {
  REQUIRE(OLMDIRECTIONALBLUR_BACK_STRENGTH == 10, 1);
  REQUIRE(PositiveDepth<PF_Pixel8>(8, PF_PixelFormat_ARGB32) == 0, 2);
  REQUIRE(PositiveDepth<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 3);
  REQUIRE(PositiveDepth<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 4);
  REQUIRE(RepresentativeHD() == 0, 19);
  REQUIRE(PartialReject<PF_Pixel8>(8, PF_PixelFormat_ARGB32) == 0, 5);
  REQUIRE(PartialReject<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 6);
  REQUIRE(PartialReject<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 7);
  REQUIRE(AtomicSDRReject<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 8);
  REQUIRE(AtomicSDRReject<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 9);
  REQUIRE(OperationBudgetReject<PF_Pixel8>(8, PF_PixelFormat_ARGB32) == 0, 10);
  REQUIRE(OperationBudgetReject<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 11);
  REQUIRE(OperationBudgetReject<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 12);
  REQUIRE(SmartMemoryBudgetReject<PF_Pixel8>(8, PF_PixelFormat_ARGB32) == 0, 13);
  REQUIRE(SmartMemoryBudgetReject<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 14);
  REQUIRE(SmartMemoryBudgetReject<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 15);
  REQUIRE(CallbackAtomic<PF_Pixel8>(8, PF_PixelFormat_ARGB32) == 0, 16);
  REQUIRE(CallbackAtomic<PF_Pixel16>(16, PF_PixelFormat_ARGB64) == 0, 17);
  REQUIRE(CallbackAtomic<PF_PixelFloat>(32, PF_PixelFormat_ARGB128) == 0, 18);
  std::puts("PASS_DBLUR_GENERIC_BACKONLY_EFFECTMAIN classic=8/16/32 smart=8/16/32 "
            "back=2/8 hd=1280x720 param=10 odd_strides=yes atomic=yes "
            "budgets=operation/memory");
  return 0;
}
'''


def build(directory: Path, sanitize: bool) -> Path:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("C++ compiler not found")
    source = directory / "dblur_generic_backonly_effectmain.cpp"
    binary = directory / "dblur_generic_backonly_effectmain"
    source.write_text(
        CPP.replace(
            "__PRODUCTION__",
            str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"'),
        ),
        encoding="utf-8",
    )
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], check=True, capture_output=True, text=True
    ).stdout.strip()
    optimization = (
        ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        if sanitize
        else ["-O2"]
    )
    command = [
        compiler,
        "-std=c++17",
        *optimization,
        "-fno-fast-math",
        "-ffp-contract=off",
        "-ffunction-sections",
        "-fdata-sections",
        "-Wno-unused-function",
        "-Wno-unused-parameter",
        "-Wno-pragma-pack",
        "-isysroot",
        sdk,
        "-I",
        str(ROOT),
        "-I",
        str(ROOT / "Headers"),
        "-I",
        str(ROOT / "Headers/SP"),
        "-I",
        str(ROOT / "Util"),
        "-I",
        str(ROOT / "Resources"),
        str(source),
        str(ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp"),
        str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"),
        str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
        str(ROOT / "Util/MissingSuiteError.cpp"),
        "-Wl,-dead_strip",
        "-framework",
        "Cocoa",
        "-o",
        str(binary),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return binary


def main() -> int:
    sanitize = os.environ.get("OLM_DBLUR_EFFECTMAIN_SANITIZE") == "1"
    with tempfile.TemporaryDirectory(prefix="dblur_effectmain_backonly_") as raw:
        binary = build(Path(raw), sanitize)
        environment = os.environ.copy()
        if sanitize:
            environment["ASAN_OPTIONS"] = "halt_on_error=1:detect_leaks=0"
            environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        result = subprocess.run(
            [str(binary)],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
        if result.returncode:
            raise RuntimeError(
                f"DirectionalBlur EffectMain probe rc={result.returncode}:\n"
                f"{result.stdout}\n{result.stderr}"
            )
    print(result.stdout, end="")
    print(
        "PASS_DBLUR_GENERIC_BACKONLY_EFFECTMAIN_BUILD "
        f"sanitizers={'asan+ubsan' if sanitize else 'off'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
