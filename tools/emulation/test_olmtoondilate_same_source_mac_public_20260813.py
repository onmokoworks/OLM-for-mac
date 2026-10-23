#!/usr/bin/env python3
"""Build and replay the frozen OLMToonDilate source through public Mac EffectMain.

This is AE-free and install-free.  It builds an isolated arm64 bundle from the
checked-in production source, compiles the durable real-SDK probe, dlopens that
bundle, and fail-closes unless all twelve shared-source cells are byte exact.
"""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
import platform
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROJECT = ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj"
PROBE_SOURCE = ROOT / "tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp"
DEFAULT_OUTPUT = Path("/tmp/olmtoondilate_same_source_mac_public_20260813.json")
FROZEN_SOURCE_SHA256 = "42b47acbc3cd37bcaefdedc1b46f0507ed2e478c5eaab921f645f9055a9c8470"

EXPECTED = {
    "PF8_copy": (7, 5, 41, 0.0, (1, 1), "28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e", "28fcdd1bae528a5ca9b3d0ed04599003b0c244d62c2a49c7c7600cbdd3a0d87e", "55977b5da6f43cae0992525f0d7e66211f224e75be53b134a851a2d2051f3161", "99b58cd7458ed0165bc3dab53da9bacaa28649ca8a249f373bcabf915bc483ce"),
    "PF8_fractional": (9, 7, 49, 2.01, (1, 1), "b0bb2f13a7b1df3715f3166e8c170801f3e547e6261e9af40ceb309b0b74f593", "9e22bace19f7dae26258e99573917c68b7327e6d1ccaf141940be94e2d70e27d", "c27e10edda06ec2cbe0126ac70f213b7aeb4a2ec6d69982a05e63f6d5ee8540d", "537ad02a499463ce116e712bc454e0253d044c7d791951e9cb8dcdd1c0b4f1a4"),
    "PF8_tie_semialpha": (7, 3, 41, 3.0, (1, 1), "3e82a3170b01e243044550f4ec7c73823901e3d9decb21441fe9850d517545ef", "05dd195813a594c4185a488a0433eaca16b8668cd6588f48fb77ca7c0050eb0c", "ef136e5e12cb06b6c3b493c77ce2ac7f5915e712992e52c7b8852a8a47f809e7", "a9906acc873782e9d6681bde00b7ffbfd7061ee2869f4bfb5ffb8da30009b69a"),
    "PF8_high_downsample": (513, 17, 2065, 100.0, (2, 1), "10a8f71efc874ad922ad1784eab5f0eec57a623eeca2742e54ef2de55148c902", "5aeed3ca62bc73ecc24a4fa05fc3db2b9b5ac258de2ce90c98724ea055d4707a", "fcffd0fec6009ea64070a7cde94b38adfff5f969705f17363772c3b700b3df62", "db196c8370e043fbcfbe1eb9854ae497b1d4f6ba5d8503423c2c3696570276a9"),
    "PF16_copy": (7, 5, 69, 0.0, (1, 1), "29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54", "29728fe4ef8dbec47f7fd68da5a9a582b59066038b27add5ebe87071c8f09b54", "f2f202f905bed35dbfdeca426377423fb169b703783c608b6c1ba6cbe5cd1ef2", "fa62fdf9fd1807476bb64367df3ae720a6492dfcc93827928f18849066b22ee3"),
    "PF16_fractional": (9, 7, 85, 2.01, (1, 1), "3bcb46077510265bd25eec45104f439f587bd03495df5edce01c61cecba21037", "b57f15217528ebbe5b1b61415688f3d046c417d39c361a6a07dfda9c24faac59", "25f70cf711916fa57bf1008c12f71231c9deed780f7dcf9357085ac99c1428d9", "56b731797901e14ac4f4e3c396bce16858b02bf3e2431aae8227d70c07720eea"),
    "PF16_tie_semialpha": (7, 3, 69, 3.0, (1, 1), "31af1cb49d73db7b803b95a653d51bf583a00fae9ff78cd98847e35d14bb7cbe", "d52a4cadf64b8177fba642b054fad4fef99e5f769124989f5844d31fde1bccb7", "dc2fd3e8eeadc3ca49790c1a48f7ce2507cac649d70ad21f3f8095c7f6c9566a", "e376c20bc1394849106c1ee935d872d65d907df587a293a215ee43eb828228b5"),
    "PF16_high_downsample": (513, 17, 4117, 100.0, (2, 1), "79653684e48ad270e5ba921be40d938cc15f1017402da54536fd35ff8f3bf002", "ab2480b2e58e3c575b9cacdbe2d483174898d5eab6024a7d170ceadabcf9d036", "93e87fba0b2874842695b4d52ea8011912e548dfe51fd8b4ddf301a3e0167f47", "36c2e106c3d42e4477fc50dad6253fbc5626c7aa59a4ba9a39a2fab0e06d8f8b"),
    "PF32_copy": (7, 5, 125, 0.0, (1, 1), "d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807", "d4bf63076bba553b519d80af8678f0bae141ab2512d2f5ef3139904ef6623807", "629b15ee89f6f55c327abedb838fb8e81454672943094fae65785f9b66ce5e1d", "9aa2d7cf061830744437a6f9a45867673fb8e39aef73261d32e0e9b555b918bd"),
    "PF32_fractional": (9, 7, 157, 2.01, (1, 1), "fef7add0856a28eab2b61dbf3427ab5f799caa6188d65b27d825398ca45d3b96", "b9767fdbd1733f8281566ca003c19514e1b60072e054cda53923f5b85b0c430e", "ea7757583fdcce2188d17ad2acb8545a532061ac92278d9d0810b14c343a596a", "a39fb89a2e383ef934caf59b6e540b30e998abbe3fb39369297fa70c7892efc5"),
    "PF32_tie_semialpha": (7, 3, 125, 3.0, (1, 1), "1c2b046b5ea08eb1aa3ed19b940c3e162ecbfbe5d562ce51b95e3eaa6fe0c0d7", "87de042025825f99d43cd8b7b3441cea78dbc0afcd5410786d7952f2bfc013e6", "e5d59e2e8a313f09e1b95108d9465c37a691f1e7fbffcceffe570f8559dd87be", "d230eb87a8ab6d5e8c1341cd84255556b2ae3646e7cce8a8026246d14fc1da22"),
    "PF32_high_downsample": (513, 17, 8221, 100.0, (2, 1), "ca82e46d2885daaa63de2920207b385573dcc2ede60ec7036bbc5e8bf05c66b0", "162e0f47588045812bdfad5f4a13347d02486fb3c4d6e5ebf4bbff4b97d2755d", "beb71bf781c821f28425b7af3bc05994142f8e4f09fc8a663166650098a5ada2", "a1c9f00a94c733327ccf1a75d38e53128b979d1d76153ccf2b71970b240cf0c2"),
}

