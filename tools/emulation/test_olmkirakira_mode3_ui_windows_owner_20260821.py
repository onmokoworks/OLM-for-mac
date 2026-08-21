#!/usr/bin/env python3
"""Strict offline verifier and opt-in live Kira Mode 3 owner capture.

The default invocation only verifies the checked-in report.  A live capture is
performed only when --capture and every explicit external path are supplied.
It runs no After Effects process: the Windows AEX is executed by AEXCompat and
the current Mac production source is exercised by the public hostless harness.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
    ROOT / "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.json"
)
DEFAULT_REPORT_PIN = DEFAULT_REPORT.with_suffix(".sha256")
MAX_REPORT_BYTES = 128 * 1024
SCHEMA = "olmkirakira.mode3-ui-windows-owner/1"
STATUS = "raw_active_bytes_exact"
DATE = "2026-08-21"
WIDTH, HEIGHT = 17, 11
LENGTHS = (1, 2, 50, 300)
ROTATIONS_RAW_FIXED = (0, 1)
DEPTHS = ("PF8", "PF16", "PF32")
DEPTH_CONTRACT = {
    "PF8": ("argb8", "argb8", 4),
    "PF16": ("argb16", "argb16le", 8),
    "PF32": ("argb32f", "argb32fle", 16),
}
EXPECTED_CELL_ORDER = tuple(
    (length, rotation, depth)
    for length in LENGTHS
    for rotation in ROTATIONS_RAW_FIXED
    for depth in DEPTHS
)

AEX_EXPECTED_SHA256 = (
    "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
)
AEX_EXPECTED_SIZE = 25_781_248
OFFICIAL_ZIP_SHA256 = (
    "2fea5b879bdee4e7641946e0bdd01e234f9ad841c8146e171a7b50f33db26b03"
)
OFFICIAL_SHA256SUMS_RELATIVE = (
    "refs/upstream_official/20260619_olm_official_zips/SHA256SUMS.txt"
)
OFFICIAL_ZIP_RELATIVE = (
    "refs/upstream_official/20260619_olm_official_zips/zips/OLMKiraKira.zip"
)
OFFICIAL_ARCHIVE_MEMBER = "OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
AEXCOMPAT_REPOSITORY = "https://github.com/onmokoworks/AEXCompat.git"
AEXCOMPAT_COMMIT = "28d535469f84f67236ef3425afe4291ea2fb0991"
AEXCOMPAT_WORKER_TARGET = "guest/target/release/aex-guest-worker"
AEXCOMPAT_BUILD_COMMAND = (
    "cargo", "build", "--manifest-path", "guest/Cargo.toml", "--release",
    "-p", "aex-guest-worker", "--frozen",
)
EXPECTED_CARGO_VERSION = "cargo 1.95.0 (f2d3ce0bd 2026-03-21)"
EXPECTED_RUSTC_VERSION = "rustc 1.95.0 (59807616e 2026-04-14)"
EXPECTED_WORKER_SIZE = 3_886_128
EXPECTED_WORKER_SHA256 = (
    "fe376e9ba1d6ee1f20cd9b6954d63542555ed4ffd52a0dfb5e8c95d1f4ccdffe"
)
AEXCOMPAT_SOURCE = (
    (
        "cargo_lock",
        "guest/Cargo.lock",
        42_844,
        "9f7d4dd02083fb81cb622a318f4448ac9bd5b889e21744d9726942bac4d3dfa9",
    ),
    (
        "worker_main",
        "guest/crates/aex-guest-worker/src/main.rs",
        41_935,
        "987e47c71054cdbf73644f8fb5a6931cb7c10d086399e61ac81eebdda4df0b24",
    ),
    (
        "worker_classic",
        "guest/crates/aex-guest-worker/src/classic.rs",
        122_159,
        "d251b8fb03b8c32dafbceb04191dc04d82909dbd049129a2024974d4b5633c84",
    ),
    (
        "worker_pixel",
        "guest/crates/aex-guest-worker/src/pixel.rs",
        8_546,
        "ee4fd50ddf44dc3f86c182ea05ad4841507f333fc132e1488a302609456c8f84",
    ),
)

SOURCE_ENTRIES = (
    ("capture_verifier", "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py"),
    ("official_zip_checksums", OFFICIAL_SHA256SUMS_RELATIVE),
    ("generic_public_harness", "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"),
    ("public_smart_harness", "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"),
    ("production_source", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("production_header", "mac/OLMKiraKira/OLMKiraKira.h"),
    ("strings_source", "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"),
    ("strings_header", "mac/OLMKiraKira/OLMKiraKira_Strings.h"),
    ("core_gaussian", "core/kirakira_gaussian.h"),
    ("core_highlight", "core/kirakira_highlight.h"),
    ("core_mode4", "core/kirakira_mode4.h"),
    ("core_warp", "core/kirakira_warp.h"),
    ("core_merge2", "core/kirakira_merge2.h"),
)

INPUT_SHA256 = {
    "rgba8": "7934392d34781b2330e4f1b451f47773d93e2f281851bd4546717ba2252068ec",
    "argb8": "3c024f8074f08c5152ba54c1b79e275eae2c5c2a2b4572a4497303cec836afd0",
    "argb16le": "b85a7304ea38b0ae22b142a3a95421a58ac3e1ff179ac53805b47a918a1f5ffb",
    "argb32fle": "2c8d46d068ef23fe313f151a4b6f4726cffbae6c98a66a5b331096e0eb849556",
}
INPUT_ACTIVE_BYTES = {"rgba8": 748, "argb8": 748, "argb16le": 1496, "argb32fle": 2992}
INPUT_COUNTS = {
    "pixels": 187,
    "transparent_pixels": 1,
    "zero_alpha_nonzero_rgb_pixels": 1,
    "partial_alpha_pixels": 185,
    "opaque_pixels": 1,
}

CLAIM_BOUNDARY = (
    "Actual Windows OLMKiraKira.aex exported SmartPreRender->SmartRender owner "
    "executed hostlessly by AEXCompat's Unicorn x86_64 backend is raw-active-byte "
    "exact against current Mac production-source public EffectMain Classic and Smart "
    "only for the fixed 17x11 fixture and listed Length, raw-fixed Rotation, and depth "
    "cells. This is not native Windows or macOS After Effects, installed-plugin, "
    "native Windows UCRT/trigonometry, GPU, or Windows padded-rowbytes evidence."
)
SOURCE_SCOPE = (
    "Declared capture/verifier, public harness, production/header/strings, Kira core "
    "headers, tracked official ZIP checksum manifest, and exact AEXCompat worker source/build "
    "identity; excludes symlinked Adobe SDK/Util, Mac system SDK/compiler, and standard-library "
    "inputs."
)
SCOPE = {
    "actual_windows_aex_exported_smart_via_aexcompat_unicorn": True,
    "worker_built_from_pinned_aexcompat_source": True,
    "mac_production_source_public_classic": True,
    "mac_production_source_public_smart": True,
    "raw_active_bytes_compared_by_sha256": True,
    "windows_tight_rowbytes_only": True,
    "native_windows_after_effects": False,
    "native_macos_after_effects": False,
    "installed_plugin": False,
    "native_windows_ucrt_or_trigonometry": False,
    "gpu": False,
    "install_or_ae_run_performed": False,
}

TOP_KEYS = {
    "schema", "date", "status", "claim_boundary", "fixture", "parameters",
    "identities", "cells", "cells_sha256", "summary", "scope",
}
FIXTURE_KEYS = {
    "width", "height", "formula", "counts", "input_active_bytes",
    "input_sha256", "input_png_sha256", "input_png_bytes",
}
PARAMETER_KEYS = {
    "lengths", "rotations_raw_fixed", "depths", "worker_pixel_formats",
    "blur_mode", "vertical_length", "diagonal_length", "diagonal2_length",
    "highlight_radius", "merge_mode", "channel", "brightness_gain_cli",
    "glow_rotation_override",
}
IDENTITY_KEYS = {
    "windows_aex", "official_distribution", "aex_guest_worker", "aexcompat",
    "repository_source", "repository_source_scope",
}
FILE_RECORD_KEYS = {"role", "path", "size_bytes", "sha256"}
AEXCOMPAT_KEYS = {
    "repository", "git_commit", "tracked_worktree_clean", "source_files",
    "worker_build",
}
WORKER_BUILD_KEYS = {
    "command", "working_directory", "cargo_version", "rustc_version",
    "target", "target_size_bytes", "target_sha256", "completed",
}
OFFICIAL_DISTRIBUTION_KEYS = {
    "checksum_manifest_path", "checksum_manifest_sha256", "zip_path",
    "zip_sha256", "archive_member", "archive_member_size_bytes",
    "archive_member_sha256",
}
CELL_KEYS = {
    "length", "rotation_raw_fixed", "depth", "pixel_format", "active_bytes",
    "input_sha256", "windows_exported_smart_sha256",
    "mac_public_smart_sha256", "mac_public_classic_sha256", "routes_exact",
    "windows_lifecycle",
}
LIFECYCLE_KEYS = {
    "worker_schema_version", "render_mode", "render_error", "guards_intact",
    "output_request", "input_requests", "suite_requests",
    "unsupported_suite_calls", "setup_unsupported_suite_calls",
    "dropped_unsupported_suite_calls", "smart_pre_render", "smart_render",
    "cleanup_complete", "input_png_file_unchanged",
}
SMART_PHASE_KEYS = {"selector", "attempted", "completed", "error"}
SUMMARY_KEYS = {
    "cell_count", "exact_cell_count", "route_count", "active_bytes_per_depth",
    "all_routes_exact", "all_windows_lifecycle_exact",
}
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class VerificationFailure(RuntimeError):
    """A capture or report failed its strict evidence contract."""


def canonical_sha256(value: Any) -> str:
    """SHA-256 of strict compact, sorted canonical JSON (no presentation newline)."""
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_bytes(report: Mapping[str, Any]) -> bytes:
    """Return the one accepted on-disk presentation for a parsed report.

    Offline verification requires the input bytes to equal this serialization,
    so each accepted parsed report has exactly one file-byte representation.
    """
    return (json.dumps(
        report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def _is_sha(value: Any) -> bool:
    return type(value) is str and SHA_RE.fullmatch(value) is not None


def _read_regular_file_bounded(
    path: Path | str,
    *,
    max_bytes: int,
    label: str,
) -> bytes:
    """Read one stable regular file without following links or blocking."""
    candidate = Path(path)
    _require(type(max_bytes) is int and max_bytes >= 0,
             f"invalid {label} size limit")
    _require(not candidate.is_symlink(), f"{label} is a symlink: {candidate}")
    flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
             | getattr(os, "O_NONBLOCK", 0)
             | getattr(os, "O_NOFOLLOW", 0))
    descriptor = os.open(candidate, flags)
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode),
                 f"{label} is not a regular file: {candidate}")
        _require(0 <= before.st_size <= max_bytes,
                 f"{label} exceeds {max_bytes} bytes")
        payload = b""
        read_limit = before.st_size + 1
        while len(payload) < read_limit:
            chunk = os.read(descriptor, min(65_536, read_limit - len(payload)))
            if not chunk:
                break
            payload += chunk
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
        )
        _require(identity_before == identity_after,
                 f"{label} changed while reading")
        _require(len(payload) == before.st_size,
                 f"{label} size changed while reading")
        return payload
    finally:
        os.close(descriptor)


def _read_report_bytes(path: Path | str) -> bytes:
    return _read_regular_file_bounded(
        path, max_bytes=MAX_REPORT_BYTES, label="report",
    )


def _read_default_report_pin(path: Path | None = None) -> str:
    """Read one strict lowercase SHA-256 line from the independent sidecar."""
    pin_path = DEFAULT_REPORT_PIN if path is None else Path(path)
    payload = _read_regular_file_bounded(
        pin_path, max_bytes=65, label="report pin",
    )
    _require(len(payload) == 65 and payload[-1:] == b"\n",
             "report pin must be 64 lowercase hex bytes plus newline")
    try:
        expected = payload[:-1].decode("ascii")
    except UnicodeDecodeError as error:
        raise VerificationFailure("report pin is not ASCII") from error
    _require(_is_sha(expected), "report pin is not a lowercase SHA-256")
    return expected


def _require_json_exact(actual: Any, expected: Any, label: str) -> None:
    """Require equal JSON values without Python's bool/int/float coercion."""
    _require(type(actual) is type(expected), f"{label} type mismatch")
    if type(expected) is dict:
        _require(set(actual) == set(expected), f"{label} keys mismatch")
        for key in expected:
            _require_json_exact(actual[key], expected[key], f"{label}.{key}")
    elif type(expected) is list:
        _require(len(actual) == len(expected), f"{label} length mismatch")
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            _require_json_exact(actual_item, expected_item, f"{label}[{index}]")
    else:
        _require(actual == expected, f"{label} value mismatch")


