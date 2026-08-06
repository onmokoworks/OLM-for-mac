#!/usr/bin/env python3
"""Compare generated PF16 walker/sub-handler with the pinned Windows AEX."""
import ctypes, hashlib, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader
from unicorn.x86_const import (UC_X86_REG_RCX, UC_X86_REG_RDX,
                               UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP)

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
INPUT = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806/inputs/smoother_v1_case0001_rgba8.png"
if not INPUT.exists():
    INPUT = ROOT / "tmp/olmsmoother_v1_pf16_boundary_fixed_20260806/package/inputs/smoother_v1_case0001_rgba8.png"
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_pf16_control_harness_20260806.cpp"


class MainCall16(ctypes.Structure):
    _fields_ = [("values", ctypes.c_int32 * 11),
                ("evaluator_kind", ctypes.c_int32),
                ("fields", ctypes.c_uint32 * 5)]


def main() -> None:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    image = Image.open(INPUT).convert("RGBA").crop((380, 170, 480, 270))
    words = []
    for red, green, blue, alpha in image.getdata():
        words.extend((alpha * 32768 // 255, red * 32768 // 255,
                      green * 32768 // 255, blue * 32768 // 255))
    raw = struct.pack("<%dH" % len(words), *words); width = height = 100

    with tempfile.TemporaryDirectory() as directory:
        library = Path(directory) / "pf16_control.dylib"
        subprocess.run(["clang++", "-std=c++17", "-O2", "-fPIC", "-shared",
                        "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS),
                        "-o", str(library)], check=True, capture_output=True)
        port = ctypes.CDLL(str(library)); pixels = (ctypes.c_uint16 * len(words))(*words)

        loader = AexLoader(str(AEX), verbose=False, fast=True)
        pixel_address = loader.host_alloc(len(raw), align=16); loader.write_bytes(pixel_address, raw)
        world = loader.host_alloc(0x50, align=16); loader.write_bytes(world, b"\0" * 0x50)
        loader.write_bytes(world + 4, struct.pack("<iii", width, height, width * 8))
        loader.write_bytes(world + 0x10, struct.pack("<Q", pixel_address))
        loader.write_bytes(world + 0x18, struct.pack("<Qiii", pixel_address, width * 8, width, height))
        state = loader.host_alloc(0x80, align=16); loader.write_bytes(state, b"\0" * 0x80)
        loader.write_bytes(state + 8, struct.pack("<ii", 6, 6))
        loader.write_bytes(state + 0x10, struct.pack("<i", 6))
        loader.write_bytes(state + 0x18, struct.pack("<Q", world))
        neighborhood = loader.host_alloc(72, align=16)
        outputs = [loader.host_alloc(4, align=4) for _ in range(9)]

        def pointers(x: int, y: int) -> list[int]:
            return [0 if not (0 <= x + dx < width and 0 <= y + dy < height)
                    else pixel_address + ((y + dy) * width + x + dx) * 8
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)]

        compared = 0
        main_args = []
        for y in range(height):
            for x in range(width):
                loader.write_bytes(neighborhood, struct.pack("<9Q", *pointers(x, y)))
                for direction in (5, 3, 1, 7):
                    scan = loader.call_function(0x180006A90,
                        [state, x, y, neighborhood, direction], max_instructions=100000)["rax"] & 0xffffffff
                    if scan != 1: continue
                    for output in outputs: loader.write_bytes(output, b"\0" * 4)
                    loader.call_function(0x180002740,
                        [state, neighborhood, x, y, direction, *outputs], max_instructions=1000000)
                    actual = [struct.unpack("<I", loader.read_bytes(output, 4))[0] for output in outputs]
                    got_buffer = (ctypes.c_uint32 * 9)()
                    port.olmsmoother_subhandler16_exact(
                        pixels, width, height, x, y, direction, 6, got_buffer)
                    got = list(got_buffer)
                    assert got == actual, (x, y, direction, actual, got)
                    main_args.append([x, y, direction, *actual])
                    compared += 1

        # Canonical first interpolation call.  This covers the exceptional
        # LinearOffsetZeroOneValue layout: its t==1 endpoint lives at +0x18.
        args12 = [84, 0, 5, 2, 0, 0, 85, 0, 85, 0, 84, 0]
        loader.write_bytes(neighborhood, struct.pack("<9Q", *pointers(84, 0)))
        captured = []
        def intercept(ld, _address, _size):
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            evaluator = struct.unpack("<Q", ld.read_bytes(rsp + 0x48, 8))[0]
            def stack_i32(offset):
                return struct.unpack("<i", ld.read_bytes(rsp + offset, 4))[0]
            def pixel_xy(address):
                word_offset = (address - pixel_address) // 2
                return ((word_offset % (width * 4)) // 4, word_offset // (width * 4))
            a = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
            b = struct.unpack("<Q", ld.read_bytes(rsp + 0x40, 8))[0]
            values = [ld.uc.reg_read(UC_X86_REG_RDX) & 0xffffffff,
                      ld.uc.reg_read(UC_X86_REG_R8) & 0xffffffff,
                      ld.uc.reg_read(UC_X86_REG_R9) & 0xffffffff,
                      *pixel_xy(a), stack_i32(0x30), stack_i32(0x38),
                      *pixel_xy(b), ld.read_bytes(rsp + 0x50, 1)[0], stack_i32(0x58)]
            values = [struct.unpack("<i", struct.pack("<I", v & 0xffffffff))[0] for v in values]
            vtable = struct.unpack("<Q", ld.read_bytes(evaluator, 8))[0]
            fields = list(struct.unpack("<5I", ld.read_bytes(evaluator + 8, 20)))
            captured.append((values, 2 if vtable == 0x18000D1E8 else -1, fields))
            ld.uc.emu_stop()
        loader.add_code_hook(0x180005F60, intercept)
        loader.call_function(0x180004B80, [state, neighborhood, *args12],
                             max_instructions=250000)
        output = (MainCall16 * 4)()
        port.olmsmoother_mainkernel16_capture.restype = ctypes.c_int
        count = port.olmsmoother_mainkernel16_capture(
            pixels, width, height, (ctypes.c_int32 * 12)(*args12), output, 4)
        candidate = (list(output[0].values), output[0].evaluator_kind,
                     list(output[0].fields))
        assert count == 1 and captured == [candidate], (captured, candidate)

        # Complete the same MainKernel call against separate source/destination
        # worlds and compare every PF16 output word.
        loader.uc.hook_del(loader._code_hooks.pop())
        dst_address = loader.host_alloc(len(raw), align=16)
        loader.write_bytes(dst_address, raw)
        dst_world = loader.host_alloc(0x50, align=16)
        loader.write_bytes(dst_world, b"\0" * 0x50)
        loader.write_bytes(dst_world + 4, struct.pack("<iii", width, height, width * 8))
        loader.write_bytes(dst_world + 0x10, struct.pack("<Q", dst_address))
        loader.write_bytes(dst_world + 0x18,
                           struct.pack("<Qiii", dst_address, width * 8, width, height))
        loader.write_bytes(state + 0x18, struct.pack("<QQ", world, dst_world))
        loader.call_function(0x180004B80, [state, neighborhood, *args12],
                             max_instructions=1000000)
        actual_main = loader.read_bytes(dst_address, len(raw))
        candidate_dst = (ctypes.c_uint16 * len(words))(*words)
        port.olmsmoother_mainkernel16_execute(
            pixels, candidate_dst, width, height,
            (ctypes.c_int32 * 12)(*args12))
        candidate_main = bytes(candidate_dst)
        assert candidate_main == actual_main, [
            (i // 4 % width, i // 4 // width, i % 4,
             struct.unpack_from("<H", actual_main, i * 2)[0],
             struct.unpack_from("<H", candidate_main, i * 2)[0])
            for i in range(len(words))
            if actual_main[i*2:i*2+2] != candidate_main[i*2:i*2+2]
        ][:20]

        # Exercise every canonical scan_type=1 tuple independently.  This
        # separates a branch-local Main/Executor discrepancy from ordering
        # effects in the full render worker.
        for case_index, case_args in enumerate(main_args):
            loader.write_bytes(dst_address, raw)
            loader.write_bytes(neighborhood,
                               struct.pack("<9Q", *pointers(case_args[0], case_args[1])))
            loader.call_function(0x180004B80,
                                 [state, neighborhood, *case_args],
                                 max_instructions=1000000)
            actual_case = loader.read_bytes(dst_address, len(raw))
            case_dst = (ctypes.c_uint16 * len(words))(*words)
            port.olmsmoother_mainkernel16_execute(
                pixels, case_dst, width, height,
                (ctypes.c_int32 * 12)(*case_args))
            candidate_case = bytes(case_dst)
            if candidate_case != actual_case:
                differences = [
                    (i // 4 % width, i // 4 // width, i % 4,
                     struct.unpack_from("<H", actual_case, i * 2)[0],
                     struct.unpack_from("<H", candidate_case, i * 2)[0])
                    for i in range(len(words))
                    if actual_case[i*2:i*2+2] != candidate_case[i*2:i*2+2]
                ]
                raise AssertionError((case_index, case_args, differences[:20]))

        # Repeat in scan order with a shared destination, matching the
        # worker's overlapping-write behavior.
        loader.write_bytes(dst_address, raw)
        cumulative_dst = (ctypes.c_uint16 * len(words))(*words)
        for case_index, case_args in enumerate(main_args):
            loader.write_bytes(neighborhood,
                               struct.pack("<9Q", *pointers(case_args[0], case_args[1])))
            loader.call_function(0x180004B80,
                                 [state, neighborhood, *case_args],
                                 max_instructions=1000000)
            port.olmsmoother_mainkernel16_execute(
                pixels, cumulative_dst, width, height,
                (ctypes.c_int32 * 12)(*case_args))
            actual_case = loader.read_bytes(dst_address, len(raw))
            candidate_case = bytes(cumulative_dst)
            if candidate_case != actual_case:
                differences = [
                    (i // 4 % width, i // 4 // width, i % 4,
                     struct.unpack_from("<H", actual_case, i * 2)[0],
                     struct.unpack_from("<H", candidate_case, i * 2)[0])
                    for i in range(len(words))
                    if actual_case[i*2:i*2+2] != candidate_case[i*2:i*2+2]
                ]
                raise AssertionError(("cumulative", case_index, case_args, differences[:20]))

        # Finally compare the production per-pixel callback, including
        # classifier scan types 2/3/4 and dispatch order.
        loader.write_bytes(dst_address, raw)
        scan_dst = (ctypes.c_uint16 * len(words))(*words)
        for scan_y in range(height):
            for scan_x in range(width):
                pixel_offset = (scan_y * width + scan_x) * 8
                loader.call_function(0x180009470,
                                     [state, scan_x, scan_y,
                                      pixel_address + pixel_offset,
                                      dst_address + pixel_offset],
                                     max_instructions=2000000)
                port.olmsmoother_scanpixel16_execute(
                    pixels, scan_dst, width, height, scan_x, scan_y)
                actual_scan = loader.read_bytes(dst_address, len(raw))
                candidate_scan = bytes(scan_dst)
                if candidate_scan != actual_scan:
                    differences = [
                        (i // 4 % width, i // 4 // width, i % 4,
                         struct.unpack_from("<H", actual_scan, i * 2)[0],
                         struct.unpack_from("<H", candidate_scan, i * 2)[0])
                        for i in range(len(words))
                        if actual_scan[i*2:i*2+2] != candidate_scan[i*2:i*2+2]
                    ]
                    raise AssertionError(("scan", scan_x, scan_y, differences[:20]))
        assert compared == 80, compared
        print("PASS actual-AEX PF16 control=80 main=80/80 cumulative=exact scan=10000 exact")


if __name__ == "__main__": main()
