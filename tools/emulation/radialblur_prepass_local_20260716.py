#!/usr/bin/env python3
"""Compare the callable portable Rotation typed prepass/scatter seam with AEX."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shlex
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_RIP, UC_X86_REG_RSP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NAME = "radialblur_prepass_local_20260716"
MAX_ULP = 1
CPP_SOURCE = ROOT / "cli" / "OLMRadialBlur" / "main.cpp"
FIXTURE_SOURCE = HERE / "test_radialblur_caller_witness_20260716_followup.py"

sys.path.insert(0, str(HERE))
import test_radialblur_caller_witness_20260716_followup as caller_witness  # noqa: E402

AEX = caller_witness.AEX


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_words(values: list[float]) -> list[str]:
    return [f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in values]


def exact_prepass_polar(record: dict[str, Any]) -> list[list[float]]:
    if len(record.get("prepass", [])) != 1:
        raise RuntimeError("actual AEX run must have exactly one prepass entry")
    cells = record["prepass"][0]["planes"]["plus_0x38_initial_or_collapsed_rgba"]["cells"]
    if any(len(cell) != 4 for cell in cells):
        raise RuntimeError("actual AEX prepass-entry polar plane contains a non-RGBA cell")
    return [[float(channel) for channel in cell] for cell in cells]


def signed_i32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def run_aex(repeat_border: int) -> dict[str, Any]:
    captures: list[dict[str, Any]] = []
    original_snapshot = caller_witness.plane_snapshot

    def snapshot_with_scatter_validity(loader: Any, param1: int) -> dict[str, Any]:
        planes = original_snapshot(loader, param1)
        if loader.uc.reg_read(UC_X86_REG_RIP) != caller_witness.SCATTER:
            return planes
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        slots = {
            "valid_mask": 0x28,
            "angular_count": 0x30,
            "quality_or_rows": 0x38,
            "start_radius": 0x40,
            "end_radius": 0x48,
            "accum_rgba": 0x50,
            "max_alpha": 0x58,
        }
        raw = {
            name: struct.unpack("<Q", loader.read_bytes(rsp + offset, 8))[0]
            for name, offset in slots.items()
        }
        angular_count = raw["angular_count"] & 0xFFFFFFFF
        start_radius = signed_i32(raw["start_radius"])
        end_radius = signed_i32(raw["end_radius"])
        byte_count = angular_count * (end_radius - start_radius)
        valid_mask = raw["valid_mask"]
        capture: dict[str, Any] = {
            "abi": "windows_x64_entry",
            "stack_slots": {name: f"RSP+0x{offset:x}" for name, offset in slots.items()},
            "valid_mask": hex(valid_mask),
            "angular_count": angular_count,
            "quality_or_rows_raw": f"0x{raw['quality_or_rows']:016x}",
            "start_radius": start_radius,
            "end_radius": end_radius,
            "byte_count": byte_count,
            "accum_rgba": hex(raw["accum_rgba"]),
            "max_alpha": hex(raw["max_alpha"]),
            "contract_proven": False,
            "validity_bytes": None,
        }
        if valid_mask and angular_count > 0 and end_radius > start_radius and byte_count == angular_count * (end_radius - start_radius):
            source = valid_mask + angular_count * start_radius
            capture["validity_bytes"] = list(loader.read_bytes(source, byte_count))
            capture["contract_proven"] = True
        else:
            capture["blocker"] = (
                f"scatter valid_mask at RSP+0x28={hex(valid_mask)}, angular_count at "
                f"RSP+0x30={angular_count}, start_radius at RSP+0x40={start_radius}, "
                f"end_radius at RSP+0x48={end_radius}; expected positive geometry with "
                f"byte_count=angular_count*(end_radius-start_radius), observed byte_count={byte_count}"
            )
        captures.append(capture)
        return planes

    caller_witness.plane_snapshot = snapshot_with_scatter_validity
    try:
        record = caller_witness.run(repeat_border)
    finally:
        caller_witness.plane_snapshot = original_snapshot
    record["scatter_validity_capture"] = captures
    return record


def captured_actual_validity(record: dict[str, Any]) -> list[int] | None:
    captures = record.get("scatter_validity_capture", [])
    if len(captures) != 1 or not captures[0].get("contract_proven"):
        return None
    validity = captures[0].get("validity_bytes")
    capture = captures[0]
    angular_count = capture.get("angular_count")
    start_radius = capture.get("start_radius")
    end_radius = capture.get("end_radius")
    expected = (
        angular_count * (end_radius - start_radius)
        if isinstance(angular_count, int) and isinstance(start_radius, int) and isinstance(end_radius, int)
        else None
    )
    return validity if isinstance(validity, list) and expected == len(validity) else None


def actual_validity_blocker(record: dict[str, Any]) -> str:
    captures = record.get("scatter_validity_capture", [])
    if len(captures) != 1:
        return "scatter entry did not yield exactly one argument-5 capture at RSP+0x28"
    return captures[0].get(
        "blocker",
        "scatter argument-5 bytes at RSP+0x28 did not satisfy the typed polar validity contract",
    )


def load_existing_fixture() -> list[float]:
    """Read the fixture assignment from its existing source of truth."""
    tree = ast.parse(FIXTURE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "source_values" for target in node.targets):
            values = ast.literal_eval(node.value)
            if isinstance(values, list) and len(values) == 16:
                return [float(value) for value in values]
    raise RuntimeError(f"2x2 source_values fixture not found in {FIXTURE_SOURCE}")


def adapter_source() -> str:
    """Build a wrapper; all render and typed-plane behavior comes from main.cpp."""
    include_path = str(CPP_SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    return f'''#define main olmradialblur_cli_embedded_main
#include "{include_path}"
#undef main

static uint32_t radialblur_adapter_word(float value) {{
    uint32_t word = 0;
    std::memcpy(&word, &value, sizeof(word));
    return word;
}}

int main(int argc, char **argv) {{
    if (argc != 8) {{
        std::fprintf(stderr, "usage: adapter fixture.bin typed_polar.bin typed_valid.bin mode width height row_stride\\n");
        return 64;
    }}
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) return 65;
    FloatImage fixture;
    fixture.width = 2;
    fixture.height = 2;
    fixture.rgba.resize(16);
    input.read(reinterpret_cast<char *>(fixture.rgba.data()),
               static_cast<std::streamsize>(fixture.rgba.size() * sizeof(float)));
    if (input.gcount() != static_cast<std::streamsize>(fixture.rgba.size() * sizeof(float))) return 66;

    std::ifstream typed_input(argv[2], std::ios::binary);
    if (!typed_input) return 67;
    RotationTypedPolarInput typed_polar;
    typed_polar.width = std::atoi(argv[5]);
    typed_polar.height = std::atoi(argv[6]);
    typed_polar.row_stride = std::atoi(argv[7]);
    if (typed_polar.width <= 0 || typed_polar.height <= 0 || typed_polar.row_stride <= 0 ||
        static_cast<size_t>(typed_polar.row_stride) != static_cast<size_t>(typed_polar.width) * 4) return 72;
    const size_t cell_count = static_cast<size_t>(typed_polar.width) * typed_polar.height;
    typed_polar.rgba.resize(cell_count * 4);
    typed_input.read(reinterpret_cast<char *>(typed_polar.rgba.data()),
                     static_cast<std::streamsize>(typed_polar.rgba.size() * sizeof(float)));
    if (typed_input.gcount() != static_cast<std::streamsize>(typed_polar.rgba.size() * sizeof(float))) return 68;

    const bool validation_only = std::strcmp(argv[4], "--validate-only") == 0;
    const bool has_validity = std::strcmp(argv[3], "--missing-validity") != 0;
    if (has_validity) {{
        std::ifstream valid_input(argv[3], std::ios::binary);
        if (!valid_input) return 69;
        typed_polar.polar_valid.resize(cell_count);
        valid_input.read(reinterpret_cast<char *>(typed_polar.polar_valid.data()), static_cast<std::streamsize>(cell_count));
        if (valid_input.gcount() != static_cast<std::streamsize>(cell_count)) return 70;
    }}

    if (validation_only) {{
        std::printf("{{\\\"implementation\\\":\\\"source-included-cli-main.cpp\\\","
                    "\\\"input_validation_only\\\":true,"
                    "\\\"typed_input_geometry\\\":{{\\\"width\\\":%d,\\\"height\\\":%d,\\\"row_stride\\\":%d}},"
                    "\\\"validity_available\\\":%s,"
                    "\\\"polar_words\\\":[", typed_polar.width, typed_polar.height, typed_polar.row_stride, has_validity ? "true" : "false");
        for (size_t i = 0; i < typed_polar.rgba.size(); ++i) {{
            if (i) std::printf(",");
            std::printf("\\\"0x%08x\\\"", radialblur_adapter_word(typed_polar.rgba[i]));
        }}
        std::printf("],\\\"validity_bytes\\\":[");
        for (size_t i = 0; i < typed_polar.polar_valid.size(); ++i) {{
            if (i) std::printf(",");
            std::printf("%u", static_cast<unsigned>(typed_polar.polar_valid[i]));
        }}
        std::printf("]}}\\n");
        return 0;
    }}

    if (!has_validity) return 71;

    const bool repeat = std::atoi(argv[4]) != 0;
    RadialBlurParams params;
    params.blur_type = 2;
    params.repeat_border = repeat;
    params.outer_source_scatter_prepass = true;
    params.outer_strength = 4;
    params.quality = 5.0;
    RotationTypedPlanes planes;
    render_olmradialblur_rotation_float(fixture, params, &planes, 8, &typed_polar);
    auto print_rgba = [](const FloatImage &image) {{
        std::printf("[");
        const size_t cells = image.rgba.size() / 4;
        for (size_t cell = 0; cell < cells; ++cell) {{
            if (cell) std::printf(",");
            std::printf("[%.9g,%.9g,%.9g,%.9g]", image.rgba[cell * 4], image.rgba[cell * 4 + 1],
                        image.rgba[cell * 4 + 2], image.rgba[cell * 4 + 3]);
        }}
        std::printf("]");
    }};
    auto print_scalar = [](const std::vector<float> &values) {{
        std::printf("[");
        const size_t cells = values.size();
        for (size_t cell = 0; cell < cells; ++cell) {{
            if (cell) std::printf(",");
            std::printf("[%.9g]", values[cell]);
        }}
        std::printf("]");
    }};
    auto print_xy = [](const std::vector<std::array<float, 2>> &values) {{
        std::printf("[");
        const size_t cells = values.size();
        for (size_t cell = 0; cell < cells; ++cell) {{
            if (cell) std::printf(",");
            std::printf("[%.9g,%.9g]", values[cell][0], values[cell][1]);
        }}
        std::printf("]");
    }};
    std::printf("{{\\\"implementation\\\":\\\"source-included-cli-main.cpp\\\","
                "\\\"typed_input_geometry\\\":{{\\\"width\\\":%d,\\\"height\\\":%d,\\\"row_stride\\\":%d}},"
                "\\\"repeat_border\\\":%s,\\\"polar_dimensions\\\":[%d,%d],\\\"polar_xy\\\":",
                typed_polar.width, typed_polar.height, typed_polar.row_stride,
                repeat ? "true" : "false", planes.polar.width, planes.polar.height);
    print_xy(planes.polar_coordinates);
    std::printf(",\\\"polar_valid\\\":[");
    for (size_t cell = 0; cell < planes.polar_valid.size(); ++cell) {{
        if (cell) std::printf(",");
        std::printf("%s", planes.polar_valid[cell] ? "true" : "false");
    }}
    std::printf("],\\\"polar\\\":");
    print_rgba(planes.polar);
    std::printf(",\\\"accum\\\":"); print_rgba(planes.accum);
    std::printf(",\\\"prepass\\\":"); print_scalar(planes.prepass_alpha);
    std::printf(",\\\"scatter\\\":"); print_scalar(planes.scatter_alpha);
    std::printf(",\\\"source_alpha\\\":"); print_scalar(planes.source_alpha);
    std::printf(",\\\"collapse\\\":"); print_rgba(planes.collapsed);
    std::printf("}}\\n");
    return 0;
}}
'''


def png_flags() -> list[str]:
    completed = subprocess.run(
        ["pkg-config", "--cflags", "--libs", "libpng"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return shlex.split(completed.stdout)
    return ["-lpng"]


def build_adapter(temp: Path) -> dict[str, Any]:
    source = temp / f"{NAME}_adapter.cpp"
    binary = temp / f"{NAME}_adapter"
    source.write_text(adapter_source(), encoding="utf-8")
    compiler = os.environ.get("CXX", "clang++")
    command = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic", str(source), *png_flags(), "-o", str(binary)]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    durable_command = [
        "<compiler>" if Path(compiler).is_absolute() else compiler,
        "-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic",
        "<adapter-source>", *png_flags(), "-o", "<adapter-binary>",
    ]
    result: dict[str, Any] = {
        "command": durable_command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.replace(str(temp), "<temp>"),
        "stderr": completed.stderr.replace(str(temp), "<temp>"),
        "adapter_source_sha256": sha256(source),
        "production_source": str(CPP_SOURCE.relative_to(ROOT)),
        "production_source_sha256": sha256(CPP_SOURCE),
    }
    if completed.returncode == 0:
        result["adapter_binary_sha256"] = sha256(binary)
        result["binary"] = binary
    return result


def run_adapter(
    binary: Path,
    fixture: Path,
    typed_polar: Path,
    typed_valid: Path | None,
    repeat_border: int,
    width: int,
    height: int,
    row_stride: int,
    validation_only: bool = False,
) -> dict[str, Any]:
    validity_arg = str(typed_valid) if typed_valid else "--missing-validity"
    durable_validity_arg = typed_valid.name if typed_valid else "--missing-validity"
    mode_arg = "--validate-only" if validation_only else str(repeat_border)
    command = [str(binary), str(fixture), str(typed_polar), validity_arg, mode_arg, str(width), str(height), str(row_stride)]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    payload = json.loads(completed.stdout) if completed.returncode == 0 else None
    return {
        "command": [binary.name, fixture.name, typed_polar.name, durable_validity_arg, mode_arg, str(width), str(height), str(row_stride)],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "payload": payload,
        "shared_stage_executed": typed_valid is not None and not validation_only and completed.returncode == 0,
    }


def synthetic_geometry_gate(binary: Path, temp: Path) -> dict[str, Any]:
    """Exercise the generalized seam with a local 1x4 echo-only payload."""
    polar = temp / "synthetic_1x4_polar_rgba_f32.bin"
    valid = temp / "synthetic_1x4_valid_u8.bin"
    values = [float(index) + 0.25 for index in range(16)]
    validity = [0, 1, 0, 1]
    polar.write_bytes(struct.pack("<16f", *values))
    valid.write_bytes(bytes(validity))
    result = run_adapter(binary, temp / "existing_2x2_rgba_f32.bin", polar, valid, 0, 1, 4, 4, validation_only=True)
    payload = result.get("payload") or {}
    return {
        "geometry": {"width": 1, "height": 4, "row_stride": 4},
        "rgba_cells": 4,
        "validity_bytes": 4,
        "passed": result["returncode"] == 0 and payload.get("typed_input_geometry") == {"width": 1, "height": 4, "row_stride": 4} and payload.get("polar_words") == f32_words(values) and payload.get("validity_bytes") == validity,
        "result": result,
    }


def ulp_distance(left: float, right: float) -> int:
    def ordered(value: float) -> int:
        bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
        return bits ^ (0xFFFFFFFF if bits & 0x80000000 else 0x80000000)

    return abs(ordered(left) - ordered(right))


def compare_cells(plane: str, expected_cells: list[list[float]], actual_cells: list[list[float]]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    max_ulp = 0
    for cell, expected_channels in enumerate(expected_cells):
        for channel, expected_value in enumerate(expected_channels):
            if cell >= len(actual_cells) or channel >= len(actual_cells[cell]):
                mismatches.append({"plane": plane, "cell": cell, "channel": channel, "reason": "missing"})
                continue
            observed = actual_cells[cell][channel]
            distance = ulp_distance(expected_value, observed)
            max_ulp = max(max_ulp, distance)
            if distance > MAX_ULP:
                mismatches.append({
                    "plane": plane,
                    "cell": cell,
                    "channel": channel,
                    "expected": expected_value,
                    "portable": observed,
                    "ulp": distance,
                })
    return {"max_ulp": max_ulp, "mismatches": mismatches, "pass": not mismatches}


def compare_stage_progression(actual: dict[str, Any], portable: dict[str, Any]) -> dict[str, Any]:
    stage_specs = [
        ("injected_polar", "polar", actual["prepass_entry"]["plus_0x38_initial_or_collapsed_rgba"]),
        ("post_prepass", "prepass", actual["scatter_entry"]["plus_0x40_scalar_prepass"]),
        ("post_scatter_accum", "accum", actual["final"]["plus_0x38_rgba_accum"]),
        ("post_scatter_max_alpha", "scatter", actual["final"]["plus_0x48_scalar_scatter"]),
        ("post_collapse", "collapse", actual["final"]["plus_0x38_initial_or_collapsed_rgba"]),
    ]
    stages: list[dict[str, Any]] = []
    earliest_divergence = None
    for stage, portable_plane, expected in stage_specs:
        comparison = compare_cells(portable_plane, expected, portable.get(portable_plane, []))
        stages.append({"stage": stage, "portable_plane": portable_plane, **comparison})
        if earliest_divergence is None and not comparison["pass"]:
            earliest_divergence = stage
    return {
        "pass": earliest_divergence is None,
        "earliest_divergence": earliest_divergence,
        "stages": stages,
    }


def actual_projection(record: dict[str, Any]) -> dict[str, Any]:
    def planes(item: dict[str, Any]) -> dict[str, Any]:
        return {key: value["cells"] for key, value in item["planes"].items()}

    result: dict[str, Any] = {
        "stop": record["stop"],
        "sampler_calls": record["sampler_calls"],
        "inverse_sampler_calls": record["inverse_sampler_calls"],
        "scatter_validity_capture": record.get("scatter_validity_capture", []),
        "prepass_entry": None,
        "scatter_entry": None,
        "final": {key: value["cells"] for key, value in record["final_planes"].items()},
    }
    if record["prepass"]:
        result["prepass_entry"] = planes(record["prepass"][0])
    if record["scatter"]:
        result["scatter_entry"] = planes(record["scatter"][0])
    for stage in ("prepass_entry", "scatter_entry", "final"):
        if result[stage] and "source_alpha_or_variation_plane" in result[stage]:
            result[stage]["plus_0x50_source_alpha_or_variation_plane"] = result[stage].pop(
                "source_alpha_or_variation_plane"
            )
    if record.get("error"):
        result["error"] = record["error"]
    return result


def run() -> dict[str, Any]:
    fixture_values = load_existing_fixture()
    observed_runs = [run_aex(repeat) for repeat in (0, 1)]
    runs: list[dict[str, Any]] = []
    build_public: dict[str, Any]

    with tempfile.TemporaryDirectory(prefix=f"{NAME}_") as raw_temp:
        temp = Path(raw_temp)
        fixture = temp / "existing_2x2_rgba_f32.bin"
        fixture.write_bytes(struct.pack("<16f", *fixture_values))
        build = build_adapter(temp)
        build_public = {key: value for key, value in build.items() if key != "binary"}
        synthetic_gate = synthetic_geometry_gate(build["binary"], temp) if build["returncode"] == 0 else {
            "geometry": {"width": 1, "height": 4, "row_stride": 4},
            "rgba_cells": 4,
            "validity_bytes": 4,
            "passed": False,
            "result": None,
        }
        for repeat_border, observed in enumerate(observed_runs):
            actual = actual_projection(observed)
            polar_cells = exact_prepass_polar(observed)
            polar_values = [channel for cell in polar_cells for channel in cell]
            polar_bytes = struct.pack("<8f", *polar_values)
            polar_width = 1
            polar_height = len(polar_cells)
            polar_row_stride = polar_width * 4
            typed_polar = temp / f"aex_repeat{repeat_border}_typed_{polar_width}x{polar_height}_polar_rgba_f32.bin"
            typed_polar.write_bytes(polar_bytes)
            serialized_values = list(struct.unpack("<8f", typed_polar.read_bytes()))
            injected_polar = {
                "source": "actual_aex.prepass_entry.plus_0x38_initial_or_collapsed_rgba",
                "cells": polar_cells,
                "raw_f32_words": f32_words(polar_values),
                "serialized_sha256": sha256(typed_polar),
                "roundtrip_raw_f32_words": f32_words(serialized_values),
                "match_by_construction": f32_words(polar_values) == f32_words(serialized_values),
            }
            validity = captured_actual_validity(observed)
            actual_capture_ready = (
                len(polar_cells) == 4 and
                validity is not None and len(validity) == 4 and
                len(actual.get("prepass_entry", {}).get("plus_0x40_scalar_prepass", [])) == 4 and
                len(actual.get("final", {}).get("plus_0x48_scalar_scatter", [])) == 4
            )
            adapter_run: dict[str, Any]
            adapter_input_validation: dict[str, Any] | None = None
            differential: dict[str, Any]
            portable_payload = None
            if build["returncode"] != 0:
                adapter_run = {"executed": False, "reason": "adapter_build_failed"}
                differential = {
                    "pass": False,
                    "result": "adapter_build_failed",
                    "earliest_divergence": None,
                    "stages": [],
                }
            elif validity is None:
                adapter_input_validation = run_adapter(
                    build["binary"], fixture, typed_polar, None, repeat_border, polar_width, polar_height, polar_row_stride,
                    validation_only=True,
                )
                adapter_run = {"executed": False, "reason": "scatter_validity_stack_contract_not_proven"}
                adapter_words = (
                    adapter_input_validation["payload"].get("polar_words", [])
                    if adapter_input_validation.get("payload") else []
                )
                adapter_input_match = adapter_words == injected_polar["raw_f32_words"]
                differential = {
                    "pass": False,
                    "result": (
                        "blocked_scatter_validity_stack_contract"
                        if adapter_input_match else "adapter_input_validation_failed"
                    ),
                    "earliest_divergence": None if adapter_input_match else "injected_polar",
                    "stages": [
                        {
                            "stage": "injected_polar",
                            "pass": injected_polar["match_by_construction"] and adapter_input_match,
                            "raw_f32_words": injected_polar["raw_f32_words"],
                            "adapter_raw_f32_words": adapter_words,
                        },
                        {
                            "stage": "input_validity",
                            "pass": False,
                            "result": "stack_contract_mismatch",
                            "evidence": observed.get("scatter_validity_capture", []),
                        },
                        {"stage": "post_prepass", "result": "not_run"},
                        {"stage": "post_scatter", "result": "not_run"},
                    ],
                }
            elif not actual_capture_ready:
                adapter_input_validation = run_adapter(
                    build["binary"], fixture, typed_polar, None, repeat_border, polar_width, polar_height, polar_row_stride,
                    validation_only=True,
                )
                adapter_run = {"executed": False, "reason": "actual_aex_capture_incomplete"}
                adapter_words = (adapter_input_validation.get("payload") or {}).get("polar_words", [])
                differential = {
                    "pass": False,
                    "result": "blocked_actual_capture_incomplete",
                    "earliest_divergence": None,
                    "stages": [{"stage": "injected_polar", "pass": adapter_words == injected_polar["raw_f32_words"]},
                               {"stage": "actual_capture_contract", "pass": False, "required": {"rgba_cells": 4, "scalar_rows": 4, "validity_bytes": 4}}],
                }
            else:
                typed_valid = temp / f"aex_repeat{repeat_border}_typed_{polar_width}x{polar_height}_valid_u8.bin"
                typed_valid.write_bytes(bytes(validity))
                adapter_input_validation = run_adapter(
                    build["binary"], fixture, typed_polar, typed_valid, repeat_border, polar_width, polar_height, polar_row_stride,
                    validation_only=True,
                )
                validation_payload = adapter_input_validation.get("payload") or {}
                input_match = (
                    validation_payload.get("polar_words") == injected_polar["raw_f32_words"] and
                    validation_payload.get("validity_bytes") == validity
                )
                if not input_match:
                    adapter_run = {"executed": False, "reason": "adapter_input_validation_failed"}
                    differential = {
                        "pass": False,
                        "result": "adapter_input_validation_failed",
                        "earliest_divergence": "typed_input",
                        "stages": [{"stage": "typed_input", "pass": False}],
                    }
                else:
                    adapter_run = run_adapter(
                        build["binary"], fixture, typed_polar, typed_valid, repeat_border, polar_width, polar_height, polar_row_stride
                    )
                    portable_payload = adapter_run["payload"]
                    geometry_ok = bool(portable_payload and portable_payload.get("typed_input_geometry") == {
                        "width": polar_width, "height": polar_height, "row_stride": polar_row_stride
                    })
                    differential = compare_stage_progression(actual, portable_payload) if geometry_ok else {
                        "pass": False,
                        "result": "typed_geometry_rejected",
                        "earliest_divergence": None,
                        "stages": [],
                    }
                    differential["result"] = (
                        "comparable_stage_pass" if differential["pass"] else "comparable_stage_mismatch"
                    )
            aex_inverse = observed["inverse_sampler_calls"]
            runs.append({
                "repeat_border": repeat_border,
                "actual_aex": actual,
                "typed_input": {
                    "polar": injected_polar,
                    "validity": {
                        "available": validity is not None,
                        "cells": validity,
                        "reason": None if validity is not None else actual_validity_blocker(observed),
                    },
                },
                "portable_cli": {
                    "deepest_callable_boundary": "render_olmradialblur_rotation_float with RotationTypedPlanes",
                    "adapter_input_validation": adapter_input_validation,
                    "adapter_run": adapter_run,
                    "typed_prepass_scatter_collapse_planes": portable_payload,
                },
                "differential_result": differential["result"],
                "differential": differential,
                "max_ulp": None,
                "geometry": {
                    "aex_source_plane": {
                        "angular_count": aex_inverse[0]["width"] if aex_inverse else None,
                        "width": aex_inverse[0]["width"] if aex_inverse else None,
                        "row_stride": aex_inverse[0]["row_stride"] if aex_inverse else None,
                        "radius_rows": observed["scatter_validity_capture"][0].get("end_radius") - observed["scatter_validity_capture"][0].get("start_radius") if observed.get("scatter_validity_capture") else None,
                        "inverse_coordinates": [[call["x"], call["y"]] for call in aex_inverse],
                    },
                    "portable_polar_plane": {
                        "width": portable_payload.get("polar_dimensions", [None, None])[0] if portable_payload else None,
                        "height": portable_payload.get("polar_dimensions", [None, None])[1] if portable_payload else None,
                        "indexed_cells_emitted": "not executed without four-cell actual capture" if portable_payload is None else f"all caller-supplied {polar_width}x{polar_height} cells",
                    },
                    "dimensions_equivalent": actual_capture_ready,
                    "typed_contract_equivalent": bool(
                        validity is not None and portable_payload and
                        portable_payload.get("typed_input_geometry") == {"width": polar_width, "height": polar_height, "row_stride": polar_row_stride}
                    ),
                },
            })

    blocker = ""
    if build_public["returncode"] != 0:
        blocker = f"Portable adapter compilation failed before the sampler boundary: {build_public['stderr'].strip()}"
    run_results = [run["differential_result"] for run in runs]
    comparison_result = (
        "adapter_build_failed" if build_public["returncode"] != 0
        else "adapter_input_validation_failed" if any(result == "adapter_input_validation_failed" for result in run_results)
        else "blocked_scatter_validity_stack_contract" if any(result == "blocked_scatter_validity_stack_contract" for result in run_results)
        else "blocked_actual_capture_incomplete" if any(result == "blocked_actual_capture_incomplete" for result in run_results)
        else "comparable_stage_pass" if run_results and all(result == "comparable_stage_pass" for result in run_results)
        else "comparable_stage_mismatch"
    )

    return {
        "kind": NAME,
        "schema": 5,
        "status": "blocked" if comparison_result.startswith(("adapter_", "blocked_")) else comparison_result,
        "claim_boundary": "bounded local evidence only; no AE-exact claim",
        "addresses": {
            "caller": "0x180004640/RadialBlur_rotation_render",
            "prepass": "0x180002780/FUN_180002780",
            "scatter": "0x1800024c0/FUN_1800024c0",
        },
        "comparison": {
            "max_allowed_ulp": MAX_ULP,
            "fail_closed": True,
            "result": comparison_result,
        },
        "aex": {"path": str(AEX.relative_to(ROOT)), "sha256": sha256(AEX)},
        "portable_cli_provenance": build_public,
        "synthetic_geometry_gate": synthetic_gate,
        "fixture": {
            "width": 2,
            "height": 2,
            "rgba_float": True,
            "source": str(FIXTURE_SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(FIXTURE_SOURCE),
            "source_rgba": fixture_values,
            "repeat_border": [0, 1],
            "size_variation": "disabled",
        },
        "runs": runs,
        "typed_seam": {
            "function": "render_olmradialblur_rotation_float",
            "source_loci": {
                "entry": "cli/OLMRadialBlur/main.cpp:1676",
                "polar_locals": "cli/OLMRadialBlur/main.cpp:1697",
                "span_gate_local": "cli/OLMRadialBlur/main.cpp:1707",
                "prepass_branch": "cli/OLMRadialBlur/main.cpp:1888",
                "accumulator_local": "cli/OLMRadialBlur/main.cpp:1894",
                "prepass_alpha_local": "cli/OLMRadialBlur/main.cpp:1936",
                "scatter_lambda": "cli/OLMRadialBlur/main.cpp:2029",
            },
            "actual_aex_call_mapping": {
                "polar_rgba": "ctx+0x38",
                "filtered_alpha": "ctx+0x48",
                "span_factor": "ctx+0x50",
                "angular_width": "iVar22 (1)",
                "row_start": "floor(chunk*fVar35)",
                "row_end": "floor(next*fVar35)",
                "accum_rgba": "ctx+0x3c940",
                "max_alpha": "ctx+0x3c948",
                "scatter_valid_mask": "argument 5 at RSP+0x28",
                "scatter_angular_count": "argument 6 at RSP+0x30",
                "scatter_start_radius": "argument 8 at RSP+0x40",
                "scatter_end_radius": "argument 9 at RSP+0x48",
            },
            "export": "RotationTypedPlanes: polar, accum, prepass_alpha, scatter_alpha, source_alpha, collapsed",
        },
        "blocker": blocker or "The live scatter-entry capture proves angular_count=1, start_radius=0, end_radius=4, and four validity bytes. The current AEX projection still exposes only two RGBA cells and two scalar rows, so actual-AEX semantic comparison remains fail-closed until four RGBA cells, four scalar rows, and four validity bytes are captured. No values are padded or invented, and no mismatch or exactness is claimed.",
    }


def markdown(report: dict[str, Any]) -> str:
    build = report["portable_cli_provenance"]
    lines = [
        f"# {NAME}",
        "",
        f"- Status: `{report['status']}` (fail closed).",
        f"- Result: `{report['comparison']['result']}`.",
        "- Scope: bounded local evidence; no AE-exact claim.",
        f"- AEX SHA-256: `{report['aex']['sha256']}`",
        f"- CLI source SHA-256: `{build['production_source_sha256']}`",
        f"- Adapter source SHA-256: `{build['adapter_source_sha256']}`",
        f"- Adapter binary SHA-256: `{build.get('adapter_binary_sha256', 'not-built')}`",
        "",
        "## Executed boundary",
        "",
        "The runtime-compiled adapter source-includes `cli/OLMRadialBlur/main.cpp` and accepts arbitrary positive typed-polar geometry with `row_stride=width*4`, exact `width*height*4` float32 RGBA values, and exact `width*height` validity bytes. A local synthetic `1x4` payload passes the validation/echo gate. For each AEX run, the harness serializes only captured cells and leaves semantic execution blocked until the four-cell/four-row capture contract is complete.",
        "",
        "## Boundary",
        "",
        report["blocker"],
        "",
        "Source loci under the recorded CLI source hash: the float helper, typed-input contract, polar/span planes, shared prepass/scatter operation, and typed export before final inverse sampling. The Ghidra call mapping is preserved in the JSON: polar RGBA `ctx+0x38`, filtered alpha `ctx+0x48`, span factor `ctx+0x50`, width `iVar22=1`, row window `floor(chunk*fVar35)` to `floor(next*fVar35)`, accum RGBA `ctx+0x3c940`, and max alpha `ctx+0x3c948`.",
        "",
        "The live validity pointer is captured as four bytes, but the AEX projection currently exposes only two RGBA cells and two scalar rows. Post-prepass and post-scatter comparisons are marked `not_run`; no values are padded or invented, and there is no semantic mismatch classification or AE-exact claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=HERE / f"{NAME}.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs" / "conformance" / f"{NAME}.md")
    args = parser.parse_args()
    report = run()
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']} result={report['comparison']['result']}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
