"""Bounded actual-AEX ToonDilate semialpha worker-boundary fixture.

This invokes the checked-in Windows PE AEX through the local Unicorn loader.
It supplies one premultiplied-looking and one straight-looking partial-alpha
pixel to each PF8/PF16/PF32 worker lane and records raw ARGB bytes at the
depth-specific copy helper.  The fixture is intentionally not an AE host
render and makes no host-convention claim.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import context_and_suite  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
REPORT = ROOT / "refs/conformance/olmtoondilate_semialpha_actual_aex_20260716.md"
JSON_REPORT = REPORT.with_suffix(".json")
WORKERS = {8: 0x1801A6150, 16: 0x1801A5A90, 32: 0x1801A6800}
HELPERS = {8: 0x1801AC880, 16: 0x1801AC8B0, 32: 0x1801AC8E0}
PIXEL_BYTES = {8: 4, 16: 8, 32: 16}
# With the four-pixel bounded row, the actual helper source is slot 3 for
# PF8/PF32 and slot 0 for PF16.  Seed that slot and keep an opaque pixel in
# the opposite end as the worker's discriminator.
HELPER_SOURCE_SLOT = {8: 3, 16: 0, 32: 3}
COPY_RESUME = {8: 0x1801A6221, 16: 0x1801A5B61, 32: 0x1801A68D1}


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    ptr = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(ptr, data)
    return ptr


def make_world(loader: AexLoader, pixel_size: int, pixels: list[bytes]) -> tuple[int, int]:
    rowbytes = pixel_size * len(pixels)
    payload = alloc(loader, b"".join(pixels), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<i", header, 0x20, rowbytes)
    struct.pack_into("<i", header, 0x24, len(pixels))
    struct.pack_into("<i", header, 0x28, 1)
    struct.pack_into("<H", header, 0x2C, pixel_size * 8)
    return alloc(loader, bytes(header)), payload


def make_context(loader: AexLoader, events: list[dict], worlds: dict[int, dict]) -> int:
    context = loader.host_alloc(0x220, align=16)
    loader.write_bytes(context, b"\0" * 0x220)
    status_vtable = loader.host_alloc(0x50, align=16)
    loader.write_bytes(status_vtable, b"\0" * 0x50)

    def status_ok(current: AexLoader, args: list[int]) -> int:
        source = worlds.get(args[1])
        destination = worlds.get(args[2])
        if source is None or destination is None:
            raise AssertionError("AEX PF_COPY callback did not identify fixture worlds")
        size = min(source["rowbytes"], destination["rowbytes"])
        current.write_bytes(destination["payload"], current.read_bytes(source["payload"], size))
        events.append({"kind": "pf_copy", "source": hex(args[1]), "destination": hex(args[2]),
                       "bytes": size})
        return 0

    status = loader.install_callback("toondilate_semialpha_status", status_ok)
    loader.write_bytes(status_vtable + 0x40, struct.pack("<Q", status))
    loader.write_bytes(context + 0xB0, struct.pack("<Q", status_vtable))
    loader.write_bytes(context + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(context + 0x11C, struct.pack("<i", 1))
    loader.write_bytes(context + 0x120, struct.pack("<i", 1))

    suite = loader.host_alloc(0x20, align=16)
    handle_vtable = loader.host_alloc(0x20, align=16)

    def suite_alloc(current: AexLoader, args: list[int]) -> int:
        size = max(1, args[0])
        ptr = current.host_alloc(size, align=16)
        current.write_bytes(ptr, b"\0" * size)
        return ptr

    def suite_noop(_current: AexLoader, _args: list[int]) -> int:
        return 0

    alloc_cb = loader.install_callback("toondilate_semialpha_alloc", suite_alloc)
    noop_a = loader.install_callback("toondilate_semialpha_noop_a", suite_noop)
    noop_b = loader.install_callback("toondilate_semialpha_noop_b", suite_noop)
    noop_c = loader.install_callback("toondilate_semialpha_noop_c", suite_noop)
    loader.write_bytes(handle_vtable, struct.pack("<4Q", alloc_cb, noop_a, noop_b, noop_c))

    def suite_probe(current: AexLoader, args: list[int]) -> int:
        current.write_bytes(args[2], struct.pack("<Q", handle_vtable))
        events.append({"kind": "suite_probe"})
        return 0

    probe = loader.install_callback("toondilate_semialpha_suite_probe", suite_probe)
    loader.write_bytes(suite, struct.pack("<2Q", probe, noop_a) + b"\0" * 0x10)
    loader.write_bytes(context + 0x180, struct.pack("<Q", suite))
    return context


def pixel_bytes(depth: int) -> tuple[bytes, bytes, bytes, bytes]:
    if depth == 8:
        return (bytes((128, 64, 32, 16)), bytes((128, 200, 100, 50)),
                bytes((255, 31, 127, 223)), bytes(4))
    if depth == 16:
        return (struct.pack("<4H", 32768, 16384, 8192, 4096),
                struct.pack("<4H", 32768, 50000, 30000, 20000),
                struct.pack("<4H", 65535, 1234, 2345, 3456), b"\0" * 8)
    return (struct.pack("<4f", 0.5, 0.25, 0.125, 0.0625),
            struct.pack("<4f", 0.5, 0.8, 0.6, 0.4),
            struct.pack("<4f", 1.0, 0.125, 0.25, 0.5), b"\0" * 16)


def run_depth(depth: int, selected: str) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    premult, straight, opaque, zero = pixel_bytes(depth)
    selected_pixel = premult if selected == "premult-looking" else straight
    if HELPER_SOURCE_SLOT[depth] == 0:
        input_pixels = [selected_pixel, zero, zero, opaque]
    else:
        input_pixels = [opaque, zero, zero, selected_pixel]
    worker_input, input_payload = make_world(loader, PIXEL_BYTES[depth], input_pixels)
    worker_source, source_payload = make_world(loader, PIXEL_BYTES[depth], input_pixels)
    worlds = {
        worker_input: {"payload": input_payload, "rowbytes": PIXEL_BYTES[depth] * 2,
                       "width": 4, "height": 1, "pixel_size": PIXEL_BYTES[depth]},
        worker_source: {"payload": source_payload, "rowbytes": PIXEL_BYTES[depth] * 2,
                        "width": 4, "height": 1, "pixel_size": PIXEL_BYTES[depth]},
    }
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", 1.0), align=16)
    captures: list[dict] = []
    return_hooks: set[int] = set()

    def on_copy_resume(current: AexLoader, _address: int, _size: int) -> None:
        # The real callback has just copied the discriminator world.  Restore
        # the selected probe in the worker-source world at this exact AEX
        # resume boundary so the following helper capture tests worker math,
        # not opaque-source selection in the synthetic copy setup.
        current.write_bytes(source_payload, selected_pixel * 4)

    loader.add_code_hook(COPY_RESUME[depth], on_copy_resume)

    def on_helper(current: AexLoader, _address: int, _size: int) -> None:
        source = current.uc.reg_read(UC_X86_REG_RCX)
        destination = current.uc.reg_read(UC_X86_REG_RDX)
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        return_address = struct.unpack("<Q", current.read_bytes(rsp, 8))[0]
        item = {"source": hex(source), "destination": hex(destination),
                "before_source": list(current.read_bytes(source, PIXEL_BYTES[depth])),
                "before_destination": list(current.read_bytes(destination, PIXEL_BYTES[depth])),
                "return_address": hex(return_address)}
        captures.append(item)

        def on_return(after: AexLoader, _return: int, _return_size: int) -> None:
            item["after_source"] = list(after.read_bytes(source, PIXEL_BYTES[depth]))
            item["after_destination"] = list(after.read_bytes(destination, PIXEL_BYTES[depth]))
            item["raw_four_channel_preserved"] = item["after_destination"] == item["before_source"]

        if return_address not in return_hooks:
            current.add_code_hook(return_address, on_return)
            return_hooks.add(return_address)

    loader.add_code_hook(HELPERS[depth], on_helper)
    result = {"depth": depth, "selected": selected, "helper_source_slot": HELPER_SOURCE_SLOT[depth],
              "selected_raw": list(selected_pixel), "worker": hex(WORKERS[depth]), "helper": hex(HELPERS[depth]),
              "input_raw": list(loader.read_bytes(input_payload, PIXEL_BYTES[depth] * 2)),
              "source_raw": list(loader.read_bytes(source_payload, PIXEL_BYTES[depth] * 2)),
              "status": "BLOCKED"}
    try:
        call = loader.call_function(WORKERS[depth], int_args=[context, 0, worker_input, worker_source, radius],
                                    max_instructions=2_000_000)
        result.update({"status": "RETURN", "instructions": call["instructions"]})
    except Exception as exc:
        result["error"] = str(exc)
    destination_payload = input_payload
    for event in events:
        if event["kind"] == "pf_copy_callback":
            destination_payload = int(event["destination_payload"], 16)
            break
    result.update({"events": events, "captures": captures,
                   "output_raw": list(loader.read_bytes(destination_payload, PIXEL_BYTES[depth] * 2))})
    result["helper_reached"] = bool(captures)
    result["helper_source_matches_selected"] = bool(captures) and all(
        item["before_source"] == result["selected_raw"] for item in captures)
    result["raw_four_channel_preserved"] = bool(captures) and all(
        item.get("raw_four_channel_preserved") is True for item in captures)
    return result


def main() -> int:
    depths = [run_depth(depth, selected) for depth in (8, 16, 32)
              for selected in ("premult-looking", "straight-looking")]
    gate = all(item["status"] == "RETURN" and item["helper_reached"] and
               item["helper_source_matches_selected"] and item["raw_four_channel_preserved"] for item in depths)
    payload = {
        "status": "PASS_NO_COPY_HELPER_PREMULTIPLY_OBSERVED" if gate else "BLOCKED",
        "aex": str(AEX.relative_to(ROOT)),
        "workers": depths,
        "input_encoding": "ARGB; partial alpha with RGB <= alpha (premult-looking) or RGB > alpha (straight-looking)",
        "raw_output_encoding": "raw bytes at actual-AEX depth-specific copy-helper boundary",
        "boundary_intervention": "at each actual PF_COPY resume address, restore selected semialpha bytes across the four-pixel worker-source row before AEX pixel propagation continues",
        "exact_checks": {"all_six_runs_return": all(item["status"] == "RETURN" for item in depths),
                         "both_input_orientations_per_depth": all(sum(item["depth"] == depth for item in depths) == 2 for depth in (8, 16, 32)),
                         "all_helpers_reached": all(item["helper_reached"] for item in depths),
                         "all_helper_sources_match_explicit_selected_raw": all(item["helper_source_matches_selected"] for item in depths),
                         "all_raw_four_channels_preserved": all(item["raw_four_channel_preserved"] for item in depths)},
        "interpretation": "The actual-AEX typed copy helpers preserve injected semialpha ARGB bytes exactly after the PF_COPY resume intervention. This does not prove the full worker has no earlier premultiply stage and does not establish AE host conventions.",
        "claim_boundary": "actual-AEX typed copy-helper boundary after explicit PF_COPY-resume injection; no full-worker, AE, Windows-runtime, or host-convention claim",
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# OLMToonDilate Semialpha Actual-AEX Worker Fixture - 2026-07-16", "",
             "## Result", "", f"- Status: **{payload['status']}**",
             "- Execution: checked-in Windows PE AEX under local Unicorn on macOS.",
             "- Scope: PF8/PF16/PF32 worker entries through their actual-AEX copy-helper boundary.",
             "- Input: ARGB pixels with partial alpha; both premultiplied-looking and straight-looking variants per depth.",
             "- Arrangement: PF8/PF32 selected pixel in helper source slot 3; PF16 selected pixel in helper source slot 0; the opposite end is opaque.",
             "- Output: raw four-channel bytes captured at the helper boundary.",
             "- No AE, Windows, production, or unsupported host-convention claim is made.", ""]
    for item in depths:
        lines += [f"## PF{item['depth']} / {item['selected']}", "", f"- Worker: `{item['worker']}`; helper: `{item['helper']}`",
                  f"- Worker returned: `{item['status']}`; helper reached: `{item['helper_reached']}`",
                  f"- Helper source slot: `{item['helper_source_slot']}`; explicit selected raw match: `{item['helper_source_matches_selected']}`",
                  f"- Raw four-channel preservation: `{item['raw_four_channel_preserved']}`",
                  f"- Input raw: `{item['input_raw']}`", f"- Source/output raw after worker: `{item['output_raw']}`",
                  f"- Captures: `{json.dumps(item['captures'])}`", ""]
    lines += ["## Exact Checks", "", "```json", json.dumps(payload["exact_checks"], indent=2), "```", "",
              "## Interpretation", "", payload["interpretation"], "", "## Reproduce", "",
              "```sh", "tools/emulation/.venv/bin/python tools/emulation/olmtoondilate_semialpha_actual_aex_20260716_fixture.py", "```", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
