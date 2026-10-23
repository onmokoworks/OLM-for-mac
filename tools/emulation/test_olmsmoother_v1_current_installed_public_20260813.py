#!/usr/bin/env python3
"""Replay representative bounded OLMSmoother v1 Classic cells through the installed Mach-O."""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmsmoother_v1_current_installed_public_20260813.cpp"
SOURCE = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
STRINGS = ROOT / "mac/OLMSmoother/OLMSmoother_Strings.cpp"
SUITE_CPP = ROOT / "Util/AEGP_SuiteHandler.cpp"
SUITE_H = ROOT / "Util/AEGP_SuiteHandler.h"
MISSING_CPP = ROOT / "Util/MissingSuiteError.cpp"
SDK_HEADER = ROOT / "Headers/AE_Effect.h"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin/Contents/MacOS/OLMSmoother"
BUILD_IDENTITY = ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/build_identity.json"
INSTALL_IDENTITY = ROOT / "refs/conformance/olm_hostless_batch4_incremental_install_20260813.json"
GUARD_REPORT = ROOT / "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_current_installed_public_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "probe": "89a13c2f4aa797ef2f76fd4cedd498d635a61878bef62c1ec73441e4d62cc39e",
    "source": "c8c7b7728553ee4ccaadc7ef802be40e607d7e7a7b829958d4b8dfab80f633dc",
    "strings": "ce4ed37933a67172f6cba6570a55a5f2ea592284e8a9f48cd852bf4fcf1484e7",
    "suite_cpp": "7c054c7b0778b1b26463d6bf31cd57ee1d971946e8da22fb174e9f088741606f",
    "suite_h": "36e1acf66a90979bd541bfb260e4dbf58dab2d00afec7d749dfcffc43a6843f7",
    "missing_cpp": "8c0cc22b898c94c73556778f5cef1ccf9cded81ee590bd04feb49028ff4f44d9",
    "sdk_header": "a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d",
    "installed_binary": "f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162",
    "build_identity": "5bc7432144a90801319452b1a23e39e131a75a266c270839640eff68a4bd40bd",
    "install_identity": "415e1b26b77097248173da13239b85ae70d0b6a446fa6eb31bc13a0bdc6895af",
    "guard_report": "55c5a81188a5042d25fb691abb154c4b44dbbec1b93cd3de8536fdced3cc92b8",
}
RUN_SHA256 = "2f070346b3b5d508bc0641c21e0af564c5180358b29b1f44d00790b869efcf35"
STATUS = "PASS_OLMSMOOTHER_V1_CURRENT_INSTALLED_REPRESENTATIVE_CLASSIC_AE_FREE"
SUMMARY = {"architectures": ["arm64", "x86_64"], "positive_cells_per_slice": 3, "positive_cells_total": 6, "negative_controls_per_slice": 2, "negative_controls_total": 4, "source_installed_byte_identical": True}
SCOPE = {"installed_arm64": True, "installed_x86_64": True, "native_after_effects": False, "complete_admission_union": False}
TOP_KEYS = {"schema", "status", "claim_boundary", "authorities", "summary", "run_sha256", "run_lines", "after_effects_processes", "scope"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authorities() -> dict[str, str]:
    return {
        "probe": sha256(PROBE), "source": sha256(SOURCE), "strings": sha256(STRINGS),
        "suite_cpp": sha256(SUITE_CPP), "suite_h": sha256(SUITE_H),
        "missing_cpp": sha256(MISSING_CPP), "sdk_header": sha256(SDK_HEADER),
        "installed_binary": sha256(INSTALLED), "build_identity": sha256(BUILD_IDENTITY),
        "install_identity": sha256(INSTALL_IDENTITY), "guard_report": sha256(GUARD_REPORT),
    }


def ae_processes() -> list[str]:
    found = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode == 0:
            found += [f"{name}:{pid}" for pid in run.stdout.split()]
    return found


def compile_and_run(arch: str) -> str:
    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-installed-") as temporary:
        executable = Path(temporary) / "probe"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [_UCRT_CXX, "-std=c++17", "-arch", arch, "-O2", "-isysroot", sdk,
                   "-Wno-pragma-pack", "-Wno-deprecated-declarations"]
        for include in ("Headers", "Headers/SP", "Util", "Resources", "mac/OLMSmoother", "mac/OLMSmoother/Mac"):
            command += ["-I", str(ROOT / include)]
        command += [str(PROBE), str(STRINGS), str(SUITE_CPP), str(MISSING_CPP), "-framework", "Cocoa", "-o", str(executable)]
        build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, text=True, capture_output=True)
        if run.returncode or run.stderr:
            raise RuntimeError(f"probe failed rc={run.returncode}: {run.stdout} {run.stderr}")
        return run.stdout


def generate() -> dict:
    live = authorities()
    if live != PINS:
        raise RuntimeError(f"authority drift: {live}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    stdout = "".join(f"ARCH {arch}\n" + compile_and_run(arch) for arch in ("arm64", "x86_64"))
    if hashlib.sha256(stdout.encode()).hexdigest() != RUN_SHA256:
        raise RuntimeError("probe transcript drift")
    return {
        "schema": "olmsmoother.v1-current-installed-public/1", "status": STATUS,
        "claim_boundary": generate_claim(),
        "authorities": live, "summary": SUMMARY, "run_sha256": RUN_SHA256,
        "run_lines": stdout.splitlines(), "after_effects_processes": [], "scope": SCOPE,
    }


def validate(report: dict) -> None:
    if set(report) != TOP_KEYS or report["schema"] != "olmsmoother.v1-current-installed-public/1" or report["status"] != STATUS:
        raise RuntimeError("schema/status drift")
    if report["authorities"] != PINS or report["summary"] != SUMMARY or report["scope"] != SCOPE:
        raise RuntimeError("authority/summary/scope drift")
    if report["after_effects_processes"] != [] or len(report["run_lines"]) != 14 or report["run_lines"][0] != "ARCH arm64" or report["run_lines"][7] != "ARCH x86_64":
        raise RuntimeError("process/row drift")
    digest = hashlib.sha256(("\n".join(report["run_lines"]) + "\n").encode()).hexdigest()
    if report["run_sha256"] != RUN_SHA256 or digest != RUN_SHA256:
        raise RuntimeError("transcript drift")
    if report["claim_boundary"] != generate_claim():
        raise RuntimeError("claim drift")


def generate_claim() -> str:
    return "Both current installed Universal slices of OLMSmoother v1 match their source-built real-SDK Classic entry for three representative fixed-source cells and two fail-closed controls per slice. The x86_64 route runs under Rosetta. This is AE-free dlopen evidence, not the complete admission union or native-After-Effects evidence."


def markdown(report: dict) -> str:
    return f"# OLMSmoother v1 current installed public replay (2026-08-13)\n\nStatus: `{STATUS}`\n\n- Both Universal slices, three representative fixed-source Classic cells per slice: exact.\n- Source mutation and Classic PF32 controls: fail-closed and untouched per slice.\n- x86_64 runs under Rosetta; AE was not launched.\n\nBoundary: {report['claim_boundary']}\n"


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
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if fresh != persisted or MARKDOWN.read_text() != markdown(persisted):
            raise RuntimeError("persisted report drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