CALLBACKS = {
    "pre_checkout": 1,
    "checkout_layer_pixels": 1,
    "checkout_output": 1,
    "optional_checkin_layer_pixels": 0,
    "checkout_param": 1,
    "checkin_param": 1,
    "acquire_world_suite": 1,
    "release_world_suite": 1,
    "get_pixel_format": 2,
}

NEGATIVE_STAGES = {
    # id: (exact PF_Err, ReleaseSuite calls, PF_GetPixelFormat calls)
    "acquire_error": (71, 0, 0),
    "acquire_success_null": (516, 1, 0),
    "get_pixel_format_null": (516, 1, 0),
    "get_input_error": (81, 1, 1),
    "get_output_error": (82, 1, 2),
    "release_error": (83, 1, 2),
    "acquire_throw_pferr": (84, 0, 0),
    "acquire_bad_alloc": (4, 0, 0),
    "acquire_throw_other": (512, 0, 0),
    "release_throw_pferr": (85, 1, 2),
    "release_bad_alloc": (4, 1, 2),
    "release_throw_other": (512, 1, 2),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_checked(command: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"BLOCKED_FAIL_CLOSED: {label} failed rc={result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def validate_cases(raw: dict) -> dict:
    cases = raw.get("cases")
    if raw.get("schema") != "olmtoondilate.same-source-mac-public/1" or not raw.get("all_exact") or not raw.get("positive_all_exact") or not raw.get("world_suite_negatives_all_exact"):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: probe did not report exact schema/result")
    if (not isinstance(cases, list) or len(cases) != 12 or
            [case.get("id") for case in cases] != list(EXPECTED) or
            len({case.get("id") for case in cases}) != 12):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: twelve-cell identity set drifted")

    sha_fields = (
        "input_sha256", "output_sha256", "input_active_sha256", "input_payload_sha256",
        "input_padding_sha256", "output_active_sha256", "expected_active_sha256",
        "output_payload_sha256", "output_padding_sha256", "input_header_sha256_before",
        "input_header_sha256_after", "output_header_sha256_before", "output_header_sha256_after",
    )
    for case in cases:
        case_id = case["id"]
        w, h, rowbytes, radius, downsample, input_sha, output_sha, input_payload, output_payload = EXPECTED[case_id]
        expected_padding_in = hashlib.sha256(bytes([0xA5]) * (13 * h)).hexdigest()
        expected_padding_out = hashlib.sha256(bytes([0xEE]) * (13 * h)).hexdigest()
        pixel_bytes = (rowbytes - 13) // w
        exact = (
            case.get("raw_exact") is True
            and case.get("geometry") == [w, h]
            and case.get("pixel_bytes") == pixel_bytes
            and case.get("rowbytes") == rowbytes
            and case.get("active_bytes") == w * h * pixel_bytes
            and case.get("payload_bytes") == rowbytes * h
            and case.get("padding_bytes_per_row") == 13
            and case.get("guard_bytes_per_side") == 19
            and case.get("input_extent") == [101, 201, 101 + w, 201 + h]
            and case.get("output_extent") == [301, 401, 301 + w, 401 + h]
            and case.get("world_flags") == [0, 0]
            and case.get("origins") == [0, 0, 0, 0]
            and case.get("radius") == radius
            and struct.pack("<d", case.get("radius")).hex() == struct.pack("<d", radius).hex()
            and case.get("downsample_x") == list(downsample)
            and case.get("downsample_y") == [0, 0]
            and case.get("input_sha256") == input_sha
            and case.get("input_active_sha256") == input_sha
            and case.get("output_sha256") == output_sha
            and case.get("output_active_sha256") == output_sha
            and case.get("expected_active_sha256") == output_sha
            and case.get("input_payload_sha256") == input_payload
            and case.get("output_payload_sha256") == output_payload
            and case.get("input_padding_sha256") == expected_padding_in
            and case.get("output_padding_sha256") == expected_padding_out
            and case.get("input_storage_immutable") is True
            and case.get("input_header_immutable") is True
            and case.get("output_header_immutable") is True
            and case.get("input_guards_untouched") is True
            and case.get("output_guards_untouched") is True
            and case.get("output_padding_exact") is True
            and case.get("row0_aligned") is True
            and case.get("callbacks") == CALLBACKS
            and case.get("world_suite_identity_exact") is True
            and case.get("preserve_rgb_requested") is False
            and case.get("pre_render_delete_present") is True
            and case.get("pre_render_rects_exact") is True
            and case.get("pre_render_output_flags") == 1
            and case.get("returns_extra_pixels_exact") is True
            and case.get("input_header_sha256_before") == case.get("input_header_sha256_after")
            and case.get("output_header_sha256_before") == case.get("output_header_sha256_after")
            and all(isinstance(case.get(field), str) and len(case[field]) == 64 for field in sha_fields)
        )
        if not exact:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: exact gates failed for {case_id}")
    negatives = raw.get("world_suite_negatives")
    if (not isinstance(negatives, list) or len(negatives) != 12 or
            [row.get("id") for row in negatives] != list(NEGATIVE_STAGES) or
            len({row.get("id") for row in negatives}) != 12):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: WorldSuite negative identity set drifted")
    for row in negatives:
        expected_error, expected_release, expected_formats = NEGATIVE_STAGES[row["id"]]
        callbacks = row.get("callbacks", {})
        exact = (
            row.get("exact") is True
            and row.get("actual_err") == expected_error
            and row.get("expected_err") == expected_error
            and row.get("input_storage_untouched") is True
            and row.get("output_storage_untouched") is True
            and row.get("input_header_untouched") is True
            and row.get("output_header_untouched") is True
            and row.get("padding_and_guards_untouched") is True
            and row.get("preserve_rgb_false") is True
            and callbacks == {
                "pre_checkout": 1, "checkout_layer_pixels": 1, "checkout_output": 1,
                "optional_checkin_layer_pixels": 0, "checkout_param": 1, "checkin_param": 1,
                "acquire_world_suite": 1, "release_world_suite": expected_release,
                "get_pixel_format": expected_formats,
            }
            and row.get("world_suite_identity_exact") is True
            and row.get("pre_render_lifecycle_exact") is True
            and row.get("pre_render_output_flags") == 1
            and row.get("returns_extra_pixels_exact") is True
        )
        if not exact:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: WorldSuite negative failed for {row['id']}")
    return {"all_12_exact": True, "case_ids_exact": True, "pinned_active_and_payload_hashes_exact": True,
            "padding_exact": True, "world_headers_immutable": True, "input_storage_immutable": True,
            "guards_untouched": True, "row0_alignment_exact": True, "callback_lifecycle_exact": True,
            "preserve_rgb_false_exact": True, "world_suite_lifecycle_exact": True,
            "pre_render_lifecycle_exact": True, "world_suite_12_negatives_exact": True,
            "negative_buffers_headers_padding_guards_untouched": True,
            "returns_extra_pixels_flag_exact_positive_and_negative": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: durable probe requires arm64 macOS")
    if sha256(SOURCE) != FROZEN_SOURCE_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: frozen OLMToonDilate source identity drifted")
    compiler = shutil.which("clang++")
    xcodebuild = shutil.which("xcodebuild")
    xcrun = shutil.which("xcrun")
    if not compiler or not xcodebuild or not xcrun:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: clang++/xcodebuild/xcrun unavailable")
    sdk = run_checked([xcrun, "--show-sdk-path"], label="SDK lookup").stdout.strip()

    with tempfile.TemporaryDirectory(prefix="olmtoondilate_same_source_mac_public_") as tmp:
        temp = Path(tmp)
        product = temp / "Product"
        probe = temp / "probe"
        build_command = [
            xcodebuild, "-project", str(PROJECT), "-target", "OLMToonDilate",
            "-configuration", "Debug", "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES",
            "CODE_SIGNING_ALLOWED=NO", f"CONFIGURATION_BUILD_DIR={product}",
            f"SYMROOT={temp / 'sym'}", f"OBJROOT={temp / 'obj'}",
            f"SHARED_PRECOMPS_DIR={temp / 'precomp'}", "build",
        ]
        run_checked(build_command, label="isolated candidate build")
        binary = product / "OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
        if not binary.is_file():
            raise RuntimeError("BLOCKED_FAIL_CLOSED: isolated candidate binary absent")
        compile_command = [
            _UCRT_CXX, "--compiler", compiler, "-std=c++17", "-O2", "-arch", "arm64", "-isysroot", sdk,
            "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")),
            "-I", str(resolve_asset(ROOT / "Util")), "-I", str(resolve_asset(ROOT / "Resources")),
            str(PROBE_SOURCE), "-o", str(probe),
        ]
        run_checked(compile_command, label="real-SDK probe build")
        candidate_sha = sha256(binary)
        probe_binary_sha = sha256(probe)
        execution = run_checked([str(probe), str(binary)], label="public EffectMain replay")
        raw = json.loads(execution.stdout)
        gates = validate_cases(raw)

    if sha256(SOURCE) != FROZEN_SOURCE_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: production source changed during isolated build/replay")
    report = {
        "status": "PASS_SAME_SOURCE_MAC_PUBLIC_12",
        "schema": "olmtoondilate.same-source-mac-public-report/1",
        "production_source": str(SOURCE.relative_to(ROOT)),
        "production_source_sha256": FROZEN_SOURCE_SHA256,
        "probe_source": str(PROBE_SOURCE.relative_to(ROOT)),
        "probe_source_sha256": sha256(PROBE_SOURCE),
        "candidate_binary_sha256": candidate_sha,
        "probe_binary_sha256": probe_binary_sha,
        "architecture": "arm64",
        "commands": ["PF_Cmd_SMART_PRE_RENDER", "PF_Cmd_SMART_RENDER"],
        "matrix": {
            "depths": [8, 16, 32],
            "families": ["copy", "fractional", "tie_semialpha", "high_downsample"],
            "case_count": 12,
            "source_generator_lineage": "installed dynamic all-depths 20260806 pixel<P>/run_case generator",
        },
        "cases": raw["cases"],
        "world_suite_negatives": raw["world_suite_negatives"],
        "gates": gates,
        "build": {
            "candidate": [
                "xcodebuild", "-project", "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj",
                "-target", "OLMToonDilate", "-configuration", "Debug", "ARCHS=arm64",
                "ONLY_ACTIVE_ARCH=YES", "CODE_SIGNING_ALLOWED=NO",
                "CONFIGURATION_BUILD_DIR=<tmp>/Product", "SYMROOT=<tmp>/sym",
                "OBJROOT=<tmp>/obj", "SHARED_PRECOMPS_DIR=<tmp>/precomp", "build",
            ],
            "probe": [
                _UCRT_CXX, "-std=c++17", "-O2", "-arch", "arm64",
                "-isysroot", "<xcrun --show-sdk-path>", "-I", "Headers", "-I", "Headers/SP",
                "-I", "Util", "-I", "Resources",
                "tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp",
                "-o", "<tmp>/probe",
            ],
        },
        "claim_boundary": "AE-free arm64 Mac public EffectMain replay of a freshly isolated bundle; no install and no real-AE-host claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
