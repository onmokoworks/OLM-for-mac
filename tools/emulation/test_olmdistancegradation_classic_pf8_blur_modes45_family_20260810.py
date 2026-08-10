#!/usr/bin/env python3
"""Close actual-AEX PF8 public Blur Mode 3/4/5 rendering semantics."""
import hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader
import cv_bridge as cvb
import opencv_impls as ocv
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_fieldgen_p1b import setup_tls
from test_dg_compose import (
    OFF_BG_B, OFF_BG_G, OFF_BG_R, OFF_DEGENERATE, OFF_FIELD_WORLD_PTR,
    OFF_GRAD_B, OFF_GRAD_G, OFF_GRAD_R, OFF_INOUT_MODE, OFF_INTERP_MODE,
    OFF_INVERT, OFF_POWER, OFF_RENDER_MODE, OFF_SRC_WORLD_PTR, OFF_USE_BG,
    alloc_refcon, make_loader,
)
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RIP, UC_X86_REG_RSP

AEX = ROOT / "plugins_2025/DistanceGradation.aex"
AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
BLUR = 0x1812864D0
COMPOSE8 = 0x181170870
W, H = 17, 11
INPUT_ROWBYTES, OUTPUT_ROWBYTES = 75, 79
HARNESS = HERE / "dg_classic_pf8_blur_modes45_family_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_classic_pf8_blur_modes45_family_exact_20260810.json"
DOC = ROOT / "refs/conformance/olmdistancegradation_classic_pf8_blur_modes45_family_exact_20260810.md"


def actual_blur(field, mode):
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    setup_tls(loader)
    ocv.register_opencv_impls(loader, "DistanceGradation",
                              ops=["threshold", "dist_transform", "resize_same_shape", "normalize_minmax"])
    tls_value = loader.host_alloc(0x20)
    loader.write_bytes(tls_value, b"\0" * 0x20)

    def tls_shim(ld, _address, _size):
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", ld.read_bytes(rsp, 8))[0]
        ld.uc.reg_write(UC_X86_REG_RAX, tls_value)
        ld.uc.reg_write(UC_X86_REG_RSP, rsp + 8)
        ld.uc.reg_write(UC_X86_REG_RIP, ret)

    loader.add_code_hook(0x181187E20, tls_shim)
    loader.add_code_hook(0x181187F50, tls_shim)

    def release(_ld, _args):
        return 0

    object_box = {}

    def allocate(ld, _args):
        data = ld.bump_alloc(0x20000, align=64)
        ld.write_bytes(data, b"\0" * 0x20000)
        umat = ld.host_alloc(0x80)
        ld.write_bytes(umat, b"\0" * 0x80)
        ld.write_bytes(umat + 8, struct.pack("<Q", object_box["object"]))
        ld.write_bytes(umat + 0x14, struct.pack("<I", 1))
        ld.write_bytes(umat + 0x18, struct.pack("<QQQ", data, data, 0x20000))
        return umat

    allocate_ptr = loader.install_callback("DG.MatAllocator.allocate", allocate)
    release_ptr = loader.install_callback("DG.MatAllocator.deallocate", release)
    vtable = loader.host_alloc(0x40)
    loader.write_bytes(vtable, b"\0" * 0x40)
    loader.write_bytes(vtable + 0x10, struct.pack("<Q", allocate_ptr))
    loader.write_bytes(vtable + 0x28, struct.pack("<Q", release_ptr))
    allocator = loader.host_alloc(0x10)
    object_box["object"] = allocator
    loader.write_bytes(allocator, struct.pack("<Q", vtable) + b"\0" * 8)

    def allocator_shim(ld, _address, _size):
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", ld.read_bytes(rsp, 8))[0]
        ld.uc.reg_write(UC_X86_REG_RAX, allocator)
        ld.uc.reg_write(UC_X86_REG_RSP, rsp + 8)
        ld.uc.reg_write(UC_X86_REG_RIP, ret)

    loader.add_code_hook(0x18118D2A0, allocator_shim)
    src = cvb.build_ipl(loader, np.ascontiguousarray(field, dtype=np.float32), align_step=16)
    dst = cvb.build_ipl(loader, np.full((H, W), -777.0, np.float32), align_step=16)
    regs = loader.call_function(BLUR, int_args=[src, dst, mode - 1, 3, 3, 0, 0],
                                max_instructions=30_000_000)
    return np.ascontiguousarray(cvb.read_ipl(loader, dst), dtype="<f4"), int(regs["instructions"])


