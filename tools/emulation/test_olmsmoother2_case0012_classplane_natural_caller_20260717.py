#!/usr/bin/env python3
"""Execute the actual AEX class-plane caller through a serial VCOMP boundary."""

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
    UC_X86_REG_RIP,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader  # noqa: E402
from test_olmsmoother2_case0012_classplane_return_replay_20260717 import (  # noqa: E402
    ARCHIVES,
    read_archive,
    validate_returns,
)
from test_smoother2_case0012_local_tuple import LOG_PATH, parse_log  # noqa: E402
from test_smoother2_fullchain_diff import call_c280_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

FUN_ADA0 = 0x18000ADA0
FUN_AC00 = 0x18000AC00
FUN_AE10 = 0x18000AE10
FUN_C280 = 0x18000C280
WIDTH = HEIGHT = 16
ORIGIN = (8, 8)
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
CANARY = 0xA5


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


class SerialVcomp:
    """Single-worker implementation of the exact three VCOMP calls on this lane."""

    def __init__(self, loader: AexLoader) -> None:
        self.loader = loader
        self.fork_events: list[dict[str, Any]] = []
        self.static_events: list[dict[str, Any]] = []
        self.worker_entries = 0
        self.classifier_entries = 0
        loader.register_import_impl("_vcomp_fork", self.fork)
        loader.register_import_impl("_vcomp_for_static_simple_init", self.static_init)
        loader.register_import_impl("_vcomp_for_static_end", self.static_end)
        loader.add_code_hook(FUN_AC00, self.at_worker)
        loader.add_code_hook(FUN_AE10, self.at_classifier)

    def at_worker(self, _loader: AexLoader, _address: int, _size: int) -> None:
        self.worker_entries += 1

    def at_classifier(self, _loader: AexLoader, _address: int, _size: int) -> None:
        self.classifier_entries += 1

    def static_init(self, uc, args: list[int]) -> int:
        require(args == [0, HEIGHT - 1, 1, 1], f"unexpected static schedule arguments {args}")
        rsp = uc.reg_read(UC_X86_REG_RSP)
        first_out = u64(self.loader, rsp + 0x28)
        last_out = u64(self.loader, rsp + 0x30)
        require(first_out != 0 and last_out != 0 and first_out != last_out, "invalid static schedule output pointers")
        self.loader.write_bytes(first_out, struct.pack("<i", args[0]))
        self.loader.write_bytes(last_out, struct.pack("<i", args[1]))
        self.static_events.append({"first": args[0], "last": args[1], "step": args[2], "increment": args[3]})
        return 0

    def static_end(self, _uc, _args: list[int]) -> int:
        return 0

    def fork(self, uc, args: list[int]) -> int:
        require(args[:3] == [1, 7, FUN_AC00], f"unexpected _vcomp_fork header {args[:3]}")
        rsp = uc.reg_read(UC_X86_REG_RSP)
        captured = [args[3]] + [u64(self.loader, rsp + offset) for offset in range(0x28, 0x58, 8)]
        require(len(captured) == 7 and all(captured), "incomplete seven-argument VCOMP capture")

        saved = self.loader.uc.context_save()
        stack_base = self.loader.host_alloc(0x1000, align=16)
        nested_rsp = ((stack_base + 0xF00 - 0x48) & ~0xF) + 8
        nested_return = self.loader.install_callback("classplane.vcomp_nested_return", lambda _loader, _args: 0)
        before_workers = self.worker_entries
        try:
            self.loader.write_bytes(nested_rsp, struct.pack("<Q", nested_return))
            for index, value in enumerate(captured[4:]):
                self.loader.write_bytes(nested_rsp + 0x28 + index * 8, struct.pack("<Q", value))
            for register, value in zip((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9), captured[:4]):
                self.loader.uc.reg_write(register, value)
            self.loader.uc.reg_write(UC_X86_REG_RSP, nested_rsp)
            self.loader.uc.reg_write(UC_X86_REG_RIP, FUN_AC00)
            self.loader.uc.emu_start(FUN_AC00, nested_return, count=2_000_000)
            require(self.loader.uc.reg_read(UC_X86_REG_RIP) == nested_return, "VCOMP worker missed its private continuation")
        finally:
            self.loader.uc.context_restore(saved)
        require(self.worker_entries == before_workers + 1, "VCOMP did not invoke exactly one natural ac00 worker")
        self.fork_events.append({
            "if_value": args[0],
            "captured_argument_count": args[1],
            "worker": hex(args[2]),
            "serial_worker_invocations": 1,
            "private_continuation": True,
        })
        return 0