def _file_record(role: str, relative: str, root: Path) -> dict[str, Any]:
    _require(role != "" and relative != "", "empty file binding")
    relative_path = Path(relative)
    _require(not relative_path.is_absolute(), f"absolute bound path: {relative}")
    root_resolved = root.resolve(strict=True)
    candidate = (root / relative_path).resolve(strict=True)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as error:
        raise VerificationFailure(f"bound path escapes root: {relative}") from error
    _require(candidate.is_file() and not candidate.is_symlink(), f"not regular file: {relative}")
    before = candidate.stat()
    payload = candidate.read_bytes()
    after = candidate.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    _require(identity_before == identity_after and len(payload) == after.st_size,
             f"file changed while hashing: {relative}")
    return {
        "role": role,
        "path": relative_path.as_posix(),
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _external_file_record(role: str, path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    _require(resolved.is_file() and not resolved.is_symlink(), f"not regular file: {path}")
    before = resolved.stat()
    payload = resolved.read_bytes()
    after = resolved.stat()
    _require(
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        f"external file changed while hashing: {path}",
    )
    canonical_name = {
        "windows_aex": "OLMKiraKira.aex",
        "aex_guest_worker": "aex-guest-worker",
    }.get(role, resolved.name)
    return {"role": role, "path": canonical_name, "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def repository_source_records() -> list[dict[str, Any]]:
    sums = (ROOT / OFFICIAL_SHA256SUMS_RELATIVE).read_text(encoding="utf-8").splitlines()
    expected_line = f"{OFFICIAL_ZIP_SHA256}  {OFFICIAL_ZIP_RELATIVE}"
    _require(sums.count(expected_line) == 1,
             "tracked official OLMKiraKira ZIP checksum line mismatch")
    return [_file_record(role, path, ROOT) for role, path in SOURCE_ENTRIES]


def official_distribution_identity(
    source_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    manifests = [
        record for record in source_records
        if record.get("role") == "official_zip_checksums"
    ]
    _require(len(manifests) == 1, "official checksum manifest binding missing")
    manifest = manifests[0]
    _require(manifest.get("path") == OFFICIAL_SHA256SUMS_RELATIVE
             and _is_sha(manifest.get("sha256")),
             "official checksum manifest binding invalid")
    return {
        "checksum_manifest_path": OFFICIAL_SHA256SUMS_RELATIVE,
        "checksum_manifest_sha256": manifest["sha256"],
        "zip_path": OFFICIAL_ZIP_RELATIVE,
        "zip_sha256": OFFICIAL_ZIP_SHA256,
        "archive_member": OFFICIAL_ARCHIVE_MEMBER,
        "archive_member_size_bytes": AEX_EXPECTED_SIZE,
        "archive_member_sha256": AEX_EXPECTED_SHA256,
    }


def aexcompat_source_identity(source_root: Path | str) -> dict[str, Any]:
    root = Path(source_root).resolve(strict=True)
    _require(root.is_dir(), f"AEXCompat source is not a directory: {root}")
    commit_run = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
        capture_output=True, timeout=30,
    )
    _require(commit_run.returncode == 0, f"cannot inspect AEXCompat commit: {commit_run.stderr}")
    commit = commit_run.stdout.strip()
    _require(commit == AEXCOMPAT_COMMIT, f"AEXCompat commit mismatch: {commit}")
    status_run = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=no"],
        text=True, capture_output=True, timeout=30,
    )
    _require(status_run.returncode == 0,
             f"cannot inspect AEXCompat worktree: {status_run.stderr}")
    _require(status_run.stdout == "", "AEXCompat tracked worktree is dirty")
    records = []
    for role, relative, expected_size, expected_sha in AEXCOMPAT_SOURCE:
        record = _file_record(role, relative, root)
        _require(record["size_bytes"] == expected_size, f"AEXCompat size drift: {relative}")
        _require(record["sha256"] == expected_sha, f"AEXCompat hash drift: {relative}")
        records.append(record)
    return {"repository": AEXCOMPAT_REPOSITORY, "git_commit": commit,
            "tracked_worktree_clean": True, "source_files": records}


def _tool_version(command: str) -> str:
    result = subprocess.run(
        [command, "--version"], text=True, capture_output=True, timeout=30,
    )
    _require(result.returncode == 0, f"{command} --version failed: {result.stderr}")
    value = result.stdout.strip()
    _require(value != "", f"{command} --version returned no version")
    return value


def _worker_build_identity(source_root: Path, worker_path: Path) -> dict[str, Any]:
    root = source_root.resolve(strict=True)
    expected_worker = (root / AEXCOMPAT_WORKER_TARGET).resolve()
    requested_worker = worker_path.resolve()
    _require(requested_worker == expected_worker,
             "--worker must be <aexcompat-source>/guest/target/release/aex-guest-worker")
    cargo_version = _tool_version("cargo")
    rustc_version = _tool_version("rustc")
    _require(cargo_version == EXPECTED_CARGO_VERSION,
             f"Cargo version mismatch: {cargo_version}")
    _require(rustc_version == EXPECTED_RUSTC_VERSION,
             f"rustc version mismatch: {rustc_version}")
    build = subprocess.run(
        list(AEXCOMPAT_BUILD_COMMAND), cwd=root, text=True,
        capture_output=True, timeout=600,
    )
    _require(build.returncode == 0,
             f"AEXCompat worker build failed: {build.stderr[-12000:]}")
    worker = _external_file_record("aex_guest_worker", expected_worker)
    _require(worker["size_bytes"] == EXPECTED_WORKER_SIZE
             and worker["sha256"] == EXPECTED_WORKER_SHA256,
             "commit28d frozen-build worker identity mismatch")
    return {
        "command": list(AEXCOMPAT_BUILD_COMMAND),
        "working_directory": ".",
        "cargo_version": cargo_version,
        "rustc_version": rustc_version,
        "target": AEXCOMPAT_WORKER_TARGET,
        "target_size_bytes": worker["size_bytes"],
        "target_sha256": worker["sha256"],
        "completed": True,
    }


def _verify_external_aexcompat(
    source_root: Path | str, expected: Mapping[str, Any],
) -> None:
    source = aexcompat_source_identity(source_root)
    _require(
        source == {key: expected[key] for key in source},
        "external AEXCompat source checkout mismatch",
    )
    build = expected["worker_build"]
    root = Path(source_root).resolve(strict=True)
    target = _external_file_record(
        "aex_guest_worker", root / AEXCOMPAT_WORKER_TARGET,
    )
    _require(target["size_bytes"] == build["target_size_bytes"]
             and target["sha256"] == build["target_sha256"],
             "external AEXCompat built worker mismatch")
    _require(_tool_version("cargo") == build["cargo_version"]
             and _tool_version("rustc") == build["rustc_version"],
             "external AEXCompat build toolchain mismatch")


def _fixture_bytes() -> dict[str, bytes]:
    pixels: list[tuple[int, int, int, int]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            value = (
                ((x * 0x9E3779B9) & 0xFFFFFFFF)
                ^ ((y * 0x85EBCA6B) & 0xFFFFFFFF)
                ^ 0x51F15E5D
            ) & 0xFFFFFFFF
            alpha = 0 if value == 0x51F15E5D else 32 + ((value >> 24) & 223)
            pixels.append((value & 255, (value >> 8) & 255,
                           (value >> 16) & 255, alpha))
    rgba8 = b"".join(bytes(pixel) for pixel in pixels)
    argb8 = b"".join(bytes((a, r, g, b)) for r, g, b, a in pixels)
    argb16le = b"".join(
        struct.pack("<4H", *((channel * 32768 + 127) // 255
                             for channel in (a, r, g, b)))
        for r, g, b, a in pixels
    )
    argb32fle = b"".join(
        struct.pack("<4f", *(channel / 255.0 for channel in (a, r, g, b)))
        for r, g, b, a in pixels
    )
    result = {"rgba8": rgba8, "argb8": argb8,
              "argb16le": argb16le, "argb32fle": argb32fle}
    _require({name: len(data) for name, data in result.items()} == INPUT_ACTIVE_BYTES,
             "fixture byte counts drifted")
    _require({name: hashlib.sha256(data).hexdigest() for name, data in result.items()}
             == INPUT_SHA256, "fixture hashes drifted")
    return result


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def fixture_png() -> bytes:
    rgba = _fixture_bytes()["rgba8"]
    rows = b"".join(
        b"\x00" + rgba[y * WIDTH * 4:(y + 1) * WIDTH * 4]
        for y in range(HEIGHT)
    )
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header)
            + _png_chunk(b"IDAT", zlib.compress(rows, 9)) + _png_chunk(b"IEND", b""))


def fixture_contract() -> dict[str, Any]:
    png = fixture_png()
    return {
        "width": WIDTH,
        "height": HEIGHT,
        "formula": (
            "v=(x*0x9e3779b9)^(y*0x85ebca6b)^0x51f15e5d (u32); "
            "RGBA=(v&255,(v>>8)&255,(v>>16)&255,"
            "v==0x51f15e5d?0:32+((v>>24)&223))"
        ),
        "counts": dict(INPUT_COUNTS),
        "input_active_bytes": dict(INPUT_ACTIVE_BYTES),
        "input_sha256": dict(INPUT_SHA256),
        "input_png_sha256": hashlib.sha256(png).hexdigest(),
        "input_png_bytes": len(png),
    }


def parameter_contract() -> dict[str, Any]:
    return {
        "lengths": list(LENGTHS),
        "rotations_raw_fixed": list(ROTATIONS_RAW_FIXED),
        "depths": list(DEPTHS),
        "worker_pixel_formats": {depth: DEPTH_CONTRACT[depth][0] for depth in DEPTHS},
        "blur_mode": 3,
        "vertical_length": 0,
        "diagonal_length": 0,
        "diagonal2_length": 0,
        "highlight_radius": 0,
        "merge_mode": 1,
        "channel": 1,
        "brightness_gain_cli": "0.1",
        "glow_rotation_override": "Glow Rotation=fixed:{raw_i32}",
    }


def _expected_lifecycle() -> dict[str, Any]:
    phase_pre = {"selector": "SMART_PRE_RENDER", "attempted": True,
                 "completed": True, "error": 0}
    phase_render = {"selector": "SMART_RENDER", "attempted": True,
                    "completed": True, "error": 0}
    return {
        "worker_schema_version": 1,
        "render_mode": "smart-cpu",
        "render_error": 0,
        "guards_intact": True,
        "output_request": [0, 0, WIDTH, HEIGHT],
        "input_requests": [[0, 0, WIDTH, HEIGHT]],
        "suite_requests": ["PF Handle Suite v2", "AEGP Utility Suite v13",
                           "PF ColorParamSuite v1"],
        "unsupported_suite_calls": [],
        "setup_unsupported_suite_calls": [],
        "dropped_unsupported_suite_calls": 0,
        "smart_pre_render": phase_pre,
        "smart_render": phase_render,
        "cleanup_complete": True,
        "input_png_file_unchanged": True,
    }


def _summary() -> dict[str, Any]:
    return {
        "cell_count": 24,
        "exact_cell_count": 24,
        "route_count": 3,
        "active_bytes_per_depth": {
            depth: WIDTH * HEIGHT * DEPTH_CONTRACT[depth][2] for depth in DEPTHS
        },
        "all_routes_exact": True,
        "all_windows_lifecycle_exact": True,
    }


def _require_exact_keys(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    _require(type(value) is dict, f"{label} is not an object")
    _require(set(value) == keys, f"{label} keys mismatch")
    return value


def _verify_file_records(value: Any, expected: Sequence[Mapping[str, Any]], label: str) -> None:
    _require(type(value) is list, f"{label} is not a list")
    _require(len(value) == len(expected), f"{label} length mismatch")
    for index, record in enumerate(value):
        _require_exact_keys(record, FILE_RECORD_KEYS, f"{label}[{index}]")
        _require(type(record["size_bytes"]) is int and record["size_bytes"] >= 0,
                 f"{label}[{index}] size")
        _require(_is_sha(record["sha256"]), f"{label}[{index}] sha")
    _require_json_exact(value, list(expected), f"{label} identity")


def _verify_report_or_raise(
    report: Any,
    expected_report_sha256: str | None = None,
    external_aex: Path | str | None = None,
    external_worker: Path | str | None = None,
    aexcompat_source: Path | str | None = None,
) -> None:
    top = _require_exact_keys(report, TOP_KEYS, "report")
    _require(top["schema"] == SCHEMA, "schema mismatch")
    _require(top["date"] == DATE, "date mismatch")
    _require(top["status"] == STATUS, "status mismatch")
    _require(top["claim_boundary"] == CLAIM_BOUNDARY, "claim boundary mismatch")

    fixture = _require_exact_keys(top["fixture"], FIXTURE_KEYS, "fixture")
    _require_exact_keys(fixture["counts"], set(INPUT_COUNTS), "fixture.counts")
    _require_exact_keys(fixture["input_active_bytes"], set(INPUT_ACTIVE_BYTES),
                        "fixture.input_active_bytes")
    _require_exact_keys(fixture["input_sha256"], set(INPUT_SHA256),
                        "fixture.input_sha256")
    _require_json_exact(fixture, fixture_contract(), "fixture")
    parameters = _require_exact_keys(top["parameters"], PARAMETER_KEYS, "parameters")
    _require_json_exact(parameters, parameter_contract(), "parameters")

    identities = _require_exact_keys(top["identities"], IDENTITY_KEYS, "identities")
    _require(identities["repository_source_scope"] == SOURCE_SCOPE,
             "repository source scope mismatch")
    expected_repo = repository_source_records()
    _verify_file_records(identities["repository_source"], expected_repo,
                         "identities.repository_source")
    aex = _require_exact_keys(identities["windows_aex"], FILE_RECORD_KEYS,
                              "identities.windows_aex")
    _require_json_exact(aex, {
        "role": "windows_aex",
        "path": "OLMKiraKira.aex",
        "size_bytes": AEX_EXPECTED_SIZE,
        "sha256": AEX_EXPECTED_SHA256,
    }, "identities.windows_aex")
    distribution = _require_exact_keys(
        identities["official_distribution"], OFFICIAL_DISTRIBUTION_KEYS,
        "identities.official_distribution",
    )
    _require_json_exact(
        distribution, official_distribution_identity(expected_repo),
        "identities.official_distribution",
    )
    _require(distribution["archive_member_size_bytes"] == aex["size_bytes"]
             and distribution["archive_member_sha256"] == aex["sha256"],
             "official archive member does not bind the captured AEX")
    worker = _require_exact_keys(identities["aex_guest_worker"], FILE_RECORD_KEYS,
                                 "identities.aex_guest_worker")
    _require_json_exact(worker, {
        "role": "aex_guest_worker",
        "path": "aex-guest-worker",
        "size_bytes": EXPECTED_WORKER_SIZE,
        "sha256": EXPECTED_WORKER_SHA256,
    }, "identities.aex_guest_worker")
    compat = _require_exact_keys(identities["aexcompat"], AEXCOMPAT_KEYS,
                                 "identities.aexcompat")
    expected_compat_files = [
        {"role": role, "path": path, "size_bytes": size, "sha256": sha}
        for role, path, size, sha in AEXCOMPAT_SOURCE
    ]
    _require(compat["repository"] == AEXCOMPAT_REPOSITORY
             and compat["git_commit"] == AEXCOMPAT_COMMIT
             and compat["tracked_worktree_clean"] is True,
             "AEXCompat identity mismatch")
    _verify_file_records(compat["source_files"], expected_compat_files,
                         "identities.aexcompat.source_files")
    worker_build = _require_exact_keys(
        compat["worker_build"], WORKER_BUILD_KEYS,
        "identities.aexcompat.worker_build",
    )
    _require_json_exact(worker_build, {
        "command": list(AEXCOMPAT_BUILD_COMMAND),
        "working_directory": ".",
        "cargo_version": EXPECTED_CARGO_VERSION,
        "rustc_version": EXPECTED_RUSTC_VERSION,
        "target": AEXCOMPAT_WORKER_TARGET,
        "target_size_bytes": EXPECTED_WORKER_SIZE,
        "target_sha256": EXPECTED_WORKER_SHA256,
        "completed": True,
    }, "identities.aexcompat.worker_build")
    _require(worker_build["target_size_bytes"] == worker["size_bytes"]
             and worker_build["target_sha256"] == worker["sha256"],
             "AEXCompat build target does not bind the captured worker")

    cells = top["cells"]
    _require(type(cells) is list and len(cells) == len(EXPECTED_CELL_ORDER),
             "cell count mismatch")
    observed_order: list[tuple[int, int, str]] = []
    lifecycle_expected = _expected_lifecycle()
    for index, cell_value in enumerate(cells):
        cell = _require_exact_keys(cell_value, CELL_KEYS, f"cells[{index}]")
        _require(type(cell["length"]) is int, f"cells[{index}] length type")
        _require(type(cell["rotation_raw_fixed"]) is int,
                 f"cells[{index}] rotation type")
        _require(type(cell["depth"]) is str, f"cells[{index}] depth type")
        key = (cell["length"], cell["rotation_raw_fixed"], cell["depth"])
        observed_order.append(key)
        _require(key == EXPECTED_CELL_ORDER[index], f"cells[{index}] order/key mismatch")
        pixel_format, input_key, pixel_size = DEPTH_CONTRACT[cell["depth"]]
        active_bytes = WIDTH * HEIGHT * pixel_size
        _require(cell["pixel_format"] == pixel_format, f"cells[{index}] format")
        _require(type(cell["active_bytes"]) is int and cell["active_bytes"] == active_bytes,
                 f"cells[{index}] active byte count")
        _require(cell["input_sha256"] == INPUT_SHA256[input_key],
                 f"cells[{index}] input hash")
        route_hashes = [cell["windows_exported_smart_sha256"],
                        cell["mac_public_smart_sha256"],
                        cell["mac_public_classic_sha256"]]
        _require(all(_is_sha(value) for value in route_hashes),
                 f"cells[{index}] route hash format")
        _require(len(set(route_hashes)) == 1 and cell["routes_exact"] is True,
                 f"cells[{index}] route mismatch")
        lifecycle = _require_exact_keys(cell["windows_lifecycle"], LIFECYCLE_KEYS,
                                        f"cells[{index}].windows_lifecycle")
        _require_exact_keys(lifecycle["smart_pre_render"], SMART_PHASE_KEYS,
                            f"cells[{index}].smart_pre_render")
        _require_exact_keys(lifecycle["smart_render"], SMART_PHASE_KEYS,
                            f"cells[{index}].smart_render")
        _require_json_exact(
            lifecycle, lifecycle_expected, f"cells[{index}].windows_lifecycle",
        )
    _require(tuple(observed_order) == EXPECTED_CELL_ORDER
             and len(set(observed_order)) == 24, "Cartesian matrix mismatch")
    _require(_is_sha(top["cells_sha256"])
             and top["cells_sha256"] == canonical_sha256(cells),
             "canonical cells digest mismatch")
    summary = _require_exact_keys(top["summary"], SUMMARY_KEYS, "summary")
    _require_json_exact(summary, _summary(), "summary")
    scope = _require_exact_keys(top["scope"], set(SCOPE), "scope")
    _require_json_exact(scope, SCOPE, "scope")

    if expected_report_sha256 is not None:
        _require(_is_sha(expected_report_sha256), "invalid expected report SHA-256")
        _require(canonical_sha256(report) == expected_report_sha256,
                 "canonical whole-report SHA-256 mismatch")
    if external_aex is not None:
        _require(_external_file_record("windows_aex", Path(external_aex)) == dict(aex),
                 "external AEX mismatch")
    if external_worker is not None:
        _require(_external_file_record("aex_guest_worker", Path(external_worker))
                 == dict(worker), "external worker mismatch")
    if aexcompat_source is not None:
        _verify_external_aexcompat(aexcompat_source, compat)


def verify_report(
    report: Any,
    expected_report_sha256: str | None = None,
    external_aex: Path | str | None = None,
    external_worker: Path | str | None = None,
    aexcompat_source: Path | str | None = None,
) -> bool:
    """Return True only for a complete, exact, source-bound report.

    Omitting ``expected_report_sha256`` binds verification to the tracked
    report's independent sidecar. Callers verifying an alternate report must
    explicitly supply its trusted canonical whole-report SHA-256.
    """
    try:
        if expected_report_sha256 is None:
            expected_report_sha256 = _read_default_report_pin()
        _verify_report_or_raise(
            report, expected_report_sha256, external_aex, external_worker,
            aexcompat_source,
        )
    except (OSError, ValueError, TypeError, subprocess.SubprocessError,
            VerificationFailure):
        return False
    return True


def _parse_tokens(line: str) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for token in line.split()[1:]:
        _require("=" in token, f"unparseable Mac harness token: {token}")
        key, value = token.split("=", 1)
        _require(key not in tokens, f"duplicate Mac harness token: {key}")
        tokens[key] = value
    expected = {
        "tuple", "length", "rotation", "depth", "size", "ok", "content",
        "callbacks", "strides", "params", "lifecycle", "headers", "mixed_alpha",
        "zero_alpha_rgb", "predata", "deleted", "handles", "input_active_hex",
        "smart_active_hex", "classic_active_hex",
    }
    _require(set(tokens) == expected, "Mac harness token set mismatch")
    return tokens


def _compile_and_run_mac_matrix(directory: Path) -> dict[tuple[int, int, str], dict[str, bytes]]:
    sdk_run = subprocess.run(["xcrun", "--show-sdk-path"], text=True,
                             capture_output=True, timeout=30)
    _require(sdk_run.returncode == 0, f"xcrun failed: {sdk_run.stderr}")
    executable = directory / "mode3-public-matrix"
    source = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
    harness = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"
    command = [
        "clang++", "-std=c++20", "-O2", "-DNDEBUG", "-fno-fast-math",
        "-ffp-contract=off", "-isysroot", sdk_run.stdout.strip(), "-w",
        "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
        f'-DKIRA_SOURCE="{source}"', str(harness),
        str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
        str(ROOT / "Util/MissingSuiteError.cpp"), "-framework", "Cocoa",
        "-o", str(executable),
    ]
    build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                           timeout=180)
    _require(build.returncode == 0, f"Mac harness build failed: {build.stderr[-12000:]}")
    run = subprocess.run([str(executable), "--mode3-public-matrix"], cwd=ROOT,
                         text=True, capture_output=True, timeout=300)
    _require(run.returncode == 0, f"Mac harness failed: {run.stdout[-12000:]}\n{run.stderr[-12000:]}")
    rows = [line for line in run.stdout.splitlines() if line.startswith("GENERIC ")]
    _require(len(rows) == 24, "Mac harness did not emit 24 rows")
    fixture = _fixture_bytes()
    result: dict[tuple[int, int, str], dict[str, bytes]] = {}
    for line in rows:
        values = _parse_tokens(line)
        depth = f"PF{int(values['depth'])}"
        rotation_float = float(values["rotation"])
        rotation = int(rotation_float)
        key = (int(values["length"]), rotation, depth)
        _require(rotation_float == float(rotation) and key in EXPECTED_CELL_ORDER,
                 f"Mac harness unexpected key: {key}")
        _require(key not in result, f"Mac harness duplicate key: {key}")
        _require(values["tuple"] == "m3_ui_length" and values["size"] == "17x11"
                 and values["ok"] == "1" and values["content"] == "full"
                 and values["callbacks"] == "1/1/1/0" and values["params"] == "25/25",
                 f"Mac harness contract failed: {key}")
        for name in ("lifecycle", "headers", "mixed_alpha", "zero_alpha_rgb",
                     "predata", "deleted", "handles"):
            _require(values[name] == "1", f"Mac harness {name} failed: {key}")
        strides = [int(item) for item in values["strides"].split("/")]
        _require(len(strides) == 3 and len(set(strides)) == 3,
                 f"Mac harness strides invalid: {key}")
        decoded = {
            "input": bytes.fromhex(values["input_active_hex"]),
            "smart": bytes.fromhex(values["smart_active_hex"]),
            "classic": bytes.fromhex(values["classic_active_hex"]),
        }
        input_key = DEPTH_CONTRACT[depth][1]
        _require(decoded["input"] == fixture[input_key], f"Mac input drift: {key}")
        _require(decoded["smart"] == decoded["classic"], f"Mac route mismatch: {key}")
        expected_bytes = WIDTH * HEIGHT * DEPTH_CONTRACT[depth][2]
        _require(all(len(payload) == expected_bytes for payload in decoded.values()),
                 f"Mac active length mismatch: {key}")
        result[key] = decoded
    _require(tuple(sorted(result, key=EXPECTED_CELL_ORDER.index)) == EXPECTED_CELL_ORDER,
             "Mac harness Cartesian matrix mismatch")
    return result


def _expected_parameter_values(length: int, rotation: int) -> list[dict[str, Any]]:
    return [
        {"name": "Channel", "slot": 1, "value": 1.0},
        {"name": "Blur Mode", "slot": 2, "value": 3.0},
        {"name": "Merge mode", "slot": 3, "value": 1.0},
        {"name": "Brightness Gain", "slot": 5, "value": 0.1},
        {"name": "Vertical Length", "slot": 10, "value": 0.0},
        {"name": "Horizontal Length", "slot": 16, "value": float(length)},
        {"name": "Diagonal Length", "slot": 22, "value": 0.0},
        {"name": "Diagonal 2 length", "slot": 28, "value": 0.0},
        {"name": "Highlight Radius", "slot": 34, "value": 0.0},
        {"angle_fixed": rotation, "name": "Glow Rotation", "slot": 40},
    ]


def _worker_lifecycle(data: Mapping[str, Any], length: int, rotation: int,
                      depth: str, input_png: Path, output_png: Path) -> dict[str, Any]:
    required = {
        "dropped_unsupported_suite_calls", "gpu", "guards_intact", "height",
        "input_png_sha256", "input_requests", "output_png", "output_request",
        "parameter_values", "pixel_bytes", "pixel_format", "raw_pixel_bytes",
        "raw_pixel_sha256", "render_error", "render_mode", "schema_version",
        "setup", "suite_requests", "unsupported_suite_calls", "width",
    }
    _require(set(data) == required, "worker JSON key set mismatch")
    pixel_format, _, pixel_size = DEPTH_CONTRACT[depth]
    active_bytes = WIDTH * HEIGHT * pixel_size
    _require(data["width"] == WIDTH and data["height"] == HEIGHT,
             "worker dimensions mismatch")
    _require(data["pixel_format"] == pixel_format and data["pixel_bytes"] == active_bytes
             and data["raw_pixel_bytes"] == active_bytes, "worker pixel contract mismatch")
    _require(data["input_png_sha256"] == hashlib.sha256(input_png.read_bytes()).hexdigest(),
             "worker input PNG hash mismatch")
    _require(Path(data["output_png"]).resolve() == output_png.resolve(),
             "worker output path mismatch")
    _require(data["parameter_values"] == _expected_parameter_values(length, rotation),
             "worker parameter override mismatch")
    expected = _expected_lifecycle()
    gpu = data["gpu"]
    setup = data["setup"]
    lifecycle = {
        "worker_schema_version": data["schema_version"],
        "render_mode": data["render_mode"],
        "render_error": data["render_error"],
        "guards_intact": data["guards_intact"],
        "output_request": data["output_request"],
        "input_requests": data["input_requests"],
        "suite_requests": data["suite_requests"],
        "unsupported_suite_calls": data["unsupported_suite_calls"],
        "setup_unsupported_suite_calls": setup.get("unsupported_suite_calls"),
        "dropped_unsupported_suite_calls": data["dropped_unsupported_suite_calls"],
        "smart_pre_render": gpu.get("pre_render"),
        "smart_render": gpu.get("render"),
        "cleanup_complete": gpu.get("cleanup_complete"),
        "input_png_file_unchanged": True,
    }
    _require(lifecycle == expected, "worker Smart lifecycle mismatch")
    _require(setup.get("execution_backend") == "unicorn-x86_64"
             and setup.get("global_setup_error") == 0
             and setup.get("params_setup_error") == 0
             and setup.get("advertised_num_params") == 41
             and setup.get("dropped_unsupported_suite_calls") == 0,
             "worker setup contract mismatch")
    _require(_is_sha(data["raw_pixel_sha256"]), "worker raw hash invalid")
    return lifecycle


def capture_report(aex_path: Path, worker_path: Path,
                   aexcompat_source: Path) -> dict[str, Any]:
    source_before = repository_source_records()
    aex_record = _external_file_record("windows_aex", aex_path)
    _require(aex_record["size_bytes"] == AEX_EXPECTED_SIZE
             and aex_record["sha256"] == AEX_EXPECTED_SHA256,
             "supplied AEX is not the pinned owner")
    compat_source_before = aexcompat_source_identity(aexcompat_source)
    worker_build = _worker_build_identity(
        Path(aexcompat_source), Path(worker_path),
    )
    worker_record = _external_file_record("aex_guest_worker", worker_path)
    compat_capture = {**compat_source_before, "worker_build": worker_build}
    fixture = fixture_contract()
    with tempfile.TemporaryDirectory(prefix="kira-mode3-owner24.") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        input_png.write_bytes(fixture_png())
        mac = _compile_and_run_mac_matrix(directory)
        cells: list[dict[str, Any]] = []
        for length, rotation, depth in EXPECTED_CELL_ORDER:
            pixel_format, input_key, pixel_size = DEPTH_CONTRACT[depth]
            output_png = directory / f"l{length}_r{rotation}_{depth}.png"
            input_before = hashlib.sha256(input_png.read_bytes()).hexdigest()
            command = [
                str(worker_path.resolve()), "render-png", str(aex_path.resolve()),
                str(input_png), str(output_png), "--pixel-format", pixel_format,
                "Blur Mode=3", "Vertical Length=0", f"Horizontal Length={length}",
                "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=0",
                "Merge mode=1", "Channel=1", "Brightness Gain=0.1",
                f"Glow Rotation=fixed:{rotation}",
            ]
            run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                                 timeout=120)
            _require(run.returncode == 0,
                     f"worker failed for {(length, rotation, depth)}: {run.stderr[-12000:]}")
            _require(hashlib.sha256(input_png.read_bytes()).hexdigest() == input_before,
                     "worker changed input PNG")
            worker_json = json.loads(run.stdout)
            lifecycle = _worker_lifecycle(worker_json, length, rotation, depth,
                                          input_png, output_png)
            mac_row = mac[(length, rotation, depth)]
            smart_sha = hashlib.sha256(mac_row["smart"]).hexdigest()
            classic_sha = hashlib.sha256(mac_row["classic"]).hexdigest()
            windows_sha = worker_json["raw_pixel_sha256"]
            _require(windows_sha == smart_sha == classic_sha,
                     f"route mismatch for {(length, rotation, depth)}")
            cells.append({
                "length": length,
                "rotation_raw_fixed": rotation,
                "depth": depth,
                "pixel_format": pixel_format,
                "active_bytes": WIDTH * HEIGHT * pixel_size,
                "input_sha256": INPUT_SHA256[input_key],
                "windows_exported_smart_sha256": windows_sha,
                "mac_public_smart_sha256": smart_sha,
                "mac_public_classic_sha256": classic_sha,
                "routes_exact": True,
                "windows_lifecycle": lifecycle,
            })
    _require(repository_source_records() == source_before,
             "repository source changed during capture")
    _require(_external_file_record("windows_aex", aex_path) == aex_record,
             "AEX changed during capture")
    _require(_external_file_record("aex_guest_worker", worker_path) == worker_record,
             "worker changed during capture")
    _require(aexcompat_source_identity(aexcompat_source) == compat_source_before,
             "AEXCompat checkout changed during capture")
    _verify_external_aexcompat(aexcompat_source, compat_capture)
    report = {
        "schema": SCHEMA,
        "date": DATE,
        "status": STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "fixture": fixture,
        "parameters": parameter_contract(),
        "identities": {
            "windows_aex": aex_record,
            "official_distribution": official_distribution_identity(source_before),
            "aex_guest_worker": worker_record,
            "aexcompat": compat_capture,
            "repository_source": source_before,
            "repository_source_scope": SOURCE_SCOPE,
        },
        "cells": cells,
        "cells_sha256": canonical_sha256(cells),
        "summary": _summary(),
        "scope": dict(SCOPE),
    }
    _verify_report_or_raise(report, external_aex=aex_path,
                            external_worker=worker_path,
                            aexcompat_source=aexcompat_source)
    return report


