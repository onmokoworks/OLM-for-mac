#!/usr/bin/env python3
"""Run scripts/ae_render_single_case.jsx through a live After Effects instance."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import stat as stat_module
import subprocess
import sys
import time
import zlib
from datetime import datetime
from pathlib import Path
from typing import Callable, NamedTuple


VOLATILE_AE_ENV_KEYS = (
    "OLM_AE_DISABLE_EFFECT",
    "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT",
    "OLM_AE_FORCE_NEW_PROJECT",
    "OLM_AE_FORCE_SOFTWARE",
    "OLM_AE_INPUT_ALPHA_MODE",
    "OLM_AE_INPUT_FILE_OVERRIDE",
    "OLM_AE_PAUSE_BEFORE_RENDER",
    "OLM_AE_READY_MARKER",
    "OLM_AE_CONTINUE_MARKER",
    "OLM_AE_PAUSE_TIMEOUT_SECONDS",
    "OLM_DBLUR_CAPTURE_PREFIX",
)
RUNNER_OWNED_AE_ENV_KEYS = frozenset({
    "OLM_AE_REQUEST_DIR",
    "OLM_AE_CASE_ID",
    "OLM_AE_OUTPUT_DIR",
    "OLM_AE_LOG_PATH",
    "OLM_AE_RESULT_JSON",
    "OLM_AE_PARAM_OVERRIDES_JSON",
    "OLM_AE_OUTPUT_MODE",
    "OLM_AE_OUTPUT_TEMPLATE",
    "OLM_AE_KEEP_OPEN",
})

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXR_MAGIC = b"\x76\x2f\x31\x01"
OUTPUT_STABLE_WINDOW_SECONDS = 2.0
OUTPUT_POLL_INTERVAL_SECONDS = 0.25
OUTPUT_COMPLETION_TIMEOUT_SECONDS = 120.0
OUTPUT_FRESHNESS_SLACK_NS = 2_000_000_000
OUTPUT_IDENTITY_FIELDS = (
    "device",
    "inode",
    "size_bytes",
    "modified_ns",
    "changed_ns",
    "link_count",
)
DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)
RUNTIME_WRAPPER_LEAF = "AE_SINGLE_CASE_WRAPPER.jsx"
RUNTIME_PROGRAM_LEAF = "ae_render_single_case.jsx"


class BoundSource(NamedTuple):
    path: Path
    sha256: str
    device: int
    inode: int
    size_bytes: int
    modified_ns: int
    changed_ns: int
    link_count: int


class BoundDirectory(NamedTuple):
    path: Path
    device: int
    inode: int
    size_bytes: int
    modified_ns: int
    changed_ns: int
    link_count: int


class ExpectedOutputBinding(NamedTuple):
    request_dir: Path
    request_dir_device: int
    request_dir_inode: int
    input_dir: Path
    input_dir_device: int
    input_dir_inode: int
    case_id: str
    output_dir: Path
    output_kind: str
    output_path: Path
    output_dir_device: int
    output_dir_inode: int
    source_snapshot: tuple[BoundSource, ...]


def output_wait_timeout(host_timeout_seconds: float) -> float:
    """Keep the post-host gate long enough to satisfy its own quiet window."""

    minimum = OUTPUT_STABLE_WINDOW_SECONDS + OUTPUT_POLL_INTERVAL_SECONDS
    return min(OUTPUT_COMPLETION_TIMEOUT_SECONDS, max(minimum, host_timeout_seconds))


def inspect_complete_png(
    path: Path,
    *,
    dir_fd: int | None = None,
) -> dict[str, object] | None:
    """Parse, inflate, and hash one PNG, optionally below a trusted directory FD."""

    try:
        path = Path(path)
        open_path: Path | str = path
        if dir_fd is not None:
            if not path.name or path.name in (".", ".."):
                return None
            open_path = path.name
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(open_path, flags, dir_fd=dir_fd)
        with os.fdopen(descriptor, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return None
            digest = hashlib.sha256()

            def read(count: int) -> bytes:
                value = source.read(count)
                digest.update(value)
                return value

            if read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                return None
            saw_ihdr = False
            saw_plte = False
            saw_idat = False
            idat_ended = False
            bit_depth = 0
            color_type = -1
            expected_inflated_size = 0
            inflated_size = 0
            scanline_passes: list[tuple[int, int]] = []
            pass_index = 0
            pass_rows_remaining = 0
            scanline_size = 0
            scanline_position = 0
            inflater: zlib.Decompress | None = None
            chunk_index = 0

            def advance_pass() -> bool:
                nonlocal pass_index, pass_rows_remaining, scanline_size, scanline_position
                while pass_index < len(scanline_passes):
                    row_bytes, rows = scanline_passes[pass_index]
                    pass_index += 1
                    if rows:
                        scanline_size = row_bytes + 1
                        pass_rows_remaining = rows
                        scanline_position = 0
                        return True
                scanline_size = 0
                pass_rows_remaining = 0
                scanline_position = 0
                return False

            def consume_inflated(payload: bytes) -> bool:
                nonlocal inflated_size, pass_rows_remaining, scanline_position
                if inflated_size + len(payload) > expected_inflated_size:
                    return False
                offset = 0
                while offset < len(payload):
                    if scanline_size == 0:
                        return False
                    if scanline_position == 0 and payload[offset] > 4:
                        return False
                    take = min(len(payload) - offset, scanline_size - scanline_position)
                    offset += take
                    scanline_position += take
                    if scanline_position == scanline_size:
                        scanline_position = 0
                        pass_rows_remaining -= 1
                        if pass_rows_remaining == 0:
                            advance_pass()
                inflated_size += len(payload)
                return True

            def feed_idat(payload: bytes) -> bool:
                if inflater is None:
                    return False
                pending = payload
                while pending:
                    inflated = inflater.decompress(pending, 1024 * 1024)
                    pending = inflater.unconsumed_tail
                    if not consume_inflated(inflated):
                        return False
                    if inflater.unused_data:
                        return False
                    if not inflated and pending:
                        return False
                return True

            def finish_idat() -> bool:
                if inflater is None:
                    return False
                try:
                    tail = inflater.flush()
                except zlib.error:
                    return False
                return (
                    consume_inflated(tail)
                    and inflater.eof
                    and not inflater.unused_data
                    and not inflater.unconsumed_tail
                    and inflated_size == expected_inflated_size
                    and scanline_position == 0
                    and pass_rows_remaining == 0
                    and pass_index == len(scanline_passes)
                )

            while True:
                header = read(8)
                if len(header) != 8:
                    return None
                length = int.from_bytes(header[:4], "big")
                chunk_type = header[4:]
                if (
                    length > 0x7FFFFFFF
                    or any(not (65 <= value <= 90 or 97 <= value <= 122) for value in chunk_type)
                    or (chunk_type[2] & 0x20) != 0
                    or (chunk_type == b"IHDR" and length != 13)
                    or (chunk_type == b"PLTE" and (length == 0 or length > 768 or length % 3 != 0))
                    or (chunk_type == b"IEND" and length != 0)
                ):
                    return None
                crc = zlib.crc32(chunk_type)
                remaining = length
                retained_payload = bytearray()
                while remaining:
                    data = read(min(remaining, 1024 * 1024))
                    if not data:
                        return None
                    crc = zlib.crc32(data, crc)
                    if chunk_type in (b"IHDR", b"PLTE"):
                        retained_payload.extend(data)
                    elif chunk_type == b"IDAT" and not feed_idat(data):
                        return None
                    remaining -= len(data)
                stored_crc = read(4)
                if len(stored_crc) != 4 or int.from_bytes(stored_crc, "big") != (crc & 0xFFFFFFFF):
                    return None
                if not saw_ihdr and chunk_type != b"IHDR":
                    return None
                if saw_idat and chunk_type != b"IDAT" and not idat_ended:
                    if not finish_idat():
                        return None
                    idat_ended = True
                if (chunk_type[0] & 0x20) == 0 and chunk_type not in (
                    b"IHDR",
                    b"PLTE",
                    b"IDAT",
                    b"IEND",
                ):
                    return None
                if chunk_type == b"IHDR":
                    if chunk_index != 0 or saw_ihdr or saw_idat or length != 13:
                        return None
                    width = int.from_bytes(retained_payload[0:4], "big")
                    height = int.from_bytes(retained_payload[4:8], "big")
                    bit_depth = retained_payload[8]
                    color_type = retained_payload[9]
                    compression_method = retained_payload[10]
                    filter_method = retained_payload[11]
                    interlace_method = retained_payload[12]
                    permitted_depths = {
                        0: (1, 2, 4, 8, 16),
                        2: (8, 16),
                        3: (1, 2, 4, 8),
                        4: (8, 16),
                        6: (8, 16),
                    }
                    if (
                        width == 0
                        or height == 0
                        or width > 0x7FFFFFFF
                        or height > 0x7FFFFFFF
                        or color_type not in permitted_depths
                        or bit_depth not in permitted_depths[color_type]
                        or compression_method != 0
                        or filter_method != 0
                        or interlace_method not in (0, 1)
                    ):
                        return None
                    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
                    bits_per_pixel = channels * bit_depth
                    pass_geometry = (
                        ((0, 0, 1, 1),)
                        if interlace_method == 0
                        else (
                            (0, 0, 8, 8),
                            (4, 0, 8, 8),
                            (0, 4, 4, 8),
                            (2, 0, 4, 4),
                            (0, 2, 2, 4),
                            (1, 0, 2, 2),
                            (0, 1, 1, 2),
                        )
                    )
                    for x_start, y_start, x_step, y_step in pass_geometry:
                        pass_width = (
                            0
                            if width <= x_start
                            else (width - x_start + x_step - 1) // x_step
                        )
                        pass_height = (
                            0
                            if height <= y_start
                            else (height - y_start + y_step - 1) // y_step
                        )
                        if pass_width and pass_height:
                            row_bytes = (pass_width * bits_per_pixel + 7) // 8
                            scanline_passes.append((row_bytes, pass_height))
                            expected_inflated_size += (row_bytes + 1) * pass_height
                    if not scanline_passes or not advance_pass():
                        return None
                    inflater = zlib.decompressobj()
                    saw_ihdr = True
                elif chunk_type == b"PLTE":
                    entries = length // 3
                    if (
                        saw_plte
                        or saw_idat
                        or color_type in (0, 4)
                        or length == 0
                        or length % 3 != 0
                        or entries > 256
                        or (color_type == 3 and entries > (1 << bit_depth))
                    ):
                        return None
                    saw_plte = True
                elif chunk_type == b"IDAT":
                    if not saw_ihdr or idat_ended or (color_type == 3 and not saw_plte):
                        return None
                    saw_idat = True
                elif chunk_type == b"IEND":
                    if not (
                        length == 0
                        and saw_ihdr
                        and saw_idat
                        and idat_ended
                        and read(1) == b""
                    ):
                        return None
                    after = os.fstat(source.fileno())
                    before_identity = (
                        before.st_dev,
                        before.st_ino,
                        before.st_size,
                        before.st_mtime_ns,
                        before.st_ctime_ns,
                        before.st_nlink,
                    )
                    after_identity = (
                        after.st_dev,
                        after.st_ino,
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                        after.st_nlink,
                    )
                    if before_identity != after_identity or source.tell() != after.st_size:
                        return None
                    return {
                        "sha256": digest.hexdigest(),
                        "device": after.st_dev,
                        "inode": after.st_ino,
                        "size_bytes": after.st_size,
                        "modified_ns": after.st_mtime_ns,
                        "changed_ns": after.st_ctime_ns,
                        "link_count": after.st_nlink,
                        "identity_bound": True,
                    }
                chunk_index += 1
    except (OSError, ValueError, zlib.error):
        return None


def is_complete_png(path: Path) -> bool:
    """Return true only for a complete, CRC-valid PNG ending at IEND."""

    return inspect_complete_png(path) is not None


def is_readable_nonempty_file(path: Path) -> bool:
    return inspect_readable_nonempty_file(path) is not None


def inspect_readable_nonempty_file(
    path: Path,
    *,
    dir_fd: int | None = None,
) -> dict[str, object] | None:
    """Bind one readable non-empty regular file to a non-following descriptor."""

    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        path = Path(path)
        if dir_fd is not None and (not path.name or path.name in (".", "..")):
            return None
        open_path: Path | str = path.name if dir_fd is not None else path
        descriptor = os.open(open_path, flags, dir_fd=dir_fd)
        before = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_nlink,
        )
        if (
            not stat_module.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size < len(EXR_MAGIC)
        ):
            return None
        digest = hashlib.sha256()
        first = os.read(descriptor, len(EXR_MAGIC))
        digest.update(first)
        if first != EXR_MAGIC:
            return None
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_nlink,
        )
        lexical = (
            os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
            if dir_fd is not None
            else path.lstat()
        )
        lexical_identity = (
            lexical.st_dev,
            lexical.st_ino,
            lexical.st_size,
            lexical.st_mtime_ns,
            lexical.st_ctime_ns,
            lexical.st_nlink,
        )
        if (
            before_identity != after_identity
            or after_identity != lexical_identity
            or not stat_module.S_ISREG(lexical.st_mode)
        ):
            return None
        return {
            "device": after.st_dev,
            "inode": after.st_ino,
            "size_bytes": after.st_size,
            "modified_ns": after.st_mtime_ns,
            "changed_ns": after.st_ctime_ns,
            "link_count": after.st_nlink,
            "sha256": digest.hexdigest(),
            "identity_bound": True,
            "readable": True,
        }
    except OSError:
        return None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def wait_for_stable_output(
    path: Path,
    *,
    output_kind: str,
    not_before_ns: int = 0,
    timeout_seconds: float = OUTPUT_COMPLETION_TIMEOUT_SECONDS,
    stable_window_seconds: float = OUTPUT_STABLE_WINDOW_SECONDS,
    poll_interval_seconds: float = OUTPUT_POLL_INTERVAL_SECONDS,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Authoritatively gate a fresh, readable output after a full quiet window."""

    if output_kind not in ("png", "exr"):
        raise ValueError(f"unsupported output kind: {output_kind}")
    fresh_threshold_ns = max(0, not_before_ns - OUTPUT_FRESHNESS_SLACK_NS)
    started = monotonic()
    last_identity: tuple[int, int, int, int, int, int] | None = None
    stable_since: float | None = None
    stable_polls = 0
    polls = 0
    last_size = 0
    last_modified_ns = 0
    path_exists = False
    regular_file = False
    fresh = False
    validated_identity: tuple[int, int, int, int, int, int] | None = None
    content_validated = False
    validation_details: dict[str, object] | None = None
    while True:
        now = monotonic()
        polls += 1
        try:
            current = path.lstat()
            path_exists = True
            regular_file = stat_module.S_ISREG(current.st_mode)
            last_size = current.st_size
            last_modified_ns = current.st_mtime_ns
            fresh = not_before_ns <= 0 or last_modified_ns >= fresh_threshold_ns
        except OSError:
            current = None
            path_exists = False
            regular_file = False
            fresh = False
            last_size = 0
            last_modified_ns = 0
        identity = (
            (
                current.st_dev,
                current.st_ino,
                current.st_size,
                current.st_mtime_ns,
                current.st_ctime_ns,
                current.st_nlink,
            )
            if current is not None and regular_file and last_size > 0 and fresh
            else None
        )
        if identity is not None:
            if identity == last_identity:
                stable_polls += 1
            else:
                last_identity = identity
                stable_since = now
                stable_polls = 1
                validated_identity = None
                content_validated = False
                validation_details = None
            stable_for = now - stable_since if stable_since is not None else 0.0
            if stable_for >= stable_window_seconds and identity != validated_identity:
                if output_kind == "png":
                    validation_details = inspect_complete_png(path)
                    content_validated = (
                        validation_details is not None
                        and (
                            validation_details.get("device"),
                            validation_details.get("inode"),
                            validation_details.get("size_bytes"),
                            validation_details.get("modified_ns"),
                            validation_details.get("changed_ns"),
                            validation_details.get("link_count"),
                        )
                        == identity
                    )
                else:
                    validation_details = inspect_readable_nonempty_file(path)
                    content_validated = (
                        validation_details is not None
                        and tuple(
                            validation_details.get(field)
                            for field in OUTPUT_IDENTITY_FIELDS
                        )
                        == identity
                    )
                validated_identity = identity
            if stable_for >= stable_window_seconds and content_validated:
                try:
                    verified = path.lstat()
                except OSError:
                    verified = None
                if verified is not None and stat_module.S_ISREG(verified.st_mode) and (
                    verified.st_dev,
                    verified.st_ino,
                    verified.st_size,
                    verified.st_mtime_ns,
                    verified.st_ctime_ns,
                    verified.st_nlink,
                ) == identity:
                    return {
                        "status": "stable",
                        "timeout_ms": int(round(timeout_seconds * 1000)),
                        "waited_ms": int(round((monotonic() - started) * 1000)),
                        "polls": polls,
                        "stable_polls": stable_polls,
                        "stable_for_ms": int(round(stable_for * 1000)),
                        "stable_window_ms": int(round(stable_window_seconds * 1000)),
                        "size_bytes": last_size,
                        "modified_ms": last_modified_ns // 1_000_000,
                        "modified_ns": last_modified_ns,
                        "device": identity[0],
                        "inode": identity[1],
                        "changed_ns": identity[4],
                        "link_count": identity[5],
                        "regular_file": True,
                        "fresh": True,
                        "readable": True,
                        "format_complete": True if output_kind == "png" else None,
                        "crc_validated": output_kind == "png",
                        "validation": (
                            "png_chunks_crc_iend"
                            if output_kind == "png"
                            else "exr_magic_sha256"
                        ),
                        "output_kind": output_kind,
                        **(validation_details or {}),
                    }
        else:
            last_identity = None
            stable_since = None
            stable_polls = 0
            validated_identity = None
            content_validated = False
            validation_details = None
        elapsed = monotonic() - started
        if elapsed >= timeout_seconds:
            if identity is not None and output_kind == "png":
                validation_details = inspect_complete_png(path)
                content_validated = (
                    validation_details is not None
                    and (
                        validation_details.get("device"),
                        validation_details.get("inode"),
                        validation_details.get("size_bytes"),
                        validation_details.get("modified_ns"),
                        validation_details.get("changed_ns"),
                        validation_details.get("link_count"),
                    )
                    == identity
                )
            elif identity is not None:
                validation_details = inspect_readable_nonempty_file(path)
                content_validated = (
                    validation_details is not None
                    and tuple(
                        validation_details.get(field)
                        for field in OUTPUT_IDENTITY_FIELDS
                    )
                    == identity
                )
            else:
                validation_details = None
                content_validated = False
            if not path_exists:
                status = "missing"
            elif not regular_file:
                status = "not_regular"
            elif last_size == 0:
                status = "empty"
            elif not fresh:
                status = "stale"
            else:
                status = "unstable"
            return {
                "status": status,
                "timeout_ms": int(round(timeout_seconds * 1000)),
                "waited_ms": int(round(elapsed * 1000)),
                "polls": polls,
                "stable_polls": stable_polls,
                "stable_for_ms": int(round((now - stable_since) * 1000)) if stable_since is not None else 0,
                "stable_window_ms": int(round(stable_window_seconds * 1000)),
                "size_bytes": last_size,
                "modified_ms": last_modified_ns // 1_000_000,
                "modified_ns": last_modified_ns,
                "device": current.st_dev if current is not None else None,
                "inode": current.st_ino if current is not None else None,
                "changed_ns": current.st_ctime_ns if current is not None else None,
                "link_count": current.st_nlink if current is not None else None,
                "regular_file": regular_file,
                "fresh": fresh,
                "readable": content_validated,
                "format_complete": content_validated if output_kind == "png" else None,
                "crc_validated": output_kind == "png" and content_validated,
                "validation": (
                    "png_chunks_crc_iend"
                    if output_kind == "png"
                    else "exr_magic_sha256"
                ),
                "output_kind": output_kind,
                **(validation_details or {}),
            }
        sleep(min(poll_interval_seconds, max(0.0, timeout_seconds - elapsed)))


