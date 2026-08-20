#!/usr/bin/env python3
"""Production-dispatch gate for the neutral DirectionalBlur Back-only beta."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
SOURCE_PNG = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
ANCHOR_REPORT = ROOT / "refs/conformance/dblur_mode1_backonly_portable_20260805.json"
ANCHOR_REPORT_SHA256 = "286dba46344d51a368827800d9bc6a665cc657848b5a343ab54f0dedadbc42b4"
SOURCE_SHA256 = "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4"
AEX_SHA256 = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"
ANCHOR_ARGB_SHA256 = "1a25fefa174c7a69f1004ce42f116e9633967587bccc3278b0d2418d99084695"
ANCHOR_SOURCE_ARGB_SHA256 = "c3b464fe8c8d8abb2fa8072b143d57773e6e7a86c1e0764e14868dae7a3194ea"
# zlib(level=9) + Base85 of the 960x540 ARGB bytes derived from SOURCE_PNG.
# Keeping the compact source fixture here makes the production replay mandatory
# in a clean checkout; the untracked PNG/AEX remain optional provenance checks.
ANCHOR_SOURCE_ARGB_ZLIB_B85 = (
    "c-rmP!3_W~3<9z2zck$<t%@IB0Ex$CW&!{J0000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000002Mu3Tb!0001fYh6tY002O1>uO>E005eMR}TXK0MOdJS{MKTK=Y!70RRAWuMP$P06_C<VE_OCbgvEu00"
    "2Pu>R<o>0CcYo1^@s+_v&B(007;K4h8@K(7otj0002(iv|V&0MNbYU;qFB?TZEm007XvIv4-|0PU-R0RRAWFFF_i06_bqfdK#jv@aSM"
    "002PyqJaSb0JJX}7ytl3_o9OV006Wv8W;co(7vF70RRB)3;qHC0BBz{FaQ96_C*5&003xTG%x@Ffc8ZL0{{SMUo<cP0D$&I0|Nj6`WN&s"
    "005wUK?4H-0NNKcFaQ9cebK-G007z-4GaJPpncK60002`7ySzW0HA%*zyJV%_5}?L008J;(7ylxfc6Cq3;+OVU(mn+0D%4l{R;p9XkRoi"
    "004mYMFRr>0O()zF8~0beL({Q008<I^e+GapnX9D0{{T}7xXUx0HA$A0|Nj6`WN&s005wU(ZB!z0QwjG3jhFUU(mn+0D%4l{R;p9XkXC4"
    "004mg1^o*E0O()PzW@M$_5}?L008J;(7ylxfc8ZL0{{T}7xXUx0HA+C{{jF2+7~o1005wWLH_~(0Qwj7F8~0beL({Q008<I^e+GapnpOC"
    "0sw&i1^o*E0BB#(zyJV%{ssLD008J;(7ylxfc^#j3jhG<U(mk*0D$%d4GaJP=wHyk005wW0sRXA0Qwj7F8~0be?k8O007z-G%x@FpnpOC"
    "0ssK|7xXUx0HA+C{{jF2`WN&s005wWLH_~(fc^#aF8~1OU(mk*0D%4l{R;p9=wHyk004mg1^o*E0O()PzW@M${ssLD008J;(7ylxfW`s+"
    "3jhH67xXUx0HA+C{{jF2`WN&s005wWLH_~(0Qwj7F8~0be?k8O008<I^e+GapnpOC0sw&i1@tcf0O()PzW@M${ssLD008J;(7ylxfc^#j"
    "3jhG<U(mk*0D%4l{R;p9XkgI3004mg1^o*E0Qwj7F8~0be?k8O008<I^e+Gapn*aA0ssK|7xXUx0HA+C{{jF2`WN&s005wWLH_~(02&yy"
    "F8~1OU(mk*0D%4l{R;p9=wHyk004jn2JH&~0O()PzW@M${ssLD003xU(7pfwfc^#j3jhG<AoMQ)0HA?E`vL#}`WN&s005wYLHhy#0Qwj7"
    "F8~0be?k8O000^ov@ZYvpnpOC0ssIS80`xH0HA--zW@M$1_td5008J;(7ylxfCdKb3jhG<U(mk*0DuMt?F#?^=wHyk004jnM*9K)0O()z"
    "F8~0521fe=000^ov@ZYvpnpOC0ssIS7_=_{0HA?E`vL#}`WN&s005wY(Y^ox02&zW3jhG1f6>1H000^o?F#?^pu^C<004jn2JH&~0BB&)"
    "z5oD#1_td5008J;^e+GafCfhU0ssJLV6-m)0DuNY`vL#}XkfH2004jnM*9K)02&yyF8~0bfkFEM000^o?F#?^pn=i80000w7~Km10HA@<"
    "z5oCK8W`;h005wY(Y^ox02&zW3jhG1gLN+e004SX`vL#}=wNg&004jnM*9K)0O(+JF8~0521fe=008J<bT0q^fDYEZ0002!VBHG<0DunG"
    "y#N3J=wRIo004jv*1Z4#0BB*&3jhG1gVDVJ003H8^8x?>poKLr0001bSnmP=0HBGrE&u=knpo=s0000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000006gmemDyY{"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_anchor_authorities() -> bool:
    report_bytes = ANCHOR_REPORT.read_bytes()
    if sha256_bytes(report_bytes) != ANCHOR_REPORT_SHA256:
        raise RuntimeError("tracked Back-only evidence report drift")
    report = json.loads(report_bytes)
    provenance = report.get("provenance", {})
    claim_boundary = report.get("claim_boundary", {})
    if (
        report.get("schema") != 1
        or report.get("kind") != "dblur_mode1_backonly_portable_20260805"
        or report.get("status") != "pass"
        or provenance.get("source_sha256") != SOURCE_SHA256
        or provenance.get("aex_sha256") != AEX_SHA256
        or report.get("actual_aex_raw_argb_sha256") != ANCHOR_ARGB_SHA256
        or report.get("portable_raw_argb_sha256") != ANCHOR_ARGB_SHA256
        or report.get("parameters", {}).get("back_strength_ui") != 240
        or report.get("parameters", {}).get("render_scale") != 0.5
        or claim_boundary.get("actual_aex_raw_exact") is not True
        or claim_boundary.get("windows_ae_pixel_exact") is not False
    ):
        raise RuntimeError("pinned Back-only raw-callback report contract drift")
    if SOURCE_PNG.exists() and sha256_bytes(SOURCE_PNG.read_bytes()) != SOURCE_SHA256:
        raise RuntimeError("locally available pinned DirectionalBlur source PNG drift")
    if AEX.exists() and sha256_bytes(AEX.read_bytes()) != AEX_SHA256:
        raise RuntimeError("locally available pinned DirectionalBlur actual AEX drift")
    return (
        SOURCE_PNG.exists()
        and AEX.exists()
        and os.environ.get("OLM_DBLUR_TEST_FORCE_TRACKED_ONLY") != "1"
    )


def embedded_anchor_source_argb() -> bytes:
    compressed = base64.b85decode(ANCHOR_SOURCE_ARGB_ZLIB_B85)
    source = zlib.decompress(compressed)
    if len(source) != 960 * 540 * 4 or sha256_bytes(source) != ANCHOR_SOURCE_ARGB_SHA256:
        raise RuntimeError("embedded DirectionalBlur source ARGB fixture drift")
    return source


CPP = r'''
#define OLM_DBLUR_TEST_SEAM 1
#include "__PRODUCTION__"
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <limits>
#include <type_traits>
#include <vector>

#define REQUIRE(condition, code) do { if (!(condition)) { \
  std::fprintf(stderr, "FAIL code=%d line=%d\n", (code), __LINE__); return (code); \
} } while (0)

static constexpr int kRouteRetained = 1;
static constexpr int kRouteGeneric = 2;
static constexpr std::uint8_t kInputPad = 0xa5;
static constexpr std::uint8_t kOutputPad = 0xee;

static OLMDirectionalBlurInfo Info(int front, int back, double angle,
                                   double scale = 1.0) {
  OLMDirectionalBlurInfo info{};
  info.angle_deg = angle;
  info.brightness_gain = 0.75;
  info.front_strength = front;
  info.back_strength = back;
  info.noise_type = 1;
  info.seed = 1;
  info.thickness = 10.0;
  info.render_scale_x = scale;
  info.render_scale_y = scale;
  return info;
}

template <class Pixel> struct Storage {
  int width = 0, height = 0, input_rowbytes = 0, output_rowbytes = 0;
  std::vector<std::uint8_t> input, output, original;
  PF_EffectWorld input_world{}, output_world{};

  Storage(int w, int h, int input_padding = 5, int output_padding = 17)
      : width(w), height(h), input_rowbytes(w * (int)sizeof(Pixel) + input_padding),
        output_rowbytes(w * (int)sizeof(Pixel) + output_padding),
        input((std::size_t)input_rowbytes * h, kInputPad),
        output((std::size_t)output_rowbytes * h, kOutputPad) {
    for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
      Pixel pixel{};
      if constexpr (std::is_same_v<Pixel, PF_Pixel8>) {
        pixel.alpha = static_cast<A_u_char>(96 + ((x * 3 + y * 5) % 160));
        pixel.red = static_cast<A_u_char>((x * 31 + y * 7 + 11) & 255);
        pixel.green = static_cast<A_u_char>((x * 3 + y * 19 + 23) & 255);
        pixel.blue = static_cast<A_u_char>((x * 11 + y * 5 + 47) & 255);
      } else if constexpr (std::is_same_v<Pixel, PF_Pixel16>) {
        pixel.alpha = static_cast<A_u_short>(12000 + ((x * 97 + y * 53) % 20000));
        pixel.red = static_cast<A_u_short>((x * 919 + y * 211 + 1000) & 32767);
        pixel.green = static_cast<A_u_short>((x * 101 + y * 677 + 2000) & 32767);
        pixel.blue = static_cast<A_u_short>((x * 431 + y * 307 + 3000) & 32767);
      } else {
        pixel.alpha = 0.35f + float((x * 3 + y * 5) % 50) / 100.0f;
        pixel.red = float((x * 31 + y * 7 + 11) & 255) / 255.0f;
        pixel.green = float((x * 3 + y * 19 + 23) & 255) / 255.0f;
        pixel.blue = float((x * 11 + y * 5 + 47) & 255) / 255.0f;
      }
      std::memcpy(input.data() + (std::size_t)y * input_rowbytes +
                    (std::size_t)x * sizeof(Pixel), &pixel, sizeof(pixel));
    }
    original = input;
    bind();
  }

  void bind() {
    input_world = {};
    input_world.data = reinterpret_cast<PF_PixelPtr>(input.data());
    input_world.rowbytes = input_rowbytes;
    input_world.width = width;
    input_world.height = height;
    input_world.extent_hint = {0, 0, width, height};
    output_world = {};
    output_world.data = reinterpret_cast<PF_PixelPtr>(output.data());
    output_world.rowbytes = output_rowbytes;
    output_world.width = width;
    output_world.height = height;
    output_world.extent_hint = {0, 0, width, height};
  }

  void clear_output() {
    std::fill(output.begin(), output.end(), kOutputPad);
    bind();
  }

  bool input_unchanged() const { return input == original; }
  bool padding_ok() const {
    const int input_active = width * (int)sizeof(Pixel);
    for (int y = 0; y < height; ++y) {
      for (int x = input_active; x < input_rowbytes; ++x)
        if (input[(std::size_t)y * input_rowbytes + x] != kInputPad) return false;
      for (int x = input_active; x < output_rowbytes; ++x)
        if (output[(std::size_t)y * output_rowbytes + x] != kOutputPad) return false;
    }
    return true;
  }
  bool active_changed() const {
    const int active = width * (int)sizeof(Pixel);
    for (int y = 0; y < height; ++y) for (int x = 0; x < active; ++x)
      if (output[(std::size_t)y * output_rowbytes + x] != kOutputPad) return true;
    return false;
  }
};

template <class Pixel>
static bool active_equal(const Storage<Pixel>& left, const Storage<Pixel>& right) {
  if (left.width != right.width || left.height != right.height) return false;
  const std::size_t active = (std::size_t)left.width * sizeof(Pixel);
  for (int y = 0; y < left.height; ++y)
    if (std::memcmp(left.output.data() + (std::size_t)y * left.output_rowbytes,
                    right.output.data() + (std::size_t)y * right.output_rowbytes,
                    active)) return false;
  return true;
}

template <class Pixel>
static int render(Storage<Pixel>& storage, short depth,
                  const OLMDirectionalBlurInfo& info, int expected_route) {
  storage.clear_output();
  int route = -1;
  const PF_Err err = OLMDirectionalBlurTestRenderWorldRoute(
      &storage.input_world, &storage.output_world, &info, depth, &route);
  if (err != PF_Err_NONE || route != expected_route || !storage.active_changed() ||
      !storage.input_unchanged() || !storage.padding_ok()) return 1;
  return 0;
}

template <class Pixel>
static int positive_depth(short depth) {
  Storage<Pixel> back_two(37, 23), back_eight(37, 23), repeated(37, 23), front(37, 23);
  const double scale = depth == 8 ? 0.5 : 1.0;
  const auto two = Info(0, 2, 37.25, scale);
  const auto eight = Info(0, 8, -21.5, scale);
  auto front_info = Info(8, 0, -21.5, scale);
  REQUIRE(render(back_two, depth, two, kRouteGeneric) == 0, 10 + depth);
  REQUIRE(render(back_eight, depth, eight, kRouteGeneric) == 0, 20 + depth);
  REQUIRE(render(repeated, depth, eight, kRouteGeneric) == 0, 30 + depth);
  REQUIRE(back_eight.output == repeated.output, 40 + depth);
  REQUIRE(render(front, depth, front_info, kRouteGeneric) == 0, 50 + depth);
  REQUIRE(!active_equal(back_eight, front), 60 + depth);
  int effective = 0;
  REQUIRE(OLMDirectionalBlurTestGenericEffectiveStrength(&eight, depth, &effective),
          70 + depth);
  REQUIRE(effective == (depth == 8 ? 4 : 8), 80 + depth);
  auto dual = Info(2, 2, 37.25, scale);
  REQUIRE(!OLMDirectionalBlurTestGenericEffectiveStrength(&dual, depth, &effective),
          90 + depth);
  return 0;
}

static int projected_scale_matrix() {
  struct ScaleCase { double angle, scale_x, scale_y; int expected; };
  const std::array<ScaleCase, 3> cases{{
    {0.0, 0.25, 0.75, 2},
    {90.0, 0.25, 0.75, 6},
    {45.0, 0.25, 0.75, 4},
  }};
  for (std::size_t i = 0; i < cases.size(); ++i) {
    auto info = Info(0, 8, cases[i].angle);
    info.render_scale_x = cases[i].scale_x;
    info.render_scale_y = cases[i].scale_y;
    int effective = 0;
    REQUIRE(OLMDirectionalBlurTestGenericEffectiveStrength(&info, 8, &effective),
            94 + (int)i);
    REQUIRE(effective == cases[i].expected, 97 + (int)i);
    Storage<PF_Pixel8> storage(37, 23);
    REQUIRE(render(storage, 8, info, kRouteGeneric) == 0, 100 + (int)i);
  }
  return 0;
}

template <class Pixel>
static int retained_depth(short depth) {
  struct RetainedCase { int back; double angle, gain; };
  std::vector<RetainedCase> cases;
  if (depth == 8) cases = {{8, 0.0, 1.0}, {8, 45.0, 1.0}};
  if (depth == 16) cases = {{1, 45.0, 1.0}, {2, 45.0, 1.0}, {8, 45.0, 1.0}};
  if (depth == 32) cases = {
    {1, 0.0, 0.5}, {1, 0.0, 1.0}, {1, 45.0, 0.5},
    {1, 45.0, 1.0}, {8, 45.0, 1.0},
  };
  REQUIRE(!cases.empty(), 103 + depth);
  for (std::size_t i = 0; i < cases.size(); ++i) {
    Storage<Pixel> storage(16, 16);
    auto info = Info(0, cases[i].back, cases[i].angle);
    info.brightness_gain = cases[i].gain;
    REQUIRE(render(storage, depth, info, kRouteRetained) == 0,
            110 + depth + (int)i);

    storage.clear_output();
    storage.input_world.rowbytes = -1;
    const auto input_negative_before = storage.output;
    int route = -1;
    REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
                &storage.input_world, &storage.output_world, &info, depth, &route) ==
                PF_Err_BAD_CALLBACK_PARAM,
            130 + depth + (int)i);
    REQUIRE(storage.output == input_negative_before, 150 + depth + (int)i);

    storage.bind();
    storage.clear_output();
    storage.output_world.rowbytes = -1;
    const auto output_negative_before = storage.output;
    route = -1;
    REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
                &storage.input_world, &storage.output_world, &info, depth, &route) ==
                PF_Err_BAD_CALLBACK_PARAM,
            170 + depth + (int)i);
    REQUIRE(storage.output == output_negative_before && storage.input_unchanged(),
            190 + depth + (int)i);
  }
  return 0;
}

template <class Pixel>
static int atomic_rejects(short depth) {
  Storage<Pixel> input(37, 23), larger(38, 23);
  const double scale = depth == 8 ? 1.0 : 1.0;
  auto valid = Info(0, 2, 37.25, scale);
  int route = -1;
  const auto larger_before = larger.output;
  REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
              &input.input_world, &larger.output_world, &valid, depth, &route) ==
              PF_Err_BAD_CALLBACK_PARAM,
          130 + depth);
  REQUIRE(larger.output == larger_before, 140 + depth);

  auto effective_zero = Info(0, 1, 37.25, 0.5);
  input.clear_output();
  const auto zero_before = input.output;
  REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
              &input.input_world, &input.output_world, &effective_zero, depth, &route) ==
              PF_Err_BAD_CALLBACK_PARAM,
          150 + depth);
  REQUIRE(input.output == zero_before, 160 + depth);

  auto over_ui = Info(0, 4001, 37.25);
  input.clear_output();
  const auto ui_before = input.output;
  REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
              &input.input_world, &input.output_world, &over_ui, depth, &route) ==
              PF_Err_BAD_CALLBACK_PARAM,
          170 + depth);
  REQUIRE(input.output == ui_before, 180 + depth);

  if (depth != 8) {
    auto dual = Info(2, 2, 37.25);
    input.clear_output();
    const auto dual_before = input.output;
    REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
                &input.input_world, &input.output_world, &dual, depth, &route) ==
                PF_Err_BAD_CALLBACK_PARAM,
            190 + depth);
    REQUIRE(input.output == dual_before, 200 + depth);
  }

  constexpr int width = 3840, height = 2160;
  std::array<std::uint8_t, 64> tiny_input{}, tiny_output{};
  tiny_output.fill(kOutputPad);
  PF_EffectWorld huge_in{}, huge_out{};
  huge_in.data = reinterpret_cast<PF_PixelPtr>(tiny_input.data());
  huge_out.data = reinterpret_cast<PF_PixelPtr>(tiny_output.data());
  huge_in.rowbytes = huge_out.rowbytes = width * (int)sizeof(Pixel);
  huge_in.width = huge_out.width = width;
  huge_in.height = huge_out.height = height;
  auto operation = Info(0, 12, 37.25);
  OLMDirectionalBlurGenericEstimate estimate{};
  REQUIRE(!OLMDirectionalBlurTestGenericEstimate(
              width, height, depth, 12, 0, &estimate), 210 + depth);
  const auto operation_before = tiny_output;
  REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
              &huge_in, &huge_out, &operation, depth, &route) ==
              PF_Err_BAD_CALLBACK_PARAM,
          220 + depth);
  REQUIRE(tiny_output == operation_before, 230 + depth);
  return 0;
}

static int deep_sdr_rejects() {
  {
    Storage<PF_Pixel16> storage(37, 23);
    PF_Pixel16 pixel{};
    pixel.alpha = pixel.red = pixel.green = pixel.blue = 32768;
    for (int y = 0; y < storage.height; ++y) for (int x = 0; x < storage.width; ++x)
      std::memcpy(storage.input.data() + (std::size_t)y * storage.input_rowbytes +
                    (std::size_t)x * sizeof(pixel), &pixel, sizeof(pixel));
    storage.original = storage.input;
    auto info = Info(0, 2, 37.25);
    REQUIRE(render(storage, 16, info, kRouteGeneric) == 0, 248);
  }
  {
    Storage<PF_Pixel16> storage(37, 23);
    PF_Pixel16 pixel{};
    std::memcpy(&pixel, storage.input.data(), sizeof(pixel));
    pixel.red = 32769;
    std::memcpy(storage.input.data(), &pixel, sizeof(pixel));
    storage.original = storage.input;
    const auto before = storage.output;
    int route = -1;
    auto info = Info(0, 2, 37.25);
    REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
                &storage.input_world, &storage.output_world, &info, 16, &route) ==
                PF_Err_BAD_CALLBACK_PARAM,
            250);
    REQUIRE(route == kRouteGeneric && storage.output == before &&
            storage.input_unchanged(), 251);
  }
  for (int poison = 0; poison < 5; ++poison) {
    Storage<PF_PixelFloat> storage(37, 23);
    PF_PixelFloat pixel{};
    std::memcpy(&pixel, storage.input.data(), sizeof(pixel));
    pixel.red = poison == 0 ? 1.01f :
      (poison == 1 ? -0.01f :
       (poison == 2 ? std::numeric_limits<float>::quiet_NaN() :
        (poison == 3 ? std::numeric_limits<float>::infinity() :
                       -std::numeric_limits<float>::infinity())));
    std::memcpy(storage.input.data(), &pixel, sizeof(pixel));
    storage.original = storage.input;
    const auto before = storage.output;
    int route = -1;
    auto info = Info(0, 2, 37.25);
    REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(
                &storage.input_world, &storage.output_world, &info, 32, &route) ==
                PF_Err_BAD_CALLBACK_PARAM,
            260 + poison);
    REQUIRE(route == kRouteGeneric && storage.output == before &&
            storage.input_unchanged(), 270 + poison);
  }
  return 0;
}

static int anchor(const char* input_path, const char* output_path) {
  std::ifstream stream(input_path, std::ios::binary);
  std::vector<std::uint8_t> input((std::istreambuf_iterator<char>(stream)), {});
  REQUIRE(input.size() == 960u * 540u * 4u, 300);
  const auto original = input;
  std::vector<std::uint8_t> output(input.size(), kOutputPad);
  PF_EffectWorld in{}, out{};
  in.data = reinterpret_cast<PF_PixelPtr>(input.data());
  out.data = reinterpret_cast<PF_PixelPtr>(output.data());
  in.rowbytes = out.rowbytes = 960 * 4;
  in.width = out.width = 960;
  in.height = out.height = 540;
  auto info = Info(0, 240, 0.0, 0.5);
  info.brightness_gain = 1.0;
  int route = -1;
  REQUIRE(OLMDirectionalBlurTestRenderWorldRoute(&in, &out, &info, 8, &route) ==
              PF_Err_NONE, 301);
  REQUIRE(route == kRouteRetained && input == original, 302);
  std::ofstream(output_path, std::ios::binary).write(
      reinterpret_cast<const char*>(output.data()), output.size());
  return 0;
}

int main(int argc, char** argv) {
  REQUIRE(positive_depth<PF_Pixel8>(8) == 0, 1);
  REQUIRE(positive_depth<PF_Pixel16>(16) == 0, 2);
  REQUIRE(positive_depth<PF_PixelFloat>(32) == 0, 3);
  REQUIRE(projected_scale_matrix() == 0, 13);
  REQUIRE(retained_depth<PF_Pixel8>(8) == 0, 4);
  REQUIRE(retained_depth<PF_Pixel16>(16) == 0, 5);
  REQUIRE(retained_depth<PF_PixelFloat>(32) == 0, 6);
  REQUIRE(atomic_rejects<PF_Pixel8>(8) == 0, 7);
  REQUIRE(atomic_rejects<PF_Pixel16>(16) == 0, 8);
  REQUIRE(atomic_rejects<PF_PixelFloat>(32) == 0, 9);
  REQUIRE(deep_sdr_rejects() == 0, 10);
  if (argc == 3) REQUIRE(anchor(argv[1], argv[2]) == 0, 11);
  else REQUIRE(argc == 1, 12);
  std::puts("PASS_DBLUR_GENERIC_BACKONLY_BETA depths=8/16/32 odd=37x23 routes=retained/generic atomic=yes");
  return 0;
}
'''


def build(directory: Path, sanitize: bool) -> Path:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("C++ compiler not found")
    source = directory / "dblur_generic_backonly_probe.cpp"
    binary = directory / "dblur_generic_backonly_probe"
    source.write_text(
        CPP.replace("__PRODUCTION__", str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')),
        encoding="utf-8",
    )
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], check=True, capture_output=True, text=True
    ).stdout.strip()
    flags = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"] if sanitize else ["-O2"]
    command = [
        compiler, "-std=c++17", *flags, "-fno-fast-math", "-ffp-contract=off",
        "-ffunction-sections", "-fdata-sections", "-Wno-unused-function",
        "-Wno-unused-parameter", "-Wno-pragma-pack", "-isysroot", sdk,
        "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
        str(source), str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"), "-Wl,-dead_strip", "-framework", "Cocoa",
        "-o", str(binary),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    return binary


def main() -> int:
    local_authorities_available = verify_anchor_authorities()
    embedded_argb = embedded_anchor_source_argb()
    force_tracked_only = os.environ.get("OLM_DBLUR_TEST_FORCE_TRACKED_ONLY") == "1"
    if SOURCE_PNG.exists() and not force_tracked_only:
        from PIL import Image

        rgba = Image.open(SOURCE_PNG).convert("RGBA").tobytes()
        local_argb = bytes(
            channel
            for offset in range(0, len(rgba), 4)
            for channel in (rgba[offset + 3], rgba[offset], rgba[offset + 1], rgba[offset + 2])
        )
        if local_argb != embedded_argb:
            raise RuntimeError("embedded ARGB fixture does not match pinned source PNG")
    sanitize = os.environ.get("OLM_DBLUR_SANITIZE") == "1"
    with tempfile.TemporaryDirectory(prefix="dblur_generic_backonly_") as raw:
        directory = Path(raw)
        binary = build(directory, sanitize)
        command = [str(binary)]
        ran_production_anchor = not sanitize
        if ran_production_anchor:
            anchor_input = directory / "anchor.argb"
            anchor_output = directory / "anchor-output.argb"
            anchor_input.write_bytes(embedded_argb)
            command += [str(anchor_input), str(anchor_output)]
        result = subprocess.run(
            command, cwd=ROOT, check=False, capture_output=True, text=True, timeout=240
        )
        if result.returncode:
            raise RuntimeError(
                f"Back-only production probe rc={result.returncode}:\n{result.stdout}\n{result.stderr}"
            )
        if ran_production_anchor and sha256_bytes(anchor_output.read_bytes()) != ANCHOR_ARGB_SHA256:
            raise RuntimeError("960x540 Back240 production-dispatch raw anchor mismatch")
    print(result.stdout, end="")
    print(
        "PASS_DBLUR_GENERIC_BACKONLY_AUTHORITIES "
        f"report={ANCHOR_REPORT_SHA256} source={SOURCE_SHA256} aex={AEX_SHA256} "
        f"anchor={ANCHOR_ARGB_SHA256} "
        f"production_anchor={'yes' if ran_production_anchor else 'sanitizer-skipped'} "
        f"local_source_aex={'yes' if local_authorities_available else 'optional-or-forced-off'} "
        f"sanitizers={'asan+ubsan' if sanitize else 'off'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
