#!/usr/bin/env python3
"""Fail-closed structural smoke for the row755 no-space JSX retry package."""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "refs/runtime_trace_support/olmdirectionalblur_row755_nospace_jsx_retry_20260713"
PACKAGE = ROOT / "refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_nospace_jsx_retry_20260713.zip"
PREFIX = "olmdirectionalblur_row755_nospace_jsx_retry_20260713/"
METADATA_ONLY_RETURN = ROOT / "refs/windows_returns/20260713/olm_directionalblur_alpha_fade_fullrender_row755_nospace_jsx_retry_20260713_return.zip"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_archive_path(name: str) -> bool:
    if not name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and "." not in path.parts and ".." not in path.parts


def validate_answered_return_archive(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            members = {
                name: archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/") and not name.endswith("\\")
            }
    except FileNotFoundError:
        return False
    json_names = [name for name in members if name.endswith("RETURN_RUNTIME_TRACE.json")]
    if len(json_names) != 1:
        return False
    payload = json.loads(members[json_names[0]].decode("utf-8-sig"))
    if payload.get("status") != "answered":
        return False
    artifacts = payload.get("artifacts")
    raw_logs = payload.get("raw_logs")
    if not isinstance(artifacts, dict) or not isinstance(raw_logs, dict):
        return False
    for group in (artifacts, raw_logs):
        for meta in group.values():
            if not isinstance(meta, dict):
                return False
            archive_path = meta.get("archive_path")
            if not isinstance(archive_path, str) or not safe_archive_path(archive_path):
                return False
            member = members.get(archive_path)
            if member is None:
                return False
            if meta.get("bytes") != len(member):
                return False
            if meta.get("sha256") != sha256_bytes(member):
                return False
    return True


def build_synthetic_return(path: Path, drop_artifact_bytes: bool) -> None:
    artifact_bytes = b"row755-live-bytes"
    log_bytes = b"trace\n"
    payload = {
        "status": "answered",
        "artifacts": {
            "row755_destination_rgba_f32_le.bin": {
                "archive_path": "return/row755_destination_rgba_f32_le.bin",
                "bytes": len(artifact_bytes),
                "sha256": sha256_bytes(artifact_bytes),
            }
        },
        "raw_logs": {
            "cdb_output": {
                "archive_path": "logs/cdb_output.txt",
                "bytes": len(log_bytes),
                "sha256": sha256_bytes(log_bytes),
            }
        },
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("RETURN_RUNTIME_TRACE.json", json.dumps(payload, indent=2) + "\n")
        archive.writestr("logs/cdb_output.txt", log_bytes)
        if not drop_artifact_bytes:
            archive.writestr("return/row755_destination_rgba_f32_le.bin", artifact_bytes)


def main() -> int:
    manifest = json.loads((SUPPORT / "runtime_trace_package_manifest.json").read_text())
    runner = (SUPPORT / "run_alpha_fade_row755.ps1").read_text()

    assert manifest["effect"] == "OLMDirectionalBlur"
    assert "nospace-jsx-nested-cdb-retry" in manifest["profile"]
    for token in (
        "Get-Process -Name 'AfterFX'",
        "$env:PUBLIC",
        "OLMTrace",
        "Copy-Item",
        "capture_at_5554.cdb",
        "-m",
        "-r",
        "ready marker",
        "exact_bind_failure",
        "RETURN_RUNTIME_TRACE.zip",
        "archive_path",
        "logs/cdb_output.txt",
        "return/row755_destination_rgba_f32_le.bin",
    ):
        assert token in runner, token
    assert "if($jsxLaunch -match '\\s')" in runner
    assert "case_id='+[regex]::Escape($caseId)+'$'" in runner
    assert "effect_loaded=1" in runner
    assert "parameters_applied=1" in runner
    assert "Set-ReturnArchiveEntries" in runner
    assert "Build-ReturnArchive" in runner
    assert "Assert-SafeArchivePath" in runner
    assert "New-ArchiveMetadata" in runner
    template = (SUPPORT / "row755_capture.cdb.in").read_text()
    assert "$><__CAPTURE_SCRIPT__" in template
    assert "&&" not in template
    assert "__CHUNK_COMMANDS__" not in template

    expected = {
        PREFIX + "runtime_trace_package_manifest.json",
        PREFIX + "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        PREFIX + "run_alpha_fade_row755.ps1",
        PREFIX + "row755_capture.cdb.in",
        PREFIX + "README.md",
        PREFIX + "case/ae_render_single_case.jsx",
        PREFIX + "case/request_manifest.json",
        PREFIX + "case/reference_manifest.json",
    }
    with zipfile.ZipFile(PACKAGE) as archive:
        names = set(archive.namelist())
        assert expected <= names, sorted(expected - names)
        packed_runner = archive.read(PREFIX + "run_alpha_fade_row755.ps1").decode()
        assert packed_runner == runner
    with tempfile.TemporaryDirectory(prefix="dblur_row755_return_smoke_") as tmp:
        good = Path(tmp) / "good_return.zip"
        bad = Path(tmp) / "bad_return.zip"
        build_synthetic_return(good, drop_artifact_bytes=False)
        build_synthetic_return(bad, drop_artifact_bytes=True)
        assert validate_answered_return_archive(good)
        assert not validate_answered_return_archive(bad)
    assert not validate_answered_return_archive(METADATA_ONLY_RETURN)

    print("PASS dblur row755 no-space JSX retry package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
