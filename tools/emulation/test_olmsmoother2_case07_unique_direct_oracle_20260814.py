#!/usr/bin/env python3
"""Prove the unique straight-PF32 preimage of the Windows case-07 EXR."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402

SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
HARNESS = ROOT / "tools/emulation/olmsmoother2_case07_current_source_direct_harness_20260814.cpp"
INPUT = ROOT / "refs/conformance/fixtures/olmsmoother2_case07_pf32_entry_20260727/pf32_input_entry_argb.bin.gz"
EXR = resolve_asset(ROOT / "refs/win_references/20260727_010629__ae26_3_32bpc_smoother2_preserve_rgb_case07/windows_preserve_rgb_effect_on.exr")
WINDOWS = ROOT / "refs/conformance/olmsmoother2_case07_windows_preserve_rgb_reference_20260727.json"
AEX = resolve_asset(ROOT / "plugins_2025/OLMSmoother2.aex")
REPORT = ROOT / "refs/conformance/olmsmoother2_case07_unique_direct_oracle_20260814.json"
NOTE = REPORT.with_suffix(".md")

EXPECTED = {
    "source": "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
    "harness": "9ea4ea615cd25565cb2c6a9a73fd579424c1c9a36e690edc634ce164528f3172",
    "input_gzip": "f29cad40b4f0081fa5f279da0e875198a2970ea2d9c1161db7cc2058acf4044c",
    "input_raw": "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b",
    "windows_exr": "404d2b5732adf9bbbc6aadab4a1f0dd075e4e0f911b29076339f6f0e17479cc0",
    "windows_manifest": "fd65184c63f529c39d5fdbb173077f45c2a969ff66a17e7972c2dbb5dad45ecc",
    "aex": "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7",
    "direct_raw": "31bbdb17ef62802bc7d67fd66e552e5c0fd7d1e5a740d7aca923acb1d15bf65c",
    "final_semantic_argb": "69b563091cfc8586113a85298365e8eaaacee51d78ec6f3857b5fd091f2d80eb",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def u2f(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def f2u(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def compile_and_run(directory: Path) -> tuple[bytes, dict[str, str]]:
    binary = directory / "case07_direct"
    output = directory / "direct.raw"
    build = subprocess.run([
        "clang++", "-std=c++17", "-O2",
        "-I", str(ROOT / "cli/OLMSmoother2/shim"),
        "-I", str(ROOT / "mac/OLMSmoother2/Mac"),
        str(HARNESS), "-lz", "-o", str(binary),
    ], cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        raise ValueError("current-source harness compile failed: " + build.stderr)
    run = subprocess.run([str(binary), str(INPUT), str(output)], cwd=ROOT,
                         capture_output=True, text=True)
    if run.returncode:
        raise ValueError("current-source harness failed: " + run.stderr)
    fields: dict[str, str] = {}
    for line in run.stdout.splitlines():
        key, value = line.split(" ", 1)
        fields[key] = value
    if fields != {
        "OUTPUT_SHA256": EXPECTED["direct_raw"],
        "INPUT_SHA256": EXPECTED["input_raw"],
        "BYTES": "33177600",
    }:
        raise ValueError("current-source transcript drift")
    direct = output.read_bytes()
    if len(direct) != 33177600 or hashlib.sha256(direct).hexdigest() != EXPECTED["direct_raw"]:
        raise ValueError("current-source direct raw drift")
    return direct, fields


def prove_unique_preimage(direct: bytes) -> dict[str, object]:
    planes, width, height = read_planes(EXR)
    if (width, height) != (1920, 1080):
        raise ValueError("Windows EXR dimensions")
    pixels = width * height
    semantic = bytearray(len(direct))
    alpha_counts: dict[str, int] = {}
    alpha_mismatches = 0
    transform_mismatches = 0
    inverse_mismatches = 0
    changed_rgb_words = 0
    ambiguous_words = 0
    nonfinite_or_negative_direct = 0
    for index in range(pixels):
        base = index * 16
        alpha_bits = struct.unpack_from("<I", direct, base)[0]
        alpha = u2f(alpha_bits)
        expected_alpha = struct.unpack_from("<I", planes["A"], index * 4)[0]
        struct.pack_into("<I", semantic, base, expected_alpha)
        alpha_counts[f"0x{alpha_bits:08x}"] = alpha_counts.get(f"0x{alpha_bits:08x}", 0) + 1
        if alpha_bits != expected_alpha:
            alpha_mismatches += 1
        for channel_index, channel in enumerate(("R", "G", "B"), start=1):
            direct_bits = struct.unpack_from("<I", direct, base + channel_index * 4)[0]
            expected_bits = struct.unpack_from("<I", planes[channel], index * 4)[0]
            struct.pack_into("<I", semantic, base + channel_index * 4, expected_bits)
            if direct_bits & 0x80000000 or (direct_bits & 0x7f800000) == 0x7f800000:
                nonfinite_or_negative_direct += 1
                continue
            transformed = f2u(f32(u2f(direct_bits) * alpha))
            if transformed != expected_bits:
                transform_mismatches += 1
            if direct_bits != expected_bits:
                changed_rgb_words += 1
            if f2u(f32(u2f(expected_bits) / alpha)) != direct_bits:
                inverse_mismatches += 1
            neighbors = [1, 0x80000000] if direct_bits == 0 else [direct_bits - 1, direct_bits + 1]
            for neighbor in neighbors:
                if f2u(f32(u2f(neighbor) * alpha)) == expected_bits:
                    ambiguous_words += 1
    semantic_sha = hashlib.sha256(semantic).hexdigest()
    if semantic_sha != EXPECTED["final_semantic_argb"]:
        raise ValueError("Windows semantic ARGB drift")
    if any((alpha_mismatches, transform_mismatches, inverse_mismatches,
            ambiguous_words, nonfinite_or_negative_direct)):
        raise ValueError("unique-preimage proof failed")
    return {
        "dimensions": [width, height],
        "pixel_count": pixels,
        "word_count": len(direct) // 4,
        "rgb_word_count": pixels * 3,
        "alpha_word_count": pixels,
        "alpha_bits_census": dict(sorted(alpha_counts.items())),
        "alpha_mismatches": alpha_mismatches,
        "float32_rgb_times_alpha_mismatches": transform_mismatches,
        "float32_divide_inverse_mismatches": inverse_mismatches,
        "adjacent_float_preimage_collisions": ambiguous_words,
        "negative_or_nonfinite_direct_words": nonfinite_or_negative_direct,
        "direct_vs_final_changed_rgb_words": changed_rgb_words,
        "direct_raw_sha256": hashlib.sha256(direct).hexdigest(),
        "final_semantic_argb_sha256": semantic_sha,
    }


def build_report() -> dict[str, object]:
    live = {
        "source": sha256(SOURCE), "harness": sha256(HARNESS),
        "input_gzip": sha256(INPUT), "windows_exr": sha256(EXR),
        "windows_manifest": sha256(WINDOWS), "aex": sha256(AEX),
    }
    for key, value in live.items():
        if value != EXPECTED[key]:
            raise ValueError(f"identity drift: {key}")
    manifest = json.loads(WINDOWS.read_text())
    if manifest.get("status") != "captured_effect_mismatch" or manifest.get("ae_exact_claim") is not False:
        raise ValueError("historical Windows claim boundary drift")
    if manifest.get("output_module", {}).get("alpha_mode") != "premultiplied":
        raise ValueError("Windows output alpha-mode drift")
    if manifest.get("pf32_input_entry", {}).get("uncompressed_sha256") != EXPECTED["input_raw"]:
        raise ValueError("Windows input-entry identity drift")
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-case07-unique-") as temp:
        direct, transcript = compile_and_run(Path(temp))
        proof = prove_unique_preimage(direct)
    return {
        "schema": "olmsmoother2.case07-unique-direct-oracle/1",
        "status": "PASS_WINDOWS_FINAL_EXR_HAS_UNIQUE_STRAIGHT_PF32_PREIMAGE_MATCHING_CURRENT_SOURCE",
        "case_id": "final_random10_olm_smoother_v2_07",
        "identities": live,
        "current_source_transcript": transcript,
        "proof": proof,
        "oracle_relation": {
            "windows_observed_boundary": "actual AEX effect-on final FLOAT EXR under Premultiplied output module",
            "host_transform": "for each RGB word, round-to-float32(direct * alpha); alpha copied bit-exact",
            "preimage_unique_over_all_words": True,
            "unique_preimage_equals_current_source_direct_output": True,
            "expected_word_correction_used": False,
        },
        "production_policy": {
            "case07_currently_admitted": True,
            "production_changed_by_this_closure": False,
            "next_gate": "closed by the separate real-SDK public Smart safety/admission closure",
        },
        "claims_not_made": [
            "No native direct output-world memory capture",
            "No arbitrary inverse of premultiplication outside this finite fixture",
            "No other source, tuple, geometry or depth",
            "No production admission from this oracle relation alone",
            "No new After Effects execution",
        ],
    }


def validate(report: dict[str, object], *, live: bool = True) -> bool:
    try:
        expected = build_report() if live else json.loads(REPORT.read_text())
        return report == expected
    except (OSError, ValueError, json.JSONDecodeError, struct.error, subprocess.SubprocessError):
        return False


def render_note(report: dict[str, object]) -> str:
    proof = report["proof"]
    return f"""# OLMSmoother2 case-07 unique direct-output oracle

Status: `{report['status']}`

The retained Windows actual-AEX effect-on EXR contains {proof['word_count']:,}
semantic ARGB float32 words. The current source independently emits straight
PF32 SHA `{proof['direct_raw_sha256']}`. Applying the observed output-module
operation, one float32 `RGB *= A` per channel while copying alpha, reproduces
all words with zero mismatch. Float32 division recovers every direct word, and
testing both adjacent float32 values gives
`{proof['adjacent_float_preimage_collisions']}` alternative preimages.

This uniquely recovers the direct straight output for this finite fixture; it
is not a native output-world memory capture. Production admission is governed
by the separate real-SDK public Smart safety closure.
No After Effects process was launched.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        current = build_report()
        if args.write:
            REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(render_note(current))
        persisted = json.loads(REPORT.read_text())
        if persisted != current:
            raise ValueError("persisted unique-oracle closure drift")
    except (OSError, ValueError, json.JSONDecodeError, struct.error) as exc:
        print(f"FAIL_OLMSMOOTHER2_CASE07_UNIQUE_DIRECT_ORACLE: {exc}")
        return 1
    print("PASS_OLMSMOOTHER2_CASE07_UNIQUE_DIRECT_ORACLE_AE_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
