#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUEST = "olmradialblur_zoom_case0009_sampler_args_20260710"

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_sampler_args_") as tmp:
        out = Path(tmp) / "request.zip"
        subprocess.run(["python3", "scripts/package_olmradialblur_zoom_case0009_sampler_args_20260710.py", "--output", str(out)], cwd=ROOT, check=True)
        with zipfile.ZipFile(out) as archive:
            assert archive.testzip() is None
            hook = archive.read("artifacts/sampler_args.cdb").decode("utf-8")
            assert "OLMRadialBlur+0x5e68" in hook and "OLMRadialBlur+0x5e6d" in hook
            assert "@ebx == 7 || @ebx == 8 || @ebx == 24" in hook
            assert json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))["results"][0]["request_id"] == REQUEST
    print("[OK] RadialBlur sampler-argument package smoke passed")
    return 0

if __name__ == "__main__": raise SystemExit(main())
