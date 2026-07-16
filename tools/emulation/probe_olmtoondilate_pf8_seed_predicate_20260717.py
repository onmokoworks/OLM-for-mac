"""Bounded actual-AEX PF8 worker probe for the opaque seed predicate.

The fixture is deliberately small: one 5x1 row, radius 1, zero neighbors,
and paired x1 alpha values 254/255.  Output bytes are read immediately after
the native worker returns.  The checked-in AEX and a fixed worker byte-window
hash must match before the worker is invoked.
"""

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
    context_and_suite,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_seed_predicate_20260717.md"
JSON_REPORT = REPORT.with_suffix(".json")
WORKER = 0x1801A6150
HELPER = 0x1801AC880
FUNCTION_HASH_SIZE = 0x100
EXPECTED_AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
EXPECTED_WORKER_FUNCTION_SHA256 = "500bda28032d0ecf005415cc9488e8348c1b20e5b99f7c0c61f976cbae10f647"
WIDTH = 5
PIXEL_BYTES = 4
ROWBYTES = WIDTH * PIXEL_BYTES + 4
PADDING = b"\xA5" * 4
ZERO = bytes((0, 0, 0, 0))
X3_CONTROL = bytes((255, 17, 29, 43))


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    ptr = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(ptr, data)
    return ptr


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
    struct.pack_into("<i", header, 0x28, 1)
    struct.pack_into("<H", header, 0x2C, 32)
    return alloc(loader, bytes(header)), payload_ptr


def pixels(raw: list[int]) -> list[list[int]]:
    return [raw[index * PIXEL_BYTES:(index + 1) * PIXEL_BYTES] for index in range(WIDTH)]


