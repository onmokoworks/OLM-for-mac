#!/usr/bin/env python3
"""Contract and archive smoke test for the OLMBlur dual-depth Windows package."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "refs/reference_requests/olmblur_windows_software_dual_depth_canonical_recapture_20260711.zip"
PREFIX = "olmblur_windows_software_dual_depth_canonical_recapture_20260711/"
HASH = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def main() -> int:
    with zipfile.ZipFile(PACKAGE) as archive:
        names = {name.removeprefix(PREFIX) for name in archive.namelist() if name.startswith(PREFIX)}
        read = lambda name: archive.read(PREFIX + name).decode("utf-8")
        manifest = json.loads(read("manifest.json"))
        ps = read("run_olmblur_dual_depth.ps1")
        required = {"manifest.json", "README.md", "render_olmblur_case.jsx", "run_olmblur_dual_depth.ps1"}
        required |= {f"inputs/case_{i:04d}_before_effects.png" for i in range(1, 8)}
        required |= {f"expected_8bpc/case_{i:04d}.png" for i in range(1, 8)}
        required |= {f"lanes/{lane}/{file}" for lane in ("8bpc", "32bpc") for file in ("request_manifest.json", "reference_manifest.json")}
        missing = sorted(required - names)
        if missing: raise SystemExit("missing entries: " + ", ".join(missing))
        assert manifest["plugin"]["required_sha256"] == HASH
        assert manifest["cases"] == [f"case_{i:04d}" for i in range(1, 8)]
        assert manifest["lanes"]["8bpc_png"]["bits_per_channel"] == 8
        assert manifest["lanes"]["32bpc_float32_rgba_exr"]["bits_per_channel"] == 32
        assert manifest["lanes"]["32bpc_float32_rgba_exr"]["output"] == {"container_format": "OpenEXR", "compression": "none", "sample_type": "float", "channel_order": "RGBA", "channel_count": 4}
        assert "Get-FileHash" in ps and "hash_mismatch" in ps and "wrong_exr_template" in ps and "no_effect_control_failed" in ps
        assert "OLMBlur OpenEXR RGBA Float32 No Compression" in ps and "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT" in ps
        assert "ADBE Force CPU GPU" in read("render_olmblur_case.jsx") and "skip = true" in read("render_olmblur_case.jsx")
        assert len(json.loads(read("lanes/32bpc/reference_manifest.json")[0:]) ["cases"]) == 7
    print(f"[OK] {PACKAGE}")
    print("[SUMMARY] archive=valid cases=7 lanes=2 hash_gate=present software=required linear_blending=false exr=float32/RGBA/no-compression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
