from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp"


class OLMSmoother2GammaColorsBeta(unittest.TestCase):
    def test_windows_gamma_palette_evidence_is_bounded(self) -> None:
        evidence = {
            "olmsmoother2_v2_gamma_colors_actual_aex_20260805.json": 1,
            "olmsmoother2_v2_gamma_palette2_actual_aex_20260805.json": 2,
            "olmsmoother2_v2_gamma_palette3_actual_aex_20260805.json": 3,
            "olmsmoother2_v2_gamma_palette4_actual_aex_20260805.json": 4,
            "olmsmoother2_v2_gamma_palette5_actual_aex_20260805.json": 5,
            "olmsmoother2_v2_gamma_palette5_reordered_actual_aex_20260805.json": 5,
            "olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805.json": 3,
            "olmsmoother2_v2_gamma_palette_tolerance_actual_aex_20260805.json": 2,
        }
        aex_sha = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
        for filename, active_count in evidence.items():
            report = json.loads((ROOT / "refs/conformance" / filename).read_text())
            self.assertEqual(report["aex_sha256"], aex_sha)
            self.assertTrue(report["verdict"].startswith("PASS_V2_GAMMA_COLORS_"))
            self.assertIn("PF16/PF32", report["scope"])
            self.assertIn("No AE host claim", report["claims_not_made"])
            self.assertEqual(
                [(fixture["depth"], fixture["equal"], fixture["padding_preserved"])
                 for fixture in report["fixtures"]],
                [("PF16", True, True), ("PF32", True, True)],
            )
            if filename.endswith("gamma_colors_actual_aex_20260805.json"):
                self.assertEqual(report["parameter_contract"]["gamma_color_count"], active_count)
            else:
                self.assertEqual(len(report["palette_contract"]["ordered_rgba"]), active_count)

    def test_arbitrary_source_palette_semantics_all_depths(self) -> None:
        compiler = shutil.which("clang++")
        if not compiler:
            self.skipTest("clang++ unavailable")
        program = f'''\
#define main retained_guard_main
#include "{HARNESS}"
#undef main

static int gamma_case(int depth, int count, int variant) {{
    const int w = 19, h = 17;
    const int ps = depth == 8 ? 4 : depth == 16 ? 8 : 16;
    Fixture f(depth, w, h, 9);
    std::memset(f.defs, 0, sizeof(f.defs));
    f.defs[SM_INPUT].u.ld = f.iw;
    f.defs[SM_KEY_COLOR].u.cd.value = {{255,17,31,47}};
    f.defs[SM_SMOOTHNESS].u.sd.value = 63;
    f.defs[SM_EXTRA_SMOOTH].u.sd.value = 29;
    f.defs[SM_SMOOTH_RANGE].u.sd.value = 41;
    f.defs[SM_VERSION].u.pd.value = variant == 3 ? SMOOTHER_V1 : SMOOTHER_V2;
    f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY;
    f.defs[SM_GAMMA_VALUE].u.fs_d.value = variant == 2 ? 1.0 : (double)(float)2.4f;
    f.defs[SM_NUM_GAMMA_COLORS].u.sd.value = count;
    const PF_Pixel colors[5] = {{
        {{255,255,0,0}}, {{255,0,255,0}}, {{255,255,0,0}},
        {{0,0,0,255}}, {{127,9,9,9}}
    }};
    for (int i = 0; i < 5; ++i) f.defs[SM_GAMMA_COLOR_0+i].u.cd.value = colors[i];
    if (variant == 1) std::swap(f.defs[SM_GAMMA_COLOR_0].u.cd.value,
                                f.defs[SM_GAMMA_COLOR_1].u.cd.value);
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w * ps; ++x)
            f.input[(size_t)y * f.iw.rowbytes + x] = (unsigned char)(x*23 + y*37 + depth);
    const auto original = f.input;
    f.ow.rowbytes = w * ps + 15;
    f.output.assign((size_t)f.ow.rowbytes * h, 0xa5);
    f.ow.data = f.output.data();
    if (Smart(f) || f.input != original) return 10 + depth;
    for (int y = 0; y < h; ++y)
        for (int x = w * ps; x < f.ow.rowbytes; ++x)
            if (f.output[(size_t)y * f.ow.rowbytes + x] != 0xa5) return 20 + depth;
    const auto first = f.output;
    std::fill(f.output.begin(), f.output.end(), 0xa5);
    if (Smart(f) || f.output != first) return 30 + depth;
    return 0;
}}

int main() {{
    for (int depth : {{8,16,32}})
        for (int variant = 0; variant < 4; ++variant)
            for (int count : {{1,3,5}})
                if (int e = gamma_case(depth, count, variant)) return e;
    // Exported AEX accepts count zero: the empty list matches no candidates,
    // so adaptive gamma stays off. The fixed five-slot storage bound remains.
    if (gamma_case(8, 0, 0) != 0) return 90;
    if (gamma_case(8, 6, 0) == 0) return 91;
    return 0;
}}
'''
        with tempfile.TemporaryDirectory(prefix="smoother2-gamma-colors-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(program, encoding="utf-8")
            subprocess.run(
                [compiler, "-std=c++17", "-O1", "-g", "-fno-omit-frame-pointer",
                 "-fsanitize=address,undefined",
                 "-I", str(ROOT / "cli/OLMSmoother2/shim"),
                 "-I", str(ROOT / "mac/OLMSmoother2"), str(source), "-o", str(binary)],
                check=True,
            )
            env = dict(__import__("os").environ)
            env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
            env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            subprocess.run([str(binary)], check=True, env=env)

    def test_palette_membership_count_order_and_duplicates_affect_production(self) -> None:
        compiler = shutil.which("clang++")
        if not compiler:
            self.skipTest("clang++ unavailable")
        program = f'''\
#define main retained_guard_main
#include "{HARNESS}"
#undef main

struct RGBA8 {{ unsigned char a, r, g, b; }};
struct GammaRun {{
    int err;
    bool input_immutable;
    bool padding_preserved;
    std::vector<unsigned char> output;
}};

static void put_pixel(Fixture &f, int depth, int x, int y, RGBA8 c) {{
    unsigned char *dst = f.input.data() + (size_t)y * f.iw.rowbytes +
                         (size_t)x * (depth == 8 ? 4 : depth == 16 ? 8 : 16);
    if (depth == 8) {{
        const PF_Pixel8 p = {{c.a, c.r, c.g, c.b}};
        std::memcpy(dst, &p, sizeof(p));
    }} else if (depth == 16) {{
        const PF_Pixel16 p = {{Widen(c.a), Widen(c.r), Widen(c.g), Widen(c.b)}};
        std::memcpy(dst, &p, sizeof(p));
    }} else {{
        const PF_PixelFloat p = {{c.a / 255.f, c.r / 255.f, c.g / 255.f, c.b / 255.f}};
        std::memcpy(dst, &p, sizeof(p));
    }}
}}

static GammaRun render_palette(int depth, int version, int count,
                               const RGBA8 palette[5]) {{
    const int w = 19, h = 17;
    const int ps = depth == 8 ? 4 : depth == 16 ? 8 : 16;
    Fixture f(depth, w, h, 9);
    std::memset(f.defs, 0, sizeof(f.defs));
    f.defs[SM_INPUT].u.ld = f.iw;
    f.defs[SM_KEY_COLOR].u.cd.value = {{255,17,31,47}};
    f.defs[SM_SMOOTHNESS].u.sd.value = 63;
    f.defs[SM_EXTRA_SMOOTH].u.sd.value = 29;
    f.defs[SM_SMOOTH_RANGE].u.sd.value = 41;
    f.defs[SM_VERSION].u.pd.value = version;
    f.defs[SM_GAMMA_MODE].u.pd.value = GAMMA_COLORS_ONLY;
    f.defs[SM_GAMMA_VALUE].u.fs_d.value = 1.8;
    f.defs[SM_NUM_GAMMA_COLORS].u.sd.value = count;
    for (int i = 0; i < 5; ++i)
        f.defs[SM_GAMMA_COLOR_0+i].u.cd.value =
            {{palette[i].a, palette[i].r, palette[i].g, palette[i].b}};

    const RGBA8 source_colors[4] = {{
        {{255,64,96,160}}, {{255,160,80,48}},
        {{255,32,192,112}}, {{255,91,137,203}}
    }};
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x)
            put_pixel(f, depth, x, y, source_colors[((x / 2) + (y / 3)) & 3]);

    const auto original = f.input;
    f.ow.rowbytes = w * ps + 15;
    f.output.assign((size_t)f.ow.rowbytes * h, 0xa5);
    f.ow.data = f.output.data();
    const int err = Smart(f);
    bool padding = true;
    for (int y = 0; y < h; ++y)
        for (int x = w * ps; x < f.ow.rowbytes; ++x)
            padding = padding && f.output[(size_t)y * f.ow.rowbytes + x] == 0xa5;
    return {{err, f.input == original, padding, f.output}};
}}

static bool successful(const GammaRun &run) {{
    return run.err == 0 && run.input_immutable && run.padding_preserved;
}}

int main() {{
    const RGBA8 a = {{255,64,96,160}};
    const RGBA8 b = {{255,160,80,48}};
    const RGBA8 c = {{255,32,192,112}};
    const RGBA8 absent = {{255,17,231,73}};
    const RGBA8 base[5] = {{a,b,c,absent,absent}};
    const RGBA8 reordered[5] = {{c,a,b,absent,absent}};
    const RGBA8 duplicated[5] = {{a,b,c,a,b}};
    const RGBA8 one_a_tail_1[5] = {{a,b,c,absent,absent}};
    const RGBA8 one_a_tail_2[5] = {{a,absent,absent,b,c}};
    const RGBA8 one_absent[5] = {{absent,a,b,c,a}};
    const RGBA8 alpha_changed[5] = {{
        {{0,a.r,a.g,a.b}}, {{127,b.r,b.g,b.b}}, {{1,c.r,c.g,c.b}}, absent, absent
    }};

    for (int depth : {{8,16,32}}) for (int version : {{SMOOTHER_V1,SMOOTHER_V2}}) {{
        const GammaRun normal = render_palette(depth, version, 3, base);
        const GammaRun order = render_palette(depth, version, 3, reordered);
        const GammaRun duplicate = render_palette(depth, version, 5, duplicated);
        const GammaRun count_one = render_palette(depth, version, 1, one_a_tail_1);
        const GammaRun inactive_tail = render_palette(depth, version, 1, one_a_tail_2);
        const GammaRun excluded = render_palette(depth, version, 1, one_absent);
        const GammaRun alpha = render_palette(depth, version, 3, alpha_changed);
        if (!successful(normal) || !successful(order) || !successful(duplicate) ||
            !successful(count_one) || !successful(inactive_tail) ||
            !successful(excluded) || !successful(alpha)) return 10 + depth + version;
        // The palette is a membership list: order, duplicates, inactive tail,
        // and alpha do not change RGB matching semantics.
        if (normal.output != order.output || normal.output != duplicate.output ||
            count_one.output != inactive_tail.output || normal.output != alpha.output)
            return 20 + depth + version;
        // Active count and actual membership must be observable. These relations
        // make the test fail if Gamma Colors silently becomes an admission-only lane.
        if (normal.output == count_one.output || count_one.output == excluded.output)
            return 30 + depth + version;
    }}
    return 0;
}}
'''
        with tempfile.TemporaryDirectory(prefix="smoother2-gamma-semantics-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(program, encoding="utf-8")
            subprocess.run(
                [compiler, "-std=c++17", "-O1", "-g", "-fno-omit-frame-pointer",
                 "-fsanitize=address,undefined",
                 "-I", str(ROOT / "cli/OLMSmoother2/shim"),
                 "-I", str(ROOT / "mac/OLMSmoother2"), str(source), "-o", str(binary)],
                check=True,
            )
            env = dict(__import__("os").environ)
            env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
            env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            subprocess.run([str(binary)], check=True, env=env)


if __name__ == "__main__":
    unittest.main()
