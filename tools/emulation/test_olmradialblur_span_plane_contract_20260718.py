#!/usr/bin/env python3
"""Exact case0009 +0x40 span-plane contract against retained AEX evidence."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
EVIDENCE = ROOT / "refs/conformance/olmradialblur_postworker_planes_20260718.json"

WIDTH = 1920
HEIGHT = 1080
POLAR_WIDTH = 1104
POLAR_HEIGHT = 1800
CELLS = POLAR_WIDTH * POLAR_HEIGHT
PLANE_BYTES = CELLS * 4
EXPECTED_SHA256 = "2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f"
EXPECTED_CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_retained_evidence() -> None:
    """Bind the oracle hash to the checked-in checkpoint extraction record.

    The multi-gigabyte runtime checkpoint was deliberately temporary.  The
    retained record pins its SHA, AEX/input identities, extraction geometry,
    checkpoint RIP, and the exact +0x40 plane SHA without pretending that the
    checkpoint payload itself is checked in.
    """
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    identities = evidence.get("identities", {})
    plane = evidence.get("planes", {}).get("source_scalar_plus_0x40", {})
    if evidence.get("status") != "pass_bounded_internal_evidence":
        raise AssertionError("retained span-plane evidence is not passing")
    if identities.get("checkpoint", {}).get("sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise AssertionError("retained checkpoint identity mismatch")
    if identities.get("aex", {}).get("sha256") != EXPECTED_AEX_SHA256:
        raise AssertionError("retained AEX identity mismatch")
    if identities.get("input", {}).get("sha256") != EXPECTED_INPUT_SHA256:
        raise AssertionError("retained case0009 input identity mismatch")
    if evidence.get("checkpoint", {}).get("rip") != "0x180005c9f":
        raise AssertionError("retained checkpoint RIP mismatch")
    if evidence.get("geometry") != {"cells": CELLS, "height": POLAR_HEIGHT, "width": POLAR_WIDTH}:
        raise AssertionError("retained span-plane geometry mismatch")
    if plane.get("bytes") != PLANE_BYTES or plane.get("sha256") != EXPECTED_SHA256:
        raise AssertionError("retained +0x40 span-plane identity mismatch")


def write_probe(path: Path) -> None:
    production = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    path.write_text(
        f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{production}"
#include <cstdint>
#include <fstream>
#include <vector>

static float f32(float value) {{ volatile float rounded = value; return rounded; }}
static float sample_scalar_a6a0(const std::vector<float>& source, int w, int h, float x, float y) {{
  const A_long xi = (A_long)x;
  const A_long yi = (A_long)y;
  const float fx = f32(x - (float)xi);
  const float fy = f32(y - (float)yi);
  const A_long x0 = std::max<A_long>(0, std::min<A_long>(xi, w - 1));
  const A_long x1 = std::max<A_long>(0, std::min<A_long>(xi + 1, w - 1));
  const A_long y0 = std::max<A_long>(0, std::min<A_long>(yi, h - 1));
  const A_long y1 = std::max<A_long>(0, std::min<A_long>(yi + 1, h - 1));
  const float w00 = f32(f32(1.0f - fx) * f32(1.0f - fy));
  const float w10 = f32(f32(1.0f - fy) * fx);
  const float w01 = f32(f32(1.0f - fx) * fy);
  const float w11 = f32(fy * fx);
  auto at = [&](A_long px, A_long py) {{ return source[(size_t)py * w + px]; }};
  // FUN_18000a6a0 uses [base + clamped_x1*4 + 4] for both right taps.
  // The retained allocation guard makes the final-row/right-edge read zero.
  auto right_at = [&](A_long py) {{ return source[(size_t)py * w + x1 + 1]; }};
  float out = f32(w00 * at(x0, y0));
  out = f32(out + f32(w10 * right_at(y0)));
  out = f32(out + f32(w01 * at(x0, y1)));
  return f32(out + f32(w11 * right_at(y1)));
}}

int main(int argc, char** argv) {{
  if (argc != 3) return 2;
  std::ifstream input(argv[1], std::ios::binary);
  std::vector<float> source((size_t){WIDTH} * {HEIGHT});
  input.read(reinterpret_cast<char*>(source.data()), source.size() * sizeof(float));
  if (!input || input.gcount() != (std::streamsize)(source.size() * sizeof(float))) return 3;
  source.push_back(0.0f);
  std::ofstream output(argv[2], std::ios::binary);
  const float step = f32((float)(3.141592653589793238462643383279502884 / 180.0 / 5.0));
  for (int ai = 0; ai < {POLAR_HEIGHT}; ++ai) {{
    const float theta = RadialF32Mul((float)ai, step);
    const RadialPairedTrig trig = RadialAEXPairedSinCos(theta);
    for (int ri = 0; ri < {POLAR_WIDTH}; ++ri) {{
      const float r = (float)ri;
      const float sx0 = RadialF32Mul(r, trig.cosine);
      const float sy0 = RadialF32Mul(RadialF32Mul(r, trig.sine), 1.0f);
      const float sx = RadialF32Add(RadialF32Sub(sx0, 0.0f), 960.0f);
      const float sy = RadialF32Add(
        RadialF32Add(RadialF32Mul(0.0f, sx0), RadialF32Mul(1.0f, sy0)), 540.0f);
      const float value = sample_scalar_a6a0(source, {WIDTH}, {HEIGHT}, sx, sy);
      output.write(reinterpret_cast<const char*>(&value), sizeof(value));
    }}
  }}
  return output.good() ? 0 : 4;
}}
''', encoding="ascii")


def main() -> int:
    if not SOURCE.is_file() or not INPUT.is_file() or not EVIDENCE.is_file():
        raise AssertionError("required source, case0009 input, or retained evidence is missing")
    validate_retained_evidence()
    if sha256_bytes(INPUT.read_bytes()) != EXPECTED_INPUT_SHA256:
        raise AssertionError("checked-in case0009 input identity mismatch")
    image = Image.open(INPUT).convert("RGBA")
    if image.size != (WIDTH, HEIGHT):
        raise AssertionError(f"unexpected case0009 input size: {image.size}")
    rgba_bytes = image.tobytes()
    alpha = rgba_bytes[3::4]
    source = b"".join(struct.pack("<f", value / 255.0) for value in alpha)
    source_factor = struct.pack("<f", 1.0) * CELLS
    if any(source_factor[index : index + 4] != struct.pack("<f", 1.0) for index in range(0, len(source_factor), 4)):
        raise AssertionError("case0009 SV=NV=0 source factor plane is not constant 1.0")
    with tempfile.TemporaryDirectory(prefix="olmradialblur_span_plane_20260718_") as tmp:
        tmp_path = Path(tmp)
        source_path = tmp_path / "source_scalar.f32"
        output_path = tmp_path / "span_plane.f32"
        probe_path = tmp_path / "span_plane_probe.cpp"
        binary_path = tmp_path / "span_plane_probe"
        source_path.write_bytes(source)
        write_probe(probe_path)
        build = subprocess.run(
            ["clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
             "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
             "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
             "-I", str(ROOT / "cli/OLMSmoother/shim"),
             "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
             "-ffunction-sections", "-fdata-sections", str(probe_path),
             "-Wl,-dead_strip", "-Wl,-undefined,dynamic_lookup", "-o", str(binary_path)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if build.returncode:
            raise AssertionError(build.stdout + build.stderr)
        run = subprocess.run([str(binary_path), str(source_path), str(output_path)], cwd=ROOT, text=True, capture_output=True)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)
        actual = output_path.read_bytes()
    print(f"compared_float_words={CELLS}")
    print(f"compared_bytes={len(actual)}")
    print(f"actual_sha256={sha256_bytes(actual)}")
    print(f"retained_checkpoint_span_sha256={EXPECTED_SHA256}")
    print("source_factor_plane=constant_1.0")
    if len(actual) != PLANE_BYTES or sha256_bytes(actual) != EXPECTED_SHA256:
        return 1
    print("PASS_OLMRADIALBLUR_SPAN_PLANE_CONTRACT_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
