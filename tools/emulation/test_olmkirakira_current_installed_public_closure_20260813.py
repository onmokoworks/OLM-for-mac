#!/usr/bin/env python3
"""AE-free public Classic/Smart closure for the current installed OLMKiraKira."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE_GENERATOR = ROOT / "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
BASE_REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
SHIM = ROOT / "tools/emulation/olmkirakira_installed_effectmain_shim_20260813.h"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
INSTALL_CLOSURE = ROOT / "refs/conformance/olmkirakira_worldsuite_incremental_install_identity_20260814.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
REPORT = ROOT / "refs/conformance/olmkirakira_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "production_source": "f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2",
    "installed_binary": "edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7",
    "accepted_identity": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
    "install_closure": "b58642cb7f7317718c7f7fd6ddcd3b2ce7312159f26b65ddea4228b8bbd92bed",
    "base_generator": "5b3e93d45632c3452e81b0b39f63786c6c146e28e0fb7ed5611a0217ec3ea9f1",
    "base_report": "22ed602e6ba016a7f0fb5c36a13d74d082d656a66808e3606d330d4ef6fcf5c1",
    "harness": "1623680d7fe2cf6525e0e2893d7c25b6d629accf5fd81318a35fab1e64af01c4",
    "shim": "eccf768d497919c1b875ea10e3c73ec53e35a16af9c4a561303497d25ae8097a",
}

CELLS_SHA = "112f5c2e11b84bff20ec961f046186e69a9e650e96cb5f1aec3449acfce2565a"
NEGATIVES_SHA = "a13a6b9b3e2372785a36566d4d0eff5aec905ab3b995f2574b384e9464378d28"
REQUESTS_SHA = "c205a7b68cc69db6520b9239e6af4babd54ae66d50fda53101185747b1cd4e68"
STATUS = "PASS_OLMKIRAKIRA_CURRENT_INSTALLED_PUBLIC_42_765_3_AE_FREE"
CLAIM = (
    "Both accepted current installed Universal slices of OLMKiraKira EffectMain independently reproduce the "
    "42 bounded Classic/Smart positive cells, 765 fail-closed parameter/world/lifecycle "
    "rows, and three full-request controls per slice from the source-built public closure. The x86_64 route runs under Rosetta. This is "
    "a real-SDK AE-free dlopen replay, not native After Effects execution or an arbitrary "
    "tuple/source/geometry claim."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("kira_public_base_for_installed", BASE_GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_base_for_arch(arch: str):
    if arch == "arm64":
        return load_base()
    if arch != "x86_64":
        raise RuntimeError(f"unsupported architecture: {arch}")
    text = BASE_GENERATOR.read_text()
    needle = 'cmd = [_UCRT_CXX, "-std=c++20",'
    if text.count(needle) != 1:
        raise RuntimeError("base harness architecture anchor drift")
    module = types.ModuleType("kira_public_base_x86_64")
    module.__file__ = str(BASE_GENERATOR)
    exec(compile(text.replace(needle, 'cmd = [_UCRT_CXX, "-arch", "x86_64", "-std=c++20",'), str(BASE_GENERATOR), "exec"), module.__dict__)
    return module


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed: {name}")
        found += [f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit()]
    return found


def authorities() -> dict[str, str]:
    live = {
        "production_source": sha256(SOURCE),
        "installed_binary": sha256(INSTALLED),
        "accepted_identity": sha256(IDENTITY),
        "install_closure": sha256(INSTALL_CLOSURE),
        "base_generator": sha256(BASE_GENERATOR),
        "base_report": sha256(BASE_REPORT),
        "harness": sha256(HARNESS),
        "shim": sha256(SHIM),
    }
    if live != PINS:
        raise RuntimeError(f"authority drift: {live}")
    identity = json.loads(IDENTITY.read_text())
    row = next(item for item in identity["plugins"] if item["plugin"] == "OLMKiraKira")
    if row["sha256"] != PINS["installed_binary"] or not all(
        row[key] for key in ("source_installed_exact", "universal_exact", "codesign_exact")
    ):
        raise RuntimeError("accepted installed Kira identity is not exact")
    if row["installed_bundle_count"] != 1:
        raise RuntimeError("accepted installed Kira bundle count is not one")
    return live


def generate() -> dict[str, Any]:
    pins = authorities()
    if ae_processes():
        raise RuntimeError("After Effects must remain stopped for installed hostless closure")
    base = load_base()
    persisted_base = json.loads(BASE_REPORT.read_text())
    base.validate(persisted_base)
    results = {}
    for arch in ("arm64", "x86_64"):
        runner = load_base_for_arch(arch)
        original_source = runner.SOURCE
        try:
            runner.SOURCE = SHIM
            results[arch] = runner.run_harness()
        finally:
            runner.SOURCE = original_source
    cells, negatives, requests = results["arm64"]
    if results["x86_64"] != results["arm64"]:
        raise RuntimeError("installed Universal slice relations differ")
    cells_sha = base.canonical(cells)
    negatives_sha = base.canonical_negatives(negatives)
    requests_sha = base.canonical_controls(requests)
    if (cells_sha, negatives_sha, requests_sha) != (CELLS_SHA, NEGATIVES_SHA, REQUESTS_SHA):
        raise RuntimeError("installed public replay differs from bounded source closure")
    if cells != persisted_base["positive_cells"] or negatives != persisted_base["negative_rows"] or requests != persisted_base["request_controls"]:
        raise RuntimeError("installed rows are not byte-for-byte semantically identical to base rows")
    return {
        "schema": "olmkirakira.current-installed-public-closure/1",
        "status": STATUS,
        "claim_boundary": CLAIM,
        "authorities": pins,
        "installed_binary_path": str(INSTALLED),
        "after_effects_processes": [],
        "positive_cells": cells,
        "positive_cells_sha256": cells_sha,
        "architecture_relations": {
            arch: {"positive_cells": 42, "negative_rows": 765, "request_controls": 3,
                   "positive_cells_sha256": cells_sha, "negative_rows_sha256": negatives_sha,
                   "request_controls_sha256": requests_sha}
            for arch in ("arm64", "x86_64")
        },
        "negative_relation": {
            "row_count": len(negatives),
            "rows_sha256": negatives_sha,
            "all_output_untouched": all(row["output_untouched"] for row in negatives),
            "all_input_headers_immutable": all(row["input_headers_immutable"] for row in negatives),
        },
        "request_controls": requests,
        "request_controls_sha256": requests_sha,
        "scope": {
            "public_classic_and_smart": True,
            "installed_effectmain_dlopen": True,
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_tuple_source_geometry": False,
            "after_effects_launched": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {
        "schema", "status", "claim_boundary", "authorities", "installed_binary_path",
        "after_effects_processes", "positive_cells", "positive_cells_sha256", "architecture_relations",
        "negative_relation", "request_controls", "request_controls_sha256", "scope",
    }:
        raise RuntimeError("report schema drift")
    if report["schema"] != "olmkirakira.current-installed-public-closure/1" or report["status"] != STATUS or report["claim_boundary"] != CLAIM:
        raise RuntimeError("report identity/claim drift")
    if report["authorities"] != PINS or report["installed_binary_path"] != str(INSTALLED):
        raise RuntimeError("report authority drift")
    if report["after_effects_processes"] != []:
        raise RuntimeError("unexpected AE process claim")
    base = load_base()
    cells = report["positive_cells"]
    requests = report["request_controls"]
    if len(cells) != 42 or report["positive_cells_sha256"] != base.canonical(cells) or report["positive_cells_sha256"] != CELLS_SHA:
        raise RuntimeError("positive cell closure drift")
    if len(requests) != 3 or report["request_controls_sha256"] != base.canonical_controls(requests) or report["request_controls_sha256"] != REQUESTS_SHA:
        raise RuntimeError("request control closure drift")
    if report["negative_relation"] != {
        "row_count": 765,
        "rows_sha256": NEGATIVES_SHA,
        "all_output_untouched": True,
        "all_input_headers_immutable": True,
    }:
        raise RuntimeError("negative relation drift")
    expected_architecture_relations = {
        arch: {"positive_cells": 42, "negative_rows": 765, "request_controls": 3,
               "positive_cells_sha256": CELLS_SHA, "negative_rows_sha256": NEGATIVES_SHA,
               "request_controls_sha256": REQUESTS_SHA}
        for arch in ("arm64", "x86_64")
    }
    if report["architecture_relations"] != expected_architecture_relations:
        raise RuntimeError("architecture relation drift")
    if report["scope"] != {
        "public_classic_and_smart": True,
        "installed_effectmain_dlopen": True,
        "installed_arm64": True,
        "installed_x86_64": True,
        "native_after_effects": False,
        "arbitrary_tuple_source_geometry": False,
        "after_effects_launched": False,
    }:
        raise RuntimeError("scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMKiraKira current installed public closure (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        f"Installed executable: `{report['authorities']['installed_binary']}`. The real-SDK "
        "harness forwards public EffectMain calls through `dlopen`/`dlsym` to that exact "
        "installed Universal Mach-O. On both arm64 and Rosetta x86_64, all 42 bounded PF8/PF16/PF32 Classic/Smart cells match the "
        "source-built oracle; all 765 negative rows and three full-request controls retain "
        "the same canonical relations per slice.\n\n"
        "Boundary: no After Effects process was launched. This does not establish native-AE "
        "execution or admit any unlisted tuple, source, geometry, layout, or callback state.\n"
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
            raise RuntimeError("persisted report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("persisted installed closure differs from live replay")
    print(STATUS)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_CURRENT_INSTALLED_PUBLIC_CLOSURE: {exc}", file=sys.stderr)
        raise
