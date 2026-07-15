#!/usr/bin/env python3
"""Typed ColorKey Edge Blur apply differential for directions 1/2/3.

The checked-in 20260716 AEX fixture proves that the helper returns, but its
numeric output is not a production-equivalent comparison: its matte payload
contains one byte per pixel although FUN_1800113c0 addresses four-byte pixels,
and the default Unicorn import shim does not implement sin/sinf return values.

This test reuses the fixture's typed world layout with three discriminating
logical source/matte/distance patterns, packs the worlds according to
FUN_1800085b0 and its FUN_1800094b0 callsite, installs narrow math callbacks,
and compares each complete 32-byte destination against current production at
the equivalent alpha-only apply boundary. This is not AE-host execution or an
AE-exact claim.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_XMM0

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402
from probe_olmcolorkey_edge_blur_apply_aex_20260716 import (  # noqa: E402
    APPLY,
    make_handle_suite,
    world,
)

FIXTURE = ROOT / "refs" / "conformance" / "olmcolorkey_edge_blur_apply_aex_20260716.json"
AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
CLI_SOURCE = ROOT / "cli" / "OLMColorKey" / "main.cpp"
WIDTH = 4
HEIGHT = 2
AMOUNT = 4.0
PIXEL_BYTES = 4
SENTINEL = 0xCC

PATTERNS = (
    {
        "id": "mixed_integer_thresholds",
        "matte": (255, 0, 255, 0, 255, 255, 0, 255),
        "distance": (0.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0),
        "source_alpha": (255,) * 8,
    },
    {
        "id": "inside_outside_endpoint_sweeps",
        "matte": (255, 255, 255, 255, 0, 0, 0, 0),
        "distance": (0.0, 1.0, 3.0, 4.0, 0.0, 1.0, 3.0, 4.0),
        "source_alpha": (17, 53, 89, 125, 161, 197, 233, 255),
    },
    {
        "id": "alternating_fractional_ramps",
        "matte": (0, 255, 0, 255, 255, 0, 255, 0),
        "distance": (0.5, 0.5, 1.5, 1.5, 2.5, 2.5, 3.5, 3.5),
        "source_alpha": (31, 63, 95, 127, 159, 191, 223, 251),
    },
)


def model_edge_blur_weight(inside: bool, distance: float, amount: float, direction: int) -> float:
    """Direct transcription of FUN_1800049a0/4b50/4cf0 for enum values 1/2/3."""
    if amount <= 0.0:
        return 1.0 if inside else 0.0
    if direction == 1:
        if not inside:
            return 0.0
        if distance >= amount:
            return 1.0
        return (math.sin(distance * (math.pi / amount) - math.pi / 2.0) + 1.0) * 0.5
    if direction == 2:
        if distance == 0.0:
            return 0.5
        if distance >= amount:
            return 1.0 if inside else 0.0
        phase = distance * ((math.pi * 0.5) / amount)
        if not inside:
            phase = -phase
        return (math.sin(phase) + 1.0) * 0.5
    if direction == 3:
        if inside:
            return 1.0
        if distance >= amount:
            return 0.0
        return (math.sin(math.pi / 2.0 - distance * (math.pi / amount)) + 1.0) * 0.5
    return 1.0 if inside else 0.0


def _xmm_bytes(uc) -> bytes:
    raw = uc.reg_read(UC_X86_REG_XMM0)
    return raw.to_bytes(16, "little") if isinstance(raw, int) else bytes(raw)


def _write_xmm(uc, value: bytes) -> None:
    uc.reg_write(UC_X86_REG_XMM0, int.from_bytes(value.ljust(16, b"\0"), "little"))


def _sin_callback(uc, _args: list[int]) -> int:
    value = struct.unpack("<d", _xmm_bytes(uc)[:8])[0]
    _write_xmm(uc, struct.pack("<d", math.sin(value)))
    return 0


def _sinf_callback(uc, _args: list[int]) -> int:
    value = struct.unpack("<f", _xmm_bytes(uc)[:4])[0]
    _write_xmm(uc, struct.pack("<f", math.sin(value)))
    return 0


def _typed_world_bytes(fixture: dict, pattern: dict) -> tuple[bytes, bytes, bytes, bytes]:
    source = bytearray(fixture["worlds"]["source"]["bytes"])
    matte_values = pattern["matte"]
    distances = pattern["distance"]
    destination = bytes(fixture["worlds"]["destination"]["initial_bytes"])
    if len(source) != WIDTH * HEIGHT * PIXEL_BYTES or len(destination) != len(source):
        raise ValueError("source/destination fixture length is not 4x2 PF_Pixel8")
    if any(len(pattern[key]) != WIDTH * HEIGHT for key in ("matte", "distance", "source_alpha")):
        raise ValueError(f"logical pattern {pattern['id']} is not 4x2")
    for pixel, alpha in enumerate(pattern["source_alpha"]):
        source[pixel * PIXEL_BYTES] = alpha

    # FUN_1800113c0 addresses x*4 and reads byte 0. Non-alpha bytes are
    # deliberately nonzero so accidental scalar/packed aliasing remains visible.
    matte = bytes(channel for alpha in matte_values for channel in (alpha, 0xA1, 0xB2, 0xC3))
    # FUN_180011420 addresses x*16 and reads float 0 from a float4 pixel.
    distance = struct.pack("<32f", *(value for distance_value in distances for value in (distance_value,) * 4))
    return bytes(source), matte, distance, destination


def _libpng_flags() -> tuple[list[str], list[str], str]:
    pkg_config = shutil.which("pkg-config")
    if pkg_config:
        cflags = subprocess.run(
            [pkg_config, "--cflags", "libpng"], capture_output=True, text=True, check=False
        )
        libs = subprocess.run(
            [pkg_config, "--libs", "libpng"], capture_output=True, text=True, check=False
        )
        if cflags.returncode == 0 and libs.returncode == 0:
            return shlex.split(cflags.stdout), shlex.split(libs.stdout), "pkg-config libpng"
    for prefix in (Path("/opt/homebrew"), Path("/usr/local")):
        if (prefix / "include" / "png.h").is_file():
            return [f"-I{prefix / 'include'}"], [f"-L{prefix / 'lib'}", "-lpng"], str(prefix)
    return [], ["-lpng"], "default linker search"


def _compile_cli_apply_probe(directory: Path) -> tuple[Path, dict]:
    cxx_name = os.environ.get("CXX", "clang++")
    cxx = shutil.which(cxx_name)
    if not cxx:
        raise RuntimeError(f"fail closed: C++ compiler not found: {cxx_name}")
    include_path = str(CLI_SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    source = directory / "olmcolorkey_edge_blur_apply_probe.cpp"
    executable = directory / "olmcolorkey_edge_blur_apply_probe"
    source.write_text(
        r'''#define main olmcolorkey_cli_embedded_main
#include "@CLI_SOURCE@"
#undef main

int main() {
    unsigned int input_channel = 0;
    unsigned int output_channel = 0;
    int inside_value = 0;
    float distance = 0.0f;
    float amount = 0.0f;
    int direction = 0;
    while (std::scanf(
        "%u %u %d %f %f %d",
        &input_channel,
        &output_channel,
        &inside_value,
        &distance,
        &amount,
        &direction) == 6) {
        const bool inside = inside_value != 0;
        const float weight = edge_blur_weight(inside, distance, amount, direction);
        const unsigned char value = edge_blur_apply_channel(
            static_cast<unsigned char>(input_channel),
            static_cast<unsigned char>(output_channel),
            inside,
            weight);
        std::printf("%u\n", static_cast<unsigned int>(value));
    }
    return std::feof(stdin) ? 0 : 2;
}
'''.replace("@CLI_SOURCE@", include_path),
        encoding="utf-8",
    )
    cflags, libs, libpng_source = _libpng_flags()
    command = [
        cxx,
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-pedantic",
        *cflags,
        str(source),
        *libs,
        "-o",
        str(executable),
    ]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if build.returncode != 0:
        raise RuntimeError(
            "fail closed: source-include CLI probe did not compile\n"
            f"stdout:\n{build.stdout}\nstderr:\n{build.stderr}"
        )
    return executable, {
        "kind": "temporary compiled source-include callable seam",
        "production_source": str(CLI_SOURCE.relative_to(ROOT)),
        "call_chain": "edge_blur_weight -> edge_blur_apply_channel",
        "compiler": cxx,
        "compiler_flags": ["-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic", *cflags],
        "libpng_flags": libs,
        "libpng_discovery": libpng_source,
        "binary_scope": "temporary local executable built from the current CLI source; not a checked-in binary",
    }


def run_cli_production_seam(fixture: dict) -> tuple[dict[tuple[str, int], list[int]], dict]:
    outputs: dict[tuple[str, int], list[int]] = {}
    requests: list[tuple[tuple[str, int], int, str]] = []
    for pattern in PATTERNS:
        source, matte, _distance_bytes, destination = _typed_world_bytes(fixture, pattern)
        for direction in (1, 2, 3):
            key = (pattern["id"], direction)
            outputs[key] = list(destination)
            for pixel, distance in enumerate(pattern["distance"]):
                offset = pixel * PIXEL_BYTES
                matte_alpha = matte[offset]
                requests.append((
                    key,
                    offset,
                    f"{source[offset]} {matte_alpha} {int(matte_alpha != 0)} "
                    f"{distance!r} {AMOUNT!r} {direction}\n",
                ))

    with tempfile.TemporaryDirectory(prefix="olmcolorkey_edge_blur_apply_") as temporary:
        executable, metadata = _compile_cli_apply_probe(Path(temporary))
        run = subprocess.run(
            [str(executable)],
            cwd=ROOT,
            input="".join(request[2] for request in requests),
            capture_output=True,
            text=True,
            check=False,
        )
    if run.returncode != 0:
        raise RuntimeError(
            "fail closed: source-include CLI probe did not execute cleanly\n"
            f"stdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )
    values = run.stdout.splitlines()
    if len(values) != len(requests):
        raise RuntimeError(
            f"fail closed: CLI probe returned {len(values)} values for {len(requests)} requests"
        )
    for (key, offset, _request), value in zip(requests, values):
        parsed = int(value)
        if not 0 <= parsed <= 255:
            raise RuntimeError(f"fail closed: CLI probe returned out-of-range byte {parsed}")
        outputs[key][offset] = parsed
    metadata["scalar_apply_requests"] = len(requests)
    metadata["destination_bytes_compared"] = len(outputs) * WIDTH * HEIGHT * PIXEL_BYTES
    return outputs, metadata


def run_typed_aex(fixture: dict, pattern: dict, direction: int) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.import_impls.update({"sin": _sin_callback, "sinf": _sinf_callback})
    source, matte, distance, destination = _typed_world_bytes(fixture, pattern)
    source_world, _ = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, source)
    matte_world, _ = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, matte)
    distance_world, _ = world(loader, WIDTH, HEIGHT, 16, distance)
    destination_world, destination_payload = world(loader, WIDTH, HEIGHT, PIXEL_BYTES, destination)

    context = loader.host_alloc(0x200)
    loader.write_bytes(context, b"\0" * 0x200)
    events: list[dict] = []
    suite, _ = make_handle_suite(loader, events)
    loader.write_bytes(context + 0x180, struct.pack("<Q", suite))
    call = loader.call_function(
        APPLY,
        int_args=[context, 0, direction, source_world, matte_world, distance_world, destination_world, 0],
        float_args={1: AMOUNT},
        max_instructions=1_000_000,
    )
    output = list(loader.read_bytes(destination_payload, len(destination)))
    return {
        "rax": hex(call["rax"]),
        "destination_bytes": output,
        "math_imports": sorted({entry.name for entry in loader.import_log if entry.name in {"sin", "sinf"}}),
        "non_alpha_sentinels_preserved": all(value == SENTINEL for i, value in enumerate(output) if i % 4 != 0),
        "cleanup_observed": any(event["callback"] == "PF_HandleSuite.release_suite" for event in events),
    }


def model_alpha_apply(fixture: dict, pattern: dict, direction: int) -> list[int]:
    """Apply the independent decomp model at FUN_1800085b0's alpha boundary."""
    source, matte, _distance_bytes, destination_bytes = _typed_world_bytes(fixture, pattern)
    output = list(destination_bytes)
    for pixel, distance in enumerate(pattern["distance"]):
        offset = pixel * PIXEL_BYTES
        matte_alpha = matte[offset]
        weight = model_edge_blur_weight(matte_alpha != 0, distance, AMOUNT, direction)
        value = source[offset] if matte_alpha == 0 and weight != 0.0 else matte_alpha
        output[offset] = max(0, min(255, int(value * weight)))
    return output


