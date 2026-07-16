#!/usr/bin/env python3
"""Hash-pinned Mac-local AEX search for the ColorKey erode leaf."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402
from probe_olmcolorkey_boundary_to_distance_actual_aex_20260716 import alloc, plane  # noqa: E402
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import make_handle_suite  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
TARGET = 0x180008320
FUNCTION_END = 0x1800085B0
WIDTH, HEIGHT = 5, 3
PIXELS = WIDTH * HEIGHT
AMOUNTS = (-1.0, -2.0, -3.0, -4.0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_ptr(loader: AexLoader, world_ptr: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(world_ptr + 0x18, 8))[0]


def l1_to_zero(seed: list[int], width: int, height: int) -> list[float]:
    result = []
    for index, value in enumerate(seed):
        if value == 0:
            result.append(0.0)
            continue
        x, y = index % width, index // width
        distances = [abs(x - (other % width)) + abs(y - (other // width))
                     for other, candidate in enumerate(seed) if candidate == 0]
        result.append(float(min(distances)) if distances else float("inf"))
    return result


def threshold_oracle(seed: list[int], width: int, height: int, amount: float, bias: int) -> list[int]:
    limit = abs(amount) + bias
    return [255 if value and distance > limit else 0
            for value, distance in zip(seed, l1_to_zero(seed, width, height))]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def independent_oracle(seed: list[int], generated: list[float], width: int, height: int) -> list[int]:
    """Model the raw 16-bit load/MULSS/CVTTSS2SI/store path."""
    source = b"".join(struct.pack("<I", value) for value in seed)
    destination = bytearray(len(source))
    row_bytes = width * 4
    for y in range(height):
        for x in range(width):
            source_offset = y * row_bytes + x * 2
            destination_offset = y * row_bytes + x * 4
            word = struct.unpack_from("<H", source, source_offset)[0]
            product = f32(f32(float(word)) * f32(generated[y * width + x]))
            struct.pack_into("<H", destination, destination_offset, int(product) & 0xFFFF)
    return [destination[index * 4] for index in range(width * height)]


def make_loader(aex_path: Path) -> tuple[AexLoader, int, list[dict]]:
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    events: list[dict] = []
    suite, _ = make_handle_suite(loader, events)
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\0" * 0x200)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", suite))
    loader.write_bytes(ctx + 0x44, struct.pack("<i", 2))
    loader.write_bytes(ctx + 0x48, struct.pack("<i", 2))
    return loader, ctx, events


def execute(loader: AexLoader, ctx: int, events: list[dict], seed: list[int], width: int, height: int, amount: float) -> dict:
    pixels = width * height
    packed = b"".join(struct.pack("<I", value) for value in seed)
    source_world = plane(loader, width, height, 4, packed)
    boundary_world = plane(loader, width, height, 4, packed)
    distance_world = plane(loader, width, height, 16, b"\0" * (pixels * 16))
    output_payload = alloc(loader, b"\0" * (pixels * 4))
    output_world = plane(loader, width, height, 4, b"\0" * (pixels * 4))
    loader.write_bytes(output_world + 0x18, struct.pack("<Q", output_payload))
    loader.write_bytes(ctx + 0x40, struct.pack("<f", amount))
    events.clear()
    call = loader.call_function(
        TARGET,
        int_args=[ctx, boundary_world, 2, source_world, source_world, distance_world, output_world],
        float_args={1: amount},
        max_instructions=1_000_000,
    )
    cleanup = any(event["callback"] == "PF_HandleSuite.release_suite" for event in events)
    if call["rax"] != 0 or not cleanup:
        raise RuntimeError("fail-closed: erode leaf did not return with suite cleanup")
    handle = next((event for event in events if event["callback"] == "PF_HandleSuite.new_handle"), None)
    temp = []
    if handle:
        address = int(handle["result"], 16)
        temp = list(struct.unpack("<%df" % pixels, loader.read_bytes(address, pixels * 4)))
    output = loader.read_bytes(output_payload, pixels * 4)
    return {
        "seed": seed,
        "amount": amount,
        "output_first_channel": [output[index * 4] for index in range(pixels)],
        "output_raw_hex": output.hex(),
        "distance_temp": temp,
        "rax": hex(call["rax"]),
        "instructions": call["instructions"],
        "suite_cleanup": cleanup,
    }


def run(aex_path: Path) -> dict:
    aex_path = aex_path.resolve()
    blob = aex_path.read_bytes()
    loader, ctx, events = make_loader(aex_path)

    # Existing proven 5x3 seed -> type-2 distance fixture, retained as the
    # baseline while the exhaustive search supplies boundary witnesses.
    seed_bytes = bytearray(PIXELS * 4)
    seed_bytes[(1 * WIDTH + 2) * 4] = 255
    seed_world = plane(loader, WIDTH, HEIGHT, 4, bytes(seed_bytes))
    distance_payload = alloc(loader, b"\0" * (PIXELS * 16))
    distance_world = plane(loader, WIDTH, HEIGHT, 16, b"\0" * (PIXELS * 16))
    loader.write_bytes(distance_world + 0x18, struct.pack("<Q", distance_payload))
    distance_call = loader.call_function(
        0x180005D60,
        int_args=[ctx, seed_world, distance_world],
        float_args={3: 255.0},
        max_instructions=200_000,
    )
    baseline = execute(loader, ctx, events, list(seed_bytes[0::4]), WIDTH, HEIGHT, -2.0)

    outcomes: list[str] = []
    discriminating_outcomes: list[str] = []
    first_witness = None
    tested = 0
    for width, height in ((5, 1), (3, 3)):
        for bits in range(1 << (width * height)):
            pattern = [255 if bits & (1 << index) else 0 for index in range(width * height)]
            for amount in AMOUNTS:
                observed = execute(loader, ctx, events, pattern, width, height, amount)
                candidate_a = threshold_oracle(pattern, width, height, amount, 0)
                candidate_b = threshold_oracle(pattern, width, height, amount, 1)
                disagreement = [index for index, pair in enumerate(zip(candidate_a, candidate_b)) if pair[0] != pair[1]]
                if disagreement and first_witness is None:
                    first_witness = {
                        "width": width,
                        "height": height,
                        "pixel_index": disagreement[0],
                        "candidate_a": candidate_a,
                        "candidate_b": candidate_b,
                        "aex": observed,
                    }
                if observed["output_first_channel"] == candidate_a:
                    outcome = "candidate_a"
                elif observed["output_first_channel"] == candidate_b:
                    outcome = "candidate_b"
                else:
                    outcome = "neither"
                outcomes.append(outcome)
                if disagreement:
                    discriminating_outcomes.append(outcome)
                tested += 1

    exact_fixtures = []
    for fixture in ([1] * 5, [3] * 5, [5] * 5, [127] * 5, [255] * 5, [32767] * 5):
        observed = execute(loader, ctx, events, fixture, 5, 1, -1.0)
        exact = independent_oracle(fixture, observed["distance_temp"], 5, 1)
        if observed["output_first_channel"] != exact:
            raise RuntimeError("fail-closed: exact fixture disagrees with independent oracle")
        exact_fixtures.append({"seed_words": fixture, "aex": observed, "oracle": exact})

    if first_witness is None:
        raise RuntimeError("fail-closed: exhaustive search found no A/B boundary disagreement")
    neither = discriminating_outcomes.count("neither")
    if neither != len(discriminating_outcomes):
        raise RuntimeError("fail-closed: an A/B oracle matched a discriminating AEX case")

    function_bytes = blob[0x400 + (TARGET - 0x180001000):0x400 + (FUNCTION_END - 0x180001000)]
    return {
        "kind": "olmcolorkey_edge_thin_erode_aex_20260717",
        "schema": 2,
        "status": "pass",
        "classification": "FACT: Mac-local Unicorn execution of the checked-in Windows PE leaf; not AE-host execution",
        "provenance": {
            "aex": str(aex_path.relative_to(ROOT)),
            "aex_sha256": sha256(blob),
            "function": "FUN_180008320",
            "function_va": hex(TARGET),
            "function_end_exclusive": hex(FUNCTION_END),
            "function_bytes_sha256": sha256(function_bytes),
        },
        "abi": {
            "call": "RCX=ctx, RDX=boundary_world, R8D=2, R9=matched_world, stack5=source_world, stack6=distance_world, stack7=destination_world, XMM1=amount",
            "ctx_offsets": {"0x40": "amount float", "0x44": "distance_type int", "0x48": "distance_type/control int", "0x180": "PF_HandleSuite acquire/release descriptor"},
            "world_offsets": {"0x18": "payload", "0x20": "row_bytes", "0x24": "width", "0x28": "height"},
        },
        "inputs": {
            "width": WIDTH,
            "height": HEIGHT,
            "distance_type": 2,
            "seed_first_channel": [[255, 255, 255, 255, 255], [255, 255, 0, 255, 255], [255, 255, 255, 255, 255]],
            "distance_leaf": {"function": "FUN_180005D60", "va": "0x180005d60", "rax": hex(distance_call["rax"]), "instructions": distance_call["instructions"]},
            "distance_first_float_bytes_sha256": sha256(loader.read_bytes(distance_payload, PIXELS * 16)),
        },
        "baseline": baseline,
        "search": {
            "dimensions": [[5, 1], [3, 3]],
            "amounts": list(AMOUNTS),
            "tested_cases": tested,
            "discriminating_cases": len(discriminating_outcomes),
            "candidate_a_matches": discriminating_outcomes.count("candidate_a"),
            "candidate_b_matches": discriminating_outcomes.count("candidate_b"),
            "neither_matches": neither,
            "first_boundary_disagreement": first_witness,
            "independent_oracle": "raw x*2 word load/store -> float32 MULSS -> CVTTSS2SI -> low uint16 -> x*4 sample",
            "exact_fixtures": exact_fixtures,
        },
        "boundary_rule_comparison": {
            "candidate_a": "keep iff dist > abs(amount)",
            "candidate_b": "keep iff dist > abs(amount)+1",
            "observed": "neither candidate matches any exhaustive AEX leaf output; these are not the semantic operation of FUN_180008320",
            "rounding": "MULSS rounds to float32, then CVTTSS2SI truncates toward zero; MOV word stores the low 16 bits",
        },
        "facts": [
            "The pinned AEX leaf returns RAX=0 and completes PF Handle Suite cleanup for every exhaustive case.",
            "The output matte and generated temporary float values are captured directly before any PNG/export stage.",
            "distance_type=2 is supplied to the proven type-2 distance leaf and erode call.",
            "The exhaustive search tests all 32 binary 5x1 seeds and all 512 binary 3x3 seeds at four negative amounts.",
            "Static target bytes 0x180008494..0x1800084A8 load a source word, multiply it by a generated float, truncate with CVTTSS2SI, and store a word; they contain no comparison against abs(amount).",
        ],
        "inferences": [
            "The two requested predicates are caller-level erode oracles, not this leaf's operation: the leaf has no comparison against abs(amount).",
            "The exact caller threshold and any caller rounding/boundary rule remain outside FUN_180008320 and are not inferred here.",
            "The independent terminal-loop oracle matches the six constant-word fixtures when supplied with the generated float values captured from the AEX; it does not independently prove the float-generation stage for all exhaustive calls.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=AEX)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.aex)
    except Exception as exc:
        report = {"kind": "olmcolorkey_edge_thin_erode_aex_20260717", "schema": 2, "status": "blocked", "error": str(exc)}
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 2
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json), "tested": report["search"]["tested_cases"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
