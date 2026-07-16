"""Follow the ToonDilate PF16 worker past the context+0x180 boundary.

This is a small, actual-AEX Unicorn witness.  It keeps the host suite model
local to the existing bounded callback fixture, but uses a fresh 2x2 PF16
world for each alpha value so source selection and the four copied words are
observable without claiming AE-host equivalence.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    AEX,
    HELPERS,
    PF_COPY_RESUME,
    alloc,
    context_and_suite,
    raw,
)

ROOT = Path(__file__).resolve().parents[2]
WORKER = 0x1801A5A90
HELPER = HELPERS[16]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_2d_propagation_followup_20260716.md"
JSON_REPORT = REPORT.with_suffix(".json")
WIDTH = HEIGHT = 2
PIXEL_BYTES = 8
ROWBYTES = WIDTH * PIXEL_BYTES
ALPHAS = (0, 1, 16384, 32767, 32768, 32769, 65535)


def make_world_2d(loader: AexLoader, pixels: list[bytes]) -> tuple[int, int]:
    """Build the exact 2x2 PF16 world used by this follow-up."""
    if len(pixels) != WIDTH * HEIGHT or any(len(pixel) != PIXEL_BYTES for pixel in pixels):
        raise ValueError("make_world_2d requires four PF16 pixels in row-major order")
    payload = alloc(loader, b"".join(pixels), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<i", header, 0x20, ROWBYTES)
    struct.pack_into("<i", header, 0x24, WIDTH)
    struct.pack_into("<i", header, 0x28, HEIGHT)
    struct.pack_into("<H", header, 0x2C, PIXEL_BYTES * 8)
    return alloc(loader, bytes(header)), payload


def header_geometry(loader: AexLoader, world: int) -> dict[str, int]:
    return {
        "data": struct.unpack("<Q", loader.read_bytes(world + 0x18, 8))[0],
        "rowbytes": struct.unpack("<i", loader.read_bytes(world + 0x20, 4))[0],
        "width": struct.unpack("<i", loader.read_bytes(world + 0x24, 4))[0],
        "height": struct.unpack("<i", loader.read_bytes(world + 0x28, 4))[0],
        "pixel_bits": struct.unpack("<H", loader.read_bytes(world + 0x2C, 2))[0],
    }


def pf16_words(raw_bytes: list[int]) -> list[int]:
    if len(raw_bytes) != PIXEL_BYTES:
        raise ValueError(f"expected four PF16 words, got {len(raw_bytes)} bytes")
    return list(struct.unpack("<4H", bytes(raw_bytes)))


def model(source: list[list[tuple[int, int, int, int]]]) -> list[list[tuple[int, int, int, int]]]:
    """Minimal independent transcription of RenderTyped<PF_Pixel16> for r=1."""
    output = [[pixel for pixel in row] for row in source]
    inf = 2**32 - 1
    distance = [[inf] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if source[y][x][0] == 32768:
                distance[y][x] = 0

    def relax(x: int, y: int, coords: tuple[tuple[int, int], ...]) -> None:
        if distance[y][x] == 0:
            return
        candidates = [(distance[ny][nx], nx, ny) for nx, ny in coords
                      if 0 <= nx < WIDTH and 0 <= ny < HEIGHT]
        if not candidates:
            return
        best, nx, ny = min(candidates)
        candidate = best + 1
        if best != inf and candidate < distance[y][x]:
            distance[y][x] = candidate
            if candidate <= 1:
                output[y][x] = output[ny][nx]

    for y in range(HEIGHT):
        for x in range(WIDTH):
            relax(x, y, ((x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)))
    for y in range(HEIGHT - 1, -1, -1):
        for x in range(WIDTH - 1, -1, -1):
            relax(x, y, ((x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)))

    result = []
    for row in output:
        cooked = []
        for alpha, red, green, blue in row:
            if alpha not in (0, 32768):
                red = (red * alpha + 16383) // 32768
                green = (green * alpha + 16383) // 32768
                blue = (blue * alpha + 16383) // 32768
            cooked.append((alpha, red, green, blue))
        result.append(cooked)
    return result


def run_case(alpha_a: int) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    seed_a = struct.pack("<4H", alpha_a, 1001, 2002, 3003)
    seed_b = struct.pack("<4H", 32768, 4004, 5005, 6006)
    clear = struct.pack("<4H", 0, 0, 0, 0)
    pixels = [seed_a, clear, clear, seed_b]
    input_world, input_payload = make_world_2d(loader, pixels)
    output_world, output_payload = make_world_2d(loader, pixels)
    input_geometry = header_geometry(loader, input_world)
    output_geometry = header_geometry(loader, output_world)
    worlds = {
        input_world: {"payload": input_payload, "width": WIDTH, "height": HEIGHT,
                      "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        output_world: {"payload": output_payload, "width": WIDTH, "height": HEIGHT,
                       "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
    }
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", 1.0), align=16)
    captures: list[dict] = []
    pending: dict[int, list[dict]] = {}
    return_hooks: set[int] = set()
    resume = {}

    def on_resume(current: AexLoader, _address: int, _size: int) -> None:
        resume.update({
            "address": hex(PF_COPY_RESUME),
            "output_payload": raw(current, output_payload, ROWBYTES * HEIGHT),
        })

    loader.add_code_hook(PF_COPY_RESUME, on_resume)

    def on_return(current: AexLoader, address: int, _size: int) -> None:
        queue = pending.get(address, [])
        if queue:
            item = queue.pop(0)
            item["after_destination"] = raw(current, item["destination_ptr"], PIXEL_BYTES)

    def on_helper(current: AexLoader, _address: int, _size: int) -> None:
        rcx = current.uc.reg_read(UC_X86_REG_RCX)
        rdx = current.uc.reg_read(UC_X86_REG_RDX)
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", current.read_bytes(rsp, 8))[0]
        item = {
            "source_ptr": rcx,
            "destination_ptr": rdx,
            "return_address": hex(ret),
            "source_words_before": pf16_words(raw(current, rcx, PIXEL_BYTES)),
            "destination_words_before": pf16_words(raw(current, rdx, PIXEL_BYTES)),
        }
        for label, ptr in (("source", rcx), ("destination", rdx)):
            for name, base in (("input", input_payload), ("output", output_payload)):
                offset = ptr - base
                if 0 <= offset < ROWBYTES * HEIGHT and offset % PIXEL_BYTES == 0:
                    item[f"{label}_selection"] = {"world": name, "x": (offset % ROWBYTES) // PIXEL_BYTES,
                                                    "y": offset // ROWBYTES}
        captures.append(item)
        pending.setdefault(ret, []).append(item)
        if ret not in return_hooks:
            current.add_code_hook(ret, on_return)
            return_hooks.add(ret)

    loader.add_code_hook(HELPER, on_helper)
    source_model = [
        [(alpha_a, 1001, 2002, 3003), (0, 0, 0, 0)],
        [(0, 0, 0, 0), (32768, 4004, 5005, 6006)],
    ]
    result: dict = {"alpha_a": alpha_a, "status": "BLOCKED"}
    try:
        call = loader.call_function(WORKER, int_args=[context, 0, input_world, output_world, radius],
                                    max_instructions=2_000_000)
        result.update({"status": "RETURN", "return_rax": hex(call["rax"]),
                       "instructions": call["instructions"]})
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    expected = [[list(pixel) for pixel in row] for row in model(source_model)]
    actual = []
    # The resume hook is the host-copy boundary.  Read again after the worker
    # returns so the comparison includes the propagation/copy decision itself.
    output_raw = raw(loader, output_payload, ROWBYTES * HEIGHT)
    for y in range(HEIGHT):
        actual.append([pf16_words(output_raw[y * ROWBYTES + x * PIXEL_BYTES:y * ROWBYTES + (x + 1) * PIXEL_BYTES])
                       for x in range(WIDTH)])
    result.update({
        "next_decision_observed": bool(captures),
        "helper_capture_count": len(captures),
        "captures": captures,
        "copy_resume_observed": resume.get("address") == hex(PF_COPY_RESUME),
        "source_selection_observed": all("source_selection" in item for item in captures),
        "four_pf16_words_captured": all(len(item.get("source_words_before", [])) == 4 for item in captures),
        "expected_render_typed_pf16": expected,
        "actual_output_pf16": actual,
        "render_typed_match": actual == expected if result["status"] == "RETURN" else None,
        "output_layout_valid": len(output_raw) == ROWBYTES * HEIGHT,
        "input_header_geometry": input_geometry,
        "output_header_geometry": output_geometry,
        "header_geometry_valid": all(
            geometry == {"data": payload, "rowbytes": ROWBYTES, "width": WIDTH,
                         "height": HEIGHT, "pixel_bits": PIXEL_BYTES * 8}
            for geometry, payload in ((input_geometry, input_payload),
                                      (output_geometry, output_payload))
        ),
        "worker_boundary_crossed": result["status"] == "RETURN" and bool(captures),
    })
    return result


def main() -> int:
    cases = [run_case(alpha) for alpha in ALPHAS]
    divergences = []
    for case in cases:
        expected = case["expected_render_typed_pf16"]
        actual = case["actual_output_pf16"]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if expected[y][x] != actual[y][x]:
                    divergences.append({"alpha_a": case["alpha_a"], "x": x, "y": y,
                                        "expected_words": expected[y][x], "actual_words": actual[y][x]})
                    break
            if divergences and divergences[-1]["alpha_a"] == case["alpha_a"]:
                break
    gates = {
        "all_returned": all(case["status"] == "RETURN" for case in cases),
        "all_crossed_boundary": all(case["worker_boundary_crossed"] for case in cases),
        "decision_observed": any(case["next_decision_observed"] for case in cases),
        "source_selection_and_four_words": all(
            (not case["next_decision_observed"])
            or (case["source_selection_observed"] and case["four_pf16_words_captured"])
            for case in cases
        ),
        "render_typed_matches": all(case["render_typed_match"] is True for case in cases),
        "output_layout_valid": all(case["output_layout_valid"] for case in cases),
        "header_geometry_valid": all(case["header_geometry_valid"] for case in cases),
    }
    status = "PASS_2D_PROPAGATION_CLASSIFIED" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    payload = {
        "status": status,
        "aex": str(AEX.relative_to(ROOT)),
        "worker": hex(WORKER),
        "known_boundary": "0x1801adc8f",
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES, "radius": 1.0,
                    "alpha_sweep": list(ALPHAS), "seed_layout": "A at (0,0), B at (1,1)"},
        "gates": gates,
        "first_divergence": divergences[0] if divergences else None,
        "cases": cases,
        "facts": [
            "The actual-AEX worker is invoked locally through Unicorn on macOS.",
            "A helper capture records the selected source pointer, destination pointer, and four PF16 words before copy.",
            "The post-boundary result is classified only when the worker returns and the copy decision is observable.",
        ],
        "inferences": [
            "The synthetic suite and PF_COPY callbacks approximate the observed host ABI; they are not AE-host behavior.",
            "RenderTyped<PF_Pixel16> comparison is a source-level semantic comparison, not an AE-exact claim.",
        ],
        "claim_boundary": "bounded actual-AEX 2D propagation/copy witness; no production or AE-exact claim",
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OLMToonDilate PF16 2D Propagation Follow-up - 2026-07-16", "", "## Result", "",
        f"- Status: **{status}**", "- Execution: checked-in Windows PE AEX under local Unicorn on macOS.",
        "- Fixture: 2x2 PF16, radius 1, distinct diagonal seeds, and an alpha sweep.",
        "- The harness fails closed if the post-`0x1801adc8f` decision is not crossed and observed.",
        "- The header geometry gate requires both worlds to read width=2, height=2, rowbytes=16, and PF16 (64 bits).",
        f"- First semantic divergence (when blocked): `{json.dumps(payload['first_divergence'])}`",
        "- No AE-exact or production-fix claim is made.", "", "## FACT", "",
        "- The harness records the next helper propagation/copy decision, source selection coordinates, and four PF16 words.",
        "- The expected side is an independent transcription of the checked-in `RenderTyped<PF_Pixel16>` alpha threshold, two-pass relaxation, and half-up premultiplication.",
        f"- Gates: `{json.dumps(gates, sort_keys=True)}`", "", "## INFERENCE", "",
        "- The host suite/PF_COPY behavior is synthetic and bounded to the observed callback ABI.",
        "- A passing comparison supports this fixture only; it does not establish AE-host equivalence.", "", "## Cases", "",
        f"- Alpha sweep: `{list(ALPHAS)}`", f"- Case summaries: `{json.dumps([{k: c.get(k) for k in ('alpha_a', 'status', 'helper_capture_count', 'next_decision_observed', 'render_typed_match', 'captures')} for c in cases])}`", "",
        "## Reproduce", "", "```sh",
        "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf16_2d_propagation_followup_20260716.py",
        "```", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if status == "PASS_2D_PROPAGATION_CLASSIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
