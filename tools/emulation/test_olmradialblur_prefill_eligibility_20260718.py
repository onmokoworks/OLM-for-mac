#!/usr/bin/env python3
"""Compare local Zoom prefill eligibility against the pinned retained mask."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
CHECKPOINT = Path(
    "/private/tmp/olmradialblur_a9d0_boundary_nway_20260718/"
    "nway_merged_at_normalization_20260718.aexcp"
)
CHECKPOINT_MODULE = ROOT / "tools/emulation/run_olmradialblur_a9d0_boundary_fork_20260718.py"
FALLBACK_MASK = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/eligibility_mask.u8")
FALLBACK_PREBLUR = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/preblur_polar_plane.f32rgba")
NORMALIZED_ORACLE = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/normalized_polar_plane.f32rgba")
FINAL_FRAME_ORACLE = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/complete_pf32_frame.f32rgba")
INPUT_PNG = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"

EXPECTED_CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_RIP = 0x180005C9F
EXPECTED_ELIGIBILITY_SHA256 = "861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7"
EXPECTED_ELIGIBILITY_COUNTS = {0: 565113, 1: 1422087}
EXPECTED_PREBLUR_SHA256 = "fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef"
EXPECTED_NORMALIZED_SHA256 = "c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8"
EXPECTED_FINAL_FRAME_SHA256 = "7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010"

WIDTH = 1920
HEIGHT = 1080
POLAR_WIDTH = 1104
POLAR_HEIGHT = 1800
PF32_IMAGE_BYTES = WIDTH * HEIGHT * 4 * 4
POLAR_FLOATS = POLAR_WIDTH * POLAR_HEIGHT * 4
POLAR_BYTES = POLAR_FLOATS * 4
ELIGIBILITY_BYTES = POLAR_WIDTH * POLAR_HEIGHT


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_mask(raw: bytes) -> dict[int, int]:
    return {int(value): int(raw.count(value)) for value in sorted(set(raw))}


def first_difference(actual: bytes, expected: bytes) -> dict[str, object] | None:
    if len(actual) != len(expected):
        raise AssertionError(f"mask size mismatch: {len(actual)} != {len(expected)}")
    for index, (left, right) in enumerate(zip(actual, expected)):
        if left != right:
            angle_index, radius_index = divmod(index, POLAR_WIDTH)
            return {
                "byte_offset": index,
                "angle_index": angle_index,
                "radius_index": radius_index,
                "actual": left,
                "expected": right,
            }
    return None


def all_differences(actual: bytes, expected: bytes, limit: int) -> list[dict[str, object]] | None:
    if len(actual) != len(expected):
        raise AssertionError(f"mask size mismatch: {len(actual)} != {len(expected)}")
    diffs: list[dict[str, object]] = []
    for index, (left, right) in enumerate(zip(actual, expected)):
        if left != right:
            angle_index, radius_index = divmod(index, POLAR_WIDTH)
            diffs.append({
                "angle_index": angle_index,
                "radius_index": radius_index,
                "actual": left,
                "expected": right,
            })
            if len(diffs) > limit:
                return None
    return diffs


def ensure_identities() -> None:
    if not SOURCE.is_file():
        raise AssertionError(f"source file is missing: {SOURCE}")
    if not INPUT_PNG.is_file():
        raise AssertionError(f"input PNG is missing: {INPUT_PNG}")
    input_sha = sha256_file(INPUT_PNG)
    if input_sha != EXPECTED_INPUT_SHA256:
        raise AssertionError(f"input PNG identity mismatch: {input_sha}")


def load_expected_prefill_from_checkpoint() -> tuple[bytes, bytes, dict[str, object]]:
    if not CHECKPOINT.is_file():
        raise AssertionError(f"checkpoint is missing: {CHECKPOINT}")
    checkpoint_sha = sha256_file(CHECKPOINT)
    if checkpoint_sha != EXPECTED_CHECKPOINT_SHA256:
        raise AssertionError(f"checkpoint SHA256 mismatch: {checkpoint_sha}")
    spec = importlib.util.spec_from_file_location("olmradialblur_checkpoint_reader", CHECKPOINT_MODULE)
    if not spec or not spec.loader:
        raise AssertionError(f"cannot load checkpoint helper: {CHECKPOINT_MODULE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    checkpoint = module.Checkpoint.read(CHECKPOINT)
    aex_sha = checkpoint.header.get("aex", {}).get("sha256")
    if aex_sha != EXPECTED_AEX_SHA256:
        raise AssertionError(f"checkpoint embedded AEX SHA256 mismatch: {aex_sha}")
    rip = int(checkpoint.header["registers"]["gp"]["rip"])
    if rip != EXPECTED_RIP:
        raise AssertionError(f"checkpoint RIP mismatch: 0x{rip:x}")
    rbp = int(checkpoint.header["registers"]["gp"]["rbp"])

    def read_checkpoint(address: int, size: int) -> bytes:
        for region in checkpoint.header["regions"]:
            base = int(region["address"])
            region_size = int(region["size"])
            if base <= address and address + size <= base + region_size:
                raw = checkpoint.raw_region(region["name"])
                offset = address - base
                return bytes(raw[offset:offset + size])
        raise AssertionError(f"checkpoint range missing: 0x{address:x}+{size}")

    slot = rbp - 0x60
    pointer = struct.unpack("<Q", read_checkpoint(slot, 8))[0]
    mask = read_checkpoint(pointer, ELIGIBILITY_BYTES)
    digest = sha256_bytes(mask)
    if digest != EXPECTED_ELIGIBILITY_SHA256:
        raise AssertionError(f"checkpoint eligibility SHA256 mismatch: {digest}")
    counts = count_mask(mask)
    if counts != EXPECTED_ELIGIBILITY_COUNTS:
        raise AssertionError(f"checkpoint eligibility counts mismatch: {counts}")
    captured = checkpoint.header.get("metadata", {}).get("captured", {})
    work = int(captured.get("zoom_param1") or 0)
    if not work:
        raise AssertionError("checkpoint is missing the Zoom work pointer")
    preblur_pointer = struct.unpack("<Q", read_checkpoint(work + 0x38, 8))[0]
    preblur = read_checkpoint(preblur_pointer, POLAR_BYTES)
    preblur_sha = sha256_bytes(preblur)
    if preblur_sha != EXPECTED_PREBLUR_SHA256:
        raise AssertionError(f"checkpoint preblur SHA256 mismatch: {preblur_sha}")
    return mask, preblur, {
        "source": "checkpoint",
        "checkpoint_sha256": checkpoint_sha,
        "aex_sha256": aex_sha,
        "rbp": f"0x{rbp:x}",
        "eligibility_slot": f"0x{slot:x}",
        "eligibility_pointer": f"0x{pointer:x}",
        "eligibility_sha256": digest,
        "eligibility_counts": counts,
        "preblur_pointer": f"0x{preblur_pointer:x}",
        "preblur_sha256": preblur_sha,
    }


def load_expected_prefill() -> tuple[bytes, bytes, dict[str, object]]:
    try:
        return load_expected_prefill_from_checkpoint()
    except Exception as exc:
        if not FALLBACK_MASK.is_file() or not FALLBACK_PREBLUR.is_file():
            raise AssertionError(f"checkpoint extraction failed and fallback prefill is missing: {exc}") from exc
        raw = FALLBACK_MASK.read_bytes()
        if len(raw) != ELIGIBILITY_BYTES:
            raise AssertionError(
                f"checkpoint extraction failed and fallback size mismatched: {len(raw)}"
            ) from exc
        digest = sha256_bytes(raw)
        if digest != EXPECTED_ELIGIBILITY_SHA256:
            raise AssertionError(
                f"checkpoint extraction failed and fallback SHA256 mismatched: {digest}"
            ) from exc
        counts = count_mask(raw)
        if counts != EXPECTED_ELIGIBILITY_COUNTS:
            raise AssertionError(
                f"checkpoint extraction failed and fallback counts mismatched: {counts}"
            ) from exc
        preblur = FALLBACK_PREBLUR.read_bytes()
        if len(preblur) != POLAR_BYTES or sha256_bytes(preblur) != EXPECTED_PREBLUR_SHA256:
            raise AssertionError("checkpoint extraction failed and fallback preblur identity mismatched") from exc
        return raw, preblur, {
            "source": "fallback_sha_pinned",
            "fallback_path": str(FALLBACK_MASK),
            "eligibility_sha256": digest,
            "eligibility_counts": counts,
            "preblur_sha256": EXPECTED_PREBLUR_SHA256,
            "checkpoint_failure": str(exc),
        }


def write_pf32_input(path: Path) -> None:
    rgba = np.asarray(Image.open(INPUT_PNG).convert("RGBA"), dtype=np.float32)
    # The retained AEX PF32 host adapter uses MULSS by the rounded 1/255
    # constant. Float division differs by one ULP for values such as 58 and 62.
    rgba *= np.float32(1.0 / 255.0)
    argb = rgba[:, :, [3, 0, 1, 2]].copy()
    argb.tofile(path)
    if path.stat().st_size != PF32_IMAGE_BYTES:
        raise AssertionError(f"unexpected PF32 input byte count: {path.stat().st_size}")


def compile_probe(temp: Path) -> Path:
    source_include = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    probe_cpp = temp / "olmradialblur_prefill_eligibility_probe.cpp"
    probe_bin = temp / "olmradialblur_prefill_eligibility_probe"
    probe_cpp.write_text(
        f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source_include}"
#include <fstream>
#include <vector>

int main(int argc, char **argv) {{
  if (argc != 6) return 2;
  constexpr int W = {WIDTH};
  constexpr int H = {HEIGHT};
  constexpr size_t polar_floats = {POLAR_FLOATS};
  constexpr size_t cells = {ELIGIBILITY_BYTES};
  std::vector<PF_PixelFloat> input(W * H), output(W * H);
  std::vector<float> preblur(polar_floats), postblur(polar_floats);
  std::vector<A_u_char> eligibility(cells);
  std::ifstream in_file(argv[1], std::ios::binary);
  in_file.read(reinterpret_cast<char *>(input.data()), input.size() * sizeof(PF_PixelFloat));
  if (!in_file || in_file.gcount() != static_cast<std::streamsize>(input.size() * sizeof(PF_PixelFloat))) return 3;
  PF_EffectWorld in{{}}, out{{}};
  in.data = reinterpret_cast<PF_PixelPtr>(input.data());
  in.rowbytes = W * sizeof(PF_PixelFloat);
  in.width = W;
  in.height = H;
  in.extent_hint = {{0, 0, W, H}};
  out.data = reinterpret_cast<PF_PixelPtr>(output.data());
  out.rowbytes = W * sizeof(PF_PixelFloat);
  out.width = W;
  out.height = H;
  out.extent_hint = {{0, 0, W, H}};
  OLMRadialBlurInfo info{{}};
  info.blur_type = 1;
  info.center_x = 960;
  info.center_y = 540;
  info.outer_strength = 1717;
  info.outer_offset_mode = 1;
  info.inner_offset_mode = 1;
  info.repeat_border = TRUE;
  info.ratio = 1;
  info.quality = 5;
  info.brightness_gain = 1;
  info.noise_type = 1;
  info.seed = 1;
  info.thickness = 10;
  info.comp_width = W;
  info.comp_height = H;
  size_t written_floats = 0;
  size_t written_cells = 0;
  A_long polar_width = 0;
  A_long polar_height = 0;
  PF_Err err = OLMRadialBlurTestRenderFloatAndCapturePolarPlanesWithEligibility(
      &in, &out, &info, preblur.data(), postblur.data(), eligibility.data(),
      preblur.size(), eligibility.size(), &written_floats, &written_cells,
      &polar_width, &polar_height);
  if (err != PF_Err_NONE) return 4;
  if (written_floats != polar_floats || written_cells != cells) return 5;
  if (polar_width != {POLAR_WIDTH} || polar_height != {POLAR_HEIGHT}) return 6;
  std::ofstream out_file(argv[2], std::ios::binary);
  out_file.write(reinterpret_cast<const char *>(eligibility.data()), eligibility.size());
  std::ofstream preblur_file(argv[3], std::ios::binary);
  preblur_file.write(reinterpret_cast<const char *>(preblur.data()), preblur.size() * sizeof(float));
  std::ofstream postblur_file(argv[4], std::ios::binary);
  postblur_file.write(reinterpret_cast<const char *>(postblur.data()), postblur.size() * sizeof(float));
  std::ofstream final_file(argv[5], std::ios::binary);
  for (const PF_PixelFloat &pixel : output) {{
    const float rgba[4] = {{pixel.red, pixel.green, pixel.blue, pixel.alpha}};
    final_file.write(reinterpret_cast<const char *>(rgba), sizeof(rgba));
  }}
  return out_file && preblur_file && postblur_file && final_file ? 0 : 7;
}}
''',
        encoding="utf-8",
    )
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    build = subprocess.run(
        [
            os.environ.get("CXX", "clang++"),
            "-std=c++17",
            "-arch",
            "arm64",
            "-O2",
            "-fno-fast-math",
            "-ffp-contract=off",
            "-Wno-unused-function",
            "-Wno-unused-parameter",
            "-isysroot",
            sdk,
            "-I",
            str(ROOT / "Headers"),
            "-I",
            str(ROOT / "Headers/SP"),
            "-I",
            str(ROOT / "Util"),
            "-I",
            str(ROOT / "Resources"),
            "-ffunction-sections",
            "-fdata-sections",
            str(probe_cpp),
            "-Wl,-dead_strip",
            "-framework",
            "Cocoa",
            "-o",
            str(probe_bin),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if build.returncode != 0:
        raise AssertionError("probe compile failed\n" + build.stdout + build.stderr)
    return probe_bin


def run_probe() -> tuple[bytes, bytes, bytes, bytes]:
    with tempfile.TemporaryDirectory(prefix="olmradialblur_prefill_eligibility_20260718_") as tmp:
        temp = Path(tmp)
        input_raw = temp / "input_pf32.argb"
        output_mask = temp / "actual_eligibility_mask.u8"
        output_preblur = temp / "actual_preblur.f32rgba"
        output_postblur = temp / "actual_postblur.f32rgba"
        output_final = temp / "actual_final.f32rgba"
        write_pf32_input(input_raw)
        probe_bin = compile_probe(temp)
        run = subprocess.run(
            [
                str(probe_bin), str(input_raw), str(output_mask), str(output_preblur),
                str(output_postblur), str(output_final),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if run.returncode != 0:
            raise AssertionError(
                f"probe run failed rc={run.returncode}\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
            )
        if not output_mask.is_file() or output_mask.stat().st_size != ELIGIBILITY_BYTES:
            raise AssertionError("probe did not emit the expected eligibility mask")
        if not output_preblur.is_file() or output_preblur.stat().st_size != POLAR_BYTES:
            raise AssertionError("probe did not emit the expected preblur plane")
        if not output_postblur.is_file() or output_postblur.stat().st_size != POLAR_BYTES:
            raise AssertionError("probe did not emit the expected postblur plane")
        if not output_final.is_file() or output_final.stat().st_size != PF32_IMAGE_BYTES:
            raise AssertionError("probe did not emit the expected final frame")
        return (
            output_mask.read_bytes(), output_preblur.read_bytes(),
            output_postblur.read_bytes(), output_final.read_bytes(),
        )


def main() -> int:
    ensure_identities()
    expected_mask, expected_preblur, expected_meta = load_expected_prefill()
    actual_mask, actual_preblur, actual_postblur, actual_final = run_probe()
    actual_sha = sha256_bytes(actual_mask)
    actual_counts = count_mask(actual_mask)
    differing_bytes = sum(left != right for left, right in zip(actual_mask, expected_mask))
    first = first_difference(actual_mask, expected_mask)
    print("eligibility_reference=" + json.dumps(expected_meta, sort_keys=True, separators=(",", ":")))
    print(f"actual_eligibility_sha256={actual_sha}")
    print(f"expected_eligibility_sha256={EXPECTED_ELIGIBILITY_SHA256}")
    print("actual_eligibility_counts=" + json.dumps(actual_counts, sort_keys=True, separators=(",", ":")))
    print("expected_eligibility_counts=" + json.dumps(
        EXPECTED_ELIGIBILITY_COUNTS, sort_keys=True, separators=(",", ":")
    ))
    print(f"eligibility_compared_bytes={ELIGIBILITY_BYTES}")
    print(f"eligibility_differing_bytes={differing_bytes}")
    print("eligibility_first_difference=" + json.dumps(first, sort_keys=True, separators=(",", ":")))
    if differing_bytes <= 32:
        print("eligibility_all_differences=" + json.dumps(
            all_differences(actual_mask, expected_mask, 32),
            sort_keys=True,
            separators=(",", ":"),
        ))
    print("eligibility_comparison=pass_exact" if differing_bytes == 0 else "eligibility_comparison=fail_closed")
    preblur_differing = sum(left != right for left, right in zip(actual_preblur, expected_preblur))
    preblur_first = next(
        (index for index, pair in enumerate(zip(actual_preblur, expected_preblur)) if pair[0] != pair[1]),
        None,
    )
    print(f"actual_preblur_sha256={sha256_bytes(actual_preblur)}")
    print(f"expected_preblur_sha256={EXPECTED_PREBLUR_SHA256}")
    print(f"preblur_compared_bytes={POLAR_BYTES}")
    print(f"preblur_differing_bytes={preblur_differing}")
    print(f"preblur_first_difference={preblur_first}")
    print("preblur_comparison=pass_exact" if preblur_differing == 0 else "preblur_comparison=fail_closed")
    if not NORMALIZED_ORACLE.is_file() or NORMALIZED_ORACLE.stat().st_size != POLAR_BYTES:
        raise AssertionError("normalized polar oracle is missing or has the wrong size")
    expected_postblur = NORMALIZED_ORACLE.read_bytes()
    if sha256_bytes(expected_postblur) != EXPECTED_NORMALIZED_SHA256:
        raise AssertionError("normalized polar oracle identity mismatch")
    postblur_differing = sum(left != right for left, right in zip(actual_postblur, expected_postblur))
    postblur_first = next(
        (index for index, pair in enumerate(zip(actual_postblur, expected_postblur)) if pair[0] != pair[1]),
        None,
    )
    print(f"actual_postblur_sha256={sha256_bytes(actual_postblur)}")
    print(f"expected_postblur_sha256={EXPECTED_NORMALIZED_SHA256}")
    print(f"postblur_compared_bytes={POLAR_BYTES}")
    print(f"postblur_differing_bytes={postblur_differing}")
    print(f"postblur_first_difference={postblur_first}")
    print("postblur_comparison=pass_exact" if postblur_differing == 0 else "postblur_comparison=fail_closed")
    if not FINAL_FRAME_ORACLE.is_file() or FINAL_FRAME_ORACLE.stat().st_size != PF32_IMAGE_BYTES:
        raise AssertionError("final PF32 frame oracle is missing or has the wrong size")
    expected_final = FINAL_FRAME_ORACLE.read_bytes()
    if sha256_bytes(expected_final) != EXPECTED_FINAL_FRAME_SHA256:
        raise AssertionError("final PF32 frame oracle identity mismatch")
    final_differing = sum(left != right for left, right in zip(actual_final, expected_final))
    final_first = next(
        (index for index, pair in enumerate(zip(actual_final, expected_final)) if pair[0] != pair[1]),
        None,
    )
    print(f"actual_final_sha256={sha256_bytes(actual_final)}")
    print(f"expected_final_sha256={EXPECTED_FINAL_FRAME_SHA256}")
    print(f"final_compared_bytes={PF32_IMAGE_BYTES}")
    print(f"final_differing_bytes={final_differing}")
    print(f"final_first_difference={final_first}")
    actual_words = np.frombuffer(actual_final, dtype="<f4").reshape(HEIGHT, WIDTH, 4)
    expected_words = np.frombuffer(expected_final, dtype="<f4").reshape(HEIGHT, WIDTH, 4)
    word_mask = actual_words.view("<u4") != expected_words.view("<u4")
    differing_words = int(np.count_nonzero(word_mask))
    differing_pixels = int(np.count_nonzero(np.any(word_mask, axis=2)))
    differing_by_channel = [int(value) for value in np.count_nonzero(word_mask, axis=(0, 1))]
    first_word = np.argwhere(word_mask)
    first_word_detail = None
    if first_word.size:
        wy, wx, wc = (int(value) for value in first_word[0])
        first_word_detail = {
            "xy": [wx, wy],
            "channel": "RGBA"[wc],
            "actual": float(actual_words[wy, wx, wc]),
            "expected": float(expected_words[wy, wx, wc]),
            "actual_bits": f"0x{int(actual_words.view('<u4')[wy, wx, wc]):08x}",
            "expected_bits": f"0x{int(expected_words.view('<u4')[wy, wx, wc]):08x}",
        }
    finite = np.isfinite(actual_words) & np.isfinite(expected_words)
    max_abs = float(np.max(np.abs(actual_words[finite] - expected_words[finite]))) if np.any(finite) else None
    print(f"final_differing_float_words={differing_words}")
    print(f"final_differing_pixels={differing_pixels}")
    print("final_differing_words_by_rgba=" + json.dumps(differing_by_channel))
    print("final_first_word=" + json.dumps(first_word_detail, sort_keys=True, separators=(",", ":")))
    print(f"final_max_abs_diff={max_abs}")
    print("final_comparison=pass_exact" if final_differing == 0 else "final_comparison=known_red")
    return 0 if differing_bytes == 0 and preblur_differing == 0 and postblur_differing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
