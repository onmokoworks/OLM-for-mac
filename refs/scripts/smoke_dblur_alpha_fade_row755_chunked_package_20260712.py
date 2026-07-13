#!/usr/bin/env python3
"""Verify the chunked DirectionalBlur row-755 retry package contract."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "runtime_trace_packages" / "olmdirectionalblur_alpha_fade_fullrender_row755_chunked_capture_20260712"
ZIP = PACKAGE.with_suffix(".zip")


def main() -> int:
    manifest = json.loads((PACKAGE / "runtime_trace_package_manifest.json").read_text())
    assert manifest["request_id"] == "olmdirectionalblur_alpha_fade_fullrender_row755_20260712"
    assert manifest["profile"].endswith("chunked-capture")
    assert "21 chunks" in manifest["binding"]["chunk_capture"]
    runner = (PACKAGE / "run_alpha_fade_row755.ps1").read_text()
    assert "$chunkPixels=16" in runner
    assert "$chunkCount=21" in runner and "$focusPixels=334" in runner
    assert "$jsxArg='\"'+$jsx.Replace" in runner
    assert "-ArgumentList @('-m','-r',$jsxArg)" in runner
    assert ".Replace(\"`r`n\",'; ')" in runner
    assert "__CHUNK_COMMANDS__" in (PACKAGE / "row755_capture.cdb.in").read_text()
    assert "capture_listing.json" in runner
    assert "Length -eq 5344" in runner and "Length -eq 1336" in runner
    cdb = (PACKAGE / "row755_capture.cdb.in").read_text()
    assert cdb.count("__CHUNK_COMMANDS__") == 1
    for token in ("0x4d84", "DBR_ROW_RANGE", "worker_hits", "row755_covered", "params_mismatch"):
        assert token in cdb, token
    for token in ("$rangesValid", "$row755Seen", "artifact_root='.'", "capture_listing='capture_listing.json'"):
        assert token in runner, token
    assert "755-dwo(@$t6+0x8098)" in cdb
    assert "747-dwo(@$t6+0x809c)" in cdb
    for path in PACKAGE.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".ps1", ".in"}:
            text = path.read_text(errors="replace")
            assert "/Users/" not in text and "\\Users\\onmk" not in text
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        for required in ("README.md", "runtime_trace_package_manifest.json", "row755_capture.cdb.in", "run_alpha_fade_row755.ps1"):
            assert any(name.endswith("/" + required) or name == required for name in names)
    pixels = [min(16, 334 - index * 16) for index in range(21)]
    assert pixels[-1] == 14 and sum(pixels) == 334
    assert sum(value * 16 for value in pixels) == 5344
    assert sum(value * 4 for value in pixels) == 1336
    print("[OK] DirectionalBlur row-755 chunked capture package integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
