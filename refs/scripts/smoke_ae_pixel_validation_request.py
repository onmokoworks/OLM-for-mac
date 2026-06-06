#!/usr/bin/env python3
"""Smoke-test AE pixel validation request packaging and verification."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(cmd: list[object], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [str(part) for part in cmd],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print("$", " ".join(str(part) for part in cmd))
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_smoke_") as tmp:
        tmp_path = Path(tmp)
        presets = [
            (
                "olmblur",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
                ("case_0001", "case_0002", "case_0003", "case_0004", "case_0005", "case_0006", "case_0007"),
            ),
            (
                "olmcolorkey",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMColorKey",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0008",
                    "case_0009",
                ),
            ),
            (
                "olmtoondilate",
                repo / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate",
                ("case_0001", "case_0002", "case_0003"),
            ),
            (
                "olmdistancegradation",
                repo / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
                (
                    "case_0001",
                    "case_0002",
                    "case_0003",
                    "case_0004",
                    "case_0005",
                    "case_0006",
                    "case_0007",
                    "case_0009",
                    "case_0015",
                    "case_0017",
                    "case_0018",
                    "case_0019",
                ),
            ),
        ]
        for preset, reference, case_ids in presets:
            request_zip = tmp_path / f"{preset}_request.zip"
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

            result_root = tmp_path / f"returned_{preset}"
            result_dir = result_root / "candidate"
            result_dir.mkdir(parents=True)
            for case_id in case_ids:
                shutil.copy2(reference / f"{case_id}.png", result_dir / f"{case_id}.png")

            result_zip = tmp_path / f"returned_{preset}.zip"
            with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in result_root.rglob("*"):
                    archive.write(path, path.relative_to(result_root))

            proc = run(
                [
                    sys.executable,
                    repo / "scripts" / "verify_ae_pixel_validation_result.py",
                    request_zip,
                    result_zip,
                    "--run-dir",
                    tmp_path / f"verify_run_{preset}",
                ],
                repo,
            )
            if proc.returncode != 0:
                return proc.returncode

    print("[OK] AE pixel validation request smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
