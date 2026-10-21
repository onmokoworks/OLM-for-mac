#!/usr/bin/env python3
"""Replay OLMColorKey's bounded public matrix through both installed slices."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmcolorkey_public_entries_real_sdk_20260813.cpp"
SHIM = ROOT / "tools/emulation/olmcolorkey_installed_effectmain_shim_20260813.h"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
SOURCE_REPORT = ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json"
BUILD_IDENTITY = ROOT / "handoffs/olmcolorkey_toggle24_universal_candidate_20260814/build_identity.json"
INSTALL_TRANSACTION = ROOT / "handoffs/olmcolorkey_toggle24_incremental_install_20260814/install_transaction.json"
ACCEPTED_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMColorKey.plugin/Contents/MacOS/OLMColorKey"
REPORT = ROOT / "refs/conformance/olmcolorkey_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "probe": "8193b267695107b42a8b32751e6fb016a50bb24e121d378159d2604bf4582372",
    "shim": "9aef5fdb5103d215a957da668f163305e697fe8eb891a6532b8a537713100e7e",
    "production_source": "4dbd264501a0d5d990a3726d16223c01c1996677b925f8546157b6a91ce677d1",
    "source_report": "423d1ea02e5aa40b78264ba7ba4cfd28ff42fde472f0d6ff99ba33ef7514a4a0",
    "build_identity": "f768e6b3413e4b6ebaee285ea478040a26311c7a6ff8e3b33b0d2dacf728bdec",
    "install_transaction": "4e8cf6f894e8b03b7b358865554c55951a1872dbb6ebe0ef3003aa6fd7d64004",
    "accepted_identity": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
    "installed_binary": "701ae9192e19d3e97dd33450e37ae97d90d9be5803ab663405507ed5e3659ca7",
}
RUN = {
    "stdout_bytes": 744240,
    "stdout_sha256": "6d6f9ecb4fba21d59c16c77f5e4f0f823bb9328204f9e00901bee29999c5f3f6",
    "stderr": "COLORKEY_PUBLIC_ENTRIES pass=1 classic=60 smart=60 callback_negatives=13\n",
    "returncode": 0,
}
STATUS = "PASS_OLMCOLORKEY_CURRENT_INSTALLED_BOTH_SLICES_PUBLIC60_AE_FREE"
CLAIM = (
    "The current installed arm64 and x86_64 OLMColorKey slices each reproduce the "
    "retained 60-cell subset of the source-built real-SDK public-entry transcript: "
    "60 bounded Classic cells, the same 60 Smart cells and 13 callback negatives. "
    "The three new 48x27 source cells are deliberately omitted because this installed "
    "identity predates them. The transformed probe includes the "
    "hash-pinned production source only for fixture/parameter helper definitions; every "
    "EffectMain call is forwarded by dlopen to the installed Mach-O. No native-AE or "
    "arbitrary-source claim is made."
)
TOP_KEYS = {
    "schema", "status", "claim_boundary", "authorities", "slice_runs", "summary",
    "after_effects_processes", "scope",
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


def authorities() -> dict[str, str]:
    return {
        "probe": sha256(PROBE),
        "shim": sha256(SHIM),
        "production_source": sha256(SOURCE),
        "source_report": sha256(SOURCE_REPORT),
        "build_identity": sha256(BUILD_IDENTITY),
        "install_transaction": sha256(INSTALL_TRANSACTION),
        "accepted_identity": sha256(ACCEPTED_IDENTITY),
        "installed_binary": sha256(INSTALLED),
    }


def run_slice(architecture: str) -> dict[str, Any]:
    source = PROBE.read_text()
    # The installed identity is the prior 60-cell build. Keep its replay exact
    # while the current source-built probe also carries the new 48x27 tuple.
    retained_only = "\t{0, 3, 4.0, 48, 27},\n"
    if source.count(retained_only) != 1:
        raise RuntimeError("installed retained-subset tuple anchor drift")
    source = source.replace(retained_only, "")
    current_count = "return pass && classic == 63 && smart == 63 ? 0 : 3;"
    retained_count = "return pass && classic == 60 && smart == 60 ? 0 : 3;"
    if source.count(current_count) != 1:
        raise RuntimeError("installed retained-subset count anchor drift")
    source = source.replace(current_count, retained_count)
    old = '#include "../../mac/OLMColorKey/OLMColorKey.cpp"'
    new = '#include "olmcolorkey_installed_effectmain_shim_20260813.h"'
    if source.count(old) != 1:
        raise RuntimeError("public probe include anchor drift")
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix=f"olmcolorkey-installed-{architecture}-") as temporary:
        directory = Path(temporary)
        transformed = directory / "probe.cpp"
        transformed.write_text(source.replace(old, new))
        executable = directory / "probe"
        command = [
            "clang++", "-std=c++17", "-arch", architecture, "-O2", "-isysroot", sdk,
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
        ]
        for include in ("Headers", "Headers/SP", "Util", "Resources", "mac/OLMColorKey", "tools/emulation"):
            command.extend(("-I", str(ROOT / include)))
        command.extend((
            str(transformed), str(ROOT / "mac/OLMColorKey/OLMColorKey_Strings.cpp"),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(executable),
        ))
        compile_run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if compile_run.returncode:
            raise RuntimeError(compile_run.stdout + compile_run.stderr)
        execute = ["arch", "-x86_64", str(executable)] if architecture == "x86_64" else [str(executable)]
        environment = os.environ.copy()
        environment["OLMCOLORKEY_INSTALLED_BINARY"] = str(INSTALLED)
        run = subprocess.run(execute, cwd=ROOT, env=environment, capture_output=True)
    observed = {
        "stdout_bytes": len(run.stdout),
        "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(),
        "stderr": run.stderr.decode(),
        "returncode": run.returncode,
    }
    if observed != RUN:
        raise RuntimeError(f"installed {architecture} public transcript drift: {observed}")
    return observed


def generate() -> dict[str, Any]:
    live = authorities()
    if live != PINS:
        raise RuntimeError(f"installed ColorKey authority drift: {live}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    runs = {architecture: run_slice(architecture) for architecture in ("arm64", "x86_64")}
    return {
        "schema": "olmcolorkey.current-installed-public-closure/1",
        "status": STATUS,
        "claim_boundary": CLAIM,
        "authorities": live,
        "slice_runs": runs,
        "summary": {
            "architectures": ["arm64", "x86_64"],
            "classic_cells_per_slice": 60,
            "smart_cells_per_slice": 60,
            "callback_negatives_per_slice": 13,
            "source_built_transcript_exact_per_slice": True,
        },
        "after_effects_processes": [],
        "scope": {
            "installed_binary": True,
            "native_after_effects": False,
            "arbitrary_source_tuple_geometry": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != TOP_KEYS:
        raise RuntimeError("installed ColorKey top schema drift")
    if report["schema"] != "olmcolorkey.current-installed-public-closure/1" or report["status"] != STATUS:
        raise RuntimeError("installed ColorKey status drift")
    if report["claim_boundary"] != CLAIM or report["authorities"] != PINS:
        raise RuntimeError("installed ColorKey identity drift")
    if report["slice_runs"] != {"arm64": RUN, "x86_64": RUN}:
        raise RuntimeError("installed ColorKey slice transcript drift")
    if report["summary"] != {
        "architectures": ["arm64", "x86_64"],
        "classic_cells_per_slice": 60,
        "smart_cells_per_slice": 60,
        "callback_negatives_per_slice": 13,
        "source_built_transcript_exact_per_slice": True,
    }:
        raise RuntimeError("installed ColorKey summary drift")
    if report["after_effects_processes"] != [] or report["scope"] != {
        "installed_binary": True,
        "native_after_effects": False,
        "arbitrary_source_tuple_geometry": False,
    }:
        raise RuntimeError("installed ColorKey scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMColorKey current installed public closure (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        "Both installed slices reproduce the source-built public transcript: 60 Classic "
        "cells, 60 Smart cells and 13 callback negatives per slice.\n\n"
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
            raise RuntimeError("installed ColorKey report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != fresh or MARKDOWN.read_text() != markdown(persisted):
            raise RuntimeError("installed ColorKey report differs from live slices")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
