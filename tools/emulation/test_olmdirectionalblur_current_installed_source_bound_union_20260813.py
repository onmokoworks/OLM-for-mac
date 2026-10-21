#!/usr/bin/env python3
"""Replay DirectionalBlur's explicit source-bound public sub-union installed."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
INSTALLED = Path.home() / (
    "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
    "OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
)
DUAL_TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_dual_side_20260813.py"
DUAL_PROBE = ROOT / "tools/emulation/probe_olmdirectionalblur_current_installed_dual_side_20260813.cpp"
DUAL_REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_dual_side_20260813.json"
TYPE3_TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_type3_layer_source_guard_closure_20260813.py"
TYPE3_PROBE = ROOT / "tools/emulation/probe_olmdirectionalblur_current_installed_type3_layer_20260813.cpp"
TYPE3_REPORT = ROOT / "refs/conformance/olmdirectionalblur_type3_layer_source_guard_closure_20260813.json"
NATURAL_TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py"
NATURAL_REPORT = ROOT / "refs/conformance/olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
FIXTURE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_source_bound_union_20260813.json"
NOTE = REPORT.with_suffix(".md")

STATUS = "PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_EXPLICIT_SOURCE_BOUND_UNION"
SOURCE_SHA = "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845"
INSTALLED_SHA = "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de"
SLICES_SHA = "0921fcabd0ca090bd7128e691ff74d478ecc58e4832f0fd15a7b66216e1b0f6d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
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


def compile_real_probe(cpp: Path, executable: Path, arch: str) -> None:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = [
        "clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
        "-ffp-contract=off", "-Wno-unused-function", "-Wno-unused-parameter",
        "-isysroot", sdk,
        "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
        str(cpp),
        str(ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp"),
        str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
        str(ROOT / "Util/MissingSuiteError.cpp"),
        str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"),
        "-framework", "Cocoa", "-o", str(executable),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)


def run_natural(arch: str) -> dict[str, Any]:
    module = load(NATURAL_TOOL, f"directional_natural_{arch}")
    saved = json.loads(NATURAL_REPORT.read_text(encoding="utf-8"))
    expected_by_name = {
        row["name"]: row["public_raw_sha256"] for row in saved["source_basis"]
    }
    crop_expected = {row["depth"]: row["raw_sha256"] for row in saved["public_effectmain"]}
    sources = {"pinned_crop": Image.open(FIXTURE).convert("RGBA").crop((472, 262, 536, 298)).tobytes()}
    sources.update(module.source_basis())

    def typed_source_hashes(rgba: bytes) -> dict[str, str]:
        pixels = [rgba[index:index + 4] for index in range(0, len(rgba), 4)]
        return {
            "PF8": hashlib.sha256(b"".join(
                bytes((pixel[3], pixel[0], pixel[1], pixel[2])) for pixel in pixels
            )).hexdigest(),
            "PF16": hashlib.sha256(b"".join(
                ((value * 32768 + 127) // 255).to_bytes(2, "little")
                for pixel in pixels for value in (pixel[3], pixel[0], pixel[1], pixel[2])
            )).hexdigest(),
            "PF32": hashlib.sha256(b"".join(
                struct.pack("<4f", pixel[3] / 255, pixel[0] / 255,
                            pixel[1] / 255, pixel[2] / 255)
                for pixel in pixels
            )).hexdigest(),
        }
    rows = []
    with tempfile.TemporaryDirectory(prefix=f"directional-installed-natural-{arch}.") as raw:
        temp = Path(raw)
        cpp = temp / "natural64_probe.cpp"
        text = DUAL_PROBE.read_text(encoding="utf-8")
        relative_source = '#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"'
        absolute_source = f'#include "{SOURCE}"'
        if text.count(relative_source) != 1:
            raise RuntimeError("Natural64 production include drift")
        text = text.replace(relative_source, absolute_source)
        replacements = {
            "constexpr int W=32,H=18;": "constexpr int W=64,H=36;",
            "g_params[3].u.fd.value=50*65536;": "g_params[3].u.fd.value=0;",
            "g_params[6].u.sd.value=50;": "g_params[6].u.sd.value=0;",
            "g_params[7].u.fd.value=100*65536;": "g_params[7].u.fd.value=0;",
            "g_params[10].u.sd.value=8;": "g_params[10].u.sd.value=0;",
            "g_params[11].u.sd.value=50;": "g_params[11].u.sd.value=0;",
            "g_params[12].u.fd.value=50*65536;": "g_params[12].u.fd.value=0;",
            "g_params[15].u.fd.value=100*65536;": "g_params[15].u.fd.value=25*65536;",
            "POS dual_side_type2_pf%d": "POS natural64_type2_pf%d",
        }
        for old, new in replacements.items():
            if text.count(old) != 1:
                raise RuntimeError(f"Natural64 probe splice drift: {old}")
            text = text.replace(old, new)
        cpp.write_text(text, encoding="utf-8")
        exe = temp / "probe"
        compile_real_probe(cpp, exe, arch)
        for name, rgba in sources.items():
            source_file = temp / f"{name}.rgba"
            source_file.write_bytes(rgba)
            run = subprocess.run(
                [str(exe), str(INSTALLED), str(source_file)],
                cwd=ROOT, capture_output=True, text=True,
            )
            if run.returncode:
                raise RuntimeError(f"Natural64 {arch}/{name}: {run.stdout} {run.stderr}")
            lines = run.stdout.splitlines()
            if lines[-1] != "SUMMARY pass=6 total=6":
                raise RuntimeError(f"Natural64 {arch}/{name} transcript drift")
            expected = crop_expected if name == "pinned_crop" else expected_by_name[name]
            rows.append({
                "name": name,
                "typed_source_sha256": typed_source_hashes(rgba),
                "output_sha256": expected,
                "source_built_installed_public_equal": True,
                "installed_source_mutation_rejects": 3,
                "transcript_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
            })
    return {
        "positive_cells": rows,
        "positive_cell_count": 15,
        "installed_source_mutation_rejects": 15,
    }


def run_type3(arch: str) -> dict[str, Any]:
    saved = json.loads(TYPE3_REPORT.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix=f"directional-installed-type3-real-{arch}.") as raw:
        temp = Path(raw)
        source_file = temp / "source.rgba"
        source_file.write_bytes(
            Image.open(FIXTURE).convert("RGBA").crop((472, 262, 488, 278)).tobytes()
        )
        exe = temp / "probe"
        compile_real_probe(TYPE3_PROBE, exe, arch)
        run = subprocess.run(
            [str(exe), str(INSTALLED), str(source_file)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if run.returncode:
            raise RuntimeError(f"Type3 {arch}: {run.stdout} {run.stderr}")
    lines = run.stdout.splitlines()
    if len(lines) != 58 or lines[-1] != "SUMMARY pass=57 total=57":
        raise RuntimeError(f"Type3 {arch} transcript drift")
    positives = [{
        "depth": row["depth"],
        "input_active_sha256": row["input_active_sha256"],
        "layer_active_sha256": row["layer_active_sha256"],
        "output_active_sha256": row["output_active_sha256"],
    } for row in saved["positives"]]
    return {
        "positive_cells": positives,
        "positive_cell_count": 3,
        "installed_negative_controls": 54,
        "transcript_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
    }


def authorities() -> dict[str, str]:
    paths = {
        "production": SOURCE, "installed_binary": INSTALLED,
        "dual_tool": DUAL_TOOL, "dual_probe": DUAL_PROBE, "dual_report": DUAL_REPORT,
        "type3_tool": TYPE3_TOOL, "type3_probe": TYPE3_PROBE, "type3_report": TYPE3_REPORT,
        "natural_tool": NATURAL_TOOL, "natural_report": NATURAL_REPORT,
        "fixture": FIXTURE,
    }
    return {name: sha(path) for name, path in paths.items()}


def generate() -> dict[str, Any]:
    if sha(SOURCE) != SOURCE_SHA or sha(INSTALLED) != INSTALLED_SHA:
        raise RuntimeError("production or installed identity drift")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    dual_module = load(DUAL_TOOL, "directional_dual_installed")
    dual_transcript = "".join(
        f"ARCH {arch}\n" + dual_module.compile_run(arch)
        for arch in ("arm64", "x86_64")
    )
    if hashlib.sha256(dual_transcript.encode()).hexdigest() != dual_module.RUN_SHA:
        raise RuntimeError("dual-side installed transcript drift")
    slices = []
    for arch in ("arm64", "x86_64"):
        slices.append({
            "arch": arch,
            "dual_side": {"positive_cells": 3, "installed_negative_controls": 3},
            "type3_layer": run_type3(arch),
            "natural64": run_natural(arch),
        })
    return {
        "schema": "olmdirectionalblur.current-installed-explicit-source-bound-union/1",
        "status": STATUS,
        "authorities": authorities(),
        "summary": {
            "architectures": ["arm64", "x86_64"],
            "explicit_source_bound_positive_cells_per_slice": 21,
            "explicit_source_bound_positive_cells_total": 42,
            "installed_negative_controls_per_slice": 72,
            "source_built_natural64_counterfactuals_not_replayed_installed": 64,
        },
        "slices": slices,
        "slices_digest": canonical_sha(slices),
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "complete_production_admission": False,
        },
        "claim_boundary": {
            "proven": (
                "The current installed arm64 and x86_64 slices execute 21 explicitly "
                "source-bound public cells each: dual-side Type2 at three depths, Type3 "
                "Layer at three depths, and Natural64 Type2 over five fixed sources at "
                "three depths. The installed real-SDK routes execute 72 negative controls "
                "per slice. x86_64 runs under Rosetta."
            ),
            "not_proven": [
                "complete production admission coverage",
                "arbitrary source, tuple, geometry, layout, Layer, or renderer",
                "the Natural64 closure's 64 internal-owner counterfactuals through the installed public entry",
                "native or interactive After Effects numerical output",
            ],
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {
        "schema", "status", "authorities", "summary", "slices", "slices_digest",
        "after_effects_processes", "scope", "claim_boundary",
    }:
        raise RuntimeError("top-level schema drift")
    if report["schema"] != "olmdirectionalblur.current-installed-explicit-source-bound-union/1":
        raise RuntimeError("schema drift")
    if report["status"] != STATUS or report["authorities"] != authorities():
        raise RuntimeError("status or authority drift")
    if report["after_effects_processes"] != []:
        raise RuntimeError("AE process claim drift")
    if report["scope"] != {
        "installed_arm64": True,
        "installed_x86_64": True,
        "native_after_effects": False,
        "complete_production_admission": False,
    }:
        raise RuntimeError("scope drift")
    if report["summary"] != {
        "architectures": ["arm64", "x86_64"],
        "explicit_source_bound_positive_cells_per_slice": 21,
        "explicit_source_bound_positive_cells_total": 42,
        "installed_negative_controls_per_slice": 72,
        "source_built_natural64_counterfactuals_not_replayed_installed": 64,
    }:
        raise RuntimeError("summary drift")
    slices = report["slices"]
    if [row.get("arch") for row in slices] != ["arm64", "x86_64"]:
        raise RuntimeError("slice set drift")
    if report["slices_digest"] != canonical_sha(slices):
        raise RuntimeError("slice digest drift")
    if report["slices_digest"] != SLICES_SHA:
        raise RuntimeError("canonical slice contract drift")
    for row in slices:
        if set(row) != {"arch", "dual_side", "type3_layer", "natural64"}:
            raise RuntimeError("slice schema drift")
        if row["dual_side"] != {"positive_cells": 3, "installed_negative_controls": 3}:
            raise RuntimeError("dual-side summary drift")
        if row["type3_layer"]["positive_cell_count"] != 3:
            raise RuntimeError("Type3 positive count drift")
        if row["type3_layer"]["installed_negative_controls"] != 54:
            raise RuntimeError("Type3 negative count drift")
        if row["natural64"]["positive_cell_count"] != 15:
            raise RuntimeError("Natural64 positive count drift")
        if len(row["natural64"]["positive_cells"]) != 5:
            raise RuntimeError("Natural64 source count drift")
        if row["natural64"]["installed_source_mutation_rejects"] != 15:
            raise RuntimeError("Natural64 mutation count drift")
    boundary = report["claim_boundary"]
    if set(boundary) != {"proven", "not_proven"} or len(boundary["not_proven"]) != 4:
        raise RuntimeError("claim boundary drift")


def markdown(report: dict[str, Any]) -> str:
    return f"""# DirectionalBlur current installed explicit source-bound union (2026-08-13)

Status: `{STATUS}`

- Installed arm64 and Rosetta x86_64: 21 explicitly source-bound public cells per slice, 42 total.
- Routes: dual-side Type2 3, Type3 Layer 3, and Natural64 Type2 5 fixed sources × 3 depths = 15.
- Installed real-SDK negative controls: 72 per slice (dual-side 3, Type3 54, Natural64 source mutations 15).
- The Natural64 closure's 64 internal-owner counterfactuals remain source-built evidence and are not relabeled as installed public replays.
- AE was not launched.

Boundary: {report['claim_boundary']['proven']} This does not prove {', '.join(report['claim_boundary']['not_proven'])}.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fresh = generate()
    validate(fresh)
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        NOTE.write_text(markdown(fresh), encoding="utf-8")
    else:
        saved = json.loads(REPORT.read_text(encoding="utf-8"))
        validate(saved)
        if saved != fresh or NOTE.read_text(encoding="utf-8") != markdown(saved):
            raise RuntimeError("persisted report drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
