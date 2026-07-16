#!/usr/bin/env python3
"""Bounded actual-AEX staged/helper replay for OLMBlur case_0004."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R15, UC_X86_REG_RDI, UC_X86_REG_R9, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_case0006_fullentry as fullworker  # noqa: E402

AEX = ROOT / "plugins_2025/OLMBlur.aex"
MANIFEST = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
INPUT_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/input"
HELPER_MANIFEST = ROOT / "tools/emulation/fixtures/olmblur_helper/manifest.json"
PORTABLE_RUNNER = ROOT / "tools/emulation/probe_olmblur_case0004_portable_helper.cpp"
PORTABLE_HELPER = ROOT / "core/olmblur_helper.cpp"

AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
INPUT_SHA256 = "930317e23068ea93bfd72961c2215e755e73cfd4ec784d97bccca223ed94e30a"
PF16_SHA256 = "afd4269575102eda52e581cec8e77fe62f5f7e808e33cf64d6baf186c81b70aa"
HELPER_MANIFEST_SHA256 = "86039756e28c4e860236456eab43e83a570df5f8f9711452b570945aacc2d453"
PORTABLE_HELPER_SHA256 = "ae31902dc64219f9568995d518b7cf8f22a8653644a4a9a8906cf67d90869098"

WIDTH, HEIGHT = 960, 540
CASE_ID = "olmblur__case_0004"
WITNESSES = ((411, 258), (458, 314))
PARAMS = {
    "blur_amount": 125.599998474121,
    "smoothness": 100,
    "repeat": 4,
    "bias_direction": 1,
    "legacy": 0,
}
FUN_ENTRY = 0x180002280
FUN_HORIZONTAL = 0x180001000
FUN_VERTICAL = 0x180001980
STAGING_DONE = 0x1800028DB
SCHEDULE_DONE = 0x180002F70


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_sha(path: Path, expected: str) -> None:
    if not path.is_file():
        raise AssertionError(f"required dependency is missing: {path}")
    actual = sha256(path.read_bytes())
    if actual != expected:
        raise AssertionError(f"dependency hash mismatch for {path}: {actual}")


def load_input() -> tuple[bytes, dict]:
    require_sha(AEX, AEX_SHA256)
    require_sha(MANIFEST, MANIFEST_SHA256)
    require_sha(HELPER_MANIFEST, HELPER_MANIFEST_SHA256)
    require_sha(PORTABLE_HELPER, PORTABLE_HELPER_SHA256)
    helper_manifest = json.loads(HELPER_MANIFEST.read_text())
    if helper_manifest.get("binary_sha256") != AEX_SHA256 or helper_manifest.get("scope") != "function":
        raise AssertionError("existing helper fixtures are not bound to the pinned function-scope AEX")

    manifest = json.loads(MANIFEST.read_text())
    case = next((item for item in manifest.get("cases", []) if item.get("id") == CASE_ID), None)
    if case is None:
        raise AssertionError(f"manifest case is missing: {CASE_ID}")
    values = {item["name"]: item["value"] for item in case["effects"][0]["params"]}
    params = {
        "blur_amount": values["Blur Amount"],
        "smoothness": values["Blur Smoothness"],
        "repeat": int(values["Number of Repeat"]),
        "bias_direction": int(values["Bias Direction"]),
        "legacy": int(values["Legacy"]),
    }
    if params != PARAMS:
        raise AssertionError(f"case_0004 parameters differ: {params!r}")

    input_path = INPUT_DIR / case["before_effects_frame"]
    require_sha(input_path, INPUT_SHA256)
    width, height, rgba = fullworker.png_rgba16(input_path)
    if (width, height) != (WIDTH, HEIGHT):
        raise AssertionError(f"case_0004 dimensions differ: {(width, height)!r}")
    pf16 = bytearray(len(rgba))
    for offset in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, offset)
        struct.pack_into("<4H", pf16, offset, *((word + 1) // 2 for word in (a, r, g, b)))
    if sha256(pf16) != PF16_SHA256:
        raise AssertionError("decoded PF16 input hash differs")
    return bytes(pf16), {"path": str(input_path.relative_to(ROOT)), "png_sha256": INPUT_SHA256, "pf16_sha256": PF16_SHA256}


def expected_staging(pf16: bytes) -> tuple[bytes, bytes]:
    plane = bytearray(WIDTH * HEIGHT * 12)
    flags = bytearray(WIDTH * HEIGHT)
    for pixel in range(WIDTH * HEIGHT):
        a, r, g, b = struct.unpack_from("<4H", pf16, pixel * 8)
        struct.pack_into("<3f", plane, pixel * 12, float(r), float(g), float(b))
        flags[pixel] = int(a != 0)
    return bytes(plane), bytes(flags)


def capture_staging_and_schedule(pf16: bytes) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = loader.bump_alloc(len(pf16), align=64)
    output_data = loader.bump_alloc(len(pf16), align=64)
    loader.write_bytes(source_data, pf16)
    loader.write_bytes(output_data, pf16)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", WIDTH * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", WIDTH))
        loader.write_bytes(address + 0x28, struct.pack("<I", HEIGHT))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    block = loader.host_alloc(0x40)
    loader.write_bytes(block, b"\x00" * 0x40)
    loader.write_bytes(block + 0x18, struct.pack("<I", 16))
    loader.write_bytes(block + 0x20, struct.pack("<f", PARAMS["blur_amount"]))
    loader.write_bytes(block + 0x24, struct.pack("<f", PARAMS["smoothness"]))
    loader.write_bytes(block + 0x28, struct.pack("<I", PARAMS["repeat"]))
    loader.write_bytes(block + 0x2C, struct.pack("<I", PARAMS["bias_direction"]))

    capture: dict = {"plane": None, "flags": None, "calls": [], "schedule_done": False}

    def staging_hook(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        plane = struct.unpack("<Q", ld.read_bytes(rsp + 0x60, 8))[0]
        flags = ld.uc.reg_read(UC_X86_REG_RDI)
        capture["plane"] = ld.read_bytes(plane, WIDTH * HEIGHT * 12)
        capture["flags"] = ld.read_bytes(flags, WIDTH * HEIGHT)

    def helper_hook(direction: str):
        def hook(ld: AexLoader, address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            width, height, passes, offset, radius = (
                struct.unpack("<i", ld.read_bytes(rsp + stack_offset, 4))[0]
                for stack_offset in (0x28, 0x30, 0x38, 0x40, 0x48)
            )
            if radius < 0 or radius > max(WIDTH, HEIGHT):
                raise AssertionError(f"captured helper radius is invalid: {radius}")
            weights_pointer = ld.uc.reg_read(UC_X86_REG_R9)
            weights = ld.read_bytes(weights_pointer, (radius + 1) * 4)
            capture["calls"].append({
                "call_index": len(capture["calls"]),
                "caller_r15": ld.uc.reg_read(UC_X86_REG_R15),
                "function": hex(address),
                "direction": direction,
                "width": width,
                "height": height,
                "passes": passes,
                "offset": offset,
                "radius": radius,
                "weights_pointer": hex(weights_pointer),
                "weights_hex": weights.hex(),
                "weights_sha256": sha256(weights),
            })
        return hook

    def schedule_done_hook(ld: AexLoader, _address: int, _size: int) -> None:
        capture["schedule_done"] = True
        ld.uc.emu_stop()

    loader.add_code_hook(STAGING_DONE, staging_hook)
    loader.add_code_hook(FUN_HORIZONTAL, helper_hook("horizontal"))
    loader.add_code_hook(FUN_VERTICAL, helper_hook("vertical"))
    loader.add_code_hook(SCHEDULE_DONE, schedule_done_hook)
    # Preserve the caller exactly while making every helper call an immediate
    # ABI-level return. The direct crop replay below executes the real bodies.
    loader.write_bytes(FUN_HORIZONTAL, b"\xc3")
    loader.write_bytes(FUN_VERTICAL, b"\xc3")
    result = loader.call_function(
        FUN_ENTRY,
        int_args=[context, world(source_data), world(output_data), block],
        max_instructions=30_000_000,
    )
    if capture["plane"] is None or capture["flags"] is None or not capture["schedule_done"]:
        raise AssertionError("actual worker did not reach the staging boundary")
    capture["instructions"] = result["instructions"]
    capture["callbacks"] = events
    return capture


def captured_iterations(calls: list[dict]) -> list[dict]:
    if len(calls) != 48:
        raise AssertionError(f"expected 48 helper calls for four iterations, captured {len(calls)}")
    iterations = []
    for iteration_index in range(4):
        group = calls[iteration_index * 12:(iteration_index + 1) * 12]
        horizontal, vertical = group[:6], group[6:]
        if [call["direction"] for call in group] != ["horizontal"] * 6 + ["vertical"] * 6:
            raise AssertionError(f"helper direction order differs in iteration {iteration_index + 1}")
        expected_dimensions = (WIDTH, HEIGHT)
        if any((call["width"], call["height"]) != expected_dimensions for call in group):
            raise AssertionError(f"helper dimensions differ in iteration {iteration_index + 1}")

        def validate_partition(axis_calls: list[dict], extent: int, direction: str) -> None:
            ranges = [(call["offset"], call["offset"] + call["passes"]) for call in axis_calls]
            if ranges[0][0] != 0 or ranges[-1][1] != extent:
                raise AssertionError(f"{direction} pass range does not cover its axis: {ranges!r}")
            if any(left[1] != right[0] for left, right in zip(ranges, ranges[1:])):
                raise AssertionError(f"{direction} pass ranges are not contiguous: {ranges!r}")

        validate_partition(horizontal, HEIGHT, "horizontal")
        validate_partition(vertical, WIDTH, "vertical")
        radii = {call["radius"] for call in group}
        weight_hex = {call["weights_hex"] for call in group}
        if len(radii) != 1 or len(weight_hex) != 1:
            raise AssertionError(f"H/V radius or weight bytes disagree in iteration {iteration_index + 1}")
        radius = radii.pop()
        weights = bytes.fromhex(weight_hex.pop())
        if len(weights) != (radius + 1) * 4:
            raise AssertionError(f"captured weight size differs in iteration {iteration_index + 1}")
        iterations.append({
            "iteration": iteration_index + 1,
            "radius": radius,
            "weights": weights,
            "weights_sha256": sha256(weights),
            "weights_pointers": sorted({call["weights_pointer"] for call in group}),
            "horizontal_pass_ranges": [[call["offset"], call["offset"] + call["passes"]] for call in horizontal],
            "vertical_pass_ranges": [[call["offset"], call["offset"] + call["passes"]] for call in vertical],
        })
    return iterations


def crop(blob: bytes, old: tuple[int, int, int, int], new: tuple[int, int, int, int], stride: int) -> bytes:
    ox0, oy0, ox1, _oy1 = old
    nx0, ny0, nx1, ny1 = new
    old_width = ox1 - ox0
    row_bytes = (nx1 - nx0) * stride
    out = bytearray(row_bytes * (ny1 - ny0))
    for row, y in enumerate(range(ny0, ny1)):
        source = ((y - oy0) * old_width + (nx0 - ox0)) * stride
        out[row * row_bytes:(row + 1) * row_bytes] = blob[source:source + row_bytes]
    return bytes(out)


def run_actual_helper_micro(direction: str, flags: bytes, source: bytes, weights: bytes,
                            width: int, height: int, radius: int) -> tuple[bytes, int, int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)

    def alloc(data: bytes, align: int = 16) -> int:
        address = loader.bump_alloc(len(data), align=align)
        loader.write_bytes(address, data)
        return address

    flags_ptr = alloc(flags)
    source_ptr = alloc(source)
    destination_ptr = alloc(bytes(len(source)))
    weights_ptr = alloc(weights)
    function = FUN_HORIZONTAL if direction == "horizontal" else FUN_VERTICAL
    passes = height if direction == "horizontal" else width
    offset = 0
    instruction_cap = 3_000_000
    result = loader.call_function(
        function,
        int_args=[flags_ptr, source_ptr, destination_ptr, weights_ptr,
                  width, height, passes, offset, radius],
        max_instructions=instruction_cap,
    )
    if result["instructions"] >= instruction_cap:
        raise AssertionError(
            f"bounded {direction} helper reached its {instruction_cap} instruction cap"
        )
    return loader.read_bytes(destination_ptr, len(source)), result["instructions"], instruction_cap


def compile_portable(executable: Path) -> list[str]:
    command = [
        os.environ.get("CXX", "c++"), "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
        str(PORTABLE_HELPER), str(PORTABLE_RUNNER), "-o", str(executable),
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"portable helper compile failed: {result.stderr.strip()}")
    return [
        command[0], *command[1:5],
        str(PORTABLE_HELPER.relative_to(ROOT)),
        str(PORTABLE_RUNNER.relative_to(ROOT)),
        "-o", "<temporary>/replay_olmblur_helper_fixture",
    ]


def run_portable(executable: Path, temp: Path, stage_id: str, direction: str,
                 flags: bytes, source: bytes, weights: bytes,
                 width: int, height: int, radius: int) -> bytes:
    paths = {}
    for name, data in (("flags", flags), ("src", source), ("weights", weights)):
        path = temp / f"{stage_id}_{name}.bin"
        path.write_bytes(data)
        paths[name] = path
    output_path = temp / f"{stage_id}_output.bin"
    passes = height if direction == "horizontal" else width
    offset = 0
    command = [
        str(executable), direction, *(str(paths[name]) for name in ("flags", "src", "weights")), str(output_path),
        str(width), str(height), str(passes), str(offset), str(radius),
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"portable helper failed at {stage_id}: {result.stderr.strip()}")
    output = output_path.read_bytes()
    if len(output) != len(source):
        raise AssertionError(f"portable helper output size differs at {stage_id}")
    return output


def deterministic_micro_fixture(direction: str, radius: int) -> tuple[bytes, bytes, int, int]:
    width, height = (2 * radius + 1, 1) if direction == "horizontal" else (1, 2 * radius + 1)
    pixels = width * height
    flags = bytearray(1 if (pixel * 7 + radius * 3 + (1 if direction == "vertical" else 0)) % 13 else 0
                      for pixel in range(pixels))
    flags[0] = 0
    flags[pixels // 2] = 1
    if set(flags) != {0, 1}:
        raise AssertionError(f"microfixture flags are not nontrivial for {direction} radius {radius}")
    values = []
    for pixel in range(pixels):
        values.extend((
            float((pixel * 37 + radius * 11 + 3) % 32769),
            float((pixel * 19 + radius * 17 + 5) % 32769),
            float((pixel * 53 + radius * 7 + 9) % 32769),
        ))
    return bytes(flags), struct.pack(f"<{len(values)}f", *values), width, height


def bits_hex(pixel: bytes) -> list[str]:
    return [f"0x{value:08x}" for value in struct.unpack("<3I", pixel)]


def run_probe() -> dict:
    pf16, input_identity = load_input()
    expected_plane, expected_flags = expected_staging(pf16)
    capture = capture_staging_and_schedule(pf16)
    if capture["plane"] != expected_plane or capture["flags"] != expected_flags:
        raise AssertionError("actual staged image state differs from decoded PF16 source")
    iterations = captured_iterations(capture["calls"])
    radius_sequence = [iteration["radius"] for iteration in iterations]

    reach = sum(radius_sequence)
    layer_a = []
    layer_b_stages = []
    layer_b_final = {}
    with tempfile.TemporaryDirectory(prefix="olmblur_case0004_staged_helper_") as temporary:
        temp = Path(temporary)
        executable = temp / "replay_olmblur_helper_fixture"
        compile_command = compile_portable(executable)
        for iteration_fixture in iterations:
            for direction in ("horizontal", "vertical"):
                radius = iteration_fixture["radius"]
                flags, plane, width, height = deterministic_micro_fixture(direction, radius)
                actual, instructions, instruction_cap = run_actual_helper_micro(
                    direction, flags, plane, iteration_fixture["weights"], width, height, radius
                )
                portable = run_portable(
                    executable, temp, f"micro_i{iteration_fixture['iteration']}_{direction[0]}",
                    direction, flags, plane, iteration_fixture["weights"], width, height, radius
                )
                exact = actual == portable
                if not exact:
                    raise AssertionError(
                        f"actual/portable microfixture differs at iteration {iteration_fixture['iteration']} {direction}"
                    )
                target_offset = (width * height // 2) * 12
                layer_a.append({
                    "iteration": iteration_fixture["iteration"], "direction": direction,
                    "radius": radius, "dimensions": [width, height],
                    "flags_sha256": sha256(flags), "source_sha256": sha256(plane),
                    "weights_sha256": iteration_fixture["weights_sha256"],
                    "output_sha256": sha256(actual), "actual_instructions": instructions,
                    "instruction_cap": instruction_cap, "exact": exact,
                    "target_index": width * height // 2,
                    "actual_target_bits_hex": bits_hex(actual[target_offset:target_offset + 12]),
                    "portable_target_bits_hex": bits_hex(portable[target_offset:target_offset + 12]),
                })
        for witness_index, (x, y) in enumerate(WITNESSES):
            bounds = (x - reach, y - reach, x + reach + 1, y + reach + 1)
            if bounds[0] < 0 or bounds[1] < 0 or bounds[2] > WIDTH or bounds[3] > HEIGHT:
                raise AssertionError(f"witness crop reaches the frame edge: {(x, y)!r}")
            plane = crop(capture["plane"], (0, 0, WIDTH, HEIGHT), bounds, 12)
            flags = crop(capture["flags"], (0, 0, WIDTH, HEIGHT), bounds, 1)
            for iteration_fixture in iterations:
                iteration = iteration_fixture["iteration"]
                radius = iteration_fixture["radius"]
                for direction in ("horizontal", "vertical"):
                    input_bounds = bounds
                    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
                    weights = iteration_fixture["weights"]
                    stage_id = f"w{witness_index + 1}_i{iteration}_{direction[0]}"
                    portable_output = run_portable(
                        executable, temp, stage_id, direction, flags, plane, weights,
                        width, height, radius
                    )
                    if direction == "horizontal":
                        bounds = (bounds[0] + radius, bounds[1], bounds[2] - radius, bounds[3])
                    else:
                        bounds = (bounds[0], bounds[1] + radius, bounds[2], bounds[3] - radius)
                    next_plane = crop(portable_output, input_bounds, bounds, 12)
                    next_flags = crop(flags, input_bounds, bounds, 1)
                    layer_b_stages.append({
                        "witness": [x, y], "iteration": iteration, "direction": direction,
                        "radius": radius, "input_bounds_xyxy": list(input_bounds),
                        "output_bounds_xyxy": list(bounds), "input_dimensions": [width, height],
                        "output_dimensions": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
                        "execution": "portable_only",
                        "portable_output_sha256": sha256(portable_output),
                        "retained_output_sha256": sha256(next_plane),
                    })
                    plane, flags = next_plane, next_flags
            if bounds != (x, y, x + 1, y + 1) or len(plane) != 12:
                raise AssertionError(f"crop replay did not converge to witness {(x, y)!r}: {bounds!r}")
            point = f"({x},{y})"
            final_bits = bits_hex(plane)
            layer_b_final[point] = {
                "portable_full_cone_bits_hex": final_bits,
                "execution": "portable_only",
            }

    return {
        "schema": "olmblur.case0004.staged-helper-replay/1",
        "status": "pass_two_layer_witness",
        "platform": "Mac-only Unicorn execution of pinned PE AEX plus local portable C++ helper replay",
        "scope": "actual helper microfixtures plus portable-only complete dependency-cone composition",
        "identity": {
            "case_id": CASE_ID, "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256,
            "entry": hex(FUN_ENTRY), "helpers": [hex(FUN_HORIZONTAL), hex(FUN_VERTICAL)],
            "input": input_identity, "manifest_sha256": MANIFEST_SHA256,
            "helper_fixture_manifest_sha256": HELPER_MANIFEST_SHA256,
            "portable_helper_sha256": PORTABLE_HELPER_SHA256,
        },
        "parameters": PARAMS,
        "radius_sequence": radius_sequence,
        "captured_iterations": [
            {key: value for key, value in iteration.items() if key != "weights"}
            for iteration in iterations
        ],
        "staging": {
            "boundary": hex(STAGING_DONE), "schedule_stop": hex(SCHEDULE_DONE),
            "instructions_to_schedule_stop": capture["instructions"],
            "plane_bytes": len(capture["plane"]), "flags_bytes": len(capture["flags"]),
            "plane_sha256": sha256(capture["plane"]), "flags_sha256": sha256(capture["flags"]),
            "full_plane_matches_pf16_decode": True,
            "helper_body_detour": "first byte of each helper patched to RET in schedule-capture loader only",
            "helper_calls_captured": capture["calls"],
        },
        "portable_compile_command": compile_command,
        "actual_helper_micro_exact": {"all_exact": all(item["exact"] for item in layer_a), "fixtures": layer_a},
        "portable_full_cone_result": {
            "initial_crop_dimensions": [reach * 2 + 1, reach * 2 + 1],
            "stages": layer_b_stages, "final": layer_b_final,
        },
        "classification": "actual_helper_micro_exact_and_portable_full_cone_result",
        "claim_limit": "Layer A is actual-AEX helper microfixture evidence. Layer B is portable-only composition; no actual-AEX full helper chain or AE exactness is claimed.",
    }


if __name__ == "__main__":
    result = run_probe()
    print(json.dumps({
        "status": result["status"],
        "actual_microfixtures": len(result["actual_helper_micro_exact"]["fixtures"]),
        "classification": result["classification"],
        "portable_final": result["portable_full_cone_result"]["final"],
    }, indent=2))
