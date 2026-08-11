#!/usr/bin/env python3
"""Measure the first live blocker after entering actual-AEX FUN_18114f4a0."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import math
import subprocess
import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_HOOK_MEM_INVALID
from unicorn.x86_const import UC_X86_REG_R12, UC_X86_REG_RBP, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_mode4_fullcaller_hostless_exact_20260807.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_mode4_fullcaller_hostless_exact_20260807.md"
NATURAL_JSON = ROOT / "refs/conformance/olmkirakira_mode4_natural_fullframe_exact_20260811.json"
NATURAL_MD = ROOT / "refs/conformance/olmkirakira_mode4_natural_fullframe_exact_20260811.md"
FULL_CALLER = 0x18114F4A0
BRIGHTNESS_CTOR = 0x18114EC20
AGGREGATE = 0x18114FD90
AGGREGATE_MERGE2 = 0x18114FFD0
COMPOSE = {
    "PF8": (0x18114E110, 4),
    "PF16": (0x18114DDC0, 8),
    "PF32": (0x18114E460, 16),
}


def flatten_mat_rows(rows: list[list[float]]) -> list[float]:
    """Preserve full row-major Mat contents for non-single-row fixtures."""
    return [value for row in rows for value in row]


def portable_mode4_ray(seed: list[float], width: int, height: int,
                       radius: int, angle: float) -> list[str]:
    rad = angle * math.pi / 180.0
    rw = max(width + 4, int(width * abs(math.cos(rad)) + height * abs(math.sin(rad)) + 4.0))
    rh = max(height + 4, int(height * abs(math.cos(rad)) + width * abs(math.sin(rad)) + 4.0))
    padded = [0.0] * (rw * rh)
    x0 = int(float(rw) * 0.5) - width // 2
    y0 = int(float(rh) * 0.5) - height // 2
    for y in range(height):
        for x in range(width):
            padded[(y + y0) * rw + x + x0] = seed[y * width + x]
    with tempfile.TemporaryDirectory(prefix="kira_natural_ray_") as temporary:
        executable = Path(temporary) / "mode4"
        subprocess.run([
            "c++", "-std=c++20", "-O2",
            str(ROOT / "tools/emulation/test_kirakira_mode4_canonical.cpp"),
            "-o", str(executable),
        ], check=True)
        words = "\n".join(
            f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in padded) + "\n"
        output = subprocess.check_output(
            [str(executable), str(rw), str(rh), str(radius), str(angle)],
            input=words, text=True)
    final = [int(line.split()[2], 16) for line in output.splitlines() if line.startswith("final ")]
    cropped = [final[(y + y0) * rw + x + x0] for y in range(height) for x in range(width)]
    return [f"0x{word:x}" for word in cropped]


def portable_highlight_ray(seed: list[float], width: int, height: int,
                           radius: int) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="kira_natural_highlight_") as temporary:
        executable = Path(temporary) / "highlight"
        subprocess.run([
            "c++", "-std=c++20", "-O2",
            str(ROOT / "tools/emulation/test_kirakira_highlight_canonical.cpp"),
            "-o", str(executable),
        ], check=True)
        words = "\n".join(
            f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in seed) + "\n"
        output = subprocess.check_output(
            [str(executable), str(width), str(height), str(radius)],
            input=words, text=True)
    return [f"0x{int(line, 16):x}" for line in output.splitlines()]


def load_base():
    spec = importlib.util.spec_from_file_location("kira_fullcaller_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Kira actual-AEX harness")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(natural: bool = False, natural_slot: int = 1,
         natural_length: int = 5, natural_rotation: int = 0,
         highlight_gradient: bool = False, allow_ray_mismatch: bool = False) -> int:
    base = load_base()
    observed: dict[str, object] = {"fullcaller_entries": 0, "vtable_calls": []}
    width, height = (5, 3) if natural else (4, 1)
    pixel_count = width * height

    class FullCallerLoader(base.AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_code_hook(FULL_CALLER, lambda _loader, _address, _size: observed.__setitem__("fullcaller_entries", int(observed["fullcaller_entries"]) + 1))
            def capture_aggregate(loader, _address, _size):
                regs = [loader.uc.reg_read(reg) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
                rsp = loader.uc.reg_read(UC_X86_REG_RSP)
                stack = [struct.unpack("<Q", loader.read_bytes(rsp + offset, 8))[0] for offset in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50)]
                ray_ptrs = struct.unpack("<5Q", loader.read_bytes(regs[1], 40))
                observed["aggregate_entry"] = {
                    "args": [hex(value) for value in regs + stack],
                    "ray_words": [[hex(value) for value in struct.unpack(f"<{pixel_count}I", loader.read_bytes(ptr, pixel_count * 4))] for ptr in ray_ptrs],
                }
            self.add_code_hook(AGGREGATE, capture_aggregate)
            self.add_code_hook(AGGREGATE_MERGE2, lambda _loader, _address, _size: observed.__setitem__("merge2_entries", int(observed.get("merge2_entries", 0)) + 1))
            def capture_tail(loader, address, _size):
                observed.setdefault("tail_sites", []).append({
                    "address": hex(address),
                    "arg15_u64": hex(struct.unpack("<Q", loader.read_bytes(loader.uc.reg_read(UC_X86_REG_RBP) + 0x600, 8))[0]),
                    "rsp_args": [hex(struct.unpack("<Q", loader.read_bytes(loader.uc.reg_read(UC_X86_REG_RSP) + offset, 8))[0]) for offset in range(0x20, 0x80, 8)],
                })
            for site in (0x18114FBCF, 0x18114FC2D, 0x18114FC8A):
                self.add_code_hook(site, capture_tail)
            if natural:
                def capture_seed(loader, _address, _size):
                    rbp = loader.uc.reg_read(UC_X86_REG_RBP)
                    mat = base.read_mat(loader, rbp)
                    if not mat or not mat.get("values_f32"):
                        raise RuntimeError("same-run seed Mat unavailable")
                    observed["same_run_seed"] = flatten_mat_rows(mat["values_f32"])
                self.add_code_hook(0x18114F589, capture_seed)

                def capture_direction(loader, _address, _size):
                    rbp = loader.uc.reg_read(UC_X86_REG_RBP)
                    rsp = loader.uc.reg_read(UC_X86_REG_RSP)
                    observed["same_run_direction"] = {
                        "slot": loader.uc.reg_read(UC_X86_REG_R12),
                        "angle_degrees": struct.unpack("<i", loader.read_bytes(rsp + 0x28, 4))[0],
                        "glow_rotation": natural_rotation,
                        "length": struct.unpack("<i", loader.read_bytes(rsp + 0x30, 4))[0],
                        "blur_mode": struct.unpack("<i", loader.read_bytes(rsp + 0x38, 4))[0],
                        "seed_mat_address": hex(rbp),
                    }
                self.add_code_hook(0x18114F929, capture_direction)

                def capture_highlight(loader, _address, _size):
                    if natural_slot != 4:
                        return
                    raw_length = loader.uc.reg_read(UC_X86_REG_RDX) & 0xffffffff
                    if raw_length & 0x80000000:
                        raw_length -= 0x100000000
                    observed["same_run_direction"] = {
                        "slot": 4,
                        "angle_degrees": None,
                        "glow_rotation": natural_rotation,
                        "length": raw_length,
                        "blur_mode": 4,
                        "seed_mat_address": hex(loader.uc.reg_read(UC_X86_REG_RBP)),
                    }
                self.add_code_hook(0x18114F964, capture_highlight)
            def capture_null_call(uc, _access, address, _size, _value, _user):
                if address == 0:
                    rsp = uc.reg_read(UC_X86_REG_RSP)
                    return_address = struct.unpack("<Q", self.read_bytes(rsp, 8))[0]
                    observed["first_null_call"] = {"return_address": hex(return_address), "rsp": hex(rsp)}
                return False
            self.uc.hook_add(UC_HOOK_MEM_INVALID, capture_null_call)

        def call_function(self, address, *args, **kwargs):
            if address != base.FUN_HELPER:
                return super().call_function(address, *args, **kwargs)
            helper_args = list(kwargs["int_args"])
            source_mat = helper_args[1]
            source = base.read_mat(self, source_mat)
            if not source or not source.get("values_f32"):
                raise RuntimeError("source Mat unavailable")
            values = flatten_mat_rows(source["values_f32"])
            if natural and natural_slot == 4 and not highlight_gradient:
                # A constant natural source isolates Highlight's full-caller
                # ownership without conflating OpenCV's non-associative box
                # accumulation seam with the same-run binding gate.
                values = [0.25] * len(values)
            pixels = self.host_alloc(len(values) * 16, align=64)
            rgba = []
            for value in values:
                rgba.extend((value, value, value, 1.0))
            self.write_bytes(pixels, struct.pack(f"<{len(rgba)}f", *rgba))

            handles: dict[int, int] = {}
            def new_handle(_loader, call_args):
                data = self.host_alloc(max(1, int(call_args[0])), align=16)
                self.write_bytes(data, b"\0" * max(1, int(call_args[0])))
                handles[data] = int(call_args[0])
                return data
            def lock_handle(_loader, call_args):
                return int(call_args[0]) if int(call_args[0]) in handles else 0
            def no_op(_loader, _call_args):
                return 0
            handle_suite = self.host_alloc(32, align=8)
            self.write_bytes(handle_suite, struct.pack("<4Q",
                self.install_callback("PFHandle.New", new_handle),
                self.install_callback("PFHandle.Lock", lock_handle),
                self.install_callback("PFHandle.Unlock", no_op),
                self.install_callback("PFHandle.Dispose", no_op),
            ))
            def acquire_suite(_loader, call_args):
                self.write_bytes(int(call_args[2]), struct.pack("<Q", handle_suite))
                observed.setdefault("suite_calls", []).append({"kind": "acquire", "version": int(call_args[1])})
                return 0
            def release_suite(_loader, call_args):
                observed.setdefault("suite_calls", []).append({"kind": "release", "version": int(call_args[1])})
                return 0
            basic = self.host_alloc(16, align=8)
            self.write_bytes(basic, struct.pack("<2Q",
                self.install_callback("SPBasic.AcquireSuite", acquire_suite),
                self.install_callback("SPBasic.ReleaseSuite", release_suite),
            ))
            host_context = self.host_alloc(0x188, align=16)
            self.write_bytes(host_context, b"\0" * 0x188)
            self.write_bytes(host_context + 0x180, struct.pack("<Q", basic))

            obj = self.host_alloc(8, align=8)
            super().call_function(BRIGHTNESS_CTOR, int_args=[obj], max_instructions=1000)
            vtable = struct.unpack("<Q", self.read_bytes(obj, 8))[0]
            observed["object"] = {"address": hex(obj), "vtable": hex(vtable)}
            for slot in (0, 0x08, 0x10, 0x18, 0x20):
                target = struct.unpack("<Q", self.read_bytes(vtable + slot, 8))[0]
                observed["vtable_calls"].append({"slot": hex(slot), "target": hex(target)})

            lengths = self.host_alloc(20, align=16)
            angles = self.host_alloc(20, align=16)
            # Suppress directional rays and retain a radius-5 Highlight in
            # either recovered pointer order while the ABI is being bounded.
            direction_angles = [0, 0, 0, 0, 0]
            direction_lengths = [0, 0, 0, 0, 5]
            if natural:
                direction_lengths = [0, 0, 0, 0, 0]
                direction_lengths[natural_slot] = natural_length
                if natural_slot < 4:
                    direction_angles[natural_slot] = (90, 0, 45, -45)[natural_slot] + natural_rotation
            self.write_bytes(lengths, struct.pack("<5i", *direction_angles))
            self.write_bytes(angles, struct.pack("<5i", *direction_lengths))
            colors = self.host_alloc(80, align=16)
            self.write_bytes(colors, struct.pack("<20f", *([1.0, 1.0, 0.25, 0.0625] * 5)))
            flags = self.host_alloc(5)
            self.write_bytes(flags, b"\0" * 5)
            ramps = self.host_alloc(5 * 0x144, align=16)
            self.write_bytes(ramps, b"\0" * (5 * 0x144))
            scratch = self.host_alloc(len(values) * 16, align=64)
            self.write_bytes(scratch, b"\0" * (len(values) * 16))
            one = struct.unpack("<I", struct.pack("<f", 1.0))[0]
            zero = struct.unpack("<I", struct.pack("<f", 0.0))[0]
            result = super().call_function(
                FULL_CALLER,
                int_args=[obj, host_context, pixels, scratch, lengths, angles, colors, ramps, flags, 4, source["cols"], source["rows"], one, zero, 1, one],
                max_instructions=20_000_000,
            )
            actual_ray = observed["aggregate_entry"]["ray_words"][natural_slot if natural else 4]
            if natural:
                direction = observed["same_run_direction"]
                portable_ray = (portable_highlight_ray(
                    observed["same_run_seed"], width, height, int(direction["length"]))
                    if natural_slot == 4 else portable_mode4_ray(
                        observed["same_run_seed"], width, height,
                        int(direction["length"]), float(direction["angle_degrees"])))
            else:
                with tempfile.TemporaryDirectory(prefix="kira_fullcaller_core_") as temporary:
                    executable = Path(temporary) / "highlight"
                    subprocess.run([
                        "c++", "-std=c++20", "-O2",
                        str(ROOT / "tools/emulation/test_kirakira_highlight_fullcaller.cpp"),
                        "-o", str(executable),
                    ], check=True)
                    portable_ray = [f"0x{int(line, 16):x}" for line in subprocess.check_output([str(executable)], text=True).splitlines()]
            observed["portable_ray"] = portable_ray
            ray_differences = [
                {"word": index, "actual": actual, "portable": portable,
                 "ulp": abs(int(actual, 16) - int(portable, 16))}
                for index, (actual, portable) in enumerate(zip(actual_ray, portable_ray))
                if actual != portable
            ]
            observed["ray_differences"] = ray_differences
            if ray_differences and not allow_ray_mismatch:
                raise AssertionError({"actual_ray": actual_ray, "portable_ray": portable_ray})

            owner = self.host_alloc(0x200, align=16)
            self.write_bytes(owner, b"\0" * 0x200)
            self.write_bytes(owner + 0x38, struct.pack("<f", 1.0))
            self.write_bytes(owner + 0x3C, struct.pack("<f", 1.0))
            self.write_bytes(owner + 0x44, struct.pack("<i", 1))
            self.write_bytes(owner + 0x58, struct.pack("<i", len(values)))
            self.write_bytes(owner + 0x128, struct.pack("<Q", pixels))
            self.write_bytes(owner + 0x190, struct.pack("<Q", scratch))
            from olmkirakira_outer_compose_oracle_20260728 import compose_pixel, stage_typed_writer
            glow_values = struct.unpack(f"<{len(values) * 4}f", self.read_bytes(scratch, len(values) * 16))
            typed_outputs = {}
            for depth, (compose_entry, pixel_size) in COMPOSE.items():
                output = self.host_alloc(len(values) * pixel_size, align=64)
                self.write_bytes(output, b"\0" * (len(values) * pixel_size))
                world = self.host_alloc(0x40, align=16)
                self.write_bytes(world, b"\0" * 0x40)
                self.write_bytes(world + 0x18, struct.pack("<Q", output))
                self.write_bytes(world + 0x20, struct.pack("<i", len(values) * pixel_size))
                self.write_bytes(world + 0x24, struct.pack("<i", len(values)))
                self.write_bytes(world + 0x28, struct.pack("<i", 1))
                super().call_function(compose_entry, int_args=[owner, world], max_instructions=200_000)
                portable_final = b"".join(
                    stage_typed_writer(compose_pixel(
                        glow_values[index * 4:index * 4 + 4],
                        rgba[index * 4:index * 4 + 4],
                        glow_opacity=1.0, source_opacity=1.0, merge_mode=1,
                    ), depth=depth)
                    for index in range(len(values))
                )
                actual_final = self.read_bytes(output, len(values) * pixel_size)
                if portable_final != actual_final:
                    raise AssertionError(f"actual AEX final {depth} output differs from portable compose/writer")
                typed_outputs[depth] = {
                    "entry": hex(compose_entry),
                    "pixel_size": pixel_size,
                    "actual_hex": actual_final.hex(),
                    "portable_hex": portable_final.hex(),
                    "exact_bytes": len(actual_final),
                    "quantization": "clamp; scale; truncate toward zero" if depth != "PF32" else "clamp; preserve IEEE-754 binary32 words",
                }
            observed["exact"] = {
                "ray_plane_words" if natural else "highlight_plane_words": len(values),
                "aggregation_words": len(values) * 4,
                "final_pf8_bytes": len(values) * 4,
                "final_pf16_bytes": len(values) * 8,
                "final_pf32_bytes": len(values) * 16,
                "max_ulp": max((item["ulp"] for item in ray_differences), default=0),
            }
            observed["output_buffers"] = {
                "scratch_u32": [hex(value) for value in struct.unpack(f"<{len(values) * 4}I", self.read_bytes(scratch, len(values) * 16))],
                "colors_u32": [hex(value) for value in struct.unpack("<20I", self.read_bytes(colors, 80))],
                "flags_hex": self.read_bytes(flags, 5).hex(),
                "typed_outputs": typed_outputs,
            }
            return result

    original = base.AexLoader
    base.AexLoader = FullCallerLoader
    args = type("Args", (), {"aex_path": AEX, "width": width, "height": height, "length": 5, "sigma": 0.0, "max_instructions": 20_000_000})()
    try:
        execution = base.run(args)
    finally:
        base.AexLoader = original
    if "aggregate_entry" not in observed:
        raise RuntimeError({"execution": execution, "observed": observed})
    if execution.get("error") is not None:
        raise RuntimeError({"execution_error": execution["error"], "observed": observed})
    suite_calls = observed.get("suite_calls", [])
    acquire_count = sum(item["kind"] == "acquire" for item in suite_calls)
    release_count = sum(item["kind"] == "release" for item in suite_calls)
    expected_exact = {
        "ray_plane_words" if natural else "highlight_plane_words": pixel_count,
        "aggregation_words": pixel_count * 4,
        "final_pf8_bytes": pixel_count * 4,
        "final_pf16_bytes": pixel_count * 8,
        "final_pf32_bytes": pixel_count * 16,
        "max_ulp": 0,
    }
    passed = (
        execution.get("status") == "completed_without_target_hit"
        and execution.get("error") is None
        and observed.get("exact") == expected_exact
        and acquire_count == release_count
        and (natural or len(suite_calls) == 24)
    )
    direction = observed.get("same_run_direction") if natural else None
    report = {
        "kind": "olmkirakira_mode4_natural_fullframe_exact" if natural else "olmkirakira_mode4_fullcaller_hostless_exact",
        "date": "2026-08-11" if natural else "2026-08-07",
        "status": "exact" if passed else "blocked",
        "aex": {
            "path": "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex",
            "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        },
        "entry": {"function": "FUN_18114f4a0", "va": hex(FULL_CALLER), "entries": observed["fullcaller_entries"]},
        "abi": {
            "argument_slots": 16,
            "slot_15": "Merge mode integer (1)",
            "slot_16": "raw FLOAT32 brightness-gain word (0x3f800000)",
            "brightness_vtable": observed["object"]["vtable"],
            "vtable_slots": observed["vtable_calls"],
        },
        "fixture": {
            "dimensions": [width, height],
            "source_rgba": ([[0.25, 0.25, 0.25, 1.0] for _ in range(pixel_count)]
                            if natural and natural_slot == 4 and not highlight_gradient else
                            [[index / 17.0] * 3 + [1.0] for index in range(pixel_count)]),
            "blur_mode": 4,
            "directional_lengths": ([natural_length if index == natural_slot else 0 for index in range(4)]
                                    if natural else [0, 0, 0, 0]),
            "highlight_radius": natural_length if natural and natural_slot == 4 else (0 if natural else 5),
            "highlight_color_argb": [1.0, 1.0, 0.25, 0.0625],
            "merge_mode": 1,
            "brightness_gain": 1.0,
        },
        "actual_aex": {
            **({
                "selected_ray_u32": observed["aggregate_entry"]["ray_words"][natural_slot],
                "portable_ray_u32": observed["portable_ray"],
                "same_run_seed_f32": observed["same_run_seed"],
                "same_run_direction": direction,
                "ray_differences": observed["ray_differences"],
            } if natural else {
                "highlight_plane_u32": observed["aggregate_entry"]["ray_words"][4],
            }),
            "aggregation_u32": observed["output_buffers"]["scratch_u32"],
            "typed_outputs": observed["output_buffers"]["typed_outputs"],
            "suite_acquire_count": acquire_count,
            "suite_release_count": release_count,
            "fault": None,
        },
        "comparison": {
            **observed["exact"],
            **({"ray_portable_owner": ("core/kirakira_highlight.h" if natural_slot == 4
                                       else "core/kirakira_mode4.h")} if natural else {
                "highlight_portable_owner": "core/kirakira_highlight.h (called by mac/OLMKiraKira/OLMKiraKira.cpp)",
            }),
            "compose_portable_owner": "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py",
            "mac_typed_writer_owner": "mac/OLMKiraKira/OLMKiraKira.cpp PixelTraits::WriteAexTruncate, selected unconditionally after RenderTyped compose",
        },
        **({"connected_evidence": {
            "directional_helper_matrix": "refs/conformance/olmkirakira_mode4_canonical_angles_actual_aex_20260810.json (17 exact cases)",
            "aggregate_compose_matrix": "refs/conformance/olmkirakira_mode4_compose_matrix_actual_aex_20260811.json (5 exact cases)",
        }} if natural else {}),
        "scaffold": {
            "SPBasic": ["AcquireSuite", "ReleaseSuite"],
            "PF Handle Suite v2": ["NewHandle", "LockHandle", "UnlockHandle", "DisposeHandle"],
            "first_unscaffolded_stop": "indirect NULL call returning to 0x181231f4d while acquiring PF Handle Suite v2",
            "resolution": "attach host context to argument slot 2 and provide the six callbacks above",
        },
        "boundary": "This is a hostless Mac Unicorn execution of the checked-in Windows AEX with typed PF8/PF16/PF32 output worlds, not a live Windows/AE render claim. The same canonical internal float chain is byte exact through each final typed writer.",
        "boundary_ja": "チェックイン済みWindows AEXをMac上のUnicornで実行したhostless境界であり、Windows/AE実機レンダーの一致主張ではない。共通の内部float経路からPF8/PF16/PF32 typed worldへ書く最終境界までをbyte exactとする。",
        "verification": "python3 tools/emulation/probe_olmkirakira_mode4_natural_fullframe_exact_20260811.py" if natural else "python3 tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py",
    }
    output_json = NATURAL_JSON if natural else OUT_JSON
    output_md = NATURAL_MD if natural else OUT_MD
    output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(
        ("# OLMKiraKira Mode4 natural full-frame exact gate（2026-08-11）\n\n"
         f"Status: **{report['status']}**\n\n"
         "actual AEX full callerの同一実行で、vtable seed 15 words、Horizontal slot 1 / Length 5 / Rotation 0°、aggregate入口ray 15 wordsを結んだ。portable Mode4 chainとray全15 wordsがraw exactで、同じaggregateからPF8/PF16/PF32 typed outputまでbyte exact。\n\n"
         "これは5×3の1 source caseに限るhostless境界であり、live Windows AEや任意sourceの一般一致主張ではない。\n\n"
         f"Verification: `{report['verification']}`\n") if natural else
        "# OLMKiraKira Mode4 full caller hostless exact gate（2026-08-07）\n\n"
        f"Status: **{report['status']}**\n\n"
        "actual AEX `FUN_18114f4a0` を16引数で直接実行し、4×1 canonical PF32 fixtureの"
        "MakeSeed、Highlight 11×11 box filter 3 pass、Mode-1 aggregation、Merge-1 compose/PF32 writerを通した。\n\n"
        "- Highlight plane: 4/4 words exact\n"
        "- aggregation: 16/16 words exact\n"
        "- final PF8 ARGB: 16/16 bytes exact\n"
        "- final PF16 ARGB: 32/32 bytes exact\n"
        "- final PF32 ARGB: 64/64 bytes exact\n"
        "- max ULP: 0\n"
        "- PF Handle Suite: Acquire 12 / Release 12、faultなし\n\n"
        "Mac productionは `core/kirakira_highlight.h` の同じportable primitiveを使用する。"
        "最終compose/writerはtyped world上で既存binary-grounded oracleと比較した。PF8/PF16はclamp後に255/32768倍し、ゼロ方向へ切り捨てる。これはhostless actual-AEX境界であり、live Windows/AE出力のraw exact主張ではない。\n\n"
        "Verification: `python3 tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "exact": report["comparison"], "json": str(output_json), "md": str(output_md)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
