#!/usr/bin/env python3
"""Compare two uncompressed FLOAT RGBA OpenEXR files by semantic channels."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from verify_32bpc_float_return import (
    EXPECTED_CHANNELS,
    VerificationError,
    decode_attrs,
    parse_exr_header,
    validate_scanline_layout,
)


def read_planes(path: Path) -> tuple[dict[str, bytes], int, int]:
    planes, width, height, _ = read_planes_with_layout(path)
    return planes, width, height


def read_planes_with_layout(
    path: Path,
) -> tuple[dict[str, bytes], int, int, dict[str, object]]:
    attrs, header_end = parse_exr_header(path)
    info = decode_attrs(attrs, path)
    channels = info["channels"]
    names = [channel["name"] for channel in channels]
    if set(names) != EXPECTED_CHANNELS or len(names) != 4:
        raise VerificationError(f"{path}: expected exactly RGBA channels, got {names!r}")
    if info["compression"] != 0:
        raise VerificationError(f"{path}: compressed EXR is not accepted by the exact comparator")
    if any(channel["sample_type"] != 2 for channel in channels):
        raise VerificationError(f"{path}: all channels must be FLOAT")
    width, height = info["width"], info["height"]
    min_y, max_y = info["data_window"][1], info["data_window"][3]
    data, chunks, layout = validate_scanline_layout(path, header_end, info)
    planes = {name: bytearray(width * height * 4) for name in names}
    rows: set[int] = set()
    row_size = width * 4
    for offset, _, _ in chunks:
        y, payload_size = struct.unpack_from("<iI", data, offset)
        if y < min_y or y > max_y or y in rows:
            raise VerificationError(f"{path}: invalid scanline y={y}")
        if payload_size != row_size * len(names):
            raise VerificationError(f"{path}: invalid scanline payload size {payload_size}")
        payload = data[offset + 8: offset + 8 + payload_size]
        if len(payload) != payload_size:
            raise VerificationError(f"{path}: truncated scanline y={y}")
        row = y - min_y
        for index, name in enumerate(names):
            start = index * row_size
            planes[name][row * row_size:(row + 1) * row_size] = payload[start:start + row_size]
        rows.add(y)
    if rows != set(range(min_y, max_y + 1)):
        raise VerificationError(f"{path}: incomplete scanline set")
    return {name: bytes(value) for name, value in planes.items()}, width, height, layout


def compare(reference: Path, candidate: Path) -> dict[str, int]:
    ref, ref_w, ref_h, ref_layout = read_planes_with_layout(reference)
    got, got_w, got_h, got_layout = read_planes_with_layout(candidate)
    if (ref_w, ref_h) != (got_w, got_h):
        raise VerificationError(f"dimension mismatch: {ref_w}x{ref_h} vs {got_w}x{got_h}")
    for key in ("data_window", "display_window", "line_order"):
        if ref_layout[key] != got_layout[key]:
            raise VerificationError(f"EXR layout mismatch for {key}")
    mismatched_values = 0
    max_ulp_bits = 0
    for name in sorted(EXPECTED_CHANNELS):
        for offset in range(0, len(ref[name]), 4):
            left = ref[name][offset:offset + 4]
            right = got[name][offset:offset + 4]
            if left != right:
                mismatched_values += 1
                max_ulp_bits = max(max_ulp_bits, abs(struct.unpack("<I", left)[0] - struct.unpack("<I", right)[0]))
    return {"width": ref_w, "height": ref_h, "mismatched_values": mismatched_values, "max_raw_u32_delta": max_ulp_bits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.reference, args.candidate)
    except (OSError, ValueError, struct.error, VerificationError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    print("[OK] float-preserving EXR byte match (not an AE exact claim)" if result["mismatched_values"] == 0 else "[FAIL] float EXR mismatch")
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 0 if result["mismatched_values"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
