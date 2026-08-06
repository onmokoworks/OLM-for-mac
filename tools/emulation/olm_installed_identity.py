#!/usr/bin/env python3
"""Fail-closed access to the accepted installed OLM identity manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SCHEMA = "olm.installed-identity-manifest/1"
SHA256 = re.compile(r"[0-9a-f]{64}")


def _fail(message: str) -> RuntimeError:
    return RuntimeError(f"FAIL CLOSED: installed identity manifest: {message}")


def accepted_plugin(plugin: str) -> dict:
    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _fail(f"unreadable: {exc}") from exc
    if payload.get("schema") != SCHEMA:
        raise _fail("schema mismatch")
    rows = payload.get("plugins")
    if not isinstance(rows, list):
        raise _fail("plugins is not a list")
    names = [row.get("plugin") for row in rows if isinstance(row, dict)]
    if len(names) != len(rows) or len(names) != len(set(names)):
        raise _fail("plugin rows are malformed or duplicated")
    matches = [row for row in rows if row.get("plugin") == plugin]
    if len(matches) != 1:
        raise _fail(f"expected exactly one {plugin} row, got {len(matches)}")
    row = matches[0]
    digest = row.get("sha256")
    path = row.get("installed_bundle")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise _fail(f"{plugin} sha256 is invalid")
    if not isinstance(path, str) or not Path(path).is_absolute():
        raise _fail(f"{plugin} installed_bundle is not absolute")
    for field in ("source_installed_exact", "universal_exact", "codesign_exact"):
        if row.get(field) is not True:
            raise _fail(f"{plugin} {field} is not true")
    return row


def verified_binary(plugin: str, executable_name: str | None = None) -> tuple[Path, dict]:
    row = accepted_plugin(plugin)
    bundle = Path(row["installed_bundle"])
    binary = bundle / "Contents/MacOS" / (executable_name or plugin)
    if not binary.is_file():
        raise _fail(f"{plugin} executable is missing: {binary}")
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    if actual != row["sha256"]:
        raise _fail(f"{plugin} executable drifted: {actual} != {row['sha256']}")
    return binary, row
