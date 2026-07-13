#!/usr/bin/env python3
"""Verify the DG 8bpc package is a reachable liveness probe, not typed proof."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


PACKAGE_DIR = Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_depth_control_20260713")
PACKAGE_ZIP = PACKAGE_DIR.with_suffix(".zip")
RUNNER = PACKAGE_DIR / "artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1"
RVAS = {"1170870", "1170c90"}
HASH = "a" * 64


def parse_fixture(path: Path) -> bool:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^DG8_DEPTH_SUMMARY\s+(.+)$", line)
        if not match:
            continue
        fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", match.group(1)))
        rows[fields.get("rva")] = fields
    if set(rows) != RVAS:
        return False
    return all(
        rows[rva].get("run_id") == "dglive-fixture"
        and rows[rva].get("aex_sha256") == HASH
        and rows[rva].get("hit_count", "").isdigit()
        for rva in RVAS
    )


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    package_dir = root / PACKAGE_DIR
    package_zip = root / PACKAGE_ZIP
    required = {
        "README_RUNTIME_TRACE.md",
        "runtime_trace_package_manifest.json",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1",
        "scripts/ae_render_olmdistancegradation_8bpc_depth_control_queue.jsx",
        "scripts/ae_render_single_case.jsx",
        "fixtures/complete_cdb_stdout.txt",
        "fixtures/missing_rva_cdb_stdout.txt",
    }
    if not package_dir.is_dir() or not package_zip.is_file():
        print("[FAIL] liveness package directory or zip is missing")
        return 1
    files = {p.relative_to(package_dir).as_posix() for p in package_dir.rglob("*") if p.is_file()}
    if not required <= files:
        print(f"[FAIL] package missing: {sorted(required - files)}")
        return 1
    with zipfile.ZipFile(package_zip) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        if names != files:
            print("[FAIL] zip/directory drift")
            return 1
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
    action = manifest["runtime_actions"][0]
    if manifest.get("submission_status") != "ready" or manifest.get("sendable") is not True or set(action["rvas"]) != RVAS:
        print("[FAIL] liveness manifest is not runnable or has the wrong RVA set")
        return 1
    if not parse_fixture(package_dir / "fixtures/complete_cdb_stdout.txt"):
        print("[FAIL] complete liveness fixture rejected")
        return 1
    if parse_fixture(package_dir / "fixtures/missing_rva_cdb_stdout.txt"):
        print("[FAIL] missing-RVA liveness fixture accepted")
        return 1
    runner = RUNNER.read_text(encoding="utf-8")
    for needle in ("-ParseOnly", "DG8_DEPTH_HIT", "DG8_DEPTH_SUMMARY", "Get-FileHash", "sxe ld:DistanceGradation.aex"):
        if needle not in runner:
            print(f"[FAIL] liveness runner missing {needle}")
            return 1
    if "bp /1" in runner or "typed_rgba" in runner or "COMPOSE_IN" in runner or "algorithm proof" in runner.lower():
        print("[FAIL] liveness runner contains typed-boundary or algorithm-proof behavior")
        return 1
    if "hit_count=%u\\\\n" in runner:
        print("[FAIL] liveness summary uses a double-escaped CDB newline")
        return 1
    if "@`$t0" not in runner or ", @\n" in runner:
        print("[FAIL] CDB pseudo-registers are not protected from PowerShell expansion")
        return 1
    for needle in (
        "project_bits_per_channel -ne 8",
        "AE did not render the requested 8bpc case",
        "bp DistanceGradation+0x1170870",
        "bp DistanceGradation+0x1170c90",
    ):
        if needle not in runner:
            print(f"[FAIL] depth-control runner missing {needle}")
            return 1
    embedded_renderer = (package_dir / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
    if "referenceManifest.comp && referenceManifest.comp.bpc" not in embedded_renderer:
        print("[FAIL] embedded AE runner ignores comp.bpc and can silently inherit 32bpc")
        return 1
    readme = (package_dir / "README_RUNTIME_TRACE.md").read_text(encoding="utf-8").lower()
    if "does not" not in readme or "algorithm proof" not in readme:
        print("[FAIL] liveness README does not bound the claim")
        return 1
    print("[OK] DG 8bpc current-AEX depth-control package, reachable parser, and bounded claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
