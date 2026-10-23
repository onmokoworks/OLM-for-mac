#!/usr/bin/env python3
"""Replay OLMBlur's complete bounded Smart admission union through both installed slices."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMU = ROOT / "tools/emulation"
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
SHIM = EMU / "olmblur_installed_effectmain_shim_20260813.h"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin/Contents/MacOS/OLMBlur"
INSTALL_IDENTITY = ROOT / "refs/conformance/olm_hostless_batch5_incremental_install_20260813.json"
REPORT = ROOT / "refs/conformance/olmblur_current_installed_complete_admission_union_20260813.json"
DOC = REPORT.with_suffix(".md")

PROBES = {
    "base": EMU / "probe_olmblur_smart_public_admission_20260813.cpp",
    "pf16_base": EMU / "probe_olmblur_pf16_7x5_public_admission_20260813.cpp",
    "pf16": EMU / "probe_olmblur_pf16_worker_sources_public_admission_20260813.cpp",
    "pf8": EMU / "probe_olmblur_pf8_retained_public_admission_20260813.cpp",
    "pf32": EMU / "probe_olmblur_pf32_retained_public_admission_20260813.cpp",
}
SOURCE_REPORTS = {
    "PF8": ROOT / "refs/conformance/olmblur_pf8_retained_public_admission_20260813.json",
    "PF16": ROOT / "refs/conformance/olmblur_pf16_worker_sources_public_admission_20260813.json",
    "PF32": ROOT / "refs/conformance/olmblur_pf32_retained_public_closure_20260813.json",
}
PINS = {
    "source": "22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7",
    "shim": "155b9dca2ef49e013574814feb158fe452741eac36fed2e5f7343b2a52e18a38",
    "installed": "ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d",
    "install_identity": "b6a97f0697defce2876740877ae6eec26de70b5db6beb5d2e402ed3b85ea5494",
    "probe_base": "1023569bb8ca7e685b2a104d5c22e9b549138bd56d908c2e6bb853f29dd785c5",
    "probe_pf16_base": "796a656e14838dac783611cf534c31c722068e2a17ebc663e0c3c078fb5ee1be",
    "probe_pf16": "a6306a0e613b71d1ab79bdf1c331acd2fc14537679ce9f33cd7705375cf8206a",
    "probe_pf8": "ee0e21390b69d7a766717275b3b6ecd03cce49caae89fccf84f0d7d8b5674b46",
    "probe_pf32": "0d4c9e29c50e7656ba46186dd78ac54af6e086c6f2bc9daaa5940028d8a9f690",
    "report_PF8": "202e078325238363ec1ae6ac33a4e9ed93a5daaf1335b27e5dd879384b114d53",
    "report_PF16": "25a3f756e435e86a04fa90eb149fe0814739ccae6914df19ba570f3a86038823",
    "report_PF32": "82136a36e39a2081a0b76221a7f8aff69963730e90252d1c2b93387db02c6d8f",
}
STATUS = "PASS_OLMBLUR_CURRENT_INSTALLED_COMPLETE_SMART_ADMISSION_UNION_AE_FREE"
TOP = {"schema", "status", "claim_boundary", "authorities", "summary", "architectures", "after_effects_processes", "scope"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authorities() -> dict:
    return {
        "source": sha(SOURCE), "shim": sha(SHIM), "installed": sha(INSTALLED),
        "install_identity": sha(INSTALL_IDENTITY),
        **{f"probe_{name}": sha(path) for name, path in PROBES.items()},
        **{f"report_{depth}": sha(path) for depth, path in SOURCE_REPORTS.items()},
    }


def expected_transcript(depth: str) -> str:
    report = json.loads(SOURCE_REPORTS[depth].read_text())
    key = "mac_run_lines" if depth == "PF32" else "run_lines"
    return "\n".join(report[key]) + "\n"


def materialize(directory: Path) -> None:
    old = '#include "../../mac/OLMBlur/OLMBlur.cpp"'
    for name, source in PROBES.items():
        text = source.read_text()
        if name == "base":
            if text.count(old) != 1:
                raise RuntimeError("source include anchor drift")
            text = text.replace(old, f'#include "{SHIM.as_posix()}"')
        (directory / source.name).write_text(text)


def compile_run(arch: str, depth: str) -> str:
    top = {"PF8": PROBES["pf8"].name, "PF16": PROBES["pf16"].name, "PF32": PROBES["pf32"].name}[depth]
    with tempfile.TemporaryDirectory(prefix=".olmblur-installed-union.", dir=EMU) as raw:
        directory = Path(raw)
        materialize(directory)
        executable = directory / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [_UCRT_CXX, "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math", "-ffp-contract=off",
                   "-isysroot", sdk, "-Wno-pragma-pack", "-Wno-deprecated-declarations"]
        for include in ("Headers", "Headers/SP", "Util", "Resources", "core", "mac/OLMBlur", "tools/emulation"):
            command.extend(("-I", str(ROOT / include)))
        command.extend((str(directory / top), "-framework", "Cocoa", "-o", str(executable)))
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)
        environment = os.environ.copy()
        environment["OLMBLUR_INSTALLED_BINARY"] = str(INSTALLED)
        run = subprocess.run([str(executable)], cwd=ROOT, env=environment, capture_output=True, text=True)
        if run.returncode or run.stderr:
            raise RuntimeError(f"{arch}/{depth} rc={run.returncode}: {run.stdout[-1000:]} {run.stderr}")
        return run.stdout


def ae_processes() -> list[str]:
    found = []
    for name in ("After Effects", "AfterFX", "aerender"):
        result = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if result.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in result.stdout.split())
    return found


def generate() -> dict:
    live = authorities()
    if live != PINS:
        raise RuntimeError(f"authority drift: {live}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    architecture_rows = {}
    for arch in ("arm64", "x86_64"):
        depth_rows = {}
        for depth in ("PF8", "PF16", "PF32"):
            observed = compile_run(arch, depth)
            expected = expected_transcript(depth)
            if observed != expected:
                raise RuntimeError(f"{arch}/{depth} differs from source-built public closure")
            depth_rows[depth] = {"line_count": len(observed.splitlines()),
                                 "transcript_sha256": hashlib.sha256(observed.encode()).hexdigest(),
                                 "source_built_transcript_exact": True}
        architecture_rows[arch] = depth_rows
    return {
        "schema": "olmblur.current-installed-complete-admission-union/1", "status": STATUS,
        "claim_boundary": "Both installed Universal slices reproduce the complete currently admitted source-bound Smart union: PF8 12, PF16 8, and PF32 20 exact cells. This is AE-free public EffectMain replay, not arbitrary-source or native-AE evidence.",
        "authorities": live,
        "summary": {"cells_per_slice": 40, "cells_total": 80, "positive_controls_per_slice": 80,
                    "negative_controls_per_slice": 1298, "source_built_transcripts_exact": True},
        "architectures": architecture_rows, "after_effects_processes": [],
        "scope": {"installed_arm64": True, "installed_x86_64": True, "native_after_effects": False,
                  "arbitrary_source_tuple_geometry": False},
    }


def validate(report: dict) -> None:
    if set(report) != TOP or report["schema"] != "olmblur.current-installed-complete-admission-union/1" or report["status"] != STATUS:
        raise RuntimeError("schema/status drift")
    if report["authorities"] != PINS or report["summary"] != {
        "cells_per_slice": 40, "cells_total": 80, "positive_controls_per_slice": 80,
        "negative_controls_per_slice": 1298, "source_built_transcripts_exact": True,
    }:
        raise RuntimeError("authority/summary drift")
    expected = {}
    for arch in ("arm64", "x86_64"):
        expected[arch] = {}
        for depth in ("PF8", "PF16", "PF32"):
            transcript = expected_transcript(depth)
            expected[arch][depth] = {"line_count": len(transcript.splitlines()),
                                     "transcript_sha256": hashlib.sha256(transcript.encode()).hexdigest(),
                                     "source_built_transcript_exact": True}
    if report["architectures"] != expected:
        raise RuntimeError("architecture transcript drift")
    if report["after_effects_processes"] != [] or report["scope"] != {
        "installed_arm64": True, "installed_x86_64": True, "native_after_effects": False,
        "arbitrary_source_tuple_geometry": False,
    }:
        raise RuntimeError("scope drift")


def markdown(report: dict) -> str:
    return (
        "# OLMBlur current installed complete Smart admission union — 2026-08-13\n\n"
        f"Status: `{STATUS}`\n\n"
        "Both installed Universal slices reproduce all 40 bounded Smart cells: PF8 12, PF16 8 and PF32 20. Per slice, 80 optional-checkin positive controls and 1,298 bounded negative controls are byte-identical to the source-built real-SDK transcripts. x86_64 runs under Rosetta; AE was not launched.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    fresh = generate()
    validate(fresh)
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(fresh))
    else:
        saved = json.loads(REPORT.read_text())
        validate(saved)
        if fresh != saved or DOC.read_text() != markdown(saved):
            raise RuntimeError("persisted installed union drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