def _atomic_write(path: Path, payload: bytes) -> None:
    _require(path.parent.is_dir(), f"report parent does not exist: {path.parent}")
    _require(not path.is_symlink(), f"refusing symlink report target: {path}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, allow_abbrev=False,
    )
    parser.add_argument("--capture", action="store_true",
                        help="opt in to the 24-cell live hostless capture")
    parser.add_argument("--aex", type=Path, help="capture-only actual OLMKiraKira.aex")
    parser.add_argument("--worker", type=Path, help="capture-only AEXCompat worker")
    parser.add_argument("--aexcompat-source", type=Path,
                        help="capture-only exact AEXCompat source checkout")
    parser.add_argument("--write-report", type=Path,
                        help="capture-only report destination")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT,
                        help="offline report to verify")
    parser.add_argument("--expected-report-sha256",
                        help=("trusted canonical whole-report SHA-256; required "
                              "with an alternate --report"))
    parser.add_argument("--external-aex", type=Path,
                        help="offline optional AEX identity check")
    parser.add_argument("--external-worker", type=Path,
                        help="offline optional worker identity check")
    parser.add_argument("--external-aexcompat-source", type=Path,
                        help="offline optional AEXCompat checkout check")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    capture_values = (args.aex, args.worker, args.aexcompat_source, args.write_report)
    offline_external = (args.external_aex, args.external_worker,
                        args.external_aexcompat_source)
    if args.capture:
        if any(value is None for value in capture_values):
            parser.error("--capture requires --aex, --worker, --aexcompat-source, and --write-report")
        if args.report != DEFAULT_REPORT or args.expected_report_sha256 is not None \
                or any(value is not None for value in offline_external):
            parser.error("offline verification options cannot be combined with --capture")
        try:
            report = capture_report(args.aex, args.worker, args.aexcompat_source)
            payload = _report_bytes(report)
            _atomic_write(args.write_report, payload)
            _require(_read_report_bytes(args.write_report) == payload,
                     "written report byte mismatch")
        except (OSError, ValueError, TypeError, json.JSONDecodeError,
                subprocess.SubprocessError, VerificationFailure) as error:
            print(f"FAIL: {error}", file=sys.stderr)
            return 1
        print(json.dumps({
            "status": STATUS,
            "cells": len(report["cells"]),
            "cells_sha256": report["cells_sha256"],
            "canonical_report_sha256": canonical_sha256(report),
            "report_file_sha256": hashlib.sha256(payload).hexdigest(),
            "report": str(args.write_report),
        }, sort_keys=True))
        return 0
    if any(value is not None for value in capture_values):
        parser.error("--aex, --worker, --aexcompat-source, and --write-report require --capture")
    try:
        is_default_report = (
            args.report.resolve(strict=False) == DEFAULT_REPORT.resolve(strict=False)
        )
        if is_default_report:
            expected_report_sha256 = _read_default_report_pin()
            if args.expected_report_sha256 is not None:
                _require(args.expected_report_sha256 == expected_report_sha256,
                         "explicit report SHA-256 disagrees with tracked sidecar")
        else:
            _require(args.expected_report_sha256 is not None,
                     "alternate --report requires --expected-report-sha256")
            expected_report_sha256 = args.expected_report_sha256
        raw = _read_report_bytes(args.report)
        report = json.loads(raw)
        _require(raw == _report_bytes(report), "report is not in canonical presentation form")
        _verify_report_or_raise(
            report, expected_report_sha256, args.external_aex,
            args.external_worker, args.external_aexcompat_source,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, VerificationFailure) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "verified",
        "cells": len(report["cells"]),
        "cells_sha256": report["cells_sha256"],
        "canonical_report_sha256": canonical_sha256(report),
        "report_file_sha256": hashlib.sha256(raw).hexdigest(),
        "report": str(args.report),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