def wait_for_complete_png(
    path: Path,
    *,
    not_before_ns: int = 0,
    timeout_seconds: float = OUTPUT_COMPLETION_TIMEOUT_SECONDS,
    stable_window_seconds: float = OUTPUT_STABLE_WINDOW_SECONDS,
    poll_interval_seconds: float = OUTPUT_POLL_INTERVAL_SECONDS,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    return wait_for_stable_output(
        path,
        output_kind="png",
        not_before_ns=not_before_ns,
        timeout_seconds=timeout_seconds,
        stable_window_seconds=stable_window_seconds,
        poll_interval_seconds=poll_interval_seconds,
        monotonic=monotonic,
        sleep=sleep,
    )


def validate_portable_leaf(value: object, label: str, *, suffix: str | None = None) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"{label} is not a portable ExtendScript leaf: {value!r}")
    leaf = Path(value)
    if leaf.is_absolute() or leaf.name != value or value in (".", ".."):
        raise ValueError(f"{label} is not a safe leaf: {value!r}")
    if suffix is not None and leaf.suffix.lower() != suffix:
        raise ValueError(f"{label} must end in {suffix}: {value!r}")
    return value


def lexical_path_has_exact_entries(path: Path) -> bool:
    """Require every existing path component to match its readdir spelling."""

    path = Path(path)
    if not path.is_absolute():
        return False
    current = Path(path.anchor)
    try:
        for component in path.parts[1:]:
            if component not in os.listdir(current):
                return False
            current /= component
            if stat_module.S_ISLNK(current.lstat().st_mode):
                return False
    except OSError:
        return False
    return True


def _bound_directory(path: Path, descriptor: int) -> BoundDirectory:
    info = os.fstat(descriptor)
    if not stat_module.S_ISDIR(info.st_mode):
        raise ValueError(f"not a directory: {path}")
    return BoundDirectory(
        path=Path(path),
        device=info.st_dev,
        inode=info.st_ino,
        size_bytes=info.st_size,
        modified_ns=info.st_mtime_ns,
        changed_ns=info.st_ctime_ns,
        link_count=info.st_nlink,
    )


def open_absolute_directory_chain(
    path: Path,
) -> tuple[list[int], tuple[BoundDirectory, ...]]:
    """Hold every absolute directory component without following aliases."""

    supplied_path = Path(path)
    if not supplied_path.is_absolute():
        raise ValueError(f"directory chain is not absolute: {supplied_path}")
    resolved_path = supplied_path.resolve(strict=True)
    if resolved_path != supplied_path:
        raise ValueError(f"directory chain contains an alias: {supplied_path}")
    path = supplied_path
    if not path.is_absolute():
        raise ValueError(f"directory chain is not absolute: {path}")
    descriptors: list[int] = []
    bindings: list[BoundDirectory] = []
    try:
        current_path = Path(path.anchor)
        descriptor = os.open(current_path, DIRECTORY_OPEN_FLAGS)
        descriptors.append(descriptor)
        bindings.append(_bound_directory(current_path, descriptor))
        for component in path.parts[1:]:
            if component in ("", ".", "..") or component not in os.listdir(descriptor):
                raise ValueError(f"directory spelling differs or is missing: {component!r}")
            child = os.open(component, DIRECTORY_OPEN_FLAGS, dir_fd=descriptor)
            descriptors.append(child)
            current_path /= component
            bindings.append(_bound_directory(current_path, child))
            descriptor = child
        lexical = path.lstat()
        final = bindings[-1]
        if (
            not stat_module.S_ISDIR(lexical.st_mode)
            or (lexical.st_dev, lexical.st_ino) != (final.device, final.inode)
        ):
            raise ValueError(f"directory endpoint changed while opening: {path}")
        return descriptors, tuple(bindings)
    except Exception:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise


def _bound_directory_payload(binding: BoundDirectory) -> dict[str, object]:
    return {
        "path": str(binding.path),
        "device": binding.device,
        "inode": binding.inode,
        "size_bytes": binding.size_bytes,
        "modified_ns": binding.modified_ns,
        "changed_ns": binding.changed_ns,
        "link_count": binding.link_count,
    }


def snapshot_directory_chains(paths: tuple[Path, ...]) -> dict[str, dict[str, object]]:
    """Snapshot every component in stable run-owned directory chains."""

    snapshot: dict[str, dict[str, object]] = {}
    stable_endpoints = {
        str(Path(path).resolve(strict=True))
        for path in paths
    }
    for path in paths:
        descriptors, bindings = open_absolute_directory_chain(path)
        try:
            for binding in bindings:
                payload = _bound_directory_payload(binding)
                key = str(binding.path)
                if key not in stable_endpoints:
                    payload = {
                        field: payload[field]
                        for field in ("path", "device", "inode")
                    }
                previous = snapshot.get(key)
                if previous is not None and previous != payload:
                    if (
                        key in stable_endpoints
                        or previous.get("device") != payload.get("device")
                        or previous.get("inode") != payload.get("inode")
                    ):
                        raise ValueError(
                            f"directory identity changed while snapshotting: {key}"
                        )
                    continue
                snapshot[key] = payload
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)
    return dict(sorted(snapshot.items()))


