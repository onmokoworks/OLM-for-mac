#!/usr/bin/env python3
"""Compile the common-core OLMDistanceGradation case_0026 16bpc witness."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.core import canonical_json, deterministic_zip, sha256_file  # noqa: E402


SPEC = ROOT / "refs/windows_witness_specs/olmdistancegradation_case0026_16bpc_livefield_20260713/witness-spec.json"
PNG_INSPECTOR = SPEC.parent / "inspect_exported_png16.py"
PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmdistancegradation_case0026_20260713"
ARCHIVE = PACKAGE.with_suffix(".zip")

LAUNCHER_OLD = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
"""
LAUNCHER_NEW = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
$exportInspector = Join-Path $PackageRoot 'scripts\\inspect_exported_png16.py'
$exportPng = Join-Path $work 'exports\\olmdistancegradation_extended__case_0026\\case_0026.png'
$exportResult = Join-Path $work 'ae_result_olmdistancegradation_extended__case_0026.json'
if ($validateCode -eq 0 -and $validated.status -eq 'answered') {
  & py -3 $exportInspector --contract $contractPath --status $statusPath --identity $identityPath --ae-result $exportResult --input $exportPng --output $statusPath
  $exportCode = $LASTEXITCODE
  $validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
  if ($validated.status -eq 'answered' -and ($exportCode -ne 0 -or !$validated.exported_png)) {
    $validated = Failure 'export_png_validation' 'RGBA16 PNG inspector failed to return a bound export witness' @('exported_png') "inspector_exit=$exportCode"
  }
} else {
  $exportCode = 2
}
Finish $validated $(if ($validateCode -eq 0 -and $exportCode -eq 0 -and $validated.status -eq 'answered' -and $validated.exported_png) { 0 } else { 2 })
"""


def add_export_validator(package: Path, archive: Path) -> None:
    inspector_destination = package / "scripts/inspect_exported_png16.py"
    shutil.copy2(PNG_INSPECTOR, inspector_destination)

    launcher = package / "artifacts/run_witness.ps1"
    launcher_text = launcher.read_text(encoding="utf-8")
    if launcher_text.count(LAUNCHER_OLD) != 1:
        raise RuntimeError("shared launcher completion anchor drifted")
    launcher.write_text(launcher_text.replace(LAUNCHER_OLD, LAUNCHER_NEW), encoding="utf-8", newline="\n")

    manifest_path = package / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = []
    for path in sorted(
        (path for path in package.rglob("*") if path.is_file() and path != manifest_path),
        key=lambda item: item.relative_to(package).as_posix(),
    ):
        inventory.append(
            {
                "path": path.relative_to(package).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest["files"] = inventory
    manifest_path.write_bytes(canonical_json(manifest))
    deterministic_zip(package, archive)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    zip_path = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    command = [
        sys.executable,
        "-m",
        "tools.windows_witness.compile",
        str(SPEC),
        "--output-dir",
        str(output_dir),
        "--zip",
        str(zip_path),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    result = json.loads(completed.stdout)
    add_export_validator(output_dir, zip_path)
    print(json.dumps({"status": "ok", "compiler": "tools.windows_witness.compile", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
