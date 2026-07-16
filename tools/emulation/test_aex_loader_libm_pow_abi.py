#!/usr/bin/env python3
"""Regression for Windows x64 pow/powf XMM ABI through actual AEX thunks."""

from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
POW = 0x18000CCBA
POWF = 0x18000CCC0


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def main() -> int:
    if hashlib.sha256(AEX.read_bytes()).hexdigest() != AEX_SHA256:
        raise AssertionError("OLMBlur.aex hash differs from pinned ABI witness")
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    base_f = f32(3.0 / f32(125.599998474121))
    exponent_f = f32(1.0 / 3.0)
    powf_result = loader.call_function(
        POWF,
        float_args={0: (base_f, "f"), 1: (exponent_f, "f")},
        max_instructions=32,
    )
    expected_powf = f32(math.pow(base_f, exponent_f))
    if powf_result["xmm0_f32"] != expected_powf or [call.name for call in loader.import_log] != ["powf"]:
        raise AssertionError(f"powf XMM ABI differs: {powf_result['xmm0_f32']!r}")

    base_d = float(expected_powf)
    exponent_d = 2.0
    pow_result = loader.call_function(
        POW,
        float_args={0: (base_d, "d"), 1: (exponent_d, "d")},
        max_instructions=32,
    )
    expected_pow = math.pow(base_d, exponent_d)
    if pow_result["xmm0_f64"] != expected_pow or [call.name for call in loader.import_log] != ["pow"]:
        raise AssertionError(f"pow XMM ABI differs: {pow_result['xmm0_f64']!r}")

    print("[OK] AexLoader powf(float,float) and pow(double,double) XMM ABI")
    print(f"powf={powf_result['xmm0_f32']!r} pow={pow_result['xmm0_f64']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