def directory_chains_match(
    expected: object,
    paths: tuple[Path, ...],
) -> bool:
    if not isinstance(expected, dict):
        return False
    try:
        actual = snapshot_directory_chains(paths)
        if set(actual) != set(expected):
            return False
        stable_endpoints = {
            str(Path(path).resolve(strict=True))
            for path in paths
        }
        for path, current in actual.items():
            previous = expected.get(path)
            if (
                not isinstance(previous, dict)
                or set(previous) != set(current)
                or not all(
                    type(previous.get(field)) is type(current.get(field))
                    for field in current
                )
            ):
                return False
            fields = (
                (
                    "path",
                    "device",
                    "inode",
                    "size_bytes",
                    "modified_ns",
                    "changed_ns",
                    "link_count",
                )
                if path in stable_endpoints
                else ("path", "device", "inode")
            )
            if any(
                not json_values_equal_exact(current.get(field), previous.get(field))
                for field in fields
            ):
                return False
        return True
    except (OSError, ValueError):
        return False


def open_exact_child_directory(parent_descriptor: int, name: str) -> int:
    if name in ("", ".", "..") or Path(name).name != name:
        raise ValueError(f"unsafe directory leaf: {name!r}")
    if name not in os.listdir(parent_descriptor):
        raise ValueError(f"directory spelling differs or is missing: {name!r}")
    descriptor = os.open(name, DIRECTORY_OPEN_FLAGS, dir_fd=parent_descriptor)
    if not stat_module.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError(f"not a lexical directory: {name!r}")
    return descriptor


def read_bound_source_at(
    parent_descriptor: int,
    name: str,
    display_path: Path,
) -> tuple[bytes, BoundSource]:
    """Read exactly one named leaf below an already-trusted directory FD."""

    if name in ("", ".", "..") or Path(name).name != name:
        raise ValueError(f"unsafe source leaf: {name!r}")
    if name not in os.listdir(parent_descriptor):
        raise ValueError(f"source spelling differs or is missing: {name!r}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    try:
        before = os.fstat(descriptor)
        if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError(f"source is not a single-link regular file: {display_path}")
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            chunks.append(chunk)
        after = os.fstat(descriptor)
        lexical = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        identities = [
            (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
                value.st_nlink,
            )
            for value in (before, after, lexical)
        ]
        if identities[0] != identities[1] or identities[1] != identities[2]:
            raise ValueError(f"source changed while reading: {display_path}")
        return b"".join(chunks), BoundSource(
            path=Path(display_path),
            sha256=digest.hexdigest(),
            device=after.st_dev,
            inode=after.st_ino,
            size_bytes=after.st_size,
            modified_ns=after.st_mtime_ns,
            changed_ns=after.st_ctime_ns,
            link_count=after.st_nlink,
        )
    finally:
        os.close(descriptor)


def validate_extendscript_path_text(path: Path, label: str) -> None:
    rendered = str(path)
    if not Path(path).is_absolute():
        raise ValueError(f"{label} is not absolute: {path}")
    if len(rendered) > 900:
        raise ValueError(f"{label} exceeds the safe ExtendScript path length")
    if any(ord(character) < 32 or character in "%:\\" for character in rendered):
        raise ValueError(f"{label} contains URI/path-active characters: {path}")


def validate_provenance_path_text(value: object, label: str) -> str:
    """Validate an absolute path string without resolving or opening it."""

    if type(value) is not str:
        raise ValueError(f"{label} is not a string")
    path = Path(value)
    validate_extendscript_path_text(path, label)
    if str(path) != value or any(component in (".", "..") for component in path.parts):
        raise ValueError(f"{label} is not canonical path text: {value}")
    return value


def validate_extendscript_bound_path(path: Path, label: str) -> None:
    validate_extendscript_path_text(path, label)
    if not lexical_path_has_exact_entries(path):
        raise ValueError(f"{label} does not match exact filesystem spelling: {path}")


def bound_directory_path_matches(path: Path, device: int, inode: int) -> bool:
    try:
        directory = Path(path).lstat()
    except OSError:
        return False
    return (
        stat_module.S_ISDIR(directory.st_mode)
        and directory.st_dev == device
        and directory.st_ino == inode
        and lexical_path_has_exact_entries(path)
    )


def read_bound_source(
    path: Path,
    *,
    dir_fd: int | None = None,
) -> tuple[bytes, BoundSource]:
    """Read and hash one single-link source while binding its exact identity."""

    path = Path(path)
    if dir_fd is not None:
        return read_bound_source_at(dir_fd, path.name, path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError(f"source is not a single-link regular file: {path}")
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            chunks.append(chunk)
        after = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_nlink,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_nlink,
        )
        lexical = path.lstat()
        lexical_identity = (
            lexical.st_dev,
            lexical.st_ino,
            lexical.st_size,
            lexical.st_mtime_ns,
            lexical.st_ctime_ns,
            lexical.st_nlink,
        )
        if (
            before_identity != after_identity
            or after_identity != lexical_identity
            or not stat_module.S_ISREG(lexical.st_mode)
            or not lexical_path_has_exact_entries(path)
        ):
            raise ValueError(f"source changed or lost lexical identity while reading: {path}")
        return b"".join(chunks), BoundSource(
            path=path,
            sha256=digest.hexdigest(),
            device=after.st_dev,
            inode=after.st_ino,
            size_bytes=after.st_size,
            modified_ns=after.st_mtime_ns,
            changed_ns=after.st_ctime_ns,
            link_count=after.st_nlink,
        )
    finally:
        os.close(descriptor)


def source_snapshot_matches(snapshot: tuple[BoundSource, ...]) -> bool:
    for expected in snapshot:
        try:
            payload, actual = read_bound_source(expected.path)
        except (OSError, ValueError):
            return False
        if actual != expected or hashlib.sha256(payload).hexdigest() != expected.sha256:
            return False
    return True


def read_fixed_runtime_sources(
    runtime_dir: Path,
    *,
    dir_fd: int | None = None,
) -> tuple[BoundSource, BoundSource]:
    """Bind the exact staged program and wrapper below one trusted runtime dir."""

    runtime_dir = Path(runtime_dir)
    descriptors: list[int] = []
    descriptor = dir_fd
    try:
        if descriptor is None:
            descriptors, _ = open_absolute_directory_chain(runtime_dir)
            descriptor = descriptors[-1]
        expected_leaves = {RUNTIME_PROGRAM_LEAF, RUNTIME_WRAPPER_LEAF}
        if set(os.listdir(descriptor)) != expected_leaves:
            raise ValueError("runtime source leaf set differs")
        for leaf in expected_leaves:
            info = os.stat(leaf, dir_fd=descriptor, follow_symlinks=False)
            if (
                not stat_module.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or stat_module.S_IMODE(info.st_mode) != 0o444
            ):
                raise ValueError(f"runtime source is not sealed read-only: {leaf}")
        sources = tuple(
            read_bound_source_at(
                descriptor,
                leaf,
                runtime_dir / leaf,
            )[1]
            for leaf in (RUNTIME_PROGRAM_LEAF, RUNTIME_WRAPPER_LEAF)
        )
        return sources
    finally:
        for owned_descriptor in reversed(descriptors):
            os.close(owned_descriptor)


def runtime_source_snapshot_matches(
    snapshot: tuple[BoundSource, ...],
    runtime_dir: Path,
    *,
    dir_fd: int | None = None,
) -> bool:
    try:
        current = read_fixed_runtime_sources(runtime_dir, dir_fd=dir_fd)
    except (OSError, ValueError):
        return False
    return runtime_source_snapshots_match(current, snapshot)


def runtime_source_snapshots_match(
    left: tuple[BoundSource, ...],
    right: tuple[BoundSource, ...],
) -> bool:
    """Compare sealed JSX sources while tolerating macOS TCC xattr ctime drift.

    After Effects may add ``com.apple.macl`` when it opens a wrapper. That only
    changes inode ctime; content SHA, inode, size, mtime, mode and link count
    remain bound. Every other identity field stays fail-closed here.
    """

    if len(left) != len(right):
        return False
    return all(
        lhs._replace(changed_ns=0) == rhs._replace(changed_ns=0)
        for lhs, rhs in zip(left, right)
    )


def create_single_run_directory(output_container: Path) -> tuple[str, Path]:
    descriptors, _ = open_absolute_directory_chain(Path(output_container))
    try:
        parent_descriptor = descriptors[-1]
        for _ in range(8):
            run_id = (
                datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                + f"_{os.getpid()}_{os.urandom(8).hex()}"
            )
            leaf = f"single_run_{run_id}"
            try:
                os.mkdir(leaf, 0o700, dir_fd=parent_descriptor)
            except FileExistsError:
                continue
            child = open_exact_child_directory(parent_descriptor, leaf)
            try:
                opened = os.fstat(child)
                run_dir = Path(output_container) / leaf
                lexical = run_dir.lstat()
                if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
                    raise ValueError("new run directory lost lexical identity")
                return run_id, run_dir
            finally:
                os.close(child)
        raise FileExistsError("could not allocate a unique single-case run directory")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def stage_request_sources(binding: ExpectedOutputBinding, run_dir: Path) -> Path:
    """Copy only the AE-consumed request sources into a run-owned capsule."""

    capsule_root = Path(run_dir) / "source_capsule"
    staged_request = capsule_root / "staged_request"
    staged_input = staged_request / binding.input_dir.name
    run_descriptors, _ = open_absolute_directory_chain(Path(run_dir))
    capsule_descriptor: int | None = None
    request_descriptor: int | None = None
    input_descriptor: int | None = None
    run_descriptor = run_descriptors[-1]
    os.mkdir("source_capsule", 0o700, dir_fd=run_descriptor)
    capsule_descriptor = open_exact_child_directory(run_descriptor, "source_capsule")
    os.mkdir("staged_request", 0o700, dir_fd=capsule_descriptor)
    request_descriptor = open_exact_child_directory(capsule_descriptor, "staged_request")
    os.mkdir(binding.input_dir.name, 0o700, dir_fd=request_descriptor)
    input_descriptor = open_exact_child_directory(request_descriptor, binding.input_dir.name)
    staged_pairs: list[tuple[Path, BoundSource]] = []
    try:
        for expected in binding.source_snapshot:
            payload, actual = read_bound_source(expected.path)
            if actual != expected:
                raise ValueError(f"request source changed before staging: {expected.path}")
            if expected.path.name == "request_manifest.json":
                destination = staged_request / expected.path.name
                parent_descriptor = request_descriptor
            elif expected.path.parent == binding.request_dir:
                destination = staged_request / expected.path.name
                parent_descriptor = request_descriptor
            elif expected.path.parent == binding.input_dir:
                destination = staged_input / expected.path.name
                parent_descriptor = input_descriptor
            else:
                raise ValueError(f"source is outside the bound request tree: {expected.path}")
            assert parent_descriptor is not None
            atomic_write_bytes(
                destination,
                payload,
                mode=0o444,
                parent_dir_fd=parent_descriptor,
            )
            staged_pairs.append((destination, expected))
        assert input_descriptor is not None
        assert request_descriptor is not None
        assert capsule_descriptor is not None
        os.fchmod(input_descriptor, 0o555)
        os.fchmod(request_descriptor, 0o555)
        os.fchmod(capsule_descriptor, 0o555)
        for destination, expected in staged_pairs:
            parent_descriptor = (
                input_descriptor if destination.parent == staged_input else request_descriptor
            )
            _, staged_source = read_bound_source_at(
                parent_descriptor,
                destination.name,
                destination,
            )
            if (
                staged_source.sha256 != expected.sha256
                or staged_source.size_bytes != expected.size_bytes
            ):
                raise ValueError(
                    f"staged source bytes differ from the bound source: {destination}"
                )
        return staged_request
    finally:
        for descriptor in (input_descriptor, request_descriptor, capsule_descriptor):
            if descriptor is not None:
                os.close(descriptor)
        for descriptor in reversed(run_descriptors):
            os.close(descriptor)


def build_expected_output_binding(
    *,
    request_dir: Path,
    case_id: str,
    output_dir: Path,
    output_mode: str,
    input_file_override: str | None = None,
) -> ExpectedOutputBinding:
    """Freeze the only output path accepted from this single-case invocation."""

    request_dir = Path(request_dir)
    output_dir = Path(output_dir)
    validate_extendscript_bound_path(request_dir, "request directory")
    validate_extendscript_bound_path(output_dir, "output directory")
    try:
        request_directory = request_dir.lstat()
        if not stat_module.S_ISDIR(request_directory.st_mode):
            raise ValueError(f"request directory is not a lexical directory: {request_dir}")
        request_manifest_bytes, request_manifest_source = read_bound_source(
            request_dir / "request_manifest.json"
        )
        request_manifest = json.loads(request_manifest_bytes.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"could not read request manifest: {error}") from error
    cases = request_manifest.get("cases") if isinstance(request_manifest, dict) else None
    matches = (
        [case for case in cases if isinstance(case, dict) and case.get("id") == case_id]
        if isinstance(cases, list)
        else []
    )
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one request case {case_id!r}, found {len(matches)}"
        )
    validate_portable_leaf(case_id, "case id")
    reference_leaf = validate_portable_leaf(
        request_manifest.get("reference_manifest"),
        "reference manifest",
        suffix=".json",
    )
    input_dir_leaf = validate_portable_leaf(
        request_manifest.get("input_dir"),
        "input directory",
    )
    input_dir_path = request_dir / input_dir_leaf
    try:
        input_directory = input_dir_path.lstat()
    except OSError as error:
        raise ValueError(f"could not bind input directory: {error}") from error
    if (
        not stat_module.S_ISDIR(input_directory.st_mode)
        or not lexical_path_has_exact_entries(input_dir_path)
    ):
        raise ValueError(f"input directory is not an exact lexical directory: {input_dir_path}")
    input_filename = validate_portable_leaf(
        input_file_override or matches[0].get("before_effects_frame"),
        "input filename",
    )
    validate_extendscript_path_text(request_dir / reference_leaf, "reference manifest path")
    validate_extendscript_path_text(
        input_dir_path / input_filename,
        "input file path",
    )
    try:
        reference_bytes, reference_source = read_bound_source(request_dir / reference_leaf)
        json.loads(reference_bytes.decode("utf-8-sig"))
        _, input_source = read_bound_source(
            input_dir_path / input_filename
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"could not bind request sources: {error}") from error
    if output_mode == "png":
        frame = validate_portable_leaf(
            matches[0].get("frame"),
            "PNG frame",
            suffix=".png",
        )
        output_kind = "png"
        output_path = output_dir / frame
    elif output_mode == "exr_render_queue":
        validate_portable_leaf(case_id, "EXR case id")
        output_kind = "exr"
        output_path = output_dir / f"{case_id}_00000.exr"
    elif output_mode == "png16_render_queue":
        frame = validate_portable_leaf(
            matches[0].get("frame"),
            "PNG16 frame",
            suffix=".png",
        )
        output_kind = "png"
        output_path = output_dir / frame
    else:
        raise ValueError(f"unsupported output mode: {output_mode}")
    try:
        directory = output_dir.lstat()
    except OSError as error:
        raise ValueError(f"could not bind output directory: {error}") from error
    if not stat_module.S_ISDIR(directory.st_mode):
        raise ValueError(f"output directory is not a lexical directory: {output_dir}")
    if output_path.parent != output_dir:
        raise ValueError(f"expected output escaped its bound directory: {output_path}")
    validate_extendscript_path_text(output_path, "expected output path")
    return ExpectedOutputBinding(
        request_dir=request_dir,
        request_dir_device=request_directory.st_dev,
        request_dir_inode=request_directory.st_ino,
        input_dir=input_dir_path,
        input_dir_device=input_directory.st_dev,
        input_dir_inode=input_directory.st_ino,
        case_id=case_id,
        output_dir=output_dir,
        output_kind=output_kind,
        output_path=output_path,
        output_dir_device=directory.st_dev,
        output_dir_inode=directory.st_ino,
        source_snapshot=(request_manifest_source, reference_source, input_source),
    )


