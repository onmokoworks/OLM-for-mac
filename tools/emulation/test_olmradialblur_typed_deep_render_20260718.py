#!/usr/bin/env python3
"""Bounded source and raw-frame checks for the typed RadialBlur Zoom path."""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AUDIT_CPP = ROOT / "tools/emulation/audit_olmradialblur_pf32_host_adapter_20260718.cpp"
RAW_ROOT = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected")
PLANE = RAW_ROOT / "normalized_polar_plane.f32rgba"
ORACLE = RAW_ROOT / "complete_pf32_frame.f32rgba"
INPUT_PNG = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
EXPECTED_BYTES = 1920 * 1080 * 4 * 4
POLAR_BYTES = 1104 * 1800 * 4 * 4
POLAR_FLOATS = POLAR_BYTES // 4
POLAR_WIDTH = 1104
POLAR_HEIGHT = 1800
EXPECTED_POLAR_SHA256 = "c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_bytes(actual: bytes, oracle: bytes) -> tuple[int, int | None]:
    if len(actual) != len(oracle):
        raise AssertionError(f"byte comparison size mismatch: {len(actual)} != {len(oracle)}")
    differing = sum(a != b for a, b in zip(actual, oracle))
    first = next((index for index, pair in enumerate(zip(actual, oracle)) if pair[0] != pair[1]), None)
    return differing, first


def polar_first_difference(actual: bytes, oracle: bytes, first_byte: int | None) -> dict[str, object] | None:
    if first_byte is None:
        return None
    word_index = first_byte // 4
    cell_index, channel = divmod(word_index, 4)
    angle_index, radius_index = divmod(cell_index, POLAR_WIDTH)
    word_offset = word_index * 4
    actual_bits = struct.unpack_from("<I", actual, word_offset)[0]
    oracle_bits = struct.unpack_from("<I", oracle, word_offset)[0]
    actual_value = struct.unpack_from("<f", actual, word_offset)[0]
    oracle_value = struct.unpack_from("<f", oracle, word_offset)[0]
    return {
        "byte_offset": first_byte,
        "float_word_index": word_index,
        "angle_index": angle_index,
        "radius_index": radius_index,
        "channel": "RGBA"[channel],
        "actual_value": actual_value,
        "oracle_value": oracle_value,
        "actual_bits": f"0x{actual_bits:08x}",
        "oracle_bits": f"0x{oracle_bits:08x}",
    }


def run_production_adapter(temp: Path) -> dict[str, object]:
    rgba = np.asarray(Image.open(INPUT_PNG).convert("RGBA"), dtype=np.float32) / np.float32(255.0)
    argb = rgba[:, :, [3, 0, 1, 2]].copy()
    input_raw = temp / "input_pf32.argb"
    output_raw = temp / "output_pf32.argb"
    polar_raw = temp / "production_normalized_polar.f32rgba"
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
  if (argc != 4) return 2;
  constexpr int W=1920, H=1080;
  std::vector<PF_PixelFloat> input(W*H), output(W*H);
  std::vector<float> polar({POLAR_FLOATS});
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
  size_t written_floats=0; A_long polar_width=0, polar_height=0;
  if (OLMRadialBlurTestRenderFloatAndCaptureNormalizedPolar(
        &in,&out,&info,polar.data(),polar.size(),&written_floats,&polar_width,&polar_height) != PF_Err_NONE) return 4;
  if (written_floats != polar.size() || polar_width != {POLAR_WIDTH} || polar_height != {POLAR_HEIGHT}) return 5;
  std::ofstream out_file(argv[2], std::ios::binary);
  out_file.write(reinterpret_cast<const char *>(output.data()), output.size()*sizeof(PF_PixelFloat));
  std::ofstream polar_file(argv[3], std::ios::binary);
  polar_file.write(reinterpret_cast<const char *>(polar.data()), polar.size()*sizeof(float));
  return out_file && polar_file ? 0 : 6;
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
    run = subprocess.run(
        [str(binary), str(input_raw), str(output_raw), str(polar_raw)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if (run.returncode != 0 or output_raw.stat().st_size != EXPECTED_BYTES or
            polar_raw.stat().st_size != POLAR_BYTES):
        raise AssertionError(f"production adapter failed closed rc={run.returncode}\n{run.stdout}{run.stderr}")
    host_argb = np.fromfile(output_raw, dtype=np.float32).reshape(1080, 1920, 4)
    host_rgba = host_argb[:, :, [1, 2, 3, 0]].copy().tobytes()
    frame_differing, frame_first = compare_bytes(host_rgba, ORACLE.read_bytes())
    production_polar = polar_raw.read_bytes()
    oracle_polar = PLANE.read_bytes()
    polar_differing, polar_first = compare_bytes(production_polar, oracle_polar)
    return {
        "frame_differing_bytes": frame_differing,
        "frame_first_difference": frame_first,
        "polar_differing_bytes": polar_differing,
        "polar_first_difference": polar_first_difference(production_polar, oracle_polar, polar_first),
        "production_polar_sha256": sha256(polar_raw),
    }


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
        "OLMRadialBlurTestRenderFloatAndCaptureNormalizedPolar",
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
    if PLANE.stat().st_size != POLAR_BYTES or ORACLE.stat().st_size != EXPECTED_BYTES:
        raise AssertionError("local oracle has an unexpected byte size")
    if sha256(PLANE) != EXPECTED_POLAR_SHA256:
        raise AssertionError("corrected normalized polar oracle hash mismatch")

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
        production = run_production_adapter(Path(tmp))
        print(f"production_polar_compared_bytes={POLAR_BYTES}")
        print(f"production_polar_differing_bytes={production['polar_differing_bytes']}")
        print("production_polar_first_difference=" + json.dumps(
            production["polar_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"production_polar_sha256={production['production_polar_sha256']}")
        print("production_polar_comparison=pass_exact" if production["polar_differing_bytes"] == 0
              else "production_polar_comparison=known_red_fail_closed")
        print(f"production_adapter_compared_bytes={EXPECTED_BYTES}")
        print(f"production_adapter_differing_bytes={production['frame_differing_bytes']}")
        print(f"production_adapter_first_difference={production['frame_first_difference']}")
        print("production_adapter_comparison=pass_exact" if production["frame_differing_bytes"] == 0
              else "production_adapter_comparison=known_red_fail_closed")
        print("ae_exact_claim=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
