#!/usr/bin/env python3
"""Build the immutable r3 OLMDistanceGradation PF16 Windows boundary child."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader
    module_spec.loader.exec_module(module)
    return module


r2 = load(
    ROOT
    / "scripts"
    / "package_windows_codex_olmdistancegradation_pf16_boundary_r2_20260728.py",
    "olmdg_pf16_r2_source",
)

JOB_ID = "olmdistancegradation_pf16_boundary_20260728_r3"
WITNESS_ID = "olmdistancegradation-pf16-direct-boundary-v3"
RUNTIME_ID = r2.RUNTIME_ID
CLAIM_BOUNDARY = r2.CLAIM_BOUNDARY
UNRESOLVED_BOUNDARY = r2.UNRESOLVED_BOUNDARY
REQUEST_ID = r2.REQUEST_ID
PROJECT_ID = r2.PROJECT_ID
PLUGIN_ID = r2.PLUGIN_ID
AEX_SHA256 = r2.AEX_SHA256
CASE_MANIFEST_SHA256 = r2.CASE_MANIFEST_SHA256
REFERENCE_MANIFEST_SHA256 = r2.REFERENCE_MANIFEST_SHA256
INPUT_SHA256 = r2.INPUT_SHA256
CASES = r2.CASES
TARGET = (
    ROOT
    / "refs"
    / "handoffs"
    / "windows_codex_batch_jobs_20260728"
    / JOB_ID
)

BROKEN_STALE_GUARD = (
    "  if (Test-Path -LiteralPath $evidenceRoot -or "
    "Test-Path -LiteralPath $workRoot) {\n"
)
FIXED_STALE_GUARD = (
    "  if ((Test-Path -LiteralPath $evidenceRoot) -or "
    "(Test-Path -LiteralPath $workRoot)) {\n"
)


def make_root_runner() -> str:
    text = r2.FAIL_CLOSED_RUNNER
    text = r2.replace_once(
        text,
        BROKEN_STALE_GUARD,
        FIXED_STALE_GUARD,
        "independent stale-path predicates",
    )
    text = r2.replace_once(
        text,
        "work_pf16_boundary_r2",
        "work_pf16_boundary_r3",
        "work directory",
    )
    validate_root_runner(text)
    return text


def validate_root_runner(source: str) -> None:
    if BROKEN_STALE_GUARD in source:
        raise ValueError("stale guard still binds two LiteralPath arguments")
    if source.count(FIXED_STALE_GUARD) != 1:
        raise ValueError("stale guard must contain two independently grouped Test-Path calls")
    if "work_pf16_boundary_r2" in source:
        raise ValueError("r2 work directory leaked into r3")
    for marker in (
        "work_pf16_boundary_r3",
        "OWNERSHIP_CLEANUP.json",
        "DIRECT_TYPED_VALIDATION.json",
        "runtime_binary_exact = $false",
        "observed_not_pinned",
    ):
        if marker not in source:
            raise ValueError(f"preserved root-runner contract missing: {marker}")


FAIL_CLOSED_RUNNER = make_root_runner()


def configure_predecessor() -> None:
    r2.JOB_ID = JOB_ID
    r2.WITNESS_ID = WITNESS_ID
    r2.RUNTIME_ID = RUNTIME_ID
    r2.UNRESOLVED_BOUNDARY = UNRESOLVED_BOUNDARY
    r2.TARGET = TARGET
    r2.FAIL_CLOSED_RUNNER = FAIL_CLOSED_RUNNER
    r2.configure_base()


def refresh_package_manifest(package_dir: Path, package_zip: Path) -> None:
    manifest_path = package_dir / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = []
    for path in sorted(
        (
            item
            for item in package_dir.rglob("*")
            if item.is_file() and item != manifest_path
        ),
        key=lambda item: item.relative_to(package_dir).as_posix(),
    ):
        inventory.append(
            {
                "path": path.relative_to(package_dir).as_posix(),
                "sha256": r2.base.sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    manifest["files"] = inventory
    manifest_path.write_bytes(r2.base.canonical_json(manifest))
    r2.base.deterministic_zip(package_dir, package_zip)


def finalize_compiled_package(package_dir: Path, package_zip: Path) -> None:
    r2.finalize_compiled_package(package_dir, package_zip)
    readme_path = package_dir / "README.md"
    readme = readme_path.read_text(encoding="ascii")
    readme = r2.replace_once(
        readme,
        "PF16 direct boundary r2",
        "PF16 direct boundary r3",
        "README revision",
    )
    readme += (
        "\nRevision r3 groups the evidence/work stale checks as two independent "
        "Test-Path expressions, preventing duplicate LiteralPath binding before "
        "the internal runner starts.\n"
    )
    readme_path.write_text(readme, encoding="ascii", newline="\n")
    refresh_package_manifest(package_dir, package_zip)


def build_bytes(work: Path) -> tuple[bytes, bytes, bytes]:
    configure_predecessor()
    r2.verify_anchor()
    validate_root_runner(FAIL_CLOSED_RUNNER)
    spec_path = r2.base.prepare_sources(work)
    package_dir = work / "compiled"
    package_zip = work / "package.zip"
    r2.base.compile_witness(spec_path, package_dir, package_zip)
    finalize_compiled_package(package_dir, package_zip)
    package = package_zip.read_bytes()
    package_sha = hashlib.sha256(package).hexdigest()
    manifest = {
        "schema": "windows_codex_batch_job_v1",
        "job_id": JOB_ID,
        "package": "package.zip",
        "package_sha256": package_sha,
        "entrypoint": "run.ps1",
        "failure_policy": "independent",
        "success_status": "answered",
        "failure_status": "exact_bind_failure",
        "request_id": REQUEST_ID,
        "description": (
            "DG PF16 direct r3 with independent stale-path predicates, RCX "
            "entry anchor, typed finite/range validation, exact-owned cleanup, "
            "and observed-unpinned host tools."
        ),
    }
    return (
        package,
        r2.base.canonical_json(manifest),
        f"{package_sha}  package.zip\n".encode("ascii"),
    )


def result(package: bytes) -> dict[str, Any]:
    return {
        "status": "verified",
        "job_id": JOB_ID,
        "request_id": REQUEST_ID,
        "package_sha256": hashlib.sha256(package).hexdigest(),
        "claim_boundary": CLAIM_BOUNDARY,
        "unresolved_boundary": UNRESOLVED_BOUNDARY,
        "target": str(TARGET),
    }


def build_target() -> dict[str, Any]:
    if TARGET.exists():
        raise RuntimeError(f"immutable target already exists: {TARGET}; use --verify")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_r3_") as tmp:
        built = build_bytes(Path(tmp))
    TARGET.mkdir(parents=True)
    for name, data in zip(
        ("package.zip", "job_manifest.json", "package.zip.sha256"), built
    ):
        (TARGET / name).write_bytes(data)
    return result(built[0])


def verify_target() -> dict[str, Any]:
    paths = (
        TARGET / "package.zip",
        TARGET / "job_manifest.json",
        TARGET / "package.zip.sha256",
    )
    if any(not path.is_file() for path in paths):
        raise RuntimeError("immutable r3 child target is incomplete")
    with tempfile.TemporaryDirectory(prefix="olmdg_pf16_r3_verify_") as tmp:
        expected = build_bytes(Path(tmp))
    actual = tuple(path.read_bytes() for path in paths)
    if actual != expected:
        raise RuntimeError("immutable r3 child drifted from deterministic build")
    return result(actual[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    value = verify_target() if args.verify else build_target()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