def validate_expected_output_binding(
    result: dict[str, object],
    binding: ExpectedOutputBinding,
) -> bool:
    """Reject host result metadata or parent-directory substitution."""

    errors: list[str] = []
    request_directory_matches = bound_directory_path_matches(
        binding.request_dir,
        binding.request_dir_device,
        binding.request_dir_inode,
    )
    input_directory_matches = bound_directory_path_matches(
        binding.input_dir,
        binding.input_dir_device,
        binding.input_dir_inode,
    )
    directory_matches = bound_directory_path_matches(
        binding.output_dir,
        binding.output_dir_device,
        binding.output_dir_inode,
    )
    if result.get("kind") != "olm_ae_single_case_result":
        errors.append("result kind mismatch")
    if result.get("request_dir") != str(binding.request_dir):
        errors.append("result request_dir mismatch")
    if result.get("case_id") != binding.case_id:
        errors.append("result case_id mismatch")
    if result.get("output_dir") != str(binding.output_dir):
        errors.append("result output_dir mismatch")
    expected_field = "output_png" if binding.output_kind == "png" else "output_exr"
    unused_field = "output_exr" if binding.output_kind == "png" else "output_png"
    if result.get(expected_field) != str(binding.output_path):
        errors.append(f"result {expected_field} mismatch")
    if result.get(unused_field) != "":
        errors.append(f"unexpected declared {unused_field}")
    sources_snapshot_matches = (
        request_directory_matches
        and input_directory_matches
        and source_snapshot_matches(binding.source_snapshot)
    )
    request_directory_matches = request_directory_matches and bound_directory_path_matches(
        binding.request_dir,
        binding.request_dir_device,
        binding.request_dir_inode,
    )
    input_directory_matches = input_directory_matches and bound_directory_path_matches(
        binding.input_dir,
        binding.input_dir_device,
        binding.input_dir_inode,
    )
    directory_matches = directory_matches and bound_directory_path_matches(
        binding.output_dir,
        binding.output_dir_device,
        binding.output_dir_inode,
    )
    sources_match = (
        sources_snapshot_matches
        and request_directory_matches
        and input_directory_matches
    )
    if not directory_matches:
        errors.append("bound output directory identity changed")
    if not request_directory_matches:
        errors.append("bound request directory identity changed")
    if not input_directory_matches:
        errors.append("bound input directory identity changed")
    if not sources_match:
        errors.append("bound request sources changed")
    result["output_binding_validation"] = {
        "status": "failed" if errors else "matched",
        "expected_output_kind": binding.output_kind,
        "expected_output_path": str(binding.output_path),
        "expected_output_dir": str(binding.output_dir),
        "output_dir_device": binding.output_dir_device,
        "output_dir_inode": binding.output_dir_inode,
        "output_dir_identity_matches": directory_matches,
        "request_dir_device": binding.request_dir_device,
        "request_dir_inode": binding.request_dir_inode,
        "request_dir_identity_matches": request_directory_matches,
        "input_dir_device": binding.input_dir_device,
        "input_dir_inode": binding.input_dir_inode,
        "input_dir_identity_matches": input_directory_matches,
        "request_source_snapshot_matches": sources_match,
        "errors": errors,
    }
    if errors:
        result["status"] = "error"
        result["error"] = "single-case output binding failed: " + "; ".join(errors)
        return False
    return True


def bound_output_directory_fd_matches(
    descriptor: int,
    binding: ExpectedOutputBinding,
) -> bool:
    try:
        current = os.fstat(descriptor)
        lexical = binding.output_dir.lstat()
    except OSError:
        return False
    return (
        stat_module.S_ISDIR(current.st_mode)
        and current.st_dev == binding.output_dir_device
        and current.st_ino == binding.output_dir_inode
        and stat_module.S_ISDIR(lexical.st_mode)
        and lexical.st_dev == current.st_dev
        and lexical.st_ino == current.st_ino
        and lexical_path_has_exact_entries(binding.output_dir)
    )


def open_bound_output_directory(binding: ExpectedOutputBinding) -> int:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(binding.output_dir, flags)
    if not bound_output_directory_fd_matches(descriptor, binding):
        os.close(descriptor)
        raise ValueError("bound output directory no longer maps to its trusted inode")
    return descriptor


def validate_result_output(
    result: dict[str, object],
    *,
    not_before_ns: int,
    expected_binding: ExpectedOutputBinding | None = None,
    timeout_seconds: float = OUTPUT_COMPLETION_TIMEOUT_SECONDS,
    stable_window_seconds: float = OUTPUT_STABLE_WINDOW_SECONDS,
    poll_interval_seconds: float = OUTPUT_POLL_INTERVAL_SECONDS,
) -> bool:
    """Validate exactly one declared PNG/EXR output in place after AE returns."""

    if result.get("status") != "ok":
        return False
    if expected_binding is not None and not validate_expected_output_binding(
        result,
        expected_binding,
    ):
        return True
    declared: list[tuple[str, Path]] = []
    if result.get("output_png"):
        declared.append(("png", Path(str(result["output_png"]))))
    if result.get("output_exr"):
        declared.append(("exr", Path(str(result["output_exr"]))))
    if len(declared) != 1:
        result["status"] = "error"
        result["error"] = f"expected exactly one declared output, found {len(declared)}"
        return True
    output_kind, output_path = declared[0]
    observation = wait_for_stable_output(
        output_path,
        output_kind=output_kind,
        not_before_ns=not_before_ns,
        timeout_seconds=timeout_seconds,
        stable_window_seconds=stable_window_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    result["output_observation"] = observation
    if output_kind == "png":
        result["png_observation"] = observation
    if observation.get("status") != "stable":
        result["status"] = "error"
        result["error"] = (
            f"{output_kind.upper()} did not reach fresh complete stable state "
            f"({observation.get('status')}): {output_path}"
        )
    return True


def revalidate_result_output_for_commit(
    result: dict[str, object],
    *,
    expected_binding: ExpectedOutputBinding | None = None,
    output_dir_fd: int | None = None,
) -> bool:
    """Fail closed if the stable output changed before result publication."""

    if result.get("status") != "ok":
        return False
    if expected_binding is not None and not validate_expected_output_binding(
        result,
        expected_binding,
    ):
        return False
    if expected_binding is not None and output_dir_fd is None:
        try:
            owned_descriptor = open_bound_output_directory(expected_binding)
        except (OSError, ValueError) as error:
            result["status"] = "error"
            result["error"] = f"could not reopen bound output directory: {error}"
            result["output_commit_revalidation"] = {
                "status": "failed",
                "error": result["error"],
            }
            return False
        try:
            return revalidate_result_output_for_commit(
                result,
                expected_binding=expected_binding,
                output_dir_fd=owned_descriptor,
            )
        finally:
            os.close(owned_descriptor)
    declared: list[tuple[str, Path]] = []
    if result.get("output_png"):
        declared.append(("png", Path(str(result["output_png"]))))
    if result.get("output_exr"):
        declared.append(("exr", Path(str(result["output_exr"]))))
    observation = result.get("output_observation")
    if (
        len(declared) != 1
        or not isinstance(observation, dict)
        or observation.get("status") != "stable"
    ):
        result["status"] = "error"
        result["error"] = "stable output observation missing before result commit"
        result["output_commit_revalidation"] = {
            "status": "failed",
            "error": result["error"],
        }
        return False

    output_kind, output_path = declared[0]
    expected_identity = tuple(observation.get(field) for field in OUTPUT_IDENTITY_FIELDS)
    identity_is_complete = all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in expected_identity
    )
    inspection_path = (
        expected_binding.output_path.name
        if expected_binding is not None and output_dir_fd is not None
        else output_path
    )
    if output_kind == "png":
        details = (
            inspect_complete_png(inspection_path, dir_fd=output_dir_fd)
            if output_dir_fd is not None
            else inspect_complete_png(output_path)
        )
    else:
        details = (
            inspect_readable_nonempty_file(inspection_path, dir_fd=output_dir_fd)
            if output_dir_fd is not None
            else inspect_readable_nonempty_file(output_path)
        )
    actual_identity = (
        tuple(details.get(field) for field in OUTPUT_IDENTITY_FIELDS)
        if details is not None
        else None
    )
    try:
        lexical = (
            os.stat(
                expected_binding.output_path.name,
                dir_fd=output_dir_fd,
                follow_symlinks=False,
            )
            if expected_binding is not None and output_dir_fd is not None
            else output_path.lstat()
        )
        lexical_identity: tuple[object, ...] | None = (
            lexical.st_dev,
            lexical.st_ino,
            lexical.st_size,
            lexical.st_mtime_ns,
            lexical.st_ctime_ns,
            lexical.st_nlink,
        )
        lexical_is_regular = stat_module.S_ISREG(lexical.st_mode)
    except OSError:
        lexical_identity = None
        lexical_is_regular = False
    try:
        leaf_spelling_matches = (
            expected_binding is None
            or (
                output_dir_fd is not None
                and expected_binding.output_path.name in os.listdir(output_dir_fd)
            )
        )
    except OSError:
        leaf_spelling_matches = False
    parent_mapping_matches = (
        expected_binding is None
        or (
            output_dir_fd is not None
            and bound_output_directory_fd_matches(output_dir_fd, expected_binding)
        )
    )
    digest_matches = (
        isinstance(observation.get("sha256"), str)
        and len(str(observation.get("sha256"))) == 64
        and details is not None
        and details.get("sha256") == observation.get("sha256")
    )
    if (
        observation.get("output_kind") != output_kind
        or not identity_is_complete
        or details is None
        or actual_identity != expected_identity
        or lexical_identity != expected_identity
        or not lexical_is_regular
        or not leaf_spelling_matches
        or not parent_mapping_matches
        or not digest_matches
    ):
        result["status"] = "error"
        result["error"] = f"{output_kind.upper()} changed after stable observation: {output_path}"
        result["output_commit_revalidation"] = {
            "status": "failed",
            "output_kind": output_kind,
            "path": str(output_path),
            "identity_matches": actual_identity == expected_identity,
            "path_identity_matches": lexical_identity == expected_identity,
            "leaf_spelling_matches": leaf_spelling_matches,
            "parent_mapping_matches": parent_mapping_matches,
            "digest_matches": digest_matches,
            "structure_valid": details is not None if output_kind == "png" else None,
            "readable": details is not None,
            "error": result["error"],
        }
        return False

    if expected_binding is not None and not validate_expected_output_binding(
        result,
        expected_binding,
    ):
        result["output_commit_revalidation"] = {
            "status": "failed",
            "output_kind": output_kind,
            "path": str(output_path),
            "error": result["error"],
        }
        return False

    result["output_commit_revalidation"] = {
        "status": "matched",
        "output_kind": output_kind,
        "path": str(output_path),
        "identity_matches": True,
        "path_identity_matches": True,
        "leaf_spelling_matches": True,
        "parent_mapping_matches": True,
        "digest_matches": True,
        "structure_valid": True,
        "readable": True,
        "validation": (
            "png_chunks_crc_iend_sha256_identity"
            if output_kind == "png"
            else "exr_magic_sha256_identity"
        ),
    }
    return True


