from __future__ import annotations

import json
import math
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
REF_DIR = REPO_ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
MANIFEST = REF_DIR / "reference_manifest.json"
INPUT_PNG = REF_DIR / "case_0010_before_effects.png"

FUN_1800024C0 = 0x1800024C0
FUN_180002780 = 0x180002780
FUN_180001000 = 0x180001000
FUN_180001B10 = 0x180001B10
FUN_180004640 = 0x180004640
FUN_180007520 = 0x180007520
FUN_180008690 = 0x180008690
FUN_18000DE60 = 0x18000DE60
FUN_18000E190 = 0x18000E190
FUN_18000E270 = 0x18000E270
FUN_18000E430 = 0x18000E430
FUN_18000E5F0 = 0x18000E5F0
FUN_18000E6D0 = 0x18000E6D0
FUN_18000E7B0 = 0x18000E7B0

WINDOWS_TYPED = {
    (844, 1603): 0xBC70F44B,
    (845, 1603): 0xBD46D045,
    (843, 1601): 0x3DD69702,
    (843, 1602): 0x3DE119CE,
}
EXTRA_DUMP_CELLS = [
    (844, 1604),
    (845, 1604),
]
ALPHA_BITS = 0x3F800000
BRIGHT_WITNESS_SOURCES = [(1669, 81), (1684, 105)]


def u32(loader: AexLoader, addr: int) -> int:
    return struct.unpack("<I", loader.read_bytes(addr, 4))[0]


def u64(loader: AexLoader, addr: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(addr, 8))[0]


def f32_from_bits(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def ulp_distance_u32(a: int, b: int) -> int:
    return abs((a & 0xFFFFFFFF) - (b & 0xFFFFFFFF))


def load_case0010_params() -> dict:
    data = json.load(open(MANIFEST))
    for case in data["cases"]:
        if case["id"] != "case_0010":
            continue
        params = case["effects"][0]["params"]
        return {
            "Blur Type": params[0]["value"],
            "Center": tuple(params[1]["value"]),
            "Outer Strength": params[3]["value"],
            "Outer Offset Mode": params[4]["value"],
            "Outer Offset": params[5]["value"],
            "Outer Edge Fade": params[6]["value"],
            "Inner Strength": params[9]["value"],
            "Inner Offset Mode": params[10]["value"],
            "Inner Offset": params[11]["value"],
            "Inner Edge Fade": params[12]["value"],
            "Repeat Border": params[14]["value"],
            "Ratio": params[16]["value"],
            "Angle": params[17]["value"],
            "Quality": params[19]["value"],
            "Brightness Gain": params[20]["value"],
            "Size Variation": params[21]["value"],
            "Noise Variation": params[23]["value"],
            "Noise Type": params[24]["value"],
            "Seed": params[26]["value"],
            "Noise Offset": params[27]["value"],
            "Thickness": params[28]["value"],
            "GPU Rendering": params[30]["value"],
        }
    raise RuntimeError("case_0010 not found")


def reader_values(params: dict) -> dict:
    return {
        "e5f0": {
            0x01: int(params["Blur Type"]),
            0x1C: int(params["Outer Offset Mode"]),
            0x1E: int(params["Inner Offset Mode"]),
            0x14: int(params["Noise Type"]),
        },
        "de60": {
            0x02: (float(params["Center"][0]), float(params["Center"][1])),
        },
        "e270": {
            0x04: int(params["Outer Strength"]),
            0x05: int(params["Outer Edge Fade"]),
            0x08: int(params["Inner Strength"]),
            0x09: int(params["Inner Edge Fade"]),
            0x1D: int(params["Outer Offset"]),
            0x1F: int(params["Inner Offset"]),
            0x16: int(params["Seed"]),
        },
        "e190": {
            0x1A: int(params["Repeat Border"]),
        },
        "e430": {
            0x0C: float(params["Ratio"]),
            0x0F: float(params["Quality"]),
            0x10: float(params["Brightness Gain"]),
            0x11: float(params["Size Variation"]),
            0x13: float(params["Noise Variation"]),
            0x18: float(params["Thickness"]),
        },
        "e6d0": {
            0x0D: int(params["Angle"]),
        },
        "e7b0": {
            0x17: float(params["Noise Offset"]),
        },
    }


def build_host_suites(loader: AexLoader) -> int:
    def h_new(ld, args):
        size = args[0] & 0xFFFFFFFFFFFFFFFF
        data = ld.bump_alloc(max(size, 1), align=64)
        ld.write_bytes(data, b"\x00" * max(size, 1))
        handle = ld.host_alloc(8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def h_lock(ld, args):
        return u64(ld, args[0]) if args[0] else 0

    def h_noop(ld, args):
        return 0

    handle_suite = loader.host_alloc(0x20)
    cbs = [
        loader.install_callback("PFHandle.new", h_new),
        loader.install_callback("PFHandle.lock", h_lock),
        loader.install_callback("PFHandle.unlock", h_noop),
        loader.install_callback("PFHandle.dispose", h_noop),
    ]
    loader.write_bytes(handle_suite, struct.pack("<4Q", *cbs))

    def sp_acquire(ld, args):
        out_ptr = args[2]
        ld.write_bytes(out_ptr, struct.pack("<Q", handle_suite))
        return 0

    spbasic = loader.host_alloc(0x10)
    spbasic_cbs = [
        loader.install_callback("SPBasic.AcquireSuite", sp_acquire),
        loader.install_callback("SPBasic.ReleaseSuite", h_noop),
    ]
    loader.write_bytes(spbasic, struct.pack("<2Q", *spbasic_cbs))
    return spbasic


def build_render_context(loader: AexLoader, spbasic: int) -> int:
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\x00" * 0x200)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", spbasic))
    loader.write_bytes(ctx + 0x11C, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x120, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x124, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x128, struct.pack("<I", 1))

    dispatch = loader.host_alloc(0x80)
    loader.write_bytes(dispatch, b"\x00" * 0x80)

    def suite_40(ld, args):
        return 0

    loader.write_bytes(
        dispatch + 0x40,
        struct.pack("<Q", loader.install_callback("RenderCtx.suite40", suite_40)),
    )
    loader.write_bytes(ctx + 0xB0, struct.pack("<Q", dispatch))
    loader.write_bytes(ctx + 0xB8, struct.pack("<Q", loader.host_alloc(8)))
    return ctx


