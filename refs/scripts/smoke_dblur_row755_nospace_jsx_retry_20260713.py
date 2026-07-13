#!/usr/bin/env python3
"""Fail-closed structural smoke for the row755 no-space JSX retry package."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "refs/runtime_trace_support/olmdirectionalblur_row755_nospace_jsx_retry_20260713"
PACKAGE = ROOT / "refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_nospace_jsx_retry_20260713.zip"
PREFIX = "olmdirectionalblur_row755_nospace_jsx_retry_20260713/"


def main() -> int:
    manifest = json.loads((SUPPORT / "runtime_trace_package_manifest.json").read_text())
    runner = (SUPPORT / "run_alpha_fade_row755.ps1").read_text()

    assert manifest["effect"] == "OLMDirectionalBlur"
    assert "nospace-jsx-nested-cdb-retry" in manifest["profile"]
    for token in (
        "Get-Process -Name 'AfterFX'",
        "$env:PUBLIC",
        "OLMTrace",
        "Copy-Item",
        "capture_at_5554.cdb",
        "-m",
        "-r",
        "ready marker",
        "exact_bind_failure",
    ):
        assert token in runner, token
    assert "if($jsxLaunch -match '\\s')" in runner
    template = (SUPPORT / "row755_capture.cdb.in").read_text()
    assert "$><__CAPTURE_SCRIPT__" in template
    assert "&&" not in template
    assert "__CHUNK_COMMANDS__" not in template

    expected = {
        PREFIX + "runtime_trace_package_manifest.json",
        PREFIX + "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        PREFIX + "run_alpha_fade_row755.ps1",
        PREFIX + "row755_capture.cdb.in",
        PREFIX + "README.md",
        PREFIX + "case/ae_render_single_case.jsx",
        PREFIX + "case/request_manifest.json",
        PREFIX + "case/reference_manifest.json",
    }
    with zipfile.ZipFile(PACKAGE) as archive:
        names = set(archive.namelist())
        assert expected <= names, sorted(expected - names)
        packed_runner = archive.read(PREFIX + "run_alpha_fade_row755.ps1").decode()
        assert packed_runner == runner

    print("PASS dblur row755 no-space JSX retry package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
