#!/usr/bin/env python3
"""Replay the bounded OLMBlur public closure through the current installed Mach-O."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmblur_smart_public_admission_20260813.cpp"
SHIM = ROOT / "tools/emulation/olmblur_installed_effectmain_shim_20260813.h"
FIXTURE = resolve_asset(ROOT / "tools/emulation/fixtures/olmblur_amount_repeat_legacy_matrix_20260810")
FIXTURE_MANIFEST = FIXTURE / "manifest.json"
SOURCE_REPORT = ROOT / "refs/conformance/olmblur_smart_public_admission_20260813.json"
BUILD_IDENTITY = resolve_asset(ROOT / "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/build_identity.json")
INSTALL_IDENTITY = ROOT / "refs/conformance/olm_hostless_batch5_incremental_install_20260813.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin/Contents/MacOS/OLMBlur"
REPORT = ROOT / "refs/conformance/olmblur_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "probe": "1023569bb8ca7e685b2a104d5c22e9b549138bd56d908c2e6bb853f29dd785c5",
    "shim": "155b9dca2ef49e013574814feb158fe452741eac36fed2e5f7343b2a52e18a38",
    "fixture_manifest": "01a5c8bc8d4269ae31ed918c6d1f3db6fcc26014800a6a06bba3c00dba012d5c",
    "source_report": "ce129458762188e4bd59906e96b263500121781b7160434b34eb54b99a3c5857",
    "build_identity": "767ec979aa369a3c2417d2577bfc9d87a2f06d3f419a8a617993de25f839dbf5",
    "install_identity": "b6a97f0697defce2876740877ae6eec26de70b5db6beb5d2e402ed3b85ea5494",
    "installed_binary": "ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d",
}
RUN_SHA256 = "184159a121d01ab948242454c59451b9f8213996eae46193e19f63d2d58c0e33"
STATUS = "PASS_OLMBLUR_CURRENT_INSTALLED_PUBLIC6_SAFETY100_AE_FREE"
CLAIM = (
    "Both current installed Universal slices of OLMBlur reproduce the source-built real-SDK public "
    "closure byte-for-byte per slice: 12 positive controls for six bounded numerical cells, 91 "
    "SmartRender negatives, one SmartPre positive and nine SmartPre negatives. The x86_64 route runs under Rosetta. This is "
    "an AE-free dlopen replay, not native-After-Effects or arbitrary-input evidence."
)
TOP_KEYS = {
    "schema", "status", "claim_boundary", "authorities", "summary", "run_sha256",
    "run_lines", "after_effects_processes", "scope",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in run.stdout.split())
    return found


def live_authorities() -> dict[str, str]:
    return {
        "probe": sha256(PROBE),
        "shim": sha256(SHIM),
        "fixture_manifest": sha256(FIXTURE_MANIFEST),
        "source_report": sha256(SOURCE_REPORT),
        "build_identity": sha256(BUILD_IDENTITY),
        "install_identity": sha256(INSTALL_IDENTITY),
        "installed_binary": sha256(INSTALLED),
    }


def compile_and_run(arch: str) -> str:
    source = PROBE.read_text()
    old = '#include "../../mac/OLMBlur/OLMBlur.cpp"'
    new = '#include "olmblur_installed_effectmain_shim_20260813.h"'
    if source.count(old) != 1:
        raise RuntimeError("probe include anchor drift")
    with tempfile.TemporaryDirectory(prefix="olmblur-installed-public-") as temporary:
        directory = Path(temporary)
        transformed = directory / "probe.cpp"
        transformed.write_text(source.replace(old, new))
        executable = directory / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [
            "clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-isysroot", sdk, "-Wno-pragma-pack",
            "-Wno-deprecated-declarations",
        ]
        for include in ("Headers", "Headers/SP", "Util", "Resources", "core", "mac/OLMBlur", "tools/emulation"):
            command.extend(("-I", str(ROOT / include)))
        command.extend((str(transformed), "-framework", "Cocoa", "-o", str(executable)))
        compile_run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if compile_run.returncode:
            raise RuntimeError(compile_run.stdout + compile_run.stderr)
        environment = os.environ.copy()
        environment["OLMBLUR_INSTALLED_BINARY"] = str(INSTALLED)
        run = subprocess.run([str(executable), str(FIXTURE)], cwd=ROOT, env=environment, text=True, capture_output=True)
        if run.returncode or run.stderr:
            raise RuntimeError(f"installed probe failed rc={run.returncode}: {run.stdout[-2000:]} {run.stderr}")
        return run.stdout


def generate() -> dict[str, Any]:
    authorities = live_authorities()
    if authorities != PINS:
        raise RuntimeError(f"installed public authority drift: {authorities}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    source_report = json.loads(SOURCE_REPORT.read_text())
    expected_source = "\n".join(source_report["run_lines"]) + "\n"
    transcripts = {}
    for arch in ("arm64", "x86_64"):
        transcripts[arch] = compile_and_run(arch)
        if transcripts[arch] != expected_source:
            raise RuntimeError(f"installed public output differs from source-built closure for {arch}")
    stdout = "".join(f"ARCH {arch}\n" + transcripts[arch] for arch in ("arm64", "x86_64"))
    lines = stdout.splitlines()
    if hashlib.sha256(stdout.encode()).hexdigest() != RUN_SHA256:
        raise RuntimeError("installed public run digest drift")
    return {
        "schema": "olmblur.current-installed-public-closure/1",
        "status": STATUS,
        "claim_boundary": CLAIM,
        "authorities": authorities,
        "summary": {
            "architectures": ["arm64", "x86_64"],
            "numerical_cells_per_slice": 6,
            "numerical_cells_total": 12,
            "positive_controls_per_slice": 12,
            "smart_render_negatives_per_slice": 91,
            "smart_pre_positive_per_slice": 1,
            "smart_pre_negatives_per_slice": 9,
            "source_built_run_byte_identical": True,
        },
        "run_sha256": RUN_SHA256,
        "run_lines": lines,
        "after_effects_processes": [],
        "scope": {
            "native_after_effects": False,
            "arbitrary_source_tuple_geometry": False,
            "installed_binary": True,
            "installed_arm64": True,
            "installed_x86_64": True,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != TOP_KEYS:
        raise RuntimeError("installed public top-level schema drift")
    if report["schema"] != "olmblur.current-installed-public-closure/1" or report["status"] != STATUS:
        raise RuntimeError("installed public status drift")
    if report["claim_boundary"] != CLAIM or report["authorities"] != PINS:
        raise RuntimeError("installed public authority drift")
    if report["summary"] != {
        "architectures": ["arm64", "x86_64"], "numerical_cells_per_slice": 6,
        "numerical_cells_total": 12, "positive_controls_per_slice": 12,
        "smart_render_negatives_per_slice": 91, "smart_pre_positive_per_slice": 1,
        "smart_pre_negatives_per_slice": 9,
        "source_built_run_byte_identical": True,
    }:
        raise RuntimeError("installed public summary drift")
    lines = report["run_lines"]
    digest = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
    if report["run_sha256"] != RUN_SHA256 or digest != RUN_SHA256 or len(lines) != 230 or lines[0] != "ARCH arm64" or lines[115] != "ARCH x86_64":
        raise RuntimeError("installed public rows drift")
    if report["after_effects_processes"] != [] or report["scope"] != {
        "native_after_effects": False,
        "arbitrary_source_tuple_geometry": False,
        "installed_binary": True,
        "installed_arm64": True,
        "installed_x86_64": True,
    }:
        raise RuntimeError("installed public scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMBlur current installed public closure (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        "- Both Universal slices: six bounded numerical cells / 12 optional-checkin controls per slice exact.\n"
        "- SmartRender negative controls: 91 per slice exact.\n"
        "- SmartPre controls: one positive plus nine negative per slice exact.\n"
        "- Each installed output transcript is byte-identical to the source-built closure; x86_64 runs under Rosetta.\n\n"
        f"Boundary: {CLAIM}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fresh = generate()
    validate(fresh)
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(fresh))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("installed public report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if fresh != persisted or MARKDOWN.read_text() != markdown(persisted):
            raise RuntimeError("installed public report differs from live installed closure")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
