#!/usr/bin/env python3
"""Capture the actual-AEX ADA0 input boundary before VCOMP fork.

This is a Mac-local witness over the retained 20260717 translated tuple.  It
does not claim that these pointers or bytes are the live Windows case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import (
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader  # noqa: E402
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import (  # noqa: E402
    CANARY,
    EXPECTED_AEX_SHA256,
    FUN_ADA0,
    ORIGIN,
    SerialVcomp,
    WIDTH,
    actual_window,
    expected_window,
    install_descriptors,
)
from test_smoother2_case0012_local_tuple import LOG_PATH, parse_log  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def unpack_desc(loader: AexLoader, address: int) -> dict[str, Any]:
    base, width, height, stride = struct.unpack("<QiiQ", loader.read_bytes(address, 24))
    return {"address": hex(address), "base": hex(base), "width": width, "height": height, "stride_bytes": stride}


def source_window(loader: AexLoader, descriptor: dict[str, Any]) -> list[dict[str, Any]]:
    base = int(descriptor["base"], 16)
    stride = descriptor["stride_bytes"]
    result = []
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            address = base + (ORIGIN[1] + dy) * stride + (ORIGIN[0] + dx) * 16
            rgba = struct.unpack("<4f", loader.read_bytes(address, 16))
            result.append({"offset": [dx, dy], "address": hex(address), "rgba": list(rgba)})
    return result


def capture_input(loader: AexLoader, observations: dict[str, Any]) -> None:
    source_ptr = loader.uc.reg_read(UC_X86_REG_RCX)
    class_ptr = loader.uc.reg_read(UC_X86_REG_RDX)
    rectangle_ptr = loader.uc.reg_read(UC_X86_REG_R8)
    config_ptr = loader.uc.reg_read(UC_X86_REG_R9)
    source = unpack_desc(loader, source_ptr)
    classes = unpack_desc(loader, class_ptr)
    rectangle = list(struct.unpack("<4i", loader.read_bytes(rectangle_ptr, 16)))
    config_bytes = loader.read_bytes(config_ptr, 0x80)
    observations.update({
        "entry": hex(FUN_ADA0),
        "registers": {"rcx": hex(source_ptr), "rdx": hex(class_ptr), "r8": hex(rectangle_ptr), "r9": hex(config_ptr)},
        "source_descriptor": source,
        "class_descriptor": classes,
        "rectangle": rectangle,
        "config": {
            "address": hex(config_ptr),
            "length": len(config_bytes),
            "bytes_hex": config_bytes.hex(),
            "offset_0x1c_i32": struct.unpack("<i", config_bytes[0x1c:0x20])[0],
            "offset_0x70_i32": struct.unpack("<i", config_bytes[0x70:0x74])[0],
            "offset_0x74_f32": struct.unpack("<f", config_bytes[0x74:0x78])[0],
        },
        "source_window_5x5": source_window(loader, source),
        "capture_point": "FUN_18000ada0 entry, before the ADA0 call to VCOMP140!_vcomp_fork",
    })


def run(tuple_data: dict[str, Any]) -> dict[str, Any]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    require(tuple_data["range"] == 88 and len(tuple_data["neighbors"]) == 25, "fixture changed")
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, WIDTH)
    loader.write_bytes(smoother.class_base, bytes([CANARY]) * (WIDTH * WIDTH * 4))
    for item in tuple_data["neighbors"]:
        dx, dy = item["offset"]
        smoother.set_src_pixel(ORIGIN[0] + dx, ORIGIN[1] + dy, item["setup"])
    source, classes, rectangle, config = install_descriptors(loader, smoother, tuple_data["range"])
    observations: dict[str, Any] = {}
    loader.add_code_hook(FUN_ADA0, lambda ld, _address, _size: capture_input(ld, observations))
    vcomp = SerialVcomp(loader)
    execution = loader.call_function(FUN_ADA0, int_args=[source, classes, rectangle, config], max_instructions=5_000_000)
    require("source_window_5x5" in observations, "ADA0 entry hook did not fire")
    generated = actual_window(loader, smoother)
    require(generated == expected_window(tuple_data), "generated class window changed")
    require(CANARY not in loader.read_bytes(smoother.class_base, WIDTH * WIDTH * 4), "class rectangle remained incomplete")
    require(len(vcomp.fork_events) == len(vcomp.static_events) == 1, "unexpected VCOMP boundary count")
    return {
        "verdict": "PASS_BOUNDED_ACTUAL_AEX_ADA0_INPUT_BEFORE_VCOMP",
        "scope": "Mac-local actual-AEX FUN_18000ada0 entry capture over the retained translated case0012 tuple",
        "binary": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": EXPECTED_AEX_SHA256},
        "fixture": {"source": str(LOG_PATH.relative_to(ROOT)), "host_origin": tuple_data["target_xy"], "translated_origin": list(ORIGIN), "smooth_range": tuple_data["range"]},
        "input_checkpoint": observations,
        "execution": {
            "instructions": execution["instructions"],
            "vcomp": {"fork": vcomp.fork_events, "static_schedule": vcomp.static_events},
            "worker_entries": vcomp.worker_entries,
            "classifier_entries": vcomp.classifier_entries,
            "generated_window_exact": True,
        },
        "claims_not_made": [
            "No live Windows pointer, source float, config, or rectangle value is claimed.",
            "No Windows or After Effects execution claim.",
            "No production source or ledger change.",
        ],
    }


def render(report: dict[str, Any]) -> str:
    checkpoint = report["input_checkpoint"]
    cfg = checkpoint["config"]
    return "\n".join([
        "# OLMSmoother2 case0012 ADA0 input witness, 2026-07-18",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "The checked-in Windows AEX was executed locally through `FUN_18000ada0`; a code hook captured its four entry pointers and the descriptor-resolved input before the ADA0 call to `VCOMP140!_vcomp_fork`.",
        "",
        "## Captured Boundary",
        "",
        f"- Source descriptor: `{checkpoint['source_descriptor']}`.",
        f"- Class descriptor: `{checkpoint['class_descriptor']}`.",
        f"- Rectangle: `{checkpoint['rectangle']}`.",
        f"- Config `+0x1c`: `{cfg['offset_0x1c_i32']}`; `+0x70`: `{cfg['offset_0x70_i32']}`; `+0x74`: `{cfg['offset_0x74_f32']}`.",
        f"- Captured source window: `{len(checkpoint['source_window_5x5'])}` RGBA float pixels, offsets `-2..2` around translated origin `{report['fixture']['translated_origin']}`.",
        "",
        "## Execution",
        "",
        f"- Bounded run counted `{report['execution']['instructions']}` guest instructions, one serial worker, and `{report['execution']['classifier_entries']}` classifier calls.",
        "- The generated class window matched the retained translated tuple exactly; this validates the capture did not alter the natural caller path.",
        "",
        "## Boundary",
        "",
        "This is an actual-AEX Mac-local witness over retained fixture inputs. It is not a replacement for same-run Windows capture: no live Windows source bytes, config bytes, descriptor strides, or rectangle are asserted.",
        "",
        "## Reproduce",
        "",
        "```sh",
        "python3 tools/emulation/probe_olmsmoother2_case0012_ada0_input_before_vcomp_20260718.py \\",
        "  --output-json refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.json \\",
        "  --output-md refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.md",
        "```",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    report = run(parse_log(LOG_PATH))
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
