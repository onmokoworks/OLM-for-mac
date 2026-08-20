#!/usr/bin/env python3
"""Run scripts/ae_pixel_validation_render.jsx through a live After Effects instance."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import re
import secrets
import stat as stat_module
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

try:
    from run_ae_single_case import (
        OUTPUT_COMPLETION_TIMEOUT_SECONDS,
        OUTPUT_POLL_INTERVAL_SECONDS,
        OUTPUT_STABLE_WINDOW_SECONDS,
        atomic_write_bytes,
        ae_active_marker_path,
        ae_lock,
        inspect_complete_png,
        output_wait_timeout,
        wait_for_complete_png,
        write_result_json,
    )
except ModuleNotFoundError:  # Imported as scripts.run_ae_validation_batch in tests.
    from scripts.run_ae_single_case import (
        OUTPUT_COMPLETION_TIMEOUT_SECONDS,
        OUTPUT_POLL_INTERVAL_SECONDS,
        OUTPUT_STABLE_WINDOW_SECONDS,
        atomic_write_bytes,
        ae_active_marker_path,
        ae_lock,
        inspect_complete_png,
        output_wait_timeout,
        wait_for_complete_png,
        write_result_json,
    )


HOSTLESS_VALIDATION_SCHEMA = "olm.ae-batch-png-integrity/1"
HOSTLESS_VALIDATOR = "python_png_chunks_crc_iend"
RAW_BATCH_KIND = "olm_ae_pixel_validation_batch_render_result"
RAW_REQUEST_KIND = "olm_ae_pixel_validation_render_result"
MAX_EXTENDSCRIPT_PATH_CHARS = 900
DEFAULT_REQUEST_IDS = [
    "ae_pixel_olmblur_20260606",
    "ae_pixel_olmcolorkey_20260606",
    "ae_pixel_olmtoondilate_20260606",
    "ae_pixel_olmdistancegradation_20260606",
    "ae_pixel_olmdistancegradation_extended_20260618",
    "ae_pixel_olmdistancegradation_blur_20260618",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", action="append", default=[], help="Request id directory to render. May be repeated.")
    parser.add_argument(
        "--request-ids-file",
        type=Path,
        default=None,
        help="Optional newline-delimited request id list. Ignored when --request-id is supplied.",
    )
    parser.add_argument("--base-dir", type=Path, default=None, help="AE validation handoff base. Defaults to handoff/ae_pixel_validation_20260618.")
    parser.add_argument("--requests-base", type=Path, default=None, help="Directory containing request subdirectories.")
    parser.add_argument(
        "--results-base",
        type=Path,
        default=None,
        help=(
            "Generation parent. Each invocation writes candidates under a new "
            "batch_run_<run_id>/raw_candidates tree."
        ),
    )
    parser.add_argument("--progress-log", type=Path, default=None)
    parser.add_argument(
        "--batch-result-json",
        type=Path,
        default=None,
        help="Optional atomically updated copy pointing to the immutable run commit.",
    )
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument(
        "--lock-path",
        type=Path,
        default=Path("/tmp/olm_ae_single_case.lock"),
        help="Serialize AE host runs that use shared $.setenv state.",
    )
    parser.add_argument("--dump-js", type=Path, default=None)
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def js_string(value: str) -> str:
    return json.dumps(value)


def build_request_ids(args: argparse.Namespace) -> list[str]:
    if args.request_id:
        return args.request_id
    if args.request_ids_file:
        return [line.strip() for line in args.request_ids_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    return []


def require_unique_request_ids(request_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    for request_id in request_ids:
        key = request_id.casefold()
        if key in seen:
            raise ValueError(f"duplicate/case-colliding request id: {request_id!r}")
        seen.add(key)
    return request_ids


def selected_request_ids(args: argparse.Namespace, base_dir: Path) -> list[str]:
    if args.request_id:
        explicit = build_request_ids(args)
        if any(not value for value in explicit):
            raise ValueError("--request-id values must be non-empty")
        return require_unique_request_ids(explicit)
    if args.request_ids_file is not None:
        explicit = build_request_ids(args)
        if not explicit:
            raise ValueError("explicit --request-ids-file selected no request ids")
        return require_unique_request_ids(explicit)
    default_file = base_dir / "REQUEST_IDS.txt"
    if default_file.is_file():
        selected = [
            line.strip()
            for line in default_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if selected:
            return require_unique_request_ids(selected)
    return require_unique_request_ids(list(DEFAULT_REQUEST_IDS))


def validate_relative_png_frame(frame: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", frame):
        raise ValueError(f"unsafe or non-portable frame name: {frame!r}")
    relative = Path(frame)
    if relative.is_absolute() or relative.name != frame or frame in (".", ".."):
        raise ValueError(f"unsafe frame path: {frame!r}")
    if relative.suffix.lower() != ".png":
        raise ValueError(f"render candidate is not PNG: {frame!r}")


def validate_extendscript_path(path: Path, label: str) -> None:
    rendered = str(path)
    if len(rendered) > MAX_EXTENDSCRIPT_PATH_CHARS:
        raise ValueError(
            f"{label} exceeds safe ExtendScript path length "
            f"({len(rendered)} > {MAX_EXTENDSCRIPT_PATH_CHARS})"
        )
    if any(ord(character) < 32 for character in rendered):
        raise ValueError(f"{label} contains a control character")


def read_regular_file_nofollow(path: Path, *, dir_fd: int | None = None) -> bytes:
    payload, _ = read_regular_file_nofollow_with_identity(path, dir_fd=dir_fd)
    return payload


def read_regular_file_nofollow_with_identity(
    path: Path,
    *,
    dir_fd: int | None = None,
) -> tuple[bytes, dict[str, int]]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path.name if dir_fd is not None else path, flags, dir_fd=dir_fd)
    try:
        before = os.fstat(descriptor)
        if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError(f"not a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                after = os.fstat(descriptor)
                if filesystem_identity(before) != filesystem_identity(after):
                    raise ValueError(f"regular file changed while reading: {path}")
                return b"".join(chunks), identity_payload(after)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def request_output_alias(request_id: str) -> str:
    alias = re.sub(r"^ae_pixel_", "", request_id)
    return re.sub(r"_20[0-9]{6}$", "", alias)


def load_expected_frames(requests_base: Path, request_ids: list[str]) -> dict[str, list[str]]:
    """Load the declared case set before AE so omissions cannot pass post-host."""

    request_ids = require_unique_request_ids(request_ids)
    expected: dict[str, list[str]] = {}
    requests_root = requests_base.resolve()
    for request_id in request_ids:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", request_id):
            raise ValueError(f"unsafe request id: {request_id!r}")
        if request_id in (".", "..") or Path(request_id).name != request_id:
            raise ValueError(f"unsafe request id: {request_id!r}")
        manifest_path = (requests_root / request_id / "request_manifest.json").resolve()
        validate_extendscript_path(manifest_path, f"{request_id} manifest path")
        if not manifest_path.is_relative_to(requests_root):
            raise ValueError(f"request manifest escapes requests base: {request_id!r}")
        manifest = json.loads(read_regular_file_nofollow(manifest_path).decode("utf-8-sig"))
        if not isinstance(manifest, dict):
            raise ValueError(f"{request_id}: request manifest must be an object")
        if manifest.get("request_id") != request_id:
            raise ValueError(
                f"{request_id}: manifest request_id differs: {manifest.get('request_id')!r}"
            )
        cases = manifest.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError(f"{request_id}: request manifest must declare cases")
        frames: list[str] = []
        frame_keys: set[str] = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                raise ValueError(f"{request_id}: case {index} must be an object")
            frame = case.get("frame")
            if not isinstance(frame, str) or not frame:
                raise ValueError(f"{request_id}: case {index} must declare a frame")
            validate_relative_png_frame(frame)
            frame_key = frame.casefold()
            if frame_key in frame_keys:
                raise ValueError(f"{request_id}: duplicate/case-colliding frame {frame!r}")
            frame_keys.add(frame_key)
            frames.append(frame)
        expected[request_id] = frames
    return expected


def snapshot_request_sources(
    requests_base: Path,
    request_ids: list[str],
) -> dict[str, dict[str, str]]:
    """Hash every manifest/input byte that JSX consumes for this generation."""

    root = requests_base.resolve()
    snapshots: dict[str, dict[str, str]] = {}
    for request_id in request_ids:
        request_root = (root / request_id).resolve()
        manifest_path = request_root / "request_manifest.json"
        manifest = json.loads(read_regular_file_nofollow(manifest_path).decode("utf-8-sig"))
        if not isinstance(manifest, dict):
            raise ValueError(f"{request_id}: request manifest must be an object")
        relative_paths = [Path("request_manifest.json")]
        reference_value = manifest.get("reference_manifest")
        if not isinstance(reference_value, str) or not reference_value:
            raise ValueError(f"{request_id}: reference_manifest is missing")
        relative_paths.append(Path(reference_value))
        input_dir_value = manifest.get("input_dir")
        if not isinstance(input_dir_value, str) or not input_dir_value:
            raise ValueError(f"{request_id}: input_dir is missing")
        input_dir = Path(input_dir_value)
        for case in manifest.get("cases", []):
            before = case.get("before_effects_frame") if isinstance(case, dict) else None
            if not isinstance(before, str) or not before:
                raise ValueError(f"{request_id}: case before_effects_frame is missing")
            relative_paths.append(input_dir / before)
        request_snapshot: dict[str, str] = {}
        for relative in relative_paths:
            relative_text = str(relative)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or ":" in relative_text
                or "%" in relative_text
                or any(ord(character) < 32 for character in relative_text)
            ):
                raise ValueError(f"{request_id}: unsafe source path {relative_text!r}")
            source = request_root / relative
            if source.is_symlink():
                raise ValueError(f"{request_id}: source path is a symlink: {source}")
            resolved = source.resolve()
            if not resolved.is_relative_to(request_root) or not resolved.is_file():
                raise ValueError(f"{request_id}: source file is missing/escaped: {source}")
            validate_extendscript_path(resolved, f"{request_id} source")
            request_snapshot[relative_text] = hashlib.sha256(
                read_regular_file_nofollow(resolved)
            ).hexdigest()
        snapshots[request_id] = dict(sorted(request_snapshot.items()))
    return snapshots


def filesystem_identity(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


def identity_payload(info: os.stat_result) -> dict[str, int]:
    return dict(
        device=info.st_dev,
        inode=info.st_ino,
        size_bytes=info.st_size,
        modified_ns=info.st_mtime_ns,
        changed_ns=info.st_ctime_ns,
        link_count=info.st_nlink,
    )


def snapshot_generation_ancestors(run_dir: Path) -> dict[str, dict[str, int]]:
    """Bind the generation directory names whose ctime records ancestor swaps."""

    lexical_run = lexical_absolute_path(run_dir)
    lexical_parent = lexical_absolute_path(lexical_run.parent)
    run_info = lexical_run.lstat()
    parent_info = lexical_parent.lstat()
    if not stat_module.S_ISDIR(run_info.st_mode) or not stat_module.S_ISDIR(
        parent_info.st_mode
    ):
        raise ValueError("generation ancestor is not a lexical directory")
    return {
        "run_dir": identity_payload(run_info),
        "run_parent": identity_payload(parent_info),
    }


DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)


def open_directory_chain(
    parent_descriptor: int,
    parts: tuple[str, ...],
    *,
    create: bool,
    directory_records: dict[str, dict[str, int]] | None = None,
    prefix: tuple[str, ...] = (),
) -> int:
    """Open a relative directory chain without ever following a component."""

    descriptor = os.dup(parent_descriptor)
    consumed = list(prefix)
    try:
        for part in parts:
            if part in ("", ".", "..") or "/" in part or ":" in part or "%" in part:
                raise ValueError(f"unsafe directory component: {part!r}")
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(part, DIRECTORY_OPEN_FLAGS, dir_fd=descriptor)
            child_info = os.fstat(child)
            if not stat_module.S_ISDIR(child_info.st_mode):
                os.close(child)
                raise ValueError(f"not a lexical directory component: {part!r}")
            os.close(descriptor)
            descriptor = child
            consumed.append(part)
            if directory_records is not None:
                key = "/".join(consumed)
                value = identity_payload(child_info)
                previous = directory_records.get(key)
                if previous is not None and previous != value:
                    raise ValueError(f"directory identity changed while staging: {key}")
                directory_records[key] = value
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def snapshot_owned_request_sources(
    requests_base: Path,
    expected_snapshot: dict[str, dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, dict[str, int]]]]:
    """Hash and identity-bind every staged source through no-follow dirfds."""

    root = lexical_absolute_path(requests_base)
    container = lexical_absolute_path(root.parent)
    container_before = container.lstat()
    if not stat_module.S_ISDIR(container_before.st_mode):
        raise ValueError("staged requests container is not a lexical directory")
    root_lexical = root.lstat()
    if not stat_module.S_ISDIR(root_lexical.st_mode):
        raise ValueError("staged requests root is not a lexical directory")
    root_descriptor = os.open(root, DIRECTORY_OPEN_FLAGS)
    directory_records: dict[str, dict[str, int]] = {}
    file_records: dict[str, dict[str, int]] = {}
    snapshots: dict[str, dict[str, str]] = {}
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        root_before = os.fstat(root_descriptor)
        if (
            not stat_module.S_ISDIR(root_before.st_mode)
            or (root_before.st_dev, root_before.st_ino)
            != (root_lexical.st_dev, root_lexical.st_ino)
        ):
            raise ValueError("staged requests root identity changed while opening")
        directory_records["."] = identity_payload(root_before)
        for request_id, files in expected_snapshot.items():
            request_descriptor = open_directory_chain(
                root_descriptor,
                (request_id,),
                create=False,
                directory_records=directory_records,
            )
            request_snapshot: dict[str, str] = {}
            try:
                for relative_text, expected_sha in files.items():
                    relative = Path(relative_text)
                    parent_parts = tuple(relative.parts[:-1])
                    parent_descriptor = open_directory_chain(
                        request_descriptor,
                        parent_parts,
                        create=False,
                        directory_records=directory_records,
                        prefix=(request_id,),
                    )
                    source_descriptor: int | None = None
                    try:
                        source_descriptor = os.open(
                            relative.name, file_flags, dir_fd=parent_descriptor
                        )
                        before = os.fstat(source_descriptor)
                        if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
                            raise ValueError(
                                f"{request_id}: staged source is not single-link regular: {relative_text}"
                            )
                        digest = hashlib.sha256()
                        while True:
                            chunk = os.read(source_descriptor, 1024 * 1024)
                            if not chunk:
                                break
                            digest.update(chunk)
                        after = os.fstat(source_descriptor)
                        if filesystem_identity(before) != filesystem_identity(after):
                            raise ValueError(
                                f"{request_id}: staged source changed while hashing: {relative_text}"
                            )
                        actual_sha = digest.hexdigest()
                        if actual_sha != expected_sha:
                            raise ValueError(
                                f"{request_id}: staged source digest changed: {relative_text}"
                            )
                        request_snapshot[relative_text] = actual_sha
                        file_records[f"{request_id}/{relative_text}"] = identity_payload(after)
                    finally:
                        if source_descriptor is not None:
                            os.close(source_descriptor)
                        os.close(parent_descriptor)
            finally:
                os.close(request_descriptor)
            snapshots[request_id] = dict(sorted(request_snapshot.items()))

        # Re-open every recorded component and leaf once more so a mutation during
        # this snapshot cannot inherit an earlier identity record.
        for key, expected_identity in list(directory_records.items()):
            if key == ".":
                current = os.fstat(root_descriptor)
                descriptor = None
            else:
                descriptor = open_directory_chain(
                    root_descriptor, tuple(key.split("/")), create=False
                )
                current = os.fstat(descriptor)
            try:
                if identity_payload(current) != expected_identity:
                    raise ValueError(f"staged directory identity changed: {key}")
            finally:
                if descriptor is not None:
                    os.close(descriptor)
        for key, expected_identity in file_records.items():
            parts = tuple(key.split("/"))
            parent_descriptor = open_directory_chain(
                root_descriptor, parts[:-1], create=False
            )
            descriptor = None
            try:
                descriptor = os.open(parts[-1], file_flags, dir_fd=parent_descriptor)
                current = os.fstat(descriptor)
                if identity_payload(current) != expected_identity:
                    raise ValueError(f"staged file identity changed: {key}")
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                os.close(parent_descriptor)
        container_after = container.lstat()
        if identity_payload(container_after) != identity_payload(container_before):
            raise ValueError("staged requests container identity changed")
        return snapshots, {
            "container": {".": identity_payload(container_after)},
            "directories": dict(sorted(directory_records.items())),
            "files": dict(sorted(file_records.items())),
        }
    finally:
        os.close(root_descriptor)


def stage_request_sources(
    source_requests_base: Path,
    staged_requests_base: Path,
    expected_snapshot: dict[str, dict[str, str]],
) -> dict[str, dict[str, dict[str, int]]]:
    """Materialize the exact validated source bytes into the run-owned tree."""

    source_root = source_requests_base.resolve()
    try:
        existing = staged_requests_base.lstat()
    except FileNotFoundError:
        existing = None
    if existing is not None:
        raise ValueError(f"staged requests path already exists: {staged_requests_base}")
    try:
        staged_parent_info = staged_requests_base.parent.lstat()
    except FileNotFoundError:
        staged_requests_base.parent.mkdir(parents=False, exist_ok=False)
        staged_parent_info = staged_requests_base.parent.lstat()
    if not stat_module.S_ISDIR(staged_parent_info.st_mode):
        raise ValueError("staged requests container is not a lexical directory")
    staged_requests_base.mkdir(parents=False, exist_ok=False)
    created_root = staged_requests_base.lstat()
    if not stat_module.S_ISDIR(created_root.st_mode):
        raise ValueError("new staged requests root is not a lexical directory")
    root_descriptor = os.open(staged_requests_base, DIRECTORY_OPEN_FLAGS)
    created_directories: set[tuple[str, ...]] = set()
    destination_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        opened_root = os.fstat(root_descriptor)
        if (opened_root.st_dev, opened_root.st_ino) != (
            created_root.st_dev,
            created_root.st_ino,
        ):
            raise ValueError("new staged requests root identity changed while opening")
        for request_id, files in expected_snapshot.items():
            for relative_text, expected_sha in files.items():
                relative = Path(relative_text)
                source = (source_root / request_id / relative).resolve()
                if not source.is_relative_to(source_root / request_id):
                    raise ValueError(f"{request_id}: staged source escaped request root")
                payload = read_regular_file_nofollow(source)
                actual_sha = hashlib.sha256(payload).hexdigest()
                if actual_sha != expected_sha:
                    raise ValueError(
                        f"{request_id}: source changed during staging: {relative_text}"
                    )
                directory_parts = (request_id, *relative.parts[:-1])
                parent_descriptor = open_directory_chain(
                    root_descriptor, directory_parts, create=True
                )
                for depth in range(1, len(directory_parts) + 1):
                    created_directories.add(directory_parts[:depth])
                destination_descriptor: int | None = None
                try:
                    destination_descriptor = os.open(
                        relative.name,
                        destination_flags,
                        0o444,
                        dir_fd=parent_descriptor,
                    )
                    written = 0
                    while written < len(payload):
                        count = os.write(destination_descriptor, payload[written:])
                        if count <= 0:
                            raise OSError("short staged source write")
                        written += count
                    os.fsync(destination_descriptor)
                    staged_info = os.fstat(destination_descriptor)
                    if not stat_module.S_ISREG(staged_info.st_mode) or staged_info.st_nlink != 1:
                        raise ValueError("new staged source is not single-link regular")
                finally:
                    if destination_descriptor is not None:
                        os.close(destination_descriptor)
                    os.fsync(parent_descriptor)
                    os.close(parent_descriptor)
        for directory_parts in sorted(created_directories, key=len, reverse=True):
            descriptor = open_directory_chain(
                root_descriptor, directory_parts, create=False
            )
            try:
                os.fchmod(descriptor, 0o555)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        os.fchmod(root_descriptor, 0o555)
        os.fsync(root_descriptor)
    finally:
        os.close(root_descriptor)
    staged_snapshot, staged_identities = snapshot_owned_request_sources(
        staged_requests_base, expected_snapshot
    )
    if staged_snapshot != expected_snapshot:
        raise ValueError("staged request snapshot differs from validated source snapshot")
    return staged_identities


def expected_output_directories(
    results_base: Path,
    expected_frames_by_request: dict[str, list[str]],
) -> dict[str, Path]:
    """Bind request IDs to the exact output folders constructed by the JSX."""

    results_root = results_base.resolve()
    expected: dict[str, Path] = {}
    seen: set[Path] = set()
    seen_alias_keys: set[str] = set()
    for request_id, frames in expected_frames_by_request.items():
        alias = request_output_alias(request_id)
        if alias in ("", ".", "..") or Path(alias).name != alias:
            raise ValueError(f"unsafe output alias for request {request_id!r}: {alias!r}")
        alias_key = alias.casefold()
        if alias_key in seen_alias_keys:
            raise ValueError(f"request output alias case collision: {alias!r}")
        seen_alias_keys.add(alias_key)
        lexical_output_dir = results_root / alias
        if lexical_output_dir.is_symlink():
            raise ValueError(f"request output directory is a symlink: {lexical_output_dir}")
        if lexical_output_dir.exists() and not lexical_output_dir.is_dir():
            raise ValueError(f"request output path is not a directory: {lexical_output_dir}")
        output_dir = lexical_output_dir
        validate_extendscript_path(output_dir, f"{request_id} output directory")
        if output_dir.parent != results_root:
            raise ValueError(f"output directory escapes results base: {output_dir}")
        if output_dir in seen:
            raise ValueError(f"request output alias collision: {output_dir}")
        seen.add(output_dir)
        for frame in frames:
            validate_relative_png_frame(frame)
            lexical_candidate = output_dir / frame
            cursor = output_dir
            for part in Path(frame).parts[:-1]:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ValueError(
                        f"{request_id}: frame parent is a symlink: {cursor}"
                    )
                if cursor.exists() and not cursor.is_dir():
                    raise ValueError(
                        f"{request_id}: frame parent is not a directory: {cursor}"
                    )
            if lexical_candidate.is_symlink():
                raise ValueError(
                    f"{request_id}: frame output is a symlink: {lexical_candidate}"
                )
            candidate = lexical_candidate
            validate_extendscript_path(candidate, f"{request_id} output PNG")
            if candidate.parent != output_dir:
                raise ValueError(
                    f"{request_id}: frame resolves outside output directory: {frame!r}"
                )
        expected[request_id] = output_dir
    return expected


def bind_output_directory_identities(
    output_dirs_by_request: dict[str, Path],
    *,
    create: bool,
) -> dict[str, tuple[int, int]]:
    """Create/bind each lexical request directory to one owned directory inode."""

    identities: dict[str, tuple[int, int]] = {}
    for request_id, output_dir in output_dirs_by_request.items():
        if create:
            output_dir.mkdir(parents=False, exist_ok=True)
        try:
            info = output_dir.lstat()
        except OSError as exc:
            raise ValueError(f"{request_id}: output directory is unavailable: {exc}") from exc
        if not stat_module.S_ISDIR(info.st_mode):
            raise ValueError(f"{request_id}: output directory is not a lexical directory")
        identities[request_id] = (info.st_dev, info.st_ino)
    return identities


def lexical_absolute_path(path: Path) -> Path:
    """Canonicalize ancestors while retaining the final component lexically."""

    absolute = path.absolute()
    return absolute.parent.resolve() / absolute.name


def _request_errors(request: dict[str, object]) -> list[str]:
    errors = request.get("errors")
    if isinstance(errors, list):
        normalized = [str(value) for value in errors]
    else:
        normalized = [] if errors is None else [f"malformed JSX errors field: {errors!r}"]
    request["errors"] = normalized
    return normalized


def _candidate_path(
    request: dict[str, object],
    frame: str,
    *,
    expected_results_base: Path | None,
) -> Path:
    output_dir_value = request.get("output_dir")
    if not isinstance(output_dir_value, str) or not output_dir_value:
        raise ValueError("missing output_dir")
    declared_output_dir = Path(output_dir_value)
    if not declared_output_dir.is_absolute():
        raise ValueError(f"output_dir is not absolute: {declared_output_dir}")
    output_dir = declared_output_dir.parent.resolve() / declared_output_dir.name
    if expected_results_base is not None:
        results_root = expected_results_base.resolve()
        if output_dir.parent != results_root:
            raise ValueError(f"output_dir escapes results base: {output_dir}")
    try:
        output_info = output_dir.lstat()
    except OSError as exc:
        raise ValueError(f"output_dir is unavailable: {exc}") from exc
    if not stat_module.S_ISDIR(output_info.st_mode):
        raise ValueError(f"output_dir is not a lexical directory: {output_dir}")
    validate_relative_png_frame(frame)
    relative = Path(frame)
    lexical_candidate = output_dir / relative
    if lexical_candidate.is_symlink():
        raise ValueError(f"render candidate is a symlink: {frame!r}")
    candidate = lexical_candidate
    if candidate.parent != output_dir:
        raise ValueError(f"frame escapes output_dir: {frame!r}")
    return candidate


def observe_and_bind_png(
    path: Path,
    *,
    observe_png: Callable[..., dict[str, object]],
    not_before_ns: int,
    timeout_seconds: float,
    stable_window_seconds: float,
    poll_interval_seconds: float,
    expected_parent_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Add a stable-file SHA/identity binding to the structural observation."""

    def parent_identity() -> tuple[int, int] | None:
        try:
            current = path.parent.lstat()
        except OSError:
            return None
        if not stat_module.S_ISDIR(current.st_mode):
            return None
        return (current.st_dev, current.st_ino)

    def lexical_identity() -> tuple[int, int, int, int, int, int] | None:
        try:
            current = path.lstat()
        except OSError:
            return None
        if not stat_module.S_ISREG(current.st_mode):
            return None
        return (
            current.st_dev,
            current.st_ino,
            current.st_size,
            current.st_mtime_ns,
            current.st_ctime_ns,
            current.st_nlink,
        )

    initial_parent_identity = parent_identity()
    if (
        initial_parent_identity is None
        or (
            expected_parent_identity is not None
            and initial_parent_identity != expected_parent_identity
        )
    ):
        return {
            "status": "validator_error",
            "format_complete": False,
            "crc_validated": False,
            "identity_bound": False,
            "error": "candidate parent directory identity is not the pre-host binding",
        }

    observation = dict(
        observe_png(
            path,
            not_before_ns=not_before_ns,
            timeout_seconds=timeout_seconds,
            stable_window_seconds=stable_window_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    )
    if parent_identity() != initial_parent_identity:
        observation.update(
            status="changed_after_validation",
            format_complete=False,
            crc_validated=False,
            identity_bound=False,
            error="candidate parent directory changed during validation",
        )
        return observation
    if not (
        observation.get("status") == "stable"
        and observation.get("format_complete") is True
        and observation.get("crc_validated") is True
    ):
        return observation
    if (
        observation.get("identity_bound") is True
        and isinstance(observation.get("sha256"), str)
        and len(str(observation.get("sha256"))) == 64
        and isinstance(observation.get("changed_ns"), int)
        and observation.get("link_count") == 1
    ):
        current_identity = lexical_identity()
        if current_identity is None:
            observation.update(
                status="validator_error",
                format_complete=False,
                crc_validated=False,
                identity_bound=False,
                error="post-parse path is missing, non-regular, or a symlink",
            )
            return observation
        if (
            observation.get("device"),
            observation.get("inode"),
            observation.get("size_bytes"),
            observation.get("modified_ns"),
            observation.get("changed_ns"),
            observation.get("link_count"),
        ) == current_identity:
            return observation
        observation.update(
            status="changed_after_validation",
            format_complete=False,
            crc_validated=False,
            identity_bound=False,
            error="output identity changed after one-pass CRC/digest validation",
        )
        return observation
    details = inspect_complete_png(path)
    if details is None:
        observation.update(
            status="changed_or_invalid_after_validation",
            format_complete=False,
            crc_validated=False,
            identity_bound=False,
            error="one-pass CRC/digest revalidation failed",
        )
        return observation
    if (
        observation.get("size_bytes") != details.get("size_bytes")
        or observation.get("modified_ns") != details.get("modified_ns")
        or observation.get("device") != details.get("device")
        or observation.get("inode") != details.get("inode")
        or (
            observation.get("changed_ns") is not None
            and observation.get("changed_ns") != details.get("changed_ns")
        )
    ):
        observation.update(
            status="changed_after_validation",
            format_complete=False,
            crc_validated=False,
            error="output identity changed after structural validation",
        )
        return observation
    details_identity = (
        details.get("device"),
        details.get("inode"),
        details.get("size_bytes"),
        details.get("modified_ns"),
        details.get("changed_ns"),
        details.get("link_count"),
    )
    if details.get("link_count") != 1 or lexical_identity() != details_identity:
        observation.update(
            status="changed_after_validation",
            format_complete=False,
            crc_validated=False,
            identity_bound=False,
            error="output path changed after one-pass CRC/digest revalidation",
        )
        return observation
    observation.update(details)
    return observation


def validate_batch_outputs(
    result: dict[str, object],
    *,
    not_before_ns: int,
    expected_request_ids: list[str] | None = None,
    expected_run_id: str | None = None,
    expected_frames_by_request: dict[str, list[str]] | None = None,
    expected_output_dirs_by_request: dict[str, Path] | None = None,
    expected_output_identities_by_request: dict[str, tuple[int, int]] | None = None,
    expected_results_base: Path | None = None,
    external_errors: list[str] | None = None,
    timeout_seconds: float = OUTPUT_COMPLETION_TIMEOUT_SECONDS,
    stable_window_seconds: float = OUTPUT_STABLE_WINDOW_SECONDS,
    poll_interval_seconds: float = OUTPUT_POLL_INTERVAL_SECONDS,
    observe_png: Callable[..., dict[str, object]] = wait_for_complete_png,
) -> bool:
    """Promote only fresh, quiet, fully parsed PNG candidates to ``rendered``.

    The JSX observation is deliberately non-authoritative: ExtendScript checks
    only the signature and terminal IEND.  This post-host gate reads every PNG
    chunk, validates every CRC, critical chunk/IHDR/PLTE ordering and the IDAT
    zlib scanline stream, rejects trailing bytes, and rechecks file identity
    after a quiet window.
    """

    requests_value = result.get("requests")
    top_errors: list[str] = list(external_errors or [])
    if expected_run_id is not None and result.get("run_id") != expected_run_id:
        top_errors.append(
            f"batch run_id differs: expected {expected_run_id!r}, got {result.get('run_id')!r}"
        )
    if expected_run_id is not None and result.get("kind") != RAW_BATCH_KIND:
        top_errors.append(f"batch kind must be {RAW_BATCH_KIND!r}")
    if expected_run_id is not None and result.get("schema_version") != 2:
        top_errors.append("batch schema_version must be 2")
    if expected_run_id is not None and result.get("hostless_validation_required") is not True:
        top_errors.append("raw batch must require hostless validation")
    if not isinstance(requests_value, list):
        requests: list[dict[str, object]] = []
        top_errors.append("batch result requests must be an array")
    else:
        requests = []
        for index, value in enumerate(requests_value):
            if isinstance(value, dict):
                requests.append(value)
            else:
                top_errors.append(f"request entry {index} must be an object")

    actual_ids = [request.get("request_id") for request in requests]
    if expected_request_ids and actual_ids != expected_request_ids:
        top_errors.append(
            f"request ids differ: expected {expected_request_ids!r}, got {actual_ids!r}"
        )
    if len(set(str(value) for value in actual_ids)) != len(actual_ids):
        top_errors.append("batch result contains duplicate request ids")

    work: list[tuple[int, str, Path, tuple[int, int] | None]] = []
    seen_paths: set[Path] = set()
    seen_output_dirs: set[Path] = set()
    for request_index, request in enumerate(requests):
        errors = _request_errors(request)
        request_id = request.get("request_id")
        if expected_run_id is not None and request.get("run_id") != expected_run_id:
            errors.append(
                f"request run_id differs: expected {expected_run_id!r}, "
                f"got {request.get('run_id')!r}"
            )
        if expected_run_id is not None and request.get("kind") != RAW_REQUEST_KIND:
            errors.append(f"request kind must be {RAW_REQUEST_KIND!r}")
        if expected_run_id is not None and request.get("schema_version") != 2:
            errors.append("request schema_version must be 2")
        if expected_run_id is not None and request.get("hostless_validation_required") is not True:
            errors.append("raw request must require hostless validation")
        output_bound = True
        bound_output_identity: tuple[int, int] | None = None
        output_dir_value = request.get("output_dir")
        if not isinstance(output_dir_value, str) or not output_dir_value:
            errors.append("missing output_dir")
            output_bound = False
        else:
            declared_output_dir = Path(output_dir_value)
            actual_output_dir = (
                declared_output_dir.parent.resolve() / declared_output_dir.name
                if declared_output_dir.is_absolute()
                else declared_output_dir
            )
            try:
                output_info = actual_output_dir.lstat()
            except OSError as exc:
                output_info = None
                errors.append(f"output_dir is unavailable: {exc}")
                output_bound = False
            if output_info is not None and not stat_module.S_ISDIR(output_info.st_mode):
                errors.append(f"output_dir is not a lexical directory: {actual_output_dir}")
                output_bound = False
            elif output_info is not None:
                bound_output_identity = (output_info.st_dev, output_info.st_ino)
            if actual_output_dir in seen_output_dirs:
                errors.append(f"duplicate output_dir across requests: {actual_output_dir}")
                output_bound = False
            seen_output_dirs.add(actual_output_dir)
            if expected_output_dirs_by_request is not None:
                expected_output_dir = (
                    expected_output_dirs_by_request.get(request_id)
                    if isinstance(request_id, str)
                    else None
                )
                if expected_output_dir is None:
                    errors.append(f"request id has no pre-host output binding: {request_id!r}")
                    output_bound = False
                elif actual_output_dir != expected_output_dir:
                    errors.append(
                        f"output_dir differs from pre-host binding: "
                        f"expected {expected_output_dir}, got {actual_output_dir}"
                    )
                    output_bound = False
            if (
                output_info is not None
                and expected_output_identities_by_request is not None
                and isinstance(request_id, str)
            ):
                expected_identity = expected_output_identities_by_request.get(request_id)
                actual_identity = (output_info.st_dev, output_info.st_ino)
                if expected_identity is None or actual_identity != expected_identity:
                    errors.append(
                        f"output_dir identity differs from pre-host binding: "
                        f"expected {expected_identity}, got {actual_identity}"
                    )
                    output_bound = False
        candidates_value = (
            request.get("render_candidates")
            if "render_candidates" in request
            else request.get("rendered", [])
        )
        request["rendered"] = []
        request["hostless_png_observations"] = {}
        if not isinstance(candidates_value, list):
            errors.append("render_candidates must be an array")
            candidates: list[object] = []
        else:
            candidates = candidates_value
        # Preserve the additive candidate field even when validating a legacy
        # result whose candidates arrived in `rendered`.
        request["render_candidates"] = list(candidates)
        if expected_frames_by_request is not None and isinstance(request_id, str):
            expected_frames = expected_frames_by_request.get(request_id)
            if expected_frames is None:
                errors.append(f"request id has no pre-host manifest: {request_id}")
            elif candidates != expected_frames:
                errors.append(
                    f"render candidates differ from pre-host manifest: "
                    f"expected {expected_frames!r}, got {candidates!r}"
                )
        seen_frames: set[str] = set()
        for candidate_index, frame_value in enumerate(candidates):
            if not isinstance(frame_value, str) or not frame_value:
                errors.append(f"render candidate {candidate_index} must be a non-empty string")
                continue
            frame = frame_value
            if frame in seen_frames:
                errors.append(f"duplicate render candidate: {frame}")
                continue
            seen_frames.add(frame)
            if not output_bound:
                continue
            try:
                path = _candidate_path(
                    request,
                    frame,
                    expected_results_base=expected_results_base,
                )
            except ValueError as exc:
                errors.append(f"{frame}: {exc}")
                continue
            if path in seen_paths:
                errors.append(f"render candidate aliases another request output: {frame}")
                continue
            seen_paths.add(path)
            work.append((request_index, frame, path, bound_output_identity))
        if not candidates:
            errors.append("request declared no render candidates")

    observations: dict[tuple[int, str], tuple[Path, dict[str, object]]] = {}
    if work:
        # Every output observes the same quiet interval in parallel, avoiding a
        # two-second-per-frame post-render penalty for large validation batches.
        with ThreadPoolExecutor(max_workers=min(32, len(work))) as executor:
            futures = {
                executor.submit(
                    observe_and_bind_png,
                    path,
                    observe_png=observe_png,
                    expected_parent_identity=parent_identity,
                    not_before_ns=not_before_ns,
                    timeout_seconds=timeout_seconds,
                    stable_window_seconds=stable_window_seconds,
                    poll_interval_seconds=poll_interval_seconds,
                ): (request_index, frame, path)
                for request_index, frame, path, parent_identity in work
            }
            for future in as_completed(futures):
                request_index, frame, path = futures[future]
                try:
                    observation = future.result()
                except Exception as exc:  # noqa: BLE001 - fail closed at host boundary.
                    observation = {
                        "status": "validator_error",
                        "format_complete": False,
                        "crc_validated": False,
                        "validation": HOSTLESS_VALIDATOR,
                        "error": str(exc),
                    }
                observations[(request_index, frame)] = (path, observation)

    identity_owners: dict[tuple[object, object], tuple[int, str]] = {}
    for key, (_, observation) in observations.items():
        if observation.get("identity_bound") is not True:
            continue
        identity = (observation.get("device"), observation.get("inode"))
        previous = identity_owners.get(identity)
        if previous is None:
            identity_owners[identity] = key
            continue
        for duplicate_key in (previous, key):
            duplicate_observation = observations[duplicate_key][1]
            duplicate_observation.update(
                status="duplicate_file_identity",
                format_complete=False,
                crc_validated=False,
                identity_bound=False,
                error="two render candidates resolved to the same file identity",
            )

    passed_count = 0
    for request_index, request in enumerate(requests):
        errors = _request_errors(request)
        hostless = request["hostless_png_observations"]
        assert isinstance(hostless, dict)
        candidates = request.get("render_candidates")
        candidate_count = len(candidates) if isinstance(candidates, list) else 0
        valid_frames: list[str] = []
        promoted_frames: set[str] = set()
        for frame_value in candidates if isinstance(candidates, list) else []:
            if not isinstance(frame_value, str) or not frame_value:
                continue
            if frame_value in promoted_frames:
                continue
            promoted_frames.add(frame_value)
            key = (request_index, frame_value)
            if key not in observations:
                continue
            path, observation = observations[key]
            observation = dict(observation)
            observation["path"] = str(path)
            observation["authoritative"] = True
            hostless[frame_value] = observation
            valid = (
                observation.get("status") == "stable"
                and observation.get("format_complete") is True
                and observation.get("crc_validated") is True
                and observation.get("validation") == "png_chunks_crc_iend"
                and observation.get("identity_bound") is True
                and isinstance(observation.get("changed_ns"), int)
                and observation.get("link_count") == 1
                and isinstance(observation.get("sha256"), str)
                and len(str(observation.get("sha256"))) == 64
            )
            if valid:
                valid_frames.append(frame_value)
            else:
                errors.append(
                    f"{frame_value}: hostless PNG integrity validation failed "
                    f"({observation.get('status')})"
                )
        request_status = "failed"
        if candidate_count > 0 and len(valid_frames) == candidate_count and not errors:
            request["rendered"] = valid_frames
            passed_count += len(valid_frames)
            request_status = "passed"
        request_passed = len(request["rendered"])
        assert isinstance(request["rendered"], list)
        request["hostless_output_validation"] = {
            "schema": HOSTLESS_VALIDATION_SCHEMA,
            "validator": HOSTLESS_VALIDATOR,
            "authoritative_for_rendered": True,
            "status": request_status,
            "candidate_count": candidate_count,
            "rendered_count": request_passed,
            "failed_count": candidate_count - request_passed,
        }
        request["hostless_validation_required"] = False
        request["hostless_validation_complete"] = True
        request["rendered_authority"] = HOSTLESS_VALIDATOR

    batch_failed = bool(top_errors) or not requests or any(
        request.get("hostless_output_validation", {}).get("status") != "passed"
        for request in requests
    )
    status = "failed" if batch_failed else "passed"
    if batch_failed:
        passed_count = 0
        for request in requests:
            request["rendered"] = []
            validation = request.get("hostless_output_validation")
            if isinstance(validation, dict):
                validation["status"] = "failed"
                validation["rendered_count"] = 0
                validation["failed_count"] = validation.get("candidate_count", 0)
            errors = _request_errors(request)
            if "batch generation failed; request promotion rolled back" not in errors:
                errors.append("batch generation failed; request promotion rolled back")
    declared_candidate_count = sum(
        len(request.get("render_candidates", []))
        if isinstance(request.get("render_candidates"), list)
        else 0
        for request in requests
    )
    result["hostless_output_validation"] = {
        "schema": HOSTLESS_VALIDATION_SCHEMA,
        "validator": HOSTLESS_VALIDATOR,
        "authoritative_for_rendered": True,
        "status": status,
        "request_count": len(requests),
        "candidate_count": declared_candidate_count,
        "rendered_count": passed_count,
        "failed_count": declared_candidate_count - passed_count,
        "errors": top_errors,
        "not_before_ns": not_before_ns,
    }
    result["hostless_validation_required"] = False
    result["hostless_validation_complete"] = True
    result["rendered_authority"] = HOSTLESS_VALIDATOR
    return status == "passed"


def rollback_generation_promotion(result: dict[str, object], error: str) -> None:
    """Fail the whole generation and revoke every per-request promotion."""

    requests = result.get("requests")
    if not isinstance(requests, list):
        requests = []
    candidate_count = 0
    for request in requests:
        if not isinstance(request, dict):
            continue
        candidates = request.get("render_candidates")
        request_candidate_count = len(candidates) if isinstance(candidates, list) else 0
        candidate_count += request_candidate_count
        request["rendered"] = []
        validation = request.get("hostless_output_validation")
        if not isinstance(validation, dict):
            validation = {
                "schema": HOSTLESS_VALIDATION_SCHEMA,
                "validator": HOSTLESS_VALIDATOR,
                "authoritative_for_rendered": True,
                "candidate_count": request_candidate_count,
            }
            request["hostless_output_validation"] = validation
        validation.update(
            status="failed",
            rendered_count=0,
            failed_count=request_candidate_count,
        )
        errors = _request_errors(request)
        rollback_error = "batch generation failed; request promotion rolled back"
        if rollback_error not in errors:
            errors.append(rollback_error)
    validation = result.get("hostless_output_validation")
    if not isinstance(validation, dict):
        validation = {
            "schema": HOSTLESS_VALIDATION_SCHEMA,
            "validator": HOSTLESS_VALIDATOR,
            "authoritative_for_rendered": True,
            "request_count": len(requests),
            "candidate_count": candidate_count,
        }
        result["hostless_output_validation"] = validation
    errors_value = validation.get("errors")
    errors = [str(value) for value in errors_value] if isinstance(errors_value, list) else []
    if error not in errors:
        errors.append(error)
    validation.update(
        status="failed",
        rendered_count=0,
        failed_count=int(validation.get("candidate_count", candidate_count)),
        errors=errors,
    )


def _png_identity(details: dict[str, object]) -> tuple[object, ...]:
    return (
        details.get("device"),
        details.get("inode"),
        details.get("size_bytes"),
        details.get("modified_ns"),
        details.get("changed_ns"),
        details.get("link_count"),
    )


def _png_rename_identity(details: dict[str, object]) -> tuple[object, ...]:
    """Identity fields preserved by an atomic rename (ctime may advance)."""

    return (
        details.get("device"),
        details.get("inode"),
        details.get("size_bytes"),
        details.get("modified_ns"),
        details.get("link_count"),
    )


def open_bound_directory(path: Path, expected_identity: tuple[int, int]) -> int:
    """Open one lexical directory and bind the FD to its preflight inode."""

    lexical = lexical_absolute_path(path)
    info = lexical.lstat()
    if (
        not stat_module.S_ISDIR(info.st_mode)
        or (info.st_dev, info.st_ino) != expected_identity
    ):
        raise ValueError(f"directory ownership changed: {lexical}")
    descriptor = os.open(lexical, DIRECTORY_OPEN_FLAGS)
    opened = os.fstat(descriptor)
    if (
        not stat_module.S_ISDIR(opened.st_mode)
        or (opened.st_dev, opened.st_ino) != expected_identity
    ):
        os.close(descriptor)
        raise ValueError(f"directory identity changed while opening: {lexical}")
    return descriptor


def open_or_create_child_directory(
    parent_descriptor: int,
    name: str,
    *,
    require_new: bool,
) -> int:
    """Create/open exactly one child directory without following aliases."""

    if name in ("", ".", "..") or Path(name).name != name:
        raise ValueError(f"unsafe publication directory name: {name!r}")
    try:
        os.mkdir(name, 0o755, dir_fd=parent_descriptor)
    except FileExistsError:
        if require_new:
            raise ValueError(f"publication child already exists: {name}")
    descriptor = os.open(name, DIRECTORY_OPEN_FLAGS, dir_fd=parent_descriptor)
    info = os.fstat(descriptor)
    if not stat_module.S_ISDIR(info.st_mode):
        os.close(descriptor)
        raise ValueError(f"publication child is not a lexical directory: {name}")
    return descriptor


def directory_path_still_names_descriptor(path: Path, descriptor: int) -> bool:
    try:
        lexical = lexical_absolute_path(path).lstat()
        opened = os.fstat(descriptor)
    except OSError:
        return False
    return (
        stat_module.S_ISDIR(lexical.st_mode)
        and stat_module.S_ISDIR(opened.st_mode)
        and (lexical.st_dev, lexical.st_ino) == (opened.st_dev, opened.st_ino)
    )


def child_name_still_names_descriptor(
    parent_descriptor: int,
    name: str,
    child_descriptor: int,
) -> bool:
    try:
        lexical = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        opened = os.fstat(child_descriptor)
    except OSError:
        return False
    return (
        stat_module.S_ISDIR(lexical.st_mode)
        and stat_module.S_ISDIR(opened.st_mode)
        and (lexical.st_dev, lexical.st_ino) == (opened.st_dev, opened.st_ino)
    )


def copy_bound_validated_png(
    source: Path,
    destination: Path,
    expected_observation: dict[str, object],
    *,
    source_directory_descriptor: int | None = None,
    destination_directory_descriptor: int | None = None,
) -> dict[str, object]:
    """Copy exactly the observed source bytes into one atomic validated artifact."""

    expected_identity = _png_identity(expected_observation)
    expected_sha = expected_observation.get("sha256")
    if expected_observation.get("link_count") != 1 or not isinstance(expected_sha, str):
        raise ValueError("raw candidate lacks a single-link SHA/identity binding")
    reparsed = inspect_complete_png(source, dir_fd=source_directory_descriptor)
    if reparsed is None or _png_identity(reparsed) != expected_identity:
        raise ValueError("raw candidate identity/structure changed before publication")
    if reparsed.get("sha256") != expected_sha:
        raise ValueError("raw candidate digest changed before publication")

    owned_destination_descriptor = (
        os.dup(destination_directory_descriptor)
        if destination_directory_descriptor is not None
        else None
    )
    if owned_destination_descriptor is None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        owned_destination_descriptor = os.open(
            destination.parent, DIRECTORY_OPEN_FLAGS
        )
    try:
        os.stat(
            destination.name,
            dir_fd=owned_destination_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        pass
    else:
        os.close(owned_destination_descriptor)
        raise ValueError(f"validated output already exists: {destination}")
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{time.time_ns()}.{os.urandom(8).hex()}.tmp"
    )
    source_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    destination_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    source_descriptor: int | None = None
    destination_descriptor: int | None = None
    try:
        source_descriptor = os.open(
            source.name if source_directory_descriptor is not None else source,
            source_flags,
            dir_fd=source_directory_descriptor,
        )
        before = os.fstat(source_descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_nlink,
        )
        if not stat_module.S_ISREG(before.st_mode) or before_identity != expected_identity:
            raise ValueError("raw candidate changed before copy")
        destination_descriptor = os.open(
            temporary.name,
            destination_flags,
            0o444,
            dir_fd=owned_destination_descriptor,
        )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(source_descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            written = 0
            while written < len(chunk):
                count = os.write(destination_descriptor, chunk[written:])
                if count <= 0:
                    raise OSError("short validated PNG write")
                written += count
        after = os.fstat(source_descriptor)
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_nlink,
        )
        if before_identity != after_identity or digest.hexdigest() != expected_sha:
            raise ValueError("raw candidate changed while copying")
        os.fsync(destination_descriptor)
        os.close(destination_descriptor)
        destination_descriptor = None
        os.close(source_descriptor)
        source_descriptor = None
        copied = inspect_complete_png(
            temporary, dir_fd=owned_destination_descriptor
        )
        if copied is None or copied.get("sha256") != expected_sha:
            raise ValueError("validated output copy failed PNG/digest verification")
        os.replace(
            temporary.name,
            destination.name,
            src_dir_fd=owned_destination_descriptor,
            dst_dir_fd=owned_destination_descriptor,
        )
        os.fsync(owned_destination_descriptor)
        final = inspect_complete_png(
            destination, dir_fd=owned_destination_descriptor
        )
        if (
            final is None
            or final.get("sha256") != expected_sha
            or _png_rename_identity(final) != _png_rename_identity(copied)
        ):
            raise ValueError("published validated output failed final verification")
        return final
    finally:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if source_descriptor is not None:
            os.close(source_descriptor)
        try:
            os.unlink(temporary.name, dir_fd=owned_destination_descriptor)
        except FileNotFoundError:
            pass
        os.close(owned_destination_descriptor)


def _manifest_identity_matches(
    actual: dict[str, object],
    expected: dict[str, object],
) -> bool:
    return all(
        actual.get(key) == expected.get(key)
        for key in (
            "device",
            "inode",
            "size_bytes",
            "modified_ns",
            "changed_ns",
            "link_count",
        )
    )


def _open_generation_subdirectory(
    generation_descriptor: int,
    generation_root: Path,
    declared_path: object,
    label: str,
) -> tuple[Path, int]:
    if not isinstance(declared_path, str) or not declared_path:
        raise ValueError(f"{label} path is missing")
    lexical = lexical_absolute_path(Path(declared_path))
    try:
        relative = lexical.relative_to(generation_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes generation root: {lexical}") from exc
    if not relative.parts:
        raise ValueError(f"{label} aliases the generation root")
    descriptor = open_directory_chain(
        generation_descriptor,
        tuple(relative.parts),
        create=False,
    )
    if not directory_path_still_names_descriptor(lexical, descriptor):
        os.close(descriptor)
        raise ValueError(f"{label} lexical path no longer names its directory")
    return lexical, descriptor


def _open_exact_child_directory(
    parent_descriptor: int,
    name: str,
    label: str,
) -> int:
    if name in ("", ".", "..") or Path(name).name != name:
        raise ValueError(f"unsafe {label} directory name: {name!r}")
    if name not in os.listdir(parent_descriptor):
        raise ValueError(f"{label} directory spelling differs or is missing: {name!r}")
    descriptor = os.open(name, DIRECTORY_OPEN_FLAGS, dir_fd=parent_descriptor)
    info = os.fstat(descriptor)
    if not stat_module.S_ISDIR(info.st_mode):
        os.close(descriptor)
        raise ValueError(f"{label} is not a lexical directory: {name!r}")
    return descriptor


def verify_generation_commit(
    batch_result_json: Path,
    *,
    expected_run_id: str | None = None,
    expected_commit_bytes: bytes | None = None,
    expected_commit_sha256: str | None = None,
    expected_generation_identity: tuple[int, int] | None = None,
) -> tuple[bool, list[str]]:
    """Re-open and verify every byte/identity attested by a passed commit.

    This is both the writer's post-commit gate and the consumer contract.  A
    caller must not treat a generation or standalone request summary as
    authoritative unless this function returns ``(True, [])`` for the commit
    it is consuming.
    """

    errors: list[str] = []
    generation_root = lexical_absolute_path(batch_result_json).parent
    descriptors: list[int] = []
    directory_bindings: list[tuple[Path, int]] = []
    child_directory_bindings: list[tuple[int, str, int]] = []

    def remember(descriptor: int, path: Path | None = None) -> int:
        descriptors.append(descriptor)
        if path is not None:
            directory_bindings.append((path, descriptor))
        return descriptor

    def remember_child(
        parent_descriptor: int,
        name: str,
        descriptor: int,
    ) -> int:
        descriptors.append(descriptor)
        child_directory_bindings.append((parent_descriptor, name, descriptor))
        return descriptor

    try:
        generation_info = generation_root.lstat()
        if not stat_module.S_ISDIR(generation_info.st_mode):
            raise ValueError("generation root is not a lexical directory")
        generation_identity = (generation_info.st_dev, generation_info.st_ino)
        if (
            expected_generation_identity is not None
            and generation_identity != expected_generation_identity
        ):
            raise ValueError("generation root identity differs from writer anchor")
        generation_descriptor = remember(
            open_bound_directory(
                generation_root,
                generation_identity,
            ),
            generation_root,
        )
        commit_bytes, commit_identity = read_regular_file_nofollow_with_identity(
            batch_result_json,
            dir_fd=generation_descriptor,
        )
        if expected_commit_bytes is not None and commit_bytes != expected_commit_bytes:
            raise ValueError("generation commit bytes differ from writer anchor")
        commit_sha256 = hashlib.sha256(commit_bytes).hexdigest()
        if (
            expected_commit_sha256 is not None
            and commit_sha256 != expected_commit_sha256
        ):
            raise ValueError("generation commit SHA-256 differs from published anchor")
        committed = json.loads(commit_bytes.decode("utf-8-sig"))
        if not isinstance(committed, dict):
            raise ValueError("generation commit must be an object")
        generation_commit = committed.get("generation_commit")
        if not isinstance(generation_commit, dict):
            raise ValueError("generation_commit is missing")
        if generation_commit.get("schema") != "olm.ae-batch-generation-commit/1":
            errors.append("generation commit schema differs")
        if generation_commit.get("status") != "passed":
            errors.append("generation commit status is not passed")
        for flag in (
            "immutable_generation",
            "commit_marker_written_last",
            "post_commit_verification_required",
        ):
            if generation_commit.get(flag) is not True:
                errors.append(f"generation commit flag is not true: {flag}")
        if generation_commit.get("consumer_verifier") != (
            "scripts.run_ae_validation_batch.verify_generation_commit"
        ):
            errors.append("generation commit consumer verifier differs")
        run_id = committed.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            errors.append("generation run_id is missing")
        if generation_commit.get("run_id") != run_id:
            errors.append("generation commit run_id differs from result")
        if expected_run_id is not None and run_id != expected_run_id:
            errors.append(
                f"generation run_id differs: expected {expected_run_id!r}, got {run_id!r}"
            )
        publication_validation = committed.get("publication_validation")
        if (
            not isinstance(publication_validation, dict)
            or publication_validation.get("status") != "passed"
        ):
            errors.append("publication validation is not passed")
        hostless_validation = committed.get("hostless_output_validation")
        if (
            not isinstance(hostless_validation, dict)
            or hostless_validation.get("status") != "passed"
        ):
            errors.append("hostless output validation is not passed")

        requests_value = committed.get("requests")
        requests = requests_value if isinstance(requests_value, list) else []
        if not requests:
            errors.append("generation contains no committed requests")
        request_by_id: dict[str, dict[str, object]] = {}
        for request in requests:
            if not isinstance(request, dict):
                errors.append("committed request entry is not an object")
                continue
            request_id = request.get("request_id")
            if not isinstance(request_id, str) or not request_id:
                errors.append("committed request id is missing")
                continue
            key = request_id.casefold()
            if any(existing.casefold() == key for existing in request_by_id):
                errors.append(f"duplicate committed request id: {request_id!r}")
                continue
            request_by_id[request_id] = request

        raw_root, raw_root_descriptor = _open_generation_subdirectory(
            generation_descriptor,
            generation_root,
            committed.get("raw_candidate_root"),
            "raw candidate root",
        )
        remember(raw_root_descriptor, raw_root)
        validated_root, validated_root_descriptor = _open_generation_subdirectory(
            generation_descriptor,
            generation_root,
            committed.get("validated_output_root"),
            "validated output root",
        )
        remember(validated_root_descriptor, validated_root)
        summary_root, summary_root_descriptor = _open_generation_subdirectory(
            generation_descriptor,
            generation_root,
            committed.get("validated_summary_root"),
            "validated summary root",
        )
        remember(summary_root_descriptor, summary_root)

        validated_outputs = committed.get("validated_outputs")
        validated_summaries = committed.get("validated_summaries")
        if not isinstance(validated_outputs, dict):
            validated_outputs = {}
            errors.append("validated output manifest is missing")
        if not isinstance(validated_summaries, dict):
            validated_summaries = {}
            errors.append("validated summary manifest is missing")
        if set(validated_outputs) != set(request_by_id):
            errors.append("validated output requests differ from committed requests")
        if set(validated_summaries) != set(request_by_id):
            errors.append("validated summary requests differ from committed requests")

        for request_id, request in request_by_id.items():
            try:
                alias = request_output_alias(request_id)
                raw_descriptor = remember_child(
                    raw_root_descriptor,
                    alias,
                    _open_exact_child_directory(
                        raw_root_descriptor, alias, f"{request_id} raw candidate"
                    ),
                )
                output_descriptor = remember_child(
                    validated_root_descriptor,
                    alias,
                    _open_exact_child_directory(
                        validated_root_descriptor, alias, f"{request_id} validated output"
                    ),
                )
                summary_descriptor = remember_child(
                    summary_root_descriptor,
                    alias,
                    _open_exact_child_directory(
                        summary_root_descriptor, alias, f"{request_id} validated summary"
                    ),
                )
            except (OSError, ValueError) as exc:
                errors.append(f"{request_id}: committed directory binding failed: {exc}")
                continue

            expected_raw_dir = raw_root / alias
            expected_validated_dir = validated_root / alias
            if lexical_absolute_path(Path(str(request.get("raw_candidate_output_dir", "")))) != expected_raw_dir:
                errors.append(f"{request_id}: raw candidate output path differs")
            if lexical_absolute_path(Path(str(request.get("validated_output_dir", "")))) != expected_validated_dir:
                errors.append(f"{request_id}: validated output path differs")
            if lexical_absolute_path(Path(str(request.get("output_dir", "")))) != expected_validated_dir:
                errors.append(f"{request_id}: authoritative output path differs")
            expected_summary_path = (
                summary_root / alias / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
            )
            if lexical_absolute_path(Path(str(request.get("validated_summary_path", "")))) != expected_summary_path:
                errors.append(f"{request_id}: validated summary path differs")
            if request.get("generation_commit_required") is not True:
                errors.append(f"{request_id}: generation commit requirement is missing")
            if lexical_absolute_path(Path(str(request.get("generation_commit_path", "")))) != lexical_absolute_path(batch_result_json):
                errors.append(f"{request_id}: generation commit path differs")
            if request.get("standalone_authoritative") is not False:
                errors.append(f"{request_id}: standalone authority flag differs")
            if request.get("generation_status") != "passed":
                errors.append(f"{request_id}: generation status is not passed")

            rendered_value = request.get("rendered")
            rendered = rendered_value if isinstance(rendered_value, list) else []
            observations = request.get("hostless_png_observations")
            request_artifacts = validated_outputs.get(request_id)
            if not rendered or not isinstance(observations, dict):
                errors.append(f"{request_id}: committed render observations are missing")
                continue
            if not isinstance(request_artifacts, dict) or set(request_artifacts) != set(rendered):
                errors.append(f"{request_id}: validated frame manifest differs from rendered")
                continue
            for frame_value in rendered:
                if not isinstance(frame_value, str):
                    errors.append(f"{request_id}: committed frame is not a string")
                    continue
                try:
                    validate_relative_png_frame(frame_value)
                except ValueError as exc:
                    errors.append(f"{request_id}/{frame_value}: {exc}")
                    continue
                if frame_value not in os.listdir(raw_descriptor):
                    errors.append(f"{request_id}/{frame_value}: raw candidate spelling differs")
                    continue
                if frame_value not in os.listdir(output_descriptor):
                    errors.append(f"{request_id}/{frame_value}: validated output spelling differs")
                    continue
                observation = observations.get(frame_value)
                artifact = request_artifacts.get(frame_value)
                raw_identity = (
                    observation.get("raw_candidate_identity")
                    if isinstance(observation, dict)
                    else None
                )
                if not isinstance(raw_identity, dict) or not isinstance(artifact, dict):
                    errors.append(f"{request_id}/{frame_value}: committed PNG identity is missing")
                    continue
                current_raw = inspect_complete_png(Path(frame_value), dir_fd=raw_descriptor)
                current_validated = inspect_complete_png(
                    Path(frame_value), dir_fd=output_descriptor
                )
                if (
                    current_raw is None
                    or current_raw.get("sha256") != raw_identity.get("sha256")
                    or not _manifest_identity_matches(current_raw, raw_identity)
                ):
                    errors.append(f"{request_id}/{frame_value}: raw candidate changed after commit")
                if (
                    current_validated is None
                    or current_validated.get("sha256") != artifact.get("sha256")
                    or not _manifest_identity_matches(current_validated, artifact)
                ):
                    errors.append(f"{request_id}/{frame_value}: validated PNG changed after commit")
                if lexical_absolute_path(Path(str(artifact.get("path", "")))) != expected_validated_dir / frame_value:
                    errors.append(f"{request_id}/{frame_value}: validated PNG path differs")

            expected_summary = validated_summaries.get(request_id)
            if not isinstance(expected_summary, dict):
                errors.append(f"{request_id}: validated summary identity is missing")
                continue
            summary_name = "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
            if summary_name not in os.listdir(summary_descriptor):
                errors.append(f"{request_id}: validated summary spelling differs")
                continue
            summary_path = Path(summary_name)
            try:
                summary_bytes, summary_identity = read_regular_file_nofollow_with_identity(
                    summary_path,
                    dir_fd=summary_descriptor,
                )
                summary_result = json.loads(summary_bytes.decode("utf-8-sig"))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{request_id}: validated summary is unreadable: {exc}")
                continue
            if (
                hashlib.sha256(summary_bytes).hexdigest() != expected_summary.get("sha256")
                or len(summary_bytes) != expected_summary.get("size_bytes")
                or not _manifest_identity_matches(summary_identity, expected_summary)
            ):
                errors.append(f"{request_id}: validated summary changed after commit")
            if (
                not isinstance(summary_result, dict)
                or summary_result.get("request_id") != request_id
                or summary_result.get("run_id") != run_id
                or summary_result.get("generation_commit_required") is not True
                or summary_result.get("standalone_authoritative") is not False
            ):
                errors.append(f"{request_id}: validated summary contract differs")

        raw_result = committed.get("raw_batch_result")
        if isinstance(raw_result, dict):
            raw_path_value = raw_result.get("path")
            if not isinstance(raw_path_value, str):
                errors.append("raw batch result path is missing")
            else:
                raw_path = lexical_absolute_path(Path(raw_path_value))
                try:
                    relative = raw_path.relative_to(generation_root)
                    raw_parent = remember(
                        open_directory_chain(
                            generation_descriptor,
                            tuple(relative.parts[:-1]),
                            create=False,
                        )
                    )
                    if relative.name not in os.listdir(raw_parent):
                        raise ValueError("raw result spelling differs")
                    raw_bytes, _ = read_regular_file_nofollow_with_identity(
                        Path(relative.name), dir_fd=raw_parent
                    )
                except (OSError, ValueError) as exc:
                    errors.append(f"raw batch result is unavailable: {exc}")
                else:
                    if (
                        hashlib.sha256(raw_bytes).hexdigest() != raw_result.get("sha256")
                        or len(raw_bytes) != raw_result.get("size_bytes")
                    ):
                        errors.append("raw batch result bytes differ from commit")

        source_required = generation_commit.get("source_snapshot_required") is True
        source_snapshot = committed.get("request_source_snapshot")
        source_identities = committed.get("request_source_identity_snapshot")
        staged_path_value = committed.get("staged_requests_base")
        if source_required or any(
            value is not None
            for value in (source_snapshot, source_identities, staged_path_value)
        ):
            if (
                not isinstance(source_snapshot, dict)
                or not isinstance(source_identities, dict)
                or not isinstance(staged_path_value, str)
                or committed.get("request_source_snapshot_verified") is not True
            ):
                errors.append("committed staged source contract is incomplete")
            else:
                try:
                    current_sources, current_source_identities = (
                        snapshot_owned_request_sources(
                            Path(staged_path_value), source_snapshot
                        )
                    )
                except (OSError, ValueError) as exc:
                    errors.append(f"committed staged sources are unavailable: {exc}")
                else:
                    if (
                        current_sources != source_snapshot
                        or current_source_identities != source_identities
                    ):
                        errors.append("committed staged source bytes/identities changed")

        for path, descriptor in directory_bindings:
            if not directory_path_still_names_descriptor(path, descriptor):
                errors.append(f"committed directory binding changed: {path}")
        for parent_descriptor, name, descriptor in child_directory_bindings:
            if not child_name_still_names_descriptor(
                parent_descriptor,
                name,
                descriptor,
            ):
                errors.append(f"committed child directory binding changed: {name}")
        final_commit_bytes, final_commit_identity = (
            read_regular_file_nofollow_with_identity(
                batch_result_json,
                dir_fd=generation_descriptor,
            )
        )
        if final_commit_bytes != commit_bytes or final_commit_identity != commit_identity:
            errors.append("generation commit bytes/identity changed during verification")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"generation commit verification failed: {exc}")
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
    return not errors, errors


def write_validated_batch_results(
    batch_result_json: Path,
    result: dict[str, object],
    *,
    expected_results_base: Path,
    validated_summaries_base: Path,
    expected_output_dirs_by_request: dict[str, Path] | None = None,
    expected_output_identities_by_request: dict[str, tuple[int, int]] | None = None,
    expected_validated_root_identities: dict[str, tuple[int, int]] | None = None,
    validated_outputs_base: Path | None = None,
    raw_batch_result_json: Path | None = None,
    raw_batch_result_bytes: bytes | None = None,
    staged_requests_base: Path | None = None,
    expected_source_snapshot: dict[str, dict[str, str]] | None = None,
    expected_staged_source_identities: dict[str, dict[str, dict[str, int]]] | None = None,
    expected_generation_ancestors: dict[str, dict[str, int]] | None = None,
    run_id: str | None = None,
) -> bool:
    """Publish validated artifacts/summaries, then write the generation commit last."""

    requests_value = result.get("requests")
    requests = requests_value if isinstance(requests_value, list) else []
    results_root = expected_results_base.resolve()
    validated_summary_root = lexical_absolute_path(validated_summaries_base)
    validated_output_root = (
        lexical_absolute_path(validated_outputs_base)
        if validated_outputs_base is not None
        else validated_summary_root.parent / "validated_outputs"
    )
    publication_errors: list[str] = []
    if not requests:
        publication_errors.append("generation contains no requests")
    generation_root = results_root.parent
    generation_descriptor: int | None = None
    validated_output_root_descriptor: int | None = None
    validated_summary_root_descriptor: int | None = None
    raw_output_descriptors: dict[str, int] = {}
    validated_output_descriptors: dict[str, int] = {}
    validated_summary_descriptors: dict[str, int] = {}
    raw_output_dirs: dict[str, Path] = {}
    request_aliases: dict[str, str] = {}

    def close_publication_descriptors() -> None:
        descriptors = {
            *raw_output_descriptors.values(),
            *validated_output_descriptors.values(),
            *validated_summary_descriptors.values(),
        }
        for descriptor in (
            validated_output_root_descriptor,
            validated_summary_root_descriptor,
            generation_descriptor,
        ):
            if descriptor is not None:
                descriptors.add(descriptor)
        for descriptor in descriptors:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def remove_published_files() -> None:
        for descriptor in validated_summary_descriptors.values():
            try:
                os.unlink(
                    "AE_PIXEL_VALIDATION_RENDER_RESULT.json", dir_fd=descriptor
                )
                os.fsync(descriptor)
            except FileNotFoundError:
                pass
        for request_id, descriptor in validated_output_descriptors.items():
            request = next(
                (
                    value
                    for value in requests
                    if isinstance(value, dict)
                    and value.get("request_id") == request_id
                ),
                None,
            )
            frames = (
                request.get("render_candidates", [])
                if isinstance(request, dict)
                else []
            )
            removed = False
            for frame in frames if isinstance(frames, list) else []:
                if not isinstance(frame, str):
                    continue
                try:
                    os.unlink(frame, dir_fd=descriptor)
                    removed = True
                except FileNotFoundError:
                    pass
            if removed:
                os.fsync(descriptor)

    if (
        validated_summary_root.parent != generation_root
        or validated_output_root.parent != generation_root
        or lexical_absolute_path(batch_result_json).parent != generation_root
    ):
        publication_errors.append("validated publication roots escape the generation directory")
    try:
        generation_info = lexical_absolute_path(generation_root).lstat()
        if not stat_module.S_ISDIR(generation_info.st_mode):
            raise ValueError("generation root is not a lexical directory")
        generation_descriptor = open_bound_directory(
            generation_root, (generation_info.st_dev, generation_info.st_ino)
        )
    except (OSError, ValueError) as exc:
        publication_errors.append(f"generation root descriptor binding failed: {exc}")
    try:
        actual_validated_root_identities = bind_output_directory_identities(
            {
                "validated_outputs": validated_output_root,
                "validated_summaries": validated_summary_root,
            },
            create=True,
        )
    except ValueError as exc:
        actual_validated_root_identities = {}
        publication_errors.append(f"validated publication root ownership failed: {exc}")
    if (
        expected_validated_root_identities is not None
        and actual_validated_root_identities != expected_validated_root_identities
    ):
        publication_errors.append("validated publication root identities changed")
    if not publication_errors:
        try:
            root_identities = (
                expected_validated_root_identities
                if expected_validated_root_identities is not None
                else actual_validated_root_identities
            )
            validated_output_root_descriptor = open_bound_directory(
                validated_output_root, root_identities["validated_outputs"]
            )
            validated_summary_root_descriptor = open_bound_directory(
                validated_summary_root, root_identities["validated_summaries"]
            )
        except (OSError, KeyError, ValueError) as exc:
            publication_errors.append(
                f"validated publication root descriptor binding failed: {exc}"
            )

    publication_updates: list[
        tuple[dict[str, object], str, Path, Path, dict[str, dict[str, object]]]
    ] = []
    artifact_manifest: dict[str, dict[str, dict[str, object]]] = {}
    generation_was_valid = (
        result.get("hostless_output_validation", {}).get("status") == "passed"
        if isinstance(result.get("hostless_output_validation"), dict)
        else False
    )

    # Bind every summary destination before writing even one summary. Production
    # generations also bind every raw/output request directory before any copy.
    if not publication_errors:
        seen_request_ids: set[str] = set()
        seen_aliases: set[str] = set()
        for request in requests:
            if not isinstance(request, dict):
                publication_errors.append("publication request entry is not an object")
                continue
            request_id = request.get("request_id")
            if not isinstance(request_id, str):
                publication_errors.append(f"invalid promoted request at publication: {request_id!r}")
                continue
            request_key = request_id.casefold()
            alias = request_output_alias(request_id)
            alias_key = alias.casefold()
            if request_key in seen_request_ids or alias_key in seen_aliases:
                publication_errors.append(
                    f"duplicate request/alias at publication: {request_id!r}"
                )
                continue
            seen_request_ids.add(request_key)
            seen_aliases.add(alias_key)
            request_aliases[request_id] = alias

    if not publication_errors:
        assert validated_summary_root_descriptor is not None
        for request in requests:
            assert isinstance(request, dict)
            request_id = str(request["request_id"])
            alias = request_aliases[request_id]
            try:
                validated_summary_descriptors[request_id] = (
                    open_or_create_child_directory(
                        validated_summary_root_descriptor,
                        alias,
                        require_new=True,
                    )
                )
            except (OSError, ValueError) as exc:
                publication_errors.append(
                    f"{request_id}: validated summary directory preflight failed: {exc}"
                )

    if generation_was_valid and not publication_errors:
        assert validated_output_root_descriptor is not None
        for request in requests:
            assert isinstance(request, dict)
            request_id = str(request["request_id"])
            rendered = request.get("rendered")
            observations = request.get("hostless_png_observations")
            if not isinstance(rendered, list) or not rendered or not isinstance(observations, dict):
                publication_errors.append(
                    f"invalid promoted request at publication: {request_id!r}"
                )
                continue
            if expected_output_dirs_by_request is not None:
                raw_output_dir = expected_output_dirs_by_request.get(request_id)
            else:
                declared_raw_output_dir = Path(str(request.get("output_dir", "")))
                raw_output_dir = (
                    declared_raw_output_dir.parent.resolve() / declared_raw_output_dir.name
                    if declared_raw_output_dir.is_absolute()
                    else declared_raw_output_dir
                )
            if raw_output_dir is None:
                publication_errors.append(f"missing raw output binding: {request_id}")
                continue
            try:
                raw_output_info = raw_output_dir.lstat()
            except OSError as exc:
                publication_errors.append(f"{request_id}: raw output directory unavailable: {exc}")
                continue
            raw_output_identity = (raw_output_info.st_dev, raw_output_info.st_ino)
            expected_output_identity = (
                expected_output_identities_by_request.get(request_id)
                if expected_output_identities_by_request is not None
                else raw_output_identity
            )
            if (
                not stat_module.S_ISDIR(raw_output_info.st_mode)
                or raw_output_dir.parent != results_root
                or raw_output_identity != expected_output_identity
            ):
                publication_errors.append(f"{request_id}: raw output ownership changed")
                continue
            try:
                raw_output_descriptors[request_id] = open_bound_directory(
                    raw_output_dir, expected_output_identity
                )
                validated_output_descriptors[request_id] = (
                    open_or_create_child_directory(
                        validated_output_root_descriptor,
                        request_aliases[request_id],
                        require_new=True,
                    )
                )
                raw_output_dirs[request_id] = raw_output_dir
            except (OSError, ValueError) as exc:
                publication_errors.append(
                    f"{request_id}: publication directory preflight failed: {exc}"
                )

    summary_preflight_complete = (
        not publication_errors
        and len(validated_summary_descriptors) == len(requests)
    )

    def bindings_are_intact(*, include_outputs: bool) -> bool:
        if (
            generation_descriptor is None
            or validated_summary_root_descriptor is None
            or not directory_path_still_names_descriptor(
                generation_root, generation_descriptor
            )
            or not directory_path_still_names_descriptor(
                validated_summary_root, validated_summary_root_descriptor
            )
        ):
            return False
        for request_id, descriptor in validated_summary_descriptors.items():
            if not child_name_still_names_descriptor(
                validated_summary_root_descriptor,
                request_aliases[request_id],
                descriptor,
            ):
                return False
        if include_outputs:
            if (
                validated_output_root_descriptor is None
                or not directory_path_still_names_descriptor(
                    validated_output_root, validated_output_root_descriptor
                )
            ):
                return False
            for request_id, descriptor in validated_output_descriptors.items():
                if not child_name_still_names_descriptor(
                    validated_output_root_descriptor,
                    request_aliases[request_id],
                    descriptor,
                ):
                    return False
                raw_descriptor = raw_output_descriptors.get(request_id)
                raw_output_dir = raw_output_dirs.get(request_id)
                if (
                    raw_descriptor is None
                    or raw_output_dir is None
                    or not directory_path_still_names_descriptor(
                        raw_output_dir, raw_descriptor
                    )
                ):
                    return False
        return True

    if generation_was_valid and not publication_errors:
        for request in requests:
            assert isinstance(request, dict)
            request_id = str(request["request_id"])
            rendered = request.get("rendered")
            observations = request.get("hostless_png_observations")
            assert isinstance(rendered, list)
            assert isinstance(observations, dict)
            raw_output_dir = raw_output_dirs[request_id]
            validated_output_dir = (
                validated_output_root / request_aliases[request_id]
            )
            request_artifacts: dict[str, dict[str, object]] = {}
            try:
                for frame_value in rendered:
                    if not isinstance(frame_value, str):
                        raise ValueError("rendered frame is not a string")
                    source = _candidate_path(
                        {"output_dir": str(raw_output_dir)},
                        frame_value,
                        expected_results_base=expected_results_base,
                    )
                    observation = observations.get(frame_value)
                    if not isinstance(observation, dict):
                        raise ValueError(f"missing promoted observation: {frame_value}")
                    destination = validated_output_dir / frame_value
                    final = copy_bound_validated_png(
                        source,
                        destination,
                        observation,
                        source_directory_descriptor=raw_output_descriptors[request_id],
                        destination_directory_descriptor=(
                            validated_output_descriptors[request_id]
                        ),
                    )
                    request_artifacts[frame_value] = {
                        "path": str(destination),
                        **final,
                    }
            except (OSError, ValueError) as exc:
                publication_errors.append(f"{request_id}: {exc}")
                continue
            publication_updates.append(
                (request, request_id, raw_output_dir, validated_output_dir, request_artifacts)
            )
            artifact_manifest[request_id] = request_artifacts
        if len(publication_updates) != len(requests):
            publication_errors.append("not every request produced a validated output publication")
        if not publication_errors and not bindings_are_intact(include_outputs=True):
            publication_errors.append(
                "publication directory bindings changed during validated output copy"
            )

    publication_valid = generation_was_valid and not publication_errors
    if publication_valid:
        for request, request_id, raw_output_dir, validated_output_dir, request_artifacts in publication_updates:
            observations = request.get("hostless_png_observations")
            assert isinstance(observations, dict)
            for frame, artifact in request_artifacts.items():
                observation = observations.get(frame)
                assert isinstance(observation, dict)
                raw_identity = {
                    key: observation.get(key)
                    for key in (
                        "path",
                        "sha256",
                        "device",
                        "inode",
                        "size_bytes",
                        "modified_ns",
                        "changed_ns",
                        "link_count",
                    )
                }
                observation.update(artifact)
                observation["raw_candidate_identity"] = raw_identity
                observation["validated_copy"] = True
                observation["authoritative"] = True
            request["raw_candidate_output_dir"] = str(raw_output_dir)
            request["validated_output_dir"] = str(validated_output_dir)
            request["output_dir"] = str(validated_output_dir)
    elif publication_errors:
        rollback_generation_promotion(
            result,
            "publication validation failed: " + " | ".join(publication_errors),
        )

    if raw_batch_result_json is not None:
        if raw_batch_result_bytes is None:
            raw_batch_result_bytes = read_regular_file_nofollow(raw_batch_result_json)
        if generation_descriptor is None:
            publication_errors.append("generation root descriptor is unavailable")
            rollback_generation_promotion(
                result, "generation root descriptor is unavailable"
            )
            publication_valid = False
            persisted_raw = b""
        else:
            atomic_write_bytes(
                raw_batch_result_json,
                raw_batch_result_bytes,
                mode=0o444,
                parent_dir_fd=generation_descriptor,
            )
            persisted_raw = read_regular_file_nofollow(
                raw_batch_result_json, dir_fd=generation_descriptor
            )
        if persisted_raw != raw_batch_result_bytes:
            raw_error = "raw batch bytes changed during publication"
            publication_errors.append(raw_error)
            rollback_generation_promotion(result, raw_error)
            publication_valid = False
        result["raw_batch_result"] = {
            "path": str(raw_batch_result_json.absolute()),
            "sha256": hashlib.sha256(raw_batch_result_bytes).hexdigest(),
            "size_bytes": len(raw_batch_result_bytes),
            "digest_of_exact_parsed_bytes": True,
        }

    result["schema_version"] = 2
    effective_run_id = run_id or result.get("run_id")
    if not isinstance(effective_run_id, str) or not effective_run_id:
        # Keep the direct hostless persistence API compatible while ensuring
        # every authoritative generation still has a concrete evidence nonce.
        effective_run_id = f"hostless_{secrets.token_hex(16)}"
    result["run_id"] = effective_run_id
    result["raw_candidate_root"] = str(results_root)
    result["validated_output_root"] = str(validated_output_root)
    result["validated_outputs"] = artifact_manifest if publication_valid else {}
    result["validated_summary_root"] = str(validated_summary_root)
    result["publication_validation"] = {
        "status": "passed" if publication_valid else "failed",
        "raw_candidates_revalidated": publication_valid,
        "validated_outputs_atomically_published": publication_valid,
        "errors": publication_errors,
    }

    summary_digests: dict[str, dict[str, object]] = {}
    summaries_safe = publication_valid and summary_preflight_complete and bindings_are_intact(
        include_outputs=bool(validated_output_descriptors)
    )
    written_summary_ids: list[str] = []
    if summaries_safe:
        try:
            for request in requests:
                assert isinstance(request, dict)
                request_id = str(request["request_id"])
                summary_dir = (
                    validated_summary_root / request_aliases[request_id]
                )
                summary_path = summary_dir / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                request["validated_summary_path"] = str(summary_path)
                request["generation_commit_required"] = True
                request["generation_commit_path"] = str(batch_result_json.absolute())
                request["generation_status"] = (
                    "pending_generation_commit" if publication_valid else "failed"
                )
                request["standalone_authoritative"] = False
                request["run_id"] = result.get("run_id")
                summary_descriptor = validated_summary_descriptors[request_id]
                summary_payload = write_result_json(
                    summary_path,
                    request,
                    parent_dir_fd=summary_descriptor,
                )
                final_descriptor = os.open(
                    summary_path.name,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=summary_descriptor,
                )
                try:
                    os.fchmod(final_descriptor, 0o444)
                    os.fsync(final_descriptor)
                    summary_identity = identity_payload(os.fstat(final_descriptor))
                finally:
                    os.close(final_descriptor)
                written_summary_ids.append(request_id)
                summary_digests[request_id] = {
                    "path": str(summary_path),
                    "sha256": hashlib.sha256(summary_payload).hexdigest(),
                    "size_bytes": len(summary_payload),
                    "digest_of_exact_written_bytes": True,
                    **summary_identity,
                }
        except (OSError, ValueError) as exc:
            publication_errors.append(f"validated summary publication failed: {exc}")
            rollback_generation_promotion(
                result, f"validated summary publication failed: {exc}"
            )
            publication_valid = False
            summary_digests = {}
            for descriptor in validated_summary_descriptors.values():
                try:
                    os.unlink(
                        "AE_PIXEL_VALIDATION_RENDER_RESULT.json",
                        dir_fd=descriptor,
                    )
                except FileNotFoundError:
                    pass
    elif publication_valid and summary_preflight_complete:
        publication_errors.append("validated summary directory bindings changed")
        rollback_generation_promotion(
            result, "validated summary directory bindings changed"
        )
        publication_valid = False

    if summary_digests and not bindings_are_intact(
        include_outputs=bool(validated_output_descriptors)
    ):
        publication_errors.append("publication directory bindings changed before commit")
        rollback_generation_promotion(
            result, "publication directory bindings changed before commit"
        )
        publication_valid = False
        summary_digests = {}
        for descriptor in validated_summary_descriptors.values():
            try:
                os.unlink(
                    "AE_PIXEL_VALIDATION_RENDER_RESULT.json", dir_fd=descriptor
                )
            except FileNotFoundError:
                pass

    final_errors: list[str] = []
    if publication_valid:
        if not bindings_are_intact(include_outputs=True):
            final_errors.append("publication directory bindings changed at commit boundary")
        for request_id, artifacts in artifact_manifest.items():
            descriptor = validated_output_descriptors.get(request_id)
            if descriptor is None:
                final_errors.append(f"{request_id}: validated output descriptor is missing")
                continue
            for frame, expected_artifact in artifacts.items():
                current = inspect_complete_png(
                    Path(str(expected_artifact.get("path", frame))),
                    dir_fd=descriptor,
                )
                if (
                    current is None
                    or current.get("sha256") != expected_artifact.get("sha256")
                    or _png_identity(current) != _png_identity(expected_artifact)
                ):
                    final_errors.append(
                        f"{request_id}/{frame}: validated PNG changed before commit"
                    )
        for request_id, expected_summary in summary_digests.items():
            descriptor = validated_summary_descriptors.get(request_id)
            if descriptor is None:
                final_errors.append(f"{request_id}: validated summary descriptor is missing")
                continue
            summary_path = Path(str(expected_summary["path"]))
            try:
                payload, current_identity = read_regular_file_nofollow_with_identity(
                    summary_path, dir_fd=descriptor
                )
            except (OSError, ValueError) as exc:
                final_errors.append(f"{request_id}: validated summary unavailable: {exc}")
                continue
            expected_identity = {
                key: expected_summary.get(key)
                for key in (
                    "device",
                    "inode",
                    "size_bytes",
                    "modified_ns",
                    "changed_ns",
                    "link_count",
                )
            }
            if (
                hashlib.sha256(payload).hexdigest() != expected_summary.get("sha256")
                or len(payload) != expected_summary.get("size_bytes")
                or current_identity != expected_identity
            ):
                final_errors.append(
                    f"{request_id}: validated summary bytes/identity changed before commit"
                )
        if raw_batch_result_json is not None and raw_batch_result_bytes is not None:
            if generation_descriptor is None:
                final_errors.append("generation descriptor missing for raw result recheck")
            else:
                try:
                    final_raw = read_regular_file_nofollow(
                        raw_batch_result_json, dir_fd=generation_descriptor
                    )
                except (OSError, ValueError) as exc:
                    final_errors.append(f"raw batch result unavailable before commit: {exc}")
                else:
                    if final_raw != raw_batch_result_bytes:
                        final_errors.append("raw batch result bytes changed before commit")
        if (
            staged_requests_base is not None
            and expected_source_snapshot is not None
            and expected_staged_source_identities is not None
        ):
            try:
                final_sources, final_source_identities = snapshot_owned_request_sources(
                    staged_requests_base, expected_source_snapshot
                )
            except (OSError, ValueError) as exc:
                final_errors.append(f"staged request recheck failed before commit: {exc}")
            else:
                if (
                    final_sources != expected_source_snapshot
                    or final_source_identities != expected_staged_source_identities
                ):
                    final_errors.append("staged request bytes/identities changed before commit")
        if expected_generation_ancestors is not None:
            try:
                final_generation_ancestors = snapshot_generation_ancestors(
                    generation_root
                )
            except (OSError, ValueError) as exc:
                final_errors.append(f"generation ancestor recheck failed: {exc}")
            else:
                if final_generation_ancestors != expected_generation_ancestors:
                    final_errors.append("generation ancestor identities changed before commit")

    if final_errors:
        publication_errors.extend(final_errors)
        rollback_generation_promotion(
            result, "final commit-boundary validation failed: " + " | ".join(final_errors)
        )
        publication_valid = False
        summary_digests = {}
        artifact_manifest = {}
        for descriptor in validated_summary_descriptors.values():
            try:
                os.unlink(
                    "AE_PIXEL_VALIDATION_RENDER_RESULT.json", dir_fd=descriptor
                )
            except FileNotFoundError:
                pass
        for request_id, descriptor in validated_output_descriptors.items():
            request = next(
                (
                    value
                    for value in requests
                    if isinstance(value, dict) and value.get("request_id") == request_id
                ),
                None,
            )
            frames = request.get("render_candidates", []) if isinstance(request, dict) else []
            for frame in frames if isinstance(frames, list) else []:
                if not isinstance(frame, str):
                    continue
                try:
                    os.unlink(frame, dir_fd=descriptor)
                except FileNotFoundError:
                    pass

    if not publication_valid:
        for descriptor in validated_summary_descriptors.values():
            try:
                os.unlink(
                    "AE_PIXEL_VALIDATION_RENDER_RESULT.json", dir_fd=descriptor
                )
            except FileNotFoundError:
                pass
        for request_id, descriptor in validated_output_descriptors.items():
            request = next(
                (
                    value
                    for value in requests
                    if isinstance(value, dict) and value.get("request_id") == request_id
                ),
                None,
            )
            frames = request.get("render_candidates", []) if isinstance(request, dict) else []
            for frame in frames if isinstance(frames, list) else []:
                if not isinstance(frame, str):
                    continue
                try:
                    os.unlink(frame, dir_fd=descriptor)
                except FileNotFoundError:
                    pass
        artifact_manifest = {}
        result["validated_outputs"] = {}
        for request in requests:
            if isinstance(request, dict):
                request["generation_status"] = "failed"
    result["validated_summaries"] = summary_digests
    publication_validation = result.get("publication_validation")
    if isinstance(publication_validation, dict):
        publication_validation.update(
            status="passed" if publication_valid else "failed",
            validated_outputs_atomically_published=publication_valid,
            errors=publication_errors,
        )
    if publication_valid:
        for request in requests:
            if isinstance(request, dict):
                request["generation_status"] = "passed"
    result["generation_commit"] = {
        "schema": "olm.ae-batch-generation-commit/1",
        "run_id": result.get("run_id"),
        "status": result.get("hostless_output_validation", {}).get("status"),
        "immutable_generation": True,
        "source_snapshot_required": (
            staged_requests_base is not None
            or expected_source_snapshot is not None
            or expected_staged_source_identities is not None
        ),
        "post_commit_verification_required": True,
        "consumer_verifier": "scripts.run_ae_validation_batch.verify_generation_commit",
        "committed_at": datetime.now().astimezone().isoformat(),
        "commit_marker_written_last": True,
    }

    def revoke_commit_attempt(commit_errors: list[str]) -> None:
        nonlocal publication_valid
        verification_error = (
            "generation commit publication/verification failed: "
            + " | ".join(commit_errors)
        )
        publication_errors.extend(commit_errors)
        rollback_generation_promotion(result, verification_error)
        publication_valid = False
        remove_published_files()
        result["validated_outputs"] = {}
        result["validated_summaries"] = {}
        result.pop("generation_commit_anchor", None)
        for request in requests:
            if isinstance(request, dict):
                request["generation_status"] = "failed"
        current_publication_validation = result.get("publication_validation")
        if isinstance(current_publication_validation, dict):
            current_publication_validation.update(
                status="failed",
                raw_candidates_revalidated=False,
                validated_outputs_atomically_published=False,
                errors=publication_errors,
            )
        generation_commit = result.get("generation_commit")
        if isinstance(generation_commit, dict):
            generation_commit.update(
                status="failed",
                post_commit_verification="failed",
                verification_errors=commit_errors,
                committed_at=datetime.now().astimezone().isoformat(),
            )

    def persist_failed_marker(generation_descriptor: int) -> None:
        try:
            failed_payload = write_result_json(
                batch_result_json,
                result,
                parent_dir_fd=generation_descriptor,
            )
            persisted_failed = read_regular_file_nofollow(
                batch_result_json,
                dir_fd=generation_descriptor,
            )
            if persisted_failed != failed_payload:
                raise ValueError("failed generation marker bytes changed")
        except (OSError, ValueError):
            try:
                os.unlink(batch_result_json.name, dir_fd=generation_descriptor)
                os.fsync(generation_descriptor)
            except FileNotFoundError:
                pass

    try:
        if generation_descriptor is None:
            raise ValueError("generation root descriptor is unavailable for commit")
        canonical_commit_bytes = (
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        generation_info = os.fstat(generation_descriptor)
        generation_identity = (generation_info.st_dev, generation_info.st_ino)
        try:
            written_commit_bytes = write_result_json(
                batch_result_json,
                result,
                parent_dir_fd=generation_descriptor,
            )
        except (OSError, ValueError) as exc:
            revoke_commit_attempt([f"generation commit write failed: {exc}"])
            persist_failed_marker(generation_descriptor)
        else:
            commit_verified, commit_errors = verify_generation_commit(
                batch_result_json,
                expected_run_id=str(result.get("run_id")),
                expected_commit_bytes=canonical_commit_bytes,
                expected_generation_identity=generation_identity,
            )
            if written_commit_bytes != canonical_commit_bytes:
                commit_errors.insert(
                    0, "commit writer returned bytes that differ from canonical payload"
                )
                commit_verified = False
            if publication_valid and commit_verified:
                result["generation_commit_anchor"] = {
                    "path": str(lexical_absolute_path(batch_result_json)),
                    "sha256": hashlib.sha256(canonical_commit_bytes).hexdigest(),
                    "size_bytes": len(canonical_commit_bytes),
                    "run_id": result.get("run_id"),
                    "generation_device": generation_identity[0],
                    "generation_inode": generation_identity[1],
                    "consumer_verifier": (
                        "scripts.run_ae_validation_batch.verify_generation_commit"
                    ),
                }
            elif publication_valid:
                revoke_commit_attempt(commit_errors)
                persist_failed_marker(generation_descriptor)
    finally:
        close_publication_descriptors()
    return publication_valid and result["generation_commit"]["status"] == "passed"


def run_locked_batch(
    *,
    args: argparse.Namespace,
    run_dir: Path,
    wrapper_jsx: Path,
    raw_batch_result_json: Path,
    commit_result_json: Path,
    published_result_json: Path | None,
    requests_base: Path,
    results_base: Path,
    validated_outputs_base: Path,
    validated_summaries_base: Path,
    run_id: str,
    request_ids: list[str],
    expected_frames: dict[str, list[str]],
    expected_output_dirs: dict[str, Path],
    expected_output_identities: dict[str, tuple[int, int]],
    expected_validated_root_identities: dict[str, tuple[int, int]],
    expected_source_snapshot: dict[str, dict[str, str]],
    expected_staged_source_identities: dict[str, dict[str, dict[str, int]]],
    js: str,
) -> int:
    """Run AE and keep result intake plus hostless promotion under one AE lock."""

    try:
        locked_output_dirs = expected_output_directories(results_base, expected_frames)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] output path preflight changed while waiting for AE lock: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if locked_output_dirs != expected_output_dirs:
        print("[FAIL] output path bindings changed while waiting for AE lock", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    try:
        locked_output_identities = bind_output_directory_identities(
            expected_output_dirs, create=False
        )
    except ValueError as exc:
        print(f"[FAIL] output directory ownership changed while waiting: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if locked_output_identities != expected_output_identities:
        print("[FAIL] output directory identities changed while waiting", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    try:
        locked_validated_root_identities = bind_output_directory_identities(
            {
                "validated_outputs": validated_outputs_base,
                "validated_summaries": validated_summaries_base,
            },
            create=False,
        )
    except ValueError as exc:
        print(f"[FAIL] validated root ownership changed while waiting: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if locked_validated_root_identities != expected_validated_root_identities:
        print("[FAIL] validated root identities changed while waiting", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    try:
        (
            locked_source_snapshot,
            locked_staged_source_identities,
        ) = snapshot_owned_request_sources(requests_base, expected_source_snapshot)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] request sources changed while waiting for AE lock: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if locked_source_snapshot != expected_source_snapshot:
        print("[FAIL] request source digests changed while waiting for AE lock", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if locked_staged_source_identities != expected_staged_source_identities:
        print("[FAIL] staged request source identities changed while waiting for AE lock", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    active_marker = ae_active_marker_path(args.lock_path.resolve())
    if active_marker.exists():
        print(f"[FAIL] prior AE host run may still be active: {active_marker}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if raw_batch_result_json.exists():
        try:
            raw_batch_result_json.unlink()
        except OSError as exc:
            print(f"[FAIL] could not remove stale batch result JSON: {exc}", file=sys.stderr)
            print(f"[INFO] run_dir: {run_dir}")
            return 1
        if raw_batch_result_json.exists():
            print(f"[FAIL] stale batch result JSON still exists: {raw_batch_result_json}", file=sys.stderr)
            print(f"[INFO] run_dir: {run_dir}")
            return 1
    wrapper_jsx.write_text(js, encoding="utf-8")
    try:
        expected_generation_ancestors = snapshot_generation_ancestors(run_dir)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] generation ancestor binding failed before AE: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    apple_script = (
        f"with timeout of {int(args.timeout)} seconds\n"
        f"tell application {js_string(args.app_name)} to DoScriptFile POSIX file {js_string(str(wrapper_jsx))} with override\n"
        "end timeout\n"
    )
    host_started_ns = time.time_ns()
    write_result_json(
        active_marker,
        {
            "schema": "olm.ae-host-active-lease/1",
            "kind": "batch",
            "run_id": run_id,
            "run_dir": str(run_dir),
            "host_started_ns": host_started_ns,
            "status": "host_call_active_or_indeterminate",
        },
    )
    try:
        proc = subprocess.run(
            ["osascript"],
            input=apple_script,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout + 30,
        )
    except subprocess.TimeoutExpired:
        print(
            f"[FAIL] AE host call timed out; active lease retained: {active_marker}",
            file=sys.stderr,
        )
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print(f"[FAIL] osascript exited {proc.returncode}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return proc.returncode
    if not raw_batch_result_json.exists():
        print(f"[FAIL] AE did not write batch result JSON: {raw_batch_result_json}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    try:
        raw_batch_result_bytes = read_regular_file_nofollow(raw_batch_result_json)
        result = json.loads(raw_batch_result_bytes.decode("utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] invalid batch result JSON: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if not isinstance(result, dict):
        print("[FAIL] batch result JSON must be an object", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    source_errors: list[str] = []
    try:
        returned_generation_ancestors = snapshot_generation_ancestors(run_dir)
    except (OSError, ValueError) as exc:
        returned_generation_ancestors = {}
        source_errors.append(f"generation ancestor snapshot failed after AE: {exc}")
    if returned_generation_ancestors != expected_generation_ancestors:
        source_errors.append("generation ancestor identities changed during AE run")
    try:
        (
            returned_source_snapshot,
            returned_staged_source_identities,
        ) = snapshot_owned_request_sources(requests_base, expected_source_snapshot)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        returned_source_snapshot = {}
        returned_staged_source_identities = {}
        source_errors.append(f"request source snapshot failed after AE: {exc}")
    if returned_source_snapshot != expected_source_snapshot:
        source_errors.append("request manifest/reference/input bytes changed during AE run")
    if returned_staged_source_identities != expected_staged_source_identities:
        source_errors.append("request manifest/reference/input identities changed during AE run")
    result["request_source_snapshot"] = expected_source_snapshot
    result["request_source_identity_snapshot"] = expected_staged_source_identities
    result["request_source_snapshot_verified"] = not source_errors
    result["staged_requests_base"] = str(requests_base.resolve())
    outputs_valid = validate_batch_outputs(
        result,
        not_before_ns=host_started_ns,
        expected_request_ids=request_ids,
        expected_run_id=run_id,
        expected_frames_by_request=expected_frames,
        expected_output_dirs_by_request=expected_output_dirs,
        expected_output_identities_by_request=expected_output_identities,
        expected_results_base=results_base,
        external_errors=source_errors,
        timeout_seconds=output_wait_timeout(float(args.timeout)),
    )
    publication_valid = write_validated_batch_results(
        commit_result_json,
        result,
        expected_results_base=results_base,
        expected_output_dirs_by_request=expected_output_dirs,
        expected_output_identities_by_request=expected_output_identities,
        expected_validated_root_identities=expected_validated_root_identities,
        validated_outputs_base=validated_outputs_base,
        validated_summaries_base=validated_summaries_base,
        raw_batch_result_json=raw_batch_result_json,
        raw_batch_result_bytes=raw_batch_result_bytes,
        staged_requests_base=requests_base,
        expected_source_snapshot=expected_source_snapshot,
        expected_staged_source_identities=expected_staged_source_identities,
        expected_generation_ancestors=expected_generation_ancestors,
        run_id=run_id,
    )
    outputs_valid = outputs_valid and publication_valid
    if published_result_json is not None and published_result_json != commit_result_json:
        result["canonical_commit_path"] = str(commit_result_json)
        published_result_json.parent.mkdir(parents=True, exist_ok=True)
        write_result_json(published_result_json, result)
    try:
        active_marker.unlink()
    except OSError as exc:
        print(f"[FAIL] could not clear AE active lease: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    if not outputs_valid:
        validation = result.get("hostless_output_validation", {})
        assert isinstance(validation, dict)
        print(
            "[FAIL] AE batch output integrity validation failed: "
            f"{validation.get('rendered_count', 0)}/{validation.get('candidate_count', 0)} rendered",
            file=sys.stderr,
        )
        print(f"[INFO] run_dir: {run_dir}")
        print(f"[INFO] batch_result_json: {commit_result_json}")
        return 1
    print("[OK] AE batch render finished")
    print(f"[INFO] run_dir: {run_dir}")
    print(f"[INFO] batch_result_json: {commit_result_json}")
    commit_anchor = result.get("generation_commit_anchor")
    if isinstance(commit_anchor, dict) and isinstance(
        commit_anchor.get("sha256"), str
    ):
        print(f"[INFO] generation_commit_sha256: {commit_anchor['sha256']}")
    if published_result_json is not None and published_result_json != commit_result_json:
        print(f"[INFO] published_batch_result_json: {published_result_json}")
    requests = result.get("requests")
    assert isinstance(requests, list)
    print(f"[INFO] requests_rendered: {len(requests)}")
    observations = [
        observation
        for request in requests
        if isinstance(request, dict)
        for observation in (request.get("hostless_png_observations") or {}).values()
    ]
    if observations:
        stable = sum(
            1
            for observation in observations
            if isinstance(observation, dict) and observation.get("status") == "stable"
        )
        print(f"[INFO] png_observations: {stable}/{len(observations)} stable")
    return 0


def run_main_under_lock(args: argparse.Namespace) -> int:
    root = repo_root()
    base_dir = (args.base_dir or (root / "handoff" / "ae_pixel_validation_20260618")).resolve()
    requests_base = (args.requests_base or (base_dir / "requests")).resolve()
    requested_results_base = args.results_base.resolve() if args.results_base else None
    run_id = (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{os.getpid()}_"
        f"{secrets.token_hex(8)}"
    )
    run_parent = requested_results_base or (base_dir / "batch_runs")
    run_dir = run_parent / f"batch_run_{run_id}"
    try:
        run_parent.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        print(f"[FAIL] could not create exclusive generation directory: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    results_base = run_dir / "raw_candidates"
    results_base.mkdir(parents=True, exist_ok=True)
    runtime_dir = run_dir / "runtime"
    runtime_dir.mkdir(parents=False, exist_ok=False)
    validated_outputs_base = run_dir / "validated_outputs"
    validated_summaries_base = run_dir / "validated_summaries"
    progress_log = (args.progress_log or (runtime_dir / "AE_PIXEL_VALIDATION_PROGRESS.log")).resolve()
    raw_batch_result_json = runtime_dir / "AE_PIXEL_VALIDATION_BATCH_RESULT.raw.json"
    commit_result_json = run_dir / "AE_PIXEL_VALIDATION_BATCH_RESULT.json"
    published_result_json = args.batch_result_json.resolve() if args.batch_result_json else None
    wrapper_jsx = run_dir / "AE_VALIDATION_BATCH_WRAPPER.jsx"
    jsx_path = root / "scripts" / "ae_pixel_validation_render.jsx"

    try:
        for label, path in (
            ("base directory", base_dir),
            ("requests base", requests_base),
            ("raw candidate root", results_base),
            ("progress log", progress_log),
            ("raw batch result", raw_batch_result_json),
            ("commit result", commit_result_json),
            ("wrapper JSX", wrapper_jsx),
            ("render JSX", jsx_path),
        ):
            validate_extendscript_path(path, label)
    except ValueError as exc:
        print(f"[FAIL] unsafe AE path: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1

    try:
        request_ids = selected_request_ids(args, base_dir)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] invalid request-id selection: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    staged_requests_base = run_dir / "source_capsule" / "staged_requests"
    try:
        original_frames = load_expected_frames(requests_base, request_ids)
        original_source_snapshot = snapshot_request_sources(requests_base, request_ids)
        expected_staged_source_identities = stage_request_sources(
            requests_base,
            staged_requests_base,
            original_source_snapshot,
        )
        expected_frames = load_expected_frames(staged_requests_base, request_ids)
        (
            expected_source_snapshot,
            verified_staged_source_identities,
        ) = snapshot_owned_request_sources(
            staged_requests_base, original_source_snapshot
        )
        if (
            expected_frames != original_frames
            or expected_source_snapshot != original_source_snapshot
            or verified_staged_source_identities != expected_staged_source_identities
        ):
            raise ValueError("staged request contract differs from validated original")
        expected_output_dirs = expected_output_directories(results_base, expected_frames)
        expected_output_identities = bind_output_directory_identities(
            expected_output_dirs, create=True
        )
        expected_validated_root_identities = bind_output_directory_identities(
            {
                "validated_outputs": validated_outputs_base,
                "validated_summaries": validated_summaries_base,
            },
            create=True,
        )
        validate_extendscript_path(staged_requests_base, "staged requests base")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] invalid/staging pre-host request sources: {exc}", file=sys.stderr)
        print(f"[INFO] run_dir: {run_dir}")
        return 1
    env_lines = [
        f"$.setenv('OLM_AE_BASE_DIR', {js_string(str(base_dir))});",
        f"$.setenv('OLM_AE_REQUESTS_BASE', {js_string(str(staged_requests_base))});",
        f"$.setenv('OLM_AE_RESULTS_BASE', {js_string(str(results_base))});",
        f"$.setenv('OLM_AE_PROGRESS_LOG', {js_string(str(progress_log))});",
        f"$.setenv('OLM_AE_BATCH_RESULT_JSON', {js_string(str(raw_batch_result_json))});",
        f"$.setenv('OLM_AE_RUN_ID', {js_string(run_id)});",
    ]
    env_lines.append(f"$.setenv('OLM_AE_REQUEST_IDS_JSON', {js_string(json.dumps(request_ids))});")

    js = "\n".join(
        [
            *env_lines,
            f"$.evalFile(new File({js_string(str(jsx_path))}));",
        ]
    )
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True)
        args.dump_js.write_text(js, encoding="utf-8")
        print(f"[OK] wrote ExtendScript wrapper: {args.dump_js}")
        return 0

    return run_locked_batch(
        args=args,
        run_dir=run_dir,
        wrapper_jsx=wrapper_jsx,
        raw_batch_result_json=raw_batch_result_json,
        commit_result_json=commit_result_json,
        published_result_json=published_result_json,
        requests_base=staged_requests_base,
        results_base=results_base,
        validated_outputs_base=validated_outputs_base,
        validated_summaries_base=validated_summaries_base,
        run_id=run_id,
        request_ids=request_ids,
        expected_frames=expected_frames,
        expected_output_dirs=expected_output_dirs,
        expected_output_identities=expected_output_identities,
        expected_validated_root_identities=expected_validated_root_identities,
        expected_source_snapshot=expected_source_snapshot,
        expected_staged_source_identities=expected_staged_source_identities,
        js=js,
    )


def main() -> int:
    args = parse_args()
    with ae_lock(args.lock_path.resolve()):
        return run_main_under_lock(args)


if __name__ == "__main__":
    sys.exit(main())
