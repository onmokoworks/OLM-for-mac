#!/usr/bin/env python3
"""Compare actual-AEX typed workers with production over padded 3x2 frames."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_RSP

import test_olmsmoother2_typed_writeback_20260717 as typed


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/olmsmoother2_typed_padded_production_harness_20260805.cpp"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_typed_padded_production_actual_aex_20260805.json"
DOC = ROOT / "refs/conformance/olmsmoother2_typed_padded_production_actual_aex_20260805.md"
WIDTH, HEIGHT = 3, 2


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("FAIL CLOSED: " + message)


def descriptor(loader, base: int, width: int, height: int, stride: int) -> int:
    address = loader.bump_alloc(24, align=16)
    loader.write_bytes(address, struct.pack("<QiiQ", base, width, height, stride))
    return address


class PaddedSerialDynamic(typed.SerialDynamic):
    """Serial VCOMP range callback with the worker's two independent int outputs."""

    def next(self, _uc, args: list[int]) -> int:
        require(len(args) >= 2 and self.active is not None, "dynamic next without init")
        first, last = self.active
        self.next_calls += 1
        if self.next_calls == 1:
            # FUN_180003990 passes &start (RCX) and &end_inclusive (RDX).
            self.loader.write_bytes(args[0], struct.pack("<i", first))
            self.loader.write_bytes(args[1], struct.pack("<i", last))
            return 1
        return 0


def actual(depth: str, rgba: tuple[float, float, float, float], padding: int) -> dict:
    loader = typed.AexLoader(str(typed.AEX_PATH), verbose=False, fast=True)
    pixel = struct.pack("<4f", *rgba)
    src_stride = WIDTH * len(pixel) + 16
    src_base = loader.bump_alloc(src_stride * HEIGHT, align=16)
    for y in range(HEIGHT):
        loader.write_bytes(src_base + y * src_stride, pixel * WIDTH + b"\x3c" * 16)
    class_stride = WIDTH * 4 + 4
    class_base = loader.bump_alloc(class_stride * HEIGHT, align=16)
    for y in range(HEIGHT):
        loader.write_bytes(class_base + y * class_stride, b"\0" * (WIDTH * 4) + b"\x4c" * 4)
    pixel_size = 8 if depth == "PF16" else 16
    out_stride = WIDTH * pixel_size + padding
    out_base = loader.bump_alloc(out_stride * HEIGHT, align=16)
    loader.write_bytes(out_base, b"\xa5" * (out_stride * HEIGHT))
    source = descriptor(loader, src_base, WIDTH, HEIGHT, src_stride)
    classes = descriptor(loader, class_base, WIDTH, HEIGHT, class_stride)
    output = descriptor(loader, out_base, WIDTH, HEIGHT, out_stride)
    config = loader.bump_alloc(0x40, align=16)
    loader.write_bytes(config, b"\0" * 0x40)
    loader.write_bytes(config, struct.pack("<i", 1))
    context = loader.bump_alloc(0x20, align=16)
    loader.write_bytes(context, b"\0" * 0x20)
    serial = PaddedSerialDynamic(loader, typed.WORKERS[depth])
    right, left, bottom, top = [loader.bump_alloc(4, align=4) for _ in range(4)]
    for address, value in ((right, WIDTH), (left, 0), (bottom, HEIGHT), (top, 0)):
        loader.write_bytes(address, struct.pack("<i", value))
    result = loader.call_function(
        typed.WORKERS[depth],
        int_args=[right, left, bottom, top, source, classes, output, config, context],
        max_instructions=5_000_000,
    )
    raw = loader.read_bytes(out_base, out_stride * HEIGHT)
    for y in range(HEIGHT):
        pad = raw[y * out_stride + WIDTH * pixel_size:(y + 1) * out_stride]
        require(pad == b"\xa5" * padding, f"{depth} AEX modified row {y} padding")
    return {"raw_hex": raw.hex(), "instructions": result["instructions"], "rowbytes": out_stride}


def production() -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_typed_padded_") as td:
        binary = Path(td) / "harness"
        subprocess.run([
            "clang++", "-std=c++17", "-O2",
            "-I", str(ROOT / "cli/OLMSmoother2/shim"),
            "-I", str(ROOT / "mac/OLMSmoother2/Mac"),
            str(HARNESS), "-o", str(binary),
        ], check=True)
        result = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
    rows = dict(line.split() for line in result.stdout.splitlines())
    require(set(rows) == {"PF16", "PF32"}, f"unexpected production rows {rows}")
    return rows


def main() -> int:
    prod = production()
    sources = {
        "PF16": tuple(typed.f32(v / 32768.0) for v in (4045, 16384, 28723, 20480)),
        "PF32": tuple(typed.f32(v) for v in typed.SRC),
    }
    paddings = {"PF16": 6, "PF32": 12}
    rows = []
    for depth in ("PF16", "PF32"):
        aex = actual(depth, sources[depth], paddings[depth])
        require(aex["raw_hex"] == prod[depth], f"{depth} padded frame differs")
        rows.append({
            "depth": depth, "width": WIDTH, "height": HEIGHT,
            "padding_bytes_per_row": paddings[depth], "rowbytes": aex["rowbytes"],
            "source_rgba_f32": list(sources[depth]), "raw_hex": aex["raw_hex"],
            "actual_aex_instructions": aex["instructions"], "equal": True,
            "padding_preserved": True,
        })
    report = {
        "verdict": "PASS_ACTUAL_AEX_TO_PRODUCTION_TYPED_PADDED_3X2_EXACT",
        "scope": "PF16/PF32 independent uniform 3x2 fixtures, v1, key disabled, gamma none, smoothness 0, padded rows, no host",
        "aex_sha256": typed.AEX_SHA256,
        "production_source": str(SOURCE.relative_to(ROOT)),
        "production_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "fixtures": rows,
        "claims_not_made": [
            "No non-uniform classifier or c280 geometry claim",
            "No v2, key, gamma, or nonzero smoothing claim",
            "No After Effects host execution claim",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# OLMSmoother2 padded 3x2 actual-AEX/production boundary", "",
        f"Verdict: `{report['verdict']}`", "",
        "PF16 and PF32 use independent uniform 3x2 fixtures. Actual-AEX typed workers and production `RenderBits` agree over every pixel and preserve each row's output padding canary.", "",
        "| Depth | Rowbytes | Padding/row | Compared bytes |", "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(f"| {row['depth']} | {row['rowbytes']} | {row['padding_bytes_per_row']} | {len(bytes.fromhex(row['raw_hex']))} |")
    lines += ["", "## Boundary", "", "This expands the center proof to padded multi-pixel traversal only. Uniform input intentionally leaves nontrivial classifier/c280 geometry unclaimed.", "", "## Reproduction", "", "```sh", "python3 tools/emulation/test_olmsmoother2_typed_padded_production_actual_aex_20260805.py", "```", ""]
    DOC.write_text("\n".join(lines))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
