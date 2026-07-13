#!/usr/bin/env python3
"""Compile the common-core OLMRadialBlur case_0009 Windows witness."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713"
SPEC = SPEC_ROOT / "witness-spec.json"
RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
REQUEST_SOURCE = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701"
PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713"
ARCHIVE = PACKAGE.with_suffix(".zip")
RADIAL_VALIDATOR = SPEC_ROOT / "validate_radial_return.py"


def install_radial_return_binding(package: Path, archive: Path) -> None:
    """Layer Radial PNG binding onto the generated common-core package."""
    validator_target = package / "scripts" / "validate_radial_return.py"
    shutil.copy2(RADIAL_VALIDATOR, validator_target)
    launcher_path = package / "artifacts" / "run_witness.ps1"
    launcher = launcher_path.read_text(encoding="utf-8")
    old = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
"""
    new = """$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
if ($validateCode -eq 0 -and $validated.status -eq 'answered') {
  $radialValidator = Join-Path $PackageRoot 'scripts\\validate_radial_return.py'
  & py -3 $radialValidator --contract $contractPath --status $statusPath --work $work
  $validateCode = $LASTEXITCODE
  $validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
}
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
"""
    if launcher.count(old) != 1:
        raise RuntimeError("common launcher validation tail changed")
    launcher_path.write_text(launcher.replace(old, new), encoding="utf-8", newline="\n")

    from tools.windows_witness.core import canonical_json, deterministic_zip, sha256_file

    manifest_path = package / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    for path in sorted(
        (item for item in package.rglob("*") if item.is_file() and item != manifest_path),
        key=lambda item: item.relative_to(package).as_posix(),
    ):
        files.append({
            "path": path.relative_to(package).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    manifest["files"] = files
    manifest_path.write_bytes(canonical_json(manifest))
    deterministic_zip(package, archive)


def staged_spec(stage: Path) -> Path:
    """Make a compiler-only staging tree without changing repository assets."""
    shutil.copy2(SPEC, stage / "witness-spec.json")
    shutil.copy2(SPEC_ROOT / "fullframe_postnorm_typed.cdb.in", stage / "fullframe_postnorm_typed.cdb.in")
    shutil.copy2(RENDERER, stage / "renderer.jsx")
    shutil.copytree(REQUEST_SOURCE, stage / "request")
    manifest_path = stage / "request" / "request_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["request_id"] = json.loads((stage / "witness-spec.json").read_text(encoding="utf-8"))["request_id"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return stage / "witness-spec.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=ARCHIVE)
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    zip_path = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    sys.path.insert(0, str(ROOT))
    from tools.windows_witness.compiler import compile_witness

    with tempfile.TemporaryDirectory(prefix="rb9_common_core_spec_") as raw_stage:
        spec_path = staged_spec(Path(raw_stage))
        package, archive = compile_witness(spec_path, output_dir, zip_path)
    install_radial_return_binding(package, archive)
    print(json.dumps({"status": "ok", "compiler": "tools.windows_witness.compile", "package": str(package), "zip": str(archive)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
