#!/usr/bin/env python3
"""Regression tests for packaged plug-in binary hash verification."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_mac_plugin_package.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("verify_mac_plugin_package", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sha256_matches_binary_bytes() -> None:
    payload = b"universal-plugin-test-payload"
    expected = hashlib.sha256(payload).hexdigest()
    with tempfile.TemporaryDirectory(prefix="olm_package_hash_test_") as raw:
        binary = Path(raw) / "Plugin"
        binary.write_bytes(payload)
        assert MODULE.binary_sha256(binary) == expected


def test_sha256_changes_when_packaged_binary_changes() -> None:
    with tempfile.TemporaryDirectory(prefix="olm_package_hash_test_") as raw:
        binary = Path(raw) / "Plugin"
        binary.write_bytes(b"original")
        manifest_sha = MODULE.binary_sha256(binary)
        binary.write_bytes(b"tampered")
        assert MODULE.binary_sha256(binary) != manifest_sha


def test_verifier_source_recomputes_and_compares_hash() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "actual_sha = binary_sha256(binary_path)" in source
    assert "sha.lower() != actual_sha" in source


def test_binary_metadata_helpers_parse_tool_output() -> None:
    binary = Path("Example.plugin/Contents/MacOS/Example")
    with mock.patch.object(MODULE, "command_output", return_value="x86_64 arm64"):
        assert MODULE.binary_architectures(binary) == {"arm64", "x86_64"}
    vtool = "Example:\nLoad command 10\n      cmd LC_BUILD_VERSION\n    minos 11.0\n      sdk 26.2\n"
    with mock.patch.object(MODULE, "command_output", return_value=vtool):
        assert MODULE.binary_minimum_macos(binary, "arm64") == "11.0"
        assert MODULE.binary_sdk_version(binary, "arm64") == "26.2"


def test_signing_kind_distinguishes_adhoc_and_developer_id() -> None:
    completed = mock.Mock(stdout="Executable=Example\nSignature=adhoc\n")
    with mock.patch.object(MODULE.subprocess, "run", return_value=completed):
        assert MODULE.signing_kind(Path("Example.plugin")) == "adhoc"
    completed = mock.Mock(stdout="Authority=Developer ID Application: Example Corp (ABCDE12345)\n")
    with mock.patch.object(MODULE.subprocess, "run", return_value=completed):
        assert MODULE.signing_kind(Path("Example.plugin")) == "developer-id-application"
