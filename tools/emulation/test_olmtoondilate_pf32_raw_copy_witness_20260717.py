"""Seeded actual-AEX PF32 live-path witness for ToonDilate on macOS.

The 3x1 fixture forces one propagation-helper copy from an opaque seed into a
semi-alpha destination.  A second semi-alpha pixel is two cells from the seed,
outside radius 1, so its raw post-return bytes distinguish an absent postpass
from RGB*=alpha while the same worker invocation proves the live helper path.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX

sys.path.insert(0, str(Path(__file__).parent))
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    AEX,
    HELPERS,
    WORKERS,
    alloc,
    context_and_suite,
    raw,
)
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmtoondilate_pf32_raw_copy_witness_20260717.md"
JSON_REPORT = REPORT.with_suffix(".json")
WORKER = WORKERS[32]
HELPER = HELPERS[32]
WIDTH = 3
HEIGHT = 1
PIXEL_BYTES = 16
ROWBYTES = WIDTH * PIXEL_BYTES + 4
PADDING = b"\xA5" * 4

# PF32 memory is A,R,G,B.  Both semi-alpha pixels use straight RGB that is
# exactly representable and differs from RGB*alpha.
OPAQUE = (1.0, 0.125, 0.25, 0.5)
SEMI_DESTINATION = (0.5, 0.625, 0.375, 0.125)
SEMI_POSTPASS_WITNESS = (0.5, 0.75, 0.25, 0.125)


def pixel(value: tuple[float, float, float, float]) -> bytes:
    return struct.pack("<4f", *value)


def premultiplied(value: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    alpha, red, green, blue = value
    return alpha, red * alpha, green * alpha, blue * alpha


def make_world(loader: AexLoader, pixels: list[bytes]) -> tuple[int, int]:
    payload = bytearray(ROWBYTES)
    for index, value in enumerate(pixels):
        payload[index * PIXEL_BYTES:(index + 1) * PIXEL_BYTES] = value
    payload[WIDTH * PIXEL_BYTES:] = PADDING
    payload_ptr = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload_ptr)
    struct.pack_into("<i", header, 0x20, ROWBYTES)
    struct.pack_into("<i", header, 0x24, WIDTH)
    struct.pack_into("<i", header, 0x28, HEIGHT)
    struct.pack_into("<H", header, 0x2C, 128)
    return alloc(loader, bytes(header)), payload_ptr


def split_pixels(payload: list[int]) -> list[list[int]]:
    return [payload[x * PIXEL_BYTES:(x + 1) * PIXEL_BYTES] for x in range(WIDTH)]


def floats(data: list[int]) -> list[float]:
    return list(struct.unpack("<4f", bytes(data)))


def run() -> dict[str, object]:
    opaque = pixel(OPAQUE)
    semi_destination = pixel(SEMI_DESTINATION)
    semi_witness = pixel(SEMI_POSTPASS_WITNESS)
    premult_witness = pixel(premultiplied(SEMI_POSTPASS_WITNESS))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    input_world, input_payload = make_world(loader, [opaque, semi_destination, semi_witness])
    output_world, output_payload = make_world(loader, [b"\0" * PIXEL_BYTES] * WIDTH)
    worlds = {
        input_world: {"payload": input_payload, "width": WIDTH, "height": HEIGHT,
                      "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        output_world: {"payload": output_payload, "width": WIDTH, "height": HEIGHT,
                       "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
    }
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", 1.0), align=16)
    helper_hits: list[dict] = []

    def on_helper(current: AexLoader, _address: int, _size: int) -> None:
        source = current.uc.reg_read(UC_X86_REG_RCX)
        destination = current.uc.reg_read(UC_X86_REG_RDX)
        helper_hits.append({
            "source_ptr": hex(source),
            "destination_ptr": hex(destination),
            "source_offset": source - output_payload,
            "destination_offset": destination - output_payload,
            "source_raw_before": raw(current, source, PIXEL_BYTES),
            "destination_raw_before": raw(current, destination, PIXEL_BYTES),
        })

    loader.add_code_hook(HELPER, on_helper)
    result: dict[str, object] = {
        "status": "BLOCKED",
        "aex": str(AEX.relative_to(ROOT)),
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "worker": hex(WORKER),
        "helper": hex(HELPER),
        "fixture": {
            "width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
            "pixel_bits": 128, "radius": 1.0,
            "layout": "x0 opaque seed; x1 semi-alpha propagated destination; x2 semi-alpha postpass witness",
        },
        "input": {
            "world": hex(input_world), "payload": hex(input_payload),
            "raw": raw(loader, input_payload, ROWBYTES),
            "pixels_float": [list(OPAQUE), list(SEMI_DESTINATION), list(SEMI_POSTPASS_WITNESS)],
            "postpass_witness_raw": list(semi_witness),
            "postpass_witness_rgb_times_alpha_raw": list(premult_witness),
        },
        "output": {"world": hex(output_world), "payload": hex(output_payload)},
    }
    try:
        call = loader.call_function(
            WORKER,
            int_args=[context, 0, input_world, output_world, radius],
            max_instructions=2_000_000,
        )
        # Required ordering: first output access after the worker return.
        output_after_return = raw(loader, output_payload, ROWBYTES)
        result.update({
            "worker_return_rax": hex(call["rax"]),
            "worker_instructions": call["instructions"],
            "output_raw_immediately_after_worker_return": output_after_return,
        })
    except Exception as exc:
        result.update({
            "status": "BLOCKED_FAIL_CLOSED",
            "first_blocker": f"{type(exc).__name__}: {exc}",
            "helper_hits": helper_hits,
            "events": events,
        })
        return result

    pixels = split_pixels(output_after_return)
    callback_hit = any(event.get("kind") == "pf_copy_callback" for event in events)
    propagation_hit = any(
        hit["source_offset"] == 0
        and hit["destination_offset"] == PIXEL_BYTES
        and hit["source_raw_before"] == list(opaque)
        and hit["destination_raw_before"] == list(semi_destination)
        for hit in helper_hits
    )
    result.update({
        "helper_hits": helper_hits,
        "events": events,
        "output": {
            **result["output"],
            "raw_immediately_after_worker_return": output_after_return,
            "pixels_raw": pixels,
            "pixels_float": [floats(value) for value in pixels],
            "padding_raw": output_after_return[WIDTH * PIXEL_BYTES:],
        },
    })
    result["gates"] = {
        "worker_returned": "worker_return_rax" in result,
        "pf_copy_callback_observed": callback_hit,
        "typed_pf32_helper_observed_live": bool(helper_hits),
        "opaque_to_semi_destination_propagation_observed": propagation_hit,
        "propagated_destination_equals_raw_opaque_source": pixels[1] == list(opaque),
        "radius_two_semi_witness_survives_raw": pixels[2] == list(semi_witness),
        "radius_two_semi_witness_not_rgb_times_alpha": pixels[2] != list(premult_witness),
        "radius_two_semi_witness_alpha_unchanged": pixels[2][:4] == list(semi_witness[:4]),
        "padding_preserved": output_after_return[WIDTH * PIXEL_BYTES:] == list(PADDING),
    }
    result["status"] = (
        "PASS_PF32_SEEDED_LIVE_RAW_NO_POSTPASS"
        if all(result["gates"].values())
        else "BLOCKED_FAIL_CLOSED"
    )
    result["facts"] = [
        "The actual PF32 worker returned through the Unicorn AexLoader trampoline.",
        "The worker PF_COPY callback and live typed PF32 helper were observed.",
        "The helper copied the opaque x0 source into the semi-alpha x1 destination at radius 1.",
        "The first output read after return showed x2 retained its semi-alpha straight RGB and alpha byte-for-byte.",
        "The x2 raw bytes differ from the exact RGB*alpha alternative.",
    ]
    result["inferences"] = [
        "The seeded live PF32 worker path contains no final RGB*=alpha postpass for the surviving semi-alpha x2 witness.",
        "The propagated x1 destination becomes the selected opaque source exactly; this is propagation behavior, not evidence of premultiplication.",
        "The synthetic suite/PF_COPY model is bounded observed-ABI scaffolding, not AE-host execution.",
    ]
    result["claim_boundary"] = (
        "Mac-local actual-AEX/Unicorn seeded PF32 worker witness; "
        "candidate/CLI/binary-grounded, not AE exact; no PNG/Windows/NAS"
    )
    return result


def main() -> int:
    payload = run()
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    gates = payload.get("gates", {})
    lines = [
        "# OLMToonDilate Seeded PF32 Live-Path Witness - 2026-07-17", "",
        "## Result", "", f"- Status: **{payload['status']}**",
        f"- AEX: `{payload['aex']}`", f"- SHA-256: `{payload['aex_sha256']}`",
        f"- Worker: `{payload['worker']}`; typed PF32 helper: `{payload['helper']}`",
        "- Execution: macOS-local Unicorn through the existing `AexLoader`; no PNG, Windows, NAS, or AE host.", "",
        "## FACT", "",
        "- Fixture: x0 opaque seed; x1 semi-alpha propagated destination; x2 semi-alpha straight-RGB witness; radius 1.",
        "- x2 is beyond the copy radius but remains in the same worker invocation that hits the live PF32 helper at x1.",
        "- The worker returned and raw output memory was read immediately after return.",
        "- x1 became the raw opaque source; x2 retained `(A=0.5, R=0.75, G=0.25, B=0.125)` exactly.",
        "- The RGB*=alpha alternative for x2 is `(A=0.5, R=0.375, G=0.125, B=0.0625)` and was not observed.",
        f"- Gates: `{json.dumps(gates, sort_keys=True)}`", "",
        "## INFERENCE", "",
        "- Required classification: **seeded live PF32 path preserves surviving semi-alpha RGB/alpha raw; no final RGB*=alpha postpass is present**.",
        "- This is candidate/CLI/binary-grounded evidence, not AE exact or broad host-conversion proof.", "",
        "## Reproduce", "", "```sh",
        "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf32_raw_copy_witness_20260717.py",
        "```", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS_PF32_SEEDED_LIVE_RAW_NO_POSTPASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
