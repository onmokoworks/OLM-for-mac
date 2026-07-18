#!/usr/bin/env python3
"""Compile the real common-core OLMBlur case_0006 Windows witness package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "refs/windows_witness_specs/olmblur_case0006_same_run_20260713/witness-spec.json"
PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmblur_case0006_20260713"
ARCHIVE = PACKAGE.with_suffix(".zip")


def publish_transaction(
    staged_package: Path,
    staged_zip: Path,
    package: Path,
    archive: Path,
    *,
    replace: Callable[[Path, Path], Path] = Path.replace,
) -> None:
    """Install a staged package and ZIP together, restoring both on failure."""

    package.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    package_backup_root = Path(tempfile.mkdtemp(prefix=f".{package.name}.backup.", dir=str(package.parent)))
    archive_backup_root = Path(tempfile.mkdtemp(prefix=f".{archive.name}.backup.", dir=str(archive.parent)))
    package_backup = package_backup_root / "package"
    archive_backup = archive_backup_root / "archive"
    package_was_present = package.exists()
    archive_was_present = archive.exists()
    package_installed = False
    archive_installed = False
    try:
        if package_was_present:
            replace(package, package_backup)
        if archive_was_present:
            replace(archive, archive_backup)
        replace(staged_package, package)
        package_installed = True
        replace(staged_zip, archive)
        archive_installed = True
    except BaseException as publish_error:
        rollback_errors: list[str] = []

        def rollback(label: str, action: Callable[[], object]) -> None:
            try:
                action()
            except BaseException as rollback_error:
                rollback_errors.append(f"{label}: {type(rollback_error).__name__}: {rollback_error}")

        if archive_installed:
            rollback("remove newly installed archive", lambda: archive.unlink())
        if package_installed:
            rollback("remove newly installed package", lambda: shutil.rmtree(package))
        if archive_was_present:
            rollback("restore archive backup", lambda: replace(archive_backup, archive))
        if package_was_present:
            rollback("restore package backup", lambda: replace(package_backup, package))
        rollback("remove package backup root", lambda: shutil.rmtree(package_backup_root))
        rollback("remove archive backup root", lambda: shutil.rmtree(archive_backup_root))
        if rollback_errors:
            publish_error.add_note("Publish rollback diagnostics: " + "; ".join(rollback_errors))
        raise
    else:
        shutil.rmtree(package_backup_root)
        shutil.rmtree(archive_backup_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    zip_path = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    package_staging_root = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging.", dir=str(output_dir.parent)))
    archive_staging_root = Path(tempfile.mkdtemp(prefix=f".{zip_path.name}.staging.", dir=str(zip_path.parent)))
    compile_output_dir = package_staging_root / "package"
    compile_zip_path = archive_staging_root / "package.zip"
    command = [
        sys.executable,
        "-m",
        "tools.windows_witness.compile",
        str(SPEC),
        "--output-dir",
        str(compile_output_dir),
        "--zip",
        str(compile_zip_path),
    ]
    try:
        completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        publish_transaction(compile_output_dir, compile_zip_path, output_dir, zip_path)
    finally:
        if package_staging_root.exists():
            shutil.rmtree(package_staging_root)
        if archive_staging_root.exists():
            shutil.rmtree(archive_staging_root)
    result = json.loads(completed.stdout)
    result["package"] = str(output_dir.resolve())
    result["zip"] = str(zip_path.resolve())
    print(json.dumps({"status": "ok", "compiler": "tools.windows_witness.compile", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
