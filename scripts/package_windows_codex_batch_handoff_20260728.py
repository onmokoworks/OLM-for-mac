#!/usr/bin/env python3
"""Consolidate immutable Windows Codex jobs into one deterministic handoff ZIP."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "windows_codex_batch_handoff_v2"
RETURN_SCHEMA = "windows_codex_batch_return_v2"
INTAKE_SCHEMA = "windows_codex_batch_intake_v2"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ID_RE = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9_-])?")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
DOS_DEVICE_RE = re.compile(
    r"(?:con|prn|aux|nul|clock\$|com[1-9¹²³]|lpt[1-9¹²³])",
    re.IGNORECASE,
)
WINDOWS_FORBIDDEN_RE = re.compile(r'[\x00-\x1f\x7f<>"|?*]')
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
RETURN_RECORD_SCHEMA = "windows_codex_batch_return_record_v2"
RETURN_CHECKSUMS_MEMBER = "CHECKSUMS.sha256"


class ContractError(ValueError):
    """A job or archive violates the batch handoff contract."""


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or not path.parts:
        raise ContractError(f"{label} is unsafe: {value!r}")
    if re.match(r"^[A-Za-z]:", value):
        raise ContractError(f"{label} is drive-qualified: {value!r}")
    for component in path.parts:
        try:
            utf16_units = len(component.encode("utf-16-le")) // 2
        except UnicodeEncodeError as exc:
            raise ContractError(f"{label} contains invalid Unicode: {value!r}") from exc
        if utf16_units > 255:
            raise ContractError(
                f"{label} component exceeds 255 UTF-16 code units: {value!r}"
            )
        if WINDOWS_FORBIDDEN_RE.search(component):
            raise ContractError(f"{label} contains a Windows-forbidden character/control: {value!r}")
        if ":" in component:
            raise ContractError(f"{label} contains a colon/ADS component: {value!r}")
        if component.endswith((" ", ".")):
            raise ContractError(f"{label} has a trailing dot/space component: {value!r}")
        if DOS_DEVICE_RE.fullmatch(component.split(".", 1)[0]):
            raise ContractError(f"{label} contains a reserved DOS device basename: {value!r}")
    return value


def validated_zip_members(
    data: bytes,
    label: str,
    *,
    allow_directories: bool = True,
) -> dict[str, bytes]:
    regular_files: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            seen: dict[str, bool] = {}
            for info in archive.infolist():
                posix = PurePosixPath(info.filename).as_posix()
                expected_name = posix + "/" if info.is_dir() else posix
                if info.filename != expected_name:
                    raise ContractError(
                        f"{label} member is not canonically spelled: {info.filename!r}"
                    )
                name = safe_relative(info.filename, f"{label} member")
                is_directory = info.is_dir()
                if is_directory and not allow_directories:
                    raise ContractError(f"{label} contains forbidden directory member: {name}")
                normalized = name.rstrip("/")
                folded = normalized.casefold()
                if folded in seen:
                    raise ContractError(f"{label} has duplicate Windows member: {name}")
                seen[folded] = is_directory
                if "__macosx" in (part.casefold() for part in PurePosixPath(name).parts):
                    raise ContractError(f"{label} contains forbidden __MACOSX member: {name}")
                mode = info.external_attr >> 16
                file_type = stat.S_IFMT(mode)
                if info.create_system == 3 and file_type:
                    valid_type = stat.S_ISDIR(mode) if is_directory else stat.S_ISREG(mode)
                    if not valid_type:
                        raise ContractError(
                            f"{label} has invalid Unix member type/path binding: {name}"
                        )
                if not is_directory:
                    regular_files[normalized] = archive.read(info)
            for folded in seen:
                parts = PurePosixPath(folded).parts
                for length in range(1, len(parts)):
                    prefix = "/".join(parts[:length])
                    if prefix in seen and not seen[prefix]:
                        raise ContractError(
                            f"{label} has file/directory hierarchy collision: {prefix}"
                        )
    except zipfile.BadZipFile as exc:
        raise ContractError(f"not a valid ZIP: {label}") from exc
    return regular_files


def validate_child_zip(data: bytes, label: str) -> set[str]:
    return set(validated_zip_members(data, label))


def load_job(manifest_path: Path, order: int) -> tuple[dict[str, Any], Path, bytes]:
    try:
        source = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read job manifest {manifest_path}: {exc}") from exc
    if not isinstance(source, dict):
        raise ContractError(f"job manifest must be an object: {manifest_path}")
    if source.get("schema") != "windows_codex_batch_job_v1":
        raise ContractError(f"unsupported job manifest schema: {manifest_path}")
    job_id = source.get("job_id")
    if not isinstance(job_id, str) or ID_RE.fullmatch(job_id) is None:
        raise ContractError(f"invalid job_id in {manifest_path}")
    package_text = safe_relative(source.get("package"), f"{job_id}.package")
    expected_sha = source.get("package_sha256")
    if not isinstance(expected_sha, str) or SHA256_RE.fullmatch(expected_sha) is None:
        raise ContractError(f"{job_id}.package_sha256 is missing or invalid")
    entrypoint = safe_relative(source.get("entrypoint"), f"{job_id}.entrypoint")
    failure_policy = source.get("failure_policy")
    if failure_policy != "independent":
        raise ContractError(f"{job_id}.failure_policy must be 'independent'")
    package = (manifest_path.parent / package_text).resolve()
    if not package.is_file():
        raise ContractError(f"{job_id} package is missing: {package}")
    try:
        package_bytes = package.read_bytes()
    except OSError as exc:
        raise ContractError(f"cannot snapshot {job_id} package {package}: {exc}") from exc
    regular_files = validate_child_zip(package_bytes, package.name)
    if entrypoint not in regular_files:
        raise ContractError(
            f"{job_id}.entrypoint is not an exact regular-file member of the child ZIP: {entrypoint}"
        )
    actual_sha = digest(package_bytes)
    if actual_sha != expected_sha:
        raise ContractError(
            f"{job_id} package SHA-256 drift: expected {expected_sha}, observed {actual_sha}"
        )
    normalized = {
        "order": order,
        "job_id": job_id,
        "package": f"jobs/{order:03d}_{job_id}/package.zip",
        "package_sha256": expected_sha,
        "package_size_bytes": len(package_bytes),
        "entrypoint": entrypoint,
        "failure_policy": "independent",
        "success_status": source.get("success_status", "answered"),
        "failure_status": source.get("failure_status", "exact_bind_failure"),
    }
    if normalized["success_status"] != "answered" or normalized["failure_status"] != "exact_bind_failure":
        raise ContractError(f"{job_id} terminal statuses must be answered/exact_bind_failure")
    for optional in ("request_id", "description"):
        if optional in source:
            if not isinstance(source[optional], str) or not source[optional]:
                raise ContractError(f"{job_id}.{optional} must be a non-empty string")
            normalized[optional] = source[optional]
    return normalized, package, package_bytes


def readme(batch_id: str) -> bytes:
    return f"""# Windows Codex consolidated batch: {batch_id}

