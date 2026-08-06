#!/usr/bin/env python3
"""Compare MainInterpKernel8 CFG interpretation on every case_0001 edge call."""
import hashlib
import ctypes
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn.x86_const import (UC_X86_REG_RDX, UC_X86_REG_R8,
                               UC_X86_REG_R9, UC_X86_REG_RIP,
                               UC_X86_REG_RSP)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader
from test_olmsmoother_v1_mainkernel8_cfg_interpreter_20260805 import Machine

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
CFG = ROOT / "refs/conformance/olmsmoother_v1_mainkernel8_cfg_20260805.json"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png"
OUT = ROOT / "refs/conformance/olmsmoother_v1_case0001_pf8_mainkernel_all_boundaries_20260805.json"
PRODUCTION_HARNESS = ROOT / "tools/emulation/olmsmoother_v1_mainkernel8_production_harness_20260805.cpp"
CLASSIFIER = 0x180008060
SUBHANDLER = 0x1800033D0
MAIN = 0x180005570
EXECUTOR = 0x180006270
DIRECTIONS = (5, 3, 1, 7)
FIELD_COUNTS = {
    "0x1800010c0": 2,
    "0x1800010e0": 3,
    "0x180001110": 4,
    "0x180001150": 3,
    "0x180001180": 4,
}
KIND_TO_FUNCTION = tuple(FIELD_COUNTS)
KIND_TO_VTABLE = ("0x18000d1a8", "0x18000d1d8", "0x18000d1e8",
                  "0x18000d1c8", "0x18000d1b8")


class ProductionCapture(ctypes.Structure):
    _fields_ = [
        ("direction", ctypes.c_int32), ("start_x", ctypes.c_int32),
        ("start_y", ctypes.c_int32), ("color_a_index", ctypes.c_int32),
        ("end_x", ctypes.c_int32), ("end_y", ctypes.c_int32),
        ("color_b_index", ctypes.c_int32), ("evaluator_kind", ctypes.c_int32),
        ("use_source", ctypes.c_int32), ("leading_span", ctypes.c_int32),
        ("fields", ctypes.c_uint32 * 4),
    ]


class NaturalMainCall(ctypes.Structure):
    _fields_ = [("args12", ctypes.c_int32 * 12)]


def i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def u64(loader, address):
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def normalize(capture):
    function = capture["evaluator_function"]
    raw = bytes.fromhex(capture["evaluator_bytes"])
    count = FIELD_COUNTS[function]
    if function == "0x180001110":
        fields = raw[8:20] + raw[0x18:0x1C]
    else:
        fields = raw[8:8 + count * 4]
    return {
        key: capture[key]
        for key in ("direction", "start", "color_a_index", "end", "color_b_index",
                    "evaluator_vtable", "evaluator_function", "use_source", "leading_span")
    } | {"evaluator_fields_hex": fields.hex()}


def load_production_harness():
    temporary = tempfile.TemporaryDirectory()
    library_path = Path(temporary.name) / "libolmsmoother_mainkernel8.dylib"
    command = [
        "clang++", "-std=c++17", "-O2", "-shared", "-fPIC",
        "-I" + str(ROOT / "cli/OLMSmoother/shim"),
        str(PRODUCTION_HARNESS), "-o", str(library_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(library_path))
    function = library.olmsmoother_run_mainkernel8_production
    function.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint8),
                         ctypes.POINTER(ProductionCapture), ctypes.c_int]
    function.restype = ctypes.c_int
    return temporary, library, function


def run_production(function, args12, neighborhood_argb):
    arguments = (ctypes.c_int32 * 12)(*args12)
    pixels = (ctypes.c_uint8 * 36)(*neighborhood_argb)
    captures = (ProductionCapture * 8)()
    count = function(arguments, pixels, captures, len(captures))
    assert 0 <= count <= len(captures)
    result = []
    for index in range(count):
        capture = captures[index]
        assert 0 <= capture.evaluator_kind < len(KIND_TO_FUNCTION)
        function_address = KIND_TO_FUNCTION[capture.evaluator_kind]
        field_count = FIELD_COUNTS[function_address]
        fields = b"".join(struct.pack("<I", capture.fields[field])
                          for field in range(field_count))
        result.append({
            "direction": capture.direction,
            "start": [capture.start_x, capture.start_y],
            "color_a_index": capture.color_a_index,
            "end": [capture.end_x, capture.end_y],
            "color_b_index": capture.color_b_index,
            "evaluator_vtable": KIND_TO_VTABLE[capture.evaluator_kind],
            "evaluator_function": function_address,
            "use_source": capture.use_source,
            "leading_span": capture.leading_span,
            "evaluator_fields_hex": fields.hex(),
        })
    return result


