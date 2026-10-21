#!/usr/bin/env python3
"""Replay the current installed Directional bounded union without launching AE."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPORTED = ROOT / "refs/conformance/olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"
NATURAL = ROOT / "refs/conformance/olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
TYPE3 = ROOT / "refs/conformance/olmdirectionalblur_current_installed_type3_layer_20260814.json"
DUAL_HELPER = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_internal_owner_boundary_20260814.py"
NATURAL_HELPER = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_source_bound_union_20260813.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_complete_bounded_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
PINS = {
    "source_sha256": "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845",
    "installed_binary_sha256": "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de",
    "accepted_identity_sha256": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
    "exported_closure_sha256": "8f0648c585b95fa03473eb315fe57cc4b9f5824ff9d0df84c2f97559411423d9",
    "natural_closure_sha256": "1a98a25bf6bbf4dadb340a122721a26965557c54f849c4881eda20a983e6eba3",
    "type3_installed_closure_sha256": "3cd6700be38699548e95be23eaacd0ba609173e9f9d4aeb46d057ea608fc0387",
}
STATUS = "PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_COMPLETE_BOUNDED_UNION_AE_FREE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if run.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in run.stdout.split())
    return found


def identities() -> dict[str, str]:
    return {
        "source_sha256": sha256(SOURCE),
        "installed_binary_sha256": sha256(INSTALLED),
        "accepted_identity_sha256": sha256(IDENTITY),
        "exported_closure_sha256": sha256(EXPORTED),
        "natural_closure_sha256": sha256(NATURAL),
        "type3_installed_closure_sha256": sha256(TYPE3),
        "dual_runtime_helper_sha256": sha256(DUAL_HELPER),
        "natural_runtime_helper_sha256": sha256(NATURAL_HELPER),
    }


def generate() -> dict[str, Any]:
    ids = identities()
    if {key: ids[key] for key in PINS} != PINS:
        raise RuntimeError(f"Directional current authority drift: {ids}")
    accepted = json.loads(IDENTITY.read_text())
    row = next(item for item in accepted["plugins"] if item["plugin"] == "OLMDirectionalBlur")
    if row.get("sha256") != PINS["installed_binary_sha256"] or not row.get("source_installed_exact"):
        raise RuntimeError("accepted Directional row drift")
    if ae_processes():
        raise RuntimeError("After Effects must remain stopped")

    dual_module = load(DUAL_HELPER, "directional_current_dual_runtime")
    dual = dual_module.installed_runtime()
    if (dual.get("arm64_success"), dual.get("arm64_fail_closed"),
            dual.get("x86_64_success"), dual.get("x86_64_fail_closed")) != (15, 0, 9, 6):
        raise RuntimeError("current installed dual-side boundary drift")

    natural_module = load(NATURAL_HELPER, "directional_current_natural_runtime")
    natural = {arch: natural_module.run_natural(arch) for arch in ("arm64", "x86_64")}
    for arch, value in natural.items():
        if value.get("positive_cell_count") != 15 or value.get("installed_source_mutation_rejects") != 15:
            raise RuntimeError(f"current installed Natural64 drift: {arch}")

    type3 = json.loads(TYPE3.read_text())
    if type3.get("status") != "PASS_CURRENT_INSTALLED_TYPE3_LAYER_BOTH_SLICES_57_OF_57_AE_FREE":
        raise RuntimeError("current installed Type3 status drift")
    for arch in ("arm64", "x86_64"):
        if type3["slices"].get(arch) != {
            "negative": 54, "positive": 3, "total": 57,
            "transcript_sha256": "395c9f84e0aa17e1ca43303b740d7f8734115856b07244c51ac17762d5683058",
        }:
            raise RuntimeError(f"current installed Type3 slice drift: {arch}")

    runtime = {
        "dual_side_exported_boundary": dual,
        "natural64_exact_sources": natural,
        "type3_layer": type3["slices"],
    }
    return {
        "schema": "olmdirectionalblur.current-installed-complete-bounded-union/1",
        "status": STATUS,
        "claim_boundary": (
            "The current installed arm64 slice replays 33 bounded public cells: 15 exported "
            "dual-side cells, 15 Natural64 exact-source cells and three Type3 Layer cells. The "
            "current installed x86_64 slice replays 27 exact cells and fail-closes the six "
            "dual-side cells whose native Windows UCRT expf words remain missing. This is AE-free "
            "installed-Mach-O evidence and does not generalize source, tuple, geometry or host math."
        ),
        "identities": ids,
        "runtime": runtime,
        "runtime_sha256": digest(runtime),
        "summary": {
            "arm64_exact_cells": 33,
            "arm64_fail_closed_cells": 0,
            "x86_64_exact_cells": 27,
            "x86_64_fail_closed_cells": 6,
            "natural64_exact_cells_per_slice": 15,
            "type3_exact_cells_per_slice": 3,
            "missing_native_ucrt_counts": [8, 50, 100],
        },
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_source_tuple_geometry": False,
            "production_or_install_changed": False,
        },
    }


def validate(value: dict[str, Any], *, live: bool = True) -> bool:
    try:
        if live:
            return value == generate()
        if set(value) != {"schema", "status", "claim_boundary", "identities", "runtime", "runtime_sha256", "summary", "after_effects_processes", "scope"}:
            return False
        if value["schema"] != "olmdirectionalblur.current-installed-complete-bounded-union/1" or value["status"] != STATUS:
            return False
        if value["runtime_sha256"] != digest(value["runtime"]):
            return False
        runtime = value["runtime"]
        if set(runtime) != {"dual_side_exported_boundary", "natural64_exact_sources", "type3_layer"}:
            return False
        dual = runtime["dual_side_exported_boundary"]
        if (dual.get("rows"), dual.get("arm64_success"), dual.get("arm64_fail_closed"),
                dual.get("x86_64_success"), dual.get("x86_64_fail_closed"),
                dual.get("source_mutation_rejects")) != (30, 15, 0, 9, 6, 24):
            return False
        natural = runtime["natural64_exact_sources"]
        if set(natural) != {"arm64", "x86_64"}:
            return False
        for architecture in ("arm64", "x86_64"):
            if natural[architecture].get("positive_cell_count") != 15 or natural[architecture].get("installed_source_mutation_rejects") != 15:
                return False
            cells = natural[architecture].get("positive_cells")
            if not isinstance(cells, list) or len(cells) != 6:
                return False
        type3 = runtime["type3_layer"]
        if set(type3) != {"arm64", "x86_64"}:
            return False
        expected_type3 = {"negative": 54, "positive": 3, "total": 57,
                          "transcript_sha256": "395c9f84e0aa17e1ca43303b740d7f8734115856b07244c51ac17762d5683058"}
        if any(type3[architecture] != expected_type3 for architecture in ("arm64", "x86_64")):
            return False
        if value["summary"] != {"arm64_exact_cells": 33, "arm64_fail_closed_cells": 0, "x86_64_exact_cells": 27, "x86_64_fail_closed_cells": 6, "natural64_exact_cells_per_slice": 15, "type3_exact_cells_per_slice": 3, "missing_native_ucrt_counts": [8, 50, 100]}:
            return False
        if value["after_effects_processes"] != [] or value["scope"] != {"installed_arm64": True, "installed_x86_64": True, "native_after_effects": False, "arbitrary_source_tuple_geometry": False, "production_or_install_changed": False}:
            return False
        if {key: value["identities"].get(key) for key in PINS} != PINS:
            return False
        if value["claim_boundary"] != generate_claim():
            return False
        return True
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def generate_claim() -> str:
    return (
        "The current installed arm64 slice replays 33 bounded public cells: 15 exported "
        "dual-side cells, 15 Natural64 exact-source cells and three Type3 Layer cells. The "
        "current installed x86_64 slice replays 27 exact cells and fail-closes the six "
        "dual-side cells whose native Windows UCRT expf words remain missing. This is AE-free "
        "installed-Mach-O evidence and does not generalize source, tuple, geometry or host math."
    )


def markdown(report: dict[str, Any]) -> str:
    return f"""# OLMDirectionalBlur current installed complete bounded union

Status: `{report['status']}`

The current installed arm64 slice replays 33 bounded public cells. Rosetta
x86_64 replays 27 exact cells and deliberately fail-closes the remaining six
until native Windows UCRT `expf` results for counts 8, 50 and 100 are accepted.

This is AE-free installed-Mach-O evidence. No arbitrary input or native-AE
claim is added.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = generate()
    if args.write:
        REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(markdown(current))
    saved = json.loads(REPORT.read_text())
    if saved != current or NOTE.read_text() != markdown(saved):
        raise RuntimeError("persisted Directional complete union drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