def build_world(loader: AexLoader, width: int, height: int, rgba_bytes: bytes) -> int:
    data = loader.bump_alloc(len(rgba_bytes), align=64)
    loader.write_bytes(data, rgba_bytes)
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, b"\x00" * 0x80)
    rowbytes = width * 4
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", rowbytes))
    loader.write_bytes(world + 0x24, struct.pack("<I", width))
    loader.write_bytes(world + 0x28, struct.pack("<I", height))
    loader.write_bytes(world + 0x2C, struct.pack("<H", 8))
    loader.write_bytes(world + 0x68, struct.pack("<I", 0))
    loader.write_bytes(world + 0x6C, struct.pack("<I", 0))
    return world


def read_world_pixel_argb(loader: AexLoader, world: int, x: int, y: int) -> tuple[int, int, int, int]:
    data = u64(loader, world + 0x18)
    rowbytes = u32(loader, world + 0x20)
    return tuple(loader.read_bytes(data + y * rowbytes + x * 4, 4))


def call_inverse_coords(loader: AexLoader, work_param1: int, x: float, y: float) -> tuple[float, float]:
    radius_out = loader.bump_alloc(4, align=16)
    angle_out = loader.bump_alloc(4, align=16)
    loader.write_bytes(radius_out, b"\x00" * 4)
    loader.write_bytes(angle_out, b"\x00" * 4)
    loader.call_function(
        FUN_180001B10,
        int_args=[work_param1, 0, 0, radius_out, angle_out],
        float_args={1: x, 2: y},
        max_instructions=10_000,
    )
    radius = struct.unpack("<f", loader.read_bytes(radius_out, 4))[0]
    angle = struct.unpack("<f", loader.read_bytes(angle_out, 4))[0]
    return radius, angle


