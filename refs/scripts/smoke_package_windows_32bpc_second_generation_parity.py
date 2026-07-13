#!/usr/bin/env python3
"""Smoke the focused Windows second-generation parity package."""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/package_windows_32bpc_second_generation_parity_20260713.py"
PREFIX = "olm_windows_32bpc_second_generation_parity_20260713/"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_32bpc_second_gen_smoke_") as td:
        archive = Path(td) / "request.zip"
        subprocess.run(["python3", str(SCRIPT), "--output", str(archive)], cwd=ROOT, check=True)
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            required = {
                PREFIX + "run.ps1",
                PREFIX + "render_case.jsx",
                PREFIX + "request_manifest.json",
                PREFIX + "cases/olmcolorkey__case_0002/request_manifest.json",
                PREFIX + "cases/olmtoondilate__case_0001/request_manifest.json",
            }
            assert required <= names
            exrs = [name for name in names if name.endswith("_before_effects.exr")]
            assert len(exrs) == 2
            ps = z.read(PREFIX + "run.ps1").decode("utf-8")
            for token in (
                "OLM_AE_DISABLE_EFFECT",
                "OLM_AE_FORCE_NEW_PROJECT",
                "OLM_AE_FORCE_SOFTWARE",
                "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT",
                "wrong_ae_version",
                "Get-FileHash",
                "$r.output_exr",
                "Compress-Archive",
            ):
                assert token in ps
    print("[OK] focused Windows 32bpc second-generation parity package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
