#!/usr/bin/env python3
"""Validate the nonce-bound pre/post identity core for a future Mac AE attestor.

This module deliberately contains no process discovery, Apple events, launch,
signal, or termination code.  A live adapter must supply two independently
captured snapshots; this core decides whether they are admissible as one
stable render-process/module interval.
"""
from __future__ import annotations

import hashlib
import contextlib
import json
import os
import re
import resource
import stat
import subprocess
import tempfile
import ctypes
import ctypes.util
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


@contextlib.contextmanager
def _held_exact(path_value: object, digest_value: object, label: str):
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
        yield path, after_identity
        final = os.fstat(descriptor)
        final_identity = (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns)
        current = os.stat(path, follow_symlinks=False)
        current_identity = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
        if final_identity != after_identity or current_identity != after_identity:
            raise AttestationError(f"{label} changed before identity release")
    finally:
        os.close(descriptor)


def _bound_exact(path_value: object, digest_value: object, label: str) -> tuple[Path, tuple[int, int, int, int]]:
    with _held_exact(path_value, digest_value, label) as bound:
        return bound


def _regular_exact(path_value: object, digest_value: object, label: str) -> Path:
    return _bound_exact(path_value, digest_value, label)[0]


def _run_read_only(command: list[str], timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
    stdout_limit = 64 * 1024 * 1024 if command and command[0] == "/usr/bin/vmmap" else 8 * 1024 * 1024
    stderr_limit = 1024 * 1024
    child_file_limit = max(stdout_limit, stderr_limit)
    def limit_child_output() -> None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (child_file_limit, child_file_limit))
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            check=False,
            timeout=timeout,
            preexec_fn=limit_child_output,
        )
        stdout_size = os.fstat(stdout_file.fileno()).st_size
        stderr_size = os.fstat(stderr_file.fileno()).st_size
        if stdout_size > stdout_limit or stderr_size > stderr_limit:
            raise AttestationError(f"read-only command output too large: {command[0]}")
        stdout_file.seek(0)
        stderr_file.seek(0)
        try:
            stdout = stdout_file.read().decode("utf-8", errors="strict")
            stderr = stderr_file.read().decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise AttestationError(f"read-only command output is not UTF-8: {command[0]}") from exc
        return subprocess.CompletedProcess(command, result.returncode, stdout, stderr)


