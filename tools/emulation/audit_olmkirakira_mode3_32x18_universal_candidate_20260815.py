#!/usr/bin/env python3
"""Audit the durable source-bound Kira Mode3 32x18 Universal candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import plistlib
import stat
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmkirakira_mode3_32x18_candidate_20260815"
BUNDLE = HANDOFF / "Product/OLMKiraKira.plugin"
BINARY = BUNDLE / "Contents/MacOS/OLMKiraKira"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
PROJECT = ROOT / "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj"
BASE = ROOT / "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
BASE_REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
MODE3 = ROOT / "tools/emulation/test_olmkirakira_mode3_32x18_public_closure_20260814.py"
MODE3_REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json"
GUARD_REPORT = ROOT / "refs/conformance/olmkirakira_classic_smart_admission_guard_20260812.json"
SHIM = ROOT / "tools/emulation/olmkirakira_installed_effectmain_shim_20260813.h"
REPORT = HANDOFF / "build_identity.json"
DOC = HANDOFF / "README.md"
PINS = {
    "source": "abf826dd450bcf879585ae786222ba5d5212d11dd9b292c6ba23d379014baeab",
    "project": "81b2d4246a5dac6f0d8579cb545a7fd9ab201ee63d42a07ccfe544404aff4e4f",
    "base_report": "a8cf5cd9560c6d54bac960eac426562ad8cc41c76f1b4f1f1a45b6ce1c8c1a93",
    "mode3_report": "bcebea0e40f1c3fce63ba1f3587141f44d111c8410b1316b50cf69c52944de4c",
    "guard_report": "7f35778fb03bff60dae47cd8c2f9be7967308d0b3fc8117b3f97009182a69436",
    "candidate": "d4c9b587d41797259de8627e2d3d5bcf7a376f12fa3c8b99dcd820e0b6d80ae3",
}
STATUS = "PASS_OLMKIRAKIRA_MODE3_32X18_DURABLE_UNIVERSAL_CANDIDATE_NO_INSTALL_NO_AE"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{args}: {result.stdout}{result.stderr}")
    return result.stdout + result.stderr


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        common = {"path": relative, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            rows.append({**common, "kind": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            rows.append({**common, "kind": "directory"})
        elif path.is_file():
            rows.append({**common, "kind": "file", "size": info.st_size, "sha256": sha(path)})
        else:
            raise RuntimeError(f"unsupported bundle inventory node: {path}")
    return rows


def with_candidate(module, callback):
    old_source = module.SOURCE
    old_binary = os.environ.get("OLMKIRAKIRA_INSTALLED_BINARY")
    try:
        module.SOURCE = SHIM
        os.environ["OLMKIRAKIRA_INSTALLED_BINARY"] = str(BINARY)
        return callback(module)
    finally:
        module.SOURCE = old_source
        if old_binary is None:
            os.environ.pop("OLMKIRAKIRA_INSTALLED_BINARY", None)
        else:
            os.environ["OLMKIRAKIRA_INSTALLED_BINARY"] = old_binary


def replay_base() -> dict[str, Any]:
    module = load(BASE, "kira_durable_base")

    def execute(mod):
        cells, negatives, requests = mod.run_harness()
        return {
            "positive_count": len(cells),
            "negative_count": len(negatives),
            "request_count": len(requests),
            "digests": {
                "positive_cells": mod.canonical(cells),
                "negative_rows": mod.canonical_negatives(negatives),
                "request_controls": mod.canonical_controls(requests),
            },
        }

    replay = with_candidate(module, execute)
    expected = {
        "positive_cells": "112f5c2e11b84bff20ec961f046186e69a9e650e96cb5f1aec3449acfce2565a",
        "negative_rows": "a13a6b9b3e2372785a36566d4d0eff5aec905ab3b995f2574b384e9464378d28",
        "request_controls": "c205a7b68cc69db6520b9239e6af4babd54ae66d50fda53101185747b1cd4e68",
    }
    if replay["digests"] != expected:
        raise RuntimeError(f"durable base replay drift: {replay}")
    return replay


def replay_mode3() -> dict[str, Any]:
    module = load(MODE3, "kira_durable_mode3")

    def execute(mod):
        cells, lifecycle, negatives = mod.run_public_harness()
        return {
            "positive_count": len(cells),
            "lifecycle_failure_count": len(lifecycle),
            "negative_count": len(negatives),
            "depths": [cell["depth"] for cell in cells],
            "oracle_sha256": [cell["oracle_sha256"] for cell in cells],
            "smart_sha256": [cell["mac_smart_sha256"] for cell in cells],
            "classic_sha256": [cell["mac_classic_sha256"] for cell in cells],
            "negative_names": sorted(row["name"] for row in negatives),
            "all_failure_outputs_untouched": all(
                row["output_untouched"] for row in lifecycle + negatives
            ),
        }

    replay = with_candidate(module, execute)
    if not (
        replay["positive_count"] == 3
        and replay["lifecycle_failure_count"] == 50
        and replay["negative_count"] == 7
        and replay["depths"] == [8, 16, 32]
        and replay["oracle_sha256"] == replay["smart_sha256"] == replay["classic_sha256"]
        and replay["all_failure_outputs_untouched"]
    ):
        raise RuntimeError(f"durable Mode3 replay drift: {replay}")
    return replay


def generate() -> dict[str, Any]:
    live = {
        "source": sha(SOURCE),
        "project": sha(PROJECT),
        "base_report": sha(BASE_REPORT),
        "mode3_report": sha(MODE3_REPORT),
        "guard_report": sha(GUARD_REPORT),
        "candidate": sha(BINARY),
    }
    if live != PINS:
        raise RuntimeError(f"candidate input drift: {live}")
    guard = json.loads(GUARD_REPORT.read_text(encoding="utf-8"))
    if guard["source_sha256"] != PINS["source"]:
        raise RuntimeError("guard source identity drift")
    if guard["universal_isolated_build"]["binary_sha256"] != PINS["candidate"]:
        raise RuntimeError("durable candidate differs from frozen transient build")

    architectures = run("lipo", "-archs", str(BINARY)).strip().split()
    if architectures != ["x86_64", "arm64"]:
        raise RuntimeError(f"architecture drift: {architectures}")
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(BUNDLE))
    signature = run("codesign", "-dv", "--verbose=4", str(BUNDLE))
    if "Signature=adhoc" not in signature:
        raise RuntimeError("candidate is not ad-hoc signed")
    signature_fields = dict(
        line.split("=", 1) for line in signature.splitlines() if "=" in line
    )
    if signature_fields.get("TeamIdentifier") != "not set":
        raise RuntimeError("unexpected signing team")
    build_versions = run("xcrun", "vtool", "-show-build", str(BINARY))
    minimums = [line.split()[1] for line in build_versions.splitlines()
                if line.strip().startswith("minos ")]
    if minimums != ["11.0", "11.0"]:
        raise RuntimeError(f"minimum OS drift: {minimums}")
    with (BUNDLE / "Contents/Info.plist").open("rb") as stream:
        info_plist = plistlib.load(stream)
    if info_plist.get("LSMinimumSystemVersion") != "11.0":
        raise RuntimeError("Info.plist minimum OS drift")
    exports: dict[str, list[str]] = {}
    for architecture in architectures:
        names = run("nm", "-arch", architecture, "-gU", str(BINARY)).split()
        exports[architecture] = sorted(
            name for name in ("_EffectMain", "_PluginDataEntryFunction2") if name in names
        )
        if exports[architecture] != ["_EffectMain", "_PluginDataEntryFunction2"]:
            raise RuntimeError(f"export drift: {architecture} {exports[architecture]}")

    nodes = inventory(BUNDLE)
    return {
        "schema": "olm.kirakira-mode3-32x18-durable-candidate/1",
        "status": STATUS,
        "authorities": live,
        "bundle": BUNDLE.relative_to(ROOT).as_posix(),
        "architectures": architectures,
        "minimum_versions": {"x86_64": "11.0", "arm64": "11.0", "Info.plist": "11.0"},
        "exports": exports,
        "codesign": {
            "identity": "adhoc",
            "team_identifier": "not set",
            "cdhash": signature_fields["CDHash"],
            "identifier": signature_fields["Identifier"],
            "deep_strict_verify": True,
        },
        "inventory": nodes,
        "inventory_summary": {
            "node_count": len(nodes),
            "file_count": sum(node["kind"] == "file" for node in nodes),
            "directory_count": sum(node["kind"] == "directory" for node in nodes),
            "symlink_count": sum(node["kind"] == "symlink" for node in nodes),
        },
        "frozen_transient_build_match": True,
        "public_replay_5x3": replay_base(),
        "public_replay_mode3_32x18": replay_mode3(),
        "build_contract": {
            "configuration": "Debug",
            "architectures": ["arm64", "x86_64"],
            "only_active_arch": False,
            "code_signing_allowed_during_build": False,
            "deployment_target": "11.0",
            "postbuild_signature": "adhoc deep",
            "build_succeeded": True,
            "command": [
                "xcodebuild", "-project", "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj",
                "-scheme", "OLMKiraKira", "-configuration", "Debug",
                "CONFIGURATION_BUILD_DIR=<handoff>/Product", "ARCHS=arm64 x86_64",
                "ONLY_ACTIVE_ARCH=NO", "CODE_SIGNING_ALLOWED=NO",
                "MACOSX_DEPLOYMENT_TARGET=11.0", "build",
            ],
        },
        "scope": {
            "installed": False,
            "native_ae": False,
            "aggregate_updated": False,
            "release_gate_updated": False,
            "developer_id_or_notarization": False,
        },
    }


def validate(saved: dict[str, Any]) -> None:
    live = generate()
    if saved != live:
        raise RuntimeError("durable candidate identity differs from live bundle")


def document(value: dict[str, Any]) -> str:
    return (
        "# OLMKiraKira Mode3 32x18 durable Universal candidate\n\n"
        f"Status: `{value['status']}`\n\n"
        f"Source: `{PINS['source']}`  \n"
        f"Executable: `{PINS['candidate']}`\n\n"
        "The durable bundle contains x86_64 and arm64 slices, both with macOS 11.0 minimum, "
        "both required AE exports, and a strict/deep-valid ad-hoc signature. The complete bundle "
        "tree is hashed in `build_identity.json`.\n\n"
        "Bundle replay closes the prior 5x3 public matrix (42 positive, 765 negative, 3 request "
        "controls) and the bounded Mode3 32x18 matrix (3 positive, 50 lifecycle failures, 7 "
        "one-away negatives). It was not installed and After Effects was not launched.\n\n"
        "Verify read-only: `python3 tools/emulation/"
        "audit_olmkirakira_mode3_32x18_universal_candidate_20260815.py`\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DOC.write_text(document(live), encoding="utf-8")
    saved = json.loads(REPORT.read_text(encoding="utf-8"))
    validate(saved)
    if DOC.read_text(encoding="utf-8") != document(saved):
        raise RuntimeError("durable candidate README drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