def compare(actual: list[int], production: list[int]) -> dict:
    if len(actual) != len(production):
        return {
            "status": "mismatch",
            "reason": "length",
            "actual_length": len(actual),
            "production_length": len(production),
        }
    differences = [
        {"offset": i, "actual": actual_value, "production": production_value}
        for i, (actual_value, production_value) in enumerate(zip(actual, production))
        if actual_value != production_value
    ]
    return {
        "status": "pass" if not differences else "mismatch",
        "byte_length": len(actual),
        "different_bytes": len(differences),
        "different_offsets": [difference["offset"] for difference in differences],
        "first_difference": differences[0] if differences else None,
    }


def build_report() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    current_outputs, production_execution = run_cli_production_seam(fixture)
    cases = []
    for pattern in PATTERNS:
        for direction in (1, 2, 3):
            actual = run_typed_aex(fixture, pattern, direction)
            production = current_outputs[(pattern["id"], direction)]
            model = model_alpha_apply(fixture, pattern, direction)
            matching_arms = [
                candidate
                for candidate in (1, 2, 3)
                if current_outputs[(pattern["id"], candidate)] == actual["destination_bytes"]
            ]
            cases.append({
                "pattern": pattern["id"],
                "direction": direction,
                "aex_rax": actual["rax"],
                "math_imports": actual["math_imports"],
                "non_alpha_sentinels_preserved": actual["non_alpha_sentinels_preserved"],
                "cleanup_observed": actual["cleanup_observed"],
                "aex_destination_bytes": actual["destination_bytes"],
                "cli_destination_bytes": production,
                "comparison": compare(actual["destination_bytes"], production),
                "matching_cli_arms": matching_arms,
                "model_destination_bytes": model,
                "model_comparison": compare(actual["destination_bytes"], model),
            })

    stable_arms = {
        str(direction): sorted(set.intersection(*(
            set(case["matching_cli_arms"])
            for case in cases
            if case["direction"] == direction
        )))
        for direction in (1, 2, 3)
    }
    exact_cases = sum(case["comparison"]["status"] == "pass" for case in cases)
    mismatch_cases = len(cases) - exact_cases
    return {
        "status": "pass" if mismatch_cases == 0 else "fail_closed_production_mismatch",
        "classification": "implemented binary-grounded local exact: typed Mac-local Unicorn AEX helper replay vs a temporary executable compiled from the current C++ CLI source; not AE-host execution and not AE-exact",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "original_fixture_blocker": {
            "classification": "adapter-scope and callback-contract mismatch; original numeric output is not a production semantic contradiction",
            "matte_payload_bytes": len(fixture["worlds"]["boundary"]["bytes"]),
            "required_matte_payload_bytes": WIDTH * HEIGHT * PIXEL_BYTES,
            "pixel_accessor": "FUN_1800113c0 uses rowbytes + x*4 and FUN_1800085b0 reads byte offset 0",
            "math_import_contract": "default AexLoader leaves XMM0 unchanged for unimplemented sin/sinf imports",
        },
        "equivalent_boundary": {
            "apply_helper": "FUN_1800085b0 @ 0x1800085b0",
            "actual_callsite": "FUN_1800094b0 @ 0x1800098a4..0x1800098cc",
            "production_execution": production_execution,
            "matte_source": "local_208 keyed matte; local_108 boundary seed is used only by the distance helper",
            "write_scope": "PF_Pixel8 byte offset 0 (alpha) only; offsets 1/2/3 remain sentinel",
            "comparison": "complete 32-byte destination, zero tolerance",
        },
        "enum_direction_evidence": {
            "popup": "Direction: Inside | Around | Outside (one-based values 1/2/3)",
            "parameter_ingest": "FUN_18000a3d0 calls FUN_18000e050 for property index 0x13 and stores it at context+0x48",
            "actual_callsite": "0x1800098a4..0x1800098cc loads *(uint32_t *)(context+0x48) into r8d and calls FUN_1800085b0 without transformation",
            "helper_dispatch": {
                "1": "FUN_1800049a0 (Inside)",
                "2": "FUN_180004b50 (Around)",
                "3": "FUN_180004cf0 (Outside/default non-1/non-2 arm)",
            },
            "independent_of_output_fitting": True,
        },
        "pattern_matrix": {
            "pattern_count": len(PATTERNS),
            "directions": [1, 2, 3],
            "case_count": len(cases),
            "patterns": list(PATTERNS),
        },
        "production_result": {
            "direction_1": "byte-exact for all three patterns; formula preserved",
            "direction_2": "byte-exact for all three patterns with the implemented Around formula",
            "direction_3": "byte-exact for all three patterns with the implemented Outside formula",
            "exact_cases": exact_cases,
            "mismatch_cases": mismatch_cases,
            "stable_cli_arms_by_aex_direction": stable_arms,
            "identity_mapping_exact": stable_arms == {"1": [1], "2": [2], "3": [3]},
            "implemented_formula_evidence": {
                "direction_1": "unchanged; FUN_1800049a0",
                "direction_2": "FUN_180004b50 initializes 0.5 at distance 0, uses sinf(+/-distance*((pi/2)/amount)) below amount, and resolves to inside?1:0 at/above amount",
                "direction_3": "FUN_180004cf0 keeps inside at 1 and uses sin(pi/2-distance*(pi/amount)) outside below amount",
            },
            "independent_model_matrix": "byte-exact for all nine cases",
        },
        "implemented_sources": {
            "status": "implemented",
            "preserve_direction_1": True,
            "files": {
                "cli/OLMColorKey/main.cpp": {
                    "direction_1_preserved": "718-722",
                    "direction_2_around": "723-729",
                    "direction_3_outside": "730-734",
                    "callable_apply_channel": "738-746; renderer calls at 950-953",
                },
                "mac/OLMColorKey/OLMColorKey.cpp": {
                    "direction_1_preserved": "715-719",
                    "direction_2_around": "720-726",
                    "direction_3_outside": "727-731",
                },
                "rust/olmcolorkey_cli/src/main.rs": {
                    "direction_1_preserved": "448-456",
                    "direction_2_around": "457-470",
                    "direction_3_outside": "471-479",
                    "grounded_unit_test": "490-518",
                },
            },
            "cli_callable_seam": "edge_blur_apply_channel is used by render_olmcolorkey and by the temporary source-include probe",
        },
        "cases": cases,
    }


