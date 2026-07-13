#!/usr/bin/env python3
"""Fail-closed comparator for AE 26.3 FLOAT EXR acceptance packages.

The package deliberately compares four artifacts in stages:

    Windows no-effect -> Mac no-effect                   (host parity)
    Mac no-effect control -> Mac effect output       (Mac plugin delta)
    Windows effect output -> Mac effect output       (cross-host conformance)

The first delta must not be attributed to the plugin. An effect-on result is
not accepted as attributable unless the no-effect control and loaded AEX hash
are both bound in the same case record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_32bpc_float_return import (  # noqa: E402
    EXPECTED_CHANNELS,
    VerificationError,
    decode_attrs,
    parse_exr_header,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise VerificationError(f"{label}: missing valid SHA-256")
    return value.lower()


def artifact_path(case: dict[str, Any], key: str, root: Path) -> tuple[Path, str]:
    item = case.get(key)
    if not isinstance(item, dict):
        raise VerificationError(f"{case.get('id')}: missing {key} artifact binding")
    value = item.get("path")
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{case.get('id')}.{key}: missing path")
    path = Path(value)
    if path.is_absolute():
        raise VerificationError(f"{case.get('id')}.{key}: absolute paths are not allowed in package metadata")
    path = (root / path).resolve()
    if not path.is_file():
        raise VerificationError(f"{case.get('id')}.{key}: artifact not found: {value}")
    stated = require_sha(item.get("sha256"), f"{case.get('id')}.{key}")
    actual = sha256(path)
    if actual != stated:
        raise VerificationError(f"{case.get('id')}.{key}: SHA-256 mismatch")
    return path, actual


def read_float_rgba(path: Path, expected_dimensions: tuple[int, int]) -> tuple[dict[str, Any], dict[str, list[int]]]:
    raw, header_end = parse_exr_header(path)
    info = decode_attrs(raw, path)
    channels = info["channels"]
    names = [channel["name"] for channel in channels]
    if set(names) != EXPECTED_CHANNELS or len(names) != 4:
        raise VerificationError(f"{path}: expected exactly A/B/G/R FLOAT channels, got {names!r}")
    if any(channel["sample_type"] != 2 for channel in channels):
        raise VerificationError(f"{path}: HALF/non-FLOAT channel rejected")
    if info["compression"] != 0:
        raise VerificationError(f"{path}: compressed EXR rejected; expected uncompressed scanlines")
    dimensions = (info["width"], info["height"])
    if dimensions != expected_dimensions:
        raise VerificationError(f"{path}: dimensions {dimensions!r} do not match {expected_dimensions!r}")
    data = path.read_bytes()
    width, height = dimensions
    table_end = header_end + height * 8
    if table_end > len(data):
        raise VerificationError(f"{path}: truncated scanline offset table")
    offsets = struct.unpack_from("<" + "Q" * height, data, header_end)
    rows: dict[int, tuple[int, ...]] = {}
    seen: set[int] = set()
    min_y, max_y = info["data_window"][1], info["data_window"][3]
    row_size = width * len(names) * 4
    for offset in offsets:
        if offset < table_end or offset + 8 > len(data):
            raise VerificationError(f"{path}: invalid scanline chunk offset {offset}")
        y, size = struct.unpack_from("<iI", data, offset)
        if y < min_y or y > max_y or y in seen:
            raise VerificationError(f"{path}: invalid or duplicate scanline y={y}")
        payload = data[offset + 8 : offset + 8 + size]
        if len(payload) != size or size != row_size:
            raise VerificationError(f"{path}: invalid scanline payload size {size}, expected {row_size}")
        seen.add(y)
        rows[y] = struct.unpack("<" + "I" * (size // 4), payload)
    if seen != set(range(min_y, max_y + 1)):
        raise VerificationError(f"{path}: incomplete/misaligned scanline image")
    values: dict[str, list[int]] = {name: [] for name in names}
    for y in range(min_y, max_y + 1):
        row = rows[y]
        for index, name in enumerate(names):
            values[name].extend(row[index::len(names)])
    return {"path": path.name, "dimensions": list(dimensions), "physical_channels": names}, values


def diff(left: dict[str, list[int]], right: dict[str, list[int]]) -> dict[str, Any]:
    mismatches = 0
    max_u32_delta = 0
    nonfinite = 0
    for name in sorted(EXPECTED_CHANNELS):
        for a, b in zip(left[name], right[name]):
            if a != b:
                mismatches += 1
                max_u32_delta = max(max_u32_delta, abs(a - b))
            if math.isnan(struct.unpack("<f", struct.pack("<I", a))[0]) or math.isnan(struct.unpack("<f", struct.pack("<I", b))[0]):
                nonfinite += 1
    return {"mismatched_samples": mismatches, "max_raw_u32_delta": max_u32_delta, "nonfinite_samples_involved": nonfinite}


def verify(package_path: Path, artifact_root: Path) -> dict[str, Any]:
    package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    if not isinstance(package, dict) or package.get("kind") != "ae26_3_float_exr_acceptance_package":
        raise VerificationError("unexpected package kind")
    if package.get("ae_version") != "26.3":
        raise VerificationError("package must declare AE 26.3")
    if package.get("bit_depth") != "32bpc" or package.get("bits_per_channel") != 32:
        raise VerificationError("package must declare 32bpc/32")
    if not isinstance(package.get("linear_light"), bool):
        raise VerificationError("package must explicitly declare linear_light")
    if package["linear_light"] is not False:
        raise VerificationError("package linear_light must be false for OLM EXR 32 Float")
    for platform, expected_os in (("windows_host", "windows"), ("mac_host", "macos")):
        host = package.get(platform)
        if not isinstance(host, dict) or host.get("os") != expected_os:
            raise VerificationError(f"package must bind {platform}.os={expected_os}")
        if host.get("renderer") != "SOFTWARE":
            raise VerificationError(f"{platform}.renderer must be SOFTWARE")
        if not isinstance(host.get("ae_build"), str) or not host["ae_build"]:
            raise VerificationError(f"{platform}.ae_build is required")
    cases = package.get("cases")
    if not isinstance(cases, list) or not cases:
        raise VerificationError("package has no cases")
    results = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise VerificationError("case must have an id")
        dimensions = case.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) != 2 or not all(isinstance(v, int) and v > 0 for v in dimensions):
            raise VerificationError(f"{case['id']}: invalid dimensions")
        expected_dimensions = (dimensions[0], dimensions[1])
        if case.get("linear_light") is not package["linear_light"]:
            raise VerificationError(f"{case['id']}: linear_light disagrees with package")
        require_sha(case.get("case_contract_sha256"), f"{case['id']}.case_contract_sha256")
        for control_key in ("windows_no_effect_control", "mac_no_effect_control"):
            no_effect = case.get(control_key)
            if not isinstance(no_effect, dict) or no_effect.get("effect_enabled") is not False:
                raise VerificationError(f"{case['id']}: {control_key} must explicitly set effect_enabled=false")
        windows_binding = case.get("windows_aex_binding")
        if not isinstance(windows_binding, dict):
            raise VerificationError(f"{case['id']}: missing Windows AEX binding")
        expected_aex = require_sha(windows_binding.get("sha256"), f"{case['id']}.windows_aex_binding")
        mac_binding = case.get("mac_plugin_binding")
        if not isinstance(mac_binding, dict):
            raise VerificationError(f"{case['id']}: missing Mac plugin binding")
        expected_mac_plugin = require_sha(mac_binding.get("sha256"), f"{case['id']}.mac_plugin_binding")
        windows_effect_metadata = case.get("windows_effect_output")
        if not isinstance(windows_effect_metadata, dict):
            raise VerificationError(f"{case['id']}: missing windows_effect_output artifact binding")
        loaded_aex = require_sha(windows_effect_metadata.get("loaded_aex_sha256"), f"{case['id']}.windows_effect_output.loaded_aex_sha256")
        if loaded_aex != expected_aex:
            raise VerificationError(f"{case['id']}: loaded Windows AEX hash does not match binding")
        mac_effect_metadata = case.get("mac_effect_output")
        if not isinstance(mac_effect_metadata, dict):
            raise VerificationError(f"{case['id']}: missing mac_effect_output artifact binding")
        loaded_mac_plugin = require_sha(mac_effect_metadata.get("loaded_plugin_sha256"), f"{case['id']}.mac_effect_output.loaded_plugin_sha256")
        if loaded_mac_plugin != expected_mac_plugin:
            raise VerificationError(f"{case['id']}: loaded Mac plugin hash does not match binding")
        source_path, source_hash = artifact_path(case, "source_input", artifact_root)
        windows_control_path, windows_control_hash = artifact_path(case, "windows_no_effect_control", artifact_root)
        mac_control_path, mac_control_hash = artifact_path(case, "mac_no_effect_control", artifact_root)
        windows_effect_path, windows_effect_hash = artifact_path(case, "windows_effect_output", artifact_root)
        mac_effect_path, mac_effect_hash = artifact_path(case, "mac_effect_output", artifact_root)
        source_info, source = read_float_rgba(source_path, expected_dimensions)
        windows_control_info, windows_control = read_float_rgba(windows_control_path, expected_dimensions)
        mac_control_info, mac_control = read_float_rgba(mac_control_path, expected_dimensions)
        windows_effect_info, windows_effect = read_float_rgba(windows_effect_path, expected_dimensions)
        mac_effect_info, mac_effect = read_float_rgba(mac_effect_path, expected_dimensions)
        windows_input_delta = diff(source, windows_control)
        host_delta = diff(windows_control, mac_control)
        mac_plugin_delta = diff(mac_control, mac_effect)
        cross_host_delta = diff(windows_effect, mac_effect)
        host_exact = host_delta["mismatched_samples"] == 0
        cross_host_exact = cross_host_delta["mismatched_samples"] == 0
        results.append({
            "id": case["id"], "plugin": case.get("plugin"), "dimensions": dimensions,
            "linear_light": package["linear_light"], "source_input": {"sha256": source_hash, **source_info},
            "windows_no_effect_control": {"sha256": windows_control_hash, **windows_control_info, "effect_enabled": False},
            "mac_no_effect_control": {"sha256": mac_control_hash, **mac_control_info, "effect_enabled": False},
            "windows_effect_output": {"sha256": windows_effect_hash, **windows_effect_info, "loaded_aex_sha256": loaded_aex},
            "mac_effect_output": {"sha256": mac_effect_hash, **mac_effect_info, "loaded_plugin_sha256": loaded_mac_plugin},
            "windows_input_conversion": windows_input_delta,
            "host_input_conversion": host_delta,
            "mac_effect_delta": mac_plugin_delta,
            "cross_host_effect_output": cross_host_delta,
            "attribution": "eligible" if host_exact else "blocked-by-host-input-conversion",
            "cross_host_status": "raw-float-bits-exact" if host_exact and cross_host_exact else "not-exact-or-not-attributable",
        })
    return {"status": "pass", "ae_version": "26.3", "bit_depth": "32bpc", "linear_light": package["linear_light"], "cases": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--artifact-root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-exact", action="store_true", help="fail if host parity or cross-host effect output is not raw-bit exact")
    args = parser.parse_args()
    try:
        result = verify(args.package, args.artifact_root)
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    if args.require_exact and any(case["cross_host_status"] != "raw-float-bits-exact" for case in result["cases"]):
        print("[FAIL] one or more cases are not attributable raw-float-bit exact", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for case in result["cases"]:
            print(f"[PASS] {case['id']}: host_input_conversion={case['host_input_conversion']['mismatched_samples']} cross_host_effect_output={case['cross_host_effect_output']['mismatched_samples']} status={case['cross_host_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