def call_polar_resampler(
    loader: AexLoader,
    plane_ptr: int,
    angular_cols: int,
    sample_x: float,
    sample_y: float,
) -> tuple[float, float, float, float]:
    out_addr = loader.bump_alloc(16, align=16)
    loader.write_bytes(out_addr, b"\x00" * 16)
    stack_x_bits = struct.unpack("<I", struct.pack("<f", sample_x))[0]
    stack_y_bits = struct.unpack("<I", struct.pack("<f", sample_y))[0]
    loader.call_function(
        FUN_180001000,
        int_args=[plane_ptr, out_addr, angular_cols, angular_cols * 4, stack_x_bits, stack_y_bits],
        max_instructions=20_000,
    )
    return struct.unpack("<4f", loader.read_bytes(out_addr, 16))


def install_reader_detours(loader: AexLoader, params: dict) -> list[tuple]:
    values = reader_values(params)
    provenance = []

    def push_log(name: str, idx: int, value, out_ptrs):
        provenance.append((name, idx, value, tuple(out_ptrs)))
        return 0

    def make_i32_reader(name: str, table: dict[int, int]):
        def handler(ld: AexLoader, args):
            idx, out_ptr = args[2], args[3]
            value = table[idx]
            ld.write_bytes(out_ptr, struct.pack("<i", value))
            return push_log(name, idx, value, [out_ptr])
        return handler

    def bool_reader(ld: AexLoader, args):
        idx, out_ptr = args[2], args[3]
        value = values["e190"][idx]
        ld.write_bytes(out_ptr, bytes([1 if value else 0]))
        return push_log("e190", idx, value, [out_ptr])

    def f32_reader(name: str, table: dict[int, float]):
        def handler(ld: AexLoader, args):
            idx, out_ptr = args[2], args[3]
            value = float(table[idx])
            ld.write_bytes(out_ptr, struct.pack("<f", value))
            return push_log(name, idx, value, [out_ptr])
        return handler

    def point_reader(ld: AexLoader, args):
        idx, out_x = args[2], args[3]
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        out_y = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        x, y = values["de60"][idx]
        ld.write_bytes(out_x, struct.pack("<d", x))
        ld.write_bytes(out_y, struct.pack("<d", y))
        return push_log("de60", idx, (x, y), [out_x, out_y])

    loader.detour_function(FUN_18000E5F0, "reader.e5f0", make_i32_reader("e5f0", values["e5f0"]))
    loader.detour_function(FUN_18000DE60, "reader.de60", point_reader)
    loader.detour_function(FUN_18000E270, "reader.e270", make_i32_reader("e270", values["e270"]))
    loader.detour_function(FUN_18000E190, "reader.e190", bool_reader)
    loader.detour_function(FUN_18000E430, "reader.e430", f32_reader("e430", values["e430"]))
    loader.detour_function(FUN_18000E6D0, "reader.e6d0", make_i32_reader("e6d0", values["e6d0"]))
    loader.detour_function(FUN_18000E7B0, "reader.e7b0", f32_reader("e7b0", values["e7b0"]))
    return provenance


def build_param_block(loader: AexLoader, size: int = 0x140) -> int:
    addr = loader.host_alloc(size, align=64)
    loader.write_bytes(addr, b"\x00" * size)
    return addr


def read_param_ctx(loader: AexLoader, ctx_addr: int) -> dict:
    return {
        "blur_type": u32(loader, ctx_addr + 0x20),
        "center_x": struct.unpack("<d", loader.read_bytes(ctx_addr + 0x28, 8))[0],
        "center_y": struct.unpack("<d", loader.read_bytes(ctx_addr + 0x30, 8))[0],
        "brightness_gain": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x38, 4))[0],
        "noise_variation_scaled": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x3C, 4))[0],
        "size_variation_scaled": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x40, 4))[0],
        "alpha_bool": loader.read_bytes(ctx_addr + 0x44, 1)[0],
        "noise_type": u32(loader, ctx_addr + 0x50),
        "outer_offset_mode": u32(loader, ctx_addr + 0x54),
        "outer_offset": u32(loader, ctx_addr + 0x58),
        "inner_offset_mode": u32(loader, ctx_addr + 0x5C),
        "inner_offset": u32(loader, ctx_addr + 0x60),
        "outer_strength": u32(loader, ctx_addr + 0x64),
        "inner_strength": u32(loader, ctx_addr + 0x68),
        "outer_edge_fade": u32(loader, ctx_addr + 0x6C),
        "inner_edge_fade": u32(loader, ctx_addr + 0x70),
        "repeat_border": loader.read_bytes(ctx_addr + 0x74, 1)[0],
        "ratio": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x78, 4))[0],
        "angle_radians_int": u32(loader, ctx_addr + 0x7C),
        "quality_recip": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x80, 4))[0],
        "seed": u32(loader, ctx_addr + 0xFC),
        "noise_offset": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x100, 4))[0],
        "thickness": struct.unpack("<f", loader.read_bytes(ctx_addr + 0x104, 4))[0],
    }


