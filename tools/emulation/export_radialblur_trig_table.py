#!/usr/bin/env python3
"""Export FUN_18001d060's paired float trig results for the Zoom angle grid."""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
from pathlib import Path

from aex_loader import AexLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = REPO_ROOT / "plugins_2025" / "OLMRadialBlur.aex"
FUN_PAIRED_TRIG = 0x18001D060
MAGIC = b"OLMTRIG1"
VERSION = 1


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aex-path", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--quality", type=float, default=5.0)
    parser.add_argument("--angular-count", type=int, default=1800)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.quality <= 0.0 or args.angular_count <= 0:
        raise SystemExit("--quality and --angular-count must be positive")

    step_rad = f32((1.0 / args.quality) * math.pi / 180.0)
    payload = bytearray()
    loader = AexLoader(str(args.aex_path), verbose=False, fast=True)
    for angle_index in range(args.angular_count):
        theta = f32(float(angle_index) * step_rad)
        result = loader.call_function(
            FUN_PAIRED_TRIG,
            float_args={0: (theta, "f")},
            max_instructions=1_000,
        )
        sin_value, cos_value = struct.unpack("<2f", result["xmm0"][:8])
        payload.extend(struct.pack("<2f", sin_value, cos_value))

    header = MAGIC + struct.pack(
        "<III", VERSION, args.angular_count, struct.unpack("<I", struct.pack("<f", step_rad))[0]
    )
    digest = hashlib.sha256(header + payload).digest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(header + payload + digest)
    print(f"output={args.output}")
    print(f"aex={args.aex_path}")
    print(f"angular_count={args.angular_count}")
    print(f"step_rad_f32={step_rad:.10g}")
    print(f"payload_bytes={len(payload)}")
    print(f"sha256={digest.hex()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
