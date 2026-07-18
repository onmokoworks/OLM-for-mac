#!/usr/bin/env python3
"""Compare the case_0009 AEX sin/cos contract with macOS sinf/cosf."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import pefile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
PINNED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
FUNCTION = 0x18001D060
FUNCTION_SIZE = 0x50
FUNCTION_PREFIX = bytes.fromhex("f30f10d0660fdb15048600000f2f152d860000")
FUNCTION_SUFFIX = bytes.fromhex("ca0f14c1c30fc6c1000f580512860000eb90")
ANGLE_COUNT = 1800
QUALITY = 5.0


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError("FAIL CLOSED: " + message)


def validate_aex() -> tuple[bytes, str]:
    if not AEX.is_file():
        fail(f"missing AEX: {AEX}")
    blob = AEX.read_bytes()
    actual_sha = sha256(blob)
    if actual_sha != PINNED_AEX_SHA256:
        fail(f"AEX SHA-256 {actual_sha} != pinned {PINNED_AEX_SHA256}")
    try:
        pe = pefile.PE(data=blob, fast_load=True)
        pe.parse_data_directories()
    except Exception as exc:
        fail(f"invalid PE AEX: {exc}")
    image_base = int(pe.OPTIONAL_HEADER.ImageBase)
    rva = FUNCTION - image_base
    section = next(
        (s for s in pe.sections if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize),
        None,
    )
    if section is None or not (section.Characteristics & 0x20000000):
        fail("FUN_18001d060 is not inside an executable section")
    offset = pe.get_offset_from_rva(rva)
    function_bytes = blob[offset:offset + FUNCTION_SIZE]
    if len(function_bytes) != FUNCTION_SIZE:
        fail(f"function bytes have size {len(function_bytes)}, expected {FUNCTION_SIZE}")
    if function_bytes[:len(FUNCTION_PREFIX)] != FUNCTION_PREFIX:
        fail("FUN_18001d060 prefix identity mismatch")
    if function_bytes[-len(FUNCTION_SUFFIX):] != FUNCTION_SUFFIX:
        fail("FUN_18001d060 suffix/RET identity mismatch")
    return function_bytes, actual_sha


HELPER_SOURCE = r'''
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <string>

static float from_word(std::uint32_t word) {
    float value;
    std::memcpy(&value, &word, sizeof(value));
    return value;
}

static std::uint32_t bits(float value) {
    std::uint32_t word;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    const int count = std::stoi(argv[1]);
    const float step = from_word(static_cast<std::uint32_t>(std::stoul(argv[2], nullptr, 16)));
    for (int index = 0; index < count; ++index) {
        const float theta = static_cast<float>(static_cast<float>(index) * step);
        const float sine = ::sinf(theta);
        const float cosine = ::cosf(theta);
        std::printf("%d %08x %08x\n", index, bits(sine), bits(cosine));
    }
    return 0;
}
'''


def mac_words(step_bits: int) -> list[tuple[int, int]]:
    with tempfile.TemporaryDirectory(prefix="olmradialblur_sincos_") as directory:
        directory_path = Path(directory)
        source = directory_path / "sincos.cpp"
        binary = directory_path / "sincos"
        source.write_text(HELPER_SOURCE, encoding="ascii")
        compile_result = subprocess.run(
            ["clang++", "-std=c++17", "-O2", "-fno-fast-math", str(source), "-o", str(binary)],
            text=True,
            capture_output=True,
            check=False,
        )
        if compile_result.returncode != 0:
            fail(f"macOS sinf/cosf helper compilation failed: {compile_result.stderr.strip()}")
        run_result = subprocess.run(
            [str(binary), str(ANGLE_COUNT), f"{step_bits:08x}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if run_result.returncode != 0:
            fail(f"macOS sinf/cosf helper failed with {run_result.returncode}: {run_result.stderr.strip()}")
    rows = run_result.stdout.splitlines()
    if len(rows) != ANGLE_COUNT:
        fail(f"macOS helper returned {len(rows)} rows, expected {ANGLE_COUNT}")
    result: list[tuple[int, int]] = []
    for expected_index, line in enumerate(rows):
        parts = line.split()
        if len(parts) != 3:
            fail(f"macOS helper row has wrong shape: {line!r}")
        try:
            index, sine, cosine = int(parts[0]), int(parts[1], 16), int(parts[2], 16)
        except ValueError as exc:
            fail(f"macOS helper row is not numeric: {line!r} ({exc})")
        if index != expected_index or sine > 0xFFFFFFFF or cosine > 0xFFFFFFFF:
            fail(f"macOS helper row identity/word error: {line!r}")
        result.append((sine, cosine))
    return result


def main() -> int:
    function_bytes, aex_sha = validate_aex()
    step = f32((1.0 / QUALITY) * 3.141592653589793 / 180.0)
    step_bits = word(step)
    theta_words = [word(f32(float(index) * step)) for index in range(ANGLE_COUNT)]

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    aex_words: list[tuple[int, int]] = []
    for index in range(ANGLE_COUNT):
        theta = struct.unpack("<f", struct.pack("<I", theta_words[index]))[0]
        result = loader.call_function(FUNCTION, float_args={0: (theta, "f")}, max_instructions=1000)
        xmm0 = result.get("xmm0")
        if not isinstance(xmm0, bytes) or len(xmm0) != 16:
            fail(f"AEX function returned malformed XMM0 at angle index {index}")
        aex_words.append(struct.unpack("<2I", xmm0[:8]))
    if len(aex_words) != ANGLE_COUNT:
        fail(f"AEX returned {len(aex_words)} rows, expected {ANGLE_COUNT}")

    mac = mac_words(step_bits)
    mismatches = []
    for index, (aex_pair, mac_pair) in enumerate(zip(aex_words, mac)):
        for lane, (aex_word, mac_word) in enumerate(zip(aex_pair, mac_pair)):
            if aex_word != mac_word:
                mismatches.append({
                    "angle_index": index,
                    "lane": "sin" if lane == 0 else "cos",
                    "aex_word": f"0x{aex_word:08x}",
                    "macos_word": f"0x{mac_word:08x}",
                    "theta_word": f"0x{theta_words[index]:08x}",
                })

    aex_blob = b"".join(struct.pack("<2I", *pair) for pair in aex_words)
    mac_blob = b"".join(struct.pack("<2I", *pair) for pair in mac)
    report = {
        "status": "pass",
        "classification": "diagnostic_sincos_comparison_not_AE_exact",
        "case": "case_0009",
        "angle_count": ANGLE_COUNT,
        "quality": QUALITY,
        "step_rad_f32": step,
        "step_rad_f32_word": f"0x{step_bits:08x}",
        "function": "FUN_18001d060",
        "function_address": hex(FUNCTION),
        "function_size": FUNCTION_SIZE,
        "aex_sha256": aex_sha,
        "function_bytes_sha256": sha256(function_bytes),
        "theta_words_sha256": sha256(b"".join(struct.pack("<I", value) for value in theta_words)),
        "aex_packed_sincos_words_sha256": sha256(aex_blob),
        "macos_sinf_cosf_packed_words_sha256": sha256(mac_blob),
        "word_mismatch_count": len(mismatches),
        "sin_word_mismatch_count": sum(item["lane"] == "sin" for item in mismatches),
        "cos_word_mismatch_count": sum(item["lane"] == "cos" for item in mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "ae_exact_claim": False,
        "note": "AEX identity and function ABI/size passed; macOS sinf/cosf is an independent comparator, not an AE exactness claim.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
