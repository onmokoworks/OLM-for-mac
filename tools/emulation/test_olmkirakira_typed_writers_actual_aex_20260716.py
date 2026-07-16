#!/usr/bin/env python3
"""Execute OLMKiraKira's checked-in PF8/PF16/PF32 writer helpers."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "plugins_2025/OLMKiraKira.aex"
REPORT_JSON = ROOT / "refs/conformance/olmkirakira_typed_writers_actual_aex_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmkirakira_typed_writers_actual_aex_20260716.md"
WRITERS = {
    "PF8": {"entry": 0x181230B90, "stop": 0x181230BC9, "size": 4},
    "PF16": {"entry": 0x181230BD0, "stop": 0x181230C0D, "size": 8},
    "PF32": {"entry": 0x181230C20, "stop": 0x181230C39, "size": 16},
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trunc_scaled(value: float, scale: float, mask: int) -> int:
    return int(f32(f32(value) * f32(scale))) & mask


def expected_argb(depth: str, rgba: tuple[float, float, float, float]) -> list[int]:
    r, g, b, a = rgba
    if depth == "PF8":
        return [trunc_scaled(v, 255.0, 0xFF) for v in (a, r, g, b)]
    if depth == "PF16":
        return [trunc_scaled(v, 32768.0, 0xFFFF) for v in (a, r, g, b)]
    return [f32_bits(v) for v in (a, r, g, b)]


def unpack_argb(depth: str, payload: bytes) -> list[int]:
    if depth == "PF8":
        return list(payload)
    if depth == "PF16":
        return list(struct.unpack("<4H", payload))
    return list(struct.unpack("<4I", payload))


def run_writer(depth: str, rgba: tuple[float, float, float, float]) -> dict[str, object]:
    spec = WRITERS[depth]
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    destination = loader.host_alloc(int(spec["size"]))
    loader.write_bytes(destination, bytes([0xA5]) * int(spec["size"]))
    r, g, b, a = (f32(value) for value in rgba)
    call = loader.call_function(
        int(spec["entry"]),
        int_args=[0, 0, 0, 0, destination],
        float_args={0: r, 1: g, 2: b, 3: a},
        max_instructions=1000,
    )
    raw = loader.read_bytes(destination, int(spec["size"]))
    observed = unpack_argb(depth, raw)
    expected = expected_argb(depth, (r, g, b, a))
    if observed != expected:
        raise AssertionError(f"{depth} writer mismatch: observed={observed}, expected={expected}")
    return {
        "depth": depth,
        "input_rgba_f32_bits": [f"0x{f32_bits(value):08x}" for value in (r, g, b, a)],
        "observed_argb_units_or_bits": [f"0x{v:08x}" if depth == "PF32" else v for v in observed],
        "expected_argb_units_or_bits": [f"0x{v:08x}" if depth == "PF32" else v for v in expected],
        "raw_hex": raw.hex(),
        "instructions": call["instructions"],
        "exact": True,
    }


def static_proof() -> dict[str, object]:
    command = [
        "objdump", "-d", "--start-address=0x181230b90", "--stop-address=0x181230c39", str(AEX)
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    required = {
        "PF8 scale": "# 0x1814d65a8",
        "PF16 scale": "# 0x1814d65ac",
        "truncate": "cvttss2si",
        "PF8 alpha store": "movb\t%al, (%rcx)",
        "PF16 alpha store": "movw\t%ax, (%rcx)",
        "PF32 raw float store": "movss\t%xmm3, (%rax)",
    }
    missing = [name for name, snippet in required.items() if snippet not in result.stdout]
    if missing:
        raise AssertionError(f"typed writer disassembly drifted: missing {missing}")
    return {
        "command": "objdump -d --start-address=0x181230b90 --stop-address=0x181230c39 plugins_2025/OLMKiraKira.aex",
        "required_fragments": required,
        "missing": missing,
    }


def render_markdown(report: dict[str, object]) -> str:
    rows = []
    for case in report["cases"]:
        rows.append(
            f"| {case['depth']} | `{', '.join(case['input_rgba_f32_bits'])}` | "
            f"`{case['observed_argb_units_or_bits']}` | {case['instructions']} | exact |"
        )
    return "\n".join([
        "# OLMKiraKira Actual-AEX Typed Writer Proof (2026-07-16)",
        "",
        "## Result",
        "",
        "The checked-in Windows AEX writer helpers were executed directly with Unicorn.",
        "This proves helper-local conversion only; it does not bind Mode 2 to these helpers or claim AE exactness.",
        "",
        "| Depth | Input RGBA f32 bits | Observed ARGB units/bits | Instructions | Result |",
        "| --- | --- | --- | ---: | --- |",
        *rows,
        "",
        "## Facts",
        "",
        "- PF8 multiplies by `255.0f`, truncates toward zero with `CVTTSS2SI`, and stores ARGB bytes.",
        "- PF16 multiplies by `32768.0f`, truncates toward zero with `CVTTSS2SI`, and stores ARGB words.",
        "- PF32 stores the four incoming float bit patterns directly in ARGB order.",
        "- The PF8/PF16 out-of-range case proves that these helpers do not clamp by themselves.",
        "",
        "## Limit",
        "",
        "The static caller graph still does not bind the Mode 2 intermediate float buffer to this writer wrapper.",
        "Mac production rounding therefore remains unchanged until a same-run host/writeback witness exists.",
        "",
    ])


def main() -> int:
    cases = [
        run_writer("PF8", (0.5, 1.0, 0.25, 0.75)),
        run_writer("PF8", (-0.25, 1.5, 1.0 / 255.0, 0.5)),
        run_writer("PF16", (127.5 / 32768.0, 1.0, -0.25, 255.5 / 32768.0)),
        run_writer("PF32", (-0.25, 1.5, 0.1, 2.0)),
    ]
    report = {
        "status": "pass",
        "aex": str(AEX.relative_to(ROOT)),
        "aex_sha256": sha256(AEX),
        "writer_entries": {depth: f"0x{spec['entry']:x}" for depth, spec in WRITERS.items()},
        "static_proof": static_proof(),
        "cases": cases,
        "facts": [
            "FACT: all observed writer outputs exactly matched the x86 float32/truncate/raw-store model.",
            "FACT: channel order at the destination is ARGB for PF8, PF16, and PF32.",
        ],
        "inferences": [
            "INFERENCE: these leaf helper semantics are reusable only after a caller path is bound to the helper in the same algorithm/run.",
        ],
        "ae_exact_claim": False,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
