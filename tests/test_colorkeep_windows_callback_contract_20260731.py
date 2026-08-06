#!/usr/bin/env python3
"""Hostless Windows-2025 contract checks for the production ColorKeep callbacks."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac" / "ColorKeep" / "ColorKeep.cpp"
HEADER = ROOT / "mac" / "ColorKeep" / "ColorKeep.h"


class ColorKeepWindowsContractTests(unittest.TestCase):
    def test_production_entrypoint_and_bitdepth_dispatch_boundary(self):
        source = SOURCE.read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", source)
        self.assertIn('"EffectMain"', source)
        self.assertIn("casePF_Cmd_RENDER:err=Render", compact)
        self.assertIn("casePF_Cmd_SMART_PRE_RENDER:err=SmartPreRender", compact)
        self.assertIn("casePF_Cmd_SMART_RENDER:err=SmartRender", compact)
        self.assertIn("if(PF_WORLD_IS_DEEP(output))", compact)
        self.assertIn("ColorKeep16Func,output", compact)
        self.assertIn("ColorKeep8Func,output", compact)
        self.assertIn("if(bpc==8)", compact)
        self.assertIn("ColorKeep8Func,output_world", compact)
        self.assertIn("elseif(bpc==16)", compact)
        self.assertIn("ColorKeep16Func,output_world", compact)
        self.assertIn("elseif(bpc==32)", compact)
        self.assertIn("ColorKeepFloatFunc,output_world", compact)
        self.assertIn(
            "for(A_longi=0;i<COLORKEEP_MAX_COLORS&&!err;++i)", compact
        )

    def test_parameter_schema_and_zero_count_ui_boundary(self):
        source = SOURCE.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        compact_source = re.sub(r"\s+", "", source)
        compact_header = re.sub(r"\s+", "", header)

        self.assertIn("#defineCOLORKEEP_MAX_COLORS100", compact_header)
        self.assertIn(
            "COLORKEEP_INPUT=0,COLORKEEP_ENABLED_COLOR_NUM,"
            "COLORKEEP_COLOR_FIRST,COLORKEEP_NUM_PARAMS="
            "COLORKEEP_COLOR_FIRST+COLORKEEP_MAX_COLORS",
            compact_header,
        )
        self.assertIn(
            "PF_ADD_SLIDER(GetStringPtr(StrID_EnabledColorNum_Param_Name),"
            "0,COLORKEEP_MAX_COLORS,0,COLORKEEP_MAX_COLORS,1,"
            "ENABLED_COLOR_NUM_DISK_ID);",
            compact_source,
        )
        self.assertIn(
            "for(inti=0;i<COLORKEEP_MAX_COLORS;++i){"
            "AEFX_CLR_STRUCT(def);"
            "PF_ADD_COLOR(GetStringPtr(StrID_Color_Param_Name),0,0,0,"
            "COLOR_DISK_ID_FIRST+i);}",
            compact_source,
        )
        self.assertIn("out_data->num_params=COLORKEEP_NUM_PARAMS;", compact_source)

        ui_body = source[
            source.index("SetColorsEnabled(") : source.index("CheckoutInfo(")
        ]
        self.assertIn("if (enabledCount < 0) enabledCount = 0;", ui_body)
        self.assertNotIn("if (enabledCount < 1)", ui_body)

    @unittest.skipUnless(sys.platform == "darwin", "requires the local macOS AE SDK")
    def test_real_callbacks_match_argb_quantization_and_float_boundaries(self):
        harness = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

#include "mac/ColorKeep/ColorKeep.cpp"

static uint32_t FloatBits(float value)
{
    uint32_t bits = 0;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

int main()
{
    assert(FloatBits(kColorKeep8Bias) == 0x3B008081u);
    assert(FloatBits(kColorKeep8Scale) == 0x437F0000u);
    assert(FloatBits(kColorKeep16Bias) == 0x37800000u);
    assert(FloatBits(kColorKeep16Scale) == 0x47000000u);
    assert(FloatBits(kColorKeepFloatTolerance) == 0x38D1B717u);

    assert(ColorKeepQuantize8(0.1234560013f) == 31);
    assert(ColorKeepQuantize8(0.5f) == 128);
    assert(ColorKeepQuantize8(70.0f / 255.0f) == 70);
    assert(ColorKeepQuantize8(nextafterf(kColorKeep8Bias, -INFINITY)) == 0);
    assert(ColorKeepQuantize8(kColorKeep8Bias) == 1);
    assert(ColorKeepQuantize8(2.0f) == 254); // low byte; no clamp

    assert(ColorKeepQuantize16(0.1234560013f) == 4045);
    assert(ColorKeepQuantize16(0.5f) == 16384);
    assert(ColorKeepQuantize16(70.0f / 255.0f) == 8995);
    const float below16 = nextafterf(
        nextafterf(kColorKeep16Bias, -INFINITY), -INFINITY);
    assert(ColorKeepQuantize16(below16) == 0);
    assert(ColorKeepQuantize16(nextafterf(
        kColorKeep16Bias, -INFINITY)) == 1);
    assert(ColorKeepQuantize16(2.0f) == 0); // low word; no clamp

    ColorKeepInfo info;
    memset(&info, 0, sizeof(info));
    info.count = 1;
    info.colors8[0].alpha = 0;
    info.colors8[0].red = 255;
    info.colors8[0].green = 255;
    info.colors8[0].blue = 255; // poison: callbacks must use float colors
    info.colors[0].alpha = 1.0f;
    info.colors[0].red = 0.1234560013f;
    info.colors[0].green = 0.5f;
    info.colors[0].blue = 70.0f / 255.0f;

    // These match/no-match units are also captured from the hash-pinned
    // actual AEX entries 0x180001580 (PF8) and 0x180001280 (PF16).
    PF_Pixel8 in8 = {};
    in8.alpha = 255; in8.red = 31; in8.green = 128; in8.blue = 70;
    PF_Pixel8 out8 = {};
    assert(ColorKeep8Func(&info, 0, 0, &in8, &out8) == PF_Err_NONE);
    assert(out8.alpha == 255 && out8.red == 31 &&
           out8.green == 128 && out8.blue == 70);
    for (int channel = 0; channel < 4; ++channel) {
        PF_Pixel8 changed = in8;
        if (channel == 0) changed.alpha = 254;
        if (channel == 1) changed.red += 1;
        if (channel == 2) changed.green += 1;
        if (channel == 3) changed.blue += 1;
        memset(&out8, 0xA5, sizeof(out8));
        ColorKeep8Func(&info, 0, 0, &changed, &out8);
        assert(out8.alpha == 0);
        assert(out8.red == changed.red && out8.green == changed.green &&
               out8.blue == changed.blue);
    }
    info.count = 0;
    ColorKeep8Func(&info, 0, 0, &in8, &out8);
    assert(out8.alpha == 0 && out8.red == in8.red &&
           out8.green == in8.green && out8.blue == in8.blue);

    info.count = 1;
    PF_Pixel16 in16 = {};
    in16.alpha = 32768; in16.red = 4045;
    in16.green = 16384; in16.blue = 8995;
    PF_Pixel16 out16 = {};
    ColorKeep16Func(&info, 0, 0, &in16, &out16);
    assert(out16.alpha == 32768 && out16.red == 4045 &&
           out16.green == 16384 && out16.blue == 8995);
    for (int channel = 0; channel < 4; ++channel) {
        PF_Pixel16 changed = in16;
        if (channel == 0) changed.alpha -= 1;
        if (channel == 1) changed.red += 1;
        if (channel == 2) changed.green += 1;
        if (channel == 3) changed.blue += 1;
        memset(&out16, 0xA5, sizeof(out16));
        ColorKeep16Func(&info, 0, 0, &changed, &out16);
        assert(out16.alpha == 0);
        assert(out16.red == changed.red && out16.green == changed.green &&
               out16.blue == changed.blue);
    }

    // Five-color PF8/PF16 actual-AEX fixtures cover the four-color unrolled
    // group and the fifth scalar-tail color independently at each depth.
    const PF_PixelFloat integerColors[5] = {
        {1.00f, 0.00f, 0.25f, 0.50f},
        {0.75f, 0.25f, 0.50f, 0.75f},
        {0.50f, 0.50f, 0.75f, 1.00f},
        {0.25f, 0.75f, 1.00f, 0.00f},
        {1.00f, 1.00f, 0.00f, 0.25f},
    };
    memset(&info, 0, sizeof(info));
    info.count = 5;
    memcpy(info.colors, integerColors, sizeof(integerColors));
    const int integerMatchIndices[3] = {0, 3, 4};
    const PF_Pixel8 inputs8[5] = {
        {255, 0, 64, 128}, {191, 64, 128, 191}, {128, 128, 191, 255},
        {64, 191, 255, 0}, {255, 255, 0, 64},
    };
    const PF_Pixel16 inputs16[5] = {
        {32768, 0, 8192, 16384}, {24576, 8192, 16384, 24576},
        {16384, 16384, 24576, 32768}, {8192, 24576, 32768, 0},
        {32768, 32768, 0, 8192},
    };
    for (int index : integerMatchIndices) {
        ColorKeep8Func(&info, 0, 0,
                       const_cast<PF_Pixel8*>(&inputs8[index]), &out8);
        assert(memcmp(&out8, &inputs8[index], sizeof(out8)) == 0);
        ColorKeep16Func(&info, 0, 0,
                        const_cast<PF_Pixel16*>(&inputs16[index]), &out16);
        assert(memcmp(&out16, &inputs16[index], sizeof(out16)) == 0);
    }
    PF_Pixel8 noMatch8 = inputs8[4];
    noMatch8.red -= 1;
    ColorKeep8Func(&info, 0, 0, &noMatch8, &out8);
    assert(out8.alpha == 0 && out8.red == noMatch8.red &&
           out8.green == noMatch8.green && out8.blue == noMatch8.blue);
    PF_Pixel16 noMatch16 = inputs16[4];
    noMatch16.red -= 1;
    ColorKeep16Func(&info, 0, 0, &noMatch16, &out16);
    assert(out16.alpha == 0 && out16.red == noMatch16.red &&
           out16.green == noMatch16.green && out16.blue == noMatch16.blue);

    PF_PixelFloat in32 = {};
    PF_PixelFloat out32 = {};
    memset(&info.colors[0], 0, sizeof(info.colors[0]));
    in32.alpha = kColorKeepFloatTolerance;
    ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
    assert(out32.alpha == kColorKeepFloatTolerance);
    in32.alpha = nextafterf(kColorKeepFloatTolerance, INFINITY);
    ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
    assert(out32.alpha == 0.0f);

    for (int channel = 0; channel < 3; ++channel) {
        memset(&info.colors[0], 0, sizeof(info.colors[0]));
        memset(&in32, 0, sizeof(in32));
        info.colors[0].alpha = 0.75f;
        in32.alpha = 0.75f;
        float *component = channel == 0 ? &in32.red :
                           channel == 1 ? &in32.green : &in32.blue;
        *component = kColorKeepFloatTolerance;
        ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
        assert(out32.alpha == 0.75f);
        *component = nextafterf(kColorKeepFloatTolerance, INFINITY);
        ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
        assert(out32.alpha == 0.0f);
        assert(out32.red == in32.red && out32.green == in32.green &&
               out32.blue == in32.blue);
    }

    // Windows uses COMISS/JA, so unordered differences fall through as
    // matches. Preserve this only as a Windows-2025 PF32 callback fact.
    memset(&info.colors[0], 0, sizeof(info.colors[0]));
    memset(&in32, 0, sizeof(in32));
    info.colors[0].alpha = 0.75f;
    in32.alpha = 0.75f;
    in32.red = NAN;
    ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
    assert(out32.alpha == 0.75f);
    assert(isnan(out32.red));

    info.colors[0].red = NAN;
    in32.red = 0.25f;
    ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
    assert(out32.alpha == 0.75f);

    // Actual-AEX five-color fixtures exercise both its four-color unrolled
    // group and scalar tail. These values are kept in ARGB field order here.
    const PF_PixelFloat fiveColors[5] = {
        {1.0f, 0.10f, 0.20f, 0.30f},
        {0.9f, 0.15f, 0.25f, 0.35f},
        {0.8f, 0.40f, 0.50f, 0.60f},
        {0.7f, 0.65f, 0.75f, 0.85f},
        {0.6f, 0.123456f, 0.234567f, 0.345678f},
    };
    memset(&info, 0, sizeof(info));
    info.count = 5;
    memcpy(info.colors, fiveColors, sizeof(fiveColors));
    const int matchIndices[3] = {0, 3, 4};
    for (int index : matchIndices) {
        in32 = fiveColors[index];
        memset(&out32, 0xA5, sizeof(out32));
        ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
        assert(memcmp(&out32, &in32, sizeof(out32)) == 0);
    }
    in32 = {0.55f, 0.91f, 0.81f, 0.71f};
    ColorKeepFloatFunc(&info, 0, 0, &in32, &out32);
    assert(out32.alpha == 0.0f);
    assert(out32.red == in32.red && out32.green == in32.green &&
           out32.blue == in32.blue);
    return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix="colorkeep_callbacks_") as raw:
            temp = Path(raw)
            harness_path = temp / "colorkeep_callbacks.cpp"
            executable = temp / "colorkeep_callbacks"
            harness_path.write_text(harness, encoding="utf-8")
            compile_result = subprocess.run(
                [
                    "xcrun",
                    "clang++",
                    "-std=c++17",
                    "-D__MACH__",
                    "-Wno-pragma-pack",
                    "-I.",
                    "-IHeaders",
                    "-IHeaders/SP",
                    "-IUtil",
                    "-IResources",
                    str(harness_path),
                    "mac/ColorKeep/ColorKeep_Strings.cpp",
                    "Util/AEGP_SuiteHandler.cpp",
                    "Util/MissingSuiteError.cpp",
                    "-framework",
                    "Cocoa",
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                compile_result.returncode,
                0,
                compile_result.stdout + compile_result.stderr,
            )
            run_result = subprocess.run(
                [str(executable)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                run_result.returncode, 0, run_result.stdout + run_result.stderr
            )


if __name__ == "__main__":
    unittest.main()
