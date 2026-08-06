#!/usr/bin/env python3
"""Prepare an AE-observable PF16 extended-range ColorKeep fixture.

This fixture intentionally contains only active pixels and public RGB color
parameters.  The separate installed-public fixture remains authoritative for
host-world row padding and synthetic ColorParam alpha values.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle  # noqa: E402

OUT = ROOT / "refs/mac_validation_fixtures/colorkeep_pf16_extended_host_20260806"
REPORT = ROOT / "refs/conformance/colorkeep_pf16_extended_host_fixture_actual_aex_20260806.json"
ENTRY = 0x180001280
ROWBYTES = 40

# ARGB.  Every key has alpha 1.0, matching AE's public RGB Color Control.
COLORS = (
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 0.25, 0.75, 1.0),
    (1.0, 0.0, 0.0, 0.0),
)

PIXELS = (
    (32768, 32768, 32768, 32768),
    (32768, 8192, 24576, 32768),
    (32768, 0, 0, 0),
    (32768, 32769, 32768, 32768),
    (32768, 32768, 32769, 32768),
    (32768, 32768, 32768, 32769),
    (32768, 65535, 65535, 65535),
    (32769, 32768, 32768, 32768),
    (65535, 8192, 24576, 32768),
    (16384, 65535, 32769, 49152),
    (1, 32769, 1, 65535),
    (32768, 12345, 23456, 34567),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_exr(path: Path, pixels: tuple[tuple[int, int, int, int], ...]) -> None:
    try:
        import Imath
        import OpenEXR
    except ImportError as exc:
        raise SystemExit("OpenEXR Python bindings are required to prepare this fixture") from exc
    if len(pixels) not in (12, 16):
        raise ValueError("expected a 4x3 or 4x4 pixel array")
    height = len(pixels) // 4
    header = OpenEXR.Header(4, height)
    header["compression"] = Imath.Compression(Imath.Compression.NO_COMPRESSION)
    channel = Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))
    header["channels"] = {name: channel for name in "ABGR"}
    arrays = {}
    for index, name in enumerate("ARGB"):
        arrays[name] = np.asarray([p[index] / 32768.0 for p in pixels], dtype=np.float32).tobytes()
    output = OpenEXR.OutputFile(str(path), header)
    output.writePixels({name: arrays[name] for name in "ABGR"})
    output.close()


def active(raw: bytes) -> bytes:
    return b"".join(raw[y * ROWBYTES:y * ROWBYTES + 32] for y in range(3))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    oracle.COLORS = COLORS
    expected_padded = oracle.actual_frame(ENTRY, "<4H", PIXELS)
    expected = active(expected_padded)
    expected_pixels = tuple(struct.unpack_from("<4H", expected, i * 8) for i in range(12))
    input_exr = OUT / "input_pf16_units_as_float.exr"
    expected_exr = OUT / "expected_actual_aex_pf16_units_as_float.exr"
    expected_raw = OUT / "expected_actual_aex_active.argb16"
    host_tail = ((0, 0, 0, 0),) * 4
    write_exr(input_exr, PIXELS + host_tail)
    write_exr(expected_exr, expected_pixels + host_tail)
    expected_raw.write_bytes(expected)
    report = {
        "schema": "colorkeep.pf16-extended-host-fixture/1",
        "status": "prepared_actual_aex_active_pixels",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "actual_worker_entry": f"0x{ENTRY:x}",
        "active_dimensions": [4, 3],
        "host_dimensions": [4, 4],
        "pf16_nominal_white": 32768,
        "keys_public_rgb": [[c[1], c[2], c[3]] for c in COLORS],
        "keys_alpha": [c[0] for c in COLORS],
        "input_argb16": [list(p) for p in PIXELS],
        "expected_argb16": [list(p) for p in expected_pixels],
        "artifacts": {p.name: {"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in (input_exr, expected_exr, expected_raw)},
        "claim_boundary": "Only 12 active PF16 pixels and public RGB keys. Row padding and synthetic ColorParam alpha remain exclusively covered by colorkeep_installed_public_pf16_render_20260805.json.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
