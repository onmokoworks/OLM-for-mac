#!/usr/bin/env python3
"""Connect retained actual-AEX Smoothness fixtures to production EffectMain.

This closes the Mac-local parameter-materialization seam: synthetic AE checkout
callbacks provide the declared UI value, production SmartRender checks out all
five parameters, converts the fixed-point Smoothness value, and dispatches the
typed Legacy renderer.  Expected buffers were produced by the pinned Windows
AEX workers; this test does not claim an actual-AEX public SmartRender call.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_32bpc_source_aex_adapter_20260717 as base

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
REPORT = ROOT / "refs/conformance/olmblur_nondefault_smoothness_effectmain_actual_aex_20260810.json"

CASES = (
    (8, "tools/emulation/fixtures/olmblur_worker8_legacy/manifest.json",
     "8bpc_legacy_smoothness43_75_byte_boundaries", "source_argb.bin", "expected_argb.bin", 17),
    (16, "tools/emulation/fixtures/olmblur_worker16_legacy/manifest.json",
     "16bpc_legacy_smoothness62_5_word_boundaries", "source_argb16.bin", "expected_argb16.bin", 23),
    (32, "tools/emulation/fixtures/olmblur_worker32_legacy/manifest.json",
     "32bpc_legacy_smoothness37_5_full24", "source_argb_f32.bin", "expected_argb_f32.bin", 32),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_source() -> str:
    source = base.probe_source()
    old = "static PF_Err checkout_param(PF_InData*, A_long, A_long, A_long, A_long, PF_ParamDef*) { return PF_Err_NONE; }"
    new = r'''static PF_ParamDef g_params[6];
static int g_checkout_count = 0, g_checkout_order[8] = {};
static double g_seen_amount = 0.0, g_seen_smoothness = 0.0; static A_long g_seen_smoothness_fixed = 0;
static PF_Err checkout_param(PF_InData*, A_long index, A_long, A_long, A_long, PF_ParamDef *out) {
  if (!out || index < 1 || index > 5 || g_checkout_count >= 8) return -1;
  g_checkout_order[g_checkout_count++] = index; *out = g_params[index];
  if (index == 1) g_seen_amount = out->u.fs_d.value;
  if (index == 2) { g_seen_smoothness_fixed = out->u.fd.value; g_seen_smoothness = static_cast<double>(out->u.fd.value) / 65536.0; }
  return PF_Err_NONE;
}'''
    if old not in source:
        raise RuntimeError("base checkout stub changed")
    source = source.replace(old, new)
    start = source.index("int main(int argc, char **argv) {")
    source = source[:start] + r'''static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static int g_pre = 0, g_pixels = 0, g_out = 0, g_checkin = 0;
static PF_Err pre_checkout(PF_ProgPtr, A_long, A_long, PF_RenderRequest*, A_long, A_long, A_long, PF_CheckoutResult *r) {
  ++g_pre; r->result_rect = {0, 0, g_input->width, g_input->height};
  r->max_result_rect = r->result_rect; r->ref_width = g_input->width; return 0;
}
static PF_Err pixel_checkout(PF_ProgPtr, A_long, PF_EffectWorld **w) { ++g_pixels; *w = g_input; return 0; }
static PF_Err output_checkout(PF_ProgPtr, PF_EffectWorld **w) { ++g_out; *w = g_output; return 0; }
static PF_Err pixel_checkin(PF_ProgPtr, A_long) { ++g_checkin; return 0; }

int main(int argc, char **argv) {
  if (argc != 11) return 2;
  const int depth = std::atoi(argv[1]), width = std::atoi(argv[2]), height = std::atoi(argv[3]);
  const double amount = std::strtod(argv[4], nullptr), smoothness = std::strtod(argv[5], nullptr);
  const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), padding = std::atoi(argv[8]);
  const auto source = read_file(argv[9]), expected = read_file(argv[10]);
  const int pixel_bytes = depth == 8 ? 4 : (depth == 16 ? 8 : 16);
  const std::size_t active = static_cast<std::size_t>(width) * pixel_bytes;
  const int rowbytes = static_cast<int>(active) + padding;
  if (source.size() != active * height || expected.size() != active * height) return 3;
  std::vector<std::uint8_t> input(rowbytes * height, 0xA5), output(rowbytes * height, 0xEE);
  for (int y = 0; y < height; ++y) std::memcpy(input.data() + y * rowbytes, source.data() + y * active, active);
  PF_EffectWorld in{input.data(), rowbytes, width, height, static_cast<A_short>(depth), {0,0,width,height}, 0};
  PF_EffectWorld out{output.data(), rowbytes, width, height, static_cast<A_short>(depth), {0,0,width,height}, 0};
  g_input = &in; g_output = &out;
  g_params[1].u.fs_d.value = amount;
  g_params[2].u.fd.value = static_cast<A_long>(smoothness * 65536.0);
  g_params[3].u.sd.value = repeat; g_params[4].u.pd.value = bias; g_params[5].u.bd.value = 1;
  PF_InData in_data{}; in_data.effect_ref = reinterpret_cast<void*>(0x1234);
  in_data.current_time = 7; in_data.time_step = 1; in_data.time_scale = 24;
  in_data.downsample_x = {1,1}; in_data.downsample_y = {1,1}; PF_OutData out_data{};
  PF_PreRenderInput pre_in{}; PF_PreRenderOutput pre_out{}; PF_PreRenderCallbacks pre_cb{&pre_checkout};
  PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
  const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data, &out_data, nullptr, nullptr, &pre_extra);
  PF_SmartRenderInput smart_in{static_cast<A_short>(depth), pre_out.pre_render_data};
  PF_SmartRenderCallbacks smart_cb{&pixel_checkout, &output_checkout, &pixel_checkin};
  PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
  const PF_Err render_err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data, nullptr, nullptr, &smart_extra);
  std::size_t mismatches = 0, padding_mismatches = 0;
  for (int y = 0; y < height; ++y) {
    const auto *actual = output.data() + y * rowbytes, *want = expected.data() + y * active;
    for (std::size_t i = 0; i < active; ++i) mismatches += actual[i] != want[i];
    for (int i = 0; i < padding; ++i) padding_mismatches += actual[active+i] != 0xA5;
  }
  const bool order_ok = g_checkout_count == 5 && g_checkout_order[0] == 1 && g_checkout_order[1] == 2 &&
                        g_checkout_order[2] == 3 && g_checkout_order[3] == 4 && g_checkout_order[4] == 5;
  const bool callbacks_ok = g_pre == 1 && g_pixels == 1 && g_out == 1 && g_checkin == 1;
  std::printf("{\"pre_err\":%d,\"render_err\":%d,\"checkout_count\":%d,\"checkout_order\":[%d,%d,%d,%d,%d],\"seen_amount\":%.17g,\"seen_smoothness_fixed\":%d,\"seen_smoothness\":%.17g,\"callbacks_ok\":%s,\"mismatched_bytes\":%zu,\"padding_mismatches\":%zu}\n",
    (int)pre_err,(int)render_err,g_checkout_count,g_checkout_order[0],g_checkout_order[1],g_checkout_order[2],g_checkout_order[3],g_checkout_order[4],g_seen_amount,(int)g_seen_smoothness_fixed,g_seen_smoothness,callbacks_ok?"true":"false",mismatches,padding_mismatches);
  return (pre_err || render_err || !order_ok || !callbacks_ok || mismatches || padding_mismatches || g_seen_smoothness != smoothness) ? 4 : 0;
}
'''
    return source


def compile_probe(directory: Path) -> Path:
    source = directory / "probe.cpp"
    source.write_text(probe_source().replace(
        "__OLMBLUR_MAC_SOURCE__", str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace("\\", "\\\\").replace('"', '\\"')),
        encoding="utf-8")
    executable = directory / "probe"
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2",
               "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1", "-fno-fast-math", "-ffp-contract=off",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), "-I", str(ROOT / "core"),
               str(source), *[str(ROOT / item) for item in (
                   "core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp",
                   "core/olmblur_worker16_nonlegacy.cpp", "core/olmblur_worker16_legacy.cpp",
                   "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
                   "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp")],
               "-framework", "Cocoa", "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    return executable


def main() -> int:
    if sha256(AEX) != AEX_SHA256:
        raise RuntimeError("actual AEX missing or hash drift")
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_smoothness_effectmain_") as name:
        executable = compile_probe(Path(name))
        for depth, manifest_rel, case_id, source_name, expected_name, padding in CASES:
            manifest_path = ROOT / manifest_rel
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert manifest["binary_sha256"] == AEX_SHA256 and manifest["bit_depth"] == depth
            case = next(row for row in manifest["cases"] if row["id"] == case_id)
            directory = manifest_path.parent / case_id
            assert sha256(directory / source_name) == case["source_sha256"]
            assert sha256(directory / expected_name) == case["expected_sha256"]
            run = subprocess.run([
                str(executable), str(depth), str(case["width"]), str(case["height"]),
                str(case["blur_amount"]), str(case["smoothness"]), str(case["repeat"]),
                str(case["bias_direction"]), str(padding), str(directory / source_name),
                str(directory / expected_name)], cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f"{case_id}: {run.stdout}\n{run.stderr}")
            observed = json.loads(run.stdout)
            assert observed["checkout_order"] == [1, 2, 3, 4, 5]
            assert observed["seen_smoothness"] == case["smoothness"]
            assert observed["seen_smoothness_fixed"] == int(case["smoothness"] * 65536)
            assert observed["mismatched_bytes"] == observed["padding_mismatches"] == 0
            results.append({
                "case": case_id, "bit_depth": depth, "smoothness": case["smoothness"],
                "actual_expected_sha256": case["expected_sha256"], "production": observed,
            })
    report = {
        "schema": "olmblur.nondefault-smoothness-effectmain/1", "status": "exact",
        "actual_aex_sha256": AEX_SHA256,
        "path": "synthetic AE parameter checkout -> Mac production EffectMain(SMART_PRE_RENDER/SMART_RENDER) -> typed Legacy renderer",
        "cases": results,
        "scope": "PF8/PF16/PF32 Legacy representative non-default Smoothness values; retained actual-AEX worker output versus public Mac production EffectMain",
        "not_proven": ["actual Windows AEX public SmartRender callback chain", "native AE parameter materialization/layout", "other Smoothness values or geometries"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMBLUR_NONDEFAULT_SMOOTHNESS_EFFECTMAIN depths=3 checkout=1,2,3,4,5 raw_exact=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
