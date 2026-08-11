#!/usr/bin/env python3
"""Cross effective Color Key, smoothing range, geometry, and PF8/PF16."""

import ctypes
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from unicorn import UC_PROT_ALL
from unicorn.x86_const import UC_X86_REG_RSP
from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
ENTRY = 0x18000A2C0
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_key_tolerance_geometry_production_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.json"
DOC = ROOT / "refs/conformance/olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.md"
W, H = 7, 5
KEY = (202, 187, 230)
TOLERANCES = (0, 1, 6, 127, 255)

ASM = r"""
.text
.globl iterate_guest
iterate_guest:
 pushq %rbx
 pushq %rbp
 pushq %rsi
 pushq %rdi
 pushq %r12
 pushq %r13
 pushq %r14
 pushq %r15
 subq $0x38, %rsp
 movl %edx, %r12d
 movl %r8d, %r13d
 movq %r9, %r14
 movq 0xa8(%rsp), %rsi
 movq 0xb0(%rsp), %r15
 movq 0xb8(%rsp), %rdi
 movq 0x18(%r14), %rbx
 movq 0x18(%rdi), %rbp
 movl 0x20(%r14), %eax
 movl %eax, 0x28(%rsp)
 movl 0x20(%rdi), %eax
 movl %eax, 0x2c(%rsp)
 movl 0x24(%r14), %eax
 movl %eax, 0x30(%rsp)
.Ly:
 cmpl %r13d, %r12d
 jge .Ldone
 movl $0, 0x34(%rsp)
.Lx:
 movl 0x34(%rsp), %eax
 cmpl 0x30(%rsp), %eax
 jge .Lnexty
 movslq %r12d, %rcx
 movslq 0x28(%rsp), %rdx
 imulq %rdx, %rcx
 leaq (%rbx,%rcx), %r9
 movslq 0x34(%rsp), %rax
 imulq $PIXEL_SIZE, %rax
 addq %rax, %r9
 movslq %r12d, %rcx
 movslq 0x2c(%rsp), %rdx
 imulq %rdx, %rcx
 leaq (%rbp,%rcx), %rdx
 addq %rax, %rdx
 movq %rdx, 0x20(%rsp)
 movq %rsi, %rcx
 movl 0x34(%rsp), %edx
 movl %r12d, %r8d
 callq *%r15
 testl %eax, %eax
 jne .Lret
 incl 0x34(%rsp)
 jmp .Lx
.Lnexty:
 incl %r12d
 jmp .Ly
.Ldone:
 xorl %eax, %eax
.Lret:
 addq $0x38, %rsp
 popq %r15
 popq %r14
 popq %r13
 popq %r12
 popq %rdi
 popq %rsi
 popq %rbp
 popq %rbx
 retq
"""


def widen(value):
    return (value * 0x8000 + 0x80) // 0xFF


def u64(loader, address):
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def u32(loader, address):
    return struct.unpack("<I", loader.read_bytes(address, 4))[0]


def guest_code(directory, pixel_size):
    source = directory / f"iterate{pixel_size}.s"
    obj = directory / f"iterate{pixel_size}.obj"
    source.write_text(ASM.replace("PIXEL_SIZE", str(pixel_size)))
    subprocess.run(["clang", "-target", "x86_64-pc-windows-msvc", "-c", str(source), "-o", str(obj)], check=True)
    raw = obj.read_bytes()
    _, count, _, _, _, opt, _ = struct.unpack_from("<HHIIIHH", raw, 0)
    section_base = 20 + opt
    for index in range(count):
        section = section_base + index * 40
        name = raw[section:section + 8].rstrip(b"\0")
        size, pointer = struct.unpack_from("<II", raw, section + 16)
        if name == b".text":
            return raw[pointer:pointer + size]
    raise RuntimeError("COFF .text missing")


