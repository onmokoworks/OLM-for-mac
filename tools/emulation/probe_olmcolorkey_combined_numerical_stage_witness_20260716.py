#!/usr/bin/env python3
"""Bounded numerical witness for the OLMColorKey Replace/Thin/Blur chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RSI, UC_X86_REG_XMM0

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import (  # noqa: E402
    APPLY,
    make_handle_suite,
    world,
)

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
REPORT_JSON = ROOT / "refs/conformance/olmcolorkey_combined_numerical_stage_witness_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmcolorkey_combined_numerical_stage_witness_20260716.md"
EXPECTED_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"

REPLACE_PIXEL = 0x180001E00
REPLACE_HIT_SELECTED = 0x1800028AF
REPLACE_WRITE = 0x18000291A
REPLACE_ALPHA_DECISION = 0x180002963
BOUNDARY = 0x180008C90
TYPE3 = 0x180007EC0
WIDTH = HEIGHT = 5
PIXEL_BYTES = 4
FLOAT4_BYTES = 16
THIN_AMOUNT = 1
BLUR_AMOUNT = 2
DISTANCE_SCALE = 255.0
BLUR_DIRECTION = 1


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_word(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def first_bytes(raw: bytes, pixel_bytes: int) -> list[int]:
    return [raw[index] for index in range(0, len(raw), pixel_bytes)]


def first_f32_words(raw: bytes) -> list[str]:
    return [f"0x{struct.unpack_from('<I', raw, offset)[0]:08x}"
            for offset in range(0, len(raw), FLOAT4_BYTES)]


def _xmm_bytes(uc) -> bytes:
    raw = uc.reg_read(UC_X86_REG_XMM0)
    return raw.to_bytes(16, "little") if isinstance(raw, int) else bytes(raw)


def _write_xmm(uc, data: bytes) -> None:
    uc.reg_write(UC_X86_REG_XMM0, int.from_bytes(data.ljust(16, b"\0"), "little"))


def sin_impl(uc, _args: list[int]) -> int:
    _write_xmm(uc, struct.pack("<d", math.sin(struct.unpack("<d", _xmm_bytes(uc)[:8])[0])))
    return 0


def sinf_impl(uc, _args: list[int]) -> int:
    _write_xmm(uc, struct.pack("<f", math.sin(struct.unpack("<f", _xmm_bytes(uc)[:4])[0])))
    return 0


def fixture_bytes() -> bytes:
    pixels = bytearray([255, 0, 255, 0] * (WIDTH * HEIGHT))
    center = (2 * WIDTH + 2) * PIXEL_BYTES
    pixels[center:center + PIXEL_BYTES] = bytes([255, 255, 0, 0])
    return bytes(pixels)


def validate_world(loader: AexLoader, address: int, pixel_bytes: int, label: str) -> dict[str, object]:
    payload, rowbytes, width, height = struct.unpack("<Qiii", loader.read_bytes(address + 0x18, 0x14))
    valid = (payload != 0 and width == WIDTH and height == HEIGHT
             and rowbytes == WIDTH * pixel_bytes and pixel_bytes in (PIXEL_BYTES, FLOAT4_BYTES))
    result = {"label": label, "address": hex(address), "payload": hex(payload),
              "width": width, "height": height, "rowbytes": rowbytes,
              "pixel_bytes": pixel_bytes, "valid": valid}
    if not valid:
        raise ValueError(f"invalid {label} world shape/rowbytes/pixel size: {result}")
    loader.read_bytes(payload + (HEIGHT - 1) * rowbytes, rowbytes)
    return result


def boundary_oracle(matte: list[int]) -> list[int]:
    output = [255] * (WIDTH * HEIGHT)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            index = y * WIDTH + x
            if matte[index] == 0:
                continue
            all_nonzero = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                        all_nonzero = all_nonzero and matte[ny * WIDTH + nx] != 0
            output[index] = 255 if all_nonzero else 0
    return output


def distance_oracle(seed: list[int]) -> list[float]:
    zeros = [(x, y) for y in range(HEIGHT) for x in range(WIDTH)
             if seed[y * WIDTH + x] == 0]
    if not zeros:
        raise ValueError("portable type-3 oracle requires at least one zero seed")
    return [f32(DISTANCE_SCALE * min(math.hypot(x - zx, y - zy) for zx, zy in zeros))
            for y in range(HEIGHT) for x in range(WIDTH)]


def blur_oracle(before: bytes, matte: list[int], distance: list[float]) -> bytes:
    output = bytearray(before)
    amount = f32(BLUR_AMOUNT * DISTANCE_SCALE)
    for index, (matte_byte, dist) in enumerate(zip(matte, distance)):
        inside = matte_byte != 0
        if not inside:
            weight = 0.0
        elif dist >= amount:
            weight = 1.0
        else:
            phase = f32(f32(dist * f32(f32(math.pi) / amount)) - f32(math.pi / 2.0))
            weight = f32(f32(math.sin(phase) + 1.0) * 0.5)
        output[index * PIXEL_BYTES] = max(0, min(255, int(f32(matte_byte * weight))))
    return bytes(output)


def lifecycle_complete(events: list[dict[str, object]]) -> bool:
    callbacks = [str(event["callback"]) for event in events]
    names = ("new_handle", "lock_handle", "unlock_handle", "dispose_handle")
    counts = [callbacks.count(f"PF_HandleSuite.{name}") for name in names]
    handles = [str(event["result"]) for event in events
               if event["callback"] == "PF_HandleSuite.new_handle"]
    handle_lifecycles = all(
        sum(event.get("handle") == handle and event["callback"] == callback for event in events) == 1
        for handle in handles
        for callback in ("PF_HandleSuite.lock_handle", "PF_HandleSuite.unlock_handle",
                         "PF_HandleSuite.dispose_handle")
    )
    return (bool(callbacks) and callbacks[0] == "PF_HandleSuite.acquire"
            and callbacks[-1] == "PF_HandleSuite.release_suite"
            and callbacks.count("PF_HandleSuite.acquire")
            == callbacks.count("PF_HandleSuite.release_suite") > 0
            and counts[0] == counts[1] == counts[2] == counts[3] > 0
            and len(handles) == len(set(handles)) and handle_lifecycles)


def first_difference(stage: str, actual: list[object], expected: list[object],
                     item_stride: int = 1) -> dict[str, object] | None:
    if len(actual) != len(expected):
        return {"stage": stage, "kind": "length", "actual": len(actual), "expected": len(expected)}
    for index, (actual_value, expected_value) in enumerate(zip(actual, expected)):
        if actual_value != expected_value:
            pixel = index // item_stride
            return {"stage": stage, "kind": "value", "index": index,
                    "x": pixel % WIDTH, "y": pixel // WIDTH,
                    "actual": actual_value, "expected": expected_value}
    return None


def blocked(reason: str, digest: str | None = None) -> dict[str, object]:
    return {"kind": "olmcolorkey_combined_numerical_stage_witness_20260716", "schema": 1,
            "status": "blocked", "first_divergence": {"stage": "preflight", "reason": reason},
            "aex": {"path": str(AEX.relative_to(ROOT)), "expected_sha256": EXPECTED_SHA256,
                    "actual_sha256": digest, "sha256_match": digest == EXPECTED_SHA256},
            "classification": "Mac-local actual-binary vs portable evidence only; never AE exact"}


def run(aex_path: Path = AEX) -> dict[str, object]:
    if sys.platform != "darwin":
        return blocked("Mac-only witness")
    if not aex_path.is_file():
        return blocked("checked-in AEX missing")
    digest = hashlib.sha256(aex_path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        return blocked("AEX SHA-256 mismatch; execution skipped", digest)

    loader = AexLoader(str(aex_path), verbose=False, fast=False)
    loader.import_impls.update({"sin": sin_impl, "sinf": sinf_impl})
    source = fixture_bytes()

    source_world, _source_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, source)
    replacement_world, replacement_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, source)
    worlds = [validate_world(loader, source_world, PIXEL_BYTES, "source"),
              validate_world(loader, replacement_world, PIXEL_BYTES, "replacement")]

    refcon = loader.host_alloc(0x600)
    loader.write_bytes(refcon, b"\0" * 0x600)
    loader.write_bytes(refcon + 0x20, struct.pack("<i", 8))
    loader.write_bytes(refcon + 0x24, b"\1")
    loader.write_bytes(refcon + 0x4D, b"\1")
    loader.write_bytes(refcon + 0x53D, b"\1")
    loader.write_bytes(refcon + 0x208, struct.pack("<3f", 0.0, 0.0, 1.0))
    replacement_writes: list[str] = []
    loader.add_code_hook(REPLACE_HIT_SELECTED, lambda ld, _a, _s: ld.uc.reg_write(UC_X86_REG_RAX, 0))
    loader.add_code_hook(REPLACE_WRITE, lambda _ld, address, _s: replacement_writes.append(hex(address)))
    loader.add_code_hook(REPLACE_ALPHA_DECISION, lambda ld, _a, _s: ld.uc.reg_write(UC_X86_REG_RSI, 1))
    center_offset = (2 * WIDTH + 2) * PIXEL_BYTES
    replacement_call = loader.call_function(
        REPLACE_PIXEL,
        int_args=[refcon, 2, 2, struct.unpack("<Q", loader.read_bytes(source_world + 0x18, 8))[0] + center_offset,
                  replacement_payload + center_offset],
        max_instructions=10_000,
    )
    replacement = loader.read_bytes(replacement_payload, len(source))
    expected_replacement = bytearray(source)
    expected_replacement[center_offset:center_offset + PIXEL_BYTES] = bytes([255, 0, 0, 255])

    matte_bytes = bytearray(WIDTH * HEIGHT * PIXEL_BYTES)
    matte_bytes[center_offset] = 255
    matte_world, matte_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, bytes(matte_bytes))
    seed_world, seed_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, b"\0" * len(matte_bytes))
    worlds.extend([validate_world(loader, matte_world, PIXEL_BYTES, "thin_matte"),
                   validate_world(loader, seed_world, PIXEL_BYTES, "thin_boundary_seed")])
    boundary_call = loader.call_function(BOUNDARY, int_args=[matte_world, seed_world, 8], max_instructions=50_000)
    matte = first_bytes(loader.read_bytes(matte_payload, len(matte_bytes)), PIXEL_BYTES)
    seed = first_bytes(loader.read_bytes(seed_payload, len(matte_bytes)), PIXEL_BYTES)
    expected_seed = boundary_oracle(matte)

    distance_world, distance_payload = world(
        loader, WIDTH, HEIGHT, FLOAT4_BYTES, b"\0" * (WIDTH * HEIGHT * FLOAT4_BYTES))
    worlds.append(validate_world(loader, distance_world, FLOAT4_BYTES, "type3_distance"))
    context = loader.host_alloc(0x200)
    loader.write_bytes(context, b"\0" * 0x200)
    loader.write_bytes(context + 0x120, struct.pack("<i", 255))
    loader.write_bytes(context + 0x128, struct.pack("<i", 255))
    suite_events: list[dict[str, object]] = []
    suite, vtable = make_handle_suite(loader, suite_events)
    loader.write_bytes(context + 0x180, struct.pack("<Q", suite))
    distance_call = loader.call_function(TYPE3, int_args=[context, seed_world, distance_world],
                                         float_args={3: DISTANCE_SCALE}, max_instructions=100_000)
    distance_raw = loader.read_bytes(distance_payload, WIDTH * HEIGHT * FLOAT4_BYTES)
    distance_words = first_f32_words(distance_raw)
    expected_distance = distance_oracle(seed)
    expected_distance_words = [f32_word(value) for value in expected_distance]

    destination_world, destination_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, replacement)
    worlds.append(validate_world(loader, destination_world, PIXEL_BYTES, "blur_destination"))
    before_apply = loader.read_bytes(destination_payload, len(replacement))
    apply_call = loader.call_function(
        APPLY,
        int_args=[context, 0, BLUR_DIRECTION, source_world, matte_world, distance_world,
                  destination_world, 0],
        float_args={1: BLUR_AMOUNT * DISTANCE_SCALE},
        max_instructions=100_000,
    )
    after_apply = loader.read_bytes(destination_payload, len(replacement))
    expected_after_apply = blur_oracle(bytes(expected_replacement), matte, expected_distance)

    callbacks = [str(event["callback"]) for event in suite_events]
    imports = [entry.name for entry in loader.import_log]
    stage_checks = [
        ("replacement_output", list(replacement), list(expected_replacement), PIXEL_BYTES),
        ("thin_boundary_seed", seed, expected_seed, 1),
        ("type3_distance", distance_words, expected_distance_words, 1),
        ("blur_destination_before", list(before_apply), list(expected_replacement), PIXEL_BYTES),
        ("blur_destination_after", list(after_apply), list(expected_after_apply), PIXEL_BYTES),
    ]
    divergence = None
    for stage, actual, expected, item_stride in stage_checks:
        divergence = first_difference(stage, actual, expected, item_stride)
        if divergence:
            break

    returns = {"replacement": replacement_call["rax"], "thin_boundary": boundary_call["rax"],
               "type3_distance": distance_call["rax"], "blur_apply": apply_call["rax"]}
    gates = {
        "hash_match": True,
        "world_contracts_valid": all(item["valid"] for item in worlds),
        "normal_returns": all(value == 0 for value in returns.values()),
        "replacement_write_observed": replacement_writes == [hex(REPLACE_WRITE)],
        "replacement_not_pass_through": replacement != source,
        "suite_lifecycle_complete": lifecycle_complete(suite_events),
        "imports_complete": imports == ["sin"],
        "all_stage_outputs_match": divergence is None,
    }
    if divergence is None:
        for gate, passed in gates.items():
            if not passed:
                divergence = {"stage": "acceptance", "gate": gate}
                break

    return {
        "kind": "olmcolorkey_combined_numerical_stage_witness_20260716",
        "schema": 1,
        "status": "pass" if divergence is None else "blocked",
        "first_divergence": divergence,
        "classification": "Mac-local actual-binary vs portable evidence only; never AE exact",
        "aex": {"path": str(aex_path.relative_to(ROOT)), "expected_sha256": EXPECTED_SHA256,
                "actual_sha256": digest, "sha256_match": True},
        "fixture": {"dimensions": [WIDTH, HEIGHT],
                    "logical_format": "RGBA8",
                    "actual_binary_adapter_format": "PF_Pixel8 packed A,R,G,B bytes",
                    "logical_rgba": {"background": [0, 255, 0, 255],
                                     "keyed_center": [255, 0, 0, 255],
                                     "replacement_center": [0, 0, 255, 255]},
                    "packed_argb": {"background": [255, 0, 255, 0],
                                    "keyed_center": [255, 255, 0, 0],
                                    "replacement_center": [255, 0, 0, 255]},
                    "thin": {"amount": THIN_AMOUNT, "distance_type": 3},
                    "blur": {"amount": BLUR_AMOUNT, "distance_type": 3,
                             "direction": BLUR_DIRECTION, "direction_name": "Inside"}},
        "abi": {"replacement_pixel": hex(REPLACE_PIXEL), "boundary": hex(BOUNDARY),
                "type3_distance": hex(TYPE3), "blur_apply": hex(APPLY),
                "distance_scale": DISTANCE_SCALE, "blur_amount_scaled": BLUR_AMOUNT * DISTANCE_SCALE},
        "worlds": worlds,
        "captures": {
            "replacement_output": list(replacement),
            "thin_matte_first_channel": matte,
            "thin_boundary_seed_first_channel": seed,
            "type3_distance_first_channel_float32_words": distance_words,
            "blur_destination_before": list(before_apply),
            "blur_destination_after": list(after_apply),
        },
        "portable_oracle": {
            "boundary_rule": "initialize to 255; clear a nonzero matte pixel to 0 iff any in-frame 8-neighbor is zero; frame exterior is ignored",
            "thin_boundary_seed_first_channel": expected_seed,
            "distance_rule": "float32(nearest zero-seed Euclidean pixel distance * 255)",
            "type3_distance_first_channel_float32_words": expected_distance_words,
            "direction_1_apply_rule": "outside=0; inside dist>=amount=1; otherwise (sin(dist*pi/amount-pi/2)+1)/2; write trunc(matte*weight)",
            "blur_destination_after": list(expected_after_apply),
        },
        "execution": {"returns": {key: hex(value) for key, value in returns.items()},
                      "instructions": {"replacement": replacement_call["instructions"],
                                       "thin_boundary": boundary_call["instructions"],
                                       "type3_distance": distance_call["instructions"],
                                       "blur_apply": apply_call["instructions"]},
                      "replacement_write_hits": replacement_writes,
                      "suite_callbacks": callbacks, "imports": imports,
                      "suite": hex(suite), "vtable": hex(vtable)},
        "acceptance_gates": gates,
    }


def markdown(report: dict[str, object]) -> str:
    divergence = report.get("first_divergence")
    captures = report.get("captures", {})
    execution = report.get("execution", {})
    return "\n".join([
        "# OLMColorKey Combined Numerical-Stage Witness 20260716", "",
        f"- Status: **{report['status']}**",
        "- Scope: Mac-local execution of the hash-pinned checked-in Windows binary under Unicorn versus an independent portable oracle; never AE exact.",
        f"- First divergence: `{json.dumps(divergence, sort_keys=True)}`", "",
        "## Fixture", "",
        "A deterministic 5x5 RGBA8 fixture uses opaque green everywhere, an opaque red keyed center, and an opaque blue replacement center. The actual binary adapter packs those pixels as PF_Pixel8 A,R,G,B bytes. Thin is amount 1/type 3; Blur is amount 2/type 3, Direction 1 (Inside).", "",
        "## Captures", "",
        f"- Replacement output: `{captures.get('replacement_output')}`",
        f"- Thin matte first channel: `{captures.get('thin_matte_first_channel')}`",
        f"- Thin boundary seed first channel: `{captures.get('thin_boundary_seed_first_channel')}`",
        f"- Type-3 first-channel float32 words: `{captures.get('type3_distance_first_channel_float32_words')}`",
        f"- Destination before Blur Apply: `{captures.get('blur_destination_before')}`",
        f"- Destination after Blur Apply: `{captures.get('blur_destination_after')}`", "",
        "## Fail-Closed Gates", "",
        f"`{json.dumps(report.get('acceptance_gates', {}), sort_keys=True)}`", "",
        f"Returns: `{json.dumps(execution.get('returns', {}), sort_keys=True)}`. Instructions: `{json.dumps(execution.get('instructions', {}), sort_keys=True)}`.",
        "The probe does not tune after a mismatch: stage comparisons are ordered replacement, Thin boundary, type-3 distance, destination-before, and destination-after, and the report retains only the first divergence classification.",
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=AEX)
    parser.add_argument("--json", type=Path, default=REPORT_JSON)
    parser.add_argument("--markdown", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    report = run(args.aex)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json),
                      "markdown": str(args.markdown),
                      "first_divergence": report.get("first_divergence")}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
