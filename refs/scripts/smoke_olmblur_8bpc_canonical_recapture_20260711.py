#!/usr/bin/env python3
"""Static smoke test for the hash-pinned OLMBlur recapture package."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "refs/reference_requests/olmblur_windows_software_8bpc_aex_canonical_recapture_20260711.zip"
REQUIRED_HASH = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
PREFIX = "olmblur_windows_software_8bpc_aex_canonical_recapture_20260711/"


def main() -> int:
    if not PACKAGE.is_file():
        raise SystemExit(f"missing package: {PACKAGE}")
    with zipfile.ZipFile(PACKAGE) as archive:
        names = set(archive.namelist())
        def read(name: str) -> str:
            return archive.read(PREFIX + name).decode("utf-8")
        manifest = json.loads(read("manifest.json"))
        ps = read("run_olmblur_recapture.ps1")
        jsx = read("render_olmblur_case.jsx")
        required = {"manifest.json", "README.md", "run_olmblur_recapture.ps1", "render_olmblur_case.jsx"}
        for case in range(1, 8):
            required.add(f"inputs/case_{case:04d}_before_effects.png")
            required.add(f"expected/case_{case:04d}.png")
        actual = {name.removeprefix(PREFIX) for name in names if name.startswith(PREFIX)}
        missing = sorted(required - actual)
        if missing:
            raise SystemExit("missing entries: " + ", ".join(missing))
        assert manifest["plugin"]["required_sha256"] == REQUIRED_HASH
        assert [case["id"] for case in manifest["cases"]] == [f"case_{i:04d}" for i in range(1, 8)]
        assert manifest["renderer_required"] == "Software"
        assert manifest["project"]["bits_per_channel"] == 8
        assert "hash_mismatch" in ps and "Get-FileHash" in ps and "AfterFX" in ps
        assert "OLM_AE_FORCE_SOFTWARE" in ps
        assert "ADBE Force CPU GPU" not in ps
        assert "ADBE Force CPU GPU" in jsx
        assert "skip = true" in jsx
        assert "GPU Rendering" not in jsx
    print(f"[OK] {PACKAGE}")
    print("[SUMMARY] archive=valid cases=7 hash_gate=present renderer=Software bpc=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