## START GATE

`START_GATE=HOLD`

Do not execute a child job until the user explicitly releases this gate in the
Windows Codex task. Inspecting manifests and verifying hashes is allowed.

After release, execute every expected job exactly once in
`BATCH_MANIFEST.json` order. Each child is immutable: verify its SHA-256 before
extraction and execution. Every job must reach exactly one terminal status:
`answered` or `exact_bind_failure`. An `exact_bind_failure` in one job must not erase,
downgrade, overwrite, or prevent collection of already successful jobs; continue
through every remaining expected job and record its terminal status.

Do not change Adobe preferences. Do not delete or bypass Adobe caches. Do not
toggle, dismiss, accept, or automate modal dialogs. If a child cannot satisfy
its exact binding, record that child as `exact_bind_failure` with available
diagnostics. Do not improvise around identity, renderer, host, or modal gates.

Do not emit, upload, attach, or return any interim result or per-job return ZIP.
Every nested ZIP under `jobs/` is forbidden, including `.zip` members such as
`return.zip` and renamed or SFX/preamble payloads detected as valid ZIPs. For
every job, collect at least one direct regular non-ZIP evidence file exactly one
path component below its ordered job directory and record a non-empty evidence
entry with its path, SHA-256, kind, and description in `BATCH_RETURN.json`.
Failure diagnostics may serve as evidence. No directory, nested evidence path,
unexpected file, or unreferenced file is allowed.

