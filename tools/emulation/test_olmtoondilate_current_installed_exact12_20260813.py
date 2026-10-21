#!/usr/bin/env python3
"""Replay the exact-12 ToonDilate matrix through the current installed binary."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROBE_SOURCE = ROOT / "tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp"
MAC_RUNNER = ROOT / "tools/emulation/test_olmtoondilate_same_source_mac_public_20260813.py"
PAIRED = ROOT / "refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json"
INSTALL = ROOT / "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
REPORT = ROOT / "refs/conformance/olmtoondilate_current_installed_exact12_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olmtoondilate_current_installed_exact12_20260813.md"

SOURCE_SHA = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"
PROBE_SHA = "687358e977691fe311b3cd3444796ef70e12c00eb6dce3accebef6afcb45df4a"
MAC_RUNNER_SHA = "d4e42d0b3d40b81c120ac68f527283cf7b0405ed4121979818902ce753a8188d"
PAIRED_SHA = "80b4e05d844a33687f0d282037fd360898f99a2cf1eca469e68bf8accafee5c2"
INSTALL_SHA = "a44987234e57fb12dc23f0c8819689560d40ba527e46781bb796bec33dc91f09"
IDENTITY_SHA = "9d7402a37c9e4e5204860b0bcff7efed00708cb469e26a9d422a0c3401775bcd"
INSTALLED_SHA = "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e"
CASES_SHA = "2501ff8739f369ee3b5f6a4606b545550d0433f092d7bb64ca1af9c1f1e78534"
GATES_SHA = "b27ea71bdfa416f5fc09ceb25eadcfd0674494ca8ca39968c08489b05b560e0f"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("toon_mac_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        result = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed: {name}")
        found += [f"{name}:{pid}" for pid in result.stdout.split() if pid.isdigit()]
    return found


def compile_and_run(arch: str) -> dict[str, Any]:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("installed exact12 replay requires Apple Silicon macOS")
    compiler = shutil.which("clang++")
    xcrun = shutil.which("xcrun")
    if not compiler or not xcrun:
        raise RuntimeError("clang++/xcrun unavailable")
    sdk = subprocess.check_output([xcrun, "--show-sdk-path"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="toon_installed_exact12_") as temporary:
        probe = Path(temporary) / "probe"
        build = subprocess.run([
            compiler, "-std=c++17", "-O2", "-arch", arch, "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(PROBE_SOURCE), "-o", str(probe),
        ], cwd=ROOT, text=True, capture_output=True)
        if build.returncode:
            raise RuntimeError("probe compile failed: " + build.stderr)
        run = subprocess.run([str(probe), str(INSTALLED)], cwd=ROOT, text=True, capture_output=True)
        if run.returncode:
            raise RuntimeError("installed replay failed: " + run.stdout + run.stderr)
        return json.loads(run.stdout)


def generate() -> dict[str, Any]:
    pins = {
        "production_source": sha256(SOURCE),
        "probe_source": sha256(PROBE_SOURCE),
        "mac_validator": sha256(MAC_RUNNER),
        "paired_closure": sha256(PAIRED),
        "install_closure": sha256(INSTALL),
        "accepted_identity": sha256(IDENTITY),
        "installed_binary": sha256(INSTALLED),
    }
    expected = {
        "production_source": SOURCE_SHA,
        "probe_source": PROBE_SHA,
        "mac_validator": MAC_RUNNER_SHA,
        "paired_closure": PAIRED_SHA,
        "install_closure": INSTALL_SHA,
        "accepted_identity": IDENTITY_SHA,
        "installed_binary": INSTALLED_SHA,
    }
    if pins != expected:
        raise RuntimeError(f"authority drift: {pins}")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"AE-family process running: {processes}")
    validator = load_module(MAC_RUNNER)
    raw_by_arch = {arch: compile_and_run(arch) for arch in ("arm64", "x86_64")}
    gates_by_arch = {arch: validator.validate_cases(raw) for arch, raw in raw_by_arch.items()}
    raw = raw_by_arch["arm64"]
    gates = gates_by_arch["arm64"]
    if raw_by_arch["x86_64"]["cases"] != raw["cases"] or gates_by_arch["x86_64"] != gates:
        raise RuntimeError("installed Universal slice exact12 relations differ")
    paired = json.loads(PAIRED.read_text())
    expected_rows = {
        row["id"]: (row["shared"]["input_active_sha256"], row["shared"]["output_active_sha256"], row["shared"]["input_payload_sha256"], row["shared"]["output_payload_sha256"])
        for row in paired["paired_cells"]
    }
    installed_rows = {
        row["id"]: (row["input_active_sha256"], row["output_active_sha256"], row["input_payload_sha256"], row["output_payload_sha256"])
        for row in raw["cases"]
    }
    if installed_rows != expected_rows:
        raise RuntimeError("installed rows differ from paired Windows/Mac authority")
    cases = [{
        "id": row["id"],
        "input_active_sha256": row["input_active_sha256"],
        "output_active_sha256": row["output_active_sha256"],
        "input_payload_sha256": row["input_payload_sha256"],
        "output_payload_sha256": row["output_payload_sha256"],
        "raw_exact": row["raw_exact"],
        "input_storage_immutable": row["input_storage_immutable"],
        "output_padding_exact": row["output_padding_exact"],
        "world_headers_immutable": row["input_header_immutable"] and row["output_header_immutable"],
        "callbacks": row["callbacks"],
    } for row in raw["cases"]]
    return {
        "schema": "olmtoondilate.current-installed-exact12/1",
        "status": "pass_current_installed_exact12_against_paired_windows_public_owner",
        "identities": pins,
        "installed_binary": str(INSTALLED),
        "architectures": ["arm64", "x86_64"],
        "architecture_relations": {
            arch: {"case_count": 12, "cases_sha256": canonical([{
                "id": row["id"], "input_active_sha256": row["input_active_sha256"],
                "output_active_sha256": row["output_active_sha256"],
                "input_payload_sha256": row["input_payload_sha256"],
                "output_payload_sha256": row["output_payload_sha256"],
                "raw_exact": row["raw_exact"], "input_storage_immutable": row["input_storage_immutable"],
                "output_padding_exact": row["output_padding_exact"],
                "world_headers_immutable": row["input_header_immutable"] and row["output_header_immutable"],
                "callbacks": row["callbacks"],
            } for row in raw_by_arch[arch]["cases"]]), "validation_gates_sha256": canonical(gates_by_arch[arch])}
            for arch in ("arm64", "x86_64")
        },
        "matrix": {"depths": [8, 16, 32], "families": ["copy", "fractional", "tie_semialpha", "high_downsample"], "case_count": 12},
        "cases": cases,
        "cases_sha256": canonical(cases),
        "validation_gates": gates,
        "validation_gates_sha256": canonical(gates),
        "after_effects_processes": [],
        "scope": {
            "installed_public_effectmain_dlopen": True,
            "installed_arm64": True,
            "installed_x86_64": True,
            "windows_public_owner_relation_inherited_from_paired_closure": True,
            "after_effects_launched": False,
            "native_after_effects_host_claim": False,
            "unlisted_tuple_or_source_claim": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {"schema", "status", "identities", "installed_binary", "architectures", "architecture_relations", "matrix", "cases", "cases_sha256", "validation_gates", "validation_gates_sha256", "after_effects_processes", "scope"}:
        raise RuntimeError("top-level schema drift")
    if report["schema"] != "olmtoondilate.current-installed-exact12/1" or report["status"] != "pass_current_installed_exact12_against_paired_windows_public_owner":
        raise RuntimeError("status drift")
    if report["identities"] != {
        "production_source": SOURCE_SHA, "probe_source": PROBE_SHA, "mac_validator": MAC_RUNNER_SHA,
        "paired_closure": PAIRED_SHA, "install_closure": INSTALL_SHA,
        "accepted_identity": IDENTITY_SHA, "installed_binary": INSTALLED_SHA,
    }:
        raise RuntimeError("identity drift")
    if report["matrix"] != {"depths": [8, 16, 32], "families": ["copy", "fractional", "tie_semialpha", "high_downsample"], "case_count": 12}:
        raise RuntimeError("matrix drift")
    if report["architectures"] != ["arm64", "x86_64"] or report["architecture_relations"] != {
        arch: {"case_count": 12, "cases_sha256": CASES_SHA, "validation_gates_sha256": GATES_SHA}
        for arch in ("arm64", "x86_64")
    }:
        raise RuntimeError("architecture relation drift")
    expected_ids = [f"PF{depth}_{family}" for depth in (8, 16, 32) for family in ("copy", "fractional", "tie_semialpha", "high_downsample")]
    if len(report["cases"]) != 12 or [row["id"] for row in report["cases"]] != expected_ids:
        raise RuntimeError("case set drift")
    if canonical(report["cases"]) != report["cases_sha256"] or report["cases_sha256"] != CASES_SHA:
        raise RuntimeError("canonical case digest drift")
    row_keys = {"id", "input_active_sha256", "output_active_sha256", "input_payload_sha256", "output_payload_sha256", "raw_exact", "input_storage_immutable", "output_padding_exact", "world_headers_immutable", "callbacks"}
    if any(set(row) != row_keys or not row["raw_exact"] or not row["input_storage_immutable"] or not row["output_padding_exact"] or not row["world_headers_immutable"] for row in report["cases"]):
        raise RuntimeError("case claim drift")
    if canonical(report["validation_gates"]) != report["validation_gates_sha256"] or report["validation_gates_sha256"] != GATES_SHA:
        raise RuntimeError("validation gate digest drift")
    if report["after_effects_processes"] != []:
        raise RuntimeError("AE process boundary drift")
    if report["scope"] != {
        "installed_public_effectmain_dlopen": True,
        "installed_arm64": True,
        "installed_x86_64": True,
        "windows_public_owner_relation_inherited_from_paired_closure": True,
        "after_effects_launched": False,
        "native_after_effects_host_claim": False,
        "unlisted_tuple_or_source_claim": False,
    }:
        raise RuntimeError("scope drift")


def markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OLMToonDilate current installed exact-12 replay (2026-08-13)", "",
        f"Status: `{report['status']}`", "",
        "Both Universal slices of the current accepted installed executable `5bbe6931...9036e` were dlopened and executed through public `EffectMain` SmartPreRender → SmartRender for the same four source families at PF8/PF16/PF32. All 12 active and padded payload hashes per slice equal the pinned Windows-public-owner/Mac-public paired closure; input storage and world headers are unchanged and output padding is exact. x86_64 runs under Rosetta.", "",
        "Boundary: AE-free installed-binary execution only. It launches no After Effects process and does not promote any unlisted tuple/source or claim native-AE pixels.", "",
    ])


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
            raise RuntimeError("persisted installed exact12 report missing")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("persisted installed exact12 differs from live replay")
    print("PASS_TOONDILATE_CURRENT_INSTALLED_EXACT12_AE_FREE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_TOONDILATE_CURRENT_INSTALLED_EXACT12: {exc}", file=sys.stderr)
        raise