def install_descriptors(loader: AexLoader, smoother: SmootherStruct, smooth_range: int) -> tuple[int, int, int, int]:
    source = loader.bump_alloc(24, align=16)
    classes = loader.bump_alloc(24, align=16)
    rectangle = loader.bump_alloc(16, align=16)
    config = loader.bump_alloc(0x80, align=16)
    loader.write_bytes(source, struct.pack("<QiiQ", smoother.src_base, WIDTH, HEIGHT, smoother.src_stride))
    loader.write_bytes(classes, struct.pack("<QiiQ", smoother.class_base, WIDTH, HEIGHT, smoother.class_stride))
    loader.write_bytes(rectangle, struct.pack("<4i", 0, 0, WIDTH, HEIGHT))
    loader.write_bytes(config, b"\x00" * 0x80)
    loader.write_bytes(config + 0x1C, struct.pack("<i", smooth_range))
    return source, classes, rectangle, config


def expected_window(tuple_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = {tuple(item["offset"]): item for item in tuple_data["neighbors"]}
    result = []
    for dy in range(-1, 3):
        for dx in range(-1, 2):
            item = rows[(dx, dy)]
            result.append({"offset": [dx, dy], "class": item["class"]})
    return result


def actual_window(loader: AexLoader, smoother: SmootherStruct) -> list[dict[str, Any]]:
    result = []
    for dy in range(-1, 3):
        for dx in range(-1, 2):
            address = smoother.class_base + (ORIGIN[1] + dy) * smoother.class_stride + (ORIGIN[0] + dx) * 4
            result.append({"offset": [dx, dy], "class": list(loader.read_bytes(address, 4))})
    return result


def run_natural_checkpoint(tuple_data: dict[str, Any]) -> dict[str, Any]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    require(tuple_data["range"] == 88 and len(tuple_data["neighbors"]) == 25, "fixture range or source coverage changed")
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, HEIGHT)
    loader.write_bytes(smoother.class_base, bytes([CANARY]) * (WIDTH * HEIGHT * 4))
    for item in tuple_data["neighbors"]:
        dx, dy = item["offset"]
        smoother.set_src_pixel(ORIGIN[0] + dx, ORIGIN[1] + dy, item["setup"])

    source, classes, rectangle, config = install_descriptors(loader, smoother, tuple_data["range"])
    vcomp = SerialVcomp(loader)
    result = loader.call_function(FUN_ADA0, int_args=[source, classes, rectangle, config], max_instructions=5_000_000)
    generated = actual_window(loader, smoother)
    expected = expected_window(tuple_data)
    require(generated == expected, "natural ae10 output differs from retained translated 3x4 class window")
    full_plane = loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4)
    require(CANARY not in full_plane, "ada0 did not populate the complete requested class rectangle")
    require(set(full_plane).issubset({0, 255}), "class plane contains a non-boolean byte")
    require(len(vcomp.fork_events) == len(vcomp.static_events) == 1, "unexpected VCOMP event count")
    require(vcomp.classifier_entries == WIDTH * HEIGHT, "ae10 classifier call count does not cover the rectangle")

    c280 = call_c280_entry(loader, smoother, *ORIGIN)
    require(c280["count"] == 1, "generated class plane no longer selects the retained one-vertex c280 path")
    require(len(c280["vertices"]) == 1, "c280 result shape changed")
    vertex = c280["vertices"][0]
    require(all(abs(a - b) <= 1e-6 for a, b in zip(vertex["rgba"], [0.991067171, 0.991067171, 0.991067171, 0.996078432])), "c280 vertex RGBA changed")
    return {
        "entry": hex(FUN_ADA0),
        "natural_chain": [hex(FUN_ADA0), "VCOMP140!_vcomp_fork", hex(FUN_AC00), hex(FUN_AE10)],
        "instructions": result["instructions"],
        "vcomp": {"fork": vcomp.fork_events, "static_schedule": vcomp.static_events},
        "worker_entries": vcomp.worker_entries,
        "classifier_entries": vcomp.classifier_entries,
        "checkpoint": "immediately after FUN_18000ada0 returns and before FUN_18000beb0/c280 consumption",
        "generated_window": generated,
        "expected_window": expected,
        "generated_window_exact": True,
        "full_rectangle_populated": True,
        "c280_from_generated_plane": {"count": c280["count"], "vertices": c280["vertices"]},
    }


