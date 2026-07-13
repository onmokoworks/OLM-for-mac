#!/usr/bin/env python3
"""Validate and sample the actual case0026 AE-exported RGBA16 PNG."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CASE_ID = "olmdistancegradation_extended__case_0026"
WITNESS_ID = "olmdistancegradation-case0026-16bpc-livefield-v1"
WIDTH = 1920
HEIGHT = 1080
POINTS = ((907, 222), (395, 477), (1589, 579), (898, 670))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def fail(request_id: str, reason: str, missing: list[str], last: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "exact_bind_failure",
        "request_id": request_id,
        "failure": {
            "stage": "export_png_validation",
            "reason": reason,
            "missing_fields": sorted(set(missing)),
            "last_observation": last,
        },
    }


def paeth(a: int, b: int, c: int) -> int:
    estimate = a + b - c
    da, db, dc = abs(estimate - a), abs(estimate - b), abs(estimate - c)
    return a if da <= db and da <= dc else b if db <= dc else c


def inspect_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG")

    offset = 8
    ihdr: tuple[int, int, int, int, int, int, int] | None = None
    compressed: list[bytes] = []
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk body")
        body = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != expected_crc:
            raise ValueError(f"bad {kind.decode('ascii', errors='replace')} CRC")
        if kind == b"IHDR":
            if ihdr is not None or length != 13:
                raise ValueError("invalid IHDR")
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            compressed.append(body)
        elif kind == b"IEND":
            if length != 0:
                raise ValueError("invalid IEND")
            saw_iend = True
            if end != len(data):
                raise ValueError("bytes after IEND")
            break
        offset = end

    if ihdr is None or not compressed or not saw_iend:
        raise ValueError("PNG lacks IHDR, IDAT, or IEND")
    width, height, depth, color, compression, filtering, interlace = ihdr
    if (width, height) != (WIDTH, HEIGHT):
        raise ValueError(f"wrong dimensions: {width}x{height}")
    if depth != 16:
        raise ValueError(f"wrong bit depth: {depth}")
    if color != 6:
        raise ValueError(f"wrong color type: {color}; RGBA is required")
    if (compression, filtering, interlace) != (0, 0, 0):
        raise ValueError("unsupported PNG compression/filter/interlace method")

    channels = 4
    bytes_per_pixel = channels * 2
    stride = width * bytes_per_pixel
    raw = zlib.decompress(b"".join(compressed))
    expected_size = height * (stride + 1)
    if len(raw) != expected_size:
        raise ValueError(f"wrong decompressed size: {len(raw)} expected {expected_size}")

    wanted_by_y: dict[int, list[int]] = {}
    for x, y in POINTS:
        wanted_by_y.setdefault(y, []).append(x)
    samples: dict[tuple[int, int], list[int]] = {}
    previous = bytearray(stride)
    cursor = 0
    for y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        if filter_type > 4:
            raise ValueError(f"invalid row filter {filter_type} at y={y}")
        source = raw[cursor : cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for index, value in enumerate(source):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            predictor = (
                0
                if filter_type == 0
                else left
                if filter_type == 1
                else above
                if filter_type == 2
                else (left + above) // 2
                if filter_type == 3
                else paeth(left, above, upper_left)
            )
            row[index] = (value + predictor) & 0xFF
        for x in wanted_by_y.get(y, []):
            start = x * bytes_per_pixel
            samples[(x, y)] = list(struct.unpack(">HHHH", row[start : start + bytes_per_pixel]))
        previous = row

    return {
        "width": width,
        "height": height,
        "bit_depth": depth,
        "color_type": color,
        "channel_layout": "RGBA",
        "interlace": interlace,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "witnesses": [
            {"xy": [x, y], "rgba16": samples[(x, y)]}
            for x, y in POINTS
        ],
    }


def bind_export(
    contract: dict[str, Any],
    status: dict[str, Any],
    identity: dict[str, Any],
    ae_result: dict[str, Any],
    png_path: Path,
) -> dict[str, Any]:
    request_id = contract["request_id"]
    if status.get("status") != "answered":
        return status

    missing: list[str] = []
    run = status.get("run", {})
    expected_identity = {
        "run_id": str(identity.get("run_id", "")),
        "ae_pid": int(identity.get("ae_pid", -1)),
        "module_base": str(identity.get("module_base", "")).lower(),
        "aex_sha256": str(contract["plugin"]["aex_sha256"]).lower(),
        "project_bits_per_channel": int(contract["project"]["bits_per_channel"]),
        "renderer": str(contract["project"]["renderer"]),
    }
    for field, expected in expected_identity.items():
        actual = run.get(field)
        if field in ("module_base", "aex_sha256"):
            actual = str(actual).lower()
        if actual != expected:
            missing.append(f"return_identity:{field}")

    expected_path = str(png_path.resolve()).casefold()
    result_path = str(Path(str(ae_result.get("output_png", ""))).resolve()).casefold()
    checks = {
        "ae_result:status": ae_result.get("status") == "ok",
        "ae_result:case_id": ae_result.get("case_id") == CASE_ID,
        "ae_result:witness_id": ae_result.get("witness_id") == WITNESS_ID,
        "ae_result:witness_run_id": ae_result.get("witness_run_id") == expected_identity["run_id"],
        "ae_result:project_bits_per_channel": ae_result.get("project_bits_per_channel") == 16,
        "ae_result:output_png": result_path == expected_path,
    }
    missing.extend(label for label, passed in checks.items() if not passed)
    if not png_path.is_file():
        missing.append("exported_png:file")
    if missing:
        return fail(request_id, "export path or same-run AE identity did not bind", missing, json.dumps(ae_result, sort_keys=True))

    try:
        inspected = inspect_png(png_path)
    except (OSError, ValueError, struct.error, zlib.error) as exc:
        return fail(request_id, "actual AE export is not a valid 1920x1080 RGBA16 PNG", ["exported_png:rgba16"], str(exc))

    witness_identity = {
        "run_id": expected_identity["run_id"],
        "ae_pid": expected_identity["ae_pid"],
        "module_base": expected_identity["module_base"],
        "aex_sha256": expected_identity["aex_sha256"],
        "project_bits_per_channel": 16,
        "renderer": expected_identity["renderer"],
        "case_id": CASE_ID,
        "witness_id": WITNESS_ID,
    }
    status["exported_png"] = {
        **witness_identity,
        "archive_path": "return/actual_case_0026.png",
        "png_sha256": inspected["sha256"],
        "png_size_bytes": inspected["size_bytes"],
        "width": inspected["width"],
        "height": inspected["height"],
        "bit_depth": inspected["bit_depth"],
        "color_type": inspected["color_type"],
        "channel_layout": inspected["channel_layout"],
        "witnesses": [
            {**witness_identity, **sample}
            for sample in inspected["witnesses"]
        ],
    }
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--ae-result", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = bind_export(
            read_json(args.contract),
            read_json(args.status),
            read_json(args.identity),
            read_json(args.ae_result),
            args.input,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        request_id = "unknown"
        try:
            request_id = read_json(args.contract).get("request_id", "unknown")
        except Exception:
            pass
        result = fail(request_id, "export witness inputs are missing or malformed", ["export_witness_inputs"], str(exc))
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "answered" else 2


if __name__ == "__main__":
    sys.exit(main())
