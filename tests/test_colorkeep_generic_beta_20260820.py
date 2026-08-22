from __future__ import annotations

import os
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"


def test_generic_admission_is_not_fixture_bound() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "sha256_active_rows_match_hex",
        "ColorKeepNineSourceMatches",
        "ColorKeepPublicPaletteMatches",
        "kColorKeepPublicWidth",
        "kColorKeepPublicPadding",
    ):
        assert forbidden not in source
    assert "count >= 1 && count <= COLORKEEP_MAX_COLORS" in source

    # Fix the public contract through production behavior, not local variable
    # names: the real worker must admit arbitrary worlds/strides at every depth,
    # and the exported Classic/Smart entries must preserve ROI and failure
    # atomicity across their checkout/checkin lifecycle.
    test_generic_worlds_counts_and_typed_workers()
    roi_path = ROOT / "tests/test_colorkeep_roi_tile_beta_20260820.py"
    spec = importlib.util.spec_from_file_location("colorkeep_roi_contract", roi_path)
    assert spec is not None and spec.loader is not None
    roi_contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(roi_contract)
    roi_contract.test_exported_effectmain_nonzero_origin_classic_and_smart()


def test_checkout_cleanup_contract_and_windows_owner_evidence() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "!extra->cb->checkin_layer_pixels ||" in source
    assert "if (input_checked_out && extra->cb->checkin_layer_pixels)" in source
    assert "if (checked_out[i])" in source
    assert "PF_CHECKIN_PARAM(in_data, &checked_params[i])" in source

    report_path = ROOT / "refs/conformance/colorkeep_thirteen_color_effectmain_actual_aex_20260805.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "exact"
    assert report["enabled_colors"] == 13
    assert report["dynamic_effectmain_paths"] == [
        "legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8",
        "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32",
    ]


