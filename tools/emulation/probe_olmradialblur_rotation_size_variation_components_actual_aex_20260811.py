#!/usr/bin/env python3
"""Actual-AEX witness for Rotation Size Variation on disconnected alpha islands.

This deliberately does not exercise the production admission gate.  It records the
owner's component prepass and its Rotation consumer for a transparent 32x18 source.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

VALUES = (1.0, 25.0, 100.0)
CELLS = [(depth, value) for depth in (8, 16, 32) for value in VALUES]
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_size_variation_components_actual_aex_20260811.json"


def component_frame(depth: int, rb: int) -> bytes:
    """Three disconnected opaque components (areas 9, 4, 1) on transparent black."""
    w, h = 32, 18
    pb = {8: 4, 16: 8, 32: 16}[depth]
    raw = bytearray(rb * h)
    points = ({(x, y) for y in range(2, 5) for x in range(2, 5)} |
              {(x, y) for y in range(9, 11) for x in range(13, 15)} |
              {(27, 14)})
    for y in range(h):
        for x in range(w):
            off = y * rb + x * pb
            if (x, y) not in points:
                continue
            if depth == 8:
                struct.pack_into("<4B", raw, off, 255, (x * 31 + y * 7) & 255,
                                 (x * 11 + y * 29) & 255, (x * 47 + y * 13) & 255)
            elif depth == 16:
                struct.pack_into("<4H", raw, off, 32768,
                                 (x * 4093 + y * 257) % 32769,
                                 (x * 1237 + y * 3559) % 32769,
                                 (x * 7919 + y * 911) % 32769)
            else:
                struct.pack_into("<4f", raw, off, 1.0,
                                 ((x * 4093 + y * 257) % 32769) / 32768.0,
                                 ((x * 1237 + y * 3559) % 32769) / 32768.0,
                                 ((x * 7919 + y * 911) % 32769) / 32768.0)
        raw[y * rb + w * pb:(y + 1) * rb] = bytes([(0xA0 + y) & 255]) * (rb - w * pb)
    return bytes(raw)


def configure(depth: int, value: float):
    target, _, rb, _, _ = base.configure(("rotation", depth, 32, 18, 0.0, 0.0, 1.0))
    fixture = target.base if depth == 32 else target
    frame = component_frame(depth, rb)
    fixture.source_frame = lambda seed=False: frame
    if depth == 32:
        target.source_frame = lambda seed=False: frame
    fixture.FIXTURE_SIZE_VARIATION = value
    fixture.CAPTURE_NOISE_INTERNALS = True
    if depth == 32:
        target.SIZE_VARIATION = value
    return target, frame


def capture(cell):
    return configure(*cell)[0].actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_rotation_sv_components_") as raw:
        out = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", str(cell[0]),
                        str(cell[1]), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def production(cell, expected):
    depth, value = cell
    synthetic = ("rotation", depth, 32, 18, 0.0, 0.0, 1.0)
    original_configure = base.configure
    original_write_text = Path.write_text

    def configure_component(requested):
        target, _, rb, cx, cy = original_configure(requested)
        frame = component_frame(depth, rb)
        fixture = target.base if depth == 32 else target
        fixture.source_frame = lambda seed=False: frame
        if depth == 32:
            target.source_frame = lambda seed=False: frame
        return target, (lambda seed=False: frame), rb, cx, cy

    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            needle = "i.noise_type=1;i.seed=1;i.thickness=10;"
            if needle not in data:
                raise RuntimeError("info marker absent")
            data = data.replace(needle, f"i.size_variation={value};" + needle, 1)
        return original_write_text(path, data, *args, **kwargs)

    base.configure = configure_component
    Path.write_text = write_text
    try:
        return base.production(synthetic, expected)
    finally:
        base.configure = original_configure
        Path.write_text = original_write_text


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def float_summary(raw: bytes):
    values = struct.unpack(f"<{len(raw)//4}f", raw)
    unique = sorted(set(values))
    return {"count": len(values), "min": min(values), "max": max(values),
            "unique_count": len(unique), "unique": unique[:32]}


def difference_summary(actual: bytes, production: bytes):
    offsets = [i for i, (a, b) in enumerate(zip(actual, production)) if a != b]
    return {"byte_count": len(offsets), "first_byte_offset": offsets[0] if offsets else None}


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    for depth, value in CELLS:
        got = captures[(depth, value)]
        prod = production((depth, value), got)
        required = ("size_factor", "polar", "source_scalar", "accum", "max_alpha",
                    "final_rgba", "coordinates", "output")
        missing = [name for name in required if name not in got]
        if missing:
            raise AssertionError((depth, value, missing, sorted(got)))
        row = {
            "depth": depth,
            "size_variation": value,
            "size_factor": float_summary(got["size_factor"]),
            "source_span": float_summary(got["source_span"]) if "source_span" in got else None,
            "sha256": {name: sha(got[name]) for name in (*required, "source_span") if name in got},
            "production_matches_actual": {
                name: prod[name] == got[name]
                for name in ("polar", "source_scalar", "accum", "max_alpha",
                             "final_rgba", "coordinates", "output")
            },
        }
        row["production_differences"] = {
            name: difference_summary(got[name], prod[name])
            for name, exact in row["production_matches_actual"].items() if not exact
        }
        rows.append(row)
        print(depth, value, row["size_factor"], row["source_span"], flush=True)
    cross_depth = {}
    for value in VALUES:
        selected = [row for row in rows if row["size_variation"] == value]
        consumer_hashes = {row["sha256"]["size_factor"] for row in selected}
        span_hashes = {row["sha256"]["source_span"] for row in selected
                       if "source_span" in row["sha256"]}
        assert len(consumer_hashes) == 1, (value, consumer_hashes)
        assert len(span_hashes) == 1, (value, span_hashes)
        cross_depth[str(value)] = {
            "rotation_consumer_size_factor_identical_pf8_pf16_pf32": True,
            "source_span_identical_pf16_pf32": True,
            "pf8_source_span_capture": "unavailable in the PF8 fixture; consumer plane is captured",
        }
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_size_variation_components_actual_aex_20260811",
        "status": "shared-direct exact" if all(all(row["production_matches_actual"].values()) for row in rows) else "shared-direct mismatch",
        "scope": "Rotation, centered 32x18, PF8/PF16/PF32, Size Variation 1/25/100; transparent black with disconnected opaque 3x3, 2x2 and 1x1 components; neutral Outer4/Inner0 tuple.",
        "boundary": "Production admission is limited to this 32x18 alpha-mask fixture, neutral Rotation tuple, PF8/PF16/PF32, and Size Variation 1/25/100. Right-edge/final-row components, NaN/Inf alpha, other masks, geometry, modes, and parameter interactions remain fail-closed.",
        "fixture_sha256": {str(depth): sha(configure(depth, 1.0)[1]) for depth in (8, 16, 32)},
        "cross_depth": cross_depth,
        "cases": rows,
    }, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--capture":
        Path(sys.argv[4]).write_bytes(pickle.dumps(capture((int(sys.argv[2]), float(sys.argv[3])))))
        raise SystemExit(0)
    raise SystemExit(main())
