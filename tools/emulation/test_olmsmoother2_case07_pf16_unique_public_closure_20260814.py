#!/usr/bin/env python3
"""Validate the exact reconstructed PF16 case-07 direct and public Smart relation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402

SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
DIRECT = ROOT / "tools/emulation/olmsmoother2_case07_pf16_reconstructed_direct_harness_20260814.cpp"
PUBLIC = ROOT / "tools/emulation/olmsmoother2_case07_pf16_public_smart_harness_20260814.cpp"
NO_EFFECT = ROOT / "refs/conformance/fixtures/olmsmoother2_case07_16bpc_ae_exact_20260727/windows_no_effect.exr.gz"
EFFECT = ROOT / "refs/conformance/fixtures/olmsmoother2_case07_16bpc_ae_exact_20260727/windows_effect_on.exr.gz"
ATTESTATION = ROOT / "refs/conformance/olmsmoother2_case07_16bpc_mac_ae_exact_20260727.json"
DECODE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_decode_lut_10000.h"
INVERSE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_encode_lut_10000.h"
REPORT = ROOT / "refs/conformance/olmsmoother2_case07_pf16_unique_public_closure_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

EXPECTED = {
    "source": "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
    "direct_harness": "ce9fba4631ffa03cc44f6c7c297bd9eeae15ec0d43cc18adfb428e9e1c19c28d",
    "public_harness": "5877f576aaf927a5c34e504657a32f4900fc84bb327fc0834378e1207f7e671e",
    "no_effect_gzip": "c617c3f2a6163a4c4b184eb56f857e9a2ffc220265cc9b4327cb1b259a691472",
    "effect_gzip": "9ba8451f91fe64a8825474a9e9b4834fbdac481797b98252ee52251496fb7f4f",
    "attestation": "51d804c5dd165e78f20401ac065278883da9d1d20f83d08361591dc767b54d35",
    "decode_header": "3f42b42800e4ea1542210f4a678e36777d8707132b13c9447213a18f2e9e3ba2",
    "inverse_header": "8fd0f56cea32a719d1576a6d0788d0e3d2823a6cfd627588e9b3e7e9084ac2ac",
}
INPUT_SHA = "c8d5ded0f9da071eb9e14e7bf20300916a3b8b292f081099d25dfc6359bbafa2"
OUTPUT_SHA = "d306573a7efb040eeb8a3eef523af89e86264741a62c93beb98ecc4f3990cb04"
CASE_NAMES = [
    "positive", "source_first", "source_middle", "source_last", "gamma_next",
    "key_color_one", "palette_one", "width_one", "rowbytes_one",
    "input_flags_one", "output_flags_one", "origin_one", "downsample_one",
    "extent_one", "format_one", "alias", "overlap", "layer_error",
    "output_error", "param_checkout_error", "param_checkin_error",
    "world_error", "color_error", "color_wrong_success",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities() -> dict[str, str]:
    return {
        "source": sha256(SOURCE), "direct_harness": sha256(DIRECT),
        "public_harness": sha256(PUBLIC), "no_effect_gzip": sha256(NO_EFFECT),
        "effect_gzip": sha256(EFFECT), "attestation": sha256(ATTESTATION),
        "decode_header": sha256(DECODE), "inverse_header": sha256(INVERSE),
    }


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def exact_code_map() -> dict[int, int]:
    result: dict[int, int] = {}
    for code in range(32769):
        word = f32_bits(code / 32768.0)
        if word in result:
            raise ValueError("PF16 code/32768 mapping is not injective")
        result[word] = code
    if len(result) != 32769:
        raise ValueError("PF16 code map size drift")
    return result


def planes_from_gzip(path: Path, directory: Path) -> tuple[dict[str, bytes], int, int]:
    raw = gzip.decompress(path.read_bytes())
    exr = directory / (path.stem + ".exr")
    exr.write_bytes(raw)
    return read_planes(exr)


def reconstruct_input(directory: Path) -> tuple[Path, dict[str, object]]:
    planes, width, height = planes_from_gzip(NO_EFFECT, directory)
    if (width, height) != (1920, 1080):
        raise ValueError("no-effect dimensions drift")
    words = {name: struct.unpack(f"<{len(data)//4}I", data)
             for name, data in planes.items()}
    code_map = exact_code_map()
    output = bytearray(width * height * 8)
    distinct: dict[str, int] = {}
    for name in "ARGB":
        distinct[name] = len(set(words[name]))
    for index in range(width * height):
        struct.pack_into("<4H", output, index * 8,
                         *(code_map[words[name][index]] for name in "ARGB"))
    raw = directory / "input_argb16.raw"
    raw.write_bytes(output)
    if hashlib.sha256(output).hexdigest() != INPUT_SHA:
        raise ValueError("reconstructed PF16 input drift")
    return raw, {
        "dimensions": [width, height], "word_count": width * height * 4,
        "all_words_have_exact_code_over_32768": True,
        "all_preimages_unique_over_codes_0_through_32768": True,
        "distinct_float_words_by_channel": distinct,
        "reconstructed_argb16_sha256": INPUT_SHA,
    }


def compile_direct(directory: Path, input_path: Path) -> tuple[Path, dict[str, str]]:
    binary = directory / "direct"
    output = directory / "direct_argb16.raw"
    command = ["clang++", "-std=c++17", "-O2", "-I", "cli/OLMSmoother2/shim",
               "-I", "mac/OLMSmoother2/Mac", str(DIRECT), "-o", str(binary)]
    subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    run = subprocess.run([str(binary), str(input_path), str(output)], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    fields = dict(line.split(" ", 1) for line in run.stdout.splitlines())
    expected = {"INPUT_SHA256": INPUT_SHA, "OUTPUT_SHA256": OUTPUT_SHA,
                "BYTES": "16588800"}
    if fields != expected or sha256(output) != OUTPUT_SHA:
        raise ValueError("direct PF16 transcript drift")
    return output, fields


def compare_effect(directory: Path, direct: Path) -> dict[str, object]:
    planes, width, height = planes_from_gzip(EFFECT, directory)
    data = direct.read_bytes()
    mismatches = {name: 0 for name in "ARGB"}
    for index in range(width * height):
        codes = struct.unpack_from("<4H", data, index * 8)
        for channel, code in zip("ARGB", codes):
            expected = struct.unpack_from("<I", planes[channel], index * 4)[0]
            if f32_bits(code / 32768.0) != expected:
                mismatches[channel] += 1
    if any(mismatches.values()):
        raise ValueError("direct PF16 output does not present exactly in effect EXR")
    return {"word_count": width * height * 4, "mismatches_by_channel": mismatches,
            "max_raw_u32_delta": 0, "presentation": "each ARGB16 code / 32768 as float32"}


def run_public(directory: Path, input_path: Path) -> tuple[list[dict[str, object]], str]:
    binary = directory / "public"
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                         text=True, check=True).stdout.strip()
    command = [
        "clang++", "-std=c++17", "-arch", "arm64", "-O2",
        "-Wno-pragma-pack", "-Wno-deprecated-declarations", "-isysroot", sdk,
        "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", "-Imac/OLMSmoother2",
        str(PUBLIC), "mac/OLMSmoother2/OLMSmoother2_Strings.cpp",
        "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp",
        "-framework", "Cocoa", "-o", str(binary),
    ]
    subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    run = subprocess.run([str(binary), str(input_path)], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    rows = []
    for line in run.stdout.splitlines():
        if line.startswith("CASE "):
            fields = line.split()
            rows.append({"name": fields[1], "pass": fields[2] == "pass=1",
                         "err": int(fields[3].split("=", 1)[1])})
    if [row["name"] for row in rows] != CASE_NAMES or not all(row["pass"] for row in rows):
        raise ValueError("public PF16 case transcript drift")
    if run.stdout.splitlines()[-1] != "SUMMARY pass=24 total=24":
        raise ValueError("public PF16 summary drift")
    return rows, hashlib.sha256(run.stdout.encode()).hexdigest()


def build_report() -> dict[str, object]:
    if identities() != EXPECTED:
        raise ValueError("identity drift")
    attestation = json.loads(ATTESTATION.read_text())
    if attestation.get("status") != "ae_exact" or not attestation.get("ae_exact_claim"):
        raise ValueError("historical AE attestation drift")
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-case07-pf16-") as name:
        directory = Path(name)
        input_path, reconstruction = reconstruct_input(directory)
        direct, direct_transcript = compile_direct(directory, input_path)
        presentation = compare_effect(directory, direct)
        cases, public_transcript = run_public(directory, input_path)
    return {
        "schema": "olmsmoother2.case07-pf16-unique-public/1",
        "status": "PASS_EXACT_PF16_RECONSTRUCTION_DIRECT_PRESENTATION_AND_PUBLIC_SMART",
        "identities": EXPECTED,
        "contract": {
            "dimensions": [1920, 1080], "depth": 16, "rowbytes": 15360,
            "input_active_sha256": INPUT_SHA, "direct_output_sha256": OUTPUT_SHA,
            "gamma_value_binary64": "3ff451eb80000000",
            "positive_count": 1, "negative_count": 23,
        },
        "input_reconstruction": reconstruction,
        "current_source_direct": direct_transcript,
        "windows_effect_on_relation": presentation,
        "public_cases": cases,
        "public_transcript_sha256": public_transcript,
        "claims_not_made": [
            "No arbitrary source, tuple, geometry, depth, or PF16 case claim",
            "No native Windows output-world memory capture",
            "No After Effects launch, installed-binary, or release claim",
        ],
    }


def validate(data: dict[str, object], live: bool = True) -> bool:
    try:
        if set(data) != {"schema", "status", "identities", "contract",
                         "input_reconstruction", "current_source_direct",
                         "windows_effect_on_relation", "public_cases",
                         "public_transcript_sha256", "claims_not_made"}:
            return False
        if data["schema"] != "olmsmoother2.case07-pf16-unique-public/1": return False
        if data["status"] != "PASS_EXACT_PF16_RECONSTRUCTION_DIRECT_PRESENTATION_AND_PUBLIC_SMART": return False
        if data["identities"] != EXPECTED or (live and identities() != EXPECTED): return False
        contract = data["contract"]
        if contract != {"dimensions": [1920, 1080], "depth": 16, "rowbytes": 15360,
                         "input_active_sha256": INPUT_SHA, "direct_output_sha256": OUTPUT_SHA,
                         "gamma_value_binary64": "3ff451eb80000000",
                         "positive_count": 1, "negative_count": 23}: return False
        reconstruction = data["input_reconstruction"]
        if set(reconstruction) != {"dimensions", "word_count",
                                   "all_words_have_exact_code_over_32768",
                                   "all_preimages_unique_over_codes_0_through_32768",
                                   "distinct_float_words_by_channel",
                                   "reconstructed_argb16_sha256"}: return False
        if reconstruction != {"dimensions": [1920, 1080], "word_count": 8294400,
                               "all_words_have_exact_code_over_32768": True,
                               "all_preimages_unique_over_codes_0_through_32768": True,
                               "distinct_float_words_by_channel": {"A": 1, "R": 129, "G": 204, "B": 212},
                               "reconstructed_argb16_sha256": INPUT_SHA}: return False
        if data["current_source_direct"] != {"INPUT_SHA256": INPUT_SHA,
                                             "OUTPUT_SHA256": OUTPUT_SHA,
                                             "BYTES": "16588800"}: return False
        if data["windows_effect_on_relation"] != {
            "word_count": 8294400, "mismatches_by_channel": {"A": 0, "R": 0, "G": 0, "B": 0},
            "max_raw_u32_delta": 0, "presentation": "each ARGB16 code / 32768 as float32"}: return False
        rows = data["public_cases"]
        if not isinstance(rows, list) or [row.get("name") for row in rows] != CASE_NAMES: return False
        if any(set(row) != {"name", "pass", "err"} or row["pass"] is not True for row in rows): return False
        if not isinstance(data["public_transcript_sha256"], str) or len(data["public_transcript_sha256"]) != 64: return False
        if data["claims_not_made"] != [
            "No arbitrary source, tuple, geometry, depth, or PF16 case claim",
            "No native Windows output-world memory capture",
            "No After Effects launch, installed-binary, or release claim"]: return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def markdown(data: dict[str, object]) -> str:
    return f"""# OLMSmoother2 case-07 PF16 unique public closure — 2026-08-14

- Status: `{data['status']}`
- Input: exact inverse of the Windows no-effect FLOAT EXR, `{INPUT_SHA}`.
- Direct current-source output: `{OUTPUT_SHA}`.
- Windows effect-on relation: all 8,294,400 ARGB float words equal `PF16 code / 32768`.
- Real-SDK public Smart: 1 positive plus 23 fail-closed safety negatives pass.
- Boundary: no native output-world capture, arbitrary tuple/source, install, or AE-launch claim.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        data = build_report()
        REPORT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(data))
    if not REPORT.exists():
        print("FAIL report missing")
        return 1
    data = json.loads(REPORT.read_text())
    ok = validate(data, live=True)
    print("PASS_OLMSMOOTHER2_CASE07_PF16_UNIQUE_PUBLIC" if ok else "FAIL_OLMSMOOTHER2_CASE07_PF16_UNIQUE_PUBLIC")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