def read_input_pixel_rgba(loader: AexLoader, unpacked_ptr: int, width: int, x: int, y: int) -> tuple[float, float, float, float]:
    base = unpacked_ptr + ((y * width + x) * 4 * 4)
    return struct.unpack("<4f", loader.read_bytes(base, 16))


def read_polar_cell_rgba_bits(loader: AexLoader, plane_ptr: int, cols: int, row: int, col: int) -> tuple[int, int, int, int]:
    cell_index = row * cols + col
    base = plane_ptr + cell_index * 16
    return struct.unpack("<4I", loader.read_bytes(base, 16))


def read_polar_cell_rgba_floats(loader: AexLoader, plane_ptr: int, cols: int, row: int, col: int) -> tuple[float, float, float, float]:
    cell_index = row * cols + col
    base = plane_ptr + cell_index * 16
    return struct.unpack("<4f", loader.read_bytes(base, 16))


def diagnose_stage(param_ctx: dict, captured_param1: int, loader: AexLoader, ctx_addr: int, width: int) -> str:
    if not math.isclose(param_ctx["quality_recip"], 0.2, rel_tol=0.0, abs_tol=1e-7):
        return "reader mock / FUN_180008690"
    if captured_param1:
        p0 = struct.unpack("<f", loader.read_bytes(captured_param1, 4))[0]
        if not math.isclose(p0, 0.2, rel_tol=0.0, abs_tol=1e-7):
            return "FUN_180001ac0 / pre-FUN_180004640 setup"
    unpacked_ptr = u64(loader, ctx_addr + 0x98)
    if unpacked_ptr:
        exp = tuple(v / 255.0 for v in (158, 158, 158, 255))
        got = read_input_pixel_rgba(loader, unpacked_ptr, width, BRIGHT_WITNESS_SOURCES[0][0], BRIGHT_WITNESS_SOURCES[0][1])
        if max(abs(a - b) for a, b in zip(got, exp)) > 1e-5:
            return "FUN_180007520 source-world unpack"
    return "FUN_180004640 / downstream scatter-gather"


def write_report(report_text: str) -> None:
    (Path(__file__).parent / "M4_REPORT.md").write_text(report_text)


