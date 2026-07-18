#!/usr/bin/env python3
"""Probe whether the remaining Zoom eligibility-mask bytes are only trig backend differences."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pefile
from PIL import Image

from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
SOURCE = ROOT / "mac" / "OLMRadialBlur" / "OLMRadialBlur.cpp"
INPUT = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur" / "case_0009_before_effects.png"
CHECKPOINT = Path(
    "/private/tmp/olmradialblur_a9d0_boundary_nway_20260718/"
    "nway_merged_at_normalization_20260718.aexcp"
)
RETAINED_MASK = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/eligibility_mask.u8")

EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_CHECKPOINT_SHA256 = "480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909"
EXPECTED_MASK_SHA256 = "861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7"

FUNCTION = 0x18001D060
FUNCTION_SIZE = 0x50
FUNCTION_PREFIX = bytes.fromhex("f30f10d0660fdb15048600000f2f152d860000")
FUNCTION_SUFFIX = bytes.fromhex("ca0f14c1c30fc6c1000f580512860000eb90")

MAGIC = b"AEXCP64\x00"
VERSION = 1
PREFIX_SIZE = len(MAGIC) + 4 + 8 + 32

WIDTH = 1920
HEIGHT = 1080
POLAR_WIDTH = 1104
POLAR_HEIGHT = 1800
MASK_BYTES = POLAR_WIDTH * POLAR_HEIGHT
PF32_BYTES = WIDTH * HEIGHT * 4 * 4

QUALITY = 5.0
ANGLE_COUNT = 1800
STEP_RAD = struct.unpack("<f", struct.pack("<f", (1.0 / QUALITY) * np.pi / 180.0))[0]
STEP_BITS = struct.unpack("<I", struct.pack("<f", STEP_RAD))[0]
EXPECTED_MASK_COUNTS = {0: 565113, 1: 1422087}
EXPECTED_RIP = 0x180005C9F


def fail(message: str) -> RuntimeError:
    return RuntimeError("FAIL CLOSED: " + message)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def validate_artifact(path: Path, expected_sha256: str) -> None:
    if not path.is_file():
        raise fail(f"missing artifact: {path}")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise fail(f"artifact SHA256 mismatch for {path}: {actual} != {expected_sha256}")


def validate_function_identity() -> dict[str, Any]:
    blob = AEX.read_bytes()
    pe = pefile.PE(data=blob, fast_load=True)
    pe.parse_data_directories()
    image_base = int(pe.OPTIONAL_HEADER.ImageBase)
    rva = FUNCTION - image_base
    section = next(
        (item for item in pe.sections if item.VirtualAddress <= rva < item.VirtualAddress + item.Misc_VirtualSize),
        None,
    )
    if section is None or not (section.Characteristics & 0x20000000):
        raise fail("FUN_18001d060 is not inside an executable section")
    offset = pe.get_offset_from_rva(rva)
    body = blob[offset:offset + FUNCTION_SIZE]
    if len(body) != FUNCTION_SIZE:
        raise fail(f"FUN_18001d060 size mismatch: {len(body)} != {FUNCTION_SIZE}")
    if body[:len(FUNCTION_PREFIX)] != FUNCTION_PREFIX:
        raise fail("FUN_18001d060 prefix identity mismatch")
    if body[-len(FUNCTION_SUFFIX):] != FUNCTION_SUFFIX:
        raise fail("FUN_18001d060 suffix identity mismatch")
    return {
        "aex_sha256": EXPECTED_AEX_SHA256,
        "function": "FUN_18001d060",
        "function_address": hex(FUNCTION),
        "function_size": FUNCTION_SIZE,
        "function_bytes_sha256": sha256_bytes(body),
        "step_rad_f32": STEP_RAD,
        "step_rad_bits": f"0x{STEP_BITS:08x}",
        "angle_count": ANGLE_COUNT,
    }


@dataclass
class Checkpoint:
    header: dict[str, Any]
    regions: dict[str, bytes]

    @classmethod
    def read(cls, path: Path) -> "Checkpoint":
        with path.open("rb") as stream:
            prefix = stream.read(PREFIX_SIZE)
            if len(prefix) != PREFIX_SIZE or prefix[:len(MAGIC)] != MAGIC:
                raise fail(f"invalid checkpoint prefix: {path}")
            version, header_size = struct.unpack("<IQ", prefix[len(MAGIC):len(MAGIC) + 12])
            if version != VERSION or header_size > 64 * 1024 * 1024:
                raise fail("unsupported checkpoint header")
            header_bytes = stream.read(header_size)
            if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
                raise fail("checkpoint header checksum mismatch")
            header = json.loads(header_bytes.decode("ascii"))
            regions: dict[str, bytes] = {}
            for region in header.get("regions", []):
                encoded = stream.read(int(region["compressed_size"]))
                raw = zlib.decompress(encoded)
                if len(raw) != int(region["size"]):
                    raise fail(f"checkpoint region size mismatch: {region['name']}")
                if sha256_bytes(raw) != region["sha256"]:
                    raise fail(f"checkpoint region checksum mismatch: {region['name']}")
                regions[region["name"]] = raw
            if stream.read(1):
                raise fail("checkpoint has trailing data")
        if header.get("format") != "aex-loader-x64-checkpoint":
            raise fail("checkpoint format mismatch")
        if header.get("aex", {}).get("sha256") != EXPECTED_AEX_SHA256:
            raise fail("checkpoint AEX identity mismatch")
        return cls(header=header, regions=regions)

    def read_range(self, address: int, size: int) -> bytes:
        for region in self.header["regions"]:
            base = int(region["address"])
            end = base + int(region["size"])
            if base <= address and address + size <= end:
                raw = self.regions[region["name"]]
                start = address - base
                return raw[start:start + size]
        raise fail(f"unreadable checkpoint range 0x{address:x}+{size}")


def qword(checkpoint: Checkpoint, address: int) -> int:
    return struct.unpack("<Q", checkpoint.read_range(address, 8))[0]


def extract_checkpoint_mask() -> tuple[bytes, dict[str, Any]]:
    checkpoint = Checkpoint.read(CHECKPOINT)
    gp = checkpoint.header["registers"]["gp"]
    rip = int(gp["rip"])
    if rip != EXPECTED_RIP:
        raise fail(f"checkpoint RIP mismatch: 0x{rip:x} != 0x{EXPECTED_RIP:x}")
    rbp = int(gp["rbp"])
    mask_slot = rbp - 0x60
    mask_pointer = qword(checkpoint, mask_slot)
    mask = checkpoint.read_range(mask_pointer, MASK_BYTES)
    digest = sha256_bytes(mask)
    if digest != EXPECTED_MASK_SHA256:
        raise fail(f"checkpoint mask SHA256 mismatch: {digest}")
    counts = {int(value): int(mask.count(value)) for value in sorted(set(mask))}
    if counts != EXPECTED_MASK_COUNTS:
        raise fail(f"checkpoint mask counts mismatch: {counts}")
    return mask, {
        "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
        "rip": hex(rip),
        "rbp": hex(rbp),
        "mask_slot": hex(mask_slot),
        "mask_pointer": hex(mask_pointer),
        "mask_sha256": digest,
        "mask_counts": counts,
    }


def retained_mask_oracle() -> tuple[bytes, dict[str, Any]]:
    retained = RETAINED_MASK.read_bytes()
    if len(retained) != MASK_BYTES:
        raise fail(f"retained mask byte size mismatch: {len(retained)} != {MASK_BYTES}")
    retained_sha = sha256_bytes(retained)
    if retained_sha != EXPECTED_MASK_SHA256:
        raise fail(f"retained mask SHA256 mismatch: {retained_sha}")
    checkpoint_mask, checkpoint_info = extract_checkpoint_mask()
    if retained != checkpoint_mask:
        raise fail("retained mask is not byte-identical to checkpoint RBP-0x60 extraction")
    return retained, {
        "retained_mask_path": str(RETAINED_MASK),
        "retained_mask_sha256": retained_sha,
        "checkpoint": checkpoint_info,
    }


def export_exact_trig_payload() -> tuple[bytes, dict[str, Any]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    payload = bytearray()
    instruction_counts: list[int] = []
    for angle_index in range(ANGLE_COUNT):
        theta = f32(float(angle_index) * STEP_RAD)
        result = loader.call_function(
            FUNCTION,
            float_args={0: (theta, "f")},
            max_instructions=1_000,
        )
        xmm0 = result["xmm0"]
        if not isinstance(xmm0, bytes) or len(xmm0) != 16:
            raise fail(f"malformed XMM0 return at angle index {angle_index}")
        payload.extend(xmm0[:8])
        instruction_counts.append(int(result["instructions"]))
    raw = bytes(payload)
    if len(raw) != ANGLE_COUNT * 8:
        raise fail(f"packed trig payload length mismatch: {len(raw)}")
    return raw, {
        "function": "FUN_18001d060",
        "function_address": hex(FUNCTION),
        "angle_count": ANGLE_COUNT,
        "payload_bytes": len(raw),
        "packed_words_sha256": sha256_bytes(raw),
        "min_instructions": min(instruction_counts),
        "max_instructions": max(instruction_counts),
        "total_instructions": sum(instruction_counts),
        "imports": sorted({entry.name for entry in loader.import_log}),
    }


def build_pf32_input(temp_dir: Path) -> Path:
    rgba = np.asarray(Image.open(INPUT).convert("RGBA"), dtype=np.float32) / np.float32(255.0)
    if rgba.shape != (HEIGHT, WIDTH, 4):
        raise fail(f"unexpected input image shape: {rgba.shape}")
    argb = rgba[:, :, [3, 0, 1, 2]].copy()
    output = temp_dir / "case0009_input_pf32.argb"
    argb.tofile(output)
    if output.stat().st_size != PF32_BYTES:
        raise fail("temporary PF32 input byte size mismatch")
    return output


PROBE_SOURCE = r"""#define OLM_RADIALBLUR_TEST_SEAM 1
#include "__SOURCE__"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace {

