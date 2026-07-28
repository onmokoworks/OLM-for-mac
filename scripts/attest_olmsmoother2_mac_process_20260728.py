#!/usr/bin/env python3
"""Validate the nonce-bound pre/post identity core for a future Mac AE attestor.

This module deliberately contains no process discovery, Apple events, launch,
signal, or termination code.  A live adapter must supply two independently
captured snapshots; this core decides whether they are admissible as one
stable render-process/module interval.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable

HEX64 = re.compile(r"[0-9a-f]{64}")
ROLES = ("no_effect_control", "effect_on")


class AttestationError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AttestationError(f"{label} must be an object")
    return value


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise AttestationError(f"{label} must be lowercase sha256")
    return value


def _nonce(value: object) -> str:
    return _hex(value, "run_nonce")


def _bound_exact(path_value: object, digest_value: object, label: str) -> tuple[Path, tuple[int, int, int, int]]:
    if not isinstance(path_value, str) or not path_value:
        raise AttestationError(f"{label} path missing")
    raw = Path(path_value)
    if not raw.is_absolute() or raw.is_symlink():
        raise AttestationError(f"{label} must be an absolute non-symlink")
    path = raw.resolve(strict=True)
    if raw != path:
        raise AttestationError(f"{label} must be canonical without symlink aliases")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise AttestationError(f"{label} cannot be opened without following links") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise AttestationError(f"{label} is not a regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        current = os.stat(path, follow_symlinks=False)
        current_identity = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
        if before_identity != after_identity or after_identity != current_identity:
            raise AttestationError(f"{label} changed while being bound")
        if digest.hexdigest() != _hex(digest_value, f"{label}.sha256"):
            raise AttestationError(f"{label} file/hash mismatch")
        return path, after_identity
    finally:
        os.close(descriptor)


def _regular_exact(path_value: object, digest_value: object, label: str) -> Path:
    return _bound_exact(path_value, digest_value, label)[0]


def validate_snapshot(snapshot: object, expected: dict[str, Any], label: str) -> dict[str, Any]:
    row = _object(snapshot, label)
    if set(row) != {"process", "module"}:
        raise AttestationError(f"{label} snapshot schema mismatch")
    process = _object(row.get("process"), f"{label}.process")
    module = _object(row.get("module"), f"{label}.module")
    required_process = ("pid", "birth_token", "executable_path", "executable_sha256", "dev", "ino", "size", "mtime_ns")
    required_module = ("path", "sha256", "dev", "ino", "size", "mtime_ns", "vmmap_match_count")
    if set(process) != set(required_process) or set(module) != set(required_module):
        raise AttestationError(f"{label} identity schema mismatch")
    if type(process["pid"]) is not int or process["pid"] <= 0 or not isinstance(process["birth_token"], str) or not process["birth_token"]:
        raise AttestationError(f"{label} process PID/birth invalid")
    for owner, keys in ((process, ("dev", "ino", "size", "mtime_ns")), (module, ("dev", "ino", "size", "mtime_ns"))):
        if any(type(owner[key]) is not int or owner[key] < 0 for key in keys):
            raise AttestationError(f"{label} stat identity invalid")
    if type(module["vmmap_match_count"]) is not int or module["vmmap_match_count"] != 1:
        raise AttestationError(f"{label} requires exactly one vmmap module match")
    expected_ae = _object(expected.get("ae_executable"), "expected.ae_executable")
    expected_module = _object(expected.get("module"), "expected.module")
    if process["executable_path"] != expected_ae.get("path") or _hex(process["executable_sha256"], f"{label}.process.sha256") != _hex(expected_ae.get("sha256"), "expected.ae_executable.sha256"):
        raise AttestationError(f"{label} executable identity mismatch")
    if module["path"] != expected_module.get("path") or _hex(module["sha256"], f"{label}.module.sha256") != _hex(expected_module.get("sha256"), "expected.module.sha256"):
        raise AttestationError(f"{label} module identity mismatch")
    for owner, path_key, digest_key, owner_label in (
        (process, "executable_path", "executable_sha256", "process executable"),
        (module, "path", "sha256", "module"),
    ):
        _, identity = _bound_exact(owner[path_key], owner[digest_key], f"{label}.{owner_label}")
        if (owner["dev"], owner["ino"], owner["size"], owner["mtime_ns"]) != identity:
            raise AttestationError(f"{label} {owner_label} stat identity mismatch")
    return row


def run_once(
    challenge: object,
    pre_request: object,
    post_request: object,
    snapshot_provider: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    challenge = _object(challenge, "challenge")
    if set(challenge) != {"kind", "schema_version", "run_nonce", "wrapper_sha256", "expected", "result_path", "outputs"}:
        raise AttestationError("challenge schema mismatch")
    if challenge.get("kind") != "olmsmoother2_mac_process_challenge" or type(challenge.get("schema_version")) is not int or challenge.get("schema_version") != 1:
        raise AttestationError("challenge kind/schema mismatch")
    nonce = _nonce(challenge.get("run_nonce"))
    expected = _object(challenge.get("expected"), "challenge.expected")
    if set(expected) != {"ae_executable", "module"}:
        raise AttestationError("challenge.expected schema mismatch")
    for name in ("ae_executable", "module"):
        identity = _object(expected[name], f"expected.{name}")
        if set(identity) != {"path", "sha256"}:
            raise AttestationError(f"expected.{name} schema mismatch")
        identity["path"] = str(_regular_exact(identity["path"], identity["sha256"], f"expected.{name}"))
    _hex(challenge.get("wrapper_sha256"), "wrapper_sha256")
    challenge_digest = canonical_sha256(challenge)

    pre = _object(pre_request, "pre_request")
    if set(pre) != {"kind", "schema_version", "run_nonce", "challenge_sha256", "sequence"}:
        raise AttestationError("pre request schema mismatch")
    if pre.get("kind") != "olmsmoother2_mac_process_pre_request" or type(pre.get("schema_version")) is not int or pre.get("schema_version") != 1 or pre.get("run_nonce") != nonce:
        raise AttestationError("pre request identity/nonce mismatch")
    if pre.get("challenge_sha256") != challenge_digest or type(pre.get("sequence")) is not int or pre.get("sequence") != 1:
        raise AttestationError("pre request challenge/sequence mismatch")
    pre_digest = canonical_sha256(pre)
    pre_snapshot = validate_snapshot(snapshot_provider("pre"), expected, "pre")
    pre_snapshot_digest = canonical_sha256(pre_snapshot)

    post = _object(post_request, "post_request")
    if set(post) != {"kind", "schema_version", "run_nonce", "challenge_sha256", "sequence", "pre_request_sha256", "pre_snapshot_sha256", "result_sha256", "artifacts"}:
        raise AttestationError("post request schema mismatch")
    if post.get("kind") != "olmsmoother2_mac_process_post_request" or type(post.get("schema_version")) is not int or post.get("schema_version") != 1 or post.get("run_nonce") != nonce:
        raise AttestationError("post request identity/nonce mismatch")
    if post.get("challenge_sha256") != challenge_digest or type(post.get("sequence")) is not int or post.get("sequence") != 2:
        raise AttestationError("post request challenge/sequence mismatch")
    if post.get("pre_request_sha256") != pre_digest or post.get("pre_snapshot_sha256") != pre_snapshot_digest:
        raise AttestationError("post request pre-phase digest chain mismatch")
    post_snapshot = validate_snapshot(snapshot_provider("post"), expected, "post")
    for section, keys in (
        ("process", ("pid", "birth_token", "executable_path", "executable_sha256", "dev", "ino", "size", "mtime_ns")),
        ("module", ("path", "sha256", "dev", "ino", "size", "mtime_ns")),
    ):
        if any(pre_snapshot[section][key] != post_snapshot[section][key] for key in keys):
            raise AttestationError(f"{section} identity changed across render interval")

    artifacts = _object(post.get("artifacts"), "post_request.artifacts")
    expected_outputs = _object(challenge.get("outputs"), "challenge.outputs")
    if set(artifacts) != set(ROLES) or set(expected_outputs) != set(ROLES):
        raise AttestationError("artifact roles must be exact")
    verified: dict[str, Any] = {}
    seen: set[Path] = set()
    seen_files: set[tuple[int, int]] = set()
    for role in ROLES:
        actual = _object(artifacts[role], f"artifacts.{role}")
        declared = _object(expected_outputs[role], f"outputs.{role}")
        if set(actual) != {"exr_sha256", "settings_sha256"} or set(declared) != {"exr", "settings"}:
            raise AttestationError(f"{role} artifact schema mismatch")
        exr, exr_identity = _bound_exact(declared["exr"], actual["exr_sha256"], f"{role}.exr")
        settings, settings_identity = _bound_exact(declared["settings"], actual["settings_sha256"], f"{role}.settings")
        identities = (exr_identity[:2], settings_identity[:2])
        if exr in seen or settings in seen or exr == settings or identities[0] == identities[1] or any(identity in seen_files for identity in identities):
            raise AttestationError("duplicate artifact path")
        seen.update((exr, settings))
        seen_files.update(identities)
        verified[role] = {"exr": str(exr), "exr_sha256": actual["exr_sha256"], "settings": str(settings), "settings_sha256": actual["settings_sha256"]}
    result_path, result_identity = _bound_exact(challenge.get("result_path"), post.get("result_sha256"), "result")
    if result_path in seen or result_identity[:2] in seen_files:
        raise AttestationError("result aliases an artifact")

    return {
        "kind": "olmsmoother2_mac_process_attestation",
        "schema_version": 1,
        "status": "attested",
        "run_nonce": nonce,
        "challenge_sha256": challenge_digest,
        "pre": {"request_sha256": pre_digest, "snapshot": pre_snapshot, "snapshot_sha256": pre_snapshot_digest},
        "post": {"request_sha256": canonical_sha256(post), "snapshot": post_snapshot, "snapshot_sha256": canonical_sha256(post_snapshot)},
        "artifacts": verified,
        "result": {"path": str(result_path), "sha256": post["result_sha256"]},
        "invariants": {
            "same_pid_birth": True,
            "same_executable": True,
            "same_module_file": True,
            "exact_vmmap_pre": True,
            "exact_vmmap_post": True,
            "pre_nonce_digest_chain": True,
            "post_snapshot_observed_by_attestor": True,
        },
    }


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() or path.is_symlink():
            raise AttestationError(f"refusing to overwrite {path}")
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    print("[FAIL_CLOSED] live process adapter is not implemented; use run_once with an independently tested snapshot provider")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