def test_typed_direction_replays_compare_the_equivalent_alpha_boundary() -> None:
    report = build_report()
    assert len(report["cases"]) == 9
    assert {case["pattern"] for case in report["cases"]} == {pattern["id"] for pattern in PATTERNS}
    assert [case["direction"] for case in report["cases"]] == [1, 2, 3] * 3
    assert all(case["aex_rax"] == "0x0" for case in report["cases"])
    assert all(case["cleanup_observed"] for case in report["cases"])
    assert all(case["non_alpha_sentinels_preserved"] for case in report["cases"])
    assert all(case["comparison"]["status"] == "pass" for case in report["cases"])
    assert all(offset % 4 == 0 for case in report["cases"] for offset in case["comparison"]["different_offsets"])
    assert all(case["model_comparison"]["status"] == "pass" for case in report["cases"])
    assert report["production_result"]["stable_cli_arms_by_aex_direction"] == {
        "1": [1],
        "2": [2],
        "3": [3],
    }
    assert report["production_result"]["identity_mapping_exact"]
    assert report["equivalent_boundary"]["production_execution"]["scalar_apply_requests"] == 72
    assert report["status"] == "pass"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--enforce", action="store_true", help="return nonzero when an equivalent-boundary byte differs")
    args = parser.parse_args()
    report = build_report()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"])}, sort_keys=True))
    return 1 if args.enforce and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
