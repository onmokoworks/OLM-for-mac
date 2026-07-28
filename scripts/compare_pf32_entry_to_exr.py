#!/usr/bin/env python3
"""Compare an interleaved PF_PixelFloat ARGB buffer with a FLOAT RGBA EXR."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

from compare_float_exr import read_planes_with_layout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_raw(path: Path, expected_size: int) -> bytes:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rb") as stream:
            data = stream.read(expected_size + 1)
    else:
        data = path.read_bytes()
    if len(data) != expected_size:
        raise ValueError(f"raw size {len(data)} != expected {expected_size}")
    return data


def compare_pf32_entry(raw_path: Path, exr_path: Path) -> dict[str, object]:
    planes, width, height, layout = read_planes_with_layout(exr_path)
    expected_size = width * height * 4 * 4
    if layout["data_window"] != [0, 0, width - 1, height - 1]:
        raise ValueError("PF32 comparison requires dataWindow origin 0")
    if layout["display_window"] != layout["data_window"]:
        raise ValueError("PF32 comparison requires full identical display/data windows")
    raw_bytes = read_raw(raw_path, expected_size)

    channel_order = ("A", "R", "G", "B")
    raw_words = np.frombuffer(raw_bytes, dtype="<u4").reshape(height, width, 4)
    exr_words = np.stack(
        [
            np.frombuffer(planes[name], dtype="<u4").reshape(height, width)
            for name in channel_order
        ],
        axis=2,
    )
    mismatch = raw_words != exr_words
    mismatch_count = int(np.count_nonzero(mismatch))
    if mismatch_count:
        left = raw_words[mismatch].astype(np.int64)
        right = exr_words[mismatch].astype(np.int64)
        max_raw_u32_delta = int(np.max(np.abs(left - right)))
    else:
        max_raw_u32_delta = 0

    first = []
    for y, x, channel in np.argwhere(mismatch)[:16]:
        left_word = int(raw_words[y, x, channel])
        right_word = int(exr_words[y, x, channel])
        first.append(
            {
                "x": int(x),
                "y": int(y),
                "channel": channel_order[int(channel)],
                "raw_u32": f"0x{left_word:08x}",
                "exr_u32": f"0x{right_word:08x}",
                "raw_float": struct.unpack("<f", struct.pack("<I", left_word))[0],
                "exr_float": struct.unpack("<f", struct.pack("<I", right_word))[0],
            }
        )

    return {
        "status": (
            "raw_float32_exact"
            if mismatch_count == 0
            else "raw_float32_mismatch"
        ),
        "width": width,
        "height": height,
        "rowbytes": width * 16,
        "channel_order": list(channel_order),
        "word_count": width * height * 4,
        "mismatched_words": mismatch_count,
        "max_raw_u32_delta": max_raw_u32_delta,
        "raw": {
            "path": str(raw_path),
            "stored_size": raw_path.stat().st_size,
            "stored_sha256": sha256_file(raw_path),
            "uncompressed_size": len(raw_bytes),
            "uncompressed_sha256": sha256_bytes(raw_bytes),
        },
        "exr": {
            "path": str(exr_path),
            "sha256": sha256_file(exr_path),
        },
        "first_mismatches": first,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("exr", type=Path)
    args = parser.parse_args()
    try:
        result = compare_pf32_entry(args.raw, args.exr)
    except (OSError, ValueError, struct.error) as exc:
        print(f"[FAIL] {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["mismatched_words"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
