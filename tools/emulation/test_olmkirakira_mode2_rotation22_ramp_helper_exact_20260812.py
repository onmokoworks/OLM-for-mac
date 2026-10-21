#!/usr/bin/env python3
"""Localize the Rotation-22 PF32 seam around actual AEX owner preparation."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "tools/emulation/test_olmkirakira_mode2_ramp_actual_aex_boundary_20260805.py"
OUT = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_ramp_helper_exact_20260812.json"
DOC = OUT.with_suffix(".md")
OUTER = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"
PF32_COMPOSE = 0x18114E460
RAY_HEX = (
    "8c5d9e3e0ca8853ec370563e118a223eb692e53dfa74b03ec86caf3ee4ecb23e"
    "661ca93ee2078c3e9dee313ec5147b3e95d5a73ec0b1b93ead7fc03e"
)
STOPS = [
    [0.0, 1.0, 1.0, 0.0, 0.0],
    [0.7799999713897705, 1.0, 1.0, 0.6510000228881836, 0.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def load_boundary():
    spec = importlib.util.spec_from_file_location("kira_ramp_boundary", BOUNDARY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_outer():
    spec = importlib.util.spec_from_file_location("kira_outer", OUTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def from_bits(words: list[str]) -> tuple[float, ...]:
    return tuple(struct.unpack("<f", struct.pack("<I", int(word, 16)))[0] for word in words)


def direct_pf32_compose(boundary, outer, glow: list[float]) -> dict[str, object]:
    source = []
    for index in range(15):
        source.extend((
            f32(index * 15 / 255.0), f32(index * 11 / 255.0),
            f32(index * 7 / 255.0), f32((64 + index * 11) / 255.0),
        ))
    loader = boundary.AexLoader(str(boundary.AEX), verbose=False, fast=True)
    glow_ptr = loader.host_alloc(len(glow) * 4)
    loader.write_bytes(glow_ptr, struct.pack(f"<{len(glow)}f", *glow))
    source_ptr = loader.host_alloc(len(source) * 4)
    loader.write_bytes(source_ptr, struct.pack(f"<{len(source)}f", *source))
    owner = loader.host_alloc(0x200)
    loader.write_bytes(owner, bytes(0x200))
    loader.write_bytes(owner + 0x38, struct.pack("<f", 1.0))
    loader.write_bytes(owner + 0x3C, struct.pack("<f", 1.0))
    loader.write_bytes(owner + 0x44, struct.pack("<i", 2))
    loader.write_bytes(owner + 0x58, struct.pack("<i", 15))
    loader.write_bytes(owner + 0x128, struct.pack("<Q", source_ptr))
    loader.write_bytes(owner + 0x190, struct.pack("<Q", glow_ptr))
    output = loader.host_alloc(15 * 16)
    loader.write_bytes(output, bytes(15 * 16))
    world = loader.host_alloc(0x40)
    loader.write_bytes(world, bytes(0x40))
    loader.write_bytes(world + 0x18, struct.pack("<Q", output))
    # The direct typed owner fixture is a flat span. Geometry/row traversal is
    # exercised separately by the exported-owner gate.
    loader.write_bytes(world + 0x20, struct.pack("<i", 15 * 16))
    loader.write_bytes(world + 0x24, struct.pack("<i", 15))
    loader.write_bytes(world + 0x28, struct.pack("<i", 1))
    loader.call_function(PF32_COMPOSE, [owner, world], max_instructions=500_000)
    actual = loader.read_bytes(output, 15 * 16)
    portable = b"".join(
        outer.stage_typed_writer(
            outer.compose_pixel(
                glow[index * 4:index * 4 + 4], source[index * 4:index * 4 + 4],
                glow_opacity=1.0, source_opacity=1.0, merge_mode=2,
            ),
            depth="PF32",
        )
        for index in range(15)
    )
    return {
        "target": hex(PF32_COMPOSE),
        "bytes": len(actual),
        "exact": actual == portable,
        "actual_hex": actual.hex(),
        "portable_hex": portable.hex(),
    }


def portable_sample(amount: float) -> list[str]:
    lower, upper = STOPS[0], STOPS[1]
    t = f32(f32(amount - lower[0]) / f32(upper[0] - lower[0]))
    channels = []
    for field in range(2, 5):
        delta = f32(f32(upper[field] - lower[field]) * t)
        channels.append(bits(f32(lower[field] + delta)))
    return channels + [bits(amount)]


def main() -> int:
    boundary = load_boundary()
    outer = load_outer()
    aex_sha256 = hashlib.sha256(boundary.AEX.read_bytes()).hexdigest()
    if aex_sha256 != boundary.EXPECTED_SHA:
        raise RuntimeError(f"unexpected OLMKiraKira AEX identity: {aex_sha256}")
    rays = struct.unpack("<15f", bytes.fromhex(RAY_HEX))
    scale = f32(0.73)
    rows = []
    for index, ray in enumerate(rays):
        scaled = f32(ray * scale)
        actual = boundary.run_case(scaled, True, STOPS)["output_rgba_f32_bits"]
        portable = portable_sample(scaled)
        rows.append({
            "word": index,
            "ray": bits(ray),
            "scaled_ray": bits(scaled),
            "actual_aex_rgba": actual,
            "portable_rgba": portable,
            "exact": actual == portable,
        })
    aggregation_exact = all(row["exact"] for row in rows)
    glow = [component for row in rows for component in from_bits(row["actual_aex_rgba"])]
    compose = direct_pf32_compose(boundary, outer, glow)
    exact = aggregation_exact and compose["exact"]
    report = {
        "kind": "olmkirakira_mode2_rotation22_ramp_helper_exact",
        "date": "2026-08-12",
        "status": "exact" if exact else "mismatch",
        "aex_sha256": aex_sha256,
        "scope": "15 Rotation-22 horizontal ray words, float32 Brightness Gain 0.73, default three-stop Ramp",
        "actual_aex_targets": {
            "mode2_aggregator": hex(boundary.TARGET),
            "ramp_helper_reached_by_aggregator": hex(boundary.RAMP_HELPER),
            "pf32_compose_writer": hex(PF32_COMPOSE),
        },
        "static_abi_boundary": {
            "brightness_transport": "float32 MOVSS trailing owner argument",
            "mode2_aggregator": "FUN_18114ffd0 consumes raw plane floats and does not read or multiply the trailing Brightness argument",
            "required_next_capture": "natural exported FUN_181232080 entry XMM2 plus five plane pointers/flags/Ramp payload",
        },
        "rows": rows,
        "direct_pf32_compose_writer": compose,
        "conclusion": (
            "The direct actual-AEX Mode-2 aggregator (including Ramp helper dispatch) and the "
            "portable SSE-ordered path are 15/15 exact for the constructed inputs. Feeding those "
            "glow words and the declared source into the direct actual-AEX PF32 compose/writer is "
            "also byte exact. The remaining exported PF32 seam is localized to natural-owner "
            "state/arguments at or before the aggregator invocation; a natural-entry argument "
            "capture is still required to distinguish Brightness arithmetic, input planes, flags, "
            "and Ramp payload setup."
        ),
        "claims_not_made": [
            "No arbitrary Ramp payload or geometry generalization",
            "No correction of the remaining exported PF32 word",
            "No expected-word substitution",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Mode 2 Rotation 22° Ramp helper boundary（2026-08-12）\n\n"
        f"Status: **{report['status']}**\n\n"
        "Rotation 22°の15 ray wordsをBrightness Gain 0.73でfloat32 scaleし、default Rampとともに"
        "actual AEX Mode 2 aggregatorへ直接入力した。Ramp helperを含む15/15 RGBAがportable SSE順序と"
        "raw exactで、同じglowをactual AEX PF32 compose/writerへ渡した240 bytesもexact。残るPF32 seamは"
        "natural ownerのstate／実引数からaggregator呼出しまでに局在する。Brightness、plane、flags、Ramp payloadの"
        "どれかを確定するにはnatural-entry captureが必要。"
        "期待値補正や未証明範囲のpromotionは行わない。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "aggregate_exact": sum(r["exact"] for r in rows),
                      "total": len(rows), "pf32_compose_exact": compose["exact"]}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
