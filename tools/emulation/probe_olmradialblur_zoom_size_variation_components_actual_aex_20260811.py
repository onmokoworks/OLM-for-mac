#!/usr/bin/env python3
"""Actual-AEX Zoom Size Variation probe with separated alpha components.

Read-only with respect to the shared RadialBlur implementation.  The 32x18
source has three four-connected opaque islands of area 1, 4, and 9 on a fully
transparent background, which makes the Size Variation prepass observable.
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

VALUES = (0.0, 25.0, 100.0)
CELLS = [(depth, value) for depth in (8, 16, 32) for value in VALUES]
REPORT = ROOT / "refs/conformance/olmradialblur_zoom_size_variation_components_actual_aex_20260811.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def component_frame_for(depth: int, mode: str, w: int, h: int, rb: int):
    assert mode == "zoom" and (w, h) == (32, 18)
    original = ORIGINAL_FRAME_FOR(depth, mode, w, h, rb)
    # Three separated four-connected components, with areas 1, 4, and 9.
    live = {(2, 2)}
    live.update((x, y) for y in range(3, 5) for x in range(9, 11))
    live.update((x, y) for y in range(10, 13) for x in range(20, 23))
    pixel_bytes = {8: 4, 16: 8, 32: 16}[depth]

    def frame(seed: bool = False) -> bytes:
        raw = bytearray(original(seed))
        if seed:
            return bytes(raw)
        for y in range(h):
            for x in range(w):
                if (x, y) not in live:
                    raw[y * rb + x * pixel_bytes:y * rb + (x + 1) * pixel_bytes] = bytes(pixel_bytes)
        return bytes(raw)

    return frame


ORIGINAL_FRAME_FOR = base.frame_for


def configure(depth: int, size: float):
    base.frame_for = component_frame_for
    try:
        target, frame, rb, _cx, _cy = base.configure(("zoom", depth, 32, 18, 0.0, 0.0, 1.0))
    finally:
        base.frame_for = ORIGINAL_FRAME_FOR
    module = target.fixture.m4
    original_install = module.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params["Size Variation"] = size
        return original_install(loader, params)

    module.install_reader_detours = install
    return target, frame, rb


def capture(cell):
    return configure(*cell)[0].actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_zoom_size_components_") as raw:
        result = Path(raw) / "actual.pkl"
        subprocess.run([sys.executable, __file__, "--capture", str(cell[0]), str(cell[1]), str(result)], check=True)
        return pickle.loads(result.read_bytes())


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actual = dict(zip(CELLS, pool.map(isolated, CELLS)))

    rows = []
    for depth in (8, 16, 32):
        control = actual[(depth, 0.0)]
        for size in (25.0, 100.0):
            got = actual[(depth, size)]
            changed = {name: got[name] != control[name] for name in ("pre_blur", "post_blur", "output")}
            rows.append({
                "depth": depth,
                "size_variation": size,
                "differs_from_size0": changed,
                "actual_sha256": {name: sha(got[name]) for name in ("pre_blur", "post_blur", "output")},
                "size0_sha256": {name: sha(control[name]) for name in ("pre_blur", "post_blur", "output")},
            })
            print(depth, size, changed, flush=True)

    # Size Variation is consumed after polar sampling: pre-blur must be stable,
    # while the post-blur plane and typed output must both react.
    assert all(not row["differs_from_size0"]["pre_blur"] and
               row["differs_from_size0"]["post_blur"] and
               row["differs_from_size0"]["output"] for row in rows), rows
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_zoom_size_variation_components_actual_aex_20260811",
        "status": "6/6 actual-AEX Zoom post-sampling consumers distinguish nonzero Size Variation",
        "scope": "Pinned actual AEX; Zoom 32x18 centered Outer4/Inner0 neutral tuple; PF8/PF16/PF32; Size Variation 25/100 against Size0; transparent background with separated four-connected opaque component areas 1,4,9.",
        "fixture": {
            "connectivity": "four-connected",
            "component_areas": [1, 4, 9],
            "transparent_pixel_count": 562,
            "source_generator": str(Path(__file__).relative_to(ROOT)),
        },
        "compared": ["pre_blur_float32_plane", "post_blur_float32_plane", "typed_padded_output"],
        "ordering_witness": "For all six typed/value cells, pre_blur is byte-identical to Size0 while post_blur and output differ. Size Variation is therefore consumed after initial polar sampling and before/during the strength collapse.",
        "cases": rows,
        "boundary": "This probe establishes that the Zoom consumer receives and uses the nontrivial Size Variation prepass. It does not by itself expose the owner source-size-factor/source-span arrays or prove the current Mac implementation exact.",
    }, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--capture":
        Path(sys.argv[4]).write_bytes(pickle.dumps(capture((int(sys.argv[2]), float(sys.argv[3])))))
        raise SystemExit(0)
    raise SystemExit(main())
