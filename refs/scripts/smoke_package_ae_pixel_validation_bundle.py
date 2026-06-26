#!/usr/bin/env python3
"""Smoke-test AE pixel validation bundle packaging."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def make_request_zip(path: Path, request_id: str, effect_name: str, case_count: int) -> None:
    manifest = {
        "kind": "olm_ae_pixel_validation_request",
        "request_id": request_id,
        "effect_name": effect_name,
        "cases": [{"id": f"case_{index:04d}", "frame": f"case_{index:04d}.png"} for index in range(case_count)],
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{request_id}/request_manifest.json", json.dumps(manifest))
        archive.writestr(f"{request_id}/README.md", "dummy request\n")


def run(cmd: list[object], cwd: Path) -> subprocess.CompletedProcess:
    printable = " ".join(str(part) for part in cmd)
    print(f"+ {printable}")
    return subprocess.run([str(part) for part in cmd], cwd=cwd, text=True)


def main() -> int:
    repo = repo_root()
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_bundle_smoke_") as tmp:
        tmp_path = Path(tmp)
        request_dir = tmp_path / "requests"
        request_dir.mkdir()
        make_request_zip(request_dir / "bitdepth16_olmblur_exact.zip", "ae_pixel_bitdepth16_olmblur_exact", "OLM Blur", 7)
        make_request_zip(
            request_dir / "bitdepth16_olmcolorkey_exact.zip",
            "ae_pixel_bitdepth16_olmcolorkey_exact",
            "OLM Color Key",
            9,
        )
        output = tmp_path / "bundle.zip"
        proc = run(
            [
                sys.executable,
                repo / "scripts" / "package_ae_pixel_validation_bundle.py",
                "--request-dir",
                request_dir,
                "--output",
                output,
                "--label",
                "smoke_16bpc",
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode
        if not zipfile.is_zipfile(output):
            print("[FAIL] output is not a zip")
            return 1
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            if "README.md" not in names or "bundle_manifest.json" not in names:
                print("[FAIL] bundle missing README.md or bundle_manifest.json")
                return 1
            manifest = json.loads(archive.read("bundle_manifest.json"))
            if manifest.get("kind") != "olm_ae_pixel_validation_bundle":
                print("[FAIL] bad bundle kind")
                return 1
            if manifest.get("request_count") != 2:
                print("[FAIL] wrong request count")
                return 1
            if "requests/bitdepth16_olmblur_exact.zip" not in names:
                print("[FAIL] missing copied request zip")
                return 1
            readme = archive.read("README.md").decode("utf-8")
            if "verify_ae_pixel_validation_batch.py" not in readme:
                print("[FAIL] README missing batch verify command")
                return 1

    print("[OK] AE pixel validation bundle smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
