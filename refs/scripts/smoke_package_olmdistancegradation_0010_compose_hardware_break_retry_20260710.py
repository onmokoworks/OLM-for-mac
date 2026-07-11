#!/usr/bin/env python3
"""Smoke-test the dormant DG single-site hardware-breakpoint successor."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_0010_compose_single_site_hardware_break_retry_20260710"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="dg_hw_break_package_") as tmp:
        archive_path = Path(tmp) / "request.zip"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/package_olmdistancegradation_0010_compose_single_site_followup_20260710.py",
                "--hardware-breakpoints",
                "--output",
                str(archive_path),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode:
            return proc.returncode
        with zipfile.ZipFile(archive_path) as archive:
            manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
            template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")
            launcher = archive.read(
                "artifacts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1"
            ).decode("utf-8")
        action = manifest["runtime_actions"][0]
        result = template["results"][0]
        if action.get("request_id") != REQUEST_ID or result.get("request_id") != REQUEST_ID:
            raise AssertionError("hardware successor request id mismatch")
        if "-UseHardwareBreakpoints" not in readme:
            raise AssertionError("handoff does not enable hardware breakpoints")
        for token in ("[switch]$UseHardwareBreakpoints", "'ba e 1'", "ENTRY_BREAKPOINT", "SITE_BREAKPOINT"):
            if token not in launcher:
                raise AssertionError(f"launcher missing hardware breakpoint token: {token}")
        observations = result.get("observations", {})
        if observations.get("hardware_breakpoints_used") is not True:
            raise AssertionError("return template does not bind hardware breakpoint mode")
    print(f"[OK] {REQUEST_ID} package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
