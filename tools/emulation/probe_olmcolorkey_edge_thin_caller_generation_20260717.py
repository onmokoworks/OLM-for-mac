#!/usr/bin/env python3
"""Static caller ABI plus connected ColorKey Edge Thin AEX stage probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASM = ROOT / "disasm/OLMColorKey.aex.asm.txt"
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"

CALLER_16 = 0x180009000
CALLER_8 = 0x1800094B0
BOUNDARY_16 = 0x180008AD0
BOUNDARY_8 = 0x180008C90
DISTANCE_16_TYPE2 = 0x1800058A0
DISTANCE_8_TYPE2 = 0x180005D60
ERODE_16 = 0x180008320
HALF_VA = 0x18001F754

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from probe_olmcolorkey_boundary_to_distance_actual_aex_20260716 import alloc, plane  # noqa: E402
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import make_handle_suite  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def first_floats(raw: bytes, pixels: int, pixel_size: int) -> list[float]:
    return [struct.unpack_from("<f", raw, index * pixel_size)[0] for index in range(pixels)]


def portable_terminal(source: bytes, matched: bytes, generated: list[float],
                      width: int, height: int, sentinel: int = 0xCC) -> bytes:
    """Portable model of 0x18000847B..0x1800084A8 for PF_Pixel16 worlds."""
    output = bytearray([sentinel] * (width * height * 8))
    for index, scale in enumerate(generated):
        source_word = struct.unpack_from("<H", source, index * 8)[0]
        if source_word == 0 and f32(scale) != 0.0:
            source_word = struct.unpack_from("<H", matched, index * 8)[0]
        product = f32(f32(float(source_word)) * f32(scale))
        struct.pack_into("<H", output, index * 8, int(product) & 0xFFFF)
    return bytes(output)


def static_contract() -> dict[str, object]:
    instructions: dict[int, str] = {}
    for line in ASM.read_text(encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if parts and parts[0].startswith("180009"):
            instructions[int(parts[0], 16)] = parts[1].strip()

    required = {
        # FUN_180009000: the only immediate caller of FUN_180008320.
        0x180009154: "MOVSS XMM8,dword ptr [0x18001f754]",
        0x180009175: "CALL 0x180008ad0",
        0x1800091AC: "MOVAPS XMM3,XMM8",
        0x1800091BB: "CALL 0x1800058a0",
        0x1800093F5: "MOV qword ptr [RSP + 0x30],R12",
        0x1800093FA: "LEA RAX,[RBP + -0x10]",
        0x180009403: "LEA RAX,[RSP + 0x70]",
        0x18000940D: "MOV R9,R15",
        0x180009410: "MOV R8D,dword ptr [R14 + 0x48]",
        0x180009414: "MOVSS XMM1,dword ptr [R14 + 0x40]",
        0x18000941A: "MOV RCX,R13",
        0x18000941D: "CALL 0x180008320",
        # FUN_1800094B0: analogous 8-bit stage, but no call to 0x180008320.
        0x180009604: "MOVSS XMM8,dword ptr [0x18001f754]",
        0x180009625: "CALL 0x180008c90",
        0x18000965C: "MOVAPS XMM3,XMM8",
        0x18000966B: "CALL 0x180005d60",
    }
    matches = {hex(address): instructions.get(address, "") == text
               for address, text in required.items()}
    caller_8_lines = [text for address, text in instructions.items()
                      if CALLER_8 <= address < 0x180009960]
    caller_8_calls_erode = any("CALL 0x180008320" in text for text in caller_8_lines)
    return {
        "status": "pass" if all(matches.values()) and not caller_8_calls_erode else "blocked",
        "required_instruction_matches": matches,
        "caller_16": {
            "name": "FUN_180009000",
            "va": hex(CALLER_16),
            "role": "immediate caller of FUN_180008320",
            "type2_chain": "FUN_180008AD0 -> FUN_1800058A0(XMM3=contents of 0x18001F754) -> FUN_180008320",
            "leaf_abi": "RCX=ctx, RDX=work_world, R8D=control, R9=matched_world, stack5=work_world, stack6=distance_world, stack7=destination_world, XMM1=amount",
        },
        "caller_8": {
            "name": "FUN_1800094B0",
            "va": hex(CALLER_8),
            "role": "separate 8-bit stage with inline erode loops",
            "type2_chain": "FUN_180008C90 -> FUN_180005D60(XMM3=contents of 0x18001F754) -> inline threshold/write loops",
            "calls_FUN_180008320": caller_8_calls_erode,
        },
        "amount": "both callers forward dword [R14+0x40] without arithmetic; FUN_180009000 moves it directly to XMM1 at 0x180009414",
    }


def make_context(loader: AexLoader, max_value: int) -> int:
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\0" * 0x200)
    loader.write_bytes(ctx + 0x120, struct.pack("<i", max_value))
    loader.write_bytes(ctx + 0x128, struct.pack("<i", max_value))
    return ctx


def probe_8bit_stage(loader: AexLoader, distance_scale: float) -> dict[str, object]:
    """Execute only the static FUN_1800094B0 seed/distance stage boundary."""
    width, height = 5, 1
    pixels = width * height
    source = bytes([255, 0, 0, 0] * pixels)
    source_world = plane(loader, width, height, 4, source)
    boundary_payload = alloc(loader, b"\0" * (pixels * 4))
    boundary_world = plane(loader, width, height, 4, b"\0" * (pixels * 4))
    loader.write_bytes(boundary_world + 0x18, struct.pack("<Q", boundary_payload))
    boundary_call = loader.call_function(BOUNDARY_8, int_args=[source_world, boundary_world, 8],
                                         max_instructions=200_000)
    ctx = make_context(loader, 255)
    distance_payload = alloc(loader, b"\0" * (pixels * 16))
    distance_world = plane(loader, width, height, 16, b"\0" * (pixels * 16))
    loader.write_bytes(distance_world + 0x18, struct.pack("<Q", distance_payload))
    distance_call = loader.call_function(DISTANCE_8_TYPE2,
                                         int_args=[ctx, boundary_world, distance_world],
                                         float_args={3: distance_scale}, max_instructions=250_000)
    boundary_raw = loader.read_bytes(boundary_payload, pixels * 4)
    distance_raw = loader.read_bytes(distance_payload, pixels * 16)
    return {
        "classification": "independently executed 8-bit seed/distance stage; not connected to FUN_180008320",
        "xmm3": distance_scale,
        "boundary_rax": hex(boundary_call["rax"]),
        "distance_rax": hex(distance_call["rax"]),
        "boundary_sha256": sha256(boundary_raw),
        "distance_sha256": sha256(distance_raw),
        "distance_first_float": first_floats(distance_raw, pixels, 16),
    }


def probe_connected_16bit_pipeline(loader: AexLoader, distance_scale: float,
                                   classification: str) -> dict[str, object]:
    """Execute the true FUN_180009000 type-2 stage chain with connected worlds."""
    width, height = 5, 1
    pixels = width * height
    source_raw = b"".join(struct.pack("<4H", 32767, 0, 0, 0) for _ in range(pixels))
    matched_raw = b"".join(struct.pack("<4H", 12345, 0, 0, 0) for _ in range(pixels))
    source_world = plane(loader, width, height, 8, source_raw)
    matched_world = plane(loader, width, height, 8, matched_raw)

    boundary_payload = alloc(loader, b"\0" * (pixels * 8))
    boundary_world = plane(loader, width, height, 8, b"\0" * (pixels * 8))
    loader.write_bytes(boundary_world + 0x18, struct.pack("<Q", boundary_payload))
    boundary_call = loader.call_function(BOUNDARY_16, int_args=[source_world, boundary_world, 16],
                                         max_instructions=200_000)

    ctx = make_context(loader, 32768)
    distance_payload = alloc(loader, b"\0" * (pixels * 16))
    distance_world = plane(loader, width, height, 16, b"\0" * (pixels * 16))
    loader.write_bytes(distance_world + 0x18, struct.pack("<Q", distance_payload))
    distance_call = loader.call_function(DISTANCE_16_TYPE2,
                                         int_args=[ctx, boundary_world, distance_world],
                                         float_args={3: distance_scale}, max_instructions=250_000)
    distance_before = loader.read_bytes(distance_payload, pixels * 16)

    events: list[dict[str, object]] = []
    suite, _ = make_handle_suite(loader, events)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", suite))
    destination_initial = bytes([0xCC] * (pixels * 8))
    destination_payload = alloc(loader, destination_initial)
    destination_world = plane(loader, width, height, 8, destination_initial)
    loader.write_bytes(destination_world + 0x18, struct.pack("<Q", destination_payload))
    amount = -2.0
    loader.write_bytes(ctx + 0x40, struct.pack("<f", amount))
    leaf_call = loader.call_function(
        ERODE_16,
        int_args=[ctx, source_world, 2, matched_world, source_world,
                  distance_world, destination_world],
        float_args={1: amount},
        max_instructions=1_000_000,
    )
    distance_after = loader.read_bytes(distance_payload, pixels * 16)
    destination_actual = loader.read_bytes(destination_payload, pixels * 8)
    handle_event = next(event for event in events
                        if event["callback"] == "PF_HandleSuite.new_handle")
    generated_address = int(handle_event["result"], 16)
    generated = list(struct.unpack("<%df" % pixels,
                                   loader.read_bytes(generated_address, pixels * 4)))
    destination_oracle = portable_terminal(source_raw, matched_raw, generated,
                                           width, height)
    if distance_before != distance_after:
        raise RuntimeError("fail-closed: leaf mutated the connected distance world")
    if destination_actual != destination_oracle:
        raise RuntimeError("fail-closed: connected AEX output disagrees with portable terminal oracle")

    return {
        "classification": classification,
        "dimensions": [width, height],
        "xmm3_distance_scale": distance_scale,
        "amount_xmm1": amount,
        "control_r8d": 2,
        "world_layouts": {
            "work": {"pixel_bytes": 8, "row_bytes": width * 8},
            "boundary": {"pixel_bytes": 8, "row_bytes": width * 8},
            "distance": {"pixel_bytes": 16, "row_bytes": width * 16},
            "destination": {"pixel_bytes": 8, "row_bytes": width * 8},
        },
        "leaf_call_abi": {
            "RCX": "context",
            "RDX": "work_world",
            "R8D": 2,
            "R9": "matched_world",
            "stack5": "same work_world pointer as RDX",
            "stack6": "exact distance_world written by FUN_1800058A0",
            "stack7": "destination_world",
            "XMM1": amount,
        },
        "returns": {
            "boundary_rax": hex(boundary_call["rax"]),
            "distance_rax": hex(distance_call["rax"]),
            "leaf_rax": hex(leaf_call["rax"]),
            "leaf_instructions": leaf_call["instructions"],
        },
        "connected_evidence": {
            "source_sha256": sha256(source_raw),
            "boundary_sha256": sha256(loader.read_bytes(boundary_payload, pixels * 8)),
            "distance_before_leaf_sha256": sha256(distance_before),
            "distance_after_leaf_sha256": sha256(distance_after),
            "distance_identity_preserved": distance_before == distance_after,
            "distance_first_float": first_floats(distance_before, pixels, 16),
            "leaf_generated_float32": generated,
            "destination_initial_sha256": sha256(destination_initial),
            "destination_actual_hex": destination_actual.hex(),
            "destination_actual_sha256": sha256(destination_actual),
            "portable_oracle_hex": destination_oracle.hex(),
            "portable_oracle_sha256": sha256(destination_oracle),
            "actual_equals_oracle": destination_actual == destination_oracle,
        },
        "oracle_boundary": "portable oracle starts from the float32 buffer generated by the AEX leaf; it independently checks selection, MULSS float32 rounding, CVTTSS2SI truncation, low-word store, and untouched destination bytes, but does not independently derive that float buffer",
        "suite_callbacks": [event["callback"] for event in events],
    }


def run(aex_path: Path) -> dict[str, object]:
    aex_path = aex_path.resolve()
    blob = aex_path.read_bytes()
    static = static_contract()
    if sha256(blob) != AEX_SHA256 or static["status"] != "pass":
        raise RuntimeError("fail-closed: pinned AEX or static caller contract changed")

    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    constant_bytes = loader.read_bytes(HALF_VA, 4)
    caller_constant = struct.unpack("<f", constant_bytes)[0]
    stage_8 = probe_8bit_stage(loader, caller_constant)
    pipeline_16 = probe_connected_16bit_pipeline(
        loader, caller_constant,
        "connected independently invoked AEX stages matching the pinned FUN_180009000 caller constant; FUN_180009000 itself is not executed",
    )
    half_pipeline = probe_connected_16bit_pipeline(
        loader, 0.5,
        "connected audit-requested XMM3=0.5 diagnostic; this scale does not match the raw constant loaded by the pinned AEX caller",
    )
    return {
        "kind": "olmcolorkey_edge_thin_caller_generation_20260717",
        "schema": 2,
        "status": "pass_static_abi_connected_stage_probe",
        "classification": "static caller ABI plus independently invoked connected AEX stages under Mac-local Unicorn; neither caller function nor AE host is executed",
        "provenance": {
            "aex": str(aex_path.relative_to(ROOT)),
            "aex_sha256": sha256(blob),
            "asm": str(ASM.relative_to(ROOT)),
            "constant_0x18001f754_bytes_hex": constant_bytes.hex(),
            "constant_0x18001f754_float32": caller_constant,
            "audit_asserted_constant_float32": 0.5,
            "audit_assertion_matches_pinned_aex": caller_constant == 0.5,
        },
        "static_caller_contract": static,
        "independent_8bit_stage_probe": stage_8,
        "connected_16bit_pipeline": pipeline_16,
        "connected_half_scale_diagnostic": half_pipeline,
        "claim_boundary": "FACT: static FUN_180009000/FUN_1800094B0 ABI and connected direct stage execution. The pinned caller constant is reported from raw bytes; the separate 0.5 fixture is diagnostic only. No claim that either caller ran, no independent oracle for leaf float generation, no AE-host/PNG/AE-exact claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path,
                        default=ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex")
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.aex)
    except Exception as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, sort_keys=True))
        return 2
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.json)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
