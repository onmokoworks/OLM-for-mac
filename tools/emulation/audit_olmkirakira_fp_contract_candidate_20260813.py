#!/usr/bin/env python3
"""Validate the source-bound Kira FP-contract Universal candidate without AE."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmkirakira_fp_contract_universal_candidate_20260813"
BUNDLE = HANDOFF / "product/OLMKiraKira.plugin"
BINARY = BUNDLE / "Contents/MacOS/OLMKiraKira"
LOG = HANDOFF / "logs/xcodebuild.log"
SOURCE_BEFORE = HANDOFF / "logs/source_before.sha256"
SOURCE_AFTER = HANDOFF / "logs/source_after.sha256"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
HEADER = ROOT / "core/kirakira_highlight.h"
PROJECT = ROOT / "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj"
BASE_GENERATOR = ROOT / "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
BASE_REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
SHIM = ROOT / "tools/emulation/olmkirakira_installed_effectmain_shim_20260813.h"
REPORT = HANDOFF / "build_identity.json"
MARKDOWN = HANDOFF / "README.md"

PINS = {
    "production_source": "8f3ccda261b525f58e9abb6d942986f5f71ce6c67758aa7edfecc50a557f3e8f",
    "highlight_header": "e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390",
    "project": "81b2d4246a5dac6f0d8579cb545a7fd9ab201ee63d42a07ccfe544404aff4e4f",
    "base_generator": "5b3e93d45632c3452e81b0b39f63786c6c146e28e0fb7ed5611a0217ec3ea9f1",
    "base_report": "79af585a04a8a8bf16724cecac049b9c688e5edd12b02b2a52728eeee17c4949",
    "harness": "1623680d7fe2cf6525e0e2893d7c25b6d629accf5fd81318a35fab1e64af01c4",
    "shim": "eccf768d497919c1b875ea10e3c73ec53e35a16af9c4a561303497d25ae8097a",
    "build_log": "aee1c3592f85aa278554aa9e2b3581b9ecdbf73941f08b868d94531e0156219c",
    "candidate_binary": "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18",
}
CELLS_SHA = "112f5c2e11b84bff20ec961f046186e69a9e650e96cb5f1aec3449acfce2565a"
NEGATIVES_SHA = "a13a6b9b3e2372785a36566d4d0eff5aec905ab3b995f2574b384e9464378d28"
REQUESTS_SHA = "c205a7b68cc69db6520b9239e6af4babd54ae66d50fda53101185747b1cd4e68"
STATUS = "PASS_OLMKIRAKIRA_FP_CONTRACT_UNIVERSAL_CANDIDATE_42_765_3_NO_AE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"command failed {args}: {result.stdout}{result.stderr}")
    return result.stdout + result.stderr


def load_base():
    spec = importlib.util.spec_from_file_location("kira_fp_candidate_base", BASE_GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "mode": stat.S_IMODE(path.stat().st_mode),
            "sha256": sha256(path),
        })
    return rows


def minos() -> dict[str, str]:
    text = run("xcrun", "vtool", "-show-build", str(BINARY))
    values = [line.split()[1] for line in text.splitlines() if line.strip().startswith("minos ")]
    if values != ["11.0", "11.0"]:
        raise RuntimeError(f"unexpected slice minimum versions: {values}")
    return {"x86_64": values[0], "arm64": values[1]}


def exports() -> dict[str, list[str]]:
    required = ["_EffectMain", "_PluginDataEntryFunction2"]
    result = {}
    for arch in ("x86_64", "arm64"):
        text = run("nm", "-arch", arch, "-gU", str(BINARY))
        found = sorted(name for name in required if name in text.split())
        if found != required:
            raise RuntimeError(f"missing exports for {arch}: {found}")
        result[arch] = found
    return result


def replay() -> dict[str, Any]:
    base = load_base()
    original_source = base.SOURCE
    original_env = os.environ.get("OLMKIRAKIRA_INSTALLED_BINARY")
    try:
        base.SOURCE = SHIM
        os.environ["OLMKIRAKIRA_INSTALLED_BINARY"] = str(BINARY)
        cells, negatives, requests = base.run_harness()
    finally:
        base.SOURCE = original_source
        if original_env is None:
            os.environ.pop("OLMKIRAKIRA_INSTALLED_BINARY", None)
        else:
            os.environ["OLMKIRAKIRA_INSTALLED_BINARY"] = original_env
    digests = {
        "positive_cells": base.canonical(cells),
        "negative_rows": base.canonical_negatives(negatives),
        "request_controls": base.canonical_controls(requests),
    }
    if digests != {
        "positive_cells": CELLS_SHA,
        "negative_rows": NEGATIVES_SHA,
        "request_controls": REQUESTS_SHA,
    }:
        raise RuntimeError(f"candidate replay digest mismatch: {digests}")
    return {
        "positive_count": len(cells),
        "negative_count": len(negatives),
        "request_control_count": len(requests),
        "digests": digests,
        "all_positive_oracle_classic_smart_exact": True,
        "all_negative_output_untouched_and_input_headers_immutable": True,
    }


def generate() -> dict[str, Any]:
    live = {
        "production_source": sha256(SOURCE),
        "highlight_header": sha256(HEADER),
        "project": sha256(PROJECT),
        "base_generator": sha256(BASE_GENERATOR),
        "base_report": sha256(BASE_REPORT),
        "harness": sha256(HARNESS),
        "shim": sha256(SHIM),
        "build_log": sha256(LOG),
        "candidate_binary": sha256(BINARY),
    }
    if live != PINS:
        raise RuntimeError(f"candidate authority drift: {live}")
    if SOURCE_BEFORE.read_bytes() != SOURCE_AFTER.read_bytes():
        raise RuntimeError("source/header/project changed across build")
    if "BUILD SUCCEEDED" not in LOG.read_text(errors="replace"):
        raise RuntimeError("build log has no success marker")
    archs = run("lipo", "-archs", str(BINARY)).strip().split()
    if archs != ["x86_64", "arm64"]:
        raise RuntimeError(f"unexpected architectures: {archs}")
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(BUNDLE))
    plist = subprocess.check_output(
        ["/usr/libexec/PlistBuddy", "-c", "Print :LSMinimumSystemVersion", str(BUNDLE / "Contents/Info.plist")],
        text=True,
    ).strip()
    if plist != "11.0":
        raise RuntimeError(f"unexpected plist minimum: {plist}")
    return {
        "schema": "olmkirakira.fp-contract-universal-candidate/1",
        "status": STATUS,
        "claim_boundary": "Source-bound Universal minOS11 ad-hoc candidate and AE-free public EffectMain replay only; not installed, native AE, Developer ID, notarization, or arbitrary-product evidence.",
        "authorities": live,
        "bundle_path": str(BUNDLE.relative_to(ROOT)),
        "architectures": archs,
        "minimum_versions": minos(),
        "plist_minimum_version": plist,
        "required_exports": exports(),
        "strict_deep_adhoc_codesign": True,
        "bundle_inventory": inventory(BUNDLE),
        "public_replay": replay(),
        "scope": {
            "installed": False,
            "after_effects_launched": False,
            "native_after_effects": False,
            "developer_id_or_notarization": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {
        "schema", "status", "claim_boundary", "authorities", "bundle_path", "architectures",
        "minimum_versions", "plist_minimum_version", "required_exports",
        "strict_deep_adhoc_codesign", "bundle_inventory", "public_replay", "scope",
    }:
        raise RuntimeError("candidate report schema drift")
    if report["schema"] != "olmkirakira.fp-contract-universal-candidate/1" or report["status"] != STATUS:
        raise RuntimeError("candidate report identity drift")
    if report["authorities"] != PINS or report["architectures"] != ["x86_64", "arm64"]:
        raise RuntimeError("candidate authority/architecture drift")
    if report["minimum_versions"] != {"x86_64": "11.0", "arm64": "11.0"} or report["plist_minimum_version"] != "11.0":
        raise RuntimeError("candidate minimum-version drift")
    if report["required_exports"] != {"x86_64": ["_EffectMain", "_PluginDataEntryFunction2"], "arm64": ["_EffectMain", "_PluginDataEntryFunction2"]}:
        raise RuntimeError("candidate export drift")
    if not report["strict_deep_adhoc_codesign"] or report["bundle_inventory"] != inventory(BUNDLE):
        raise RuntimeError("candidate signature/inventory drift")
    if report["public_replay"] != {
        "positive_count": 42,
        "negative_count": 765,
        "request_control_count": 3,
        "digests": {"positive_cells": CELLS_SHA, "negative_rows": NEGATIVES_SHA, "request_controls": REQUESTS_SHA},
        "all_positive_oracle_classic_smart_exact": True,
        "all_negative_output_untouched_and_input_headers_immutable": True,
    }:
        raise RuntimeError("candidate public replay drift")
    if report["scope"] != {"installed": False, "after_effects_launched": False, "native_after_effects": False, "developer_id_or_notarization": False}:
        raise RuntimeError("candidate scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMKiraKira FP-contract Universal candidate (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        f"Candidate executable `{report['authorities']['candidate_binary']}` is Universal "
        "x86_64+arm64, minOS 11.0 in both slices and Info.plist, exports both public entry "
        "symbols, and passes strict/deep ad-hoc code-sign verification. Its public `EffectMain` "
        "replay is exact for 42 positives, 765 negatives, and three request controls.\n\n"
        "Boundary: candidate only. It is not installed and no After Effects process was launched. "
        "No Developer ID, notarization, native-AE, or unlisted-product claim is made.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    validate(live)
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(live))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("candidate report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("candidate report differs from live candidate")
    print(STATUS)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_FP_CONTRACT_CANDIDATE: {exc}", file=sys.stderr)
        raise
