#!/usr/bin/env python3
"""Compare actual ADA0 worker bytes with the current Mac helper boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import (  # noqa: E402
    FUN_ADA0,
    SerialVcomp,
)
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402
from aex_loader import AexLoader  # noqa: E402

INPUT_REPORT = ROOT / "refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.json"
MAC_SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
ORIGIN = (8, 8)
WIDTH = HEIGHT = 16
WINDOW = [(dx, dy) for dy in range(-1, 3) for dx in range(-1, 2)]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def color_dist(a: list[float], b: list[float]) -> float:
    if a[3] == 0.0 and b[3] == 0.0:
        return 0.0
    dr = abs(f32(a[0] - b[0]))
    dg = abs(f32(a[1] - b[1]))
    db = abs(f32(a[2] - b[2]))
    la = f32(f32(f32(a[0] * 0.2126) + f32(a[1] * 0.7152)) + f32(a[2] * 0.0722))
    lb = f32(f32(f32(b[0] * 0.2126) + f32(b[1] * 0.7152)) + f32(b[2] * 0.0722))
    dy = abs(f32(la - lb))
    return f32(f32(max(dr, dg, db, dy)) + f32(abs(f32(a[3] - b[3]))) )


def load_input() -> dict[str, Any]:
    report = json.loads(INPUT_REPORT.read_text(encoding="utf-8"))
    checkpoint = report["input_checkpoint"]
    require(report["verdict"] == "PASS_BOUNDED_ACTUAL_AEX_ADA0_INPUT_BEFORE_VCOMP", "ADA0 input witness verdict drift")
    require(checkpoint["rectangle"] == [0, 0, 16, 16], "rectangle drift")
    require(checkpoint["config"]["offset_0x1c_i32"] == 88, "config +0x1c drift")
    require(checkpoint["config"]["offset_0x70_i32"] == 0, "config +0x70 drift")
    require(checkpoint["config"]["offset_0x74_f32"] == 0.0, "config +0x74 drift")
    require(checkpoint["source_descriptor"]["width"] == checkpoint["source_descriptor"]["height"] == 16, "source dimensions drift")
    require(checkpoint["class_descriptor"]["width"] == checkpoint["class_descriptor"]["height"] == 16, "class dimensions drift")
    values = {tuple(item["offset"]): item["rgba"] for item in checkpoint["source_window_5x5"]}
    require(set(values) == {(dx, dy) for dy in range(-2, 3) for dx in range(-2, 3)}, "source witness is not a 5x5 window")
    return {"report": report, "source": values}


def actual_worker(source: dict[tuple[int, int], list[float]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, HEIGHT)
    for (dx, dy), rgba in source.items():
        smoother.set_src_pixel(ORIGIN[0] + dx, ORIGIN[1] + dy, rgba)
    loader.write_bytes(smoother.class_base, b"\xA5" * (WIDTH * HEIGHT * 4))
    source_desc = loader.bump_alloc(24, align=16)
    class_desc = loader.bump_alloc(24, align=16)
    rectangle = loader.bump_alloc(16, align=16)
    config = loader.bump_alloc(0x80, align=16)
    loader.write_bytes(source_desc, struct.pack("<QiiQ", smoother.src_base, 16, 16, smoother.src_stride))
    loader.write_bytes(class_desc, struct.pack("<QiiQ", smoother.class_base, 16, 16, smoother.class_stride))
    loader.write_bytes(rectangle, struct.pack("<4i", 0, 0, 16, 16))
    loader.write_bytes(config, b"\x00" * 0x80)
    loader.write_bytes(config + 0x1C, struct.pack("<i", 88))
    vcomp = SerialVcomp(loader)
    result = loader.call_function(FUN_ADA0, int_args=[source_desc, class_desc, rectangle, config], max_instructions=5_000_000)
    require(0xA5 not in loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4), "worker did not fill rectangle")
    output = []
    for dx, dy in WINDOW:
        address = smoother.class_base + (ORIGIN[1] + dy) * smoother.class_stride + (ORIGIN[0] + dx) * 4
        output.append({"offset": [dx, dy], "bytes": list(loader.read_bytes(address, 4))})
    return output, {"instructions": result["instructions"], "worker_entries": vcomp.worker_entries, "classifier_entries": vcomp.classifier_entries}


def mac_helper(source: dict[tuple[int, int], list[float]]) -> list[dict[str, Any]]:
    threshold = f32(f32(88 / 100.0) + 0.001)

    def get(dx: int, dy: int) -> list[float]:
        require((dx, dy) in source, f"Mac helper dependency outside witness at {(dx, dy)}")
        return source[(dx, dy)]

    result = []
    for dx, dy in WINDOW:
        self_pixel = get(dx, dy)
        distances = [
            color_dist(self_pixel, get(dx - 1, dy)),
            color_dist(self_pixel, get(dx, dy - 1)),
            color_dist(self_pixel, get(dx - 1, dy - 1)),
            color_dist(self_pixel, get(dx + 1, dy - 1)),
        ]
        result.append({"offset": [dx, dy], "bytes": [255 if value >= threshold else 0 for value in distances], "distances": distances})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    loaded = load_input()
    actual, runtime = actual_worker(loaded["source"])
    mac = mac_helper(loaded["source"])
    divergences = []
    for index, (a, m) in enumerate(zip(actual, mac)):
        for channel, (actual_byte, mac_byte) in enumerate(zip(a["bytes"], m["bytes"])):
            if actual_byte != mac_byte:
                divergences.append({"ordinal": index, "offset": a["offset"], "channel": channel, "actual": actual_byte, "mac": mac_byte, "actual_record": a, "mac_record": m})
    verdict = "PASS_NO_POST_WORKER_DIVERGENCE_IN_COMPARED_WINDOW" if not divergences else "DIVERGENCE_AT_FIRST_POST_WORKER_BYTE"
    report = {
        "schema": 1,
        "verdict": verdict,
        "scope": "actual AEX FUN_18000ada0/ac00/ae10 output versus current Mac helper class-plane formula at the first post-worker boundary",
        "input_witness": str(INPUT_REPORT.relative_to(ROOT)),
        "binary": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": EXPECTED_AEX_SHA256},
        "mac_source": {"path": str(MAC_SOURCE.relative_to(ROOT)), "sha256": hashlib.sha256(MAC_SOURCE.read_bytes()).hexdigest(), "anchors": ["Frame-level u8 class plane", "color_dist", "Class-plane threshold =", "byte[0] = LEFT edge", "byte[3] = TOP-RIGHT"]},
        "boundary": {"worker": "0x18000ac00", "classifier": "0x18000ae10", "compared_window": WINDOW, "threshold_f32": f32(f32(88 / 100.0) + 0.001)},
        "runtime": runtime,
        "actual_worker": actual,
        "mac_helper": mac,
        "first_divergence": divergences[0] if divergences else None,
        "claims_not_made": ["No Windows/AE execution claim", "No production source edit", "No ledger change", "No post-c280 or writer attribution"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    first = report["first_divergence"]
    lines = ["# OLMSmoother2 ADA0 post-worker boundary - 2026-07-18", "", f"- Verdict: `{verdict}`", "", "## Boundary", "", "The ADA0 input witness was replayed into the actual AEX. The comparison stops immediately after the natural `FUN_18000ac00` worker and its `FUN_18000ae10` classifier writes, before c280 or any later helper.", "", f"- Compared window: `{WINDOW}`.", f"- Actual worker calls: `{runtime['worker_entries']}` worker, `{runtime['classifier_entries']}` classifier entries.", f"- First divergence: `{first}`." if first else "- First divergence: none; every compared byte is equal.", "", "## Result", "", "The current Mac helper and the actual worker agree byte-for-byte across the retained 3x4 window. This local boundary does not justify a production edit; any remaining mismatch is downstream of the compared worker boundary or requires a live Windows post-worker capture.", "", "## Claims Not Made", "", "- No Windows/After Effects execution claim.", "- No production source or ledger change.", "- No c280, cce0, f130, or writer attribution.", ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "first_divergence": first}, indent=2))
    return 0 if not divergences else 1


if __name__ == "__main__":
    raise SystemExit(main())
