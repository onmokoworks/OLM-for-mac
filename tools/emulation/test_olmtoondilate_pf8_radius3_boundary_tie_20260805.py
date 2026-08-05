#!/usr/bin/env python3
"""Actual-AEX PF8 radius-3 boundary/tie fixture under local Unicorn."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    AEX, alloc, context_and_suite, raw,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_radius3_boundary_tie_20260805.json"
MARKDOWN = REPORT.with_suffix(".md")
AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
WORKER, WIDTH, HEIGHT, ROWBYTES, RADIUS = 0x1801A6150, 7, 3, 32, 3
PIXEL_BYTES, PAD = 4, 0xA5
A, B, CLEAR = (255, 10, 20, 30), (255, 90, 80, 70), (0, 3, 5, 7)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_world(loader: AexLoader) -> tuple[int, int]:
    payload = bytearray([PAD] * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixel = A if (x, y) == (0, 1) else B if (x, y) == (6, 1) else CLEAR
            struct.pack_into("<4B", payload, y * ROWBYTES + x * 4, *pixel)
    data = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<QiiiH", header, 0x18, data, ROWBYTES, WIDTH, HEIGHT, 32)
    return alloc(loader, bytes(header)), data


def expected_visible() -> bytes:
    result = bytearray()
    # Two-pass scan order makes the top-row equal-distance frontier choose the
    # right seed at x=3, while the middle/bottom frontier chooses the left.
    split_by_row = (3, 4, 4)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            result.extend(A if x < split_by_row[y] else B)
    return bytes(result)


def visible(world: bytes) -> bytes:
    return b"".join(world[y * ROWBYTES:y * ROWBYTES + WIDTH * 4] for y in range(HEIGHT))


def main() -> int:
    if sha(AEX) != AEX_SHA256:
        raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    input_world, input_data = make_world(loader)
    output_world, output_data = make_world(loader)
    worlds = {
        input_world: {"payload": input_data, "width": WIDTH, "height": HEIGHT,
                      "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        output_world: {"payload": output_data, "width": WIDTH, "height": HEIGHT,
                       "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
    }
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", float(RADIUS)), align=16)
    result = loader.call_function(WORKER, int_args=[context, 0, input_world, output_world, radius],
                                  max_instructions=5_000_000)
    actual_world = bytes(raw(loader, output_data, ROWBYTES * HEIGHT))
    actual = visible(actual_world)
    expected = expected_visible()
    center = list(actual[(1 * WIDTH + 3) * 4:(1 * WIDTH + 4) * 4])
    gates = {
        "aex_sha256_exact": sha(AEX) == AEX_SHA256,
        "worker_returned": True,
        "full_visible_argb_exact": actual == expected,
        "center_tie_prefers_left_seed": center == list(A),
        "both_boundary_seeds_preserved": actual[WIDTH * 4:WIDTH * 4 + 4] == bytes(A)
        and actual[(WIDTH + 6) * 4:(WIDTH + 7) * 4] == bytes(B),
        "padding_preserved": all(
            actual_world[y * ROWBYTES + WIDTH * 4:(y + 1) * ROWBYTES] == bytes([PAD] * 4)
            for y in range(HEIGHT)
        ),
    }
    status = "PASS_PF8_RADIUS3_BOUNDARY_TIE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    payload = {
        "status": status, "schema": "olmtoondilate.pf8-radius3-boundary-tie/1",
        "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256, "worker": hex(WORKER),
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
                    "radius": RADIUS, "left_seed": [0, 1], "right_seed": [6, 1],
                    "left_argb": list(A), "right_argb": list(B), "padding_byte": PAD},
        "execution": {"instructions": result["instructions"], "return_rax": hex(result["rax"])},
        "gates": gates, "center_tie_actual_argb": center,
        "actual_rows_argb": [[list(actual[(y * WIDTH + x) * 4:(y * WIDTH + x + 1) * 4])
                              for x in range(WIDTH)] for y in range(HEIGHT)],
        "actual_visible_sha256": hashlib.sha256(actual).hexdigest(),
        "expected_visible_sha256": hashlib.sha256(expected).hexdigest(),
        "claim_boundary": "bounded actual-AEX PF8 radius-3 boundary/tie fixture under local Unicorn; no AE-host claim",
    }
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        "# OLMToonDilate PF8 Radius-3 Boundary Tie — 2026-08-05\n\n"
        f"- Status: **{status}**\n- Padded `7x3` PF8 world with distinct seeds on both horizontal boundaries.\n"
        f"- Center equal-distance tie selects the left seed: `{gates['center_tie_prefers_left_seed']}`.\n"
        f"- Full visible ARGB exact: `{gates['full_visible_argb_exact']}`.\n"
        "- Bounded actual-AEX worker evidence only; no AE-host claim.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
