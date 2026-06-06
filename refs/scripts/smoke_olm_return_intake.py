#!/usr/bin/env python3
"""Smoke-test scripts/intake_olm_return.py for AE-host and Windows-ref returns."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_ae_validation_result_verifier import base_result
from smoke_import_and_check_win_reference import write_synthetic_result
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


def copy_expected_as_returned(request_zip: Path, result_dir: Path, target_name: str) -> None:
    request_root = extract_zip(request_zip, result_dir.parent / f"_request_extract_{target_name}")
    manifest = json.loads((request_root / "request_manifest.json").read_text(encoding="utf-8"))
    target = result_dir / target_name
    target.mkdir()
    for case in manifest["cases"]:
        frame = case["frame"]
        shutil.copy2(request_root / "expected" / frame, target / frame)


def make_ae_host_return(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    mac_zip = make_mac_package(repo, tmp_path)
    reference_zip = make_reference_package(tmp_path)
    handoff_zip = make_handoff_package(tmp_path, mac_zip, reference_zip)
    mac_root = extract_zip(mac_zip, tmp_path / "mac_extract")

    result_root = tmp_path / "ae_returned"
    result_root.mkdir()
    (result_root / "AE_VALIDATION_RESULT.template.json").write_text(
        json.dumps(base_result(), indent=2),
        encoding="utf-8",
    )
    for target_name, zip_name in (
        ("olmblur", "olmblur_request.zip"),
        ("olmcolorkey", "olmcolorkey_request.zip"),
        ("olmtoondilate", "olmtoondilate_request.zip"),
    ):
        copy_expected_as_returned(mac_root / "AE_PIXEL_VALIDATION" / zip_name, result_root, target_name)

    result_zip = tmp_path / "ae_host_return.zip"
    with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in result_root.rglob("*"):
            archive.write(path, path.relative_to(result_root))
    return handoff_zip, result_zip


def make_windows_ref_return(tmp_path: Path) -> tuple[Path, Path, Path]:
    requests_dir = tmp_path / "requests"
    request_path = requests_dir / "synthetic_intake_20260606.json"
    request = {
        "request_id": "synthetic_intake_20260606",
        "effect": {"name": "Synthetic Effect", "match_name": "Synthetic Effect"},
        "render_sets": [
            {
                "id": "SOFTWARE",
                "required": True,
                "project_gpu_accel_type.current_name": "SOFTWARE",
            }
        ],
        "manifest_requirements": [],
        "cases": [{"id": "case_a"}, {"id": "case_b"}],
    }
    requests_dir.mkdir()
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")
    return write_synthetic_result(tmp_path, request), requests_dir, request_path


def run(cmd: list[str], repo: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    return proc.returncode


def run_capture(cmd: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    return proc


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    intake = repo / "scripts" / "intake_olm_return.py"
    with tempfile.TemporaryDirectory(prefix="olm_return_intake_smoke_") as tmp:
        tmp_path = Path(tmp)
        handoff_zip, ae_return_zip = make_ae_host_return(repo, tmp_path)
        win_return_zip, requests_dir, request_path = make_windows_ref_return(tmp_path)

        rc = run(
            [
                sys.executable,
                str(intake),
                str(ae_return_zip),
                "--package",
                str(handoff_zip),
                "--require-all-pass",
                "--require-all-pixel-requests",
                "--run-dir",
                str(tmp_path / "ae_verify_run"),
            ],
            repo,
        )
        if rc != 0:
            return rc

        proc = run_capture(
            [
                sys.executable,
                str(intake),
                str(win_return_zip),
                "--dest-root",
                str(tmp_path / "win_references"),
                "--requests-dir",
                str(requests_dir),
                "--request",
                str(request_path),
                "--set-id",
                "synthetic_return",
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode
        if "next covered reference action" not in proc.stdout:
            print("[FAIL] intake did not print next covered reference action", file=sys.stderr)
            return 1

    print("[OK] OLM return intake smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