def main() -> int:
    params = load_case0010_params()
    from PIL import Image

    image = Image.open(INPUT_PNG).convert("RGBA")
    width, height = image.size
    # After Effects PF_Pixel is ARGB (alpha-first) in memory, not RGBA. PIL's
    # tobytes() is RGBA, so feeding it directly makes FUN_180007520's unpack
    # read alpha into blue and blue into alpha (observed [x,x,y,y] vs Windows
    # [z,z,z,1.0]). Repack channels to A,R,G,B before building the world.
    r, g, b, a = image.split()
    input_bytes = Image.merge("RGBA", (a, r, g, b)).tobytes()
    output_bytes = bytes(width * height * 4)

    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = build_host_suites(loader)
    render_ctx = build_render_context(loader, spbasic)
    input_world = build_world(loader, width, height, input_bytes)
    output_world = build_world(loader, width, height, output_bytes)
    param_ctx = build_param_block(loader)
    provenance = install_reader_detours(loader, params)

    captured = {
        "rotation_param1": 0,
        "rotation_param2": 0,
        "scatter_calls": [],
        "max_calls": [],
    }

    def capture_rotation(ld: AexLoader, address: int, size: int) -> None:
        captured["rotation_param1"] = ld.uc.reg_read(UC_X86_REG_RCX)
        captured["rotation_param2"] = ld.uc.reg_read(UC_X86_REG_RDX)

    def capture_scatter(ld: AexLoader, address: int, size: int) -> None:
        args = [ld.uc.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        stack5 = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        captured["scatter_calls"].append((address, args, stack5))

    loader.add_code_hook(FUN_180004640, capture_rotation)
    loader.add_code_hook(FUN_180002780, capture_scatter)
    loader.add_code_hook(FUN_1800024C0, capture_scatter)

    t0 = time.time()
    loader.call_function(FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    param_ctx_dump = read_param_ctx(loader, param_ctx)
    loader.call_function(
        FUN_180007520,
        int_args=[render_ctx, 0, input_world, output_world, param_ctx],
        max_instructions=1_500_000_000,
    )
    elapsed = time.time() - t0

    if not captured["rotation_param1"]:
        raise RuntimeError("FUN_180004640 entry was not observed")

    work_param1 = captured["rotation_param1"]
    f250_ptr = u64(loader, work_param1 + 0xF250 * 4)
    f252_ptr = u64(loader, work_param1 + 0xF252 * 4)
    e0e_ptr = u64(loader, work_param1 + 0xE * 4)
    quality_recip = struct.unpack("<f", loader.read_bytes(work_param1, 4))[0]
    angular_cols = int(round(360.0 / quality_recip)) if quality_recip else 0

    results = []
    extra_cells = []
    all_match = True
    stage = diagnose_stage(param_ctx_dump, work_param1, loader, param_ctx, width)
    for (row, col), target in WINDOWS_TYPED.items():
        normalized_bits = read_polar_cell_rgba_bits(loader, e0e_ptr, angular_cols, row, col)
        accumulator = read_polar_cell_rgba_floats(loader, f250_ptr, angular_cols, row, col)
        f252_raw = read_polar_cell_rgba_floats(loader, f252_ptr, angular_cols, row, col)
        accumulator_weight = accumulator[3]
        normalized_from_acc = tuple(
            accumulator[i] / accumulator_weight if accumulator_weight else float("nan")
            for i in range(4)
        )
        rgb_ulps = tuple(ulp_distance_u32(bits, target) for bits in normalized_bits[:3])
        alpha_ulp = ulp_distance_u32(normalized_bits[3], ALPHA_BITS)
        match = rgb_ulps == (0, 0, 0) and alpha_ulp == 0
        all_match = all_match and match
        results.append({
            "row": row,
            "col": col,
            "target": target,
            "normalized_bits": normalized_bits,
            "accumulator": accumulator,
            "f252_raw": f252_raw,
            "normalized_from_acc": normalized_from_acc,
            "rgb_ulps": rgb_ulps,
            "alpha_ulp": alpha_ulp,
            "match": match,
            "stage": None if match else stage,
        })
    for row, col in EXTRA_DUMP_CELLS:
        extra_cells.append({
            "row": row,
            "col": col,
            "normalized_bits": read_polar_cell_rgba_bits(loader, e0e_ptr, angular_cols, row, col),
            "accumulator": read_polar_cell_rgba_floats(loader, f250_ptr, angular_cols, row, col),
        })

    unpacked_ptr = u64(loader, param_ctx + 0x98)
    witness_unpack = {
        "1669,81": read_input_pixel_rgba(loader, unpacked_ptr, width, 1669, 81),
        "1684,105": read_input_pixel_rgba(loader, unpacked_ptr, width, 1684, 105),
    }
    witness_output_argb = read_world_pixel_argb(loader, output_world, 1614, 6)
    witness_output_rgba = (
        witness_output_argb[1],
        witness_output_argb[2],
        witness_output_argb[3],
        witness_output_argb[0],
    )
    witness_radius, witness_angle = call_inverse_coords(loader, work_param1, 1614.0, 6.0)
    angle_scale = struct.unpack("<f", loader.read_bytes(work_param1 + 0x8, 4))[0]
    radius_base = struct.unpack("<i", loader.read_bytes(work_param1 + 0xC, 4))[0]
    sample_x = witness_angle * angle_scale
    if float(angular_cols) <= sample_x:
        sample_x -= float(angular_cols)
    sample_y = witness_radius - float(radius_base)
    direct_sample = call_polar_resampler(loader, e0e_ptr, angular_cols, sample_x, sample_y)
    direct_sample_u8 = tuple(
        max(0, min(255, int(round(channel * 255.0)))) for channel in direct_sample
    )

    report_lines = []
    report_lines.append("## M4到達点")
    report_lines.append(f"- `FUN_180008690 -> FUN_180007520 -> FUN_180004640` を case_0010 実入力 `{width}x{height}` で emulation 実行した。")
    report_lines.append(f"- 実行モードは `fast=True`。壁時計は {elapsed:.2f}s。")
    report_lines.append(f"- reader provenance は {len(provenance)} call を捕捉し、`param_2` は実バイナリの `FUN_180008690` 本体に構築させた。")
    report_lines.append(f"- `FUN_180004640` 入口の実引数は `param_1=0x{work_param1:x}`, `param_2=0x{captured['rotation_param2']:x}`。")
    report_lines.append(f"- `param_1[0]` = {quality_recip:.9f} -> `iVar29={angular_cols}`。")
    report_lines.append(f"- witness buffers: `f250=0x{f250_ptr:x}`, `f252=0x{f252_ptr:x}`, `+0xe=0x{e0e_ptr:x}`。")
    report_lines.append(f"- output witness `(1614,6)` ARGB bytes `{witness_output_argb}`, RGBA `{witness_output_rgba}`。")
    report_lines.append(
        "- direct inverse sample `(1614,6)`: "
        f"radius={witness_radius:.9f}, angle={witness_angle:.9f}, "
        f"angle_scale={angle_scale:.9f}, radius_base={radius_base}, "
        f"sample=({sample_x:.9f}, {sample_y:.9f}), "
        f"`+0xe` RGBA float={tuple(round(v, 9) for v in direct_sample)}, "
        f"u8={direct_sample_u8}."
    )
    report_lines.append("")
    report_lines.append("## ビット照合結果")
    exact_count = sum(1 for item in results if item["match"])
    one_ulp_count = sum(
        1
        for item in results
        if max(item["rgb_ulps"]) <= 1 and item["alpha_ulp"] == 0
    )
    report_lines.append(
        f"- Summary: exact `{exact_count}/4`, <=1 ULP RGB with alpha exact `{one_ulp_count}/4`."
    )
    for item in results:
        rgba = " ".join(f"{v:08x}" for v in item["normalized_bits"])
        acc = tuple(round(v, 9) for v in item["accumulator"])
        f252_raw = tuple(round(v, 9) for v in item["f252_raw"])
        acc_norm = tuple(round(v, 9) for v in item["normalized_from_acc"])
        ulps = f"rgb_ulps={item['rgb_ulps']}, alpha_ulp={item['alpha_ulp']}"
        if item["match"]:
            report_lines.append(
                f"- row{item['row']} col{item['col']}: 一致 "
                f"(+0xe RGBA bits `{rgba}`; RGB=`{item['target']:08x}`, A=`{ALPHA_BITS:08x}`; "
                f"f250={acc}, f250.rgb/f250.a={acc_norm}, f252_raw={f252_raw}, {ulps})"
            )
        else:
            report_lines.append(
                f"- row{item['row']} col{item['col']}: 乖離 "
                f"(+0xe got `{rgba}` vs win RGB=`{item['target']:08x}` A=`{ALPHA_BITS:08x}`; "
                f"f250={acc}, f250.rgb/f250.a={acc_norm}, f252_raw={f252_raw}, {ulps}; "
                f"乖離開始段: {item['stage']})"
            )
    report_lines.append("")
    report_lines.append("## Extra +0xe Dump Cells")
    for item in extra_cells:
        rgba = " ".join(f"{v:08x}" for v in item["normalized_bits"])
        acc = tuple(round(v, 9) for v in item["accumulator"])
        report_lines.append(f"- row{item['row']} col{item['col']}: +0xe bits `{rgba}`, f250={acc}")
    report_lines.append("")
    report_lines.append("## promotion 機序")
    if all_match or one_ulp_count == len(results):
        scatter_desc = ", ".join(
            f"`0x{addr:x}` rcx=0x{args[0]:x} rdx=0x{args[1]:x} r8=0x{args[2]:x} r9=0x{args[3]:x} stack5=0x{stack5:x}"
            for addr, args, stack5 in captured["scatter_calls"][:4]
        )
        if all_match:
            report_lines.append(f"- ビット一致ゲートは通過した。scatter entry 観測: {scatter_desc}")
        else:
            report_lines.append(f"- Windows typed cells とローカル emulation は全セル <=1 ULP まで一致した。scatter entry 観測: {scatter_desc}")
            report_lines.append("- 残る 1 ULP は libm / FMA / fast-math 系の丸め差候補で、promotion 機序の判定には十分な ground truth として扱える。")
        report_lines.append("- ただし本 run では `FUN_180002780 / FUN_1800024c0` 内の witness-angle promotion 条件分岐までは未分解で、bright lobe が col1604 へ届く具体条件の確定には追加の段階 dump が残る。")
    else:
        report_lines.append("- ビット一致ゲート未達。`FUN_180002780 / FUN_1800024c0` の promotion 条件確定は保留。")
    report_lines.append("")
    report_lines.append("## Mac 港への含意")
    if direct_sample_u8[:3] == (0, 0, 0):
        report_lines.append("- AEX の座標変換と `+0xe` direct sampler は witness `(1614,6)` を黒として返す。これは 20260604 PNG 参照の白とは一致しない。")
        report_lines.append("- よって、この witness だけを根拠に Mac 側 scatter を白へ寄せる変更は危険。まず Windows PNG が CPU AEX Software 経路そのものか、またはGPU/旧AEX/manifest混入かを分離する必要がある。")
    elif all_match or one_ulp_count == len(results):
        report_lines.append("- emulation が Windows typed cells と同値で direct sampler も参照方向に出るなら、Mac 港の欠落は scatter 段の `FUN_180002780 / FUN_1800024c0` にある。次段は witness-angle 近傍角への配布条件をそのまま移植すること。")
    else:
        report_lines.append(f"- 現時点の乖離開始段は `{stage}`。Mac 港の scatter 欠落を断定する前に、この段の値を Windows trace target に揃える必要がある。")
        report_lines.append(f"- 参考 dump: `FUN_180007520` unpack 後の bright source px 1669,81 -> {tuple(round(v, 6) for v in witness_unpack['1669,81'])}, 1684,105 -> {tuple(round(v, 6) for v in witness_unpack['1684,105'])}。")
    report_lines.append("")
    report_lines.append("## 残課題")
    if direct_sample_u8[:3] == (0, 0, 0):
        report_lines.append("- case_0010 witness `(1614,6)` は `reference-path-split suspected` として扱う。PNG白へ合わせ込む前に、同一AEX/Software/EXRまたはCPU writeback witnessで参照経路を確定する。")
        report_lines.append("- 追加解析する場合は、`FUN_180001b10 -> FUN_180001000(+0xe)` の direct sample 黒を起点に、PNG参照生成時のAEXバージョン/レンダー経路/入力manifestを監査する。")
    elif all_match or one_ulp_count == len(results):
        report_lines.append("- `FUN_180002780 / FUN_1800024c0` の loop-level dump を追加し、radius-844 bright lobe が witness angle col1604 へ入る具体的条件分岐を固定する。")
        report_lines.append("- Windows trace 上の source px 1669,81 / 1684,105 と scatter 寄与セルの対応を、cell-level accumulator dump で一本化する。")
    else:
        report_lines.append("- reader provenance 20 call のうち各 index の raw value と `FUN_180008690` 後変換値を Windows 側期待と照合する追加 ground truth が要る。")
        report_lines.append("- `FUN_180004640` 直前 `param_1` と `FUN_180007520` unpack buffer の typed dump を増やし、reader/transform/unpack/rotation のどこで first mismatch が出るかをさらに細分化する。")

    report = "\n".join(report_lines) + "\n"
    write_report(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