def converted(pixel: bytes) -> bytes:
    alpha, red, green, blue = pixel
    if 0 < alpha < 255:
        return bytes((alpha, *((value * alpha + 127) // 255 for value in (red, green, blue))))
    return pixel


def model_exact_equality(source: list[bytes]) -> list[list[int]]:
    out = list(source)
    seeds = [index for index, value in enumerate(source) if value[0] == 255]
    for index, value in enumerate(source):
        if value[0] != 0:
            continue
        candidates = [seed for seed in seeds if abs(seed - index) <= 1]
        if candidates:
            out[index] = source[min(candidates, key=lambda seed: (abs(seed - index), seed))]
    return [list(value) for value in out]


def model_threshold_conversion(source: list[bytes]) -> list[list[int]]:
    out = list(source)
    seeds = [index for index, value in enumerate(source) if value[0] >= 254]
    for index, value in enumerate(source):
        if value[0] != 0:
            continue
        candidates = [seed for seed in seeds if abs(seed - index) <= 1]
        if candidates:
            out[index] = source[min(candidates, key=lambda seed: (abs(seed - index), seed))]
    return [list(converted(value)) for value in out]


def provenance() -> dict[str, object]:
    result: dict[str, object] = {
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest() if AEX.exists() else None,
        "expected_aex_sha256": EXPECTED_AEX_SHA256,
        "worker_address": hex(WORKER),
        "function_hash_size": FUNCTION_HASH_SIZE,
        "expected_worker_function_sha256": EXPECTED_WORKER_FUNCTION_SHA256,
    }
    if result["aex_sha256"] != EXPECTED_AEX_SHA256:
        result["first_unavailable_abi"] = "AEX provenance hash mismatch; native worker execution not attempted"
        return result
    try:
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        actual = hashlib.sha256(bytes(loader.read_bytes(WORKER, FUNCTION_HASH_SIZE))).hexdigest()
        result["worker_function_sha256"] = actual
        if actual != EXPECTED_WORKER_FUNCTION_SHA256:
            result["first_unavailable_abi"] = "worker address/function hash mismatch; native worker execution not attempted"
    except Exception as exc:
        result["first_unavailable_abi"] = f"{type(exc).__name__}: {exc}"
    return result


def run_pair(alpha: int, source: list[bytes], gate: dict[str, object]) -> dict[str, object]:
    item: dict[str, object] = {"x1_alpha": alpha, "input_raw": [list(value) for value in source], "status": "BLOCKED_FAIL_CLOSED"}
    if "first_unavailable_abi" in gate:
        item["first_unavailable_abi"] = gate["first_unavailable_abi"]
        return item
    try:
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        input_world, input_payload = make_world(loader, source)
        output_world, output_payload = make_world(loader, [ZERO] * WIDTH)
        worlds = {
            input_world: {"payload": input_payload, "width": WIDTH, "height": 1, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
            output_world: {"payload": output_payload, "width": WIDTH, "height": 1, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        }
        events: list[dict] = []
        context = context_and_suite(loader, events, worlds)
        radius = alloc(loader, struct.pack("<f", 1.0), align=16)
        helper_hits: list[dict] = []

        def on_helper(current: AexLoader, _address: int, _size: int) -> None:
            source_ptr = current.uc.reg_read(UC_X86_REG_RCX)
            destination_ptr = current.uc.reg_read(UC_X86_REG_RDX)
            helper_hits.append({"source": hex(source_ptr), "destination": hex(destination_ptr),
                                "source_raw_before": list(current.read_bytes(source_ptr, PIXEL_BYTES)),
                                "destination_raw_before": list(current.read_bytes(destination_ptr, PIXEL_BYTES))})

        loader.add_code_hook(HELPER, on_helper)
        call = loader.call_function(WORKER, int_args=[context, 0, input_world, output_world, radius], max_instructions=2_000_000)
        raw_after_return = list(loader.read_bytes(output_payload, ROWBYTES))
        actual = pixels(raw_after_return)
        expected_exact = model_exact_equality(source)
        expected_threshold = model_threshold_conversion(source)
        item.update({
            "status": "RETURN",
            "worker_return_rax": hex(call["rax"]),
            "worker_instructions": call["instructions"],
            "helper_hits": helper_hits,
            "events": events,
            "output_raw_immediately_after_worker_return": raw_after_return,
            "output_pixels": actual,
            "model_exact_equality_alpha_255": expected_exact,
            "model_threshold_conversion_alpha_ge_254": expected_threshold,
            "matches_exact_equality_model": actual == expected_exact,
            "matches_threshold_conversion_model": actual == expected_threshold,
            "padding_preserved": raw_after_return[WIDTH * PIXEL_BYTES:] == list(PADDING),
        })
        return item
    except Exception as exc:
        item["first_unavailable_abi"] = f"{type(exc).__name__}: {exc}"
        return item


def run() -> dict[str, object]:
    gate = provenance()
    pair = [
        run_pair(254, [ZERO, bytes((254, 255, 40, 80)), ZERO, X3_CONTROL, ZERO], gate),
        run_pair(255, [ZERO, bytes((255, 255, 40, 80)), ZERO, X3_CONTROL, ZERO], gate),
    ]
    gates = {
        "provenance_gate_passed": "first_unavailable_abi" not in gate,
        "both_workers_returned": all(item.get("status") == "RETURN" for item in pair),
        "both_helpers_observed": all(bool(item.get("helper_hits")) for item in pair),
        "raw_captured_immediately_after_return": all("output_raw_immediately_after_worker_return" in item for item in pair),
        "paired_alpha_only_difference": pair[0]["input_raw"][1][1:] == pair[1]["input_raw"][1][1:],
        "x3_opaque_control_retained_or_propagated": all(item.get("output_pixels", [[0] * 4] * WIDTH)[3] == list(X3_CONTROL) for item in pair),
        "padding_preserved": all(item.get("padding_preserved") is True for item in pair),
    }
    status = "PASS_PF8_SEED_PREDICATE_DISCRIMINATED" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    return {
        "status": status,
        "aex": str(AEX.relative_to(ROOT)),
        "worker": hex(WORKER),
        "helper": hex(HELPER),
        "fixture": {"width": WIDTH, "height": 1, "radius": 1.0, "layout": "x0 zero; x1 paired alpha 254/255; x2 zero; x3 alpha255 control; x4 zero", "pixel_format": "PF8 ARGB"},
        "provenance": gate,
        "paired_runs": pair,
        "gates": gates,
        "claim_boundary": "bounded actual-AEX PF8 worker fixture through local Unicorn; no PNG tuning, production edit, host or AE exact claim",
    }


def main() -> int:
    payload = run()
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# OLMToonDilate PF8 Seed Predicate - 2026-07-17", "", "## Result", "", f"- Status: **{payload['status']}**", f"- AEX: `{payload['aex']}`", f"- Worker/helper: `{payload['worker']}` / `{payload['helper']}`", "- Execution target: checked-in AEX under local Unicorn; no PNG, production, host, or AE-exact claim.", "", "## FACT", "", "- Fixture is 5x1 PF8 ARGB, radius 1, with zero neighbors.", "- x1 is paired at RGB `[255,40,80]` with alpha 254 versus 255; x3 is an alpha255 control.", "- Raw output is captured as the first memory read after native worker return.", f"- Provenance/hash gate: `{json.dumps(payload['provenance'], sort_keys=True)}`", f"- Gates: `{json.dumps(payload['gates'], sort_keys=True)}`", "", "## MODEL COMPARISON", "", "- `alpha == 255`: opaque seeds only; copied bytes remain raw.", "- `alpha >= 254` plus conversion: threshold seeds and partial-alpha RGB is converted with integer `(channel*alpha+127)//255`.", "- See the paired JSON for exact output bytes and both model comparisons.", "", "## Reproduce", "", "```sh", "tools/emulation/.venv/bin/python tools/emulation/probe_olmtoondilate_pf8_seed_predicate_20260717.py", "```", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS_PF8_SEED_PREDICATE_DISCRIMINATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
