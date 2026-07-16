#!/usr/bin/env python3
"""Mac-only function-level equivalence harness for FUN_180001c90.

The harness deliberately calls only the internal scatter-tail helper.  It
does not involve After Effects, Windows, image files, or production sources.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import struct
import sys
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R14

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
TARGET = 0x180001C90
POST_EFFECTIVE_LEN = 0x180001D1D
OUT_JSON = ROOT / "refs/conformance/olmradialblur_scatter_tail_equivalence_20260717.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_scatter_tail_equivalence_20260717.md"

OUTER_TABLE = 0x68
INNER_TABLE = 0x1D528
BASE_LENGTH_OUTER = 0x3A9E8
BASE_LENGTH_INNER = 0x3A9EC
TABLE_LEN = 30000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32(value: float) -> float:
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError:
        return math.copysign(float("inf"), value)


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def from_bits(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value))[0]


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("+Inf" if value > 0 else "-Inf")
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


def trunc_f32_to_i32(value: float) -> int:
    # CVTTSS2SI r32 returns integer-indefinite for NaN and out-of-range input.
    if not math.isfinite(value) or value >= 2147483648.0 or value < -2147483648.0:
        return -2147483648
    return math.trunc(value)


def effective_length(case: dict) -> int:
    resolved = case["base_length"]
    if case["mode"] == 1:
        resolved += case["caller_distance"]
    elif case["mode"] == 2:
        resolved = max(resolved, case["caller_distance"])
    elif case["mode"] == 3:
        resolved = case["caller_distance"]
    return trunc_f32_to_i32(f32(f32(float(min(resolved, 3000))) * f32(case["span_gate"])))


def reference(case: dict, tables: dict[str, list[float]], scatter: list[float], maxima: list[float]) -> tuple[list[float], list[float]]:
    mode = case["direction"]
    resolved = case["base_length"]
    if case["mode"] == 1:
        resolved += case["caller_distance"]
    elif case["mode"] == 2:
        resolved = max(resolved, case["caller_distance"])
    elif case["mode"] == 3:
        resolved = case["caller_distance"]
    resolved = min(resolved, 3000)
    effective_len = effective_length(case)
    if effective_len <= 0:
        return scatter, maxima

    step = f32(float(30000 // effective_len))
    table = tables["inner" if mode else "outer"]
    col = case["angular"]
    count = case["angular_count"]
    inner_cell = case["radius"] * count + col
    for offset in range(1, effective_len):
        if mode == 0:
            col += 1
            if col >= count:
                col = 0
            cell = case["radius"] * count + col
        else:
            inner_cell -= 1
            if inner_cell < case["radius"] * count:
                inner_cell = (case["radius"] + 1) * count - 1
            cell = inner_cell
        weight_index = trunc_f32_to_i32(f32(f32(float(offset)) * step))
        contribution = f32(f32(case["source_alpha"]) * table[weight_index])
        base = cell * 4
        scatter[base + 0] = f32(scatter[base + 0] + f32(contribution * f32(case["source_r"])))
        scatter[base + 1] = f32(scatter[base + 1] + f32(contribution * f32(case["source_g"])))
        scatter[base + 2] = f32(scatter[base + 2] + f32(contribution * f32(case["source_b"])))
        scatter[base + 3] = f32(scatter[base + 3] + contribution)
        old = maxima[cell]
        if old <= contribution and contribution != old:
            maxima[cell] = contribution
    return scatter, maxima


def fixture(name: str, *, direction: int = 0, mode: int = 1, base_length: int = 3,
            caller_distance: int = 2, span_gate: float = 1.0, angular: int = 1,
            radius: int = 0, angular_count: int = 4, source_alpha: float = 1.0,
            source_rgb: tuple[float, float, float] = (2.0, 3.0, 5.0),
            initial_max: dict[int, float] | None = None,
            span_gate_bits: int | None = None, source_alpha_bits: int | None = None) -> dict:
    if span_gate_bits is not None:
        span_gate = from_bits(span_gate_bits)
    if source_alpha_bits is not None:
        source_alpha = from_bits(source_alpha_bits)
    return {
        "name": name, "direction": direction, "mode": mode,
        "base_length": base_length, "caller_distance": caller_distance,
        "span_gate": span_gate, "angular": angular, "radius": radius,
        "angular_count": angular_count, "source_alpha": source_alpha,
        "source_r": source_rgb[0], "source_g": source_rgb[1], "source_b": source_rgb[2],
        "initial_max": initial_max or {},
        "span_gate_bits": bits(span_gate), "source_alpha_bits": bits(source_alpha),
    }


FIXTURES = [
    fixture("mode1_span_adds_caller_distance", mode=1, base_length=2, caller_distance=3),
    fixture("mode2_span_uses_max", mode=2, base_length=2, caller_distance=4),
    fixture("resolved_span_clamps_to_3000", mode=3, caller_distance=4000, span_gate=0.002),
    fixture("effective_len_float32_truncation", mode=3, caller_distance=7, span_gate=0.5),
    fixture("outer_table_sample_origin_is_one", mode=3, caller_distance=3, angular=0),
    fixture("inner_table_base_and_row_tail_underflow", direction=1, mode=3, caller_distance=3, angular=0, radius=1),
    fixture("persistent_max_alpha_is_not_overwritten_by_lower_tap", mode=3, caller_distance=3, angular=0, initial_max={1: 9.0}),
    fixture("nan_source_payload_propagates_and_max_stays", mode=3, caller_distance=3, angular=0,
            source_alpha_bits=0x7FC12345, initial_max={1: 7.0, 2: 8.0}),
    fixture("span_gate_nan_cvtt_sentinel_no_write", mode=3, caller_distance=3, angular=0,
            span_gate_bits=0x7FC54321, initial_max={1: 6.0}),
    fixture("span_gate_out_of_range_cvtt_sentinel_no_write", mode=3, caller_distance=3000,
            angular=0, span_gate_bits=0x7F7FFFFF, initial_max={1: 5.0}),
]


def run_one(loader: AexLoader, case: dict) -> dict:
    count = case["angular_count"]
    cells = (case["radius"] + 3) * count
    context = loader.bump_alloc(0x3AA20, align=64)
    loader.write_bytes(context, b"\x00" * 0x3AA20)
    outer = [f32(0.0)] * TABLE_LEN
    inner = [f32(0.0)] * TABLE_LEN
    # Unique table values make origin, stride, and table-base errors visible.
    for i in range(TABLE_LEN):
        outer[i] = f32(0.001 + i * 0.000031)
        inner[i] = f32(0.007 + i * 0.000047)
    loader.write_f32_array(context + OUTER_TABLE, outer)
    loader.write_f32_array(context + INNER_TABLE, inner)
    mode_offset = 0x2C if case["direction"] else 0x24
    loader.write_bytes(context + mode_offset, struct.pack("<i", case["mode"]))
    loader.write_bytes(context + BASE_LENGTH_OUTER, struct.pack("<ii", case["base_length"], case["base_length"]))

    scatter_addr = loader.bump_alloc(cells * 16, align=64)
    max_addr = loader.bump_alloc(cells * 4, align=64)
    scatter = [f32(0.0)] * (cells * 4)
    maxima = [f32(0.0)] * cells
    for cell, value in case["initial_max"].items():
        maxima[cell] = f32(value)
    loader.write_f32_array(scatter_addr, scatter)
    loader.write_f32_array(max_addr, maxima)

    args = [context, case["direction"], case["caller_distance"], case["angular"], case["radius"],
            bits(case["source_alpha"]), bits(case["source_r"]), bits(case["source_g"]),
            bits(case["source_b"]), bits(case["span_gate"]), count, scatter_addr, max_addr]
    captured: dict[str, int] = {}

    def capture_effective_len(ld: AexLoader, _address: int, _size: int) -> None:
        raw = ld.uc.reg_read(UC_X86_REG_R14) & 0xFFFFFFFF
        captured["effective_len"] = raw if raw < 0x80000000 else raw - 0x100000000

    loader.add_code_hook(POST_EFFECTIVE_LEN, capture_effective_len)
    emu = loader.call_function(TARGET, int_args=args, max_instructions=2_000_000)
    actual_scatter = loader.read_f32_array(scatter_addr, len(scatter))
    actual_maxima = loader.read_f32_array(max_addr, len(maxima))

    expected_scatter, expected_maxima = reference(case, {"outer": outer, "inner": inner}, scatter[:], maxima[:])
    actual_bits = [bits(v) for v in actual_scatter + actual_maxima]
    expected_bits = [bits(v) for v in expected_scatter + expected_maxima]
    expected_effective_len = effective_length(case)
    actual_effective_len = captured.get("effective_len")
    first = next((i for i, (a, e) in enumerate(zip(actual_bits, expected_bits)) if a != e), None)
    return {
        "name": case["name"], "inputs": json_safe(case),
        "expected_effective_len_i32": expected_effective_len,
        "actual_effective_len_i32": actual_effective_len,
        "actual_scatter_bits": [f"0x{v:08x}" for v in actual_bits[:len(actual_scatter)]],
        "expected_scatter_bits": [f"0x{v:08x}" for v in expected_bits[:len(expected_scatter)]],
        "actual_max_bits": [f"0x{v:08x}" for v in actual_bits[len(actual_scatter):]],
        "expected_max_bits": [f"0x{v:08x}" for v in expected_bits[len(expected_scatter):]],
        "first_difference_index": first,
        "exact": first is None and actual_effective_len == expected_effective_len,
        "instructions": emu["instructions"],
    }


def write_cpp_fixture_vector(report: dict, path: Path) -> None:
    def u32(value: int) -> bytes:
        return struct.pack("<I", value & 0xFFFFFFFF)

    def i32(value: int) -> bytes:
        return struct.pack("<i", value)

    def fixture_f32(case: dict, key: str) -> bytes:
        return u32(bits(case[key]))

    with path.open("wb") as output:
        output.write(u32(0x31544252))  # RBT1
        output.write(u32(1))
        output.write(u32(len(report["fixtures"])))
        for item in report["fixtures"]:
            case = FIXTURES[next(i for i, f in enumerate(FIXTURES) if f["name"] == item["name"])]
            name = item["name"].encode("utf-8")
            output.write(u32(len(name)))
            output.write(name)
            for key in ("direction", "mode", "base_length", "caller_distance", "angular", "radius", "angular_count"):
                output.write(i32(case[key]))
            for key in ("span_gate", "source_alpha", "source_r", "source_g", "source_b"):
                output.write(fixture_f32(case, key))
            seeds = list(case["initial_max"].items())
            output.write(u32(len(seeds)))
            for cell, value in seeds:
                output.write(u32(cell))
                output.write(u32(bits(value)))
            actual_scatter = item["actual_scatter_bits"]
            actual_max = item["actual_max_bits"]
            output.write(u32(len(actual_scatter)))
            for word in actual_scatter:
                output.write(u32(int(word, 16)))
            output.write(u32(len(actual_max)))
            for word in actual_max:
                output.write(u32(int(word, 16)))


def run_cpp_probe(report: dict) -> dict:
    compiler = os.environ.get("CXX", "c++")
    source = Path(__file__).with_name("radialblur_scatter_tail_probe.cpp")
    with tempfile.TemporaryDirectory(prefix="olm-radialblur-scatter-") as directory:
        directory_path = Path(directory)
        vector = directory_path / "fixtures.bin"
        binary = directory_path / "radialblur_scatter_tail_probe"
        write_cpp_fixture_vector(report, vector)
        command = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                   "-fno-fast-math", "-ffp-contract=off", "-Icore",
                   "core/radialblur_scatter_tail.cpp", str(source), "-o", str(binary)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode != 0:
            return {"status": "build-fail", "command": command, "stderr": build.stderr}
        probe = subprocess.run([str(binary), str(vector)], cwd=ROOT, capture_output=True, text=True)
        ubsan_binary = directory_path / "radialblur_scatter_tail_probe_ubsan"
        ubsan_command = [compiler, "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                         "-fno-fast-math", "-ffp-contract=off", "-fsanitize=undefined",
                         "-fno-sanitize-recover=undefined", "-Icore",
                         "core/radialblur_scatter_tail.cpp", str(source), "-o", str(ubsan_binary)]

        def stable_command(command: list[str]) -> list[str]:
            prefix = str(directory_path)
            return [part.replace(prefix, "<tmp>") for part in command]

        ubsan_build = subprocess.run(ubsan_command, cwd=ROOT, capture_output=True, text=True)
        if ubsan_build.returncode == 0:
            ubsan_run = subprocess.run([str(ubsan_binary), str(vector)], cwd=ROOT,
                                       capture_output=True, text=True)
            ubsan = {
                "status": "pass" if ubsan_run.returncode == 0 else "fail",
                "command": stable_command(ubsan_command), "stdout": ubsan_run.stdout,
                "stderr": ubsan_run.stderr, "returncode": ubsan_run.returncode,
            }
        else:
            ubsan = {"status": "build-fail", "command": stable_command(ubsan_command),
                     "stderr": ubsan_build.stderr, "returncode": ubsan_build.returncode}
        return {
            "status": "pass" if probe.returncode == 0 and ubsan["status"] == "pass" else "fail",
            "command": stable_command(command),
            "stdout": probe.stdout,
            "stderr": probe.stderr,
            "returncode": probe.returncode,
            "ubsan": ubsan,
        }


def main() -> int:
    actual_hash = sha256(AEX.read_bytes())
    report: dict = {
        "schema": "olmradialblur.scatter-tail-equivalence/1",
        "platform": "Mac-only Unicorn execution of checked-in AEX; no AE, Windows, or PNG",
        "target": hex(TARGET), "aex": str(AEX.relative_to(ROOT)),
        "pinned_aex_sha256": AEX_SHA256, "actual_aex_sha256": actual_hash,
        "status": "blocked-hash-mismatch" if actual_hash != AEX_SHA256 else "running",
        "fixtures": [],
    }
    if actual_hash != AEX_SHA256:
        OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
        OUT_MD.write_text("# OLMRadialBlur scatter-tail equivalence\n\n- **Status:** `blocked-hash-mismatch`\n- The checked-in AEX does not match the pinned contract binary; no emulation was attempted.\n")
        print(json.dumps({"status": report["status"], "actual": actual_hash, "pinned": AEX_SHA256}, indent=2))
        return 2

    for case in FIXTURES:
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        result = run_one(loader, case)
        report["fixtures"].append(result)
    report["python_reference_status"] = "pass" if all(x["exact"] for x in report["fixtures"]) else "fail"
    report["cpp_probe"] = run_cpp_probe(report)
    report["status"] = "pass" if report["python_reference_status"] == "pass" and report["cpp_probe"]["status"] == "pass" else "fail"
    report["contract"] = {
        "proven_domain": "the ten recorded fixtures with valid 30000-entry tables, angular_count=4, and destination buffers sized for every reached cell",
        "mode_selection": "mode1=base+caller, mode2=max(base,caller), mode3=caller",
        "resolved_span_clamp": "upper clamp to 3000 only",
        "effective_len": "CVTTSS2SI-r32(float32(resolved_span) * float32(span_gate)); NaN and out-of-range return INT32_MIN",
        "table_step": "float32(trunc(30000 / effective_len))",
        "sample_offsets": "1 <= offset < effective_len",
        "table_bases": {"outer": "ctx+0x68", "inner": "ctx+0x1d528"},
        "inner_underflow": "decrement destination cell; on underflow restart at (radius+1)*angular_count-1 row tail",
        "max_alpha": "update iff old <= contribution and contribution != old; persistent destination plane",
        "arithmetic": "float32 multiply/add at each SSE scalar operation; exact raw float32 output comparison",
        "bounds_safety_divergence": "portable core returns early when computed cell >= cell_count; AEX performs no equivalent bounds check, and behavior for undersized buffers is outside the proven domain",
        "nan_scope": "AEX-proven only for source payload 0x7fc12345 and span-gate payload 0x7fc54321 in the recorded fixtures; no general NaN-payload claim",
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    lines = [
        "# OLMRadialBlur Scatter-Tail Equivalence",
        "",
        f"- Status: `{report['status']}`",
        f"- Target: `{hex(TARGET)}` in `{AEX.relative_to(ROOT)}`",
        f"- Pinned AEX SHA-256: `{AEX_SHA256}`",
        "- Execution: Mac-local Unicorn only; no AE, Windows, PNG, or production edits.",
        f"- C++ portable core probe: `{report['cpp_probe']['status']}`.",
        f"- C++ UBSan replay: `{report['cpp_probe']['ubsan']['status']}`.",
        "",
        "## Contract",
        "",
        "- Mode 1 adds caller distance; mode 2 takes max; mode 3 uses caller distance; resolved span is upper-clamped at 3000.",
        "- Effective length uses `CVTTSS2SI r32`: truncate finite in-range float32 toward zero, and return `INT32_MIN` for NaN or out-of-range input. The helper exits for that non-positive sentinel.",
        "- Samples use offsets `1 <= offset < effective_len`, with outer table `ctx+0x68` and inner table `ctx+0x1d528`.",
        "- Outer wraps within the current radius row. Inner underflow advances to the next radius row tail.",
        "- The source-NaN claim is limited to AEX-proven payload `0x7fc12345`; it propagates unchanged to two RGBA destinations while seeded max-alpha values remain unchanged. Span-gate payload `0x7fc54321` and the overflowing finite fixture both produce the captured `INT32_MIN` sentinel and no writes.",
        "- The contract assumes valid 30,000-entry tables, `angular_count=4`, and buffers covering every reached fixture cell. The portable `cell >= cell_count` early return is an intentional safety divergence; the AEX has no equivalent check, and undersized-buffer behavior is not claimed.",
        "",
        "## Fixtures",
        "",
        "| Fixture | Effective len AEX/ref | Exact buffers | Instructions |",
        "| --- | --- | --- | ---: |",
    ]
    for item in report["fixtures"]:
        lengths = f"{item['actual_effective_len_i32']}/{item['expected_effective_len_i32']}"
        lines.append(f"| `{item['name']}` | `{lengths}` | `{item['exact']}` | {item['instructions']} |")
    lines += [
        "",
        "## Reproduction",
        "",
        "```text",
        "python3 tools/emulation/test_radialblur_scatter_tail_equivalence_20260717.py",
        "```",
        "",
        "## Interpretation",
        "",
        "A `pass` is a function-level equivalence result for the pinned AEX contract, not an AE-host or rendered-image claim. Any hash mismatch or byte mismatch fails closed and blocks production implementation decisions.",
        "",
        "The release and UBSan C++ probes use `-fno-fast-math -ffp-contract=off` and consume the ten recorded AEX output buffers from this report through a temporary binary fixture vector.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "fixtures": len(report["fixtures"]), "all_exact": report["status"] == "pass"}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
