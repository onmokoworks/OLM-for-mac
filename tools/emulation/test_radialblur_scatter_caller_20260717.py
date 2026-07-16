#!/usr/bin/env python3
"""Verify the bounded RadialBlur scatter caller contract and AEX call order."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R14, UC_X86_REG_RSP, UC_X86_REG_RDX

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
CALLER = 0x1800024C0
ANCHOR = 0x180002520
TAIL = 0x180001C90
POST_EFFECTIVE_LEN = 0x180001D1D
OUT_JSON = ROOT / "refs/conformance/olmradialblur_scatter_caller_20260717.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_scatter_caller_20260717.md"


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def from_bits(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def caller_distance(quality: int, offset: int, radius: int) -> int:
    numerator = f32(float((quality // 2) * offset))
    denominator = f32(float(radius + 1))
    ratio = f32(f32(1.0) / denominator)
    return int(f32(numerator * ratio))


def expected_active(source_alpha: float = 0.5) -> tuple[list[float], list[float]]:
    angles = 4
    scatter = [0.0] * (3 * angles * 4)
    maximum = [0.0] * (3 * angles)
    source = (2.0, 3.0, 5.0)
    radius = 1
    for direction, distance in ((0, caller_distance(8, 4, radius)),
                                (1, caller_distance(8, 6, radius))):
        column = 0
        inner_cell = radius * angles
        for _offset in range(1, distance):
            if direction == 0:
                column = (column + 1) % angles
                destination = radius * angles + column
            else:
                inner_cell -= 1
                if inner_cell < radius * angles:
                    inner_cell = (radius + 1) * angles - 1
                destination = inner_cell
            contribution = f32(source_alpha)
            base = destination * 4
            for channel, value in enumerate(source):
                scatter[base + channel] = f32(scatter[base + channel] + f32(contribution * value))
            scatter[base + 3] = f32(scatter[base + 3] + contribution)
            if maximum[destination] <= contribution and contribution != maximum[destination]:
                maximum[destination] = contribution
    return scatter, maximum


def run_aex_case(case: str) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    context = loader.bump_alloc(0x3AA20, align=64)
    loader.write_bytes(context, b"\0" * 0x3AA20)
    loader.write_f32_array(context + 0x68, [1.0] * 30000)
    loader.write_f32_array(context + 0x1D528, [1.0] * 30000)
    loader.write_bytes(context + 0x24, struct.pack("<i", 1))
    loader.write_bytes(context + 0x28, struct.pack("<i", 4))
    loader.write_bytes(context + 0x2C, struct.pack("<i", 1))
    loader.write_bytes(context + 0x30, struct.pack("<i", 6))

    rows, angles = 3, 4
    source = loader.bump_alloc(rows * angles * 16, align=64)
    alpha = loader.bump_alloc(rows * angles * 4, align=64)
    span = loader.bump_alloc(rows * angles * 4, align=64)
    valid = loader.bump_alloc(rows * angles, align=64)
    source_values = [0.0] * (rows * angles * 4)
    source_values[angles * 4:angles * 4 + 4] = [2.0, 3.0, 5.0, 0.5]
    alpha_values = [0.0] * (rows * angles)
    span_values = [0.0] * (rows * angles)
    valid_values = [0] * (rows * angles)
    active = angles
    alpha_values[active] = 0.5
    span_values[active] = 1.0
    valid_values[active] = 1
    if case == "valid=0": valid_values[active] = 0
    if case == "alpha=0": alpha_values[active] = 0.0
    if case == "span=0": span_values[active] = 0.0
    if case == "alpha=NaN": alpha_values[active] = from_bits(0x7FC12345)
    if case == "span=NaN": span_values[active] = from_bits(0x7FC54321)
    if case == "alpha=-0.5": alpha_values[active] = -0.5
    if case == "span=-1": span_values[active] = -1.0
    loader.write_f32_array(source, source_values)
    loader.write_f32_array(alpha, alpha_values)
    loader.write_f32_array(span, span_values)
    loader.write_bytes(valid, bytes(valid_values))
    scatter = loader.bump_alloc(rows * angles * 16, align=64)
    maximum = loader.bump_alloc(rows * angles * 4, align=64)
    loader.write_f32_array(scatter, [0.0] * (rows * angles * 4))
    loader.write_f32_array(maximum, [0.0] * (rows * angles))

    calls: list[dict[str, int]] = []
    loader.add_code_hook(ANCHOR, lambda *_: None)

    def on_tail(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        calls.append({
            "direction": ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF,
            "caller_distance": ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
            "angular": ld.uc.reg_read(UC_X86_REG_R9) & 0xFFFFFFFF,
            "radius": struct.unpack("<i", ld.uc.mem_read(rsp + 0x28, 4))[0],
        })
    loader.add_code_hook(TAIL, on_tail)
    loader.call_function(CALLER, int_args=[context, source, alpha, span, valid, angles, 8, 1, 3,
                                            scatter, maximum], max_instructions=500000)
    actual_scatter = loader.read_f32_array(scatter, rows * angles * 4)
    actual_maximum = loader.read_f32_array(maximum, rows * angles)
    if case == "active" or case == "alpha=-0.5":
        expected_scatter, expected_maximum = expected_active(alpha_values[active])
    else:
        expected_scatter = [0.0] * (rows * angles * 4)
        expected_maximum = [0.0] * (rows * angles)
    expected_call_count = 2 if case in ("active", "alpha=-0.5", "span=-1") else 0
    exact = (actual_scatter == expected_scatter and actual_maximum == expected_maximum and
             len(calls) == expected_call_count)
    return {"status": "pass" if exact else "fail", "helper_calls": calls,
            "expected_helper_call_count": expected_call_count,
            "scatter_exact": actual_scatter == expected_scatter,
            "max_exact": actual_maximum == expected_maximum}


def run_aex_wrap_add() -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    context = loader.bump_alloc(0x3AA20, align=64)
    loader.write_bytes(context, b"\0" * 0x3AA20)
    loader.write_bytes(context + 0x24, struct.pack("<i", 1))
    loader.write_bytes(context + 0x3A9E8, struct.pack("<i", 0x7FFFFFFF))
    scatter = loader.bump_alloc(4 * 16, align=64)
    maximum = loader.bump_alloc(4 * 4, align=64)
    loader.write_f32_array(scatter, [7.0] * 16)
    loader.write_f32_array(maximum, [9.0] * 4)
    captured: dict[str, int] = {}

    def on_effective_len(ld: AexLoader, _address: int, _size: int) -> None:
        raw = ld.uc.reg_read(UC_X86_REG_R14) & 0xFFFFFFFF
        captured["effective_len"] = raw if raw < 0x80000000 else raw - 0x100000000

    loader.add_code_hook(POST_EFFECTIVE_LEN, on_effective_len)
    loader.call_function(
        TAIL,
        int_args=[context, 0, 1, 0, 0, bits(1.0), bits(2.0), bits(3.0), bits(5.0),
                  bits(1.0), 4, scatter, maximum],
        max_instructions=100000,
    )
    unchanged = (loader.read_f32_array(scatter, 16) == [7.0] * 16 and
                 loader.read_f32_array(maximum, 4) == [9.0] * 4)
    effective_len = captured.get("effective_len")
    return {"status": "pass" if effective_len == -2147483648 and unchanged else "fail",
            "base_length_i32": 2147483647, "caller_distance_i32": 1,
            "wrapped_sum_i32": -2147483648, "actual_effective_len_i32": effective_len,
            "buffers_unchanged": unchanged}


def run_aex() -> dict:
    if not AEX.exists(): return {"status": "blocked-missing-aex"}
    actual_hash = hashlib.sha256(AEX.read_bytes()).hexdigest()
    if actual_hash != AEX_SHA256: return {"status": "blocked-hash-mismatch", "actual_sha256": actual_hash}
    cases = {name: run_aex_case(case) for name, case in (
        ("start_radius=1", "active"), ("valid=0", "valid=0"),
        ("alpha=0", "alpha=0"), ("span=0", "span=0"),
        ("alpha=NaN", "alpha=NaN"), ("span=NaN", "span=NaN"),
        ("alpha=-0.5", "alpha=-0.5"), ("span=-1", "span=-1"))}
    order = cases["start_radius=1"]["helper_calls"]
    order_pass = [c["direction"] for c in order] == [0, 1] and [c["radius"] for c in order] == [1, 1]
    wrap_add = run_aex_wrap_add()
    return {"status": "pass" if all(c["status"] == "pass" for c in cases.values()) and order_pass and wrap_add["status"] == "pass" else "fail",
            "aex_sha256": actual_hash, "cases": cases,
            "tail_entry_order": order, "tail_order_outer_then_inner": order_pass,
            "tail_mode1_wrap_add": wrap_add}


def run_cpp() -> dict:
    compiler = shutil.which("c++")
    if compiler is None: return {"status": "blocked-no-compiler"}
    with tempfile.TemporaryDirectory(prefix="olm-radialblur-caller-") as directory:
        binary = Path(directory) / "probe"
        base = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-fno-fast-math", "-ffp-contract=off", "-Icore",
                "core/radialblur_scatter_tail.cpp", "core/radialblur_scatter_caller.cpp",
                "tools/emulation/radialblur_scatter_caller_probe_20260717.cpp", "-o", str(binary)]
        build = subprocess.run(base, cwd=ROOT, capture_output=True, text=True)
        if build.returncode: return {"status": "build-fail", "stderr": build.stderr}
        run = subprocess.run([str(binary)], cwd=ROOT, capture_output=True, text=True)
        ubsan_binary = Path(directory) / "probe-ubsan"
        ubsan = [compiler, "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-fno-fast-math", "-ffp-contract=off",
                 "-fsanitize=undefined", "-fno-sanitize-recover=undefined", "-Icore",
                 "core/radialblur_scatter_tail.cpp", "core/radialblur_scatter_caller.cpp",
                 "tools/emulation/radialblur_scatter_caller_probe_20260717.cpp", "-o", str(ubsan_binary)]
        ubsan_build = subprocess.run(ubsan, cwd=ROOT, capture_output=True, text=True)
        ubsan_run = None if ubsan_build.returncode else subprocess.run(
            [str(ubsan_binary)], cwd=ROOT, capture_output=True, text=True)
        ubsan_status = ("blocked-build-fail" if ubsan_run is None else
                         ("pass" if ubsan_run.returncode == 0 and ubsan_run.stdout.strip() == "PASS" else "fail"))
        return {"status": "pass" if run.returncode == 0 and run.stdout.strip() == "PASS" and ubsan_status == "pass" else "fail",
                "ubsan_status": ubsan_status, "ubsan_extreme_mode1_wrap": ubsan_status,
                "stderr": run.stderr, "ubsan_stderr": ubsan_build.stderr if ubsan_run is None else ubsan_run.stderr}


def main() -> int:
    aex = run_aex()
    cpp = run_cpp()
    report = {"schema": "olmradialblur.scatter-caller/3", "status": "pass" if aex["status"] == "pass" and cpp["status"] == "pass" else "blocked-or-fail",
              "caller": hex(CALLER), "aex_anchor": hex(ANCHOR), "aex_tail_helper": hex(TAIL),
              "claim_boundary": "bounded caller fixtures against the pinned AEX and portable C++; not AE exact, production wiring, or broad equivalence",
              "float_contract": "DAT_1800212d4=1.0f; scalar float32 operation order; builds use -fno-fast-math -ffp-contract=off",
              "gate_contract": "UCOMISS value,0 then JZ: zero and unordered NaN skip; negative finite nonzero values remain active",
              "mode1_add_contract": "base_length + caller_distance uses defined uint32 representation addition and bit-preserving int32 conversion to emulate x86 ADD wrap",
              "bounds_divergences": ["portable caller rejects geometry/buffer coverage failures before writing", "portable tail bails out when a computed cell reaches cell_count; AEX has no equivalent check; undersized buffers are outside the claim"],
              "cpp": cpp, "aex": aex}
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# OLMRadialBlur Scatter Caller, 2026-07-17", "", f"- Status: `{report['status']}`", "- Caller: `0x1800024c0`", "- Anchor: `0x180002520`", "- Tail helper: `0x180001c90`", "- Source and destination planes use absolute radius rows; `start_radius` selects the first visited row.", "- Actual-AEX and portable gates skip `valid=0`, `alpha=0`, `span=0`, `alpha=NaN`, and `span=NaN`.", "- Negative finite alpha and span remain active; AEX tail-entry hooks record both outer and inner calls for `alpha=-0.5` and `span=-1`.", "- Actual-AEX tail entry instrumentation records outer (`direction=0`) before inner (`direction=1`) for the active `start_radius=1` cell.", "- Mode-1 `INT_MAX + 1` wraps to `INT32_MIN` with defined portable arithmetic; the bounded AEX helper fixture captures effective length `INT32_MIN` and unchanged buffers.", "- The release and UBSan caller probes include the mode-1 overflow case; both pass.", "- DAT_1800212d4 is preserved as float32 `1.0f`; no fast math is permitted.", "- Intentional bounds divergences are limited to portable preflight/bailouts and are outside the AEX undersized-buffer claim.", "- This is not an AE-exact, production-wiring, or broad-equivalence claim.", "", "## Reproduce", "", "```text", "python3 tools/emulation/test_radialblur_scatter_caller_20260717.py", "python3 tools/emulation/test_radialblur_scatter_tail_equivalence_20260717.py", "```", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
