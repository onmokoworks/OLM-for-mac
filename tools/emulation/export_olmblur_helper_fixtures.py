"""Export small, actual-AEX helper fixtures for the portable OLMBlur core."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_case0006 import (  # noqa: E402
    AEX_PATH,
    FUN_OLMBLUR_NONLEGACY_HORIZONTAL,
    FUN_OLMBLUR_NONLEGACY_VERTICAL,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools/emulation/fixtures/olmblur_helper"

CASES = [
    ("basic", "horizontal", 5, 1, 1, 0, 2, [1, 1, 1, 1, 1]),
    ("inactive_copy", "horizontal", 3, 1, 1, 0, 1, [1, 0, 1]),
    ("direction_break", "horizontal", 5, 1, 1, 0, 2, [1, 1, 0, 1, 1]),
    ("edge_radius_clamp", "horizontal", 2, 1, 1, 0, 4, [1, 1]),
    ("zero_denominator", "horizontal", 3, 1, 1, 0, 1, [1, 1, 1]),
    ("nonzero_offset", "vertical", 3, 5, 2, 1, 2, [1] * 15),
]


def blob_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call_case(direction: str, width: int, height: int, passes: int,
              offset: int, radius: int, flags: list[int]) -> tuple[bytes, bytes, bytes]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    pixels = width * height
    src_values = [float(10 + i * 3 + channel) for i in range(pixels) for channel in range(3)]
    if direction == "vertical":
        # A row/column-sensitive pattern makes stride and offset visible.
        src_values = [float(100 * y + 10 * x + channel) for y in range(height)
                      for x in range(width) for channel in range(3)]
    weights = [0.0] * (radius + 1)
    if radius == 0:
        weights[0] = 1.0
    elif direction == "horizontal" and width == 3 and radius == 1:
        weights[:] = [0.0, 0.0] if "zero" in direction else [1.0, 2.0]
    else:
        weights[:] = [1.0, 2.0] + [1.0] * max(0, radius - 1)
    if direction == "horizontal" and width == 3 and radius == 1 and flags == [1, 1, 1]:
        weights[:] = [0.0, 0.0]

    def alloc(data: bytes, align: int = 16) -> int:
        address = loader.bump_alloc(len(data), align=align)
        loader.write_bytes(address, data)
        return address

    flags_blob = bytes(flags)
    src_blob = struct.pack("<%df" % len(src_values), *src_values)
    dst_blob = bytes(pixels * 3 * 4)
    weights_blob = struct.pack("<%df" % len(weights), *weights)
    flags_ptr = alloc(flags_blob)
    src_ptr = alloc(src_blob)
    dst_ptr = alloc(dst_blob)
    weights_ptr = alloc(weights_blob)
    function = FUN_OLMBLUR_NONLEGACY_HORIZONTAL if direction == "horizontal" else FUN_OLMBLUR_NONLEGACY_VERTICAL
    loader.call_function(function, int_args=[flags_ptr, src_ptr, dst_ptr, weights_ptr,
                                              width, height, passes, offset, radius],
                         max_instructions=200_000)
    return flags_blob, src_blob, weights_blob, loader.read_bytes(dst_ptr, len(dst_blob))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "olm.aex.cpu-fixture/1", "scope": "function",
                "plugin": "OLMBlur", "binary_sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(),
                "claim": "Actual AEX helper fixture only; not full-entry or AE exact.", "cases": []}
    for name, direction, width, height, passes, offset, radius, flags in CASES:
        flags_blob, src_blob, weights_blob, expected_blob = call_case(
            direction, width, height, passes, offset, radius, flags)
        case_dir = OUT / name
        case_dir.mkdir(exist_ok=True)
        blobs = {"flags": flags_blob, "src": src_blob, "weights": weights_blob, "expected": expected_blob}
        files = {}
        for label, data in blobs.items():
            path = case_dir / f"{label}.bin"
            path.write_bytes(data)
            files[label] = {"path": path.relative_to(OUT).as_posix(), "bytes": len(data), "sha256": blob_sha(path)}
        manifest["cases"].append({"id": name, "direction": direction,
            "width": width, "height": height, "passes": passes, "offset": offset,
            "radius": radius, "flags": flags, "files": files})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[OK] exported {len(CASES)} actual-AEX OLMBlur helper fixtures: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
