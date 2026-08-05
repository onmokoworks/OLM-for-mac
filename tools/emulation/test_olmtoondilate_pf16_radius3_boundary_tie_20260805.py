#!/usr/bin/env python3
"""Independent actual-AEX PF16 radius-3 boundary/tie fixture."""

from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import AEX, alloc, context_and_suite, raw  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_radius3_boundary_tie_20260805.json"
MARKDOWN = REPORT.with_suffix(".md")
AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
WORKER, WIDTH, HEIGHT, ROWBYTES, RADIUS = 0x1801A5A90, 7, 3, 60, 3
PIXEL_BYTES, PAD = 8, 0xA5
A = (32768, 1001, 2002, 3003)
B = (32768, 4004, 5005, 6006)
CLEAR = (0, 17, 19, 23)


def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def make_world(loader: AexLoader) -> tuple[int, int]:
    buf = bytearray([PAD] * (ROWBYTES * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = A if (x, y) == (0, 1) else B if (x, y) == (6, 1) else CLEAR
            struct.pack_into("<4H", buf, y * ROWBYTES + x * PIXEL_BYTES, *p)
    data = alloc(loader, bytes(buf), align=64)
    header = bytearray(0x30)
    struct.pack_into("<QiiiH", header, 0x18, data, ROWBYTES, WIDTH, HEIGHT, 64)
    return alloc(loader, bytes(header)), data


def visible(world: bytes) -> bytes:
    return b"".join(world[y * ROWBYTES:y * ROWBYTES + WIDTH * PIXEL_BYTES] for y in range(HEIGHT))


def expected() -> bytes:
    # Independent PF16 fixture oracle. The split is checked against actual PF16
    # execution, not imported from the PF8 report.
    splits = (3, 4, 4)
    result = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH): result.extend(struct.pack("<4H", *(A if x < splits[y] else B)))
    return bytes(result)


def main() -> int:
    if digest(AEX) != AEX_SHA256: raise SystemExit("BLOCKED_FAIL_CLOSED: AEX identity drifted")
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    input_world, input_data = make_world(loader); output_world, output_data = make_world(loader)
    worlds = {
        input_world: {"payload": input_data, "width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        output_world: {"payload": output_data, "width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
    }
    events: list[dict] = []; context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", float(RADIUS)), align=16)
    call = loader.call_function(WORKER, int_args=[context, 0, input_world, output_world, radius], max_instructions=5_000_000)
    world = bytes(raw(loader, output_data, ROWBYTES * HEIGHT)); actual = visible(world); oracle = expected()
    words = lambda offset: list(struct.unpack("<4H", actual[offset:offset + 8]))
    center = words((WIDTH + 3) * 8); top_tie = words(3 * 8)
    gates = {
        "aex_sha256_exact": digest(AEX) == AEX_SHA256,
        "worker_returned": True,
        "full_visible_four_word_exact": actual == oracle,
        "middle_tie_prefers_left_seed": center == list(A),
        "top_tie_prefers_right_seed": top_tie == list(B),
        "padding_preserved": all(world[y * ROWBYTES + WIDTH * 8:(y + 1) * ROWBYTES] == bytes([PAD] * 4) for y in range(HEIGHT)),
    }
    status = "PASS_PF16_RADIUS3_BOUNDARY_TIE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    rows = [[words((y * WIDTH + x) * 8) for x in range(WIDTH)] for y in range(HEIGHT)]
    payload = {
        "status": status, "schema": "olmtoondilate.pf16-radius3-boundary-tie/1",
        "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256, "worker": hex(WORKER),
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES, "radius": RADIUS,
                    "left_seed": [0, 1], "right_seed": [6, 1], "left_words": list(A), "right_words": list(B), "padding_byte": PAD},
        "execution": {"instructions": call["instructions"], "return_rax": hex(call["rax"])},
        "gates": gates, "actual_rows_words": rows,
        "actual_visible_sha256": hashlib.sha256(actual).hexdigest(), "expected_visible_sha256": hashlib.sha256(oracle).hexdigest(),
        "claim_boundary": "independent bounded actual-AEX PF16 radius-3 boundary/tie fixture; no PF8 or AE-host inference",
    }
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        f"# OLMToonDilate PF16 Radius-3 Boundary Tie — 2026-08-05\n\n- Status: **{status}**\n"
        "- Independently executes the PF16 AEX worker; it does not consume the PF8 fixture.\n"
        f"- Top tie selects right: `{gates['top_tie_prefers_right_seed']}`; middle tie selects left: `{gates['middle_tie_prefers_left_seed']}`.\n"
        f"- Full visible PF16 four-word exact: `{gates['full_visible_four_word_exact']}`.\n- Bounded worker evidence only; no AE-host claim.\n",
        encoding="utf-8")
    print(json.dumps(payload, indent=2)); return 0 if status.startswith("PASS") else 1


if __name__ == "__main__": raise SystemExit(main())
