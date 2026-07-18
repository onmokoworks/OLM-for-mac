#!/usr/bin/env python3
"""Bounded source and raw-frame checks for the typed RadialBlur Zoom path."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AUDIT_CPP = ROOT / "tools/emulation/audit_olmradialblur_pf32_host_adapter_20260718.cpp"
RAW_ROOT = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected")
PLANE = RAW_ROOT / "normalized_polar_plane.f32rgba"
PREBLUR_PLANE = RAW_ROOT / "preblur_polar_plane.f32rgba"
ELIGIBILITY_MASK = RAW_ROOT / "eligibility_mask.u8"
ORACLE = RAW_ROOT / "complete_pf32_frame.f32rgba"
CHECKPOINT = Path(
    "/private/tmp/olmradialblur_a9d0_boundary_nway_20260718/"
    "nway_merged_at_normalization_20260718.aexcp"
)
CHECKPOINT_MODULE = ROOT / "tools/emulation/run_olmradialblur_a9d0_boundary_fork_20260718.py"
INPUT_PNG = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
AEX_PATH = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
AEX_WEIGHT_FUNCTION = 0x18000B680
AEX_WEIGHT_COUNT = 1717
AEX_WEIGHT_BYTES = AEX_WEIGHT_COUNT * 4
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_AEX_WEIGHT_SHA256 = "82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8"
EXPECTED_BYTES = 1920 * 1080 * 4 * 4
POLAR_BYTES = 1104 * 1800 * 4 * 4
POLAR_FLOATS = POLAR_BYTES // 4
POLAR_WIDTH = 1104
POLAR_HEIGHT = 1800
ELIGIBILITY_BYTES = POLAR_WIDTH * POLAR_HEIGHT
SCALAR_PLANE_BYTES = ELIGIBILITY_BYTES * 4
EXPECTED_POLAR_SHA256 = "c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8"
EXPECTED_PREBLUR_SHA256 = "fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef"
EXPECTED_ELIGIBILITY_SHA256 = "861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7"
EXPECTED_ELIGIBILITY_COUNTS = {0: 565113, 1: 1422087}
EXPECTED_SPAN_SHA256 = "2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f"
EXPECTED_SOURCE_SCALAR_SHA256 = "13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce"
EXPECTED_SOURCE_SCALAR_COUNTS = {
    0x3F800000: 1922504,
    0x3F7FFFFF: 58895,
    0x3F800001: 5108,
    0x3F7FFFFE: 693,
}
EXPECTED_SPAN_COUNTS = {
    0x3F800000: 1922497,
    0x3F7FFFFF: 58895,
    0x3F800001: 5108,
    0x3F7FFFFE: 693,
    0x3F68BA54: 1,
    0x3F2A3000: 1,
    0x3F4B3000: 1,
    0x3F6C2000: 1,
    0x3D520000: 1,
    0x3F511000: 1,
    0x3F727000: 1,
}
EXPECTED_CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
EXPECTED_CHECKPOINT_RIP = 0x180005C9F
EXPECTED_PRODUCTION_PREBLUR_SHA256 = "8e245bccbda1a856df3e079d4b49d81af256c844acee6557a1375ebebad11530"
EXPECTED_PRODUCTION_POSTBLUR_SHA256 = "64b237cd1e46d65aef300f94caf5bec1b45bfac9a2b9b945f86780f435e64cdd"
EXPECTED_WORKER_SHA256 = "76669d0d85dd711e73ff130335a3667bc3bbc0799ac0116c2ac17320e35e81c0"
EXPECTED_CANDIDATE1_SHA256 = "9a68c2f490aa62c156389e1682f8ac37d6b1d34d769cc8beadcd3941d3f0c4bb"
EXPECTED_CANDIDATE2_SHA256 = "0095a814ddaae2f82a13bf98c02c79f2b8c8a67a7ba5837010d06b311e81e4fe"
EXPECTED_CANDIDATE3_SHA256 = "5b911036e356ed2d17a47b4aa89ca59271b4106abf8c8f19899870a5d0284331"
EXPECTED_CANDIDATE4_SHA256 = "221d571e6ddaba753d982af61fe4d7e4d6b5d8be2ed61eb97c9fb5d078f4c6d5"
EXPECTED_CANDIDATE5_SHA256 = "940d3d8c914111362674f7c49216dab1e59ce0e7dffef18e1934e7ee9004d79e"
EXPECTED_CANDIDATE6_SHA256 = EXPECTED_POLAR_SHA256


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


def extract_aex_weight_table(output_path: Path) -> dict[str, object]:
    if not AEX_PATH.is_file() or sha256(AEX_PATH) != EXPECTED_AEX_SHA256:
        raise AssertionError("AEX identity mismatch for weight-table extraction")
    sys.path.insert(0, str(ROOT / "tools/emulation"))
    from aex_loader import AexLoader  # noqa: PLC0415

    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    address = loader.bump_alloc(AEX_WEIGHT_BYTES, align=16)
    loader.write_bytes(address, b"\xa5" * AEX_WEIGHT_BYTES)
    result = loader.call_function(
        AEX_WEIGHT_FUNCTION,
        int_args=[address, AEX_WEIGHT_COUNT],
        max_instructions=2_000_000,
    )
    raw = loader.read_bytes(address, AEX_WEIGHT_BYTES)
    if len(raw) != AEX_WEIGHT_BYTES:
        raise AssertionError(f"AEX weight output size mismatch: {len(raw)}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_AEX_WEIGHT_SHA256:
        raise AssertionError(f"AEX weight output hash mismatch: {digest}")
    imports = sorted({entry.name for entry in loader.import_log})
    if imports != ["expf"]:
        raise AssertionError(f"unexpected AEX weight imports: {imports}")
    output_path.write_bytes(raw)
    if output_path.stat().st_size != AEX_WEIGHT_BYTES or sha256(output_path) != digest:
        raise AssertionError("persisted AEX weight table failed identity check")
    return {
        "aex_sha256": EXPECTED_AEX_SHA256,
        "function": f"0x{AEX_WEIGHT_FUNCTION:x}",
        "length": AEX_WEIGHT_COUNT,
        "output_bytes": len(raw),
        "output_sha256": digest,
        "imports": imports,
        "instructions": result["instructions"],
    }


def float_residual_stats(actual: bytes, oracle: bytes) -> dict[str, object]:
    if len(actual) != len(oracle) or len(actual) % 4:
        raise AssertionError("float residual inputs have incompatible sizes")
    actual_bits = np.frombuffer(actual, dtype="<u4")
    oracle_bits = np.frombuffer(oracle, dtype="<u4")
    different = actual_bits != oracle_bits
    different_words = int(np.count_nonzero(different))
    channel_counts = {
        channel: int(np.count_nonzero(different[index::4]))
        for index, channel in enumerate("RGBA")
    }
    actual_zero = (actual_bits & np.uint32(0x7FFFFFFF)) == 0
    oracle_zero = (oracle_bits & np.uint32(0x7FFFFFFF)) == 0
    zero_vs_nonzero = int(np.count_nonzero(different & (actual_zero ^ oracle_zero)))

    differing_actual = actual_bits[different]
    differing_oracle = oracle_bits[different]
    sign = np.uint32(0x80000000)
    actual_ordered = np.where(
        (differing_actual & sign) != 0,
        ~differing_actual,
        differing_actual | sign,
    ).astype(np.uint64)
    oracle_ordered = np.where(
        (differing_oracle & sign) != 0,
        ~differing_oracle,
        differing_oracle | sign,
    ).astype(np.uint64)
    ulp = np.maximum(actual_ordered, oracle_ordered) - np.minimum(actual_ordered, oracle_ordered)
    histogram = {str(value): int(np.count_nonzero(ulp == value)) for value in range(1, 5)}
    histogram[">4"] = int(np.count_nonzero(ulp > 4))
    return {
        "compared_float_words": int(actual_bits.size),
        "differing_float_words": different_words,
        "channel_differing_float_words": channel_counts,
        "ulp_histogram": histogram,
        "max_ulp": int(ulp.max()) if different_words else 0,
        "zero_vs_nonzero_float_words": zero_vs_nonzero,
    }


def extract_checkpoint_inputs() -> tuple[bytes, bytes, bytes, bytes, dict[str, object]]:
    checkpoint_sha256 = sha256(CHECKPOINT)
    if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
        raise AssertionError(f"checkpoint identity mismatch: {checkpoint_sha256}")
    spec = importlib.util.spec_from_file_location("olmradialblur_checkpoint_reader", CHECKPOINT_MODULE)
    if not spec or not spec.loader:
        raise AssertionError("cannot load checkpoint reader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    checkpoint = module.Checkpoint.read(CHECKPOINT)
    rip = int(checkpoint.header["registers"]["gp"]["rip"])
    if rip != EXPECTED_CHECKPOINT_RIP:
        raise AssertionError(f"checkpoint is not at pre-normalization RIP: 0x{rip:x}")
    captured = checkpoint.header.get("metadata", {}).get("captured", {})
    work = int(captured.get("zoom_param1") or 0)
    if not work:
        raise AssertionError("checkpoint has no live Zoom work pointer")

    def read_checkpoint(address: int, size: int) -> bytes:
        for region in checkpoint.header["regions"]:
            base = int(region["address"])
            region_size = int(region["size"])
            if base <= address and address + size <= base + region_size:
                raw = checkpoint.raw_region(region["name"])
                offset = address - base
                return bytes(raw[offset:offset + size])
        raise AssertionError(f"checkpoint range is not contained: 0x{address:x}+{size}")

    source_pointer = struct.unpack("<Q", read_checkpoint(work + 0x38, 8))[0]
    raw = read_checkpoint(source_pointer, POLAR_BYTES)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_PREBLUR_SHA256:
        raise AssertionError(f"checkpoint pre-blur hash mismatch: {digest}")
    if raw[:16].hex() != "0000803f00000000000000000000803f":
        raise AssertionError("checkpoint pre-blur first16 mismatch")
    rbp = int(checkpoint.header["registers"]["gp"]["rbp"])
    eligibility_slot = rbp - 0x60
    eligibility_pointer = struct.unpack("<Q", read_checkpoint(eligibility_slot, 8))[0]
    eligibility = read_checkpoint(eligibility_pointer, ELIGIBILITY_BYTES)
    eligibility_digest = hashlib.sha256(eligibility).hexdigest()
    if eligibility_digest != EXPECTED_ELIGIBILITY_SHA256:
        raise AssertionError(f"checkpoint eligibility hash mismatch: {eligibility_digest}")
    counts = {value: eligibility.count(value) for value in set(eligibility)}
    if counts != EXPECTED_ELIGIBILITY_COUNTS:
        raise AssertionError(f"checkpoint eligibility counts mismatch: {counts}")
    mask_array = np.frombuffer(eligibility, dtype=np.uint8).reshape(POLAR_HEIGHT, POLAR_WIDTH)
    alpha_bits = np.frombuffer(raw, dtype="<u4").reshape(POLAR_HEIGHT, POLAR_WIDTH, 4)[:, :, 3]
    alpha_zero = (alpha_bits & np.uint32(0x7FFFFFFF)) == 0
    mask_zero_alpha_nonzero = int(np.count_nonzero((mask_array == 0) & ~alpha_zero))
    mask_nonzero_alpha_zero = int(np.count_nonzero((mask_array != 0) & alpha_zero))
    zero_locations = np.nonzero(mask_array == 0)
    zero_radius_min = int(zero_locations[1].min())
    zero_radius_max = int(zero_locations[1].max())
    zero_counts_by_radius = {
        radius: int(np.count_nonzero(mask_array[:, radius] == 0))
        for radius in (960, 961, 1103)
    }
    if (mask_zero_alpha_nonzero != 565113 or mask_nonzero_alpha_zero != 0 or
            (zero_radius_min, zero_radius_max) != (540, 1103) or
            zero_counts_by_radius != {960: 1115, 961: 1143, 1103: 1799}):
        raise AssertionError("eligibility mask alpha-independence or radius distribution mismatch")
    if (not ELIGIBILITY_MASK.is_file() or ELIGIBILITY_MASK.stat().st_size != ELIGIBILITY_BYTES or
            sha256(ELIGIBILITY_MASK) != eligibility_digest or ELIGIBILITY_MASK.read_bytes() != eligibility):
        raise AssertionError("eligibility mask file is not byte-identical to checkpoint RBP-0x60 extraction")

    def extract_scalar_plane(slot_offset: int, expected_sha256: str,
                             expected_counts: dict[int, int]) -> tuple[bytes, int, dict[int, int]]:
        pointer = struct.unpack("<Q", read_checkpoint(work + slot_offset, 8))[0]
        plane = read_checkpoint(pointer, SCALAR_PLANE_BYTES)
        digest = hashlib.sha256(plane).hexdigest()
        words = np.frombuffer(plane, dtype="<u4")
        unique, unique_counts = np.unique(words, return_counts=True)
        counts_by_bits = {int(bits): int(count) for bits, count in zip(unique, unique_counts)}
        if digest != expected_sha256 or counts_by_bits != expected_counts:
            raise AssertionError(f"checkpoint scalar plane +0x{slot_offset:x} identity mismatch")
        return plane, pointer, counts_by_bits

    span_plane, span_pointer, span_counts = extract_scalar_plane(
        0x40, EXPECTED_SPAN_SHA256, EXPECTED_SPAN_COUNTS)
    source_scalar_plane, source_scalar_pointer, source_scalar_counts = extract_scalar_plane(
        0x50, EXPECTED_SOURCE_SCALAR_SHA256, EXPECTED_SOURCE_SCALAR_COUNTS)
    return raw, eligibility, span_plane, source_scalar_plane, {
        "checkpoint_sha256": checkpoint_sha256,
        "aex_sha256": checkpoint.header["aex"]["sha256"],
        "rip": f"0x{rip:x}",
        "work_pointer": f"0x{work:x}",
        "source_pointer": f"0x{source_pointer:x}",
        "preblur_sha256": digest,
        "rbp": f"0x{rbp:x}",
        "eligibility_slot": f"0x{eligibility_slot:x}",
        "eligibility_pointer": f"0x{eligibility_pointer:x}",
        "eligibility_bytes": len(eligibility),
        "eligibility_sha256": eligibility_digest,
        "eligibility_counts": counts,
        "mask_zero_alpha_nonzero": mask_zero_alpha_nonzero,
        "mask_nonzero_alpha_zero": mask_nonzero_alpha_zero,
        "zero_radius_range": [zero_radius_min, zero_radius_max],
        "zero_counts_by_radius": zero_counts_by_radius,
        "span_plane_pointer": f"0x{span_pointer:x}",
        "span_plane_bytes": len(span_plane),
        "span_plane_sha256": EXPECTED_SPAN_SHA256,
        "span_plane_counts_by_bits": {f"0x{bits:08x}": count for bits, count in span_counts.items()},
        "source_scalar_pointer": f"0x{source_scalar_pointer:x}",
        "source_scalar_bytes": len(source_scalar_plane),
        "source_scalar_sha256": EXPECTED_SOURCE_SCALAR_SHA256,
        "source_scalar_counts_by_bits": {
            f"0x{bits:08x}": count for bits, count in source_scalar_counts.items()
        },
    }


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


def run_production_adapter(
        temp: Path, exact_weights_path: Path, eligibility_path: Path,
        span_plane_path: Path, source_scalar_path: Path) -> dict[str, object]:
    rgba = np.asarray(Image.open(INPUT_PNG).convert("RGBA"), dtype=np.float32) / np.float32(255.0)
    argb = rgba[:, :, [3, 0, 1, 2]].copy()
    input_raw = temp / "input_pf32.argb"
    output_raw = temp / "output_pf32.argb"
    preblur_raw = temp / "production_preblur_polar.f32rgba"
    postblur_raw = temp / "production_normalized_polar.f32rgba"
    worker_raw = temp / "production_worker_from_aex_preblur.f32rgba"
    candidate_raw = temp / "aex_worker_candidate1_from_aex_preblur.f32rgba"
    candidate2_raw = temp / "aex_worker_candidate2_from_aex_preblur.f32rgba"
    candidate3_raw = temp / "aex_worker_candidate3_from_aex_preblur.f32rgba"
    candidate4_raw = temp / "aex_worker_candidate4_from_aex_preblur.f32rgba"
    candidate5_raw = temp / "aex_worker_candidate5_from_aex_preblur.f32rgba"
    candidate6_raw = temp / "aex_worker_candidate6_from_aex_preblur.f32rgba"
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
  if (argc != 17) return 2;
  constexpr int W=1920, H=1080;
  std::vector<PF_PixelFloat> input(W*H), output(W*H);
  std::vector<float> preblur({POLAR_FLOATS}), postblur({POLAR_FLOATS});
  std::vector<float> aex_preblur({POLAR_FLOATS}), worker_output({POLAR_FLOATS});
  std::vector<float> candidate_output({POLAR_FLOATS}), candidate2_output({POLAR_FLOATS});
  std::vector<float> candidate3_output({POLAR_FLOATS}), candidate4_output({POLAR_FLOATS});
  std::vector<float> candidate5_output({POLAR_FLOATS});
  std::vector<float> candidate6_output({POLAR_FLOATS});
  std::vector<float> exact_weights({AEX_WEIGHT_COUNT});
  std::vector<A_u_char> eligibility({ELIGIBILITY_BYTES});
  std::vector<float> span_plane({ELIGIBILITY_BYTES}), source_scalar_plane({ELIGIBILITY_BYTES});
  std::ifstream in_file(argv[1], std::ios::binary);
  in_file.read(reinterpret_cast<char *>(input.data()), input.size()*sizeof(PF_PixelFloat));
  if (!in_file || in_file.gcount() != static_cast<std::streamsize>(input.size()*sizeof(PF_PixelFloat))) return 3;
  std::ifstream aex_preblur_file(argv[5], std::ios::binary);
  aex_preblur_file.read(reinterpret_cast<char *>(aex_preblur.data()), aex_preblur.size()*sizeof(float));
  if (!aex_preblur_file || aex_preblur_file.gcount() != static_cast<std::streamsize>(aex_preblur.size()*sizeof(float))) return 7;
  std::ifstream exact_weights_file(argv[10], std::ios::binary);
  exact_weights_file.read(reinterpret_cast<char *>(exact_weights.data()), exact_weights.size()*sizeof(float));
  if (!exact_weights_file || exact_weights_file.gcount() != static_cast<std::streamsize>(exact_weights.size()*sizeof(float))) return 16;
  std::ifstream eligibility_file(argv[12], std::ios::binary);
  eligibility_file.read(reinterpret_cast<char *>(eligibility.data()), eligibility.size());
  if (!eligibility_file || eligibility_file.gcount() != static_cast<std::streamsize>(eligibility.size())) return 19;
  std::ifstream span_file(argv[14], std::ios::binary);
  span_file.read(reinterpret_cast<char *>(span_plane.data()), span_plane.size()*sizeof(float));
  if (!span_file || span_file.gcount() != static_cast<std::streamsize>(span_plane.size()*sizeof(float))) return 22;
  std::ifstream source_scalar_file(argv[15], std::ios::binary);
  source_scalar_file.read(reinterpret_cast<char *>(source_scalar_plane.data()), source_scalar_plane.size()*sizeof(float));
  if (!source_scalar_file || source_scalar_file.gcount() != static_cast<std::streamsize>(source_scalar_plane.size()*sizeof(float))) return 23;
  PF_EffectWorld in{{}}, out{{}};
  in.data=(PF_PixelPtr)input.data(); in.rowbytes=W*sizeof(PF_PixelFloat); in.width=W; in.height=H;
  in.extent_hint={{0,0,W,H}}; out.data=(PF_PixelPtr)output.data(); out.rowbytes=W*sizeof(PF_PixelFloat);
  out.width=W; out.height=H; out.extent_hint={{0,0,W,H}};
  OLMRadialBlurInfo info{{}}; info.blur_type=1; info.center_x=960; info.center_y=540;
  info.outer_strength=1717; info.outer_offset_mode=1; info.inner_offset_mode=1;
  info.repeat_border=TRUE; info.ratio=1; info.quality=5; info.brightness_gain=1;
  info.noise_type=1; info.seed=1; info.thickness=10; info.comp_width=W; info.comp_height=H;
  size_t written_floats=0; A_long polar_width=0, polar_height=0;
  if (OLMRadialBlurTestRenderFloatAndCapturePolarPlanes(
        &in,&out,&info,preblur.data(),postblur.data(),preblur.size(),
        &written_floats,&polar_width,&polar_height) != PF_Err_NONE) return 4;
  if (written_floats != preblur.size() || polar_width != {POLAR_WIDTH} || polar_height != {POLAR_HEIGHT}) return 5;
  size_t worker_written=0; A_Boolean worker_used_fft=FALSE;
  if (OLMRadialBlurTestRunFloatWorker(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,worker_output.data(),worker_output.size(),
        &worker_written,&worker_used_fft) != PF_Err_NONE) return 8;
  if (worker_written != worker_output.size() || worker_used_fft != TRUE) return 9;
  size_t candidate_written=0; A_long candidate_weight_count=0;
  if (OLMRadialBlurTestRunAEXWorkerCandidate(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,candidate_output.data(),candidate_output.size(),
        &candidate_written,&candidate_weight_count) != PF_Err_NONE) return 10;
  if (candidate_written != candidate_output.size() || candidate_weight_count != 1717) return 11;
  size_t candidate2_written=0; A_long candidate2_weight_count=0;
  if (OLMRadialBlurTestRunAEXWorkerCandidate2(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,candidate2_output.data(),candidate2_output.size(),
        &candidate2_written,&candidate2_weight_count) != PF_Err_NONE) return 12;
  if (candidate2_written != candidate2_output.size() || candidate2_weight_count != 1717) return 13;
  size_t candidate3_written=0; A_long candidate3_weight_count=0;
  if (OLMRadialBlurTestRunAEXWorkerCandidate3(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,candidate3_output.data(),candidate3_output.size(),
        &candidate3_written,&candidate3_weight_count) != PF_Err_NONE) return 14;
  if (candidate3_written != candidate3_output.size() || candidate3_weight_count != 1717) return 15;
  size_t candidate4_written=0; A_long candidate4_weight_count=0;
  if (OLMRadialBlurTestRunAEXWorkerCandidate4(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,exact_weights.data(),exact_weights.size(),
        candidate4_output.data(),candidate4_output.size(),&candidate4_written,&candidate4_weight_count) != PF_Err_NONE) return 17;
  if (candidate4_written != candidate4_output.size() || candidate4_weight_count != 1717) return 18;
  size_t candidate5_written=0; A_long candidate5_weight_count=0;
  if (OLMRadialBlurTestRunCandidate5DirectionMaskDiagnostic(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,exact_weights.data(),exact_weights.size(),
        eligibility.data(),eligibility.size(),candidate5_output.data(),candidate5_output.size(),
        &candidate5_written,&candidate5_weight_count) != PF_Err_NONE) return 20;
  if (candidate5_written != candidate5_output.size() || candidate5_weight_count != 1717) return 21;
  size_t candidate6_written=0; A_long candidate6_weight_count=0;
  if (OLMRadialBlurTestRunCandidate6ScalarPlaneDiagnostic(
        aex_preblur.data(),{POLAR_WIDTH},{POLAR_HEIGHT},&info,exact_weights.data(),exact_weights.size(),
        eligibility.data(),eligibility.size(),span_plane.data(),source_scalar_plane.data(),span_plane.size(),
        candidate6_output.data(),candidate6_output.size(),&candidate6_written,&candidate6_weight_count) != PF_Err_NONE) return 24;
  if (candidate6_written != candidate6_output.size() || candidate6_weight_count != 1717) return 25;
  std::ofstream out_file(argv[2], std::ios::binary);
  out_file.write(reinterpret_cast<const char *>(output.data()), output.size()*sizeof(PF_PixelFloat));
  std::ofstream preblur_file(argv[3], std::ios::binary);
  preblur_file.write(reinterpret_cast<const char *>(preblur.data()), preblur.size()*sizeof(float));
  std::ofstream postblur_file(argv[4], std::ios::binary);
  postblur_file.write(reinterpret_cast<const char *>(postblur.data()), postblur.size()*sizeof(float));
  std::ofstream worker_file(argv[6], std::ios::binary);
  worker_file.write(reinterpret_cast<const char *>(worker_output.data()), worker_output.size()*sizeof(float));
  std::ofstream candidate_file(argv[7], std::ios::binary);
  candidate_file.write(reinterpret_cast<const char *>(candidate_output.data()), candidate_output.size()*sizeof(float));
  std::ofstream candidate2_file(argv[8], std::ios::binary);
  candidate2_file.write(reinterpret_cast<const char *>(candidate2_output.data()), candidate2_output.size()*sizeof(float));
  std::ofstream candidate3_file(argv[9], std::ios::binary);
  candidate3_file.write(reinterpret_cast<const char *>(candidate3_output.data()), candidate3_output.size()*sizeof(float));
  std::ofstream candidate4_file(argv[11], std::ios::binary);
  candidate4_file.write(reinterpret_cast<const char *>(candidate4_output.data()), candidate4_output.size()*sizeof(float));
  std::ofstream candidate5_file(argv[13], std::ios::binary);
  candidate5_file.write(reinterpret_cast<const char *>(candidate5_output.data()), candidate5_output.size()*sizeof(float));
  std::ofstream candidate6_file(argv[16], std::ios::binary);
  candidate6_file.write(reinterpret_cast<const char *>(candidate6_output.data()), candidate6_output.size()*sizeof(float));
  return out_file && preblur_file && postblur_file && worker_file && candidate_file && candidate2_file && candidate3_file && candidate4_file && candidate5_file && candidate6_file ? 0 : 6;
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
        [str(binary), str(input_raw), str(output_raw), str(preblur_raw), str(postblur_raw),
         str(PREBLUR_PLANE), str(worker_raw), str(candidate_raw), str(candidate2_raw), str(candidate3_raw),
         str(exact_weights_path), str(candidate4_raw), str(eligibility_path), str(candidate5_raw),
         str(span_plane_path), str(source_scalar_path), str(candidate6_raw)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if (run.returncode != 0 or output_raw.stat().st_size != EXPECTED_BYTES or
            preblur_raw.stat().st_size != POLAR_BYTES or postblur_raw.stat().st_size != POLAR_BYTES or
            worker_raw.stat().st_size != POLAR_BYTES or candidate_raw.stat().st_size != POLAR_BYTES or
            candidate2_raw.stat().st_size != POLAR_BYTES or candidate3_raw.stat().st_size != POLAR_BYTES or
            candidate4_raw.stat().st_size != POLAR_BYTES or candidate5_raw.stat().st_size != POLAR_BYTES or
            candidate6_raw.stat().st_size != POLAR_BYTES):
        raise AssertionError(f"production adapter failed closed rc={run.returncode}\n{run.stdout}{run.stderr}")
    host_argb = np.fromfile(output_raw, dtype=np.float32).reshape(1080, 1920, 4)
    host_rgba = host_argb[:, :, [1, 2, 3, 0]].copy().tobytes()
    frame_differing, frame_first = compare_bytes(host_rgba, ORACLE.read_bytes())
    production_preblur = preblur_raw.read_bytes()
    actual_aex_preblur = PREBLUR_PLANE.read_bytes()
    preblur_differing, preblur_first = compare_bytes(production_preblur, actual_aex_preblur)
    production_polar = postblur_raw.read_bytes()
    oracle_polar = PLANE.read_bytes()
    polar_differing, polar_first = compare_bytes(production_polar, oracle_polar)
    worker_output = worker_raw.read_bytes()
    worker_differing, worker_first = compare_bytes(worker_output, oracle_polar)
    candidate_output = candidate_raw.read_bytes()
    candidate_differing, candidate_first = compare_bytes(candidate_output, oracle_polar)
    candidate2_output = candidate2_raw.read_bytes()
    candidate2_differing, candidate2_first = compare_bytes(candidate2_output, oracle_polar)
    candidate3_output = candidate3_raw.read_bytes()
    candidate3_differing, candidate3_first = compare_bytes(candidate3_output, oracle_polar)
    candidate4_output = candidate4_raw.read_bytes()
    candidate4_differing, candidate4_first = compare_bytes(candidate4_output, oracle_polar)
    candidate5_output = candidate5_raw.read_bytes()
    candidate5_differing, candidate5_first = compare_bytes(candidate5_output, oracle_polar)
    candidate6_output = candidate6_raw.read_bytes()
    candidate6_differing, candidate6_first = compare_bytes(candidate6_output, oracle_polar)
    return {
        "frame_differing_bytes": frame_differing,
        "frame_first_difference": frame_first,
        "preblur_differing_bytes": preblur_differing,
        "preblur_first_difference": polar_first_difference(production_preblur, actual_aex_preblur, preblur_first),
        "production_preblur_sha256": sha256(preblur_raw),
        "polar_differing_bytes": polar_differing,
        "polar_first_difference": polar_first_difference(production_polar, oracle_polar, polar_first),
        "production_polar_sha256": sha256(postblur_raw),
        "worker_differing_bytes": worker_differing,
        "worker_first_difference": polar_first_difference(worker_output, oracle_polar, worker_first),
        "worker_sha256": sha256(worker_raw),
        "candidate_differing_bytes": candidate_differing,
        "candidate_first_difference": polar_first_difference(candidate_output, oracle_polar, candidate_first),
        "candidate_sha256": sha256(candidate_raw),
        "candidate2_differing_bytes": candidate2_differing,
        "candidate2_first_difference": polar_first_difference(candidate2_output, oracle_polar, candidate2_first),
        "candidate2_sha256": sha256(candidate2_raw),
        "candidate3_differing_bytes": candidate3_differing,
        "candidate3_first_difference": polar_first_difference(candidate3_output, oracle_polar, candidate3_first),
        "candidate3_sha256": sha256(candidate3_raw),
        "candidate4_differing_bytes": candidate4_differing,
        "candidate4_first_difference": polar_first_difference(candidate4_output, oracle_polar, candidate4_first),
        "candidate4_sha256": sha256(candidate4_raw),
        "candidate4_float_residual_stats": float_residual_stats(candidate4_output, oracle_polar),
        "candidate4_residual_classification": (
            "rgb_structural_or_accumulation_residual_not_weight_generation_or_simple_ulp_rounding"
        ),
        "candidate5_differing_bytes": candidate5_differing,
        "candidate5_first_difference": polar_first_difference(candidate5_output, oracle_polar, candidate5_first),
        "candidate5_sha256": sha256(candidate5_raw),
        "candidate5_float_residual_stats": float_residual_stats(candidate5_output, oracle_polar),
        "candidate6_differing_bytes": candidate6_differing,
        "candidate6_first_difference": polar_first_difference(candidate6_output, oracle_polar, candidate6_first),
        "candidate6_sha256": sha256(candidate6_raw),
        "candidate6_float_residual_stats": float_residual_stats(candidate6_output, oracle_polar),
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
        "OLMRadialBlurTestRenderFloatAndCapturePolarPlanes",
        "OLMRadialBlurTestRunFloatWorker",
        "OLMRadialBlurTestRunAEXWorkerCandidate",
        "OLMRadialBlurTestRunAEXWorkerCandidate2",
        "OLMRadialBlurTestRunAEXWorkerCandidate3",
        "OLMRadialBlurTestRunAEXWorkerCandidate4",
        "OLMRadialBlurTestRunCandidate5DirectionMaskDiagnostic",
        "OLMRadialBlurTestRunCandidate6ScalarPlaneDiagnostic",
        "ZoomGaussianWeightsAEXScalarCandidate",
        "BuildZoomBlurredPolar(polar, info, debug, &use_fft_convolution)",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise AssertionError(f"missing typed-render contract: {missing}")
    if source.count("BuildZoomBlurredPolar(") != 3:
        raise AssertionError("worker logic must have one definition and exactly two callers")
    dispatch = re.search(r"static PF_Err RenderWorld\(.*?\n\}", source, re.DOTALL)
    if not dispatch or "CopyWorld<PF_Pixel16>" in dispatch.group(0) or "CopyWorld<PF_PixelFloat>" in dispatch.group(0):
        raise AssertionError("deep RenderWorld dispatch still contains a no-op copy")

    print("source_contract=pass")
    if (not PLANE.is_file() or not PREBLUR_PLANE.is_file() or not ELIGIBILITY_MASK.is_file() or
            not ORACLE.is_file() or not CHECKPOINT.is_file()):
        print("raw_frame_comparison=skipped_missing_local_oracle")
        print("ae_exact_claim=false")
        return 0
    if (PLANE.stat().st_size != POLAR_BYTES or PREBLUR_PLANE.stat().st_size != POLAR_BYTES or
            ORACLE.stat().st_size != EXPECTED_BYTES):
        raise AssertionError("local oracle has an unexpected byte size")
    if sha256(PLANE) != EXPECTED_POLAR_SHA256:
        raise AssertionError("corrected normalized polar oracle hash mismatch")
    if sha256(PREBLUR_PLANE) != EXPECTED_PREBLUR_SHA256:
        raise AssertionError("pre-blur polar oracle hash mismatch")
    (checkpoint_preblur, checkpoint_eligibility, checkpoint_span,
     checkpoint_source_scalar, checkpoint_identity) = extract_checkpoint_inputs()
    if checkpoint_preblur != PREBLUR_PLANE.read_bytes():
        raise AssertionError("pre-blur oracle is not byte-identical to the pinned checkpoint extraction")
    print("checkpoint_preblur_identity=" + json.dumps(checkpoint_identity, sort_keys=True, separators=(",", ":")))

    with tempfile.TemporaryDirectory(prefix="olmradialblur_typed_deep_20260718_") as tmp:
        exact_weights_path = Path(tmp) / "aex_loader_exact_weights_1717.f32"
        eligibility_path = Path(tmp) / "checkpoint_eligibility_mask.u8"
        span_plane_path = Path(tmp) / "checkpoint_span_plane.f32"
        source_scalar_path = Path(tmp) / "checkpoint_source_scalar_plane.f32"
        eligibility_path.write_bytes(checkpoint_eligibility)
        if (eligibility_path.stat().st_size != ELIGIBILITY_BYTES or
                sha256(eligibility_path) != EXPECTED_ELIGIBILITY_SHA256):
            raise AssertionError("temporary eligibility mask identity mismatch")
        span_plane_path.write_bytes(checkpoint_span)
        source_scalar_path.write_bytes(checkpoint_source_scalar)
        if (span_plane_path.stat().st_size != SCALAR_PLANE_BYTES or
                sha256(span_plane_path) != EXPECTED_SPAN_SHA256 or
                source_scalar_path.stat().st_size != SCALAR_PLANE_BYTES or
                sha256(source_scalar_path) != EXPECTED_SOURCE_SCALAR_SHA256):
            raise AssertionError("temporary scalar plane identity mismatch")
        weight_identity = extract_aex_weight_table(exact_weights_path)
        print("aex_weight_table_identity=" + json.dumps(
            weight_identity, sort_keys=True, separators=(",", ":")))
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
        production = run_production_adapter(
            Path(tmp), exact_weights_path, eligibility_path, span_plane_path, source_scalar_path)
        expected_production = {
            "production_preblur_sha256": EXPECTED_PRODUCTION_PREBLUR_SHA256,
            "preblur_differing_bytes": 327417,
            "production_polar_sha256": EXPECTED_PRODUCTION_POSTBLUR_SHA256,
            "polar_differing_bytes": 13953051,
            "worker_sha256": EXPECTED_WORKER_SHA256,
            "worker_differing_bytes": 12744511,
            "candidate_sha256": EXPECTED_CANDIDATE1_SHA256,
            "candidate_differing_bytes": 5779701,
            "candidate2_sha256": EXPECTED_CANDIDATE2_SHA256,
            "candidate2_differing_bytes": 5535769,
            "candidate3_sha256": EXPECTED_CANDIDATE3_SHA256,
            "candidate3_differing_bytes": 5533669,
            "candidate4_sha256": EXPECTED_CANDIDATE4_SHA256,
            "candidate4_differing_bytes": 5465443,
            "candidate5_sha256": EXPECTED_CANDIDATE5_SHA256,
            "candidate5_differing_bytes": 21375,
            "candidate6_sha256": EXPECTED_CANDIDATE6_SHA256,
            "candidate6_differing_bytes": 0,
            "frame_differing_bytes": 10047226,
        }
        for key, expected in expected_production.items():
            if production[key] != expected:
                raise AssertionError(f"production behavior changed: {key}={production[key]!r}, expected={expected!r}")
        print(f"production_preblur_compared_bytes={POLAR_BYTES}")
        print(f"production_preblur_differing_bytes={production['preblur_differing_bytes']}")
        print("production_preblur_first_difference=" + json.dumps(
            production["preblur_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"production_preblur_sha256={production['production_preblur_sha256']}")
        print("production_preblur_comparison=pass_exact" if production["preblur_differing_bytes"] == 0
              else "production_preblur_comparison=known_red_fail_closed")
        print(f"production_polar_compared_bytes={POLAR_BYTES}")
        print(f"production_polar_differing_bytes={production['polar_differing_bytes']}")
        print("production_polar_first_difference=" + json.dumps(
            production["polar_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"production_polar_sha256={production['production_polar_sha256']}")
        print("production_polar_comparison=pass_exact" if production["polar_differing_bytes"] == 0
              else "production_polar_comparison=known_red_fail_closed")
        print(f"worker_from_aex_preblur_compared_bytes={POLAR_BYTES}")
        print(f"worker_from_aex_preblur_differing_bytes={production['worker_differing_bytes']}")
        print("worker_from_aex_preblur_first_difference=" + json.dumps(
            production["worker_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"worker_from_aex_preblur_sha256={production['worker_sha256']}")
        print("worker_from_aex_preblur_comparison=pass_exact" if production["worker_differing_bytes"] == 0
              else "worker_from_aex_preblur_comparison=known_red_fail_closed")
        print(f"aex_worker_candidate1_compared_bytes={POLAR_BYTES}")
        print(f"aex_worker_candidate1_differing_bytes={production['candidate_differing_bytes']}")
        print("aex_worker_candidate1_first_difference=" + json.dumps(
            production["candidate_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"aex_worker_candidate1_sha256={production['candidate_sha256']}")
        print("aex_worker_candidate1_comparison=pass_exact" if production["candidate_differing_bytes"] == 0
              else "aex_worker_candidate1_comparison=known_red_fail_closed")
        print(f"aex_worker_candidate2_compared_bytes={POLAR_BYTES}")
        print(f"aex_worker_candidate2_differing_bytes={production['candidate2_differing_bytes']}")
        print("aex_worker_candidate2_first_difference=" + json.dumps(
            production["candidate2_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"aex_worker_candidate2_sha256={production['candidate2_sha256']}")
        print("aex_worker_candidate2_comparison=pass_exact" if production["candidate2_differing_bytes"] == 0
              else "aex_worker_candidate2_comparison=known_red_fail_closed")
        print(f"aex_worker_candidate3_compared_bytes={POLAR_BYTES}")
        print(f"aex_worker_candidate3_differing_bytes={production['candidate3_differing_bytes']}")
        print("aex_worker_candidate3_first_difference=" + json.dumps(
            production["candidate3_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"aex_worker_candidate3_sha256={production['candidate3_sha256']}")
        print("aex_worker_candidate3_comparison=pass_exact" if production["candidate3_differing_bytes"] == 0
              else "aex_worker_candidate3_comparison=known_red_fail_closed")
        print(f"aex_worker_candidate4_compared_bytes={POLAR_BYTES}")
        print(f"aex_worker_candidate4_differing_bytes={production['candidate4_differing_bytes']}")
        print("aex_worker_candidate4_first_difference=" + json.dumps(
            production["candidate4_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"aex_worker_candidate4_sha256={production['candidate4_sha256']}")
        print("aex_worker_candidate4_float_residual_stats=" + json.dumps(
            production["candidate4_float_residual_stats"], sort_keys=True, separators=(",", ":")))
        print(f"aex_worker_candidate4_residual_classification={production['candidate4_residual_classification']}")
        print("aex_worker_candidate4_comparison=pass_exact" if production["candidate4_differing_bytes"] == 0
              else "aex_worker_candidate4_comparison=known_red_fail_closed")
        print(f"candidate5_direction_mask_diagnostic_compared_bytes={POLAR_BYTES}")
        print(f"candidate5_direction_mask_diagnostic_differing_bytes={production['candidate5_differing_bytes']}")
        print("candidate5_direction_mask_diagnostic_first_difference=" + json.dumps(
            production["candidate5_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"candidate5_direction_mask_diagnostic_sha256={production['candidate5_sha256']}")
        print("candidate5_direction_mask_diagnostic_channel_differing_float_words=" + json.dumps(
            production["candidate5_float_residual_stats"]["channel_differing_float_words"],
            sort_keys=True, separators=(",", ":")))
        print("candidate5_direction_mask_diagnostic_comparison=pass_exact" if production["candidate5_differing_bytes"] == 0
              else "candidate5_direction_mask_diagnostic_comparison=known_red_fail_closed")
        print(f"candidate6_scalar_plane_diagnostic_compared_bytes={POLAR_BYTES}")
        print(f"candidate6_scalar_plane_diagnostic_differing_bytes={production['candidate6_differing_bytes']}")
        print("candidate6_scalar_plane_diagnostic_first_difference=" + json.dumps(
            production["candidate6_first_difference"], sort_keys=True, separators=(",", ":")))
        print(f"candidate6_scalar_plane_diagnostic_sha256={production['candidate6_sha256']}")
        print("candidate6_scalar_plane_diagnostic_channel_differing_float_words=" + json.dumps(
            production["candidate6_float_residual_stats"]["channel_differing_float_words"],
            sort_keys=True, separators=(",", ":")))
        print("candidate6_scalar_plane_diagnostic_comparison=pass_exact" if production["candidate6_differing_bytes"] == 0
              else "candidate6_scalar_plane_diagnostic_comparison=known_red_fail_closed")
        print(f"production_adapter_compared_bytes={EXPECTED_BYTES}")
        print(f"production_adapter_differing_bytes={production['frame_differing_bytes']}")
        print(f"production_adapter_first_difference={production['frame_first_difference']}")
        print("production_adapter_comparison=pass_exact" if production["frame_differing_bytes"] == 0
              else "production_adapter_comparison=known_red_fail_closed")
        print("ae_exact_claim=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
