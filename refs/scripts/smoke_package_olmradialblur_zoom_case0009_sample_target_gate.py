#!/usr/bin/env python3
"""Smoke-test the grounded RadialBlur sampler-target package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmradialblur_zoom_case0009_sample_target_gate_20260710"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_target_gate_") as tmp:
        output = Path(tmp) / "request.zip"
        subprocess.run(["python3", "scripts/package_olmradialblur_zoom_case0009_sample_target_gate_20260710.py", "--output", str(output)], cwd=ROOT, check=True)
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            names = set(archive.namelist())
            assert "artifacts/sample_target_gate.cdb" in names
            hook = archive.read("artifacts/sample_target_gate.cdb").decode("utf-8")
            assert "@ebx == 7 || @ebx == 8 || @ebx == 24" in hook
            assert hook.count("OLMRadialBlur+0x5e") == 2
            result = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
            assert result["results"][0]["request_id"] == REQUEST
    print("[OK] RadialBlur sampler-target gate package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
