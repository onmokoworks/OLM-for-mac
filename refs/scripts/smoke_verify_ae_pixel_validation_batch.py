#!/usr/bin/env python3
"""Smoke-test batch verification of AE pixel validation returns."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[object], cwd: Path) -> subprocess.CompletedProcess:
    printable = " ".join(str(part) for part in cmd)
    print(f"+ {printable}")
    return subprocess.run([str(part) for part in cmd], cwd=cwd, text=True)


def request_case_frames(request_zip: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(request_zip) as archive:
        manifest_name = next(name for name in archive.namelist() if name.endswith("request_manifest.json"))
        data = json.loads(archive.read(manifest_name))
    return [(case.get("case_id", case.get("id", "")), case["frame"]) for case in data["cases"]]


def main() -> int:
    repo = repo_root()
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_batch_smoke_") as tmp:
        tmp_path = Path(tmp)
        request_dir = tmp_path / "requests"
        result_dir = tmp_path / "returns"
        request_dir.mkdir()
        result_dir.mkdir()

        specs = [
            (
                "bitdepth16_olmblur_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
            ),
            (
                "bitdepth16_olmdistancegradation_blur_exact",
                repo
                / "refs"
                / "win_references"
                / "olm_bitdepth_16bpc_normalized_exact_20260625"
                / "OLMbit-depthconformancebatch",
            ),
        ]

        for preset, reference in specs:
            request_zip = request_dir / f"{preset}.zip"
            proc = run(
                [
                    sys.executable,
                    repo / "scripts" / "package_ae_pixel_validation_request.py",
                    "--preset",
                    preset,
                    "--output",
                    request_zip,
                ],
                repo,
            )
            if proc.returncode != 0:
                return proc.returncode

            result_root = tmp_path / f"result_{preset}"
            candidate = result_root / "rendered"
            candidate.mkdir(parents=True)
            for _case_id, frame in request_case_frames(request_zip):
                shutil.copy2(reference / frame, candidate / frame)

            # Deliberately use a different name shape to test alias matching.
            result_zip = result_dir / f"returned_{preset}_mac_ae.zip"
            with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in result_root.rglob("*"):
                    archive.write(path, path.relative_to(result_root))

        proc = run(
            [
                sys.executable,
                repo / "scripts" / "verify_ae_pixel_validation_batch.py",
                request_dir,
                result_dir,
                "--run-dir",
                tmp_path / "batch_run",
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] AE pixel validation batch smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
