#!/usr/bin/env python3
"""Smoke-test the focused RadialBlur raw hook-liveness package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmradialblur_zoom_case0009_hook_liveness_20260710"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_liveness_package_") as tmp:
        output = Path(tmp) / "request.zip"
        subprocess.run(["python3", "scripts/package_olmradialblur_zoom_case0009_hook_liveness_20260710.py", "--output", str(output)], cwd=ROOT, check=True)
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            names = set(archive.namelist())
            for name in ("README_RUNTIME_TRACE.md", "RETURN_RUNTIME_TRACE_TEMPLATE.json", "artifacts/hook_liveness.cdb", "artifacts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1", "scripts/ae_render_single_case.jsx"):
                assert name in names, name
            result = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            assert result["results"][0]["request_id"] == REQUEST
            hook = archive.read("artifacts/hook_liveness.cdb").decode("utf-8")
            assert hook.count("bp /1 OLMRadialBlur+") == 4
    print("[OK] RadialBlur hook-liveness package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