def atomic_write_bytes(
    path: Path,
    payload: bytes,
    *,
    mode: int = 0o644,
    parent_dir_fd: int | None = None,
) -> None:
    """Durably replace one file, optionally relative to a trusted parent FD."""

    path = Path(path)
    if not path.name or path.name in (".", ".."):
        raise ValueError(f"atomic destination must name a file: {path}")
    owns_parent_descriptor = parent_dir_fd is None
    directory_descriptor: int | None = None
    if owns_parent_descriptor:
        path.parent.mkdir(parents=True, exist_ok=True)
        directory_descriptor = os.open(path.parent, DIRECTORY_OPEN_FLAGS)
    else:
        directory_descriptor = parent_dir_fd
    assert directory_descriptor is not None
    if not stat_module.S_ISDIR(os.fstat(directory_descriptor).st_mode):
        if owns_parent_descriptor:
            os.close(directory_descriptor)
        raise NotADirectoryError("trusted parent descriptor is not a directory")
    temporary_name = (
        f".{path.name}.{os.getpid()}.{time.time_ns()}.{os.urandom(8).hex()}.tmp"
    )
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary_name, flags, mode, dir_fd=directory_descriptor)
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("short atomic file write")
            written += count
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        os.fsync(directory_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temporary_name, dir_fd=directory_descriptor)
        except FileNotFoundError:
            pass
        if owns_parent_descriptor:
            os.close(directory_descriptor)


def write_result_json(
    path: Path,
    result: dict[str, object],
    *,
    parent_dir_fd: int | None = None,
) -> bytes:
    payload = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write_bytes(path, payload, parent_dir_fd=parent_dir_fd)
    return payload


def commit_bound_result_json(
    path: Path,
    result: dict[str, object],
    binding: ExpectedOutputBinding,
) -> bool:
    """Commit through the bound directory, then downgrade on any late mutation."""

    path = Path(path)
    if path.parent != binding.output_dir or path.name != "AE_SINGLE_CASE_RESULT.json":
        raise ValueError(f"result JSON escaped its bound destination: {path}")
    directory_descriptor = open_bound_output_directory(binding)
    try:
        if result.get("status") == "ok":
            revalidate_result_output_for_commit(
                result,
                expected_binding=binding,
                output_dir_fd=directory_descriptor,
            )
        write_result_json(path, result, parent_dir_fd=directory_descriptor)
        if result.get("status") == "ok" and not revalidate_result_output_for_commit(
            result,
            expected_binding=binding,
            output_dir_fd=directory_descriptor,
        ):
            write_result_json(path, result, parent_dir_fd=directory_descriptor)
        return result.get("status") == "ok"
    finally:
        os.close(directory_descriptor)


