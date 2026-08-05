#!/usr/bin/env python3
"""Capture production case0009 helper planes and compare their AEX identities."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
REPORT = ROOT / "refs/conformance/olmradialblur_production_outer_inputs_20260805.json"
WIDTH, HEIGHT = 1920, 1080
POLAR_WIDTH, POLAR_HEIGHT = 1104, 1800
CELLS = POLAR_WIDTH * POLAR_HEIGHT
FLOATS = CELLS * 4
EXPECTED_FRAME = "7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010"

EXPECTED = {
    "eligibility": "861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7",
    "span": "2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f",
    "source_scalar": "13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce",
    "preblur": "fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef",
    "normalized": "c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def float_bits_counts(path: Path) -> dict[str, int]:
    return {f"0x{bits:08x}": count for bits, count in sorted(Counter(
        struct.unpack(f"<{CELLS}I", path.read_bytes())).items())}


def main() -> int:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradialblur_outer_inputs_") as raw_tmp:
        temp = Path(raw_tmp)
        input_path = temp / "input.argb32"
        # The retained PF32 AEX fixture was created with a rounded float32
        # reciprocal multiply; direct float32 division differs for some bytes.
        rgba = (np.asarray(Image.open(INPUT).convert("RGBA"), dtype=np.float32) *
                np.float32(1.0 / 255.0))
        rgba[:, :, [3, 0, 1, 2]].copy().tofile(input_path)
        probe = temp / "probe.cpp"
        binary = temp / "probe"
        probe.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc, char **argv) {{
  if (argc != 8) return 2;
  constexpr int W={WIDTH}, H={HEIGHT}, CELLS={CELLS}, FLOATS={FLOATS};
  std::vector<PF_PixelFloat> input(W*H), output(W*H);
  std::vector<float> pre(FLOATS), post(FLOATS), span(CELLS), scalar(CELLS);
  std::vector<A_u_char> eligibility(CELLS);
  std::ifstream in(argv[1], std::ios::binary);
  in.read(reinterpret_cast<char *>(input.data()), input.size()*sizeof(PF_PixelFloat));
  if (!in || in.gcount() != static_cast<std::streamsize>(input.size()*sizeof(PF_PixelFloat))) return 3;
  PF_EffectWorld iw{{}}, ow{{}};
  iw.data=(PF_PixelPtr)input.data(); iw.rowbytes=W*sizeof(PF_PixelFloat); iw.width=W; iw.height=H;
  iw.extent_hint={{0,0,W,H}}; ow.data=(PF_PixelPtr)output.data(); ow.rowbytes=W*sizeof(PF_PixelFloat);
  ow.width=W; ow.height=H; ow.extent_hint={{0,0,W,H}};
  OLMRadialBlurInfo info{{}}; info.blur_type=1; info.center_x=960; info.center_y=540;
  info.outer_strength=1717; info.outer_offset_mode=1; info.inner_offset_mode=1;
  info.repeat_border=TRUE; info.ratio=1; info.quality=5; info.brightness_gain=1;
  info.noise_type=1; info.seed=1; info.thickness=10; info.comp_width=W; info.comp_height=H;
  size_t wf=0, wc=0; A_long pw=0, ph=0;
  const PF_Err err=OLMRadialBlurTestRenderFloatAndCaptureOuterOnlyInputs(
    &iw,&ow,&info,pre.data(),post.data(),eligibility.data(),span.data(),scalar.data(),
    pre.size(),eligibility.size(),&wf,&wc,&pw,&ph);
  if (err != PF_Err_NONE || wf != FLOATS || wc != CELLS || pw != {POLAR_WIDTH} || ph != {POLAR_HEIGHT}) return 4;
  std::ofstream(argv[2],std::ios::binary).write(reinterpret_cast<char *>(eligibility.data()),eligibility.size());
  std::ofstream(argv[3],std::ios::binary).write(reinterpret_cast<char *>(span.data()),span.size()*sizeof(float));
  std::ofstream(argv[4],std::ios::binary).write(reinterpret_cast<char *>(scalar.data()),scalar.size()*sizeof(float));
  std::ofstream(argv[5],std::ios::binary).write(reinterpret_cast<char *>(pre.data()),pre.size()*sizeof(float));
  std::ofstream(argv[6],std::ios::binary).write(reinterpret_cast<char *>(post.data()),post.size()*sizeof(float));
  std::ofstream(argv[7],std::ios::binary).write(reinterpret_cast<char *>(output.data()),output.size()*sizeof(PF_PixelFloat));
  return 0;
}}
''', encoding="utf-8")
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        command = [os.environ.get("CXX", "clang++"), "-std=c++17", "-arch", "arm64", "-O2",
                   "-fno-fast-math", "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
                   "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                   "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                   "-ffunction-sections", "-fdata-sections", str(probe), "-Wl,-dead_strip",
                   "-framework", "Cocoa", "-o", str(binary)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise AssertionError(build.stderr)
        paths = {name: temp / f"{name}.bin" for name in EXPECTED}
        output_path = temp / "output.argb32"
        run = subprocess.run([str(binary), str(input_path), *(str(paths[n]) for n in EXPECTED), str(output_path)],
                             cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise AssertionError(f"probe failed rc={run.returncode}\n{run.stdout}{run.stderr}")
        actual = {name: sha256(path) for name, path in paths.items()}
        output_argb = np.fromfile(output_path, dtype=np.float32).reshape(HEIGHT, WIDTH, 4)
        frame_sha256 = hashlib.sha256(output_argb[:, :, [1, 2, 3, 0]].copy().tobytes()).hexdigest()
        report = {
            "kind": "olmradialblur_production_outer_inputs_20260805",
            "scope": "case0009 PF32 production entry-to-worker helper planes; no AE claim",
            "expected_actual_aex_sha256": EXPECTED,
            "production_sha256": actual,
            "matches": {name: actual[name] == EXPECTED[name] for name in EXPECTED},
            "final_frame_expected_sha256": EXPECTED_FRAME,
            "final_frame_production_sha256": frame_sha256,
            "final_frame_matches": frame_sha256 == EXPECTED_FRAME,
            "eligibility_counts": dict(sorted(Counter(paths["eligibility"].read_bytes()).items())),
            "span_counts_by_bits": float_bits_counts(paths["span"]),
            "source_scalar_counts_by_bits": float_bits_counts(paths["source_scalar"]),
        }
        report["status"] = "pass" if all(report["matches"].values()) and report["final_frame_matches"] else "diagnostic_mismatch"
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