The completion barrier is `all_jobs_terminal`: it is satisfied only after every
expected job appears exactly once with a terminal status and checksum-bound
evidence. Only after that barrier is satisfied, emit exactly one consolidated parent ZIP
conforming to `BATCH_RETURN_CONTRACT.json`. The parent status is
`answered` only when every job answered, `partial_success` only when at least
one answered and at least one returned `exact_bind_failure`, and
`exact_bind_failure` when zero jobs answered. `partial_success` is a transport
summary, not permission to discard successful child results.

Exactly-one delivery and its timing are external Windows Codex session policy.
Archive intake validates only the properties of the one consolidated archive it
receives; it cannot prove prior delivery history or timing.
""".encode()


def completion_contract() -> dict[str, Any]:
    return {
        "required_jobs": "all_expected_jobs_exactly_once",
        "terminal_statuses": ["answered", "exact_bind_failure"],
        "barrier": "all_jobs_terminal",
    }


def delivery_contract() -> dict[str, Any]:
    return {
        "archive_count": 1,
        "mode": "single_consolidated_zip",
        "emit_only_after": "all_jobs_terminal",
        "interim_delivery_forbidden": True,
        "per_job_return_zip_delivery_forbidden": True,
        "return_zip_members_forbidden": True,
        "session_policy_enforcement": "external_to_archive_intake",
        "archive_intake_proves": "one_received_archive_only_not_delivery_history_or_timing",
    }


def evidence_contract() -> dict[str, Any]:
    return {
        "minimum_entries_per_job": 1,
        "required_fields": ["path", "sha256", "kind", "description"],
        "non_empty_fields": ["path", "sha256", "kind", "description"],
        "sha256_must_match_referenced_file": True,
        "path_scope": "exactly_one_nonempty_component_below_exact_ordered_job_directory",
        "direct_regular_non_zip_files_only": True,
    }


def return_contract(batch_id: str, jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "$schema": RETURN_SCHEMA,
        "batch_id": batch_id,
        "return_record_schema": RETURN_RECORD_SCHEMA,
        "expected_job_count": len(jobs),
        "completion": completion_contract(),
        "delivery": delivery_contract(),
        "evidence_requirements": evidence_contract(),
        "allowed_parent_statuses": ["answered", "partial_success", "exact_bind_failure"],
        "status_rules": {
            "answered": "every child job answered",
            "partial_success": "at least one child answered and at least one child returned exact_bind_failure",
            "exact_bind_failure": "zero child jobs answered",
        },
        "preserve_successful_jobs": True,
        "return_record_keys": [
            "$schema",
            "batch_id",
            "request_manifest_sha256",
            "request_return_contract_sha256",
            "status",
            "jobs",
        ],
        "expected_jobs": [
            {
                "order": row["order"],
                "job_id": row["job_id"],
                "request_package_sha256": row["package_sha256"],
                "evidence_root": f"jobs/{row['order']:03d}_{row['job_id']}/",
            }
            for row in jobs
        ],
        "job_record_keys": [
            "order",
            "job_id",
            "request_package_sha256",
            "status",
            "evidence",
            "failure",
        ],
        "failure_rules": {
            "answered": "failure must be null",
            "exact_bind_failure": "failure must contain exactly non-empty stage and reason strings",
        },
        "allowlisted_return_members": {
            "fixed": [
                "BATCH_RETURN.json",
                "BATCH_MANIFEST.json",
                "BATCH_RETURN_CONTRACT.json",
                RETURN_CHECKSUMS_MEMBER,
            ],
            "variable": "only regular evidence files referenced exactly once by BATCH_RETURN.json",
            "directories": "forbidden",
            "unexpected_or_unreferenced_members": "forbidden",
            "nested_zip_extension_magic_or_valid_payload_under_jobs": "forbidden",
        },
        "immutable_request_copies": ["BATCH_MANIFEST.json", "BATCH_RETURN_CONTRACT.json"],
        "checksums_file": RETURN_CHECKSUMS_MEMBER,
        "checksum_coverage": {
            "sole_unlisted_member": RETURN_CHECKSUMS_MEMBER,
            "listed_members": "every other exact allowlisted regular-file member",
            "cardinality": "exactly_once",
            "unexpected_entries": "forbidden",
            "accepted_path_spellings": [
                "canonical_member_name",
                "exactly_one_leading_dot_slash_plus_canonical_member_name",
            ],
            "normalization": "remove_at_most_one_leading_dot_slash_before_all_checks",
            "order": "lexicographic_by_normalized_canonical_member_name",
        },
        "validator": {
            "algorithm": "windows_codex_batch_return_validator_v2",
            "implementation": "scripts/package_windows_codex_batch_handoff_20260728.py",
            "cli": "--validate-return REQUEST_BATCH.zip RETURN_BATCH.zip",
        },
    }


def intake_schema(
    batch_id: str,
    jobs: list[dict[str, Any]],
    manifest_sha256: str,
    return_contract_sha256: str,
) -> dict[str, Any]:
    return {
        "$schema": INTAKE_SCHEMA,
        "batch_id": batch_id,
        "validator_algorithm": "windows_codex_batch_return_validator_v2",
        "expected_job_count": len(jobs),
        "request_bindings": {
            "batch_manifest_sha256": manifest_sha256,
            "batch_return_contract_sha256": return_contract_sha256,
        },
        "completion": completion_contract(),
        "delivery": delivery_contract(),
        "evidence_requirements": evidence_contract(),
        "required_root_members": [
            "BATCH_RETURN.json",
            "BATCH_MANIFEST.json",
            "BATCH_RETURN_CONTRACT.json",
            RETURN_CHECKSUMS_MEMBER,
        ],
        "validation": [
            "reject unsafe, duplicate-on-Windows, symlink, and __MACOSX ZIP members",
            "reject directory members and every unexpected or unreferenced member",
            "reject every nested ZIP by .zip extension, ZIP magic, or valid ZIP payload anywhere under jobs, including renamed SFX/preamble payloads",
            "require returned BATCH_MANIFEST.json and BATCH_RETURN_CONTRACT.json bytes and SHA-256 values to equal request copies",
            "require every expected job exactly once and reject missing, duplicate, unexpected, or reordered job records",
            "require each job status to be answered or exact_bind_failure before satisfying all_jobs_terminal",
            "derive and require the exact parent status from all child statuses",
            "require failure null for answered and exact non-empty stage/reason for exact_bind_failure",
            "require each job to contain at least one non-empty evidence entry with path, SHA-256, kind, and description",
            "require every evidence path to name a direct regular non-ZIP file exactly one path component below that job's exact ordered directory",
            "verify every evidence SHA-256 against its referenced file",
            "verify CHECKSUMS.sha256 lists every allowlisted non-directory member except itself exactly once and no others, accepting only canonical paths or one leading ./ and checking normalized canonical paths",
            "accept answered and exact_bind_failure children independently",
            "preserve and intake answered children when parent status is partial_success",
            "validate one received consolidated archive; delivery count and timing remain an external session policy",
        ],
        "expected_jobs": [
            {"order": row["order"], "job_id": row["job_id"], "package_sha256": row["package_sha256"]}
            for row in jobs
        ],
    }


def deterministic_zip(path: Path, members: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            safe_relative(name, "output member")
            info = zipfile.ZipInfo(name, ZIP_EPOCH)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, members[name])


def preflight_output_targets(output: Path, input_paths: list[Path]) -> tuple[Path, Path]:
    output = output.resolve()
    checksum_path = output.with_suffix(output.suffix + ".sha256").resolve()
    if output == checksum_path:
        raise ContractError("output ZIP and checksum sidecar resolve to the same path")
    resolved_input_list = [path.resolve() for path in input_paths]
    resolved_inputs = set(resolved_input_list)
    if len(resolved_inputs) != len(resolved_input_list):
        raise ContractError("immutable manifest/package input paths alias each other")
    for target, label in ((output, "output ZIP"), (checksum_path, "checksum sidecar")):
        if target in resolved_inputs:
            raise ContractError(f"{label} aliases an immutable input: {target}")
        if target.exists():
            raise ContractError(f"{label} already exists; overwrite is forbidden: {target}")
    return output, checksum_path


def fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def atomic_write_batch(
    output: Path,
    checksum_path: Path,
    members: dict[str, bytes],
) -> tuple[str, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    reserved: set[Path] = set()
    temporary: set[Path] = set()
    try:
        for target in (output, checksum_path):
            try:
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError as exc:
                raise ContractError(
                    f"{target.name} appeared after preflight; overwrite is forbidden"
                ) from exc
            os.close(descriptor)
            reserved.add(target)

        zip_fd, zip_temp_text = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
        )
        os.close(zip_fd)
        zip_temp = Path(zip_temp_text)
        temporary.add(zip_temp)
        deterministic_zip(zip_temp, members)
        fsync_file(zip_temp)
        output_sha256 = file_digest(zip_temp)
        output_size = zip_temp.stat().st_size

        checksum_fd, checksum_temp_text = tempfile.mkstemp(
            prefix=f".{checksum_path.name}.",
            suffix=".tmp",
            dir=checksum_path.parent,
        )
        checksum_temp = Path(checksum_temp_text)
        temporary.add(checksum_temp)
        with os.fdopen(checksum_fd, "wb") as handle:
            handle.write(f"{output_sha256}  {output.name}\n".encode("ascii"))
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(zip_temp, output)
        temporary.remove(zip_temp)
        os.replace(checksum_temp, checksum_path)
        temporary.remove(checksum_temp)
        fsync_directory(output.parent)
        if checksum_path.parent != output.parent:
            fsync_directory(checksum_path.parent)
        return output_sha256, output_size
    except BaseException:
        for path in temporary:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for path in reserved:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise


def load_json_object(data: bytes, label: str) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"{label} contains duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    observed = set(value)
    if observed != expected:
        raise ContractError(
            f"{label} keys mismatch: expected {sorted(expected)}, observed {sorted(observed)}"
        )


def normalize_return_checksum_path(value: str) -> str:
    canonical = value[2:] if value.startswith("./") else value
    safe_relative(canonical, "returned checksum path")
    if PurePosixPath(canonical).as_posix() != canonical:
        raise ContractError(
            "returned checksum path must be canonical after at most one leading './'"
        )
    return canonical


def validate_return_checksums(members: dict[str, bytes]) -> None:
    try:
        text = members[RETURN_CHECKSUMS_MEMBER].decode("ascii")
    except (KeyError, UnicodeDecodeError) as exc:
        raise ContractError(f"returned {RETURN_CHECKSUMS_MEMBER} is missing or non-ASCII") from exc
    lines = text.splitlines()
    if text and not text.endswith("\n"):
        raise ContractError(f"returned {RETURN_CHECKSUMS_MEMBER} must end with a newline")
    parsed: dict[str, str] = {}
    observed_order: list[str] = []
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise ContractError(f"invalid returned checksum line: {line!r}")
        sha256, spelled_name = match.groups()
        name = normalize_return_checksum_path(spelled_name)
        if name == RETURN_CHECKSUMS_MEMBER or name in parsed:
            raise ContractError(
                f"duplicate or self-referential returned checksum after normalization: "
                f"{spelled_name}"
            )
        parsed[name] = sha256
        observed_order.append(name)
    # A checksum manifest cannot bind its own final bytes without a circular
    # fixed point. It is the sole allowlisted member intentionally omitted.
    expected_names = sorted(set(members) - {RETURN_CHECKSUMS_MEMBER})
    if observed_order != expected_names:
        raise ContractError(
            f"returned checksums must list every allowlisted member except "
            f"{RETURN_CHECKSUMS_MEMBER} exactly once"
        )
    for name in expected_names:
        if parsed[name] != digest(members[name]):
            raise ContractError(f"returned checksum mismatch: {name}")


def expected_parent_status(statuses: list[str]) -> str:
    answered = statuses.count("answered")
    if answered == len(statuses):
        return "answered"
    if answered:
        return "partial_success"
    return "exact_bind_failure"


def is_zip_payload(data: bytes) -> bool:
    return data.startswith(ZIP_MAGIC) or zipfile.is_zipfile(io.BytesIO(data))


def validate_return_archive(request_batch: Path, return_batch: Path) -> dict[str, Any]:
    try:
        request_bytes = request_batch.resolve().read_bytes()
        returned_bytes = return_batch.resolve().read_bytes()
    except OSError as exc:
        raise ContractError(f"cannot read request/return archive: {exc}") from exc
    request_members = validated_zip_members(
        request_bytes,
        request_batch.name,
        allow_directories=False,
    )
    returned_members = validated_zip_members(
        returned_bytes,
        return_batch.name,
        allow_directories=False,
    )
    for required in ("BATCH_MANIFEST.json", "BATCH_RETURN_CONTRACT.json"):
        if required not in request_members:
            raise ContractError(f"request batch is missing {required}")
    fixed_members = {
        "BATCH_RETURN.json",
        "BATCH_MANIFEST.json",
        "BATCH_RETURN_CONTRACT.json",
        RETURN_CHECKSUMS_MEMBER,
    }
    missing = fixed_members - set(returned_members)
    if missing:
        raise ContractError(f"returned archive is missing fixed members: {sorted(missing)}")
    for name, data in returned_members.items():
        if name.startswith("jobs/") and (
            PurePosixPath(name).suffix.casefold() == ".zip" or is_zip_payload(data)
        ):
            raise ContractError(f"nested ZIP archive/payload is forbidden under jobs: {name}")

    request_manifest_bytes = request_members["BATCH_MANIFEST.json"]
    request_contract_bytes = request_members["BATCH_RETURN_CONTRACT.json"]
    if returned_members["BATCH_MANIFEST.json"] != request_manifest_bytes:
        raise ContractError("returned BATCH_MANIFEST.json is not the immutable request copy")
    if returned_members["BATCH_RETURN_CONTRACT.json"] != request_contract_bytes:
        raise ContractError("returned BATCH_RETURN_CONTRACT.json is not the immutable request copy")

    manifest = load_json_object(request_manifest_bytes, "request BATCH_MANIFEST.json")
    contract = load_json_object(request_contract_bytes, "request BATCH_RETURN_CONTRACT.json")
    if manifest.get("$schema") != SCHEMA or contract.get("$schema") != RETURN_SCHEMA:
        raise ContractError("request batch does not use the supported v2 schemas")
    if (
        contract.get("batch_id") != manifest.get("batch_id")
        or contract.get("return_record_schema") != RETURN_RECORD_SCHEMA
    ):
        raise ContractError("request manifest and return contract batch/schema binding disagree")
    delivery = contract.get("delivery")
    evidence_requirements = contract.get("evidence_requirements")
    if (
        not isinstance(delivery, dict)
        or type(delivery.get("archive_count")) is not int
        or delivery["archive_count"] != 1
        or not isinstance(evidence_requirements, dict)
        or type(evidence_requirements.get("minimum_entries_per_job")) is not int
        or evidence_requirements["minimum_entries_per_job"] != 1
    ):
        raise ContractError("request return contract count fields must be strict integers")
    strict_true_fields = [
        delivery.get("interim_delivery_forbidden"),
        delivery.get("per_job_return_zip_delivery_forbidden"),
        delivery.get("return_zip_members_forbidden"),
        evidence_requirements.get("sha256_must_match_referenced_file"),
        evidence_requirements.get("direct_regular_non_zip_files_only"),
        contract.get("preserve_successful_jobs"),
    ]
    if any(type(value) is not bool or value is not True for value in strict_true_fields):
        raise ContractError("request return contract boolean policy fields must be strict true")
    manifest_jobs = manifest.get("jobs")
    expected_jobs = contract.get("expected_jobs")
    if not isinstance(manifest_jobs, list) or not isinstance(expected_jobs, list):
        raise ContractError("request jobs must be arrays")
    derived_jobs = [
        {
            "order": row.get("order"),
            "job_id": row.get("job_id"),
            "request_package_sha256": row.get("package_sha256"),
            "evidence_root": f"jobs/{row.get('order'):03d}_{row.get('job_id')}/"
            if isinstance(row, dict)
            and type(row.get("order")) is int
            and isinstance(row.get("job_id"), str)
            else None,
        }
        for row in manifest_jobs
        if isinstance(row, dict)
    ]
    if len(derived_jobs) != len(manifest_jobs) or derived_jobs != expected_jobs:
        raise ContractError("request manifest and return contract expected jobs disagree")
    if (
        type(contract.get("expected_job_count")) is not int
        or contract["expected_job_count"] != len(expected_jobs)
    ):
        raise ContractError("request return contract expected_job_count is inconsistent")

    record = load_json_object(returned_members["BATCH_RETURN.json"], "BATCH_RETURN.json")
    require_exact_keys(
        record,
        {
            "$schema",
            "batch_id",
            "request_manifest_sha256",
            "request_return_contract_sha256",
            "status",
            "jobs",
        },
        "BATCH_RETURN.json",
    )
    if record["$schema"] != RETURN_RECORD_SCHEMA or record["batch_id"] != manifest.get("batch_id"):
        raise ContractError("returned record schema or batch_id mismatch")
    if record["request_manifest_sha256"] != digest(request_manifest_bytes):
        raise ContractError("returned request manifest SHA-256 binding mismatch")
    if record["request_return_contract_sha256"] != digest(request_contract_bytes):
        raise ContractError("returned request contract SHA-256 binding mismatch")
    returned_jobs = record["jobs"]
    if not isinstance(returned_jobs, list) or len(returned_jobs) != len(expected_jobs):
        raise ContractError("returned jobs must contain every expected job exactly once")

    evidence_paths: set[str] = set()
    statuses: list[str] = []
    job_keys = {
        "order",
        "job_id",
        "request_package_sha256",
        "status",
        "evidence",
        "failure",
    }
    for index, (job, expected) in enumerate(zip(returned_jobs, expected_jobs), 1):
        if not isinstance(job, dict):
            raise ContractError(f"returned job {index} must be an object")
        require_exact_keys(job, job_keys, f"returned job {index}")
        if type(job["order"]) is not int:
            raise ContractError(
                f"returned job {index} order must be a strict integer, not boolean/float"
            )
        identity = (job["order"], job["job_id"], job["request_package_sha256"])
        expected_identity = (
            expected["order"],
            expected["job_id"],
            expected["request_package_sha256"],
        )
        if identity != expected_identity:
            raise ContractError(f"returned job {index} identity/order/request SHA mismatch")
        status = job["status"]
        if status not in ("answered", "exact_bind_failure"):
            raise ContractError(f"returned job {index} has invalid terminal status")
        statuses.append(status)
        failure = job["failure"]
        if status == "answered":
            if failure is not None:
                raise ContractError(f"answered job {index} failure must be null")
        else:
            if not isinstance(failure, dict):
                raise ContractError(f"exact_bind_failure job {index} requires failure")
            require_exact_keys(failure, {"stage", "reason"}, f"returned job {index} failure")
            if not all(isinstance(failure[key], str) and failure[key] for key in ("stage", "reason")):
                raise ContractError(f"returned job {index} failure stage/reason must be non-empty")

        evidence = job["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ContractError(f"returned job {index} requires at least one evidence entry")
        for evidence_index, item in enumerate(evidence, 1):
            if not isinstance(item, dict):
                raise ContractError(f"returned job {index} evidence {evidence_index} must be an object")
            require_exact_keys(
                item,
                {"path", "sha256", "kind", "description"},
                f"returned job {index} evidence {evidence_index}",
            )
            if not all(
                isinstance(item[key], str) and item[key]
                for key in ("path", "sha256", "kind", "description")
            ):
                raise ContractError(
                    f"returned job {index} evidence {evidence_index} fields must be non-empty"
                )
            path = safe_relative(item["path"], f"returned job {index} evidence path")
            if not path.startswith(expected["evidence_root"]):
                raise ContractError(f"returned job {index} evidence path escapes its ordered root")
            remainder = path[len(expected["evidence_root"]):]
            if not remainder or "/" in remainder:
                raise ContractError(
                    f"returned job {index} evidence must be exactly one direct path component"
                )
            if path in evidence_paths:
                raise ContractError(f"returned evidence path is referenced more than once: {path}")
            if SHA256_RE.fullmatch(item["sha256"]) is None:
                raise ContractError(f"returned job {index} evidence SHA-256 is invalid")
            if path not in returned_members:
                raise ContractError(f"returned evidence file is missing: {path}")
            if digest(returned_members[path]) != item["sha256"]:
                raise ContractError(f"returned evidence SHA-256 mismatch: {path}")
            evidence_paths.add(path)

    aggregate = expected_parent_status(statuses)
    if record["status"] != aggregate:
        raise ContractError(
            f"returned parent status aggregation mismatch: expected {aggregate}, observed {record['status']}"
        )
    allowed_members = fixed_members | evidence_paths
    unexpected = set(returned_members) - allowed_members
    if unexpected:
        raise ContractError(f"returned archive has unexpected or unreferenced members: {sorted(unexpected)}")
    validate_return_checksums(returned_members)
    return {
        "batch_id": record["batch_id"],
        "status": record["status"],
        "job_count": len(returned_jobs),
        "return_zip_sha256": digest(returned_bytes),
    }


def package(batch_id: str, manifest_paths: list[Path], output: Path) -> dict[str, Any]:
    if not ID_RE.fullmatch(batch_id):
        raise ContractError("batch_id is invalid")
    if not manifest_paths:
        raise ContractError("at least one --job-manifest is required")
    jobs: list[dict[str, Any]] = []
    package_snapshots: list[bytes] = []
    input_paths: list[Path] = []
    ids: set[str] = set()
    shas: set[str] = set()
    for order, path in enumerate(manifest_paths, 1):
        manifest_path = path.resolve()
        job, package_path, package_bytes = load_job(manifest_path, order)
        folded = job["job_id"].casefold()
        if folded in ids:
            raise ContractError(f"duplicate job_id: {job['job_id']}")
        if job["package_sha256"] in shas:
            raise ContractError(f"duplicate child package SHA-256: {job['package_sha256']}")
        ids.add(folded)
        shas.add(job["package_sha256"])
        jobs.append(job)
        package_snapshots.append(package_bytes)
        input_paths.extend((manifest_path, package_path))
    manifest = {
        "$schema": SCHEMA,
        "batch_id": batch_id,
        "start_gate": "HOLD",
        "execution": {
            "ordered": True,
            "failure_policy": "per_job_independent",
            **completion_contract(),
        },
        "delivery": delivery_contract(),
        "prohibitions": {
            "change_adobe_preferences": True,
            "delete_or_bypass_adobe_cache": True,
            "automate_modal_dialogs": True,
        },
        "jobs": jobs,
    }
    manifest_bytes = canonical_json(manifest)
    return_contract_bytes = canonical_json(return_contract(batch_id, jobs))
    members: dict[str, bytes] = {
        "START_GATE.txt": b"START_GATE=HOLD\nExplicit user release is required before any child execution.\n",
        "README_FIRST.md": readme(batch_id),
        "BATCH_MANIFEST.json": manifest_bytes,
        "BATCH_RETURN_CONTRACT.json": return_contract_bytes,
        "INTAKE_SCHEMA.json": canonical_json(
            intake_schema(
                batch_id,
                jobs,
                digest(manifest_bytes),
                digest(return_contract_bytes),
            )
        ),
    }
    for row, package_bytes in zip(jobs, package_snapshots):
        prefix = f"jobs/{row['order']:03d}_{row['job_id']}"
        members[f"{prefix}/package.zip"] = package_bytes
        members[f"{prefix}/job_manifest.json"] = canonical_json(row)
    checksums = "".join(f"{digest(members[name])}  {name}\n" for name in sorted(members))
    members["CHECKSUMS.sha256"] = checksums.encode()
    for name in members:
        safe_relative(name, "generated output member")
    output, checksum_path = preflight_output_targets(output, input_paths)
    output_sha256, output_size = atomic_write_batch(output, checksum_path, members)
    result = {
        "batch_id": batch_id,
        "output_zip": str(output),
        "output_zip_sha256": output_sha256,
        "output_zip_size_bytes": output_size,
        "manifest_sha256": digest(manifest_bytes),
        "job_count": len(jobs),
    }
    result["checksum_file"] = str(checksum_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id")
    parser.add_argument("--job-manifest", action="append", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--validate-return",
        nargs=2,
        type=Path,
        metavar=("REQUEST_BATCH", "RETURN_BATCH"),
    )
    args = parser.parse_args()
    try:
        if args.validate_return:
            if args.batch_id or args.job_manifest or args.output:
                raise ContractError("--validate-return cannot be combined with packaging arguments")
            result = validate_return_archive(*args.validate_return)
        else:
            if not args.batch_id or not args.job_manifest or not args.output:
                raise ContractError(
                    "--batch-id, --job-manifest, and --output are required for packaging"
                )
            result = package(args.batch_id, args.job_manifest, args.output)
    except ContractError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
