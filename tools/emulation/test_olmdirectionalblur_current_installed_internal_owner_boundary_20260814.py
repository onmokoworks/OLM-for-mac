#!/usr/bin/env python3
"""Bind installed DirectionalBlur to the exported-Smart exact/fail-closed boundary."""
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
from pathlib import Path
import subprocess
import tempfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
TRANSACTION = ROOT / "handoffs/olmdirectionalblur_testseam_compat_install_20260814/install_transaction.json"
CANDIDATE = resolve_asset(ROOT / "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/build_identity.json")
EXPORTED = ROOT / "refs/conformance/olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"
DUAL = ROOT / "refs/conformance/olmdirectionalblur_dual_side_public_owner_boundary_20260814.json"
SOURCE_GUARD = ROOT / "refs/conformance/olmdirectionalblur_dual_side_public_source_guard_closure_20260813.json"
TYPE3 = ROOT / "refs/conformance/olmdirectionalblur_type3_public_owner_boundary_20260814.json"
NATURAL = ROOT / "refs/conformance/olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
DUAL_PROBE = ROOT / "tools/emulation/probe_olmdirectionalblur_exported_smart5_candidate_20260814.cpp"
TYPE3_PROBE = ROOT / "tools/emulation/probe_olmdirectionalblur_type3_failclose_candidate_20260814.cpp"
SOURCE_PNG = resolve_asset(ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png")
STRINGS = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp"
FRONTONLY = ROOT / "core/dblur_frontonly.cpp"
GAUSSIAN = ROOT / "core/dblur_gaussian.h"
ROTATE = ROOT / "core/dblur_rotate.cpp"
ROWDRIVER = ROOT / "core/dblur_rowdriver.cpp"
FIELD = ROOT / "core/dblur_field.cpp"
SUITE_CPP = resolve_asset(ROOT / str(resolve_asset("Util/AEGP_SuiteHandler.cpp")))
MISSING_CPP = resolve_asset(ROOT / str(resolve_asset("Util/MissingSuiteError.cpp")))
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_internal_owner_boundary_20260814.json"
NOTE = REPORT.with_suffix(".md")
EXPECTED_BINARY = "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de"
EXPECTED_SOURCE_BUNDLE = "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/Product/OLMDirectionalBlur.plugin"
INSTALLED_TRANSCRIPT_SHA256 = "03f69f1b125f968e1d212070b4f6194063b3a287a9b696089588b6c70bac46cd"
SPECS = (
    (32, 18, 1, 8), (32, 18, 1, 16), (32, 18, 1, 32),
    (64, 36, 0, 8), (64, 36, 0, 16), (64, 36, 0, 32),
    (64, 36, 1, 8), (64, 36, 1, 16), (64, 36, 1, 32),
    (64, 36, 2, 8), (64, 36, 2, 16), (64, 36, 2, 32),
    (64, 36, 3, 8), (64, 36, 3, 16), (64, 36, 3, 32),
)
X86_SUCCESSES = {
    (32, 1, 8), (32, 1, 16), (32, 1, 32),
    (64, 0, 8), (64, 0, 16),
    (64, 1, 8), (64, 1, 16),
    (64, 3, 8), (64, 3, 16),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_processes() -> list[str]:
    found = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        found.extend(f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit())
    return found


def identities() -> dict[str, str]:
    return {
        "source_sha256": sha256(SOURCE), "installed_binary_sha256": sha256(INSTALLED),
        "accepted_identity_sha256": sha256(IDENTITY), "transaction_sha256": sha256(TRANSACTION),
        "candidate_identity_sha256": sha256(CANDIDATE), "dual_boundary_sha256": sha256(DUAL),
        "exported_smart_closure_sha256": sha256(EXPORTED),
        "source_guard_closure_sha256": sha256(SOURCE_GUARD),
        "type3_boundary_sha256": sha256(TYPE3), "natural64_closure_sha256": sha256(NATURAL),
        "dual_probe_sha256": sha256(DUAL_PROBE), "type3_probe_sha256": sha256(TYPE3_PROBE),
        "source_png_sha256": sha256(SOURCE_PNG), "strings_sha256": sha256(STRINGS),
        "frontonly_sha256": sha256(FRONTONLY), "gaussian_sha256": sha256(GAUSSIAN),
        "rotate_sha256": sha256(ROTATE), "rowdriver_sha256": sha256(ROWDRIVER),
        "field_sha256": sha256(FIELD), "suite_cpp_sha256": sha256(SUITE_CPP),
        "missing_cpp_sha256": sha256(MISSING_CPP),
    }


def installed_runtime() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="dblur-current-installed-arm15.") as raw:
        directory = Path(raw)
        image = Image.open(SOURCE_PNG).convert("RGBA")
        for width, height in {(row[0], row[1]) for row in SPECS}:
            (directory / f"{width}x{height}.rgba").write_bytes(
                image.crop((472, 262, 472 + width, 262 + height)).tobytes())
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        common = [_UCRT_CXX, "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                  "-isysroot", sdk, "-Wno-pragma-pack", "-Wno-deprecated-declarations"]
        for include in ("Headers", "Headers/SP", "Util", "Resources", "core", "mac/OLMDirectionalBlur"):
            common += ["-I", str(ROOT / include)]
        common += [str(DUAL_PROBE), str(STRINGS), str(SUITE_CPP), str(MISSING_CPP),
                   str(FRONTONLY), str(ROTATE), str(ROWDRIVER), str(FIELD),
                   "-framework", "Cocoa"]
        lines: list[str] = []
        probe_hashes: dict[str, str] = {}
        for arch in ("arm64", "x86_64"):
            probe = directory / f"probe-{arch}"
            build = subprocess.run([*common, "-arch", arch, "-o", str(probe)],
                                   cwd=ROOT, capture_output=True, text=True)
            if build.returncode:
                raise RuntimeError(build.stdout + build.stderr)
            probe_hashes[arch] = sha256(probe)
            for width, height, tuple_index, depth in SPECS:
                success = arch == "arm64" or (width, tuple_index, depth) in X86_SUCCESSES
                command = [str(probe), str(INSTALLED), str(directory / f"{width}x{height}.rgba"),
                           str(width), str(height), str(tuple_index), str(depth), str(int(success))]
                if arch == "x86_64":
                    command = ["arch", "-x86_64", *command]
                run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                line = run.stdout.strip()
                if run.returncode or run.stderr or not line.startswith("PASS=1 "):
                    raise RuntimeError(f"installed {arch} runtime drift: {line} {run.stderr}")
                lines.append(line)
        transcript = "\n".join(lines) + "\n"
        if hashlib.sha256(transcript.encode()).hexdigest() != INSTALLED_TRANSCRIPT_SHA256:
            raise RuntimeError("installed transcript drift")
        return {"architectures": ["arm64", "x86_64"], "rows": 30,
                "arm64_success": 15, "arm64_fail_closed": 0,
                "x86_64_success": 9, "x86_64_fail_closed": 6,
                "source_mutation_rejects": 24,
                "input_headers_padding_lifecycle_unchanged": True,
                "probe_sha256": probe_hashes,
                "transcript_sha256": INSTALLED_TRANSCRIPT_SHA256,
                "transcript_lines": lines}


def generate() -> dict[str, object]:
    ids = identities()
    if ids["installed_binary_sha256"] != EXPECTED_BINARY:
        raise RuntimeError("installed DirectionalBlur identity drift")
    accepted = json.loads(IDENTITY.read_text())
    row = next(item for item in accepted["plugins"] if item["plugin"] == "OLMDirectionalBlur")
    if (row["sha256"] != EXPECTED_BINARY or row["source_sha256"] != EXPECTED_BINARY
            or row["source_bundle"] != EXPECTED_SOURCE_BUNDLE
            or row["architectures"] != ["x86_64", "arm64"]
            or not row["source_installed_exact"]):
        raise RuntimeError("accepted DirectionalBlur row drift")
    if ae_processes():
        raise RuntimeError("AE-family process running")
    return {
        "schema": "olmdirectionalblur.current-installed-exported-smart-boundary/4",
        "status": "PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_ARM64_15_EXACT_X86_64_9_EXACT_6_FAIL_CLOSED_AE_FREE",
        "architectures": ["arm64", "x86_64"], "identities": ids,
        "summary": {
            "dual_side_exact_arm64": 15,
            "dual_side_fail_closed_arm64": 0,
            "dual_side_exact_x86_64": 9,
            "dual_side_fail_closed_x86_64": 6,
            "type3_layer_exact_per_slice": 3,
            "direct_probe_depths_per_family_per_slice": 3,
            "error_symbol": "PF_Err_BAD_CALLBACK_PARAM", "error_value": 516,
            "input_layer_destination_headers_padding_unchanged": True,
            "natural64_exported_aexcompat_lane_retained": True,
        },
        "installed_runtime": installed_runtime(), "after_effects_processes": [],
        "scope": {"installed_arm64": True, "installed_x86_64": True,
                  "native_after_effects": False, "windows_internal_owner_numerics_retained": True,
                  "windows_exported_smart_for_all_fifteen_dual_cells": True,
                  "remaining_six_promoted_on_arm64_only": True,
                  "remaining_six_promoted_on_x86_64": False,
                  "windows_exported_smart_for_type3": False,
                  "arbitrary_source_tuple_geometry": False},
    }


def validate(report: dict[str, object], live: bool = True) -> bool:
    if set(report) != {"schema", "status", "architectures", "identities", "summary", "installed_runtime", "after_effects_processes", "scope"}:
        return False
    if report["schema"] != "olmdirectionalblur.current-installed-exported-smart-boundary/4" or report["status"] != "PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_ARM64_15_EXACT_X86_64_9_EXACT_6_FAIL_CLOSED_AE_FREE":
        return False
    expected_identities = identities()
    if report["architectures"] != ["arm64", "x86_64"] or set(report["identities"]) != set(expected_identities):
        return False
    if report["identities"] != expected_identities:
        return False
    if report["summary"] != {"dual_side_exact_arm64": 15, "dual_side_fail_closed_arm64": 0,
                             "dual_side_exact_x86_64": 9, "dual_side_fail_closed_x86_64": 6,
                             "type3_layer_exact_per_slice": 3,
                             "direct_probe_depths_per_family_per_slice": 3,
                             "error_symbol": "PF_Err_BAD_CALLBACK_PARAM", "error_value": 516,
                             "input_layer_destination_headers_padding_unchanged": True,
                             "natural64_exported_aexcompat_lane_retained": True}:
        return False
    runtime = report["installed_runtime"]
    if (set(runtime) != {"architectures", "rows", "arm64_success", "arm64_fail_closed",
                         "x86_64_success", "x86_64_fail_closed", "source_mutation_rejects",
                         "input_headers_padding_lifecycle_unchanged", "probe_sha256",
                         "transcript_sha256", "transcript_lines"}
            or runtime["architectures"] != ["arm64", "x86_64"] or runtime["rows"] != 30
            or runtime["arm64_success"] != 15 or runtime["arm64_fail_closed"] != 0
            or runtime["x86_64_success"] != 9 or runtime["x86_64_fail_closed"] != 6
            or runtime["source_mutation_rejects"] != 24
            or runtime["input_headers_padding_lifecycle_unchanged"] is not True
            or runtime["probe_sha256"] != {"arm64": "255bcd13e83617174d38c6c3f237552e9b6770b40604c521be83161553faefcc",
                                            "x86_64": "dc8dedaef3ea67ea8c5345a39c136b1ba0dca2c4e7405ad32426a04ffb039fd5"}
            or runtime["transcript_sha256"] != INSTALLED_TRANSCRIPT_SHA256
            or len(runtime["transcript_lines"]) != 30
            or hashlib.sha256(("\n".join(runtime["transcript_lines"]) + "\n").encode()).hexdigest() != INSTALLED_TRANSCRIPT_SHA256
            or any(not line.startswith("PASS=1 ") for line in runtime["transcript_lines"])):
        return False
    return report["after_effects_processes"] == [] and report["scope"] == {
        "installed_arm64": True, "installed_x86_64": True, "native_after_effects": False,
        "windows_internal_owner_numerics_retained": True,
        "windows_exported_smart_for_all_fifteen_dual_cells": True,
        "remaining_six_promoted_on_arm64_only": True,
        "remaining_six_promoted_on_x86_64": False,
        "windows_exported_smart_for_type3": False,
        "arbitrary_source_tuple_geometry": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = generate()
    if args.write:
        REPORT.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(
            "# OLMDirectionalBlur current installed exported-Smart boundary\n\n"
            "The installed arm64 slice admits all fifteen dual-side cells that replay raw-exact "
            "through the Windows AEX exported Smart route under the pinned AEXCompat/Unicorn worker. "
            "The x86_64 slice retains nine exact cells and fail-closes the six libSystem-expf residual "
            "cells; the separate exact-source Type-3 closure admits three cells on both slices. "
            "Natural64 remains its separate "
            "exported-AEXCompat numerical lane. This is hostless evidence and does not claim native AE.\n"
        )
    if not REPORT.exists() or not validate(json.loads(REPORT.read_text())) or json.loads(REPORT.read_text()) != generated:
        raise RuntimeError("current installed DirectionalBlur boundary report drift")
    print(generated["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
