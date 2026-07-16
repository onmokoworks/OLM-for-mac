"""PF32 seed-propagation matrix against the checked-in actual AEX worker.

The oracle is intentionally independent: an 8-neighbor breadth-first copy of
the seed's four raw float32 words, with no production implementation reuse.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    AEX,
    HELPERS,
    WORKERS,
    alloc,
    context_and_suite,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf32_seed_propagation_matrix_20260717.md"
JSON_REPORT = REPORT.with_suffix(".json")
WORKER = WORKERS[32]
HELPER = HELPERS[32]
WIDTH = HEIGHT = 5
PIXEL_BYTES = 16
ROWBYTES = WIDTH * PIXEL_BYTES + 4
PADDING = b"\xA5" * 4
CENTER = (2, 2)
DIRECTIONS = {
    "left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1),
    "up_left": (-1, -1), "up_right": (1, -1),
    "down_left": (-1, 1), "down_right": (1, 1),
}
ALPHAS = (0.499, 0.5, 0.501)
RADII = (1.0, 2.0)


def pixel(alpha: float, index: int) -> bytes:
    # A,R,G,B; distinct finite words make accidental channel/word conversion visible.
    return struct.pack("<4f", alpha, 0.125 + index / 64.0,
                       0.25 + index / 128.0, 0.375 + index / 256.0)


def make_world(loader: AexLoader, pixels: list[bytes]) -> tuple[int, int]:
    payload = bytearray(ROWBYTES * HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            offset = y * ROWBYTES + x * PIXEL_BYTES
            payload[offset:offset + PIXEL_BYTES] = pixels[y * WIDTH + x]
        payload[y * ROWBYTES + WIDTH * PIXEL_BYTES:(y + 1) * ROWBYTES] = PADDING
    payload_ptr = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload_ptr)
    struct.pack_into("<i", header, 0x20, ROWBYTES)
    struct.pack_into("<i", header, 0x24, WIDTH)
    struct.pack_into("<i", header, 0x28, HEIGHT)
    struct.pack_into("<H", header, 0x2C, 128)
    return alloc(loader, bytes(header)), payload_ptr


def raw_pixels(payload: bytes) -> list[list[int]]:
    return [list(payload[y * ROWBYTES + x * PIXEL_BYTES:y * ROWBYTES + (x + 1) * PIXEL_BYTES])
            for y in range(HEIGHT) for x in range(WIDTH)]


def oracle(source: list[bytes], seed: tuple[int, int], radius: int) -> list[list[int]]:
    """Independent raw-copy oracle: bounded 8-neighbor BFS, exact word copy."""
    distances = {seed: 0}
    queue = deque([seed])
    while queue:
        x, y = queue.popleft()
        if distances[(x, y)] == radius:
            continue
        for dx, dy in DIRECTIONS.values():
            point = (x + dx, y + dy)
            if 0 <= point[0] < WIDTH and 0 <= point[1] < HEIGHT and point not in distances:
                distances[point] = distances[(x, y)] + 1
                queue.append(point)
    result = [list(value) for value in source]
    seed_words = list(source[seed[1] * WIDTH + seed[0]])
    for x, y in distances:
        result[y * WIDTH + x] = seed_words[:]
    return result


def run_case(direction: str, alpha: float, radius: float) -> dict[str, object]:
    dx, dy = DIRECTIONS[direction]
    seed = (CENTER[0] + dx, CENTER[1] + dy)
    seed_index = seed[1] * WIDTH + seed[0]
    source = [pixel(alpha, index) for index in range(WIDTH * HEIGHT)]
    source[seed_index] = pixel(1.0, 900 + seed_index)
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    input_world, input_payload = make_world(loader, source)
    output_world, output_payload = make_world(loader, [b"\0" * PIXEL_BYTES] * (WIDTH * HEIGHT))
    worlds = {
        input_world: {"payload": input_payload, "width": WIDTH, "height": HEIGHT,
                      "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        output_world: {"payload": output_payload, "width": WIDTH, "height": HEIGHT,
                       "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
    }
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius_ptr = alloc(loader, struct.pack("<f", radius), align=16)
    helper_hits: list[dict] = []

    def on_helper(current: AexLoader, _address: int, _size: int) -> None:
        from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX
        source_ptr = current.uc.reg_read(UC_X86_REG_RCX)
        destination_ptr = current.uc.reg_read(UC_X86_REG_RDX)
        helper_hits.append({"source": hex(source_ptr), "destination": hex(destination_ptr),
                            "source_raw": list(current.read_bytes(source_ptr, PIXEL_BYTES)),
                            "destination_raw": list(current.read_bytes(destination_ptr, PIXEL_BYTES))})

    loader.add_code_hook(HELPER, on_helper)
    try:
        call = loader.call_function(WORKER, int_args=[context, 0, input_world, output_world, radius_ptr],
                                    max_instructions=2_000_000)
        output_raw = bytes(loader.read_bytes(output_payload, ROWBYTES * HEIGHT))
        actual = raw_pixels(output_raw)
        expected = oracle(source, seed, int(radius))
        actual_bytes = b"".join(bytes(words) for words in actual)
        expected_bytes = b"".join(bytes(words) for words in expected)
        return {
            "status": "RETURN", "direction": direction, "seed": list(seed),
            "alpha": alpha, "radius": radius, "worker_return_rax": hex(call["rax"]),
            "worker_instructions": call["instructions"],
            "helper_hit_count": len(helper_hits),
            "actual_visible_sha256": hashlib.sha256(actual_bytes).hexdigest(),
            "oracle_visible_sha256": hashlib.sha256(expected_bytes).hexdigest(),
            "visible_byte_diff_count": sum(a != b for a, b in zip(actual_bytes, expected_bytes)),
            "visible_exact_4_word": actual == expected,
            "padding_preserved": all(output_raw[y * ROWBYTES + WIDTH * PIXEL_BYTES:(y + 1) * ROWBYTES] == PADDING
                                      for y in range(HEIGHT)),
        }
    except Exception as exc:
        return {"status": "BLOCKED_FAIL_CLOSED", "direction": direction, "seed": list(seed),
                "alpha": alpha, "radius": radius, "error": f"{type(exc).__name__}: {exc}",
                "helper_hit_count": len(helper_hits)}


def main() -> int:
    cases = [run_case(direction, alpha, radius)
             for direction in DIRECTIONS for alpha in ALPHAS for radius in RADII]
    gates = {
        "aex_present": AEX.exists(),
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest() if AEX.exists() else None,
        "case_count_48": len(cases) == 48,
        "all_workers_returned": all(case.get("status") == "RETURN" for case in cases),
        "all_helpers_observed": all(case.get("helper_hit_count", 0) > 0 for case in cases),
        "all_visible_4_word_exact": all(case.get("visible_exact_4_word") is True for case in cases),
        "all_row_padding_preserved": all(case.get("padding_preserved") is True for case in cases),
    }
    payload = {
        "status": "PASS_PF32_SEED_PROPAGATION_MATRIX" if all(gates.values()) else "BLOCKED_FAIL_CLOSED",
        "schema": "olmtoondilate.pf32-seed-propagation-matrix/1",
        "aex": str(AEX.relative_to(ROOT)), "worker": hex(WORKER), "helper": hex(HELPER),
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES, "pixel_bits": 128,
                    "directions": list(DIRECTIONS), "alphas": list(ALPHAS), "radii": list(RADII),
                    "layout": "one opaque seed at each center-adjacent direction; every other pixel has paired semi-alpha raw words"},
        "oracle": "independent 8-neighbor BFS; copy the seed's raw four float32 words to every point at graph distance <= radius",
        "gates": gates, "cases": cases,
        "claim_boundary": "bounded Mac-local actual-AEX/Unicorn PF32 worker versus independent raw-copy oracle; no AE exact, Windows exact, host-conversion, or production claim",
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# OLMToonDilate PF32 Seed Propagation Matrix - 2026-07-17", "", "## Result", "",
             f"- Status: **{payload['status']}**", f"- AEX: `{payload['aex']}`",
             f"- Worker/helper: `{payload['worker']}` / `{payload['helper']}`",
             "- Scope: 48 independent actual-worker runs: 8 directions x 3 alpha values x 2 radii.",
             "- Execution: checked-in AEX under local Unicorn; output read immediately after worker return.", "",
             "## FACT", "", "- Seed directions cover left, right, up, down, and all four diagonals.",
             "- Semi-alpha values are 0.499, 0.5, and 0.501; radii are 1 and 2.",
             "- The independent oracle copies raw PF32 A,R,G,B words through an 8-neighbor BFS.",
             "- Every case requires exact visible 4-word equality and all four bytes of every row padding sentinel.",
             f"- Gates: `{json.dumps(gates, sort_keys=True)}`", "",
             "## Boundary", "", "- This report is bounded Mac-local binary/Unicorn evidence only.",
             "- It makes no After Effects exactness or Windows exactness claim.",
             "- It does not modify production code or the existing witness.", "",
             "## Reproduce", "", "```sh",
             "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf32_seed_propagation_matrix_20260717.py",
             "```", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "case_count": len(cases), "gates": gates}, sort_keys=True))
    return 0 if payload["status"] == "PASS_PF32_SEED_PROPAGATION_MATRIX" else 1


if __name__ == "__main__":
    raise SystemExit(main())
