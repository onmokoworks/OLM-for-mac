#!/usr/bin/env python3
"""Bounded PF8 radius-2 shape witness using the checked-in actual AEX."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    AEX, alloc, context_and_suite, raw,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_radius2_shape_20260805.json"
MARKDOWN = REPORT.with_suffix(".md")
WORKER = 0x1801A6150
HELPER = 0x1801AC880
AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
WIDTH, HEIGHT, PIXEL_BYTES, ROWBYTES = 5, 3, 4, 24
RADIUS, PAD = 2, 0xA5
SEED = (255, 10, 20, 30)
CLEAR = (0, 101, 202, 77)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_world(loader: AexLoader) -> tuple[int, int]:
    payload = bytearray([PAD] * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixel = SEED if (x, y) == (2, 1) else CLEAR
            struct.pack_into("<4B", payload, y * ROWBYTES + x * PIXEL_BYTES, *pixel)
    data = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<QiiiH", header, 0x18, data, ROWBYTES, WIDTH, HEIGHT, 32)
    return alloc(loader, bytes(header)), data


def expected() -> bytes:
    output = bytearray([PAD] * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pixel = SEED if max(abs(x - 2), abs(y - 1)) <= RADIUS else CLEAR
            struct.pack_into("<4B", output, y * ROWBYTES + x * PIXEL_BYTES, *pixel)
    return bytes(output)


def visible(world: bytes) -> bytes:
    return b"".join(world[y * ROWBYTES:y * ROWBYTES + WIDTH * PIXEL_BYTES]
                    for y in range(HEIGHT))


def padding(world: bytes) -> bytes:
    return b"".join(world[y * ROWBYTES + WIDTH * PIXEL_BYTES:(y + 1) * ROWBYTES]
                    for y in range(HEIGHT))


def main() -> int:
    if sha256(AEX) != AEX_SHA256:
        raise SystemExit("BLOCKED_FAIL_CLOSED: OLMToonDilate AEX identity drifted")
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
    copies: list[dict] = []

    def helper(current: AexLoader, _address: int, _size: int) -> None:
        source = current.uc.reg_read(UC_X86_REG_RCX)
        destination = current.uc.reg_read(UC_X86_REG_RDX)
        copies.append({
            "source_argb": list(current.read_bytes(source, PIXEL_BYTES)),
            "destination_argb": list(current.read_bytes(destination, PIXEL_BYTES)),
        })

    loader.add_code_hook(HELPER, helper)
    result = loader.call_function(
        WORKER, int_args=[context, 0, input_world, output_world, radius],
        max_instructions=4_000_000,
    )
    actual = bytes(raw(loader, output_data, ROWBYTES * HEIGHT))
    oracle = expected()
    input_raw = bytes(raw(loader, input_data, ROWBYTES * HEIGHT))
    gates = {
        "aex_sha256_exact": sha256(AEX) == AEX_SHA256,
        "worker_returned": True,
        "copy_helper_observed": len(copies) > 0,
        "full_visible_argb_exact": visible(actual) == visible(oracle),
        "output_padding_preserved": padding(actual) == bytes([PAD] * 12),
        "non_noop": visible(actual) != visible(input_raw),
    }
    status = "PASS_PF8_RADIUS2_SHAPE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    payload = {
        "status": status,
        "schema": "olmtoondilate.pf8-radius2-shape/1",
        "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256,
        "worker": hex(WORKER),
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
                    "radius": RADIUS, "seed": [2, 1], "seed_argb": list(SEED),
                    "clear_argb": list(CLEAR), "padding_byte": PAD},
        "execution": {"instructions": result["instructions"], "return_rax": hex(result["rax"]),
                      "copy_helper_hits": len(copies)},
        "gates": gates,
        "actual_visible_sha256": hashlib.sha256(visible(actual)).hexdigest(),
        "expected_visible_sha256": hashlib.sha256(visible(oracle)).hexdigest(),
        "claim_boundary": "bounded actual-AEX PF8 radius-2 worker fixture under local Unicorn; no AE-host claim",
    }
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        "# OLMToonDilate PF8 Radius-2 Shape — 2026-08-05\n\n"
        f"- Status: **{status}**\n"
        "- Checked-in Windows AEX executed under local Unicorn on macOS.\n"
        "- Fixture: padded `5x3` PF8 world, center opaque seed, Search Radius `2`.\n"
        f"- Full visible ARGB exact: `{gates['full_visible_argb_exact']}`.\n"
        f"- Padding preserved: `{gates['output_padding_preserved']}`.\n"
        "- This is a bounded worker/fixture result, not AE-host exactness.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
