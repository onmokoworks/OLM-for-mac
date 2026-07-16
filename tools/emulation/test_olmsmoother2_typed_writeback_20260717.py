#!/usr/bin/env python3
"""Run the post-cce0 typed writeback workers against an independent oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_producer import AEX_PATH  # noqa: E402

AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
WRAPPERS = {"PF8": 0x180003D00, "PF16": 0x180003E20, "PF32": 0x180003D90}
WORKERS = {"PF8": 0x180003370, "PF16": 0x180003990, "PF32": 0x1800036E0}
SRC = (0.1234567, 0.5, 0.8765432, 0.625)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def qword(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


class SerialDynamic:
    """Minimal natural replacement for the worker's dynamic VCOMP loop."""

    def __init__(self, loader: AexLoader, worker: int) -> None:
        self.loader = loader
        self.worker = worker
        self.ranges: list[dict[str, int]] = []
        self.next_calls = 0
        self.active: tuple[int, int] | None = None
        self.fork_calls = 0
        loader.register_import_impl("_vcomp_fork", self.fork)
        loader.register_import_impl("_vcomp_for_dynamic_init", self.init)
        loader.register_import_impl("_vcomp_for_dynamic_next", self.next)

    def fork(self, uc, args: list[int]) -> int:
        require(len(args) >= 4 and args[1] == 9 and args[2] == self.worker, "typed worker fork contract changed")
        rsp = uc.reg_read(UC_X86_REG_RSP)
        captured = [args[3]] + [qword(self.loader, rsp + offset) for offset in range(0x28, 0x68, 8)]
        require(len(captured) == 9 and all(captured), "typed worker fork arguments incomplete")
        saved = self.loader.uc.context_save()
        stack = self.loader.host_alloc(0x1000, align=16)
        nested_rsp = ((stack + 0xF00 - 0x48) & ~0xF) + 8
        continuation = self.loader.install_callback("smoother2.typed_worker_return", lambda _loader, _args: 0)
        try:
            self.loader.write_bytes(nested_rsp, struct.pack("<Q", continuation))
            for index, value in enumerate(captured[4:]):
                self.loader.write_bytes(nested_rsp + 0x28 + index * 8, struct.pack("<Q", value))
            for register, value in zip((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9), captured[:4]):
                self.loader.uc.reg_write(register, value)
            self.loader.uc.reg_write(UC_X86_REG_RSP, nested_rsp)
            self.loader.uc.reg_write(UC_X86_REG_RIP, self.worker)
            self.loader.uc.emu_start(self.worker, continuation, count=2_000_000)
            require(self.loader.uc.reg_read(UC_X86_REG_RIP) == continuation, "typed worker missed continuation")
        finally:
            self.loader.uc.context_restore(saved)
        self.fork_calls += 1
        return 0

    def init(self, _uc, args: list[int]) -> int:
        require(len(args) >= 3, "dynamic init arity changed")
        first, last = int(args[1]), int(args[2])
        self.active = (first, last)
        self.ranges.append({"first": first, "last": last, "step": int(args[3]) if len(args) > 3 else 0})
        return 0

    def next(self, _uc, args: list[int]) -> int:
        require(len(args) >= 2 and self.active is not None, "dynamic next arrived without init")
        first, last = self.active
        self.next_calls += 1
        if self.next_calls == 1:
            self.loader.write_bytes(args[0], struct.pack("<i", first))
            self.loader.write_bytes(args[1], struct.pack("<ii", first, last))
            return 1
        return 0


def descriptor(loader: AexLoader, base: int, stride: int) -> int:
    address = loader.bump_alloc(24, align=16)
    loader.write_bytes(address, struct.pack("<QiiQ", base, 1, 1, stride))
    return address


def oracle(depth: str) -> bytes:
    values = [f32(value) for value in SRC]
    if depth == "PF32":
        return struct.pack("<4f", values[3], values[0], values[1], values[2])
    scale = f32(255.0 if depth == "PF8" else 32768.0)
    words = [int(f32(f32(value * scale) + f32(0.5))) for value in (values[3], values[0], values[1], values[2])]
    if depth == "PF8":
        return bytes(words)
    return struct.pack("<4H", *words)