def world8(loader, pixels):
    data = loader.bump_alloc(W * H * 4, align=64)
    loader.write_bytes(data, pixels)
    world = loader.host_alloc(0x80, align=16)
    loader.write_bytes(world, b"\0" * 0x80)
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<III", W * 4, W, H))
    return world


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    mask = np.ones((H, W), np.uint8)
    mask[2:9, 4:13] = 0
    source_pixels = [
        (255, (x * 997 + y * 211) % 256, (x * 613 + y * 1231) % 256,
         (x * 1499 + y * 307) % 256) if mask[y, x] else (0, 0, 0, 0)
        for y in range(H) for x in range(W)
    ]
    source_active = b"".join(bytes((a, r, g, b)) for a, g, r, b in source_pixels)
    source_padded = b"".join(
        source_active[y * W * 4:(y + 1) * W * 4] + b"\xa5" * (INPUT_ROWBYTES - W * 4)
        for y in range(H)
    )

    loader = make_loader()
    loader.register_libm_impls(max_threads=1)
    source_world = world8(loader, b"".join(bytes(p) for p in source_pixels))
    refcon = alloc_refcon(loader)

    def put(offset, fmt, value):
        loader.write_bytes(refcon + offset, struct.pack(fmt, value))

    for item in (
        (OFF_SRC_WORLD_PTR, "<Q", source_world), (OFF_DEGENERATE, "<B", 0),
        (OFF_USE_BG, "<B", 0), (OFF_INVERT, "<B", 1),
        (OFF_INOUT_MODE, "<i", 1), (OFF_RENDER_MODE, "<i", 1),
        (OFF_POWER, "<f", 1.0), (OFF_GRAD_G, "<f", 0.0),
        (OFF_GRAD_R, "<f", 28 / 255), (OFF_GRAD_B, "<f", 238 / 255),
        (OFF_BG_G, "<f", 160 / 255), (OFF_BG_R, "<f", 16 / 255),
        (OFF_BG_B, "<f", 48 / 255),
    ):
        put(*item)

    rows = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        source_path, expected_path, executable = temp / "source", temp / "expected", temp / "harness"
        source_path.write_bytes(source_padded)
        build = subprocess.run([
            "clang++", "-std=c++17", "-O0", "-I", str(HERE / "dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(executable),
        ], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr

        for interp_name, interp_mode, constant in (("constant", 1, True), ("linear", 2, False)):
            field, field_trace = run_aex_fieldgen(mask, 4, 1 if constant else 0)
            preblur = (field >= 1.0).astype(np.float32) if constant else field
            for blur_mode in (3, 4, 5):
                blurred, instructions = actual_blur(preblur, blur_mode)
                staged = np.rint(np.clip(blurred, 0, 1) * 255).astype(np.uint8)
                field_world = world8(loader, b"".join(
                    bytes((0, int(staged[y, x]), 0, 0)) for y in range(H) for x in range(W)
                ))
                put(OFF_FIELD_WORLD_PTR, "<Q", field_world)
                put(OFF_INTERP_MODE, "<i", interp_mode)
                output = []
                for y in range(H):
                    for x in range(W):
                        pixel = loader.bump_alloc(4, align=8)
                        loader.write_bytes(pixel, b"\xee" * 4)
                        loader.call_function(COMPOSE8, int_args=[refcon, x, y, 0, pixel],
                                             max_instructions=200_000)
                        raw = loader.read_bytes(pixel, 4)  # callback-local A,G,R,B
                        output.append(bytes((raw[0], raw[2], raw[1], raw[3])))
                active = b"".join(output)
                expected = b"".join(
                    active[y * W * 4:(y + 1) * W * 4] + b"\xa5" * (OUTPUT_ROWBYTES - W * 4)
                    for y in range(H)
                )
                expected_path.write_bytes(expected)
                run = subprocess.run([str(executable), str(source_path), str(expected_path),
                                      interp_name, str(blur_mode)], capture_output=True, text=True)
                assert run.returncode == 0, run.stderr
                print(run.stdout, end="")
                rows.append({
                    "interpolation": interp_name, "blur_mode": blur_mode,
                    "field_sha256": hashlib.sha256(field.astype("<f4").tobytes()).hexdigest(),
                    "preblur_sha256": hashlib.sha256(preblur.astype("<f4").tobytes()).hexdigest(),
                    "blurred_sha256": hashlib.sha256(blurred.tobytes()).hexdigest(),
                    "staged_u8_sha256": hashlib.sha256(staged.tobytes()).hexdigest(),
                    "output_active_sha256": hashlib.sha256(active).hexdigest(),
                    "fieldgen_trace_events": len(field_trace), "blur_instructions": instructions,
                    "bytes_compared": len(expected), "mismatches": 0,
                })

    by_interp = {name: [r for r in rows if r["interpolation"] == name]
                 for name in ("constant", "linear")}
    for values in by_interp.values():
        hashes = {r["blur_mode"]: r["blurred_sha256"] for r in values}
        assert len(set(hashes.values())) == 3
    report = {
        "schema": "olmdistancegradation.classic-pf8-blur-modes45-family/1",
        "status": "exact",
        "aex_sha256": AEX_SHA256,
        "scope": "PF8 17x11 padded classic numerical chain using actual FUN_181174760, FUN_1812864d0, and FUN_181170870; Inside RGB, invert on, threshold 4, blur size 1, full resolution, background off; Constant/Linear x public Blur Modes 3/4/5",
        "semantics": {"3": "Gaussian", "4": "median with replicated border", "5": "zero-sigma bilateral; identity on this scalar fixture"},
        "alias_result": "modes 3, 4, and 5 are pairwise distinct for both interpolation inputs",
        "source_active_sha256": hashlib.sha256(source_active).hexdigest(),
        "rows": rows,
        "claims_not_made": ["public classic wrapper and host resize/staging", "other blur sizes", "other geometry or ownership/render/background branches", "PF16/PF32", "PF32 SmartRender", "AE host execution"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMDistanceGradation PF8 Blur Modes 4/5\n\n"
        "Status: **exact** for the declared bounded classic path.\n\n"
        "The actual Windows AEX's five-choice Blur Mode popup is not an alias surface. "
        "On the padded 17x11 transparent-island fixture, modes 3, 4, and 5 produce "
        "pairwise-distinct internal blurred fields and final PF8 outputs for both Constant "
        "and Linear interpolation. Mode 3 is Gaussian, mode 4 is replicated-border median, "
        "and mode 5 is the legacy zero-sigma bilateral operation. Production matches all six "
        "actual-AEX `FUN_181174760` -> `FUN_1812864d0` -> `FUN_181170870` cases "
        "byte-for-byte, including padding. The public classic wrapper and its host resize/staging "
        "remain a separate boundary.\n\n"
        "Boundary: Inside/RGB, invert on, threshold 4, Blur Size 1, full resolution, "
        "Background off, PF8, and this fixture only. PF16/PF32, other sizes/branches, "
        "PF32 SmartRender, and AE-host execution are not claimed.\n"
    )
    print("PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_BLUR_MODES45_FAMILY_EXACT")


if __name__ == "__main__":
    raise SystemExit(main())