def _command_text(command_runner: Callable[..., object], command: list[str], timeout: float = 10.0) -> str:
    try:
        result = command_runner(command, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AttestationError(f"read-only command failed: {command[0]}") from exc
    returncode = getattr(result, "returncode", None)
    stdout = getattr(result, "stdout", None)
    stderr = getattr(result, "stderr", None)
    if type(returncode) is not int or returncode != 0 or not isinstance(stdout, str) or not isinstance(stderr, str):
        raise AttestationError(f"read-only command failed: {command[0]}")
    limit = 64 * 1024 * 1024 if command and command[0] == "/usr/bin/vmmap" else 8 * 1024 * 1024
    if len(stdout.encode("utf-8")) > limit:
        raise AttestationError(f"read-only command output too large: {command[0]}")
    return stdout


VMMAP_REGION = re.compile(
    r"^\s*__TEXT\s+[0-9A-Fa-f]{8,16}-[0-9A-Fa-f]{8,16}\s+"
    r"\[\s*[^\]]+\]\s+[rwx-]{3}/[rwx-]{3}\s+SM=\S+\s+(?P<path>/.*)$"
)


def _vmmap_paths(output: str) -> list[str]:
    return [
        match.group("path")
        for line in output.splitlines()
        if (match := VMMAP_REGION.fullmatch(line.rstrip())) is not None
    ]


def _ps_rows(output: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for line in output.splitlines():
        match = re.fullmatch(r"\s*([0-9]+)\s+(.+?)\s*", line)
        if not match:
            if line.strip():
                raise AttestationError("malformed ps output")
            continue
        pid = int(match.group(1))
        if pid <= 0:
            raise AttestationError("invalid ps PID")
        rows.append((pid, match.group(2)))
    return rows


def _native_birth_token(pid: int) -> str:
    """Return the kernel BSD start time for PID, failing closed off macOS/libproc."""
    PROC_PIDTBSDINFO = 3
    PROC_PIDTBSDINFO_SIZE = 136
    library_name = ctypes.util.find_library("proc")
    if not library_name:
        raise AttestationError("native process birth provider unavailable")
    try:
        library = ctypes.CDLL(library_name, use_errno=True)
        proc_pidinfo = library.proc_pidinfo
        proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        proc_pidinfo.restype = ctypes.c_int
        buffer = (ctypes.c_ubyte * PROC_PIDTBSDINFO_SIZE)()
        received = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, buffer, PROC_PIDTBSDINFO_SIZE)
    except (AttributeError, OSError) as exc:
        raise AttestationError("native process birth provider unavailable") from exc
    if received != PROC_PIDTBSDINFO_SIZE:
        raise AttestationError("could not read native process birth identity")
    # struct proc_bsdinfo ends with struct timeval pbi_start_tv (uint64 sec/usec).
    seconds = int.from_bytes(bytes(buffer[120:128]), byteorder="little")
    microseconds = int.from_bytes(bytes(buffer[128:136]), byteorder="little")
    if seconds <= 0 or not 0 <= microseconds < 1_000_000:
        raise AttestationError("invalid native process birth identity")
    return f"{seconds}:{microseconds}"


def _exact_process(rows: list[tuple[int, str]], pid: int, executable: Path) -> None:
    if rows != [(pid, str(executable))]:
        raise AttestationError("pinned process identity changed")


def snapshot_from_macos(
    expected: dict[str, Any],
    command_runner: Callable[..., object] = _run_read_only,
    birth_provider: Callable[[int], str] = _native_birth_token,
) -> dict[str, Any]:
    """Capture one fail-closed, read-only process/module identity snapshot."""
    expected_ae = _object(expected.get("ae_executable"), "expected.ae_executable")
    expected_module = _object(expected.get("module"), "expected.module")
    with contextlib.ExitStack() as stack:
        executable, executable_identity = stack.enter_context(
            _held_exact(expected_ae.get("path"), expected_ae.get("sha256"), "expected.ae_executable")
        )
        module, module_identity = stack.enter_context(
            _held_exact(expected_module.get("path"), expected_module.get("sha256"), "expected.module")
        )
        candidates = [
            (pid, command)
            for pid, command in _ps_rows(_command_text(command_runner, ["/bin/ps", "-axo", "pid=,comm="]))
            if command == str(executable)
        ]
        if len(candidates) != 1:
            raise AttestationError("requires exactly one canonical executable process")
        pid = candidates[0][0]
        pinned_command = ["/bin/ps", "-p", str(pid), "-o", "pid=,comm="]
        _exact_process(_ps_rows(_command_text(command_runner, pinned_command)), pid, executable)
        birth_before = birth_provider(pid)
        if not isinstance(birth_before, str) or not birth_before:
            raise AttestationError("invalid process birth token")
        vmmap = _command_text(command_runner, ["/usr/bin/vmmap", str(pid)], timeout=120.0)
        parsed_paths = _vmmap_paths(vmmap)
        match_count = len({path for path in parsed_paths if path == str(module)})
        if match_count != 1:
            raise AttestationError("requires exactly one exact vmmap module pathname")
        # Verify the pinned PID/path first, then read birth last so a same-path
        # PID replacement between these operations cannot pass.
        _exact_process(_ps_rows(_command_text(command_runner, pinned_command)), pid, executable)
        birth_after = birth_provider(pid)
        if not isinstance(birth_after, str) or birth_after != birth_before:
            raise AttestationError("process birth identity changed during snapshot")
    return {
        "process": {
            "pid": pid,
            "birth_token": birth_before,
            "executable_path": str(executable),
            "executable_sha256": expected_ae["sha256"],
            "dev": executable_identity[0],
            "ino": executable_identity[1],
            "size": executable_identity[2],
            "mtime_ns": executable_identity[3],
        },
        "module": {
            "path": str(module),
            "sha256": expected_module["sha256"],
            "dev": module_identity[0],
            "ino": module_identity[1],
            "size": module_identity[2],
            "mtime_ns": module_identity[3],
            "vmmap_match_count": match_count,
        },
    }


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
