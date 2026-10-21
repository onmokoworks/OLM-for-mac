#!/usr/bin/env python3
"""Bind ColorKeep's complete bounded union to the current installed identity."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin/Contents/MacOS/ColorKeep"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
UNION = ROOT / "tools/emulation/test_colorkeep_source_bound_complete_union_candidate_20260813.py"
LEGACY = ROOT / "refs/conformance/colorkeep_public_guard_closure_20260812.json"
COUNT9 = ROOT / "refs/conformance/colorkeep_nine_color_public_closure_20260813.json"
REPORT = ROOT / "refs/conformance/colorkeep_current_installed_complete_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
PINS = {
    "source_sha256": "d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3",
    "installed_binary_sha256": "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d",
    "accepted_identity_sha256": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
}
STATUS = "PASS_COLORKEEP_CURRENT_INSTALLED_COMPLETE_BOUNDED_UNION_AE_FREE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def generate() -> dict[str, Any]:
    identities = {
        "source_sha256": sha256(SOURCE),
        "installed_binary_sha256": sha256(INSTALLED),
        "accepted_identity_sha256": sha256(IDENTITY),
        "union_generator_sha256": sha256(UNION),
        "legacy_closure_sha256": sha256(LEGACY),
        "count9_closure_sha256": sha256(COUNT9),
    }
    if {key: identities[key] for key in PINS} != PINS:
        raise RuntimeError(f"ColorKeep current identity drift: {identities}")
    manifest = json.loads(IDENTITY.read_text())
    row = next(item for item in manifest["plugins"] if item["plugin"] == "ColorKeep")
    if row.get("sha256") != PINS["installed_binary_sha256"] or not row.get("source_installed_exact"):
        raise RuntimeError("accepted ColorKeep row drift")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    union = load(UNION, "colorkeep_current_union")
    union.BINARY = INSTALLED
    legacy = union.check_legacy()
    count9 = union.check_count9()
    if legacy.get("paths_per_slice") != 10 or legacy.get("source_helper_active_mutation_rejects") != 18:
        raise RuntimeError("ColorKeep current legacy union drift")
    architectures = count9.get("architectures")
    expected_count9 = {"paths": 5, "padded_output_sha256": "2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe", "rejects": 136, "all_precommit_atomic": True}
    if not isinstance(architectures, dict) or set(architectures) != {"arm64", "x86_64"} or any(value != expected_count9 for value in architectures.values()):
        raise RuntimeError("ColorKeep current count9 union drift")
    return {
        "schema": "colorkeep.current-installed-complete-bounded-union/1",
        "status": STATUS,
        "claim_boundary": (
            "The current installed arm64 and Rosetta x86_64 slices replay all ten exact-source "
            "legacy count5/100 public paths and all five exact-source/palette count9 paths per "
            "slice. This current-state closure does not rewrite the historical install transaction "
            "and adds no arbitrary source, palette, tuple or native-AE claim."
        ),
        "identities": identities,
        "runtime": {"legacy": legacy, "count9": count9},
        "summary": {
            "exact_public_paths_per_slice": 15,
            "exact_public_paths_total": 30,
            "legacy_paths_per_slice": 10,
            "count9_paths_per_slice": 5,
            "legacy_source_mutation_rejects": 18,
            "count9_rejects_per_slice": 136,
        },
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_source_palette_tuple": False,
            "historical_transaction_rewritten": False,
        },
    }


def validate(value: dict[str, Any], *, live: bool = True) -> bool:
    try:
        if live:
            return value == generate()
        if set(value) != {"schema", "status", "claim_boundary", "identities", "runtime", "summary", "after_effects_processes", "scope"}:
            return False
        if value["schema"] != "colorkeep.current-installed-complete-bounded-union/1" or value["status"] != STATUS:
            return False
        if {key: value["identities"].get(key) for key in PINS} != PINS:
            return False
        if value["summary"] != {"exact_public_paths_per_slice": 15, "exact_public_paths_total": 30, "legacy_paths_per_slice": 10, "count9_paths_per_slice": 5, "legacy_source_mutation_rejects": 18, "count9_rejects_per_slice": 136}:
            return False
        if value["after_effects_processes"] != [] or value["scope"] != {"installed_arm64": True, "installed_x86_64": True, "native_after_effects": False, "arbitrary_source_palette_tuple": False, "historical_transaction_rewritten": False}:
            return False
        runtime = value["runtime"]
        if set(runtime) != {"legacy", "count9"} or runtime["legacy"].get("paths_per_slice") != 10 or runtime["legacy"].get("source_helper_active_mutation_rejects") != 18:
            return False
        expected_count9 = {"paths": 5, "padded_output_sha256": "2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe", "rejects": 136, "all_precommit_atomic": True}
        architectures = runtime["count9"].get("architectures")
        if not isinstance(architectures, dict) or set(architectures) != {"arm64", "x86_64"} or any(row != expected_count9 for row in architectures.values()):
            return False
        return "does not rewrite the historical install transaction" in value["claim_boundary"]
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def markdown(report: dict[str, Any]) -> str:
    return f"""# ColorKeep current installed complete bounded union

Status: `{report['status']}`

Both current installed Universal slices replay 15 bounded public paths each:
ten legacy count5/100 paths and five count9 paths. The historical install
transaction remains immutable; this report binds only the current accepted row
and current installed executable. No AE process is launched.
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
        raise RuntimeError("persisted ColorKeep current closure drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