def edge_centers(image):
    width, height = image.size
    pixels = image.load()
    result = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            center = pixels[x, y]
            if any(pixels[x + dx, y + dy] != center
                   for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                   if dx or dy):
                result.append((x, y))
    return result


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    cfg = json.loads(CFG.read_text())
    instructions = {int(ins["address"], 0): ins
                    for block in cfg["blocks"] for ins in block["instructions"]}
    image = Image.open(SOURCE).convert("RGBA")
    width, height = image.size
    rgba = list(image.getdata())
    argb = bytearray()
    for red, green, blue, alpha in rgba:
        argb += bytes((alpha, red, green, blue))

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    temporary_library, production_library, production_function = load_production_harness()
    src_pixels = loader.host_alloc(len(argb), align=16)
    dst_pixels = loader.host_alloc(len(argb), align=16)
    loader.write_bytes(src_pixels, bytes(argb))
    loader.write_bytes(dst_pixels, bytes(argb))
    src_world = loader.host_alloc(0x40, align=16)
    dst_world = loader.host_alloc(0x40, align=16)
    for world, pixels in ((src_world, src_pixels), (dst_world, dst_pixels)):
        loader.write_bytes(world, b"\0" * 0x40)
        loader.write_bytes(world + 4, struct.pack("<iii", width, height, width * 4))
        loader.write_bytes(world + 0x10, struct.pack("<Q", pixels))
        loader.write_bytes(world + 0x18, struct.pack("<Qiii", pixels, width * 4, width, height))
    state = loader.host_alloc(0x80, align=16)
    loader.write_bytes(state, b"\0" * 0x80)
    loader.write_bytes(state + 8, struct.pack("<ii", 6, 6))
    loader.write_bytes(state + 0x10, struct.pack("<QQ", src_world, dst_world))
    loader.write_bytes(state + 0x24, struct.pack("<i", 6))
    neighborhood = loader.host_alloc(72, align=16)
    outputs = [loader.host_alloc(4, align=4) for _ in range(9)]

    current_pointers = []
    current_context = {}
    actual_captures = []

    def executor_hook(ld, _address, _size):
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        # The hook observes the callee after CALL has pushed its return address;
        # stack argument 5 therefore starts at rsp+0x28 (not caller rsp+0x20).
        evaluator = u64(ld, rsp + 0x48)
        vtable = u64(ld, evaluator)
        if not 0x180000000 <= vtable < 0x181000000:
            raise AssertionError({"invalid_evaluator_vtable": hex(vtable),
                                  "evaluator": hex(evaluator),
                                  "context": current_context.copy(),
                                  "stack": ld.read_bytes(rsp, 0x60).hex()})
        color_a = u64(ld, rsp + 0x28)
        color_b = u64(ld, rsp + 0x40)
        actual_captures.append({
            "direction": i32(ld.uc.reg_read(UC_X86_REG_RDX)),
            "start": [i32(ld.uc.reg_read(UC_X86_REG_R8)), i32(ld.uc.reg_read(UC_X86_REG_R9))],
            "color_a_index": current_pointers.index(color_a) if color_a in current_pointers else None,
            "end": [i32(u64(ld, rsp + 0x30)), i32(u64(ld, rsp + 0x38))],
            "color_b_index": current_pointers.index(color_b) if color_b in current_pointers else None,
            "evaluator_bytes": ld.read_bytes(evaluator, 0x20).hex(),
            "evaluator_vtable": hex(vtable),
            "evaluator_function": hex(u64(ld, vtable)),
            "use_source": u64(ld, rsp + 0x50) & 0xFF,
            "leading_span": i32(u64(ld, rsp + 0x58)),
        })
        ld.uc.reg_write(UC_X86_REG_RIP, u64(ld, rsp))
        ld.uc.reg_write(UC_X86_REG_RSP, rsp + 8)

    loader.add_code_hook(EXECUTOR, executor_hook)
    centers = edge_centers(image)
    natural_main_calls = 0
    executor_calls = 0
    mode_counts = {}
    args_digest = hashlib.sha256()
    capture_digest = hashlib.sha256()
    production_digest = hashlib.sha256()
    replay_specs = []
    actual_main_args = []
    mismatches = []

    for x, y in centers:
        current_pointers[:] = [
            src_pixels + ((y + dy) * width + (x + dx)) * 4
            for dy in (-1, 0, 1) for dx in (-1, 0, 1)
        ]
        loader.write_bytes(neighborhood, struct.pack("<9Q", *current_pointers))
        for direction in DIRECTIONS:
            scan_type = i32(loader.call_function(
                CLASSIFIER, [state, x, y, neighborhood, direction],
                max_instructions=100000)["rax"])
            if scan_type != 1:
                continue
            for pointer in outputs:
                loader.write_bytes(pointer, b"\xCC" * 4)
            loader.call_function(
                SUBHANDLER, [state, neighborhood, x, y, direction, *outputs],
                max_instructions=500000)
            words = [struct.unpack("<I", loader.read_bytes(pointer, 4))[0]
                     for pointer in outputs]
            mode, flag_a, flag_b = words[0], words[1] & 0xFF, words[2] & 0xFF
            p9x, p9y, p11x, p11y, p13x, p13y = map(i32, words[3:])
            if p9x == p11x and p9y == p11y:
                continue
            args = [state, neighborhood, x, y, direction, mode, flag_a, flag_b,
                    p9x, p9y, p11x, p11y, p13x, p13y]
            natural_main_calls += 1
            actual_main_args.append(list(map(i32, args[2:])))
            mode_counts[str(mode)] = mode_counts.get(str(mode), 0) + 1
            args_digest.update(struct.pack("<12i", *map(i32, args[2:])))

            actual_captures.clear()
            current_context.clear()
            current_context.update({"center": [x, y], "direction": direction,
                                    "main_args": args[2:]})
            loader.call_function(MAIN, args, max_instructions=250000)
            expected = [normalize(item) for item in actual_captures]
            for capture in actual_captures:
                color_a_index = capture["color_a_index"]
                color_b_index = capture["color_b_index"]
                color_a_xy = [x + color_a_index % 3 - 1, y + color_a_index // 3 - 1]
                color_b_xy = [x + color_b_index % 3 - 1, y + color_b_index // 3 - 1]
                function_address = capture["evaluator_function"]
                replay_specs.append({
                    "args11": [capture["direction"], *capture["start"], *color_a_xy,
                               *capture["end"], *color_b_xy, capture["use_source"],
                               capture["leading_span"]],
                    "evaluator_kind": KIND_TO_FUNCTION.index(function_address),
                    "evaluator_bytes": capture["evaluator_bytes"],
                })
            machine = Machine(loader, instructions, args, current_pointers)
            machine.run()
            got = [normalize(item) for item in machine.captures]
            neighborhood_bytes = b"".join(loader.read_bytes(pointer, 4)
                                            for pointer in current_pointers)
            production = run_production(production_function, args[2:], neighborhood_bytes)
            executor_calls += len(expected)
            capture_digest.update(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode())
            production_digest.update(json.dumps(production, sort_keys=True, separators=(",", ":")).encode())
            if got != expected or production != expected:
                mismatches.append({
                    "center": [x, y], "direction": direction,
                    "main_args": args[2:], "actual": expected,
                    "interpreted": got, "production": production,
                })
                if len(mismatches) >= 10:
                    break
        if len(mismatches) >= 10:
            break

    collect_function = production_library.olmsmoother_collect_natural_main_calls_production
    collect_function.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(NaturalMainCall), ctypes.c_int32,
    ]
    collect_function.restype = ctypes.c_int
    collect_source = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
    centers_flat = (ctypes.c_int32 * (len(centers) * 2))(
        *(coordinate for center in centers for coordinate in center))
    production_calls_buffer = (NaturalMainCall * (len(centers) * 4))()
    production_main_count = collect_function(
        collect_source, width, height, width * 4, centers_flat, len(centers),
        production_calls_buffer, len(production_calls_buffer))
    production_main_args = [list(production_calls_buffer[index].args12)
                            for index in range(production_main_count)]
    main_caller_mismatch = actual_main_args != production_main_args
    first_main_caller_mismatch = None
    if main_caller_mismatch:
        for index in range(max(len(actual_main_args), len(production_main_args))):
            actual_item = actual_main_args[index] if index < len(actual_main_args) else None
            production_item = production_main_args[index] if index < len(production_main_args) else None
            if actual_item != production_item:
                first_main_caller_mismatch = {"index": index, "actual": actual_item,
                                              "production": production_item}
                break

    # Remove the interception hook before replaying every captured Executor
    # call in natural scan order against the actual function body.
    executor_hook_handle = loader._code_hooks.pop()
    loader.uc.hook_del(executor_hook_handle)
    loader.write_bytes(dst_pixels, bytes(argb))
    for spec in replay_specs:
        evaluator = loader.host_alloc(0x20, align=16)
        loader.write_bytes(evaluator, bytes.fromhex(spec["evaluator_bytes"]))
        a = spec["args11"]
        color_a = src_pixels + (a[4] * width + a[3]) * 4
        color_b = src_pixels + (a[8] * width + a[7]) * 4
        loader.call_function(
            EXECUTOR, [state, a[0], a[1], a[2], color_a, a[5], a[6],
                       color_b, evaluator, a[9], a[10]],
            max_instructions=100000)
    actual_replay = loader.read_bytes(dst_pixels, len(argb))

    executor_function = production_library.olmsmoother_run_executor8_production
    executor_function.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    source_array = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
    destination_array = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
    for spec in replay_specs:
        args11 = (ctypes.c_int32 * 11)(*spec["args11"])
        raw = bytes.fromhex(spec["evaluator_bytes"])
        if spec["evaluator_kind"] == 2:
            semantic_fields = raw[8:20] + raw[0x18:0x1C]
        else:
            semantic_fields = raw[8:24]
        fields = (ctypes.c_uint32 * 4)(*struct.unpack("<4I", semantic_fields))
        executor_function(source_array, destination_array, width, height, width * 4,
                          args11, spec["evaluator_kind"], fields)
    production_replay = bytes(destination_array)
    replay_mismatch = sum(a != b for a, b in zip(actual_replay, production_replay))

    report = {
        "schema_version": 1,
        "status": "exact" if not mismatches and replay_mismatch == 0 and not main_caller_mismatch else "fail",
        "actual_aex_sha256": SHA,
        "input_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "edge_centers": len(centers),
        "classifier_calls": len(centers) * len(DIRECTIONS),
        "natural_main_calls": natural_main_calls,
        "executor_calls": executor_calls,
        "mode_counts": mode_counts,
        "main_args_sha256": args_digest.hexdigest(),
        "normalized_executor_captures_sha256": capture_digest.hexdigest(),
        "production_executor_captures_sha256": production_digest.hexdigest(),
        "mismatch_count": len(mismatches) + int(replay_mismatch != 0) + int(main_caller_mismatch),
        "first_mismatches": mismatches,
        "executor_replay_calls": len(replay_specs),
        "actual_executor_replay_sha256": hashlib.sha256(actual_replay).hexdigest(),
        "production_executor_replay_sha256": hashlib.sha256(production_replay).hexdigest(),
        "actual_vs_production_executor_replay_mismatch": replay_mismatch,
        "production_natural_main_calls": production_main_count,
        "main_caller_mismatch": main_caller_mismatch,
        "first_main_caller_mismatch": first_main_caller_mismatch,
        "scope": "case_0001 nonuniform 3x3 centers; actual Classifier8/SubHandler8 ownership and actual-versus-CFG-interpreted MainInterpKernel8 Executor ABI boundary",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert not mismatches and replay_mismatch == 0 and not main_caller_mismatch
    # Keep the temporary library and CDLL alive through the final native call.
    del production_library
    temporary_library.cleanup()


if __name__ == "__main__":
    main()