def run_depth(depth: str) -> dict[str, Any]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    source_base = loader.bump_alloc(16, align=16)
    loader.write_bytes(source_base, struct.pack("<4f", *SRC))
    class_base = loader.bump_alloc(4, align=16)
    loader.write_bytes(class_base, b"\x00" * 4)
    out_stride = {"PF8": 4, "PF16": 8, "PF32": 16}[depth]
    out_base = loader.bump_alloc(out_stride, align=16)
    loader.write_bytes(out_base, b"\xA5" * out_stride)
    source = descriptor(loader, source_base, 16)
    classes = descriptor(loader, class_base, 4)
    output = descriptor(loader, out_base, out_stride)
    rect = loader.bump_alloc(16, align=16)
    loader.write_bytes(rect, struct.pack("<4i", 0, 0, 1, 1))
    config = loader.bump_alloc(0x40, align=16)
    loader.write_bytes(config, b"\x00" * 0x40)
    loader.write_bytes(config, struct.pack("<i", 1))
    context = loader.bump_alloc(0x20, align=16)
    loader.write_bytes(context, b"\x00" * 0x20)
    serial = SerialDynamic(loader, WORKERS[depth])
    right = loader.bump_alloc(4, align=4)
    left = loader.bump_alloc(4, align=4)
    bottom = loader.bump_alloc(4, align=4)
    top = loader.bump_alloc(4, align=4)
    loader.write_bytes(right, struct.pack("<i", 1))
    loader.write_bytes(left, struct.pack("<i", 0))
    loader.write_bytes(bottom, struct.pack("<i", 1))
    loader.write_bytes(top, struct.pack("<i", 0))
    # The wrapper's fork ABI is statically grounded below; the nine-argument
    # worker ABI is invoked directly so every callback argument is explicit.
    result = loader.call_function(WORKERS[depth], int_args=[right, left, bottom, top, source, classes, output, config, context], max_instructions=2_000_000)
    actual = loader.read_bytes(out_base, out_stride)
    expected = oracle(depth)
    require(actual == expected, f"{depth} raw writeback differs: {actual.hex()} != {expected.hex()} ranges={serial.ranges} next={serial.next_calls}")
    require(b"\xA5" not in actual, f"{depth} output canary survived")
    return {
        "depth": depth,
        "wrapper": hex(WRAPPERS[depth]),
        "worker": hex(WORKERS[depth]),
        "invocation": "direct nine-argument worker ABI; wrapper dispatch statically grounded",
        "instructions": result["instructions"],
        "dynamic_ranges": serial.ranges,
        "dynamic_next_calls": serial.next_calls,
        "source_rgba_f32": list(SRC),
        "actual_raw_hex": actual.hex(),
        "oracle_raw_hex": expected.hex(),
        "raw_equal": True,
    }


def grounding() -> None:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == AEX_SHA256, "AEX hash drift")
    asm = (ROOT / "disasm/OLMSmoother2.aex.asm.txt").read_text(encoding="utf-8")
    for anchor in ("; === FUN_180003370", "; === FUN_1800036e0", "; === FUN_180003990"):
        require(anchor in asm, f"missing typed worker anchor {anchor}")
    require("LEA R8,[0x180003370]" in asm and "LEA R8,[0x1800036e0]" in asm and "LEA R8,[0x180003990]" in asm, "wrapper dispatch anchors missing")


def render(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 post-cce0 typed writeback boundary",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "The checked-in AEX executes each depth-specific worker through its explicit nine-argument ABI and serial dynamic-VCOMP callback. The corresponding wrappers are statically grounded. A zero class plane makes c280 select the center sample; the independent oracle checks only the subsequent typed store.",
        "",
        "## Results",
        "",
        "| Depth | Wrapper | Worker | Raw output | Equal |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        lines.append(f"| `{row['depth']}` | `{row['wrapper']}` | `{row['worker']}` | `{row['actual_raw_hex']}` | `{row['raw_equal']}` |")
    lines += [
        "",
        "The oracle uses float32 source values, A,R,G,B byte/word order, and the independently transcribed `+0.5` truncating quantization with scales `255` and `32768`; PF32 is compared as raw float32 words.",
        "",
        "## Boundary",
        "",
        "This closes only the bounded post-cce0 typed writeback workers for a center-sample fixture. It does not claim classifier, c280, cce0 algorithm, Windows behavior, host state, or AE exactness.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/test_olmsmoother2_typed_writeback_20260717.py --output-json refs/conformance/olmsmoother2_typed_writeback_20260717.json --output-md refs/conformance/olmsmoother2_typed_writeback_20260717.md",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding()
    cases = [run_depth(depth) for depth in ("PF8", "PF16", "PF32")]
    report = {
        "verdict": "PASS_ACTUAL_AEX_POST_CCE0_TYPED_WRITEBACK_ORACLE",
        "scope": "Mac-local actual-AEX typed writeback workers versus independent raw-byte/word/float32 oracle",
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": AEX_SHA256},
        "boundary": {"wrappers": {key: hex(value) for key, value in WRAPPERS.items()}, "workers": {key: hex(value) for key, value in WORKERS.items()}, "center_sample_only": True},
        "cases": cases,
        "claims_not_made": ["No classifier/c280/cce0 correctness claim", "No case0012 host-state claim", "No Windows or AE exact claim", "No production or ledger edit"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