def validate_live_boundary() -> dict[str, Any]:
    parsed = {label: read_archive(label, relative, digest) for label, (relative, digest) in ARCHIVES.items()}
    intake = validate_returns(parsed)
    require(len(intake["retained_class_pixels"]) == 3, "corrected retained class-pixel scope changed")
    traces = [item for archive in parsed.values() for item in archive["trace"]]
    require(not any(item["prefix"] in {"S2_UPSTREAM_ADA0", "S2_UPSTREAM_AE10"} for item in traces), "a new producer-input checkpoint requires review")
    reentrant_c280 = next(item["fields"] for item in parsed["reentrant"]["trace"] if item["prefix"] == "S2_UPSTREAM_C280")
    require(reentrant_c280.get("source_plane", "0") != "0", "reentrant c280 source pointer is absent")
    require("source_plane_bytes" not in reentrant_c280 and "config_bytes" not in reentrant_c280, "unexpected live producer input bytes require review")
    return {
        "corrected_retained_class_pixels": 3,
        "ada0_or_ae10_input_checkpoints_in_returns": 0,
        "reentrant_source_plane_pointer_only": reentrant_c280["source_plane"],
        "missing_inputs": [
            "post-frame-setup float source neighborhood needed by ae10",
            "ada0 config bytes +0x1c, +0x70, and float +0x74",
            "requested rectangle and source/class descriptor strides bound to the same run",
        ],
        "exact_next_checkpoint": "FUN_18000ada0 entry: RCX=source FPlane*, RDX=class FPlane*, R8=rect*, R9=config*; capture source neighborhood and config before _vcomp_fork",
    }


def render_markdown(report: dict[str, Any]) -> str:
    natural = report["natural_checkpoint"]
    return "\n".join([
        "# OLMSmoother2 case0012 natural class-plane caller",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "Actual AEX `FUN_18000ada0` reaches the compiler-generated `FUN_18000ac00` worker through a continuation-safe serial implementation of `VCOMP140!_vcomp_fork`. The worker naturally calls `FUN_18000ae10` once per pixel and fills the requested class rectangle before c280.",
        "",
        "## Checkpoint Result",
        "",
        f"- Actual chain: `{' -> '.join(natural['natural_chain'])}`.",
        f"- Runtime: `{natural['instructions']}` fully counted guest instructions, one worker, `{natural['classifier_entries']}` ae10 calls.",
        "- The translated retained source fixture regenerates the central `3x4` class window exactly; this is the largest rectangular output window whose ae10 dependencies are wholly covered by the retained `5x5` source setup.",
        f"- Actual c280 consumes that newly generated plane and returns polygon count `{natural['c280_from_generated_plane']['count']}`.",
        "",
        "## Live Boundary",
        "",
        "The VCOMP runtime boundary is locally closed. The three Windows returns provide a later c280 source-plane pointer but no post-frame-setup source floats and no ada0 config snapshot, so the corrected live neighborhood still cannot be regenerated.",
        "",
        f"Exact next checkpoint: `{report['live_boundary']['exact_next_checkpoint']}`.",
        "",
        "Required same-run fields are the float source neighborhood, config `+0x1c/+0x70/+0x74`, rectangle, and both descriptor strides. Process pointers without bytes remain non-replayable.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/test_olmsmoother2_case0012_classplane_natural_caller_20260717.py \\",
        "  --output-json refs/conformance/olmsmoother2_case0012_classplane_natural_caller_20260717.json \\",
        "  --output-md refs/conformance/olmsmoother2_case0012_classplane_natural_caller_20260717.md",
        "```",
        "",
        "## Claims Not Made",
        "",
        "- No recovered corrected Windows class plane.",
        "- No Windows or After Effects execution claim.",
        "- No production correctness or AE exact claim.",
        "- No ledger or production-source change.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=LOG_PATH)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    tuple_data = parse_log(args.log)
    natural = run_natural_checkpoint(tuple_data)
    live_boundary = validate_live_boundary()
    report = {
        "verdict": "PASS_MAC_NATURAL_CLASSPLANE_CALLER_WITH_EXACT_LIVE_INPUT_BOUNDARY",
        "scope": "Mac-local actual-AEX ada0/ac00/ae10 execution on a translated retained fixture; corrected live source inputs remain absent",
        "binary": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": EXPECTED_AEX_SHA256},
        "binary_grounding": {
            "ada0_vcomp_fork_call": "0x18000adfe",
            "vcomp_import_thunk": "0x180020f00 -> IAT 0x180022120 -> VCOMP140!_vcomp_fork",
            "ac00_static_init_call": "0x18000ac44",
            "ac00_ae10_call": "0x18000aced",
            "ac00_static_end_call": "0x18000ad84",
            "cce0_c280_call": "0x18000cd5a",
        },
        "fixture": {"source": str(args.log.relative_to(ROOT)), "host_origin": tuple_data["target_xy"], "translated_origin": list(ORIGIN), "smooth_range": tuple_data["range"]},
        "natural_checkpoint": natural,
        "live_boundary": live_boundary,
        "claims_not_made": [
            "No recovered corrected Windows class plane",
            "No Windows or After Effects execution claim",
            "No production correctness or AE exact claim",
            "No ledger or production-source change",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
