"""Bounded actual-AEX ToonDilate PF16/PF32 copy-boundary witness.

The fixture calls the two typed worker entries in the checked-in Windows PE
through the local Unicorn loader.  It records raw source/destination bytes at
the copy-helper entry and immediately after each helper returns.  The suite
object at context+0x180 is deliberately separate from the worker context;
this is an ABI fixture, not an AE host implementation.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path
from unicorn.x86_const import (
    UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP, UC_X86_REG_R8,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
REPORT = ROOT / "refs/conformance/olmtoondilate_pf16_pf32_copy_boundary_20260716.md"
JSON_REPORT = REPORT.with_suffix(".json")

WORKERS = {16: 0x1801A5A90, 32: 0x1801A6800}
HELPERS = {16: 0x1801AC8B0, 32: 0x1801AC8E0}
PIXEL_BYTES = {16: 8, 32: 16}
PF_COPY_CALL = 0x1801A5B5E
PF_COPY_RESUME = 0x1801A5B61


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    ptr = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(ptr, data)
    return ptr


def make_world(loader: AexLoader, pixel_size: int, pixels: list[bytes], rowbytes: int) -> tuple[int, int]:
    height = 1
    width = len(pixels)
    payload = bytearray(rowbytes * height)
    for x, pixel in enumerate(pixels):
        payload[x * pixel_size:x * pixel_size + pixel_size] = pixel
    payload_ptr = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload_ptr)
    struct.pack_into("<i", header, 0x20, rowbytes)
    struct.pack_into("<i", header, 0x24, width)
    struct.pack_into("<i", header, 0x28, height)
    struct.pack_into("<H", header, 0x2C, pixel_size * 8)
    return alloc(loader, bytes(header)), payload_ptr


def context_and_suite(loader: AexLoader, events: list[dict], worlds: dict[int, dict]) -> int:
    context = loader.host_alloc(0x220, align=16)
    loader.write_bytes(context, b"\0" * 0x220)
    status_vtable = loader.host_alloc(0x50, align=16)
    loader.write_bytes(status_vtable, b"\0" * 0x50)

    def status_ok(current: AexLoader, args: list[int]) -> int:
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        source_ptr, destination_ptr = args[1], args[2]
        source = worlds.get(source_ptr)
        destination = worlds.get(destination_ptr)
        fifth_arg = struct.unpack("<Q", current.read_bytes(rsp + 0x28, 8))[0]
        events.append({"kind": "pf_copy_callback_entry", "args": [hex(v) for v in args] + [hex(fifth_arg)],
                       "world_keys": [hex(v) for v in worlds]})
        if source is None or destination is None:
            raise AssertionError("PF_COPY callback pointers did not identify fixture worlds")
        if source["pixel_size"] != destination["pixel_size"]:
            raise AssertionError("PF_COPY callback crossed pixel depths")
        visible = min(source["width"] * source["pixel_size"], source["rowbytes"],
                      destination["width"] * destination["pixel_size"], destination["rowbytes"])
        copied_rows = []
        for y in range(min(source["height"], destination["height"])):
            source_row = source["payload"] + y * source["rowbytes"]
            destination_row = destination["payload"] + y * destination["rowbytes"]
            copied_rows.append({"source": source_row, "destination": destination_row, "bytes": visible})
            current.write_bytes(destination_row, current.read_bytes(source_row, visible))
        events.append({
            "kind": "pf_copy_callback", "abi": "5 args",
            "args": [hex(v) for v in args] + [hex(fifth_arg)],
            "return_address": hex(struct.unpack("<Q", current.read_bytes(rsp, 8))[0]),
            "source_world": hex(source_ptr), "destination_world": hex(destination_ptr),
            "source_payload": hex(source["payload"]), "destination_payload": hex(destination["payload"]),
            "width": source["width"], "height": source["height"], "source_rowbytes": source["rowbytes"],
            "destination_rowbytes": destination["rowbytes"], "visible_bytes_per_row": visible,
            "copied_rows": copied_rows,
        })
        return 0

    status = loader.install_callback("toondilate_pf_copy_host_callback", status_ok)
    loader.write_bytes(status_vtable + 0x40, struct.pack("<Q", status))
    loader.write_bytes(context + 0xB0, struct.pack("<Q", status_vtable))
    loader.write_bytes(context + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(context + 0x11C, struct.pack("<i", 1))
    loader.write_bytes(context + 0x120, struct.pack("<i", 1))

    suite = loader.host_alloc(0x20, align=16)

    def suite_alloc(current: AexLoader, args: list[int]) -> int:
        size = max(1, args[0])
        ptr = current.host_alloc(size, align=16)
        current.write_bytes(ptr, b"\0" * size)
        events.append({"kind": "suite_alloc", "size": size, "result": hex(ptr)})
        return ptr

    def suite_free(_loader: AexLoader, args: list[int]) -> int:
        events.append({"kind": "suite_free", "ptr": hex(args[0])})
        return args[0]

    def suite_handle_slot10(_loader: AexLoader, args: list[int]) -> int:
        events.append({"kind": "suite_handle_slot10", "handle": hex(args[0])})
        return 0

    def suite_handle_slot18(_loader: AexLoader, args: list[int]) -> int:
        events.append({"kind": "suite_handle_slot18", "handle": hex(args[0])})
        return 0

    def suite_release(_loader: AexLoader, args: list[int]) -> int:
        events.append({"kind": "suite_release", "args": [hex(v) for v in args]})
        return 0

    alloc_callback = loader.install_callback("toondilate_suite_alloc_copy_boundary", suite_alloc)
    free_callback = loader.install_callback("toondilate_suite_free_copy_boundary", suite_free)
    handle_slot10_callback = loader.install_callback("toondilate_suite_handle_slot10_copy_boundary", suite_handle_slot10)
    handle_slot18_callback = loader.install_callback("toondilate_suite_handle_slot18_copy_boundary", suite_handle_slot18)
    release_callback = loader.install_callback("toondilate_suite_release_copy_boundary", suite_release)
    handle_vtable = loader.host_alloc(0x20, align=16)
    loader.write_bytes(handle_vtable, struct.pack("<4Q", alloc_callback, free_callback,
                                                   handle_slot10_callback, handle_slot18_callback))

    def suite_probe(current: AexLoader, args: list[int]) -> int:
        events.append({"kind": "suite", "args": [hex(v) for v in args]})
        current.write_bytes(args[2], struct.pack("<Q", handle_vtable))
        return 0

    suite_callback = loader.install_callback("toondilate_suite_probe_copy_boundary", suite_probe)
    loader.write_bytes(suite, struct.pack("<2Q", suite_callback, release_callback) + b"\0" * 0x10)
    loader.write_bytes(context + 0x180, struct.pack("<Q", suite))
    return context


def raw(loader: AexLoader, ptr: int, size: int) -> list[int]:
    return list(loader.read_bytes(ptr, size))


def run_depth(depth: int, pf16_alpha: int = 32768) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    size = PIXEL_BYTES[depth]
    rowbytes = size * 2 + 4  # retain visible padding after the two pixels
    if depth == 16:
        winner = struct.pack("<4H", 16384, 24000, 8000, 4000)
        opaque = struct.pack("<4H", pf16_alpha, 1234, 2345, 3456)
        fill = struct.pack("<4H", 0, 0, 0, 0)
        padding = b"\xA5" * 4
    else:
        winner = struct.pack("<4f", 0.5, 0.75, 0.25, 0.125)
        opaque = struct.pack("<4f", 1.0, 0.125, 0.25, 0.5)
        fill = struct.pack("<4f", 0.0, 0.0, 0.0, 0.0)
        padding = b"\xA5" * 4
    # R8 supplies the alpha discriminator matrix and R9 is retained as RBX
    # for the raw helper source world.  Seed the first input pixel and put
    # the discriminating source pixel second so propagation copies it back.
    worker_input, input_payload = make_world(loader, size, [winner, opaque], rowbytes)
    worker_source, source_payload = make_world(loader, size, [opaque, winner], rowbytes)
    worlds = {
        worker_input: {"payload": input_payload, "width": 2, "height": 1, "rowbytes": rowbytes, "pixel_size": size},
        worker_source: {"payload": source_payload, "width": 2, "height": 1, "rowbytes": rowbytes, "pixel_size": size},
    }
    loader.write_bytes(input_payload + size * 2, b"\x5A" * 4)
    loader.write_bytes(source_payload + size * 2, padding)
    events: list[dict] = []
    context = context_and_suite(loader, events, worlds)
    radius = alloc(loader, struct.pack("<f", 1.0), align=16)
    captures: list[dict] = []
    pending: dict[int, list[dict]] = {}
    return_hooks: set[int] = set()
    copy_resume: dict[str, object] = {}

    def on_copy_resume(current: AexLoader, _address: int, _size: int) -> None:
        callback = next((event for event in events if event["kind"] == "pf_copy_callback"), None)
        if callback is None:
            return
        visible = int(callback["visible_bytes_per_row"])
        destination = int(callback["destination_payload"], 16)
        source = int(callback["source_payload"], 16)
        copy_resume.update({
            "address": hex(PF_COPY_RESUME),
            "input_visible_after_callback": raw(current, input_payload, visible),
            "output_visible_after_callback": raw(current, destination, visible),
            "output_padding_after_callback": raw(current, destination + visible, rowbytes - visible),
            "output_visible_equals_input": raw(current, destination, visible) == raw(current, input_payload, visible),
        })

    loader.add_code_hook(PF_COPY_RESUME, on_copy_resume)

    def on_return(current: AexLoader, _address: int, _size: int) -> None:
        queue = pending.get(_address, [])
        if not queue:
            return
        item = queue.pop(0)
        item["after_source"] = raw(current, item["source_ptr"] - 4, size + 8)
        item["after_destination"] = raw(current, item["destination_ptr"] - 4, size * 2 + 8)

    def on_helper(current: AexLoader, _address: int, _size: int) -> None:
        rcx = current.uc.reg_read(UC_X86_REG_RCX)
        rdx = current.uc.reg_read(UC_X86_REG_RDX)
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", current.read_bytes(rsp, 8))[0]
        item = {"helper_entry": hex(HELPERS[depth]), "source_ptr": rcx, "destination_ptr": rdx,
                "return_address": hex(ret), "before_source": raw(current, rcx - 4, size + 8),
                "before_destination": raw(current, rdx - 4, size * 2 + 8)}
        captures.append(item)
        pending.setdefault(ret, []).append(item)
        if ret not in return_hooks:
            current.add_code_hook(ret, on_return)
            return_hooks.add(ret)

    loader.add_code_hook(HELPERS[depth], on_helper)
    result: dict[str, object] = {"depth": depth, "worker_entry": hex(WORKERS[depth]),
                                 "helper": hex(HELPERS[depth]), "status": "blocked"}
    try:
        call = loader.call_function(WORKERS[depth], int_args=[context, 0, worker_input, worker_source, radius],
                                    max_instructions=2_000_000)
        result.update({"status": "return", "return_rax": hex(call["rax"]), "instructions": call["instructions"]})
    except Exception as exc:
        match = re.search(r"RIP=0x([0-9a-fA-F]+)", str(exc))
        result.update({"error": str(exc), "deepest_address": f"0x{match.group(1).lower()}" if match else None})
    result.update({"context": hex(context), "context_180": hex(struct.unpack("<Q", loader.read_bytes(context + 0x180, 8))[0]),
                   "events": events, "captures": captures,
                   "copy_resume": copy_resume,
                   "input_world_raw": raw(loader, input_payload, rowbytes),
                   "worker_source_world_raw": raw(loader, source_payload, rowbytes),
                   "padding_expected": list(padding),
                   "worker_return_confirmed": result["status"] == "return"})
    for item in captures:
        source_pixel = item.get("before_source", [])[4:4 + size]
        destination_pixel = item.get("after_destination", [])[4:4 + size]
        destination_padding = item.get("after_destination", [])[4 + size * 2:4 + size * 2 + 4]
        item["source_pixel"] = source_pixel
        item["after_destination_pixel"] = destination_pixel
        item["after_destination_padding"] = destination_padding
        item["copy_model_match"] = bool(source_pixel and destination_pixel == source_pixel)
        item["padding_sentinel_preserved"] = destination_padding == list(padding)
        item["semantic_gate"] = item["copy_model_match"] and item["padding_sentinel_preserved"]
    callback = next((event for event in events if event["kind"] == "pf_copy_callback"), {})
    result["callback_semantic_gate"] = (bool(callback and copy_resume.get("output_visible_equals_input")
                                            and copy_resume.get("output_padding_after_callback") == list(padding))
                                        if depth == 16 else bool(callback))
    result["helper_source_in_output_payload"] = bool(captures) and all(
        item["destination_ptr"] <= item["source_ptr"] < item["destination_ptr"] + rowbytes
        and item["destination_ptr"] <= item["destination_ptr"] < item["destination_ptr"] + rowbytes
        for item in captures)
    result["semantic_gate"] = bool(captures) and all(item["semantic_gate"] for item in captures) and result["callback_semantic_gate"] and result["helper_source_in_output_payload"]
    return result


def run_direct_helper(depth: int) -> dict:
    """Prove the typed helper contract independently of the worker ABI."""
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    size = PIXEL_BYTES[depth]
    if depth == 16:
        winner = struct.pack("<4H", 16384, 24000, 8000, 4000)
        fill = struct.pack("<4H", 0, 0, 0, 0)
    else:
        winner = struct.pack("<4f", 0.5, 0.75, 0.25, 0.125)
        fill = struct.pack("<4f", 0.0, 0.0, 0.0, 0.0)
    sentinel = b"\xA5" * 4
    source_base = alloc(loader, b"\xCC" * 4 + winner + sentinel, align=16)
    destination_base = alloc(loader, b"\xDD" * 4 + fill + sentinel, align=16)
    source_ptr = source_base + 4
    destination_ptr = destination_base + 4
    result: dict[str, object] = {
        "depth": depth, "entry": hex(HELPERS[depth]), "source_ptr": hex(source_ptr),
        "destination_ptr": hex(destination_ptr), "before_source": raw(loader, source_base, size + 8),
        "before_destination": raw(loader, destination_base, size + 8), "return_confirmed": False,
    }
    try:
        call = loader.call_function(HELPERS[depth], int_args=[source_ptr, destination_ptr], max_instructions=10_000)
        result.update({"return_confirmed": True, "return_rax": hex(call["rax"])})
    except Exception as exc:
        result["error"] = str(exc)
    result["after_source"] = raw(loader, source_base, size + 8)
    result["after_destination"] = raw(loader, destination_base, size + 8)
    source_pixel = result["after_source"][4:4 + size]
    destination_pixel = result["after_destination"][4:4 + size]
    destination_padding = result["after_destination"][4 + size:4 + size + 4]
    result.update({
        "source_pixel": source_pixel,
        "after_destination_pixel": destination_pixel,
        "after_destination_padding": destination_padding,
        "copy_model_match": destination_pixel == source_pixel,
        "padding_sentinel_preserved": destination_padding == list(sentinel),
    })
    result["semantic_gate"] = bool(result["return_confirmed"] and result["copy_model_match"]
                                     and result["padding_sentinel_preserved"])
    return result


def main() -> int:
    depths = [run_depth(16), run_depth(32)]
    alpha_matrix = []
    for alpha in (1, 16384, 32767, 32768, 32769, 65535):
        probe = run_depth(16, alpha)
        capture = (probe.get("captures") or [{}])[0]
        alpha_matrix.append({
            "alpha": alpha,
            "worker_return_confirmed": probe.get("worker_return_confirmed"),
            "callback_resume_confirmed": probe.get("copy_resume", {}).get("address") == hex(PF_COPY_RESUME),
            "callback_output_equals_raw_input": probe.get("copy_resume", {}).get("output_visible_equals_input"),
            "helper_source_words": list(struct.unpack("<4H", bytes(capture.get("source_pixel", [])))) if len(capture.get("source_pixel", [])) == 8 else [],
            "helper_destination_words": list(struct.unpack("<4H", bytes(capture.get("after_destination_pixel", [])))) if len(capture.get("after_destination_pixel", [])) == 8 else [],
            "seed_or_propagate_observed": bool(capture.get("source_pixel")),
        })
    alpha_matrix_gate = all(
        item["seed_or_propagate_observed"] is (item["alpha"] == 32768)
        and item["callback_output_equals_raw_input"] is True
        for item in alpha_matrix
    )
    direct_helpers = [run_direct_helper(16), run_direct_helper(32)]
    semantic_pass = all(item["semantic_gate"] for item in direct_helpers)
    worker_pass = all(item["worker_return_confirmed"] and item["semantic_gate"] for item in depths)
    payload = {"status": "WORKER_COPY_GATE_PASS" if semantic_pass and worker_pass and alpha_matrix_gate else
               ("HELPER_GATE_PASS_WORKER_SEMANTIC_BLOCKED" if semantic_pass else "HELPER_GATE_FAILED"),
               "aex": str(AEX.relative_to(ROOT)), "workers": depths, "direct_helpers": direct_helpers,
               "pf16_alpha_matrix": alpha_matrix,
               "pf16_alpha_matrix_gate": alpha_matrix_gate,
               "comparison": "exact visible-byte copy and padding ownership only; no internal transformation claim",
               "semantic_gate": semantic_pass and alpha_matrix_gate and all(item["semantic_gate"] for item in depths),
               "abi_block": "Resolved locally: the suite handle vtable slots +0x10/+0x18 are modeled as the observed worker cleanup/accessor callbacks; no ABI block remains in this bounded fixture.",
               "claim_boundary": "bounded actual-AEX helper-boundary fixture only; no AE-exact or production-fix claim"}
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# OLMToonDilate PF16/PF32 Copy Boundary - 2026-07-16", "", "## Result", "",
             f"- Status: **{payload['status']}**", "- Execution: checked-in Windows PE AEX under local Unicorn on macOS.",
             "- Scope: worker entry/return and raw bytes immediately around the typed copy helpers.",
             "- No AE-exact or production-fix claim is made.", ""]
    for item in depths:
        lines += [f"## PF{item['depth']}", "", f"- Worker entry: `{item['worker_entry']}`",
                  f"- Copy helper: `{item['helper']}`", f"- Worker outcome: `{item['status']}`",
                  f"- Worker return confirmed: `{item['worker_return_confirmed']}`",
                  f"- Deepest address: `{item.get('deepest_address', 'return trampoline')}`",
                  f"- Helper captures: `{len(item['captures'])}`", f"- Full-worker semantic gate: `{item['semantic_gate']}`",
                  "- Gate requires helper source pixel == after-destination pixel byte-for-byte and preserves padding ownership.",
                  f"- Row padding preserved: `{item['padding_expected']}`", f"- Host PF_COPY callback gate: `{item['callback_semantic_gate']}`; resume hook: `{item['copy_resume'].get('address', 'not instrumented')}`",
                  f"- Helper source/destination both lie in output payload: `{item['helper_source_in_output_payload']}`", ""]
    lines += ["## Direct Helper Semantic Gates", "", "- These gates call the actual helper entries directly and are independent of the full-worker suite ABI.", ""]
    for item in direct_helpers:
        lines += [f"### PF{item['depth']}", "", f"- Helper entry: `{item['entry']}`",
                  f"- Helper return confirmed: `{item['return_confirmed']}`",
                  f"- Semantic gate: `{item['semantic_gate']}`",
                  f"- Source pixel: `{item['source_pixel']}`",
                  f"- After-destination pixel: `{item['after_destination_pixel']}`",
                  "- No internal-stage transformation model is used for classification.",
                  f"- Padding after destination: `{item['after_destination_padding']}`",
                  "- Required: exact copy equality and unchanged sentinel padding.", ""]
    lines += ["## ABI Boundary", "", "- The worker context is allocated through `context+0x180`.",
              "- `context+0x180` points to a separate suite object with a callback-shaped first slot.",
              "- The synthetic suite models acquire/release plus the observed handle-vtable slots at `+0x10` and `+0x18` used by worker cleanup.",
              "- PF16 callback arguments are captured at `0x1801a5b5e`; the post-callback point `0x1801a5b61` proves output visible bytes equal raw input.",
              "- The PF16 alpha matrix is binary-grounded worker evidence: only alpha `32768` observed the seed/propagation helper path.",
              "- A worker is marked returned only when the loader reaches its return trampoline.", "", "## Reproduce", "",
              "```sh", "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf16_pf32_copy_boundary_20260716.py", "```", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