def copy_validated_output(
    result: dict[str, object],
    binding: ExpectedOutputBinding,
    validated_dir: Path,
    *,
    validated_dir_fd: int | None = None,
) -> dict[str, object]:
    """Copy the exact observed raw output into a run-owned validated artifact."""

    raw_directory_descriptor = open_bound_output_directory(binding)
    validated_directory_descriptor: int | None = validated_dir_fd
    owns_validated_descriptor = validated_dir_fd is None
    source_descriptor: int | None = None
    destination_descriptor: int | None = None
    temporary_name = (
        f".{binding.output_path.name}.{os.getpid()}.{os.urandom(8).hex()}.tmp"
    )
    try:
        if not revalidate_result_output_for_commit(
            result,
            expected_binding=binding,
            output_dir_fd=raw_directory_descriptor,
        ):
            raise ValueError(result.get("error", "raw output revalidation failed"))
        observation = result.get("output_observation")
        if not isinstance(observation, dict):
            raise ValueError("raw output observation is missing")
        expected_identity = tuple(
            observation.get(field) for field in OUTPUT_IDENTITY_FIELDS
        )
        expected_sha = observation.get("sha256")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ValueError("raw output observation lacks SHA-256")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        source_descriptor = os.open(
            binding.output_path.name,
            flags,
            dir_fd=raw_directory_descriptor,
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
        if (
            not stat_module.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before_identity != expected_identity
        ):
            raise ValueError("raw output identity changed before validated copy")
        if validated_directory_descriptor is None:
            validated_flags = (
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            validated_directory_descriptor = os.open(validated_dir, validated_flags)
        destination_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        destination_descriptor = os.open(
            temporary_name,
            destination_flags,
            0o444,
            dir_fd=validated_directory_descriptor,
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
                    raise OSError("short validated output write")
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
            raise ValueError("raw output changed while copying")
        os.fchmod(destination_descriptor, 0o444)
        os.fsync(destination_descriptor)
        os.close(destination_descriptor)
        destination_descriptor = None
        os.replace(
            temporary_name,
            binding.output_path.name,
            src_dir_fd=validated_directory_descriptor,
            dst_dir_fd=validated_directory_descriptor,
        )
        os.fsync(validated_directory_descriptor)
        details = (
            inspect_complete_png(
                binding.output_path.name,
                dir_fd=validated_directory_descriptor,
            )
            if binding.output_kind == "png"
            else inspect_readable_nonempty_file(
                binding.output_path.name,
                dir_fd=validated_directory_descriptor,
            )
        )
        if (
            details is None
            or details.get("sha256") != expected_sha
            or binding.output_path.name not in os.listdir(validated_directory_descriptor)
        ):
            raise ValueError("validated output failed final structure/digest verification")
        return _validated_artifact_payload(
            Path(validated_dir) / binding.output_path.name,
            binding.output_kind,
            details,
        )
    finally:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if source_descriptor is not None:
            os.close(source_descriptor)
        if validated_directory_descriptor is not None:
            try:
                os.unlink(temporary_name, dir_fd=validated_directory_descriptor)
            except FileNotFoundError:
                pass
            if owns_validated_descriptor:
                os.close(validated_directory_descriptor)
        os.close(raw_directory_descriptor)


def _bound_source_payload(source: BoundSource) -> dict[str, object]:
    return {
        "path": str(source.path),
        "sha256": source.sha256,
        "device": source.device,
        "inode": source.inode,
        "size_bytes": source.size_bytes,
        "modified_ns": source.modified_ns,
        "changed_ns": source.changed_ns,
        "link_count": source.link_count,
    }


def _directory_payload(path: Path) -> dict[str, object]:
    info = Path(path).lstat()
    if not stat_module.S_ISDIR(info.st_mode) or not lexical_path_has_exact_entries(path):
        raise ValueError(f"directory is not an exact lexical directory: {path}")
    return {
        "path": str(path),
        "device": info.st_dev,
        "inode": info.st_ino,
        "size_bytes": info.st_size,
        "modified_ns": info.st_mtime_ns,
        "changed_ns": info.st_ctime_ns,
        "link_count": info.st_nlink,
    }


def json_values_equal_exact(left: object, right: object) -> bool:
    """Compare decoded JSON without Python's bool/int equality alias."""

    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            json_values_equal_exact(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_values_equal_exact(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def _directory_matches_entry(
    path: Path,
    entry: object,
    *,
    identity_only: bool = False,
) -> bool:
    if not isinstance(entry, dict) or entry.get("path") != str(path):
        return False
    try:
        actual = _directory_payload(path)
    except (OSError, ValueError):
        return False
    fields = ("path", "device", "inode") if identity_only else tuple(actual)
    expected = {field: actual[field] for field in fields}
    return json_values_equal_exact(
        expected,
        entry,
    )


def _source_entry_matches(
    actual: BoundSource,
    entry: object,
    *,
    allow_changed_ns_drift: bool = False,
) -> bool:
    payload = _bound_source_payload(actual)
    if allow_changed_ns_drift and isinstance(entry, dict):
        payload.pop("changed_ns", None)
        entry = {key: value for key, value in entry.items() if key != "changed_ns"}
    return json_values_equal_exact(
        payload,
        entry,
    )


def _validated_artifact_payload(
    path: Path,
    output_kind: str,
    details: dict[str, object],
) -> dict[str, object]:
    return {
        "status": "stable",
        "output_kind": output_kind,
        "path": str(path),
        "sha256": details["sha256"],
        "validation": (
            "png_chunks_crc_iend_sha256"
            if output_kind == "png"
            else "exr_magic_sha256"
        ),
        **details,
    }


def verify_single_case_commit(
    commit_path: Path,
    *,
    expected_run_id: str,
    expected_commit_sha256: str,
    expected_commit_bytes: bytes | None = None,
    expected_run_identity: tuple[int, int] | None = None,
) -> dict[str, object]:
    """Consumer-time authority for one fixed, run-owned publication tree."""

    errors: list[str] = []
    descriptors: list[int] = []
    commit: dict[str, object] = {}
    commit_bytes = b""
    commit_source: BoundSource | None = None
    result_bytes = b""
    result_source: BoundSource | None = None
    current_sources: list[tuple[BoundSource, object]] = []
    current_runtime_sources: tuple[BoundSource, BoundSource] | None = None
    commit_path = Path(commit_path)
    supplied_publication_dir = commit_path.parent
    run_dir = supplied_publication_dir.parent
    publication_dir = run_dir / "publication"
    runtime_dir = run_dir / "runtime"
    validated_dir = run_dir / "validated_output"
    source_capsule = run_dir / "source_capsule"
    staged_request = source_capsule / "staged_request"
    fixed_commit = run_dir / "publication" / "AE_SINGLE_CASE_COMMIT.json"
    fixed_result = publication_dir / "AE_SINGLE_CASE_RESULT.json"
    try:
        validate_portable_leaf(expected_run_id, "expected run id")
        if (
            not commit_path.is_absolute()
            or supplied_publication_dir.name != "publication"
            or supplied_publication_dir != publication_dir
            or commit_path != fixed_commit
            or commit_path.resolve(strict=True) != commit_path
            or run_dir.resolve(strict=True) != run_dir
            or not lexical_path_has_exact_entries(commit_path)
        ):
            raise ValueError("commit path is outside the fixed publication leaf")
        if run_dir.name != f"single_run_{expected_run_id}":
            raise ValueError("run directory name does not match expected run id")
        chain_descriptors, _ = open_absolute_directory_chain(run_dir)
        descriptors.extend(chain_descriptors)
        run_descriptor = chain_descriptors[-1]
        run_info = os.fstat(run_descriptor)
        if (
            expected_run_identity is not None
            and (run_info.st_dev, run_info.st_ino) != expected_run_identity
        ):
            errors.append("run directory differs from the writer identity anchor")
        publication_descriptor = open_exact_child_directory(run_descriptor, "publication")
        validated_descriptor = open_exact_child_directory(run_descriptor, "validated_output")
        runtime_descriptor = open_exact_child_directory(run_descriptor, "runtime")
        capsule_descriptor = open_exact_child_directory(run_descriptor, "source_capsule")
        for descriptor in (
            publication_descriptor,
            validated_descriptor,
            runtime_descriptor,
            capsule_descriptor,
        ):
            descriptors.append(descriptor)
        staged_descriptor = open_exact_child_directory(capsule_descriptor, "staged_request")
        descriptors.append(staged_descriptor)
        current_runtime_sources = read_fixed_runtime_sources(
            runtime_dir,
            dir_fd=runtime_descriptor,
        )
        commit_bytes, commit_source = read_bound_source_at(
            publication_descriptor,
            fixed_commit.name,
            fixed_commit,
        )
        commit_sha256 = hashlib.sha256(commit_bytes).hexdigest()
        if commit_sha256 != expected_commit_sha256:
            errors.append("commit digest does not match the external writer anchor")
        if expected_commit_bytes is not None and commit_bytes != expected_commit_bytes:
            errors.append("commit bytes do not match the external writer anchor")
        parsed = json.loads(commit_bytes.decode("utf-8-sig"))
        if not isinstance(parsed, dict):
            raise ValueError("commit JSON is not an object")
        commit = parsed
        if set(os.listdir(publication_descriptor)) != {
            fixed_commit.name,
            fixed_result.name,
        }:
            errors.append("publication leaf set differs")
        if set(os.listdir(run_descriptor)) != {
            "runtime",
            "raw_output",
            "validated_output",
            "publication",
            "source_capsule",
        }:
            errors.append("run-owned directory set differs")
        if set(os.listdir(capsule_descriptor)) != {"staged_request"}:
            errors.append("source capsule directory set differs")

        if commit.get("schema") != "olm.ae-single-case-commit/1":
            errors.append("commit schema mismatch")
        if commit.get("status") != "passed":
            errors.append("commit status is not passed")
        if commit.get("run_id") != expected_run_id:
            errors.append("commit run id mismatch")
        if commit.get("consumer_verifier") != "verify_single_case_commit":
            errors.append("consumer verifier contract mismatch")
        if commit.get("consumer_time_reverification_required") is not True:
            errors.append("consumer-time re-verification is not required")
        if commit.get("static_status_is_authoritative") is not False:
            errors.append("commit static authority flag mismatch")
        if commit.get("ae_metadata_is_authoritative") is not False:
            errors.append("commit AE metadata authority flag mismatch")

        runtime_entries = commit.get("runtime_sources")
        runtime_entries_by_path = {
            str(entry.get("path")): entry
            for entry in runtime_entries
            if isinstance(entry, dict) and isinstance(entry.get("path"), str)
        } if isinstance(runtime_entries, list) else {}
        expected_runtime_paths = {
            str(source.path) for source in current_runtime_sources
        }
        if (
            not isinstance(runtime_entries, list)
            or len(runtime_entries) != 2
            or len(runtime_entries_by_path) != 2
            or set(runtime_entries_by_path) != expected_runtime_paths
        ):
            errors.append("runtime source set mismatch")
        for source in current_runtime_sources:
            if not _source_entry_matches(
                source,
                runtime_entries_by_path.get(str(source.path)),
                allow_changed_ns_drift=True,
            ):
                errors.append(f"runtime source identity mismatch: {source.path}")

        case_id = validate_portable_leaf(commit.get("case_id"), "commit case id")
        output_kind = commit.get("output_kind")
        manifest_bytes, manifest_source = read_bound_source_at(
            staged_descriptor,
            "request_manifest.json",
            staged_request / "request_manifest.json",
        )
        manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
        if not isinstance(manifest, dict):
            raise ValueError("staged request manifest is not an object")
        cases = manifest.get("cases")
        matching_cases = [
            row for row in cases
            if isinstance(row, dict) and row.get("id") == case_id
        ] if isinstance(cases, list) else []
        if len(matching_cases) != 1:
            raise ValueError("staged request case cardinality mismatch")
        reference_leaf = validate_portable_leaf(
            manifest.get("reference_manifest"),
            "staged reference manifest",
            suffix=".json",
        )
        if reference_leaf == "request_manifest.json":
            raise ValueError("staged reference manifest aliases the request manifest")
        input_dir_leaf = validate_portable_leaf(
            manifest.get("input_dir"),
            "staged input directory",
        )
        default_input_leaf = validate_portable_leaf(
            matching_cases[0].get("before_effects_frame"),
            "default staged input file",
        )
        input_leaf = validate_portable_leaf(
            commit.get("input_file_selection"),
            "committed input file selection",
        )
        if input_leaf != default_input_leaf:
            validate_portable_leaf(input_leaf, "allowed input file override")
        input_descriptor = open_exact_child_directory(staged_descriptor, input_dir_leaf)
        descriptors.append(input_descriptor)
        if set(os.listdir(staged_descriptor)) != {
            "request_manifest.json",
            reference_leaf,
            input_dir_leaf,
        }:
            errors.append("staged request leaf set differs")
        if set(os.listdir(input_descriptor)) != {input_leaf}:
            errors.append("staged input leaf set differs")
        if output_kind == "png":
            output_leaf = validate_portable_leaf(
                matching_cases[0].get("frame"),
                "validated PNG",
                suffix=".png",
            )
        elif output_kind == "exr":
            output_leaf = f"{case_id}_00000.exr"
        else:
            raise ValueError("unsupported committed output kind")
        expected_output = validated_dir / output_leaf
        if set(os.listdir(validated_descriptor)) != {output_leaf}:
            errors.append("validated output leaf set differs")

        reference_path = staged_request / reference_leaf
        input_path = staged_request / input_dir_leaf / input_leaf
        _, reference_source = read_bound_source_at(
            staged_descriptor,
            reference_leaf,
            reference_path,
        )
        input_bytes, input_source = read_bound_source_at(
            input_descriptor,
            input_leaf,
            input_path,
        )
        if not input_bytes:
            errors.append("staged input is empty")
        expected_sources = (
            manifest_source,
            reference_source,
            input_source,
        )
        source_entries = commit.get("staged_sources")
        entries_by_path = {
            str(entry.get("path")): entry
            for entry in source_entries
            if isinstance(entry, dict) and isinstance(entry.get("path"), str)
        } if isinstance(source_entries, list) else {}
        if (
            not isinstance(source_entries, list)
            or len(source_entries) != 3
            or len(entries_by_path) != 3
            or set(entries_by_path) != {str(source.path) for source in expected_sources}
        ):
            errors.append("staged source set mismatch")
        for source in expected_sources:
            entry = entries_by_path.get(str(source.path))
            current_sources.append((source, entry))
            if not _source_entry_matches(source, entry):
                errors.append(f"staged source identity mismatch: {source.path}")

        result_entry = commit.get("result")
        if not isinstance(result_entry, dict) or result_entry.get("path") != str(fixed_result):
            errors.append("commit result entry does not name the fixed result leaf")
        result_bytes, result_source = read_bound_source_at(
            publication_descriptor,
            fixed_result.name,
            fixed_result,
        )
        if not _source_entry_matches(result_source, result_entry):
            errors.append("result JSON identity/digest mismatch")
        decoded_result = json.loads(result_bytes.decode("utf-8-sig"))
        if not isinstance(decoded_result, dict):
            raise ValueError("result JSON is not an object")
        result = decoded_result

        output_entry = commit.get("validated_output")
        details = (
            inspect_complete_png(Path(output_leaf), dir_fd=validated_descriptor)
            if output_kind == "png"
            else inspect_readable_nonempty_file(Path(output_leaf), dir_fd=validated_descriptor)
        )
        expected_artifact = (
            _validated_artifact_payload(expected_output, output_kind, details)
            if details is not None
            else None
        )
        if not json_values_equal_exact(output_entry, expected_artifact):
            errors.append("validated output identity/structure/digest mismatch")

        expected_output_field = "output_png" if output_kind == "png" else "output_exr"
        unused_output_field = "output_exr" if output_kind == "png" else "output_png"
        result_artifact = result.get("validated_output")
        result_observation = result.get("output_observation")
        if result.get("status") != "ok":
            errors.append("result status is not ok")
        if result.get("kind") != "olm_ae_single_case_result":
            errors.append("result kind mismatch")
        if result.get("consumer_verifier") != "verify_single_case_commit":
            errors.append("result consumer verifier mismatch")
        if result.get("run_id") != expected_run_id or result.get("case_id") != case_id:
            errors.append("result run/case identity mismatch")
        if result.get("input_file_selection") != input_leaf:
            errors.append("result input file selection mismatch")
        if result.get("generation_commit_path") != str(fixed_commit):
            errors.append("result commit path mismatch")
        if (
            result.get("request_dir") != str(staged_request)
            or result.get("host_request_dir") != str(staged_request)
        ):
            errors.append("result host request path mismatch")
        invocation_provenance_matches = True
        try:
            result_invocation_request = validate_provenance_path_text(
                result.get("invocation_request_dir"),
                "result invocation request provenance",
            )
            commit_invocation_request = validate_provenance_path_text(
                commit.get("invocation_request_dir"),
                "commit invocation request provenance",
            )
            invocation_provenance_matches = (
                result_invocation_request == commit_invocation_request
            )
        except ValueError:
            invocation_provenance_matches = False
        if (
            not invocation_provenance_matches
            or result.get("invocation_request_dir_provenance_only") is not True
            or commit.get("invocation_request_dir_provenance_only") is not True
        ):
            errors.append("invocation request provenance mismatch")
        if result.get("output_dir") != str(validated_dir):
            errors.append("result validated directory mismatch")
        if result.get(expected_output_field) != str(expected_output) or result.get(unused_output_field) != "":
            errors.append("result output path mismatch")
        if result.get("static_status_is_authoritative") is not False:
            errors.append("result static authority flag mismatch")
        if result.get("ae_metadata_is_authoritative") is not False:
            errors.append("result AE metadata authority flag mismatch")
        for raw_field in (
            "raw_output_path",
            "output_binding_validation",
            "output_commit_revalidation",
        ):
            if raw_field in result:
                errors.append(f"result retains unauthoritative raw field: {raw_field}")
        for label, entry in (
            ("validated output", result_artifact),
            ("output observation", result_observation),
        ):
            if not json_values_equal_exact(entry, expected_artifact):
                errors.append(f"result {label} differs from validated artifact")
        if output_kind == "png":
            png_observation = result.get("png_observation")
            if not json_values_equal_exact(png_observation, expected_artifact):
                errors.append("result PNG observation differs from validated artifact")
        elif "png_observation" in result:
            errors.append("EXR result contains a PNG observation")

        stable_paths = (
            run_dir,
            runtime_dir,
            validated_dir,
            staged_request,
            staged_request / input_dir_leaf,
        )
        fixed_directories = {
            "output_container": run_dir.parent,
            "run": run_dir,
            "runtime": runtime_dir,
            "validated_output": validated_dir,
            "staged_request": staged_request,
            "staged_input": staged_request / input_dir_leaf,
        }
        directories = commit.get("directories")
        if (
            not isinstance(directories, dict)
            or set(directories) != set(fixed_directories)
        ):
            errors.append("committed directory identity set mismatch")
        else:
            for label, path in fixed_directories.items():
                if not _directory_matches_entry(
                    path,
                    directories.get(label),
                    identity_only=label == "output_container",
                ):
                    errors.append(f"committed {label} directory identity mismatch")
        directory_snapshot = commit.get("directory_chain_snapshot")
        if not directory_chains_match(directory_snapshot, stable_paths):
            errors.append("committed directory chain identity mismatch")

        final_result_bytes, final_result_source = read_bound_source_at(
            publication_descriptor,
            fixed_result.name,
            fixed_result,
        )
        if final_result_bytes != result_bytes or final_result_source != result_source:
            errors.append("result changed during consumer verification")
        final_details = (
            inspect_complete_png(Path(output_leaf), dir_fd=validated_descriptor)
            if output_kind == "png"
            else inspect_readable_nonempty_file(Path(output_leaf), dir_fd=validated_descriptor)
        )
        if details != final_details:
            errors.append("validated output changed during consumer verification")
        for source, _ in current_sources:
            if source.path.parent == staged_request:
                parent_descriptor = staged_descriptor
            else:
                parent_descriptor = input_descriptor
            _, final_source = read_bound_source_at(
                parent_descriptor,
                source.path.name,
                source.path,
            )
            if final_source != source:
                errors.append(f"staged source changed during verification: {source.path}")
        final_runtime_sources = read_fixed_runtime_sources(
            runtime_dir,
            dir_fd=runtime_descriptor,
        )
        if not runtime_source_snapshots_match(
            final_runtime_sources,
            current_runtime_sources,
        ):
            errors.append("runtime sources changed during consumer verification")
        final_commit_bytes, final_commit_source = read_bound_source_at(
            publication_descriptor,
            fixed_commit.name,
            fixed_commit,
        )
        if final_commit_bytes != commit_bytes or final_commit_source != commit_source:
            errors.append("commit changed during consumer verification")
        for label, path in fixed_directories.items():
            if (
                not isinstance(directories, dict)
                or not _directory_matches_entry(
                    path,
                    directories.get(label),
                    identity_only=label == "output_container",
                )
            ):
                errors.append(f"{label} directory changed during consumer verification")
        if not directory_chains_match(directory_snapshot, stable_paths):
            errors.append("directory chain changed during consumer verification")
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"consumer verification failed closed: {error}")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)

    return {
        "status": "passed" if not errors else "failed",
        "run_id": commit.get("run_id"),
        "commit_sha256": hashlib.sha256(commit_bytes).hexdigest() if commit_bytes else None,
        "errors": errors,
        "consumer_time_reverification_required": True,
    }


def publish_single_case_evidence(
    *,
    result: dict[str, object],
    raw_binding: ExpectedOutputBinding,
    invocation_request_dir: Path,
    validated_dir: Path,
    publication_dir: Path,
    run_id: str,
    run_dir: Path,
    runtime_source_snapshot: tuple[BoundSource, ...],
) -> tuple[Path, Path, str]:
    """Publish validated output/result and write the consumer commit marker last."""

    host_request_dir = str(raw_binding.request_dir)
    result_path = Path(publication_dir) / "AE_SINGLE_CASE_RESULT.json"
    commit_path = Path(publication_dir) / "AE_SINGLE_CASE_COMMIT.json"
    input_file_selection = validate_portable_leaf(
        raw_binding.source_snapshot[2].path.name,
        "staged input file selection",
    )
    descriptors, _ = open_absolute_directory_chain(Path(run_dir))
    publication_descriptor: int | None = None
    validated_descriptor: int | None = None
    runtime_descriptor: int | None = None
    artifact_created = False
    publication_passed = False
    try:
        run_descriptor = descriptors[-1]
        run_info = os.fstat(run_descriptor)
        run_identity = (run_info.st_dev, run_info.st_ino)
        publication_descriptor = open_exact_child_directory(
            run_descriptor,
            "publication",
        )
        validated_descriptor = open_exact_child_directory(
            run_descriptor,
            "validated_output",
        )
        runtime_descriptor = open_exact_child_directory(
            run_descriptor,
            "runtime",
        )
        runtime_sources = read_fixed_runtime_sources(
            Path(run_dir) / "runtime",
            dir_fd=runtime_descriptor,
        )
        if not runtime_source_snapshots_match(
            runtime_sources,
            runtime_source_snapshot,
        ):
            raise ValueError("runtime sources changed before publication")
        artifact = copy_validated_output(
            result,
            raw_binding,
            validated_dir,
            validated_dir_fd=validated_descriptor,
        )
        artifact_created = True
        result["run_id"] = run_id
        result["input_file_selection"] = input_file_selection
        result["invocation_request_dir"] = str(invocation_request_dir)
        result["invocation_request_dir_provenance_only"] = True
        result["host_request_dir"] = host_request_dir
        result["request_dir"] = host_request_dir
        result.pop("raw_output_path", None)
        result.pop("output_binding_validation", None)
        result.pop("output_commit_revalidation", None)
        result["validated_output"] = artifact
        result["output_dir"] = str(validated_dir)
        result["output_png"] = (
            artifact["path"] if raw_binding.output_kind == "png" else ""
        )
        result["output_exr"] = (
            artifact["path"] if raw_binding.output_kind == "exr" else ""
        )
        result["output_observation"] = artifact
        if raw_binding.output_kind == "png":
            result["png_observation"] = artifact
        else:
            result.pop("png_observation", None)
        result["generation_commit_path"] = str(commit_path)
        result["consumer_verifier"] = "verify_single_case_commit"
        result["static_status_is_authoritative"] = False
        result["ae_metadata_is_authoritative"] = False
        artifact_details = (
            inspect_complete_png(
                Path(raw_binding.output_path.name),
                dir_fd=validated_descriptor,
            )
            if raw_binding.output_kind == "png"
            else inspect_readable_nonempty_file(
                Path(raw_binding.output_path.name),
                dir_fd=validated_descriptor,
            )
        )
        if artifact_details is None or artifact_details.get("sha256") != artifact.get("sha256"):
            raise ValueError("validated artifact changed before publication")
        result_payload = write_result_json(
            result_path,
            result,
            parent_dir_fd=publication_descriptor,
        )
        result_bytes, result_source = read_bound_source_at(
            publication_descriptor,
            result_path.name,
            result_path,
        )
        if result_bytes != result_payload:
            raise ValueError("published result bytes differ from writer payload")
        stable_paths = (
            Path(run_dir),
            Path(run_dir) / "runtime",
            Path(validated_dir),
            raw_binding.request_dir,
            raw_binding.input_dir,
        )
        directory_snapshot = snapshot_directory_chains(stable_paths)
        output_container_payload = _directory_payload(Path(run_dir).parent)
        commit = {
            "schema": "olm.ae-single-case-commit/1",
            "run_id": run_id,
            "status": "passed",
            "case_id": raw_binding.case_id,
            "output_kind": raw_binding.output_kind,
            "input_file_selection": input_file_selection,
            "invocation_request_dir": str(invocation_request_dir),
            "invocation_request_dir_provenance_only": True,
            "consumer_verifier": "verify_single_case_commit",
            "consumer_time_reverification_required": True,
            "static_status_is_authoritative": False,
            "ae_metadata_is_authoritative": False,
            "directory_chain_snapshot": directory_snapshot,
            "directories": {
                "output_container": {
                    field: output_container_payload[field]
                    for field in ("path", "device", "inode")
                },
                "run": _directory_payload(Path(run_dir)),
                "runtime": _directory_payload(Path(run_dir) / "runtime"),
                "validated_output": _directory_payload(Path(validated_dir)),
                "staged_request": _directory_payload(raw_binding.request_dir),
                "staged_input": _directory_payload(raw_binding.input_dir),
            },
            "result": _bound_source_payload(result_source),
            "validated_output": dict(artifact),
            "staged_sources": [
                _bound_source_payload(source) for source in raw_binding.source_snapshot
            ],
            "runtime_sources": [
                _bound_source_payload(source) for source in runtime_sources
            ],
        }
        commit_payload = write_result_json(
            commit_path,
            commit,
            parent_dir_fd=publication_descriptor,
        )
        persisted_commit, _ = read_bound_source_at(
            publication_descriptor,
            commit_path.name,
            commit_path,
        )
        if persisted_commit != commit_payload:
            raise ValueError("published commit bytes differ from writer payload")
        commit_sha256 = hashlib.sha256(commit_payload).hexdigest()
        verification = verify_single_case_commit(
            commit_path,
            expected_run_id=run_id,
            expected_commit_sha256=commit_sha256,
            expected_commit_bytes=commit_payload,
            expected_run_identity=run_identity,
        )
        if verification.get("status") != "passed":
            result["status"] = "error"
            result["error"] = "single-case commit verification failed: " + "; ".join(
                str(value) for value in verification.get("errors", [])
            )
            failed_result_payload = write_result_json(
                result_path,
                result,
                parent_dir_fd=publication_descriptor,
            )
            failed_result_bytes, failed_result_source = read_bound_source_at(
                publication_descriptor,
                result_path.name,
                result_path,
            )
            if failed_result_bytes != failed_result_payload:
                raise ValueError("failed result publication did not persist exactly")
            commit["status"] = "failed"
            commit["result"] = _bound_source_payload(failed_result_source)
            write_result_json(
                commit_path,
                commit,
                parent_dir_fd=publication_descriptor,
            )
            try:
                os.unlink(raw_binding.output_path.name, dir_fd=validated_descriptor)
                os.fsync(validated_descriptor)
                artifact_created = False
            except FileNotFoundError:
                pass
            raise ValueError(result["error"])
        publication_passed = True
        return result_path, commit_path, commit_sha256
    finally:
        if (
            artifact_created
            and not publication_passed
            and validated_descriptor is not None
        ):
            try:
                os.unlink(raw_binding.output_path.name, dir_fd=validated_descriptor)
                os.fsync(validated_descriptor)
            except FileNotFoundError:
                pass
        if runtime_descriptor is not None:
            os.close(runtime_descriptor)
        if validated_descriptor is not None:
            os.close(validated_descriptor)
        if publication_descriptor is not None:
            os.close(publication_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument(
        "--output-mode",
        choices=("png", "png16_render_queue", "exr_render_queue"),
        default="png",
    )
    parser.add_argument("--output-template", default="", help="Output Module template required for --output-mode exr_render_queue.")
    parser.add_argument("--keep-open", action="store_true", help="Keep the live AE project/application open after rendering.")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument(
        "--param-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override one AE parameter by display name or match name, e.g. 'Use Background Color=0'.",
    )
    parser.add_argument(
        "--ae-env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Set an ExtendScript environment variable before running the case.",
    )
    parser.add_argument(
        "--lock-path",
        type=Path,
        default=Path("/tmp/olm_ae_single_case.lock"),
        help="Serialize AE host runs that use shared $.setenv state.",
    )
    parser.add_argument("--dump-js", type=Path, default=None, help="Write the generated ExtendScript wrapper and exit.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def js_string(value: str) -> str:
    return json.dumps(value)


def js_escape_expr(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


@contextlib.contextmanager
def ae_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def ae_active_marker_path(lock_path: Path) -> Path:
    """Persistent lease used when a timed-out AE script may still be running."""

    return lock_path.with_name(lock_path.name + ".active.json")


def build_single_case_wrapper_js(
    *,
    request_dir: Path,
    case_id: str,
    output_dir: Path,
    log_path: Path,
    result_json: Path,
    jsx_path: Path,
    overrides: dict[str, object],
    ae_env: dict[str, str],
    output_mode: str,
    output_template: str,
    keep_open: bool,
) -> str:
    reserved_overrides = sorted(RUNNER_OWNED_AE_ENV_KEYS.intersection(ae_env))
    if reserved_overrides:
        raise ValueError(
            "runner-owned AE environment cannot be overridden: "
            + ", ".join(reserved_overrides)
        )
    reset_env_lines = [f"$.setenv({js_string(key)}, '');" for key in VOLATILE_AE_ENV_KEYS]
    extra_env_lines = [
        f"$.setenv({js_string(key)}, {js_string(value)});"
        for key, value in sorted(ae_env.items())
    ]
    return "\n".join(
        [
            "function __olmWriteText(path, text) { var f = new File(path); f.encoding = 'UTF-8'; if (f.open('w')) { f.write(text); f.close(); } }",
            "function __olmEsc(value) { return String(value).replace(/\\\\/g, '\\\\\\\\').replace(/\"/g, '\\\\\"').replace(/\\r/g, '\\\\r').replace(/\\n/g, '\\\\n'); }",
            *reset_env_lines,
            f"$.setenv('OLM_AE_REQUEST_DIR', {js_string(str(request_dir))});",
            f"$.setenv('OLM_AE_CASE_ID', {js_string(case_id)});",
            f"$.setenv('OLM_AE_OUTPUT_DIR', {js_string(str(output_dir))});",
            f"$.setenv('OLM_AE_LOG_PATH', {js_string(str(log_path))});",
            f"$.setenv('OLM_AE_RESULT_JSON', {js_string(str(result_json))});",
            f"$.setenv('OLM_AE_PARAM_OVERRIDES_JSON', {js_string(json.dumps(overrides))});",
            f"$.setenv('OLM_AE_OUTPUT_MODE', {js_string(output_mode)});",
            f"$.setenv('OLM_AE_OUTPUT_TEMPLATE', {js_string(output_template)});",
            f"$.setenv('OLM_AE_KEEP_OPEN', {js_string('1' if keep_open else '0')});",
            *extra_env_lines,
            "try {",
            f"  $.evalFile(new File({js_string(str(jsx_path))}));",
            "} catch (__olmError) {",
            f"  __olmWriteText({js_string(str(log_path))}, 'wrapper.error ' + __olmError.toString() + '\\n');",
            (
                f"  __olmWriteText({js_string(str(result_json))}, "
                "'{\\n'"
                f" + '  \"kind\": \"olm_ae_single_case_result\",\\n'"
                f" + '  \"ae_version\": \"' + __olmEsc(app.version) + '\",\\n'"
                f" + '  \"request_dir\": \"{js_escape_expr(str(request_dir))}\",\\n'"
                f" + '  \"case_id\": \"{js_escape_expr(case_id)}\",\\n'"
                f" + '  \"output_dir\": \"{js_escape_expr(str(output_dir))}\",\\n'"
                f" + '  \"output_png\": \"\",\\n'"
                f" + '  \"output_exr\": \"\",\\n'"
                f" + '  \"status\": \"error\",\\n'"
                f" + '  \"error\": \"' + __olmEsc(__olmError.toString()) + '\",\\n'"
                f" + '  \"warnings\": []\\n'"
                " + '}\\n');"
            ),
            "}",
        ]
    )


def main() -> int:
    args = parse_args()
    root = repo_root()
    request_dir = args.request_dir.resolve()
    if not request_dir.exists():
        print(f"[FAIL] request dir not found: {request_dir}", file=sys.stderr)
        return 1
    output_container = (
        args.output_dir.resolve()
        if args.output_dir
        else Path("/tmp") / f"olm_ae_single_case_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{os.getpid()}"
    ).resolve()
    output_container.mkdir(parents=True, exist_ok=True)
    jsx_path = root / "scripts" / "ae_render_single_case.jsx"
    overrides: dict[str, object] = {}
    for item in args.param_override:
        if "=" not in item:
            print(f"[FAIL] --param-override must be NAME=JSON: {item}", file=sys.stderr)
            return 1
        key, raw_value = item.split("=", 1)
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        overrides[key] = value
    ae_env: dict[str, str] = {}
    for item in args.ae_env:
        if "=" not in item:
            print(f"[FAIL] --ae-env must be NAME=VALUE: {item}", file=sys.stderr)
            return 1
        key, value = item.split("=", 1)
        if not key:
            print(f"[FAIL] --ae-env key is empty: {item}", file=sys.stderr)
            return 1
        if key in RUNNER_OWNED_AE_ENV_KEYS:
            print(
                f"[FAIL] --ae-env cannot override runner-owned binding: {key}",
                file=sys.stderr,
            )
            return 1
        ae_env[key] = value
    if args.output_mode in ("png16_render_queue", "exr_render_queue") and not args.output_template:
        print("[FAIL] --output-template is required for render-queue output modes", file=sys.stderr)
        return 1
    if args.dump_js:
        requested_dump_path = Path(args.dump_js).absolute()
        validate_portable_leaf(requested_dump_path.name, "dump-js filename")
        requested_dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_parent = requested_dump_path.parent.resolve(strict=True)
        dump_path = dump_parent / requested_dump_path.name
        js = build_single_case_wrapper_js(
            request_dir=request_dir,
            case_id=args.case_id,
            output_dir=output_container,
            log_path=output_container / "AE_SINGLE_CASE.log",
            result_json=output_container / "AE_SINGLE_CASE_RESULT.json",
            jsx_path=jsx_path,
            overrides=overrides,
            ae_env=ae_env,
            output_mode=args.output_mode,
            output_template=args.output_template,
            keep_open=args.keep_open,
        )
        dump_descriptors, _ = open_absolute_directory_chain(dump_parent)
        try:
            atomic_write_bytes(
                dump_path,
                js.encode("utf-8"),
                mode=0o444,
                parent_dir_fd=dump_descriptors[-1],
            )
        finally:
            for descriptor in reversed(dump_descriptors):
                os.close(descriptor)
        print(f"[OK] wrote ExtendScript wrapper: {dump_path}")
        return 0
    try:
        host_program_payload, _ = read_bound_source(jsx_path)
    except (OSError, ValueError) as error:
        print(f"[FAIL] could not bind the AE host program: {error}", file=sys.stderr)
        return 1
    result: dict[str, object] = {"status": "error", "error": "single-case run did not complete"}
    run_dir: Path | None = None
    result_json: Path | None = None
    commit_json: Path | None = None
    commit_sha256: str | None = None
    with ae_lock(args.lock_path.resolve()):
        active_marker = ae_active_marker_path(args.lock_path.resolve())
        if active_marker.exists():
            print(
                f"[FAIL] prior AE host run may still be active: {active_marker}",
                file=sys.stderr,
            )
            return 1
        try:
            run_id, run_dir = create_single_run_directory(output_container)
            runtime_dir = run_dir / "runtime"
            raw_output_dir = run_dir / "raw_output"
            validated_output_dir = run_dir / "validated_output"
            publication_dir = run_dir / "publication"
            run_descriptors, _ = open_absolute_directory_chain(run_dir)
            try:
                run_descriptor = run_descriptors[-1]
                for leaf in (
                    "runtime",
                    "raw_output",
                    "validated_output",
                    "publication",
                ):
                    os.mkdir(leaf, 0o700, dir_fd=run_descriptor)
                    child_descriptor = open_exact_child_directory(run_descriptor, leaf)
                    os.close(child_descriptor)
            finally:
                for descriptor in reversed(run_descriptors):
                    os.close(descriptor)
            origin_binding = build_expected_output_binding(
                request_dir=request_dir,
                case_id=args.case_id,
                output_dir=raw_output_dir,
                output_mode=args.output_mode,
                input_file_override=ae_env.get("OLM_AE_INPUT_FILE_OVERRIDE") or None,
            )
            staged_request_dir = stage_request_sources(origin_binding, run_dir)
            expected_binding = build_expected_output_binding(
                request_dir=staged_request_dir,
                case_id=args.case_id,
                output_dir=raw_output_dir,
                output_mode=args.output_mode,
                input_file_override=ae_env.get("OLM_AE_INPUT_FILE_OVERRIDE") or None,
            )
            raw_log_path = raw_output_dir / "AE_SINGLE_CASE.log"
            raw_result_json = raw_output_dir / "AE_SINGLE_CASE_RESULT.json"
            staged_program_jsx = runtime_dir / RUNTIME_PROGRAM_LEAF
            wrapper_jsx = runtime_dir / RUNTIME_WRAPPER_LEAF
            atomic_write_bytes(raw_log_path, b"", mode=0o600)
            atomic_write_bytes(raw_result_json, b"", mode=0o600)
            runtime_descriptors, _ = open_absolute_directory_chain(runtime_dir)
            try:
                runtime_descriptor = runtime_descriptors[-1]
                atomic_write_bytes(
                    staged_program_jsx,
                    host_program_payload,
                    mode=0o444,
                    parent_dir_fd=runtime_descriptor,
                )
                js = build_single_case_wrapper_js(
                    request_dir=staged_request_dir,
                    case_id=args.case_id,
                    output_dir=raw_output_dir,
                    log_path=raw_log_path,
                    result_json=raw_result_json,
                    jsx_path=staged_program_jsx,
                    overrides=overrides,
                    ae_env=ae_env,
                    output_mode=args.output_mode,
                    output_template=args.output_template,
                    keep_open=args.keep_open,
                )
                atomic_write_bytes(
                    wrapper_jsx,
                    js.encode("utf-8"),
                    mode=0o444,
                    parent_dir_fd=runtime_descriptor,
                )
                runtime_source_snapshot = read_fixed_runtime_sources(
                    runtime_dir,
                    dir_fd=runtime_descriptor,
                )
            finally:
                for descriptor in reversed(runtime_descriptors):
                    os.close(descriptor)
            raw_log_identity = (
                raw_log_path.lstat().st_dev,
                raw_log_path.lstat().st_ino,
            )
            raw_result_identity = (
                raw_result_json.lstat().st_dev,
                raw_result_json.lstat().st_ino,
            )
        except (OSError, ValueError) as error:
            print(f"[FAIL] could not prepare run-owned single-case inputs: {error}", file=sys.stderr)
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
                "kind": "single_case",
                "owner": str(run_dir),
                "host_started_ns": host_started_ns,
                "status": "host_call_active_or_indeterminate",
            },
        )
        host_directory_snapshot = snapshot_directory_chains(
            (
                output_container,
                run_dir,
                runtime_dir,
                staged_request_dir,
                expected_binding.input_dir,
            )
        )
        if not runtime_source_snapshot_matches(
            runtime_source_snapshot,
            runtime_dir,
        ):
            print("[FAIL] run-owned runtime sources changed before host invocation", file=sys.stderr)
            try:
                active_marker.unlink()
            except OSError:
                pass
            return 1
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
            return 1
        if proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.stderr:
            print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
        host_tree_matches = directory_chains_match(
            host_directory_snapshot,
            (
                output_container,
                run_dir,
                runtime_dir,
                staged_request_dir,
                expected_binding.input_dir,
            ),
        )
        try:
            log_info = raw_log_path.lstat()
            result_info = raw_result_json.lstat()
            host_leaf_identities_match = (
                stat_module.S_ISREG(log_info.st_mode)
                and stat_module.S_ISREG(result_info.st_mode)
                and log_info.st_nlink == 1
                and result_info.st_nlink == 1
                and (log_info.st_dev, log_info.st_ino) == raw_log_identity
                and (result_info.st_dev, result_info.st_ino) == raw_result_identity
            )
        except OSError:
            host_leaf_identities_match = False
        runtime_sources_match = runtime_source_snapshot_matches(
            runtime_source_snapshot,
            runtime_dir,
        )
        if (
            not host_tree_matches
            or not host_leaf_identities_match
            or not runtime_sources_match
        ):
            failed_invariants = []
            if not host_tree_matches:
                failed_invariants.append("directory_chains")
            if not host_leaf_identities_match:
                failed_invariants.append("result_leaf_identities")
            if not runtime_sources_match:
                failed_invariants.append("runtime_sources")
            print(
                "[FAIL] run-owned host inputs or result leaves changed: "
                + ", ".join(failed_invariants),
                file=sys.stderr,
            )
            try:
                active_marker.unlink()
            except OSError:
                pass
            return 1
        if proc.returncode != 0:
            print(f"[FAIL] osascript exited {proc.returncode}", file=sys.stderr)
            try:
                active_marker.unlink()
            except OSError as error:
                print(f"[FAIL] could not clear AE active lease: {error}", file=sys.stderr)
                return 1
            print(f"[INFO] run_dir: {run_dir}")
            return proc.returncode
        if not raw_result_json.exists():
            print(f"[FAIL] AE did not write result JSON: {raw_result_json}", file=sys.stderr)
            try:
                active_marker.unlink()
            except OSError as error:
                print(f"[FAIL] could not clear AE active lease: {error}", file=sys.stderr)
            print(f"[INFO] run_dir: {run_dir}")
            return 1
        try:
            raw_result_bytes, _ = read_bound_source(raw_result_json)
            parsed_result = json.loads(raw_result_bytes.decode("utf-8-sig"))
            if not isinstance(parsed_result, dict):
                raise ValueError("AE result JSON must be an object")
            result = parsed_result
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
            print(f"[FAIL] AE result JSON is unreadable: {error}", file=sys.stderr)
            try:
                active_marker.unlink()
            except OSError:
                pass
            return 1
        if validate_result_output(
            result,
            not_before_ns=host_started_ns,
            expected_binding=expected_binding,
            timeout_seconds=output_wait_timeout(float(args.timeout)),
        ):
            try:
                result_json, commit_json, commit_sha256 = publish_single_case_evidence(
                    result=result,
                    raw_binding=expected_binding,
                    invocation_request_dir=request_dir,
                    validated_dir=validated_output_dir,
                    publication_dir=publication_dir,
                    run_id=run_id,
                    run_dir=run_dir,
                    runtime_source_snapshot=runtime_source_snapshot,
                )
            except (OSError, ValueError) as error:
                result["status"] = "error"
                result["error"] = f"could not publish bound single-case evidence: {error}"
                result["result_commit_status"] = "failed"
                print(f"[FAIL] {result['error']}", file=sys.stderr)
        if result_json is None:
            result_json = publication_dir / "AE_SINGLE_CASE_RESULT.json"
            write_result_json(result_json, result)
        try:
            active_marker.unlink()
        except OSError as error:
            print(f"[FAIL] could not clear AE active lease: {error}", file=sys.stderr)
            return 1
    print(f"[OK] AE single case status: {result.get('status')}")
    print(f"[INFO] output_container: {output_container}")
    print(f"[INFO] run_dir: {run_dir}")
    print(f"[INFO] result_json: {result_json}")
    if commit_json is not None:
        print(f"[INFO] commit_json: {commit_json}")
    if commit_sha256 is not None:
        print(f"[INFO] commit_sha256: {commit_sha256}")
    if result.get("output_png"):
        print(f"[INFO] output_png: {result['output_png']}")
    observation = result.get("output_observation") or result.get("png_observation") or {}
    if observation:
        observation_label = "png_observation" if result.get("output_png") else "output_observation"
        print(
            f"[INFO] {observation_label}: {observation.get('status')} "
            f"waited_ms={observation.get('waited_ms', 0)} "
            f"size_bytes={observation.get('size_bytes', 0)}"
        )
    if result.get("output_exr"):
        print(f"[INFO] output_exr: {result['output_exr']}")
    if result.get("status") != "ok":
        print(f"[FAIL] AE single case error: {result.get('error')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