struct PackedTrigPair {
    float sin_value = 0.0f;
    float cos_value = 0.0f;
};

static std::vector<char> read_all(const char *path) {
    std::ifstream stream(path, std::ios::binary);
    return std::vector<char>(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

static bool write_all(const char *path, const void *data, size_t size) {
    std::ofstream stream(path, std::ios::binary);
    stream.write(reinterpret_cast<const char *>(data), static_cast<std::streamsize>(size));
    return static_cast<bool>(stream);
}

static bool build_zoom_prefill_mask(
    const std::vector<PF_PixelFloat> &input,
    const std::vector<PackedTrigPair> &aex_trig,
    bool use_aex_trig,
    std::vector<A_u_char> &mask_out)
{
    OLMRadialBlurInfo info{};
    info.blur_type = 1;
    info.center_x = 960.0;
    info.center_y = 540.0;
    info.outer_strength = 1717;
    info.outer_offset_mode = 1;
    info.outer_offset = 0;
    info.outer_edge_fade = 0;
    info.inner_strength = 0;
    info.inner_offset_mode = 1;
    info.inner_offset = 0;
    info.inner_edge_fade = 0;
    info.repeat_border = TRUE;
    info.ratio = 1.0;
    info.angle_deg = 0.0;
    info.quality = 5.0;
    info.brightness_gain = 1.0;
    info.noise_variation = 0.0;
    info.noise_type = 1;
    info.seed = 1;
    info.thickness = 10.0;
    info.comp_width = 1920.0;
    info.comp_height = 1080.0;

    const A_long w = 1920;
    const A_long h = 1080;
    FloatImage src;
    src.width = w;
    src.height = h;
    src.rgba.resize(static_cast<size_t>(w) * static_cast<size_t>(h) * 4);
    for (A_long y = 0; y < h; ++y) {
        for (A_long x = 0; x < w; ++x) {
            const PF_PixelFloat &pixel = input[static_cast<size_t>(y) * static_cast<size_t>(w) + static_cast<size_t>(x)];
            const size_t index = (static_cast<size_t>(y) * static_cast<size_t>(w) + static_cast<size_t>(x)) * 4;
            src.rgba[index + 0] = pixel.red;
            src.rgba[index + 1] = pixel.green;
            src.rgba[index + 2] = pixel.blue;
            src.rgba[index + 3] = pixel.alpha;
        }
    }

    const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : static_cast<PF_FpLong>(w);
    const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : static_cast<PF_FpLong>(h);
    const double cx = info.center_x * (static_cast<double>(w) / comp_w);
    const double cy = info.center_y * (static_cast<double>(h) / comp_h);
    const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
    const double base_angle = info.angle_deg * kPi / 180.0;
    const double quality = info.quality > 0.0 ? info.quality : 5.0;
    const double step_deg = 1.0 / quality;
    const double step_rad = step_deg * kPi / 180.0;
    const A_long angular_count = static_cast<A_long>(360.0 / step_deg);

    const double min_dx = (0.0 <= cx && cx < w) ? 0.0 : std::abs(cx < 0.0 ? cx : cx - w);
    const double min_dy = (0.0 <= cy && cy < h) ? 0.0 : std::abs(cy < 0.0 ? cy : cy - h);
    const double max_dx = (0.0 <= cx && cx < w) ? std::max(cx, static_cast<double>(w) - cx) : (cx < 0.0 ? static_cast<double>(w) - cx : cx);
    const double max_dy = (0.0 <= cy && cy < h) ? std::max(cy, static_cast<double>(h) - cy) : (cy < 0.0 ? static_cast<double>(h) - cy : cy);
    const A_long min_r = std::max<A_long>(0, static_cast<A_long>(std::sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2);
    const A_long max_r = static_cast<A_long>(std::sqrt(max_dx * max_dx + max_dy * max_dy)) + 2;
    const A_long radius_count = max_r - min_r + 1;
    if (angular_count != 1800 || radius_count != 1104) return false;
    if (use_aex_trig && static_cast<A_long>(aex_trig.size()) != angular_count) return false;

    mask_out.assign(static_cast<size_t>(angular_count) * static_cast<size_t>(radius_count), 0);
    const double cos_a = std::cos(base_angle);
    const double sin_a = std::sin(base_angle);
    const float cx_f = static_cast<float>(cx);
    const float cy_f = static_cast<float>(cy);
    const float ratio_f = static_cast<float>(ratio);
    const float step_rad_f = static_cast<float>(step_rad);
    const float cos_a_f = static_cast<float>(cos_a);
    const float sin_a_f = static_cast<float>(sin_a);

    for (A_long ai = 0; ai < angular_count; ++ai) {
        const float theta = RadialF32Mul(static_cast<float>(ai), step_rad_f);
        const float cos_t = use_aex_trig ? aex_trig[static_cast<size_t>(ai)].cos_value : std::cos(theta);
        const float sin_t = use_aex_trig ? aex_trig[static_cast<size_t>(ai)].sin_value : std::sin(theta);
        for (A_long ri = 0; ri < radius_count; ++ri) {
            const float r = static_cast<float>(min_r + ri);
            const float sx0 = RadialF32Mul(r, cos_t);
            const float sy0 = RadialF32Mul(RadialF32Mul(r, sin_t), ratio_f);
            const float sx = RadialF32Add(
                RadialF32Sub(RadialF32Mul(cos_a_f, sx0), RadialF32Mul(sin_a_f, sy0)), cx_f);
            const float sy = RadialF32Add(
                RadialF32Add(RadialF32Mul(sin_a_f, sx0), RadialF32Mul(cos_a_f, sy0)), cy_f);
            const AEXPolarSample sampled = SampleRGBAAEXAlpha(src, sx, sy, info.repeat_border != FALSE);
            mask_out[static_cast<size_t>(ai) * static_cast<size_t>(radius_count) + static_cast<size_t>(ri)] = sampled.eligible;
        }
    }
    return true;
}

}  // namespace

int main(int argc, char **argv) {
    if (argc != 5) {
        std::fprintf(stderr, "usage: %s input_pf32.argb exact_trig_pairs.bin native_mask.u8 aex_mask.u8\n", argv[0]);
        return 2;
    }
    const std::vector<char> input_raw = read_all(argv[1]);
    const std::vector<char> trig_raw = read_all(argv[2]);
    if (input_raw.size() != static_cast<size_t>(1920) * static_cast<size_t>(1080) * 4 * sizeof(float)) {
        std::fprintf(stderr, "invalid input size: %zu\n", input_raw.size());
        return 3;
    }
    if (trig_raw.size() != static_cast<size_t>(1800) * sizeof(PackedTrigPair)) {
        std::fprintf(stderr, "invalid trig size: %zu\n", trig_raw.size());
        return 4;
    }
    std::vector<PF_PixelFloat> input(static_cast<size_t>(1920) * static_cast<size_t>(1080));
    std::memcpy(input.data(), input_raw.data(), input_raw.size());
    std::vector<PackedTrigPair> trig(1800);
    std::memcpy(trig.data(), trig_raw.data(), trig_raw.size());
    std::vector<A_u_char> native_mask;
    std::vector<A_u_char> aex_mask;
    if (!build_zoom_prefill_mask(input, trig, false, native_mask)) return 5;
    if (!build_zoom_prefill_mask(input, trig, true, aex_mask)) return 6;
    if (native_mask.size() != static_cast<size_t>(1800) * static_cast<size_t>(1104)) return 7;
    if (aex_mask.size() != native_mask.size()) return 8;
    if (!write_all(argv[3], native_mask.data(), native_mask.size())) return 9;
    if (!write_all(argv[4], aex_mask.data(), aex_mask.size())) return 10;
    return 0;
}
"""


def compile_and_run_probe(temp_dir: Path, input_pf32: Path, trig_payload: bytes) -> tuple[bytes, bytes, dict[str, Any]]:
    trig_path = temp_dir / "case0009_exact_trig_pairs.bin"
    native_path = temp_dir / "native_mask.u8"
    aex_path = temp_dir / "aex_mask.u8"
    probe_cpp = temp_dir / "probe.cpp"
    probe_bin = temp_dir / "probe"

    trig_path.write_bytes(trig_payload)
    if trig_path.stat().st_size != ANGLE_COUNT * 8:
        raise fail("temporary exact trig payload size mismatch")

    probe_source = PROBE_SOURCE.replace("__SOURCE__", str(SOURCE).replace("\\", "\\\\").replace('"', '\\"'))
    probe_cpp.write_text(probe_source, encoding="utf-8")

    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    compile_cmd = [
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
        str(ROOT / "Headers" / "SP"),
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
    ]
    build = subprocess.run(compile_cmd, cwd=ROOT, text=True, capture_output=True)
    if build.returncode != 0:
        raise fail("arm64 probe compilation failed:\n" + build.stdout + build.stderr)

    run = subprocess.run(
        [str(probe_bin), str(input_pf32), str(trig_path), str(native_path), str(aex_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if run.returncode != 0:
        raise fail(f"arm64 probe failed rc={run.returncode}:\n{run.stdout}{run.stderr}")
    native_mask = native_path.read_bytes()
    aex_mask = aex_path.read_bytes()
    if len(native_mask) != MASK_BYTES or len(aex_mask) != MASK_BYTES:
        raise fail("probe output mask size mismatch")
    return native_mask, aex_mask, {
        "compile_command": compile_cmd,
        "probe_binary": str(probe_bin),
        "native_mask_path": str(native_path),
        "aex_mask_path": str(aex_path),
    }


def mask_counts(raw: bytes) -> dict[str, int]:
    return {
        "0": int(raw.count(0)),
        "1": int(raw.count(1)),
        "other": int(sum(value not in (0, 1) for value in raw)),
    }


def diff_entries(actual: bytes, oracle: bytes) -> list[dict[str, Any]]:
    if len(actual) != len(oracle):
        raise fail(f"diff size mismatch: {len(actual)} != {len(oracle)}")
    differences: list[dict[str, Any]] = []
    for offset, (left, right) in enumerate(zip(actual, oracle)):
        if left == right:
            continue
        angle_index, radius_index = divmod(offset, POLAR_WIDTH)
        differences.append(
            {
                "byte_offset": offset,
                "angle_index": angle_index,
                "radius_index": radius_index,
                "actual": int(left),
                "oracle": int(right),
            }
        )
    return differences


def compare_mask(name: str, actual: bytes, oracle: bytes) -> dict[str, Any]:
    differences = diff_entries(actual, oracle)
    return {
        "name": name,
        "bytes": len(actual),
        "sha256": sha256_bytes(actual),
        "counts": mask_counts(actual),
        "differing_bytes": len(differences),
        "all_differences": differences,
    }


def main() -> int:
    validate_artifact(AEX, EXPECTED_AEX_SHA256)
    validate_artifact(INPUT, EXPECTED_INPUT_SHA256)
    validate_artifact(CHECKPOINT, EXPECTED_CHECKPOINT_SHA256)
    validate_artifact(RETAINED_MASK, EXPECTED_MASK_SHA256)

    function_identity = validate_function_identity()
    retained_mask, retained_info = retained_mask_oracle()
    trig_payload, trig_info = export_exact_trig_payload()

    with tempfile.TemporaryDirectory(prefix="olmradialblur_prefill_sincos_20260718_") as temp:
        temp_dir = Path(temp)
        input_pf32 = build_pf32_input(temp_dir)
        native_mask, aex_mask, probe_info = compile_and_run_probe(temp_dir, input_pf32, trig_payload)

    native_vs_checkpoint = compare_mask("native_trig_prefill_mask", native_mask, retained_mask)
    aex_vs_checkpoint = compare_mask("aex_trig_prefill_mask", aex_mask, retained_mask)
    native_vs_aex = compare_mask("native_vs_aex_mask", native_mask, aex_mask)

    same_offsets = [
        entry["byte_offset"] for entry in native_vs_checkpoint["all_differences"]
    ] == [
        entry["byte_offset"] for entry in native_vs_aex["all_differences"]
    ]
    trig_only = (
        native_vs_checkpoint["differing_bytes"] > 0
        and aex_vs_checkpoint["differing_bytes"] == 0
        and native_vs_aex["differing_bytes"] == native_vs_checkpoint["differing_bytes"]
        and same_offsets
    )

    report = {
        "schema": 1,
        "kind": "olmradialblur_prefill_aex_sincos_candidate_20260718",
        "date": "2026-07-18",
        "status": "pass_local_prefill_mask_probe",
        "scope": "Zoom prefill eligibility mask only; no worker claim and no AE claim",
        "ae_exact_claim": False,
        "input": {
            "path": str(INPUT),
            "sha256": EXPECTED_INPUT_SHA256,
            "size": [WIDTH, HEIGHT],
            "pf32_bytes": PF32_BYTES,
        },
        "function_identity": function_identity,
        "retained_checkpoint_mask": retained_info,
        "exact_trig_payload": trig_info,
        "probe": probe_info,
        "comparisons": {
            "native_vs_retained_checkpoint_mask": native_vs_checkpoint,
            "aex_vs_retained_checkpoint_mask": aex_vs_checkpoint,
            "native_vs_aex_mask": native_vs_aex,
        },
        "conclusion": {
            "remaining_eligibility_bytes_are_solely_trig_backend_differences": trig_only,
            "native_diff_count": native_vs_checkpoint["differing_bytes"],
            "aex_diff_count": aex_vs_checkpoint["differing_bytes"],
            "native_vs_aex_diff_count": native_vs_aex["differing_bytes"],
            "offset_sets_match_between_native_checkpoint_and_native_aex": same_offsets,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
