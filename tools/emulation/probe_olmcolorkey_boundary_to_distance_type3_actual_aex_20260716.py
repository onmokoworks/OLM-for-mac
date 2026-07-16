#!/usr/bin/env python3
"""Drive the ColorKey boundary seed through the type 3 distance leaf."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from probe_olmcolorkey_boundary_to_distance_actual_aex_20260716 import (  # noqa: E402
    BOUNDARY,
    DEFAULT_AEX,
    alloc,
    byte_grid,
    plane,
)
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import make_handle_suite  # noqa: E402
from aex_loader import AexLoader  # noqa: E402

TYPE3 = 0x180007EC0
EXPECTED_AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"


def f32_pixels(loader: AexLoader, payload: int, width: int, height: int) -> list[list[list[float]]]:
    values = struct.unpack("<%df" % (width * height * 4), loader.read_bytes(payload, width * height * 16))
    return [[list(values[(y * width + x) * 4:(y * width + x + 1) * 4]) for x in range(width)] for y in range(height)]


def euclidean_model(seed: list[list[int]], width: int, height: int, scale: float = 255.0) -> list[list[float]]:
    zeros = [(x, y) for y, row in enumerate(seed) for x, value in enumerate(row) if value == 0]
    if not zeros:
        raise AssertionError("independent model requires at least one zero seed")
    return [[scale * min(math.hypot(x - sx, y - sy) for sx, sy in zeros) for x in range(width)] for y in range(height)]


def float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def compare_float32(output: list[list[list[float]]], model: list[list[float]]) -> dict:
    errors = [
        abs(output[y][x][channel] - float32(model[y][x]))
        for y in range(len(model)) for x in range(len(model[0])) for channel in range(4)
    ]
    return {"match": all(error == 0.0 for error in errors), "max_abs_error": max(errors, default=None), "channels": 4}


def run(aex_path: Path) -> dict:
    width, height = 5, 3
    actual_sha256 = hashlib.sha256(aex_path.read_bytes()).hexdigest()
    try:
        aex_label = str(aex_path.relative_to(ROOT))
    except ValueError:
        aex_label = str(aex_path)
    base = {
        "target": {"va": hex(TYPE3), "name": "FUN_180007ec0"},
        "aex": {"path": aex_label, "expected_sha256": EXPECTED_AEX_SHA256, "actual_sha256": actual_sha256, "sha256_match": actual_sha256 == EXPECTED_AEX_SHA256},
        "loader_import_log": [],
        "classification": "Mac-local Unicorn execution of checked-in Windows PE with the proven narrow PF Handle Suite shim; not AE-host execution and not AE-exact",
        "scope_note": "Type3 boundary-to-distance lane only; no full Replace+Edge claim.",
    }
    if actual_sha256 != EXPECTED_AEX_SHA256:
        base.update({"status": "blocked", "blocked_reason": "AEX SHA-256 identity mismatch; loader execution skipped"})
        return base

    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    source = bytearray(width * height * 4)
    source[(1 * width + 2) * 4] = 255
    source_world = plane(loader, width, height, 4, bytes(source))
    seed_payload = alloc(loader, b"\0" * (width * height * 4))
    seed_world = plane(loader, width, height, 4, b"\0" * (width * height * 4))
    loader.write_bytes(seed_world + 0x18, struct.pack("<Q", seed_payload))
    boundary_call = loader.call_function(BOUNDARY, int_args=[source_world, seed_world, 8], max_instructions=200_000)
    seed = byte_grid(loader, seed_payload, width, height)

    output_bytes = b"\0" * (width * height * 16)
    output_world = plane(loader, width, height, 16, output_bytes)
    output_payload = struct.unpack("<Q", loader.read_bytes(output_world + 0x18, 8))[0]
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\0" * 0x200)
    loader.write_bytes(ctx + 0x120, struct.pack("<i", 255))
    loader.write_bytes(ctx + 0x128, struct.pack("<i", 255))
    events: list[dict] = []
    suite, vtable = make_handle_suite(loader, events)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", suite))

    result: dict[str, object] = {"status": "blocked"}
    output: list[list[list[float]]] | None = None
    error_text: str | None = None
    try:
        call = loader.call_function(TYPE3, int_args=[ctx, seed_world, output_world], float_args={3: 255.0}, max_instructions=500_000)
        result.update({
            "rax": hex(call["rax"]),
            "instructions": call["instructions"],
        })
        output = f32_pixels(loader, output_payload, width, height)
    except Exception as error:
        error_text = str(error)

    callbacks = [item["callback"] for item in events]
    import_log = [entry.name for entry in loader.import_log]
    new_handles = [item for item in events if item["callback"] == "PF_HandleSuite.new_handle"]
    expected = euclidean_model(seed, width, height)
    required_allocations = [item for item in new_handles if item["size"] == width * height * 4]
    lifecycle_valid = all(
        callbacks.index("PF_HandleSuite.lock_handle", callbacks.index("PF_HandleSuite.new_handle", start))
        >= start
        for start, item in enumerate(callbacks) if item == "PF_HandleSuite.new_handle"
    )
    cleanup_observed = "PF_HandleSuite.release_suite" in callbacks and callbacks[-1:] == ["PF_HandleSuite.release_suite"]
    lifecycle_complete = lifecycle_valid and callbacks.count("PF_HandleSuite.acquire") == callbacks.count("PF_HandleSuite.release_suite") and callbacks.count("PF_HandleSuite.new_handle") == callbacks.count("PF_HandleSuite.lock_handle") == callbacks.count("PF_HandleSuite.unlock_handle") == callbacks.count("PF_HandleSuite.dispose_handle")
    model_comparison = compare_float32(output, expected) if output is not None else {"match": False, "max_abs_error": None, "channels": 4}
    normal_return = result.get("rax") == "0x0" and output is not None and error_text is None
    gates = {"normal_return": normal_return, "exactly_one_required_allocation": len(required_allocations) == 1, "lifecycle_complete": lifecycle_complete, "cleanup_observed": cleanup_observed, "no_unresolved_imports": not import_log, "float32_model_match": model_comparison["match"]}
    result.update({
        **base,
        "status": "pass" if all(gates.values()) else "blocked",
        "blocked_reason": None if all(gates.values()) else "one or more acceptance gates failed",
        "abi": {"args": "RCX=ctx, RDX=seed_world, R8=distance_world, XMM3=255.0", "ctx_offsets": {"0x120": 255, "0x128": 255, "0x180": "HandleSuite descriptor"}},
        "world": {"width": width, "height": height, "distance_channels": 4, "pixel_bytes": 16},
        "seed": {"first_channel": seed, "boundary_rax": hex(boundary_call["rax"])},
        "independent_model": {"kind": "nearest_zero_seed_euclidean_pixel_distance", "first_channel": expected, "four_channel": True},
        "shim": {"suite": hex(suite), "vtable": hex(vtable), "events": events, "callbacks_seen": callbacks, "new_handle_allocations": new_handles, "allocation_count": len(new_handles), "required_allocation_count": len(required_allocations), "required_allocations": required_allocations, "expected_allocation_bytes": width * height * 4, "lifecycle_order_valid": lifecycle_valid},
        "loader_import_log": import_log,
        "normal_return": normal_return,
        "cleanup_observed": cleanup_observed,
        "lifecycle_complete": lifecycle_complete,
        "float32_model_comparison": model_comparison,
        "acceptance_gates": gates,
    })
    if output is not None:
        result["output"] = output
    if error_text is not None:
        result["error"] = error_text
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.aex)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