def fixture(depth):
    # Key islands at both corners and the center interrupt a nonuniform
    # checkerboard.
    # This deliberately keeps the bounded family on the actual-AEX branches
    # already understood by the PF16 CFG evidence while still making both the
    # key pass and smoothing pass observable.
    key_locations = {(0, 0), (6, 0), (3, 2), (0, 4), (6, 4)}
    q = []
    for y in range(H):
        for x in range(W):
            value = 128 if (x + y) & 1 else 0
            q.append((255, *KEY) if (x, y) in key_locations else
                     (255, value, value, value))
    pixel_size = 4 if depth == 8 else 8
    rowbytes = W * pixel_size + 8
    payload = bytearray()
    for y in range(H):
        for p in q[y*W:(y+1)*W]:
            if depth == 8:
                payload += bytes(p)
            else:
                payload += struct.pack("<4H", *(widen(v) for v in p))
        payload += bytes([0xD0 + y]) * 8
    return bytes(payload), rowbytes


def actual(depth, payload, rowbytes, use_key, tolerance, code, diagnostics=False):
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    trace = []
    guest = 0x83000000
    loader.uc.mem_map(guest, 0x1000, UC_PROT_ALL)
    loader.uc.mem_write(guest, code)
    iterate_suite = loader.host_alloc(8)
    loader.write_bytes(iterate_suite, struct.pack("<Q", guest))

    def acquire(ld, args):
        ld.write_bytes(args[2], struct.pack("<Q", iterate_suite))
        trace.append("acquire")
        return 0

    def release(_ld, _args):
        trace.append("release")
        return 0

    suite_provider = loader.host_alloc(16)
    loader.write_bytes(suite_provider, struct.pack("<2Q", loader.install_callback("acquire", acquire), loader.install_callback("release", release)))

    def make_world(data_payload=None, fill=0):
        data = loader.host_alloc(rowbytes * H, align=16)
        loader.write_bytes(data, data_payload if data_payload is not None else bytes([fill]) * (rowbytes * H))
        world = loader.host_alloc(0x80, align=16)
        loader.write_bytes(world, b"\0" * 0x80)
        # PF_WORLD_IS_DEEP reads the world flags at +0x10.  The separate
        # bitdepth word is retained for the fixture record, but does not drive
        # the Windows dispatch.
        loader.write_bytes(world + 0x10, struct.pack("<I", 1 if depth == 16 else 0))
        loader.write_bytes(world + 0x18, struct.pack("<Qiii", data, rowbytes, W, H))
        loader.write_bytes(world + 0x2C, struct.pack("<H", depth))
        loader.write_bytes(world + 0x30, struct.pack("<4i", 0, 0, H, W))
        return world, data

    def copy(ld, args):
        src, dst = args[1], args[2]
        for y in range(H):
            ld.write_bytes(u64(ld, dst + 0x18) + y * u32(ld, dst + 0x20), ld.read_bytes(u64(ld, src + 0x18) + y * u32(ld, src + 0x20), W * (depth // 2)))
        trace.append("copy")
        return 0

    def new_world(ld, args):
        out_pointer = u64(ld, ld.uc.reg_read(UC_X86_REG_RSP) + 0x28)
        world, _ = make_world(None, 0xC3)
        ld.write_bytes(out_pointer, ld.read_bytes(world, 0x80))
        trace.append("new_world")
        return 0

    def dispose(_ld, _args):
        trace.append("dispose")
        return 0

    utilities = loader.host_alloc(0x90)
    loader.write_bytes(utilities, b"\0" * 0x90)
    loader.write_bytes(utilities + 0x40, struct.pack("<Q", loader.install_callback("copy", copy)))
    loader.write_bytes(utilities + 0x70, struct.pack("<Q", loader.install_callback("new_world", new_world)))
    loader.write_bytes(utilities + 0x78, struct.pack("<Q", loader.install_callback("dispose", dispose)))
    indata = loader.host_alloc(0x200)
    loader.write_bytes(indata, b"\0" * 0x200)
    loader.write_bytes(indata + 0xB0, struct.pack("<QQ", utilities, 0x1234))
    loader.write_bytes(indata + 0x180, struct.pack("<Q", suite_provider))
    outdata = loader.host_alloc(0x200)
    loader.write_bytes(outdata, b"\0" * 0x200)
    output, output_data = make_world(None, 0xA5)
    input_world, _ = make_world(payload)
    params = []
    for _ in range(4):
        param = loader.host_alloc(0x200)
        loader.write_bytes(param, b"\0" * 0x200)
        params.append(param)
    loader.write_bytes(params[0] + 0x38, loader.read_bytes(input_world, 0x80))
    loader.write_bytes(params[1] + 0x38, struct.pack("<I", use_key))
    loader.write_bytes(params[2] + 0x38, bytes((255, *KEY)))
    loader.write_bytes(params[3] + 0x38, struct.pack("<I", tolerance))
    parameter_array = loader.host_alloc(32)
    loader.write_bytes(parameter_array, struct.pack("<4Q", *params))
    mask_entry = 0x1800026E0 if depth == 8 else 0x180002670
    main_entry = 0x1800095B0 if depth == 8 else 0x180009470
    loader.add_code_hook(mask_entry, lambda *_: trace.append("mask"))
    loader.add_code_hook(main_entry, lambda *_: trace.append("main"))
    # These are the natural classifier and interpolation-executor entries used
    # below the PF16 main callback.  Keep them available to larger geometry
    # fixtures without changing the compact historical report schema.
    if diagnostics and depth == 16:
        loader.add_code_hook(0x180006A90, lambda *_: trace.append("classifier"))
        loader.add_code_hook(0x180005F60, lambda *_: trace.append("executor"))
    result = loader.call_function(ENTRY, [11, indata, outdata, parameter_array, output, 0], max_instructions=100_000_000)
    assert result["rax"] == 0
    rendered = loader.read_bytes(output_data, rowbytes * H)
    if diagnostics:
        source_data = u64(loader, input_world + 0x18)
        return rendered, trace, loader.read_bytes(source_data, rowbytes * H)
    return rendered, trace


def build_production():
    temporary = tempfile.TemporaryDirectory(prefix="sm1-key-tol-prod-")
    dylib = Path(temporary.name) / "lib.dylib"
    subprocess.run(["clang++", "-std=c++17", "-O2", "-shared", "-fPIC", "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS), "-o", str(dylib)], check=True, capture_output=True)
    return temporary, ctypes.CDLL(str(dylib))


def production(lib, depth, payload, rowbytes, use_key, tolerance):
    scalar = ctypes.c_uint8 if depth == 8 else ctypes.c_uint16
    fn = getattr(lib, f"olmsmoother_v1_effectmain_render{depth}_matrix")
    fn.argtypes = [ctypes.POINTER(scalar), ctypes.POINTER(scalar), ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_int32]
    count = len(payload) if depth == 8 else len(payload) // 2
    values = list(payload) if depth == 8 else list(struct.unpack(f"<{count}H", payload))
    src = (scalar * count)(*values)
    seed = 0xA5 if depth == 8 else 0xA5A5
    dst = (scalar * count)(*([seed] * count))
    assert fn(src, dst, W, H, rowbytes, use_key, *KEY, tolerance) == 0
    return bytes(dst) if depth == 8 else struct.pack(f"<{count}H", *dst)


def active(payload, depth, rowbytes):
    active_bytes = W * (4 if depth == 8 else 8)
    return b"".join(payload[y*rowbytes:y*rowbytes+active_bytes] for y in range(H))


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA
    temporary, lib = build_production()
    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix="sm1-key-tol-guest-") as td:
            codes = {depth: guest_code(Path(td), 4 if depth == 8 else 8) for depth in (8, 16)}
        for depth in (8, 16):
            payload, rowbytes = fixture(depth)
            for use_key in (0, 1):
                for tolerance in TOLERANCES:
                    win, trace = actual(depth, payload, rowbytes, use_key, tolerance, codes[depth])
                    mac = production(lib, depth, payload, rowbytes, use_key, tolerance)
                    assert win == mac, (depth, use_key, tolerance, next((i,a,b) for i,(a,b) in enumerate(zip(win,mac)) if a != b))
                    assert all(win[y*rowbytes+W*(4 if depth==8 else 8):(y+1)*rowbytes] == bytes([0xA5])*8 for y in range(H))
                    rows.append({"depth": depth, "use_key": use_key, "tolerance": tolerance, "raw_sha256": hashlib.sha256(win).hexdigest(), "active_sha256": hashlib.sha256(active(win,depth,rowbytes)).hexdigest(), "changed_active_bytes_from_input": sum(a != b for a,b in zip(active(win,depth,rowbytes),active(payload,depth,rowbytes))), "trace_counts": {name: trace.count(name) for name in ("mask","main","copy","new_world","dispose")}})
    finally:
        temporary.cleanup()
    for depth in (8,16):
        subset=[r for r in rows if r["depth"]==depth]
        assert all(r["trace_counts"]["main"] == W*H for r in subset)
        assert all(r["trace_counts"]["mask"] == (W*H if r["use_key"] else 0) for r in subset)
        assert any(r["changed_active_bytes_from_input"] > 0 for r in subset if not r["use_key"])
        assert any(r["changed_active_bytes_from_input"] > 0 for r in subset if r["use_key"])
        assert len({r["active_sha256"] for r in subset if not r["use_key"]}) >= 3
        assert len({r["active_sha256"] for r in subset if r["use_key"]}) >= 3
        for tolerance in TOLERANCES:
            off=next(r for r in subset if not r["use_key"] and r["tolerance"]==tolerance)
            on=next(r for r in subset if r["use_key"] and r["tolerance"]==tolerance)
            assert off["active_sha256"] != on["active_sha256"]
    report={"schema_version":1,"status":"exact","verdict":"PASS_V1_EFFECTIVE_COLOR_KEY_TOLERANCE_GEOMETRY_PF8_PF16_EXPORTED_EFFECTMAIN_EXACT","actual_aex_sha256":AEX_SHA,"scope":"actual exported PF_Cmd_RENDER vs production EffectMain; padded nonuniform 7x5; effective Color Key off/on x Do Smooth Range 0/1/6/127/255 x PF8/PF16","fixture":{"width":W,"height":H,"key_rgb8":KEY,"tolerances":TOLERANCES,"key_locations":"both top corners, center, both bottom corners","background":"nonuniform grayscale 0/128 checkerboard","padding_bytes_per_row":8},"nonvacuity":{"smoothing_changes_active_pixels_in_both_key_states_and_depths":True,"tolerance_255_key_off_identity_equivalence_recorded":True,"key_on_off_distinct_all_tolerances_depths":True,"at_least_three_distinct_tolerance_outputs_each_key_state_depth":True,"mask_callback_count_exact":True,"main_callback_count_exact":True},"cases":rows,"claims_not_made":["PF32","other key colors","arbitrary geometry","AE host/export color management"]}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text("# OLMSmoother v1 Color Key × smoothing × geometry boundary\n\nVerdict: `"+report["verdict"]+"`\n\nA padded nonuniform 7×5 fixture crosses effective Color Key off/on and Do Smooth Range 0/1/6/127/255 at PF8 and PF16 through the actual exported Windows AEX `PF_Cmd_RENDER` and production `EffectMain`. Active pixels and row padding are byte-exact in all 20 cells. Key, tolerance and main-kernel effects are independently non-vacuous.\n\nPF32, other key colors/geometries and AE host/export color management remain unclaimed.\n")
    print(report["verdict"])


if __name__ == "__main__":
    main()
