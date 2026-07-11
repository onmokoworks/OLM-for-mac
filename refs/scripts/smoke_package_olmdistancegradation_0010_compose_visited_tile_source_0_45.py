#!/usr/bin/env python3
"""Verify the visited-tile `(0,45)` source-only DG runtime package."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "refs/runtime_trace_packages/olmdistancegradation_0010_compose_visited_tile_source_0_45_windows_20260710.zip"
REQUEST_ID = "olmdistancegradation_0010_compose_visited_tile_source_0_45_20260710"
CONTRACT = "refs/conformance/olmdistancegradation_0010_compose_visited_tile_source_0_45_contract_20260710.md"


def main() -> int:
    assert zipfile.is_zipfile(ARCHIVE), ARCHIVE
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = set(archive.namelist())
        for name in (CONTRACT, "artifacts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1", "scripts/ae_render_single_case.jsx"):
            assert name in names, name
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        result = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")
    action = manifest["runtime_actions"][0]
    assert action["request_id"] == REQUEST_ID
    assert "(0,45)" in action["command"] and "source at +0x11705f1" in action["command"]
    assert manifest["entrypoint"] == CONTRACT
    observation = result["results"][0]["observations"]
    assert result["results"][0]["request_id"] == REQUEST_ID
    assert observation["target_xy"] == [0, 45]
    assert set(observation["site_runs"]) == {"source"}
    assert "rdx_source_words_u16" in observation["site_runs"]["source"]
    assert "-Site source -X 0 -Y 45" in readme
    print(f"[OK] {REQUEST_ID} package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
