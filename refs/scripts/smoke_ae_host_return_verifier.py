#!/usr/bin/env python3
"""Smoke-test scripts/verify_ae_host_return.py with a synthetic return bundle."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_ae_validation_result_verifier import base_result
from smoke_olm_handoff_package_verifier import (
    make_handoff_package,
    make_mac_package,
    make_reference_package,
)


def extract_zip(source: Path, dest: Path) -> Path:
    with zipfile.ZipFile(source) as archive:
        archive.extractall(dest)
    roots = [path for path in dest.iterdir() if path.is_dir() and path.name != "__MACOSX"]
    return roots[0] if len(roots) == 1 else dest


def copy_expected_as_returned(request_zip: Path, result_dir: Path) -> None:
    request_root = extract_zip(request_zip, result_dir.parent / "_request_extract")
    manifest = json.loads((request_root / "request_manifest.json").read_text(encoding="utf-8"))
    target = result_dir / "olmblur"
    target.mkdir()
    for case in manifest["cases"]:
        frame = case["frame"]
        shutil.copy2(request_root / "expected" / frame, target / frame)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    verifier = repo / "scripts" / "verify_ae_host_return.py"

    with tempfile.TemporaryDirectory(prefix="olm_ae_host_return_smoke_") as tmp:
        tmp_path = Path(tmp)
        mac_zip = make_mac_package(repo, tmp_path)
        reference_zip = make_reference_package(tmp_path)
        handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip)

        mac_root = extract_zip(mac_zip, tmp_path / "mac_extract")
        request_zip = mac_root / "AE_PIXEL_VALIDATION" / "olmblur_request.zip"

        result_root = tmp_path / "returned"
        result_root.mkdir()
        (result_root / "AE_VALIDATION_RESULT.json").write_text(
            json.dumps(base_result(), indent=2),
            encoding="utf-8",
        )
        copy_expected_as_returned(request_zip, result_root)

        result_zip = tmp_path / "returned_ae_host.zip"
        with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in result_root.rglob("*"):
                archive.write(path, path.relative_to(result_root))

        proc = subprocess.run(
            [
                sys.executable,
                str(verifier),
                str(handoff_zip),
                str(result_zip),
                "--require-all-pass",
                "--run-dir",
                str(tmp_path / "verify_run"),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] AE host return verifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
