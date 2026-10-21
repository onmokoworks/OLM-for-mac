#!/usr/bin/env python3
"""Build and audit the non-installed Universal PF32 Power candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
FIELD = ROOT / "core/olmdistancegradation_fieldgen.cpp"
PROJECT = ROOT / "mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj"
DIRECT = ROOT / "tools/emulation/dg_exported_typed_owner_compare_harness_20260811.cpp"
PUBLIC = ROOT / "tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp"
CLOSURE = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.json"
HANDOFF = ROOT / "handoffs/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815"
BUNDLE = HANDOFF / "Product/OLMDistanceGradation.plugin"
BINARY = BUNDLE / "Contents/MacOS/OLMDistanceGradation"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.json"
DOC = REPORT.with_suffix(".md")

EXPECTED = {
    "mode2.bg0": "42d8142e9aa8cc2abe581cfc8ebc1b473d0861a2e3664e617895639d5451f38c",
    "mode2.bg1": "47ec340cbbaa60bbacff42f15030619fa9d3fc543b3baf5f9bf17560d1dda36d",
    "mode3.bg0": "12bdf0c207bff9fb8c0390f848883281b8484802baea72c82f98db96c3176849",
    "mode3.bg1": "dfeb76265a320e6aae3945fdb2aaa76cd9e77f7e63f586046bca744bfad9cb07",
    "mode4.bg0": "849be120ac0c5e4990c8a19135ebfccdb2f6350ffe53cd0bb1a9f6aafb486c2a",
    "mode4.bg1": "0d8860db7bffd87c6737298482eb60d0378b2dc63841d861ee8e174aaee0a81c",
    "mode5.bg0": "40b5d262cdc0ab372036c9d2774fa9400f74daa7895c75c2222a246b01c485a5",
    "mode5.bg1": "fe715e7973fa79d6043cbe86dcfce3205869fb23ac9d69a8d98b288ab20ad6d7",
}
MARKER = (
    "PASS_OLMDISTANCEGRADATION_PUBLIC_SMART_OWNER_CONTRACT positive=17 "
    "mode5_positive=8 power_positive=8 power_negative=7 negative=21 classic_guards=4"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def inventory() -> list[dict]:
    return [{"path": str(path.relative_to(BUNDLE)), "bytes": path.stat().st_size,
             "mode": stat.S_IMODE(path.stat().st_mode), "sha256": sha(path)}
            for path in sorted(BUNDLE.rglob("*")) if path.is_file()]


def fixture() -> bytes:
    data = bytearray()
    for y in range(11):
        for x in range(17):
            transparent = 4 <= x < 13 and 2 <= y < 9
            values = (0.0, 0.0, 0.0, 0.0) if transparent else (
                1.0, (x * 613 + y * 1231) % 256 / 255.0,
                (x * 997 + y * 211) % 256 / 255.0,
                (x * 1499 + y * 307) % 256 / 255.0,
            )
            data += struct.pack("<4f", *values)
    return bytes(data)


def build_candidate() -> dict:
    require(not HANDOFF.exists(), "refusing to overwrite candidate handoff")
    with tempfile.TemporaryDirectory(prefix="dg-native-candidate-build-") as raw:
        temp = Path(raw)
        command = [
            "xcodebuild", "-project", str(PROJECT), "-target", "OLMDistanceGradation",
            "-configuration", "Debug", "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO",
            "CODE_SIGNING_ALLOWED=NO", f"CONFIGURATION_BUILD_DIR={HANDOFF / 'Product'}",
            f"OBJROOT={temp / 'Obj'}", f"SYMROOT={temp / 'Sym'}",
            f"SHARED_PRECOMPS_DIR={temp / 'Precomp'}", "build",
        ]
        run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        require(run.returncode == 0, run.stderr)
    sign = subprocess.run(["codesign", "-s", "-", "--force", "--deep", str(BUNDLE)],
                          text=True, capture_output=True)
    require(sign.returncode == 0, sign.stderr)
    return {"command": [item if not item.startswith(("OBJROOT=", "SYMROOT=", "SHARED_PRECOMPS_DIR="))
                         else item.split("=", 1)[0] + "=<temporary>" for item in command],
            "configuration": "Debug", "code_signing": "ad-hoc after CODE_SIGNING_ALLOWED=NO"}


def runtime() -> dict[str, dict]:
    with tempfile.TemporaryDirectory(prefix="dg-native-universal-runtime-") as raw:
        temp = Path(raw)
        include = ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"
        direct = temp / "direct"
        public = temp / "public"
        for source, output in ((DIRECT, direct), (PUBLIC, public)):
            build = subprocess.run([
                "clang++", "-std=c++17", "-O0", "-arch", "arm64", "-arch", "x86_64",
                "-mmacosx-version-min=11.0", "-I", str(include), str(source), str(FIELD), "-o", str(output),
            ], cwd=ROOT, text=True, capture_output=True)
            require(build.returncode == 0, build.stderr)
        source = temp / "source.raw"
        source.write_bytes(fixture())
        result = {}
        for arch in ("arm64", "x86_64"):
            rows = []
            for mode in range(2, 6):
                for background in (0, 1):
                    cell = f"mode{mode}.bg{background}"
                    output = temp / f"{arch}.{cell}.raw"
                    run = subprocess.run([
                        "arch", f"-{arch}", str(direct), "PF32", str(source), str(output),
                        "power", str(background), str(mode),
                    ], cwd=ROOT, text=True, capture_output=True)
                    require(run.returncode == 0 and sha(output) == EXPECTED[cell], f"{arch} {cell}")
                    rows.append({"cell": cell, "raw_bytes": output.stat().st_size,
                                 "raw_sha256": sha(output), "native_ucrt_exact": True})
            public_run = subprocess.run(["arch", f"-{arch}", str(public)], cwd=ROOT,
                                        text=True, capture_output=True)
            require(public_run.returncode == 0 and MARKER in public_run.stdout, f"public {arch}")
            result[arch] = {"rows": rows, "raw_exact_cells": 8, "public_marker": MARKER}
        return result


def generate(build: bool) -> dict:
    closure = json.loads(CLOSURE.read_text())
    require(closure["status"].endswith("RAW_EXACT_8_OF_8"), "closure status")
    build_result = build_candidate() if build else {"reused_existing_candidate": True}
    require(BINARY.is_file(), "candidate binary absent")
    archs = subprocess.run(["lipo", "-archs", str(BINARY)], text=True,
                           capture_output=True, check=True).stdout.split()
    require(set(archs) == {"arm64", "x86_64"}, "candidate architectures")
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)],
                            text=True, capture_output=True)
    require(verify.returncode == 0, verify.stderr)
    slices = runtime()
    return {
        "schema": "olmdistancegradation.pf32-power-native-ucrt-universal-candidate/1",
        "status": "PASS_NONINSTALLED_UNIVERSAL_IDENTITY_SOURCE_RUNTIME_ARM64_X86_64_POWER8_EXACT",
        "identities": {"production_source_sha256": sha(SOURCE), "fieldgen_sha256": sha(FIELD),
                       "direct_harness_sha256": sha(DIRECT), "public_harness_sha256": sha(PUBLIC),
                       "closure_sha256": sha(CLOSURE), "binary_sha256": sha(BINARY)},
        "candidate": {"bundle": str(BUNDLE.relative_to(ROOT)), "architectures": archs,
                      "strict_codesign": True, "inventory": inventory(), "build": build_result},
        "slices": slices,
        "summary": {"architectures": 2, "source_runtime_raw_exact_cells_per_arch": 8,
                    "source_runtime_raw_exact_cells_total": 16,
                    "source_runtime_public_contract_passed_per_arch": True},
        "scope": {"installed": False, "after_effects_launched": False,
                  "fixed_17x11_pf32_power_only": True, "unlisted_fail_closed": True},
    }


def validate(value: object, live: bool = True) -> bool:
    if not isinstance(value, dict) or value.get("schema") != \
            "olmdistancegradation.pf32-power-native-ucrt-universal-candidate/1" or value.get("status") != \
            "PASS_NONINSTALLED_UNIVERSAL_IDENTITY_SOURCE_RUNTIME_ARM64_X86_64_POWER8_EXACT":
        return False
    try:
        if value["summary"] != {"architectures": 2, "source_runtime_raw_exact_cells_per_arch": 8,
                               "source_runtime_raw_exact_cells_total": 16,
                               "source_runtime_public_contract_passed_per_arch": True}:
            return False
        if set(value["slices"]) != {"arm64", "x86_64"}:
            return False
        for arch in ("arm64", "x86_64"):
            row = value["slices"][arch]
            if row["raw_exact_cells"] != 8 or row["public_marker"] != MARKER or len(row["rows"]) != 8:
                return False
            if any(item["raw_sha256"] != EXPECTED[item["cell"]] or
                   item["raw_bytes"] != 2992 or item["native_ucrt_exact"] is not True
                   for item in row["rows"]):
                return False
        if live:
            expected_identities = {"production_source_sha256": sha(SOURCE),
                                   "fieldgen_sha256": sha(FIELD),
                                   "direct_harness_sha256": sha(DIRECT),
                                   "public_harness_sha256": sha(PUBLIC),
                                   "closure_sha256": sha(CLOSURE),
                                   "binary_sha256": sha(BINARY)}
            if value["identities"] != expected_identities or not BINARY.is_file() or \
                    value["candidate"]["inventory"] != inventory():
                return False
            if subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)],
                              capture_output=True).returncode:
                return False
    except (KeyError, TypeError, OSError):
        return False
    return True


def markdown(value: dict) -> str:
    return (
        "# OLMDistanceGradation PF32 Power Universal candidate\n\n"
        f"Status: **{value['status']}**.\n\n"
        "The isolated, ad-hoc-signed candidate contains arm64 and x86_64 slices built from the pinned "
        "source. Separate architecture-specific source harnesses replay all eight fixed PF32 Power "
        "cells at full native-UCRT RAW identity and pass the public SmartRender lifecycle/input/padding "
        "contract; this is not a direct invocation of the candidate Mach-O. It was not installed and After Effects "
        "was not launched; all unlisted tuples and geometries remain fail-closed.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(args.build)
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    require(validate(value), "candidate evidence validation")
    require(DOC.read_text() == markdown(value), "candidate markdown drift")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
