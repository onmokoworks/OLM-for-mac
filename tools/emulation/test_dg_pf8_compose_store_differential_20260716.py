#!/usr/bin/env python3
"""Fail-closed PF8 compose/store differential at DG +0x1170870.

The field and source worlds are Mac-side fixture inputs. This runner does not
execute or compare DistanceGradation field generation. It compares only the
actual-AEX compose/store callback with the current Mac portable model.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_XMM1, UC_X86_REG_XMM3, UC_X86_REG_XMM5, UC_X86_REG_XMM6

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
from test_dg_compose import (  # noqa: E402
    WORLD_DATA_PTR,
    WORLD_HEIGHT,
    WORLD_ROWBYTES,
    WORLD_WIDTH,
    alloc_refcon,
)

AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
EXPECTED_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
CALLBACK = 0x181170870
FIELD_READ = 0x18117098F
SOURCE_READ = 0x181170A09
PRE_U8 = 0x181170C20
POST_STORE = 0x181170C40
WIDTH, HEIGHT, ROWBYTES = 1024, 512, 4096
POINTS = ((17, 0), (780, 495), (987, 496))

# Memory order is A,G,R,B, matching PF_Pixel8 and the callback stores.
MAC_FIXTURE = {
    (17, 0): {"field": (255, 2, 0, 0), "source": (57, 0, 0, 57)},
    (780, 495): {"field": (10, 10, 0, 0), "source": (10, 10, 0, 0)},
    (987, 496): {"field": (64, 64, 0, 0), "source": (64, 28, 0, 238)},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(loader: AexLoader, reg: int) -> float:
    return struct.unpack("<f", loader.uc.reg_read(reg).to_bytes(16, "little")[:4])[0]


def world_data(loader: AexLoader, world: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(world + WORLD_DATA_PTR, 8))[0]


def build_world8(loader: AexLoader, pixels: dict[tuple[int, int], tuple[int, int, int, int]]) -> int:
    data = loader.bump_alloc(ROWBYTES * HEIGHT, align=64)
    loader.write_bytes(data, b"\x00" * (ROWBYTES * HEIGHT))
    for (x, y), values in pixels.items():
        loader.write_bytes(data + y * ROWBYTES + x * 4, bytes(values))
    world = loader.host_alloc(0x80, align=16)
    loader.write_bytes(world, b"\x00" * 0x80)
    loader.write_bytes(world + WORLD_DATA_PTR, struct.pack("<Q", data))
    loader.write_bytes(world + WORLD_ROWBYTES, struct.pack("<I", ROWBYTES))
    loader.write_bytes(world + WORLD_WIDTH, struct.pack("<I", WIDTH))
    loader.write_bytes(world + WORLD_HEIGHT, struct.pack("<I", HEIGHT))
    return world


def validate_world(loader: AexLoader, world: int, expected: dict[tuple[int, int], tuple[int, int, int, int]]) -> dict[str, object]:
    data = world_data(loader, world)
    rowbytes = struct.unpack("<I", loader.read_bytes(world + WORLD_ROWBYTES, 4))[0]
    width = struct.unpack("<I", loader.read_bytes(world + WORLD_WIDTH, 4))[0]
    height = struct.unpack("<I", loader.read_bytes(world + WORLD_HEIGHT, 4))[0]
    checks = []
    for (x, y), values in expected.items():
        address = data + y * rowbytes + x * 4
        actual = tuple(loader.read_bytes(address, 4))
        checks.append({"xy": [x, y], "address": hex(address), "expected": list(values), "actual": list(actual), "match": actual == values})
    return {
        "world": hex(world), "data": hex(data), "width": width, "height": height,
        "rowbytes": rowbytes, "geometry_match": (width, height, rowbytes) == (WIDTH, HEIGHT, ROWBYTES),
        "readback": checks, "readback_match": all(item["match"] for item in checks),
    }


def make_refcon(loader: AexLoader, field_world: int, source_world: int) -> int:
    refcon = alloc_refcon(loader)
    loader.write_bytes(refcon + 0x00, struct.pack("<Q", source_world))
    loader.write_bytes(refcon + 0x08, struct.pack("<Q", field_world))
    loader.write_bytes(refcon + 0x94, struct.pack("<i", 3))
    for offset, value in ((0x9C, 0.22), (0xA0, 0.91), (0xA4, 0.08),
                          (0xAC, 0.03), (0xB0, 0.80), (0xB4, 0.12)):
        loader.write_bytes(refcon + offset, struct.pack("<f", value))
    loader.write_bytes(refcon + 0xC0, b"\x01")
    loader.write_bytes(refcon + 0xC1, b"\x00")
    loader.write_bytes(refcon + 0xC8, struct.pack("<i", 1))
    loader.write_bytes(refcon + 0xCC, struct.pack("<i", 1))
    return refcon


def portable_model(field: tuple[int, int, int, int], source: tuple[int, int, int, int]) -> dict[str, object]:
    field_x = field[1] / 255.0
    x = 1.0 - field_x
    sa, sr, sg, sb = (value / 255.0 for value in source)
    del sa, sr, sg, sb
    out_a = 1.0
    out_r = (1.0 - x) * 0.80 + x * 0.91
    out_g = (1.0 - x) * 0.03 + x * 0.22
    out_b = (1.0 - x) * 0.12 + x * 0.08
    pre = (out_a * 255.0, out_g * 255.0, out_r * 255.0, out_b * 255.0)
    stored = tuple(max(0, min(255, int(value))) for value in pre)
    return {"field_x": field_x, "pre_u8_agrb": list(pre), "stored_agrb": list(stored)}


def canonical_pre_u8(register_lanes: list[float]) -> list[float]:
    """Convert the captured C20 lanes to scaled A,G,R,B units.

    The actual callback's C20 register lanes are [G*255, B*255, R, A*255].
    Keeping the raw lanes and this canonical conversion prevents a normalized
    red lane from being compared directly with byte-scaled channels.
    """
    green, blue, red_norm, alpha = register_lanes
    return [alpha, green, red_norm * 255.0, blue]


def run() -> dict[str, object]:
    actual_hash = sha256(AEX)
    report: dict[str, object] = {
        "schema": "olmdistancegradation.pf8-compose-store-differential/1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "fail_closed",
        "scope": "compose/store only; not AEX field generation",
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": actual_hash,
                   "expected_sha256": EXPECTED_SHA256, "hash_match": actual_hash == EXPECTED_SHA256,
                   "entry_rva": hex(0x1170870), "entry_va": hex(CALLBACK)},
        "fixture": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES,
                    "pixel_size": 4, "world_contract": "test_dg_compose.py PF_EffectWorld offsets",
                    "field_and_source_generation_compared": False,
                    "points": [list(point) for point in POINTS]},
        "points": [],
    }
    if actual_hash != EXPECTED_SHA256:
        return report

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    field_pixels = {point: MAC_FIXTURE[point]["field"] for point in POINTS}
    source_pixels = {point: MAC_FIXTURE[point]["source"] for point in POINTS}
    field_world = build_world8(loader, field_pixels)
    source_world = build_world8(loader, source_pixels)
    field_validation = validate_world(loader, field_world, field_pixels)
    source_validation = validate_world(loader, source_world, source_pixels)
    report["fixture"]["field_world_validation"] = field_validation
    report["fixture"]["source_world_validation"] = source_validation
    if not (field_validation["geometry_match"] and source_validation["geometry_match"] and
            field_validation["readback_match"] and source_validation["readback_match"]):
        report["conclusion"] = {"fact": "Fixture geometry or readback did not match before AEX execution.", "field_generation_claim": False}
        return report
    refcon = make_refcon(loader, field_world, source_world)
    field_base, source_base = world_data(loader, field_world), world_data(loader, source_world)
    records = []
    active_stages: list[str] = []
    active_pre: list[float] | None = None

    def hook(ld: AexLoader, rip: int, _size: int) -> None:
        nonlocal active_pre
        if rip == FIELD_READ:
            active_stages.append("field_read")
        elif rip == SOURCE_READ:
            active_stages.append("source_read")
        elif rip == PRE_U8:
            active_stages.append("pre_u8")
            active_pre = [f32(ld, reg) for reg in (UC_X86_REG_XMM1, UC_X86_REG_XMM3, UC_X86_REG_XMM5, UC_X86_REG_XMM6)]
        elif rip == POST_STORE:
            active_stages.append("post_store")

    for rip in (FIELD_READ, SOURCE_READ, PRE_U8, POST_STORE):
        loader.add_code_hook(rip, hook)
    for x, y in POINTS:
        output = loader.bump_alloc(4, align=16)
        loader.write_bytes(output, b"\xee" * 4)
        active_stages.clear()
        active_pre = None
        loader.call_function(CALLBACK, int_args=[refcon, x, y, 0, output], max_instructions=200_000)
        field_addr = field_base + y * ROWBYTES + x * 4
        source_addr = source_base + y * ROWBYTES + x * 4
        field_bytes = list(loader.read_bytes(field_addr, 4))
        source_bytes = list(loader.read_bytes(source_addr, 4))
        actual = list(loader.read_bytes(output, 4))
        model = portable_model(tuple(field_bytes), tuple(source_bytes))
        actual_pre = canonical_pre_u8(active_pre) if active_pre is not None else None
        pre_match = actual_pre is not None and all(abs(a - b) <= 1e-3 for a, b in zip(actual_pre, model["pre_u8_agrb"]))
        stages_match = active_stages == ["field_read", "source_read", "pre_u8", "post_store"]
        record = {
            "xy": [x, y], "field_addr": hex(field_addr), "source_addr": hex(source_addr),
            "output_addr": hex(output), "field_bytes_agrb": field_bytes,
            "source_bytes_agrb": source_bytes, "actual_pre_u8_register_lanes": active_pre,
            "actual_pre_u8_agrb": actual_pre,
            "actual_output_bytes_agrb": actual, "portable_pre_u8_agrb": model["pre_u8_agrb"],
            "portable_output_bytes_agrb": model["stored_agrb"], "stages": list(active_stages),
            "pre_u8_match": pre_match, "stages_match": stages_match,
            "store_match": actual == model["stored_agrb"],
            "match": pre_match and stages_match and actual == model["stored_agrb"],
        }
        records.append(record)
    report["points"] = records
    report["status"] = "pass" if all(record["match"] for record in records) else "fail_closed"
    report["conclusion"] = {
        "actual_aex_and_portable_model_match": report["status"] == "pass",
        "field_generation_claim": False,
        "fact": "The same injected field/source bytes produced matching actual-AEX and portable compose/store bytes.",
        "inference": "Any unexplained external render residual remains upstream of this injected compose/store comparison or outside this bounded callback.",
    }
    return report


def main() -> int:
    report = run()
    out_json = ROOT / "refs/conformance/olmdistancegradation_pf8_compose_store_differential_20260716.json"
    out_md = ROOT / "refs/conformance/olmdistancegradation_pf8_compose_store_differential_20260716.md"
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OLMDistanceGradation PF8 compose/store differential",
        "",
        f"- Status: `{report['status']}`",
        "- Scope: **compose/store only; not AEX field generation**.",
        f"- AEX SHA-256: `{report['binary']['sha256']}`; hash pin match: `{report['binary']['hash_match']}`.",
        f"- Fixture: `{WIDTH}x{HEIGHT}`, rowbytes `{ROWBYTES}`, entry `B+0x1170870`.",
        "- The three points use identical injected Mac-side field and source ARGB bytes in both lanes.",
        "",
        "## FACT",
        "",
        "- Actual-AEX PF8 callback execution and the portable/current Mac compose/store model were run in the same local test.",
        "- The report records field/source addresses and bytes, pre-U8 compose floats, converted bytes, and final output bytes.",
        "",
        "## INFERENCE",
        "",
        "- A passing result bounds agreement to compose/store for these injected inputs; it does not validate AEX field generation or AE-host output.",
        "- A hash mismatch or any missing stage/mismatch leaves the result `fail_closed`.",
        "",
        "## Smoke",
        "",
        "- Command: `python3 tools/emulation/test_dg_pf8_compose_store_differential_20260716.py`",
        f"- Result: `{report['status']}`.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
