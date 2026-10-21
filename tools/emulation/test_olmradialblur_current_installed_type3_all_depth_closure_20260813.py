#!/usr/bin/env python3
"""Validate the frozen installed Radial Type 3 replay and its live binary.

The persisted replay belongs to the installed batch-4 source.  A newer source
candidate may coexist in the worktree, so the default read-only path validates
the frozen report plus the live installed/build/install identities without
silently recompiling the newer source as the old installed owner.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import types
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmradialblur_type3_all_depth_public_closure_20260813.py"
SHIM = ROOT / "tools/emulation/olmradialblur_installed_effectmain_shim_20260813.h"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
SOURCE_REPORT = ROOT / "refs/conformance/olmradialblur_type3_all_depth_public_closure_20260813.json"
BUILD_IDENTITY = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/build_identity.json"
INSTALL_IDENTITY = ROOT / "refs/conformance/olmradialblur_worldsuite_lifecycle_install_20260814.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_type3_all_depth_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "base_generator": "2538fae2eb4c2b3534058a219d9ac0a273fb5ec8a1ad7d19a6671efdef6665ec",
    "shim": "7506106dd5b9bac9e0ecd77cff0b13ab8f4e66823a2fe341759039035f28fb49",
    "production_source": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
    "source_report": "ce0dc29245a93775a384984c70999ae2381fd148b0bd2c53d9c0a697a2830002",
    "build_identity": "641af05eec81269738fa65d99fcd59bd0d16f1d28f89eb95bbe8f978c5c6bb93",
    "install_identity": "a5ed6932892caf5dfb5db0d95620af5c05dfe6d70a8aa006eead4da85982d4f3",
    "installed_binary": "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5",
}
STATUS = "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_TYPE3_ALL_DEPTH_PUBLIC_AE_FREE"
CLAIM = (
    "For all 45 fixed 9x7 Type 3 source/Layer pairs, both current installed Universal "
    "slices EffectMain Classic and Smart entries reproduce the source-built typed owner: "
    "15 pairs each at PF8, PF16 and PF32, including padded output and each pair's bounded "
    "variation/source/Layer reject controls. The source is "
    "compiled into the probe only for direct-owner and fixture helpers; all public calls "
    "are forwarded by dlopen to the installed Mach-O. This is not native-AE evidence."
)
TOP_KEYS = {
    "schema", "status", "claim_boundary", "authorities", "rows", "rows_sha256",
    "summary", "after_effects_processes", "scope",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("radial_installed_base", BASE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_base_for_arch(arch: str):
    if arch == "arm64":
        return load_base()
    if arch != "x86_64":
        raise RuntimeError(f"unsupported probe architecture: {arch}")
    text = BASE.read_text()
    needle = 'cmd = ["clang++", "-std=c++17", "-arch", "arm64",'
    if text.count(needle) != 1:
        raise RuntimeError("base probe architecture anchor drift")
    text = text.replace(needle, 'cmd = ["clang++", "-std=c++17", "-arch", "x86_64",')
    module = types.ModuleType("radial_installed_base_x86_64")
    module.__file__ = str(BASE)
    exec(compile(text, str(BASE), "exec"), module.__dict__)
    return module


def authorities() -> dict[str, str]:
    return {
        "base_generator": sha256(BASE),
        "shim": sha256(SHIM),
        "production_source": sha256(SOURCE),
        "source_report": sha256(SOURCE_REPORT),
        "build_identity": sha256(BUILD_IDENTITY),
        "install_identity": sha256(INSTALL_IDENTITY),
        "installed_binary": sha256(INSTALLED),
    }


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in run.stdout.split())
    return found


def canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_rows() -> list[dict[str, Any]]:
    report = json.loads(SOURCE_REPORT.read_text())
    rows = report.get("rows")
    if report.get("status") != "pass" or not isinstance(rows, list) or len(rows) != 45:
        raise RuntimeError("source Type 3 45-row closure drift")
    return rows


def expected_rows() -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for architecture in ("arm64", "x86_64"):
        for row in source_rows():
            output = row["candidate"]["output"]
            expected.append({
                "architecture": architecture,
                "depth": row["depth"],
                "source_kind": row["source_kind"],
                "layer_family": row["layer_family"],
                "direct_owner_sha256": output,
                "installed_classic_sha256": row["candidate"]["classic_output"],
                "installed_smart_sha256": row["candidate"]["smart_output"],
                "reject_controls": row["reject_controls"],
                "padded_output_exact": True,
            })
    return expected


def generate() -> dict[str, Any]:
    live = authorities()
    if live != PINS:
        raise RuntimeError(f"installed Radial authority drift: {live}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    original = SOURCE.read_text()
    prefix = "#define EffectMain SourceBuiltOLMRadialBlurEffectMain\n"
    suffix = f'\n#undef EffectMain\n#include "{SHIM}"\n'
    rows = []
    retained_rows = source_rows()
    with tempfile.TemporaryDirectory(prefix="radial-installed-source-") as temporary:
        transformed = Path(temporary) / "source.cpp"
        transformed.write_text(prefix + original + suffix)
        for architecture in ("arm64", "x86_64"):
            base = load_base_for_arch(architecture)
            old_source = base.SOURCE
            base.SOURCE = transformed
            try:
                for retained in retained_rows:
                    depth = retained["depth"]
                    source_kind = retained["source_kind"]
                    layer_family = retained["layer_family"]
                    produced = base.candidate(
                        depth,
                        {},
                        base.source(depth, source_kind),
                        base.layer(depth, layer_family),
                    )
                    hashes = {name: hashlib.sha256(produced[name]).hexdigest()
                              for name in ("output", "classic_output", "smart_output")}
                    expected = retained["candidate"]
                    if hashes != {name: expected[name] for name in hashes}:
                        raise RuntimeError(
                            f"installed Radial {architecture} PF{depth} "
                            f"{source_kind}/{layer_family} differs: {hashes}")
                    if produced["reject_controls"] != retained["reject_controls"]:
                        raise RuntimeError("installed Radial reject-control drift")
                    rows.append({
                        "architecture": architecture,
                        "depth": depth,
                        "source_kind": source_kind,
                        "layer_family": layer_family,
                        "direct_owner_sha256": hashes["output"],
                        "installed_classic_sha256": hashes["classic_output"],
                        "installed_smart_sha256": hashes["smart_output"],
                        "reject_controls": produced["reject_controls"],
                        "padded_output_exact": True,
                    })
            finally:
                base.SOURCE = old_source
    digest = canonical(rows)
    expected = expected_rows()
    if rows != expected:
        raise RuntimeError("installed Radial complete row matrix drift")
    return {
        "schema": "olmradialblur.current-installed-type3-all-depth/2",
        "status": STATUS,
        "claim_boundary": CLAIM,
        "authorities": live,
        "rows": rows,
        "rows_sha256": digest,
        "summary": {
            "depths": [8, 16, 32],
            "public_exact_cells_per_slice": 45,
            "public_exact_cells_total": 90,
            "bounded_reject_control_sets_per_slice": 45,
            "classic_smart_direct_owner_exact": True,
        },
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_source_layer_tuple_geometry": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != TOP_KEYS:
        raise RuntimeError("installed Radial top schema drift")
    if report["schema"] != "olmradialblur.current-installed-type3-all-depth/2" or report["status"] != STATUS:
        raise RuntimeError("installed Radial status drift")
    if report["claim_boundary"] != CLAIM or report["authorities"] != PINS:
        raise RuntimeError("installed Radial identity drift")
    rows = report["rows"]
    expected = expected_rows()
    expected_digest = canonical(expected)
    if canonical(rows) != expected_digest or report["rows_sha256"] != expected_digest:
        raise RuntimeError("installed Radial row drift")
    if rows != expected:
        raise RuntimeError("installed Radial cell drift")
    if report["summary"] != {
        "depths": [8, 16, 32], "public_exact_cells_per_slice": 45,
        "public_exact_cells_total": 90, "bounded_reject_control_sets_per_slice": 45,
        "classic_smart_direct_owner_exact": True,
    }:
        raise RuntimeError("installed Radial summary drift")
    if report["after_effects_processes"] != [] or report["scope"] != {
        "installed_arm64": True, "installed_x86_64": True,
        "native_after_effects": False, "arbitrary_source_layer_tuple_geometry": False,
    }:
        raise RuntimeError("installed Radial scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMRadialBlur current installed Type 3 all-depth closure (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        "Installed arm64 and Rosetta x86_64 Classic and Smart match the direct typed owner for all "
        "45 exact fixed 9x7 source/Layer pairs: 15 each at PF8, PF16 and PF32. Every pair also "
        "executes its bounded public reject controls without committing output.\n\n"
        f"Boundary: {CLAIM}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        # Rewriting is intentionally possible only while every historical
        # authority, including the batch-4 source, is present byte-for-byte.
        fresh = generate()
        validate(fresh)
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(fresh))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("installed Radial report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if MARKDOWN.read_text() != markdown(persisted):
            raise RuntimeError("installed Radial markdown differs from frozen report")
        live_binary = sha256(INSTALLED)
        if live_binary != PINS["installed_binary"]:
            raise RuntimeError(f"installed Radial binary drift: {live_binary}")
        if sha256(BUILD_IDENTITY) != PINS["build_identity"]:
            raise RuntimeError("installed Radial build identity drift")
        if sha256(INSTALL_IDENTITY) != PINS["install_identity"]:
            raise RuntimeError("installed Radial install identity drift")
        processes = ae_processes()
        if processes:
            raise RuntimeError(f"After Effects must remain stopped: {processes}")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
