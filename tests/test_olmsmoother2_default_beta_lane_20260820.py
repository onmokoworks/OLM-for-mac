from __future__ import annotations

import re
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"


def function_body(text: str, name: str, next_name: str) -> str:
    return text.split(name, 1)[1].split(next_name, 1)[0]


class OLMSmoother2DefaultBetaLane(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SOURCE.read_text()
        cls.beta = function_body(
            cls.text, "V2GenericBetaAdmission(", "ValidatePublicWorlds("
        )
        cls.validate = function_body(
            cls.text, "ValidatePublicWorlds(", "// Classic Render"
        )
        cls.smart = function_body(cls.text, "SmartRender(", "// Entry point")

    def test_lane_is_source_identity_free_and_bounded_to_proven_axes(self) -> None:
        self.assertNotIn("V2SourceIs", self.beta)
        self.assertNotRegex(self.beta, r'"[0-9a-f]{64}"')
        for contract in (
            "depth != 8 && depth != 16 && depth != 32",
            "world->width < 1",
            "world->height < 1",
            "world->width > 8192",
            "world->height > 8192",
            "version == SMOOTHER_V1 || version == SMOOTHER_V2",
            "gamma_mode == GAMMA_NONE || gamma_mode == GAMMA_ALL_COLORS",
            "gamma_mode == GAMMA_COLORS_ONLY",
            "smoothness >= 0 && smoothness <= 100",
            "smooth_range >= 0 && smooth_range <= 100",
            "extra_smooth >= 0 && extra_smooth <= 100",
            "std::isfinite(gamma_value)",
            "gamma_ui_max = (A_FpLong)(float)2.4f",
        ):
            self.assertIn(contract, self.beta)

    def test_input_and_output_rowbytes_are_independently_legal(self) -> None:
        self.assertNotIn("input->rowbytes != output->rowbytes", self.validate)
        self.assertIn("input->rowbytes < input->width * pixel_size", self.validate)
        self.assertIn("output->rowbytes < output->width * pixel_size", self.validate)
        self.assertIn("input_span", self.validate)
        self.assertIn("output_span", self.validate)

    def test_smart_route_preserves_exact_fixture_precedence_then_uses_beta(self) -> None:
        self.assertIn("const bool retained_fixture", self.smart)
        self.assertIn("const bool generic_beta", self.smart)
        self.assertRegex(
            self.smart,
            re.compile(
                r"generic_beta\s*=\s*!err\s*&&\s*!retained_fixture\s*&&\s*"
                r"V2GenericBetaAdmission",
                re.MULTILINE,
            ),
        )
        self.assertIn(
            "retained_fixture && input_world->width == 1920", self.smart
        )
        self.assertRegex(
            self.smart,
            re.compile(
                r"!retained_fixture\s*&&\s*!generic_beta", re.MULTILINE
            ),
        )

    def test_effectmain_accepts_arbitrary_source_at_all_depths(self) -> None:
        harness = ROOT / "tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp"
        program = f'''\
#define main retained_guard_main
#include "{harness}"
#undef main

static int beta_case(int depth, int w = 19, int h = 17, int variant = 0) {{
    const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
    Fixture f(depth, w, h, 5);
    std::memset(f.defs, 0, sizeof(f.defs));
    for (int i = 0; i < SM_NUM_PARAMS; ++i) f.params[i] = f.defs + i;
    f.defs[SM_INPUT].u.ld = f.iw;
    f.defs[SM_KEY_COLOR].u.cd.value = {{255,255,255,255}};
    f.defs[SM_SMOOTHNESS].u.sd.value = 100;
    f.defs[SM_EXTRA_SMOOTH].u.sd.value = 0;
    f.defs[SM_SMOOTH_RANGE].u.sd.value = 2;
    f.defs[SM_VERSION].u.pd.value = SMOOTHER_V2;
    f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    f.defs[SM_GAMMA_VALUE].u.fs_d.value = (double)(float)2.4f;
    f.defs[SM_NUM_GAMMA_COLORS].u.sd.value = 1;
    if (variant == 1) {{
        f.defs[SM_VERSION].u.pd.value = SMOOTHER_V1;
        f.defs[SM_SMOOTHNESS].u.sd.value = 0;
        f.defs[SM_SMOOTH_RANGE].u.sd.value = 0;
        f.defs[SM_EXTRA_SMOOTH].u.sd.value = 100;
        f.defs[SM_GAMMA_VALUE].u.fs_d.value = 1.0;
    }} else if (variant == 2) {{
        f.defs[SM_ENABLE_KEY].u.bd.value = 1;
        f.defs[SM_SMOOTHNESS].u.sd.value = 1;
        f.defs[SM_SMOOTH_RANGE].u.sd.value = 100;
        f.defs[SM_EXTRA_SMOOTH].u.sd.value = 1;
    }} else if (variant == 3) {{
        f.defs[SM_ENABLE_KEY].u.bd.value = 1;
        f.defs[SM_INVERT_KEY].u.bd.value = 1;
        f.defs[SM_VERSION].u.pd.value = SMOOTHER_V1;
        f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_ALL_COLORS;
        f.defs[SM_GAMMA_VALUE].u.fs_d.value = 1.0;
        f.defs[SM_SMOOTHNESS].u.sd.value = 50;
        f.defs[SM_SMOOTH_RANGE].u.sd.value = 50;
        f.defs[SM_EXTRA_SMOOTH].u.sd.value = 50;
    }} else if (variant == 4) {{
        f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_ALL_COLORS;
        f.defs[SM_SMOOTHNESS].u.sd.value = 99;
        f.defs[SM_SMOOTH_RANGE].u.sd.value = 99;
        f.defs[SM_EXTRA_SMOOTH].u.sd.value = 99;
    }}
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w * pixel_size; ++x)
            f.input[(size_t)y * f.iw.rowbytes + x] = (unsigned char)(x * 17 + y * 31 + depth);
    const std::vector<unsigned char> original = f.input;
    f.ow.rowbytes = w * pixel_size + 11;
    f.output.assign((size_t)f.ow.rowbytes * h, 0xa5);
    f.ow.data = f.output.data();
    if (Smart(f) != 0 || f.input != original) return 10 + depth;
    for (int y = 0; y < h; ++y)
        for (int x = w * pixel_size; x < f.ow.rowbytes; ++x)
            if (f.output[(size_t)y * f.ow.rowbytes + x] != 0xa5) return 20 + depth;
    const std::vector<unsigned char> first = f.output;
    std::fill(f.output.begin(), f.output.end(), 0xa5);
    f.ow.data = f.output.data();
    if (Smart(f) != 0 || f.output != first || f.input != original) return 30 + depth;
    return 0;
}}

int main() {{
    for (int depth : {{8,16,32}})
        for (int variant = 0; variant < 5; ++variant)
            if (int e = beta_case(depth, 19, 17, variant)) return e;
    if (const char *selected = std::getenv("SM2_BETA_GEOMETRY")) {{
        const int w = std::strcmp(selected, "hd") == 0 ? 1920 :
                      std::strcmp(selected, "uhd") == 0 ? 3840 : 0;
        const int h = w == 1920 ? 1080 : w == 3840 ? 2160 : 0;
        if (!w || !h) return 89;
        for (int depth : {{8,16,32}}) {{
            const int representative = w == 1920 ?
                (depth == 8 ? 1 : depth == 16 ? 3 : 4) : 0;
            if (int e = beta_case(depth, w, h, representative)) return e;
        }}
    }}
    if (std::getenv("SM2_BETA_EXTENDED")) {{
        const int geometry[][2] = {{
            {{16,16}}, {{853,479}}, {{720,480}}, {{1920,1080}}, {{3840,2160}}
        }};
        for (int depth : {{8,16,32}})
            for (const auto &g : geometry)
                if (int e = beta_case(depth, g[0], g[1])) return e;
    }}

    // Synthesize every c280 index directly. This exercises all dispatch leaves
    // without depending on whether a natural image happens to generate them.
    std::vector<unsigned char> cp(5 * 5 * 4, 0xff);
    std::vector<FPix> fp(5 * 5, FPix{{0.5f,0.5f,0.5f,1.0f}});
    FPlane plane{{fp.data(), 5 * sizeof(FPix), 0}};
    SMParams sp{{}}; sp.class_plane = cp.data(); sp.w = 5; sp.h = 5;
    sp.smoothness_raw = 100; sp.extra_smooth_raw = 0;
    for (int index = 0; index < 256; ++index) {{
        std::fill(cp.begin(), cp.end(), 0xff);
        unsigned char *center = cp.data() + (2 * 5 + 2) * 4;
        center[0] = (index & 8) ? 0 : 0xff;
        center[1] = (index & 2) ? 0 : 0xff;
        center[2] = (index & 1) ? 0 : 0xff;
        center[3] = (index & 4) ? 0 : 0xff;
        cp[(3 * 5 + 1) * 4 + 3] = (index & 0x20) ? 0 : 0xff;
        cp[(2 * 5 + 3) * 4 + 0] = (index & 0x10) ? 0 : 0xff;
        cp[(3 * 5 + 2) * 4 + 1] = (index & 0x40) ? 0 : 0xff;
        cp[(3 * 5 + 3) * 4 + 2] = (index & 0x80) ? 0 : 0xff;
        SmootherPolygon poly{{}};
        OLMSmoother2ResetIndexHistogram(true);
        build_polygon(poly, plane, 2, 2, sp);
        if (g_olmsmoother2_index_hist[index] != 1) return 100 + index;
    }}

    Fixture small(8, 15, 16, 5);
    std::memset(small.defs, 0, sizeof(small.defs));
    for (int i = 0; i < SM_NUM_PARAMS; ++i) small.params[i] = small.defs + i;
    small.defs[SM_INPUT].u.ld = small.iw;
    small.defs[SM_SMOOTHNESS].u.sd.value = 100;
    small.defs[SM_SMOOTH_RANGE].u.sd.value = 2;
    small.defs[SM_VERSION].u.pd.value = SMOOTHER_V2;
    small.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    small.defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
    small.defs[SM_NUM_GAMMA_COLORS].u.sd.value = 1;
    // Exported AEX positive-dimension witnesses supersede the old beta-only
    // 16x16 exclusion. The ordinary full-world checks still apply.
    if (Smart(small) != 0) return 90;
    Fixture excluded(8, 19, 17, 5);
    std::memset(excluded.defs, 0, sizeof(excluded.defs));
    excluded.defs[SM_SMOOTHNESS].u.sd.value = 100;
    excluded.defs[SM_SMOOTH_RANGE].u.sd.value = 2;
    excluded.defs[SM_VERSION].u.pd.value = SMOOTHER_V2;
    excluded.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY;
    excluded.defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
    excluded.defs[SM_NUM_GAMMA_COLORS].u.sd.value = 1;
    if (Smart(excluded) != 0) return 91;
    excluded.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
    excluded.defs[SM_GAMMA_VALUE].u.fs_d.value = 2.400001;
    if (Smart(excluded) == 0) return 92;
    return 0;
}}
'''
        with tempfile.TemporaryDirectory(prefix="olmsmoother2-beta-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(program)
            subprocess.run(
                [
                    "clang++", "-std=c++17", "-O1", "-g",
                    "-fno-omit-frame-pointer", "-fsanitize=address,undefined",
                    "-I", str(ROOT / "cli/OLMSmoother2/shim"),
                    "-I", str(ROOT / "mac/OLMSmoother2"),
                    str(source), "-o", str(binary),
                ],
                check=True,
            )
            sanitizer_env = {
                "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1",
                "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
            }
            if os.environ.get("SM2_BETA_EXTENDED"):
                sanitizer_env["SM2_BETA_EXTENDED"] = "1"
            if geometry := os.environ.get("OLM_PERF_GEOMETRY"):
                sanitizer_env["SM2_BETA_GEOMETRY"] = geometry
            subprocess.run(
                [str(binary)], check=True,
                # Apple's ASan runtime does not implement LeakSanitizer.
                env=sanitizer_env,
            )


if __name__ == "__main__":
    unittest.main()
