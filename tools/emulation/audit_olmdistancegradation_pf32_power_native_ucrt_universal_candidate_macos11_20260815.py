#!/usr/bin/env python3
"""Build and freeze the macOS-11 Universal Distance PF32 Power candidate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE_TOOL = ROOT / "tools/emulation/audit_olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.py"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
FIELD = ROOT / "core/olmdistancegradation_fieldgen.cpp"
PROJECT = ROOT / "mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj"
CLOSURE = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.json"
OLD_REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.json"
OLD_BUNDLE = ROOT / "handoffs/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815/Product/OLMDistanceGradation.plugin"
HANDOFF = ROOT / "handoffs/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815"
BUNDLE = HANDOFF / "Product/OLMDistanceGradation.plugin"
BINARY = BUNDLE / "Contents/MacOS/OLMDistanceGradation"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815.json"
DOC = REPORT.with_suffix(".md")
STATUS = "PASS_DISTANCE_PF32_POWER_FRESH_UNIVERSAL_MACOS11_CANDIDATE_SOURCE_RUNTIME_16_OF_16"
SOURCE_SHA256 = "e2f5020f995b59277ee288f48e74a851fc1c9f6a456678cf0361d00e073dd9a9"
CLOSURE_SHA256 = "5a9072bf9c55089939892a57c6ddd8bbfaf805f6a170dae79803926657d73253"
OLD_BINARY_SHA256 = "d138c75d7dbd4c9ca3643988eebd9d53b7581947b6e22aa0f424de6433e2f206"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_base():
    spec = importlib.util.spec_from_file_location("dg_native_universal_base", BASE_TOOL)
    require(spec is not None and spec.loader is not None, "load base audit")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory() -> list[dict]:
    return [{"path": str(path.relative_to(BUNDLE)), "bytes": path.stat().st_size,
             "mode": stat.S_IMODE(path.stat().st_mode), "sha256": sha(path)}
            for path in sorted(BUNDLE.rglob("*")) if path.is_file()]


def minos(architecture: str) -> str:
    output = subprocess.run(["otool", "-arch", architecture, "-l", str(BINARY)],
                            text=True, capture_output=True, check=True).stdout
    values = re.findall(r"\bminos\s+([0-9.]+)", output)
    require(values == ["11.0"], f"{architecture} minOS")
    return values[0]


def ae_entrypoint_exports(architecture: str) -> list[str]:
    output = subprocess.run(["nm", "-arch", architecture, "-gU", str(BINARY)],
                            text=True, capture_output=True, check=True).stdout
    public = sorted(line.split()[-1] for line in output.splitlines()
                    if line.split() and line.split()[-1] in {"_EffectMain", "_PluginDataEntryFunction2"})
    require(public == ["_EffectMain"], f"{architecture} Distance AE entrypoint contract")
    return public


def build() -> dict:
    require(not HANDOFF.exists(), "refusing to overwrite versioned candidate")
    with tempfile.TemporaryDirectory(prefix="dg-native-macos11-build-") as raw:
        temp = Path(raw)
        command = [
            "xcodebuild", "-project", str(PROJECT), "-target", "OLMDistanceGradation",
            "-configuration", "Debug", "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO",
            "CODE_SIGNING_ALLOWED=NO", "MACOSX_DEPLOYMENT_TARGET=11.0",
            f"CONFIGURATION_BUILD_DIR={HANDOFF / 'Product'}", f"OBJROOT={temp / 'Obj'}",
            f"SYMROOT={temp / 'Sym'}", f"SHARED_PRECOMPS_DIR={temp / 'Precomp'}", "build",
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        require(result.returncode == 0, result.stderr)
    signed = subprocess.run(["codesign", "-s", "-", "--force", "--deep", str(BUNDLE)],
                            text=True, capture_output=True)
    require(signed.returncode == 0, signed.stderr)
    return {
        "configuration": "Debug", "deployment_target_override": "11.0",
        "architectures": ["arm64", "x86_64"], "only_active_arch": False,
        "code_signing_allowed_during_build": False, "postbuild_signature": "adhoc deep",
        "command": [item if not item.startswith(("OBJROOT=", "SYMROOT=", "SHARED_PRECOMPS_DIR="))
                    else item.split("=", 1)[0] + "=<temporary>" for item in command],
    }


def candidate_identity(build_contract: dict) -> dict:
    require(BINARY.is_file(), "candidate binary")
    architectures = subprocess.run(["lipo", "-archs", str(BINARY)], text=True,
                                   capture_output=True, check=True).stdout.split()
    require(architectures == ["x86_64", "arm64"], "Universal architecture order")
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)],
                            text=True, capture_output=True)
    require(verify.returncode == 0, verify.stderr)
    detail = subprocess.run(["codesign", "-dvvv", str(BUNDLE)], text=True,
                            capture_output=True, check=True).stderr
    plist_min = plistlib.loads((BUNDLE / "Contents/Info.plist").read_bytes()).get("LSMinimumSystemVersion")
    require(plist_min == "11.0", "Info.plist minOS")
    return {
        "bundle": str(BUNDLE.relative_to(ROOT)), "binary_sha256": sha(BINARY),
        "binary_bytes": BINARY.stat().st_size, "architectures": architectures,
        "minimum_macos": {"Info.plist": plist_min, "arm64": minos("arm64"),
                          "x86_64": minos("x86_64")},
        "ae_entrypoint_exports": {"arm64": ae_entrypoint_exports("arm64"),
                                  "x86_64": ae_entrypoint_exports("x86_64")},
        "ae_entrypoint_filter": ["_EffectMain", "_PluginDataEntryFunction2"],
        "ae_entrypoint_contract": "Distance PiPL CodeMac binds EffectMain; PluginDataEntryFunction2 is intentionally absent. Other global-defined implementation symbols are out of scope.",
        "strict_codesign": True, "signature": "adhoc",
        "cdhash": re.search(r"CDHash=([0-9a-f]+)", detail).group(1),
        "inventory": inventory(), "build": build_contract,
    }


def generate() -> dict:
    require(sha(SOURCE) == SOURCE_SHA256 and sha(CLOSURE) == CLOSURE_SHA256, "numeric authority drift")
    require(sha(OLD_BUNDLE / "Contents/MacOS/OLMDistanceGradation") == OLD_BINARY_SHA256,
            "superseded candidate identity")
    build_contract = build()
    base = load_base()
    runtime = base.runtime()
    require(set(runtime) == {"arm64", "x86_64"} and
            all(row["raw_exact_cells"] == 8 and len(row["rows"]) == 8 for row in runtime.values()),
            "source runtime closure")
    return {
        "schema": "olmdistancegradation.pf32-power-native-ucrt-universal-macos11-candidate/1",
        "status": STATUS,
        "authorities": {"production_source_sha256": sha(SOURCE), "fieldgen_sha256": sha(FIELD),
                        "closure_sha256": sha(CLOSURE), "base_audit_tool_sha256": sha(BASE_TOOL)},
        "candidate": candidate_identity(build_contract),
        "source_runtime": runtime,
        "summary": {"architectures": 2, "source_runtime_exact_per_arch": 8,
                    "source_runtime_exact_total": 16, "public_contract_passed_per_arch": True},
        "supersedes": {"report": str(OLD_REPORT.relative_to(ROOT)),
                       "bundle": str(OLD_BUNDLE.relative_to(ROOT)),
                       "binary_sha256": OLD_BINARY_SHA256,
                       "reason": "old candidate Info.plist and both LC_BUILD_VERSION commands require macOS 26.2"},
        "scope": {"installed": False, "after_effects_launched": False,
                  "identity_manifest_changed": False, "mediacore_changed": False,
                  "numeric_evidence_changed": False, "candidate_macho_direct_pixel_claim": False},
    }


def refresh() -> dict:
    saved = json.loads(REPORT.read_text())
    require(sha(SOURCE) == SOURCE_SHA256 and sha(CLOSURE) == CLOSURE_SHA256, "numeric authority drift")
    base = load_base()
    runtime = base.runtime()
    saved["candidate"] = candidate_identity(saved["candidate"]["build"])
    saved["source_runtime"] = runtime
    return saved


def validate(value: object, live: bool = True) -> bool:
    if not isinstance(value, dict) or value.get("schema") != \
            "olmdistancegradation.pf32-power-native-ucrt-universal-macos11-candidate/1" or \
            value.get("status") != STATUS:
        return False
    try:
        if value["authorities"] != {"production_source_sha256": sha(SOURCE),
                                    "fieldgen_sha256": sha(FIELD),
                                    "closure_sha256": sha(CLOSURE),
                                    "base_audit_tool_sha256": sha(BASE_TOOL)}:
            return False
        candidate = value["candidate"]
        if candidate["architectures"] != ["x86_64", "arm64"] or \
                candidate["minimum_macos"] != {"Info.plist": "11.0", "arm64": "11.0", "x86_64": "11.0"} or \
                candidate["ae_entrypoint_exports"] != {"arm64": ["_EffectMain"],
                                                       "x86_64": ["_EffectMain"]} or \
                candidate["ae_entrypoint_filter"] != ["_EffectMain", "_PluginDataEntryFunction2"] or \
                "Other global-defined implementation symbols are out of scope" not in candidate["ae_entrypoint_contract"] or \
                candidate["strict_codesign"] is not True or candidate["signature"] != "adhoc":
            return False
        if "MACOSX_DEPLOYMENT_TARGET=11.0" not in candidate["build"]["command"] or \
                candidate["build"]["deployment_target_override"] != "11.0":
            return False
        binary_rows = [row for row in candidate["inventory"]
                       if row["path"] == "Contents/MacOS/OLMDistanceGradation"]
        if len(binary_rows) != 1 or binary_rows[0]["sha256"] != candidate["binary_sha256"] or \
                binary_rows[0]["bytes"] != candidate["binary_bytes"]:
            return False
        if value["summary"] != {"architectures": 2, "source_runtime_exact_per_arch": 8,
                               "source_runtime_exact_total": 16,
                               "public_contract_passed_per_arch": True}:
            return False
        expected = load_base().EXPECTED
        if set(value["source_runtime"]) != {"arm64", "x86_64"}:
            return False
        for architecture in ("arm64", "x86_64"):
            runtime = value["source_runtime"][architecture]
            if runtime["raw_exact_cells"] != 8 or len(runtime["rows"]) != 8 or \
                    runtime["public_marker"] != load_base().MARKER:
                return False
            for row in runtime["rows"]:
                if row["cell"] not in expected or row["raw_sha256"] != expected[row["cell"]] or \
                        row["raw_bytes"] != 2992 or row["native_ucrt_exact"] is not True:
                    return False
        if value["supersedes"]["binary_sha256"] != OLD_BINARY_SHA256 or \
                "macOS 26.2" not in value["supersedes"]["reason"]:
            return False
        if value["scope"] != {"installed": False, "after_effects_launched": False,
                              "identity_manifest_changed": False, "mediacore_changed": False,
                              "numeric_evidence_changed": False,
                              "candidate_macho_direct_pixel_claim": False}:
            return False
        if live:
            if not BINARY.is_file() or candidate["binary_sha256"] != sha(BINARY) or \
                    candidate["binary_bytes"] != BINARY.stat().st_size or \
                    candidate["inventory"] != inventory() or minos("arm64") != "11.0" or \
                    minos("x86_64") != "11.0" or ae_entrypoint_exports("arm64") != ["_EffectMain"] or \
                    ae_entrypoint_exports("x86_64") != ["_EffectMain"]:
                return False
            if subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)],
                              capture_output=True).returncode:
                return False
    except (KeyError, TypeError, OSError, subprocess.SubprocessError):
        return False
    return True


def markdown(value: dict) -> str:
    return (
        "# OLMDistanceGradation PF32 Power Universal macOS 11 candidate\n\n"
        f"Status: **{value['status']}**.\n\n"
        "A fresh isolated Debug build explicitly sets `MACOSX_DEPLOYMENT_TARGET=11.0`. The ad-hoc "
        "signed bundle is strict/deep-valid and contains x86_64 plus arm64 slices; Info.plist and both "
        "LC_BUILD_VERSION commands report 11.0. Within the two AE entrypoints checked, both slices expose "
        "`_EffectMain` and intentionally omit `_PluginDataEntryFunction2`, matching the Distance PiPL "
        "`CodeMac` contract; other global-defined implementation symbols are outside this claim. Separate "
        "per-architecture source-runtime harnesses retain the eight native-UCRT exact cells. The earlier "
        "26.2-minimum candidate is superseded. No install, identity, MediaCore, AE, or numerical evidence "
        "change occurred.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.build:
        value = generate()
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(value))
    elif args.refresh:
        value = refresh()
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    require(validate(value), "macOS 11 candidate validation")
    require(DOC.read_text() == markdown(value), "macOS 11 candidate markdown drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
