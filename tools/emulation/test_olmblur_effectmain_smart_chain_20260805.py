#!/usr/bin/env python3
"""AE-free production EffectMain SMART_PRE_RENDER -> SMART_RENDER proof."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_pf8_nonlegacy_source_aex_adapter_20260805 as adapter
from olm_installed_identity import verified_binary

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/fixtures/olmblur_worker_orchestration/8bpc_nonlegacy_basic"
INSTALLED, _IDENTITY = verified_binary("OLMBlur")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_source() -> str:
    source = adapter.pf8_probe_source()
    old_checkout = "static PF_Err checkout_param(PF_InData*, A_long, A_long, A_long, A_long, PF_ParamDef*) { return PF_Err_NONE; }"
    new_checkout = r'''static PF_ParamDef g_params[6];
static int g_param_checkouts = 0;
static PF_Err checkout_param(PF_InData*, A_long index, A_long, A_long, A_long, PF_ParamDef* out) {
  if (index < 0 || index >= 6 || !out) return -1;
  *out = g_params[index]; ++g_param_checkouts; return PF_Err_NONE;
}'''
    if old_checkout not in source:
        raise RuntimeError("base checkout stub changed")
    source = source.replace(old_checkout, new_checkout)
    main_start = source.index("int main(int argc, char **argv) {")
    source = source[:main_start] + r'''static PF_EffectWorld *g_input_world = nullptr, *g_output_world = nullptr;
static int g_pre_checkout = 0, g_pixel_checkout = 0, g_output_checkout = 0, g_checkin = 0;
static PF_Err pre_checkout(PF_ProgPtr, A_long, A_long, PF_RenderRequest*, A_long, A_long, A_long, PF_CheckoutResult *out) {
  ++g_pre_checkout; out->result_rect = {0, 0, g_input_world->width, g_input_world->height};
  out->max_result_rect = out->result_rect; out->ref_width = g_input_world->width; return PF_Err_NONE;
}
static PF_Err pixel_checkout(PF_ProgPtr, A_long, PF_EffectWorld **out) { ++g_pixel_checkout; *out = g_input_world; return PF_Err_NONE; }
static PF_Err output_checkout(PF_ProgPtr, PF_EffectWorld **out) { ++g_output_checkout; *out = g_output_world; return PF_Err_NONE; }
static PF_Err pixel_checkin(PF_ProgPtr, A_long) { ++g_checkin; return PF_Err_NONE; }

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const int width = 12, height = 12, rowbytes = width * 4 + 17;
  const std::size_t active = width * 4;
  const auto source = read_file(argv[1]); const auto expected = read_file(argv[2]);
  if (source.size() != active * height || expected.size() != active * height) return 3;
  std::vector<std::uint8_t> input(rowbytes * height, 0xA5), output(rowbytes * height, 0xEE);
  for (int y = 0; y < height; ++y) std::memcpy(input.data() + y * rowbytes, source.data() + y * active, active);
  PF_EffectWorld in{input.data(), rowbytes, width, height, 8, {0, 0, width, height}, 0};
  PF_EffectWorld out{output.data(), rowbytes, width, height, 8, {0, 0, width, height}, 0};
  g_input_world = &in; g_output_world = &out;
  g_params[1].u.fs_d.value = 3.0; g_params[2].u.fd.value = 100 * 65536;
  g_params[3].u.sd.value = 2; g_params[4].u.pd.value = 1; g_params[5].u.bd.value = 0;
  PF_InData in_data{}; in_data.effect_ref = reinterpret_cast<void*>(0x1234);
  in_data.current_time = 7; in_data.time_step = 1; in_data.time_scale = 24;
  in_data.downsample_x = {1, 1}; in_data.downsample_y = {1, 1};
  PF_OutData out_data{};
  PF_PreRenderInput pre_in{}; PF_PreRenderOutput pre_out{}; PF_PreRenderCallbacks pre_cb{&pre_checkout};
  PF_PreRenderExtra pre_extra{&pre_in, &pre_out, &pre_cb};
  const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data, &out_data, nullptr, nullptr, &pre_extra);
  PF_SmartRenderInput smart_in{8, pre_out.pre_render_data};
  PF_SmartRenderCallbacks smart_cb{&pixel_checkout, &output_checkout, &pixel_checkin};
  PF_SmartRenderExtra smart_extra{&smart_in, &smart_cb};
  const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data, nullptr, nullptr, &smart_extra);
  std::size_t mismatches = 0, alpha_mismatches = 0, padding_mismatches = 0;
  for (int y = 0; y < height; ++y) {
    const auto *actual = output.data() + y * rowbytes; const auto *want = expected.data() + y * active;
    for (std::size_t i = 0; i < active; ++i) mismatches += actual[i] != want[i];
    for (int i = 0; i < 17; ++i) padding_mismatches += actual[active + i] != 0xA5;
    for (int x = 0; x < width; ++x) alpha_mismatches += actual[x * 4] != source[y * active + x * 4];
  }
  const bool rect_ok = pre_out.result_rect.right == width && pre_out.result_rect.bottom == height &&
                       pre_out.max_result_rect.right == width && pre_out.max_result_rect.bottom == height;
  const bool callbacks_ok = g_pre_checkout == 1 && g_pixel_checkout == 1 && g_output_checkout == 1 &&
                            g_checkin == 1 && g_param_checkouts == 5;
  std::printf("{\"pre_err\":%d,\"smart_err\":%d,\"rect_ok\":%s,\"callbacks_ok\":%s,\"param_checkouts\":%d,\"mismatched_bytes\":%zu,\"alpha_mismatches\":%zu,\"padding_mismatches\":%zu}\n",
              (int)pre_err, (int)smart_err, rect_ok ? "true" : "false", callbacks_ok ? "true" : "false",
              g_param_checkouts, mismatches, alpha_mismatches, padding_mismatches);
  return (pre_err || smart_err || !rect_ok || !callbacks_ok || mismatches || alpha_mismatches || padding_mismatches) ? 4 : 0;
}
'''
    return source


def installed_identity() -> dict:
    checks = {
        "installed_binary_present": INSTALLED.is_file(),
        "installed_binary_hash": INSTALLED.is_file() and sha256(INSTALLED) == _IDENTITY["sha256"],
        "manifest_source_installed_exact": _IDENTITY["source_installed_exact"],
        "manifest_codesign_exact": _IDENTITY["codesign_exact"],
    }
    arch = subprocess.run(["lipo", "-archs", str(INSTALLED)], capture_output=True,
                          text=True, check=False) if INSTALLED.is_file() else None
    checks["installed_architectures"] = bool(arch and arch.returncode == 0 and
                                             set(arch.stdout.split()) == {"arm64", "x86_64"})
    if not all(checks.values()):
        raise RuntimeError(f"installed identity failed closed: {checks}")
    return checks


def main() -> int:
    checks = installed_identity()
    with tempfile.TemporaryDirectory(prefix="olmblur_effectmain_smart_") as name:
        directory = Path(name)
        source = directory / "probe.cpp"
        source.write_text(probe_source().replace(
            "__OLMBLUR_MAC_SOURCE__",
            str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace("\\", "\\\\").replace('"', '\\"')),
            encoding="utf-8")
        executable = directory / "probe"
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        compile_command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2",
                           "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1", "-fno-fast-math",
                           "-ffp-contract=off", "-isysroot", sdk, "-I", str(ROOT / "Headers"),
                           "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
                           "-I", str(ROOT / "Resources"), "-I", str(ROOT / "core"), str(source),
                           *[str(ROOT / item) for item in (
                               "core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp",
                               "core/olmblur_worker16_nonlegacy.cpp", "core/olmblur_worker16_legacy.cpp",
                               "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
                               "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp")],
                           "-framework", "Cocoa", "-o", str(executable)]
        subprocess.run(compile_command, cwd=ROOT, check=True)
        run = subprocess.run([str(executable), str(FIXTURE / "source_argb.bin"),
                              str(FIXTURE / "expected_argb.bin")], cwd=ROOT,
                             capture_output=True, text=True, check=False)
        if run.returncode:
            raise RuntimeError(f"smart chain failed: {run.stdout} {run.stderr}")
        result = json.loads(run.stdout)
    print(json.dumps({"schema": "olmblur.effectmain-smart-chain/1", "status": "pass",
                      "installed_identity_checks": checks, "result": result,
                      "scope": "AE-free Mac production EffectMain SMART_PRE_RENDER -> SMART_RENDER -> BlurRender PF8 NonLegacy; synthetic suites, no AE-host claim"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
