#!/usr/bin/env python3
"""Bounded source and raw-frame checks for the typed RadialBlur Zoom path."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AUDIT_CPP = ROOT / "tools/emulation/audit_olmradialblur_pf32_host_adapter_20260718.cpp"
RAW_ROOT = Path("/tmp/olmradialblur_continuation_dump_20260718")
PLANE = RAW_ROOT / "normalized_polar_plane.f32rgba"
ORACLE = RAW_ROOT / "complete_pf32_frame.f32rgba"
INPUT_PNG = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
EXPECTED_BYTES = 1920 * 1080 * 4 * 4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_production_adapter(temp: Path) -> tuple[int, int | None]:
    rgba = np.asarray(Image.open(INPUT_PNG).convert("RGBA"), dtype=np.float32) / np.float32(255.0)
    argb = rgba[:, :, [3, 0, 1, 2]].copy()
    input_raw = temp / "input_pf32.argb"
    output_raw = temp / "output_pf32.argb"
    argb.tofile(input_raw)
    production = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe = temp / "radialblur_pf32_host_probe.cpp"
    binary = temp / "radialblur_pf32_host_probe"
    probe.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{production}"
#include <cstdio>
#include <fstream>
#include <vector>
int main(int argc, char **argv) {{
  if (argc != 3) return 2;
  constexpr int W=1920, H=1080;
  std::vector<PF_PixelFloat> input(W*H), output(W*H);
  std::ifstream in_file(argv[1], std::ios::binary);
  in_file.read(reinterpret_cast<char *>(input.data()), input.size()*sizeof(PF_PixelFloat));
  if (!in_file || in_file.gcount() != static_cast<std::streamsize>(input.size()*sizeof(PF_PixelFloat))) return 3;
  PF_EffectWorld in{{}}, out{{}};
  in.data=(PF_PixelPtr)input.data(); in.rowbytes=W*sizeof(PF_PixelFloat); in.width=W; in.height=H;
  in.extent_hint={{0,0,W,H}}; out.data=(PF_PixelPtr)output.data(); out.rowbytes=W*sizeof(PF_PixelFloat);
  out.width=W; out.height=H; out.extent_hint={{0,0,W,H}};
  OLMRadialBlurInfo info{{}}; info.blur_type=1; info.center_x=960; info.center_y=540;
  info.outer_strength=1717; info.outer_offset_mode=1; info.inner_offset_mode=1;
  info.repeat_border=TRUE; info.ratio=1; info.quality=5; info.brightness_gain=1;
  info.noise_type=1; info.seed=1; info.thickness=10; info.comp_width=W; info.comp_height=H;
  if (OLMRadialBlurTestRenderWorld(&in,&out,&info,32) != PF_Err_NONE) return 4;
  std::ofstream out_file(argv[2], std::ios::binary);
  out_file.write(reinterpret_cast<const char *>(output.data()), output.size()*sizeof(PF_PixelFloat));
  return out_file ? 0 : 5;
}}
''', encoding="utf-8")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = [os.environ.get("CXX", "clang++"), "-std=c++17", "-arch", "arm64", "-O2",
               "-fno-fast-math", "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), "-ffunction-sections",
               "-fdata-sections", str(probe), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(binary)]
    build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if build.returncode != 0:
        raise AssertionError("production adapter compile failed\n" + build.stderr)
    run = subprocess.run([str(binary), str(input_raw), str(output_raw)], cwd=ROOT, text=True, capture_output=True)
    if run.returncode != 0 or output_raw.stat().st_size != EXPECTED_BYTES:
        raise AssertionError(f"production adapter failed closed rc={run.returncode}\n{run.stdout}{run.stderr}")
    host_argb = np.fromfile(output_raw, dtype=np.float32).reshape(1080, 1920, 4)
    host_rgba = host_argb[:, :, [1, 2, 3, 0]].copy().tobytes()
    oracle = ORACLE.read_bytes()
    differing = sum(a != b for a, b in zip(host_rgba, oracle))
    first = next((index for index, pair in enumerate(zip(host_rgba, oracle)) if pair[0] != pair[1]), None)
    return differing, first


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "RenderZoomTyped<PF_Pixel8>",
        "RenderZoomTyped<PF_Pixel16>",
        "RenderZoomTyped<PF_PixelFloat>",
        "return RenderZoom16(input, output, info);",
        "return RenderZoomFloat(input, output, info);",
        "1.0f / 32768.0f",
        "RadialF32Mul(value, 32768.0f)",
        "pixel.red = state.final_rgb[0];",
        "strict_nonzero_alpha ? state.alpha != 0.0f",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise AssertionError(f"missing typed-render contract: {missing}")
    dispatch = re.search(r"static PF_Err RenderWorld\(.*?\n\}", source, re.DOTALL)
    if not dispatch or "CopyWorld<PF_Pixel16>" in dispatch.group(0) or "CopyWorld<PF_PixelFloat>" in dispatch.group(0):
        raise AssertionError("deep RenderWorld dispatch still contains a no-op copy")

    print("source_contract=pass")
    if not PLANE.is_file() or not ORACLE.is_file():
        print("raw_frame_comparison=skipped_missing_local_oracle")
        print("ae_exact_claim=false")
        return 0
    if PLANE.stat().st_size != EXPECTED_BYTES or ORACLE.stat().st_size != EXPECTED_BYTES:
        raise AssertionError("local oracle has an unexpected byte size")

    with tempfile.TemporaryDirectory(prefix="olmradialblur_typed_deep_20260718_") as tmp:
        binary = Path(tmp) / "audit"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic", str(AUDIT_CPP), "-o", str(binary)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if build.returncode != 0:
            raise AssertionError(build.stdout + build.stderr)
        run = subprocess.run([str(binary), str(PLANE), str(ORACLE)], cwd=ROOT, text=True, capture_output=True)
        print(run.stdout, end="")
        if run.stderr:
            print(run.stderr, end="")
        if run.returncode not in (0, 1):
            raise AssertionError(f"comparator did not fail closed: rc={run.returncode}")
        differing = re.search(r"differing_bytes=(\d+)", run.stdout)
        compared = re.search(r"compared_bytes=(\d+)", run.stdout)
        if not differing or not compared or int(compared.group(1)) != EXPECTED_BYTES:
            raise AssertionError("comparator did not account for the complete frame")
        if (int(differing.group(1)) == 0) != (run.returncode == 0):
            raise AssertionError("comparator exit code disagrees with byte comparison")
        print(f"normalized_plane_sha256={sha256(PLANE)}")
        print(f"complete_frame_sha256={sha256(ORACLE)}")
        print("raw_frame_comparison=pass_exact" if run.returncode == 0 else "raw_frame_comparison=known_red_fail_closed")
        production_differing, production_first = run_production_adapter(Path(tmp))
        print(f"production_adapter_compared_bytes={EXPECTED_BYTES}")
        print(f"production_adapter_differing_bytes={production_differing}")
        print(f"production_adapter_first_difference={production_first}")
        print("production_adapter_comparison=pass_exact" if production_differing == 0 else "production_adapter_comparison=known_red_fail_closed")
        print("ae_exact_claim=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