def test_generic_worlds_counts_and_typed_workers() -> None:
    pf816_report = json.loads(
        (ROOT / "refs/conformance/colorkeep_pf8_pf16_multicolor_actual_aex_20260805.json")
        .read_text(encoding="utf-8")
    )
    pf32_report = json.loads(
        (ROOT / "refs/conformance/colorkeep_pf32_multicolor_actual_aex_20260805.json")
        .read_text(encoding="utf-8")
    )
    assert pf816_report["status"] == pf32_report["status"] == "exact"
    assert pf816_report["aex_sha256"] == pf32_report["aex_sha256"]
    assert pf816_report["aex_sha256"] == (
        "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
    )
    assert pf816_report["scope"]["paths"] == pf32_report["scope"]["paths"] == [
        "four-color unrolled group", "one-color scalar tail",
    ]

    def words(rows: list[list[str]]) -> str:
        return ",\n        ".join(
            "{" + ", ".join(f"{int(value, 16)}u" for value in row) + "}" for row in rows
        )

    def units(rows: list[list[int]]) -> str:
        return ",\n        ".join("{" + ", ".join(str(value) for value in row) + "}" for row in rows)

    case_order = ("first_unrolled_match", "fourth_unrolled_match", "fifth_tail_match", "no_match")
    win_float_colors = words(pf816_report["colors_argb_f32_bits"])
    win_pf8_sources = units([
        pf816_report["depth_results"]["PF8"]["cases"][name]["source_argb_units"]
        for name in case_order
    ])
    win_pf8_expected = units([
        pf816_report["depth_results"]["PF8"]["cases"][name]["observed_argb_units"]
        for name in case_order
    ])
    win_pf16_sources = units([
        pf816_report["depth_results"]["PF16"]["cases"][name]["source_argb_units"]
        for name in case_order
    ])
    win_pf16_expected = units([
        pf816_report["depth_results"]["PF16"]["cases"][name]["observed_argb_units"]
        for name in case_order
    ])
    win_pf32_colors = words(pf32_report["enabled_color_argb_bits"])
    win_pf32_sources = words([
        pf32_report["cases"][name]["source_argb_bits"] for name in case_order
    ])
    win_pf32_expected = words([
        pf32_report["cases"][name]["observed_argb_bits"] for name in case_order
    ])

    probe = f'''#include <cstdint>
#include <cstring>
#include <vector>
#include "{SOURCE}"

template <class P>
static bool valid_world(A_long width, A_long height, A_long input_padding,
                        A_long output_padding, short depth,
                        A_long origin_x=0, A_long origin_y=0,
                        PF_WorldFlags additional_flags=0) {{
    const A_long input_rb = width * (A_long)sizeof(P) + input_padding;
    const A_long output_rb = width * (A_long)sizeof(P) + output_padding;
    std::vector<P> input_storage(((size_t)input_rb * height + sizeof(P) - 1) / sizeof(P));
    std::vector<P> output_storage(((size_t)output_rb * height + sizeof(P) - 1) / sizeof(P));
    PF_EffectWorld input = {{}}, output = {{}};
    input.data = reinterpret_cast<PF_PixelPtr>(input_storage.data());
    output.data = reinterpret_cast<PF_PixelPtr>(output_storage.data());
    input.width = output.width = width;
    input.height = output.height = height;
    input.rowbytes = input_rb;
    output.rowbytes = output_rb;
    input.extent_hint.left = output.extent_hint.left = origin_x;
    input.extent_hint.top = output.extent_hint.top = origin_y;
    input.extent_hint.right = output.extent_hint.right = origin_x + width;
    input.extent_hint.bottom = output.extent_hint.bottom = origin_y + height;
    input.origin_x = output.origin_x = origin_x;
    input.origin_y = output.origin_y = origin_y;
    input.world_flags = output.world_flags =
        (depth == 16 ? PF_WorldFlag_DEEP : 0) | additional_flags;
    return ColorKeepValidateWorldPair(&input, &output, depth) == PF_Err_NONE;
}}

template <class P, class F>
static bool exercise(A_long width, A_long height, A_long input_padding,
                     A_long output_padding, A_long count, short depth, F worker) {{
    const size_t input_rb = (size_t)width * sizeof(P) + input_padding;
    const size_t output_rb = (size_t)width * sizeof(P) + output_padding;
    std::vector<P> input_storage((input_rb * height + sizeof(P) - 1) / sizeof(P));
    std::vector<P> output_storage((output_rb * height + sizeof(P) - 1) / sizeof(P));
    unsigned char *input = reinterpret_cast<unsigned char *>(input_storage.data());
    unsigned char *output = reinterpret_cast<unsigned char *>(output_storage.data());
    std::memset(input, 0x31, input_rb * height);
    std::memset(output, 0xa5, output_rb * height);
    ColorKeepInfo info = {{}};
    info.count = count;
    info.colors[0] = PF_PixelFloat{{1.0f, 0.25f, 0.5f, 0.75f}};
    for (A_long i = 1; i < count; ++i)
        info.colors[i] = PF_PixelFloat{{1.0f, i / 101.0f, i / 103.0f, i / 107.0f}};
    for (A_long y = 0; y < height; ++y) {{
        for (A_long x = 0; x < width; ++x) {{
            P *in = reinterpret_cast<P *>(input + y * input_rb + x * sizeof(P));
            P *out = reinterpret_cast<P *>(output + y * output_rb + x * sizeof(P));
            worker(&info, x, y, in, out);
        }}
        for (size_t x = (size_t)width * sizeof(P); x < output_rb; ++x)
            if (output[y * output_rb + x] != 0xa5) return false;
    }}
    return true;
}}

int main() {{
    if (!ColorKeepCountIsAdmitted(1) || !ColorKeepCountIsAdmitted(13) ||
        !ColorKeepCountIsAdmitted(100) || ColorKeepCountIsAdmitted(0) ||
        ColorKeepCountIsAdmitted(101)) return 1;
    if (!valid_world<PF_Pixel8>(1, 1, 0, 12, 8)) return 2;
    if (!valid_world<PF_Pixel16>(17, 11, 6, 22, 16)) return 3;
    if (!valid_world<PF_PixelFloat>(9, 7, 32, 0, 32)) return 4;
    if (!valid_world<PF_Pixel8>(1920, 1080, 64, 16, 8)) return 9;
    if (!valid_world<PF_Pixel8>(37, 19, 20, 4, 8, 311, -207)) return 18;
    if (!valid_world<PF_Pixel16>(23, 17, 8, 40, 16, -91, 53)) return 19;
    if (!valid_world<PF_PixelFloat>(13, 7, 48, 16, 32, 4096, 2048)) return 20;
    if (!valid_world<PF_Pixel8>(19, 13, 8, 24, 8, 0, 0,
                                PF_WorldFlag_RESERVED0)) return 21;
    if (!valid_world<PF_Pixel16>(19, 13, 8, 24, 16, 0, 0,
                                 PF_WorldFlag_RESERVED0)) return 22;
    if (!valid_world<PF_PixelFloat>(19, 13, 8, 24, 32, 0, 0,
                                    PF_WorldFlag_RESERVED0)) return 23;
    if (!exercise<PF_Pixel8>(1, 1, 0, 12, 1, 8, ColorKeep8Func)) return 10;
    if (!exercise<PF_Pixel8>(17, 11, 12, 4, 5, 8, ColorKeep8Func)) return 11;
    if (!exercise<PF_Pixel16>(1920, 1080, 32, 64, 9, 16, ColorKeep16Func)) return 12;
    if (!exercise<PF_PixelFloat>(3840, 2160, 64, 16, 13, 32, ColorKeepFloatFunc)) return 13;
    if (!exercise<PF_Pixel8>(127, 73, 4, 28, 100, 8, ColorKeep8Func)) return 14;

    alignas(PF_Pixel8) unsigned char malformed_in[32] = {{0}}, malformed_out[32] = {{0}};
    PF_EffectWorld bad_in = {{}}, bad_out = {{}};
    bad_in.data = reinterpret_cast<PF_PixelPtr>(malformed_in);
    bad_out.data = reinterpret_cast<PF_PixelPtr>(malformed_out);
    bad_in.width = bad_out.width = 4; bad_in.height = bad_out.height = 1;
    bad_in.rowbytes = 15; bad_out.rowbytes = 16;
    bad_in.extent_hint = bad_out.extent_hint = PF_LRect{{0, 0, 4, 1}};
    if (ColorKeepValidateWorldPair(&bad_in, &bad_out, 8) == PF_Err_NONE) return 15;
    bad_in.rowbytes = 16; bad_out.origin_x = 1;
    if (ColorKeepValidateWorldPair(&bad_in, &bad_out, 8) == PF_Err_NONE) return 16;
    bad_out.origin_x = 0; bad_out.data = bad_in.data;
    if (ColorKeepValidateWorldPair(&bad_in, &bad_out, 8) == PF_Err_NONE) return 17;

    PF_InData render_data = {{}};
    PF_EffectWorld tile_output = {{}};
    tile_output.origin_x = render_data.output_origin_x = 311;
    tile_output.origin_y = render_data.output_origin_y = -207;
    render_data.downsample_x.num = render_data.downsample_x.den = 1;
    render_data.downsample_y.num = render_data.downsample_y.den = 1;
    if (!ColorKeepIsOneToOne(&render_data, &tile_output)) return 21;
    render_data.downsample_x.num = 2;
    if (ColorKeepIsOneToOne(&render_data, &tile_output)) return 22;
    render_data.downsample_x.num = 1; render_data.output_origin_x++;
    if (ColorKeepIsOneToOne(&render_data, &tile_output)) return 23;

    ColorKeepInfo info = {{}};
    info.count = 1;
    info.colors[0] = PF_PixelFloat{{1.0f, 0.25f, 0.5f, 0.75f}};
    PF_Pixel8 in8{{255, 64, 128, 191}}, out8{{}};
    if (ColorKeep8Func(&info, 0, 0, &in8, &out8) ||
        std::memcmp(&in8, &out8, sizeof(in8))) return 5;
    in8.red = 63;
    if (ColorKeep8Func(&info, 0, 0, &in8, &out8) || out8.alpha != 0 ||
        out8.red != in8.red || out8.green != in8.green || out8.blue != in8.blue) return 6;

    PF_PixelFloat inf{{1.0f, 0.25005f, 0.5f, 0.75f}}, outf{{}};
    if (ColorKeepFloatFunc(&info, 0, 0, &inf, &outf) || outf.alpha != inf.alpha) return 7;
    inf.red = 0.251f;
    if (ColorKeepFloatFunc(&info, 0, 0, &inf, &outf) || outf.alpha != 0.0f) return 8;

    // Bind the current production callbacks to the tracked Windows 2025 AEX
    // worker oracle. These are the same five-color unrolled/tail match and
    // no-match calls recorded in the two conformance reports loaded above.
    const uint32_t pf816_color_bits[5][4] = {{
        {win_float_colors}
    }};
    ColorKeepInfo win816 = {{}};
    win816.count = 5;
    std::memcpy(win816.colors, pf816_color_bits, sizeof(pf816_color_bits));
    const uint8_t pf8_source[4][4] = {{
        {win_pf8_sources}
    }};
    const uint8_t pf8_expected[4][4] = {{
        {win_pf8_expected}
    }};
    for (int i = 0; i < 4; ++i) {{
        PF_Pixel8 source{{pf8_source[i][0], pf8_source[i][1], pf8_source[i][2], pf8_source[i][3]}};
        PF_Pixel8 actual{{}};
        if (ColorKeep8Func(&win816, 0, 0, &source, &actual) ||
            std::memcmp(&actual, pf8_expected[i], sizeof(actual))) return 24 + i;
    }}
    const uint16_t pf16_source[4][4] = {{
        {win_pf16_sources}
    }};
    const uint16_t pf16_expected[4][4] = {{
        {win_pf16_expected}
    }};
    for (int i = 0; i < 4; ++i) {{
        PF_Pixel16 source{{pf16_source[i][0], pf16_source[i][1], pf16_source[i][2], pf16_source[i][3]}};
        PF_Pixel16 actual{{}};
        if (ColorKeep16Func(&win816, 0, 0, &source, &actual) ||
            std::memcmp(&actual, pf16_expected[i], sizeof(actual))) return 28 + i;
    }}

    const uint32_t pf32_color_bits[5][4] = {{
        {win_pf32_colors}
    }};
    ColorKeepInfo win32 = {{}};
    win32.count = 5;
    std::memcpy(win32.colors, pf32_color_bits, sizeof(pf32_color_bits));
    const uint32_t pf32_source_bits[4][4] = {{
        {win_pf32_sources}
    }};
    const uint32_t pf32_expected_bits[4][4] = {{
        {win_pf32_expected}
    }};
    for (int i = 0; i < 4; ++i) {{
        PF_PixelFloat source{{}}, actual{{}};
        std::memcpy(&source, pf32_source_bits[i], sizeof(source));
        if (ColorKeepFloatFunc(&win32, 0, 0, &source, &actual) ||
            std::memcmp(&actual, pf32_expected_bits[i], sizeof(actual))) return 32 + i;
    }}
    return 0;
}}
'''
    with tempfile.TemporaryDirectory(prefix="colorkeep-generic-beta-") as raw:
        directory = Path(raw)
        cpp = directory / "probe.cpp"
        executable = directory / "probe"
        cpp.write_text(probe, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            "clang++", "-std=c++17", "-O1", "-g", "-arch", "arm64", "-isysroot", sdk,
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources",
            str(cpp), str(ROOT / "mac/ColorKeep/ColorKeep_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"), "-framework", "Cocoa", "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        environment = os.environ.copy()
        environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1"
        run = subprocess.run([str(executable)], cwd=ROOT, text=True, capture_output=True, env=environment)
        assert run.returncode == 0, run.stdout + run.stderr
