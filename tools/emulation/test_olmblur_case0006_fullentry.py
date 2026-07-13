"""Actual-AEX OLMBlur 16bpc Non-Legacy case_0006 worker probe.

The 1920x1080 worker staging and writer execute normally.  Helper calls are
restricted to the backwards dependency cone of the two requested witnesses:
the real AEX helper still executes every row/column that can influence either
witness, while irrelevant six-way chunks receive passes=0 and return through
their normal ABI.  This makes a typed full-worker witness practical without
turning a PNG crop into execution evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDI,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "plugins_2025" / "OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MANIFEST = REPO_ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
BASE = MANIFEST.parent
CASE_ID = "olmblur__case_0006"
WITNESSES = ((314, 14), (29, 71))
WIDTH, HEIGHT = 1920, 1080
FUN_ENTRY = 0x180002280
FUN_HORIZONTAL = 0x180001000
FUN_VERTICAL = 0x180001980
STAGING_DONE = 0x1800028DB
WRITER_PRE = 0x1800030E2
WRITER_POST = 0x180003123
HORIZONTAL_RETURNS = (
    0x1800029F5, 0x180002A27, 0x180002A5C, 0x180002A91,
    0x180002AC6, 0x180002AFA,
)
VERTICAL_RETURNS = (
    0x180002B30, 0x180002B62, 0x180002B97, 0x180002BCC,
    0x180002C01, 0x180002C35,
)
REPORT_JSON = REPO_ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json"
REPORT_MD = REPO_ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.md"
PORTABLE_SOURCE = Path(__file__).with_name("probe_olmblur_case0006_portable.cpp")


def png_rgba16(path: Path) -> tuple[int, int, bytes]:
    blob = path.read_bytes()
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    pos = 8
    width = height = None
    compressed = bytearray()
    while pos < len(blob):
        size = struct.unpack(">I", blob[pos:pos + 4])[0]
        kind = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + size]
        pos += size + 12
        if kind == b"IHDR":
            width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", data)
            if (depth, color, comp, filt, interlace) != (16, 6, 0, 0, 0):
                raise ValueError("probe requires non-interlaced RGBA16 PNG")
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("missing PNG IHDR")
    stride = width * 8
    raw = zlib.decompress(compressed)
    rows: list[bytes] = []
    previous = bytearray(stride)
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        encoded = raw[cursor + 1:cursor + 1 + stride]
        cursor += stride + 1
        recon = bytearray(stride)
        for i, value in enumerate(encoded):
            left = recon[i - 8] if i >= 8 else 0
            up = previous[i]
            up_left = previous[i - 8] if i >= 8 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                estimate = left + up - up_left
                pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
            else:
                raise ValueError(f"unsupported PNG filter {filter_type}")
            recon[i] = (value + predictor) & 0xFF
        rows.append(bytes(recon))
        previous = recon
    return width, height, b"".join(rows)


def guest_argb_words(rgba: bytes) -> bytes:
    out = bytearray(len(rgba))
    for off in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, off)
        struct.pack_into("<4H", out, off, a, r, g, b)
    return bytes(out)


def f32_record(loader: AexLoader, address: int) -> dict:
    raw = loader.read_bytes(address, 12)
    values = struct.unpack("<3f", raw)
    bits = struct.unpack("<3I", raw)
    return {"values": list(values), "bits_hex": [f"0x{value:08x}" for value in bits]}


def point_plane(loader: AexLoader, plane: int, x: int, y: int) -> dict:
    return f32_record(loader, plane + (y * WIDTH + x) * 12)


def i32(loader: AexLoader, address: int) -> int:
    return struct.unpack("<i", loader.read_bytes(address, 4))[0]


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


RADII = (5, 4, 4, 4, 3, 3, 3, 3, 3, 3)


def interval_for(direction: str, iteration: int, witnesses: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    # The output interval for each stage includes the exact reach of every
    # later pass on the opposite axis.  RADII is independently emitted by the
    # current portable worker trace and checked against each AEX helper call.
    if direction == "horizontal":
        reach = sum(RADII[iteration:])
        lo = min(y for _, y in witnesses) - reach
        hi = max(y for _, y in witnesses) + reach + 1
        return max(0, lo), min(HEIGHT, hi)
    reach = sum(RADII[iteration + 1:])
    lo = min(x for x, _ in witnesses) - reach
    hi = max(x for x, _ in witnesses) + reach + 1
    return max(0, lo), min(WIDTH, hi)


def intersect(offset: int, passes: int, wanted: tuple[int, int]) -> tuple[int, int]:
    lo = max(offset, wanted[0])
    hi = min(offset + passes, wanted[1])
    return lo, max(0, hi - lo)


def compile_and_run_portable(source_argb: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="olmblur_case0006_") as temp:
        temp_path = Path(temp)
        source_path = temp_path / "source_argb16.bin"
        executable = temp_path / "portable_probe"
        source_path.write_bytes(source_argb)
        command = [
            os.environ.get("CXX", "c++"), "-std=c++17", "-O2", "-ffp-contract=off",
            str(PORTABLE_SOURCE),
            str(REPO_ROOT / "core/olmblur_helper.cpp"),
            str(REPO_ROOT / "core/olmblur_worker16_nonlegacy.cpp"),
            "-o", str(executable),
        ]
        build = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            raise RuntimeError(f"portable helper compile failed: {build.stderr.strip()}")
        run = subprocess.run([str(executable), str(source_path)], text=True, capture_output=True, check=False)
        if run.returncode:
            raise RuntimeError(f"portable helper failed: {run.stderr.strip()}\n{run.stdout}")
    result: dict = {"staging": {}, "stages": [], "final": {}, "self_check": False}
    for line in run.stdout.splitlines():
        fields = line.split("\t")
        if fields[0] in ("STAGING", "STAGE"):
            record, iteration, direction, radius, x, y, *bits = fields
            point = f"({x},{y})"
            value = {"bits_hex": [f"0x{int(bit):08x}" for bit in bits]}
            if record == "STAGING":
                result["staging"][point] = value
            else:
                key = (int(iteration), direction, int(radius))
                if not result["stages"] or result["stages"][-1]["key"] != key:
                    result["stages"].append({"key": key, "points": {}})
                result["stages"][-1]["points"][point] = value
        elif fields[0] == "FINAL":
            _, x, y, *numbers = fields
            result["final"][f"({x},{y})"] = {
                "pre_store_bits_hex": [f"0x{int(bit):08x}" for bit in numbers[:3]],
                "stored_rgb_words": [int(word) for word in numbers[3:]],
            }
        elif fields[:2] == ["SELF", "portable_worker_final_exact"]:
            result["self_check"] = fields[2] == "1"
    for stage in result["stages"]:
        iteration, direction, radius = stage.pop("key")
        stage.update(iteration=iteration, direction=direction, radius=radius)
    return result


def build_params(loader: AexLoader) -> int:
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 16))
    loader.write_bytes(params + 0x20, struct.pack("<f", 5.0))
    loader.write_bytes(params + 0x24, struct.pack("<f", 100.0))
    loader.write_bytes(params + 0x28, struct.pack("<I", 10))
    loader.write_bytes(params + 0x2C, struct.pack("<I", 1))
    loader.write_bytes(params + 0x30, struct.pack("<I", 0))
    return params


def execute_worker(input_guest: bytes, witnesses: tuple[tuple[int, int], ...]) -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def impl_powf(uc, args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("powf", impl_powf)
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = loader.bump_alloc(len(input_guest), align=64)
    output_data = loader.bump_alloc(len(input_guest), align=64)
    loader.write_bytes(source_data, input_guest)
    loader.write_bytes(output_data, input_guest)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", WIDTH * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", WIDTH))
        loader.write_bytes(address + 0x28, struct.pack("<I", HEIGHT))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    source_world, output_world = world(source_data), world(output_data)
    params = build_params(loader)
    actual: dict = {
        "staging": {}, "helper_calls": [], "stages": [], "writer": {},
        "dependency_cone": [],
    }
    planes: dict[str, int] = {}
    pending: dict | None = None
    writer_pending: tuple[int, int] | None = None

    def staging_hook(ld: AexLoader, address: int, size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        planes.update(a=u64(ld, rsp + 0x60), b=u64(ld, rsp + 0x70), flags=ld.uc.reg_read(UC_X86_REG_RDI))
        for x, y in witnesses:
            pixel = y * WIDTH + x
            actual["staging"][f"({x},{y})"] = {
                "source_argb16_words": list(struct.unpack_from("<4H", input_guest, pixel * 8)),
                "plane_rgb": point_plane(ld, planes["a"], x, y),
                "active_flag": ld.read_bytes(planes["flags"] + pixel, 1)[0],
            }

    def helper_entry(direction: str):
        def hook(ld: AexLoader, address: int, size: int) -> None:
            nonlocal pending
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            call_index = len(actual["helper_calls"])
            iteration = call_index // 12
            part = call_index % 6
            expected_direction = "horizontal" if call_index % 12 < 6 else "vertical"
            if direction != expected_direction:
                raise RuntimeError(f"unexpected helper order at call {call_index}: {direction}")
            width, height, passes, offset, radius = [i32(ld, rsp + off) for off in (0x28, 0x30, 0x38, 0x40, 0x48)]
            wanted = interval_for(direction, iteration, witnesses)
            effective_offset, effective_passes = intersect(offset, passes, wanted)
            ld.write_bytes(rsp + 0x38, struct.pack("<i", effective_passes))
            ld.write_bytes(rsp + 0x40, struct.pack("<i", effective_offset))
            src = ld.uc.reg_read(UC_X86_REG_RDX)
            dst = ld.uc.reg_read(UC_X86_REG_R8)
            weights = ld.uc.reg_read(UC_X86_REG_R9)
            record = {
                "call_index": call_index,
                "iteration": iteration + 1,
                "direction": direction,
                "part": part,
                "function": hex(address),
                "return_address": hex(u64(ld, rsp)),
                "planes": {"flags": hex(ld.uc.reg_read(UC_X86_REG_RCX)), "src": hex(src), "dst": hex(dst), "weights": hex(weights)},
                "abi": {"width": width, "height": height, "passes": passes, "offset": offset, "radius": radius},
                "effective": {"passes": effective_passes, "offset": effective_offset, "wanted_interval": list(wanted)},
                "points_before": {},
            }
            if part == 0:
                record["weights_bits_hex"] = [
                    f"0x{value:08x}"
                    for value in struct.unpack(f"<{radius + 1}I", ld.read_bytes(weights, (radius + 1) * 4))
                ]
            axis_values = {f"({x},{y})": y if direction == "horizontal" else x for x, y in witnesses}
            for x, y in witnesses:
                point = f"({x},{y})"
                selected = effective_offset <= axis_values[point] < effective_offset + effective_passes
                if selected:
                    record["points_before"][point] = {
                        "src": point_plane(ld, src, x, y),
                        "dst": point_plane(ld, dst, x, y),
                    }
            actual["helper_calls"].append(record)
            pending = record
        return hook

    def helper_return(ld: AexLoader, address: int, size: int) -> None:
        nonlocal pending
        if pending is None or pending["return_address"] != hex(address):
            raise RuntimeError(f"helper return mismatch at {hex(address)}")
        dst = int(pending["planes"]["dst"], 16)
        coordinates = {f"({x},{y})": (x, y) for x, y in witnesses}
        pending["points_after"] = {
            point: point_plane(ld, dst, *coordinates[point])
            for point in pending["points_before"]
        }
        if pending["part"] == 5:
            actual["stages"].append({
                "iteration": pending["iteration"],
                "direction": pending["direction"],
                "radius": pending["abi"]["radius"],
                "plane": hex(dst),
                "points": pending["points_after"],
            })
        pending = None

    def writer_pre(ld: AexLoader, address: int, size: int) -> None:
        nonlocal writer_pending
        # Deriving coordinates from the destination pointer avoids coupling
        # this probe to the worker's loop-register allocation.
        destination = ld.uc.reg_read(UC_X86_REG_RBX)
        delta = destination - output_data
        if delta < 0 or delta % 8:
            return
        pixel = delta // 8
        x_coord, y_coord = pixel % WIDTH, pixel // WIDTH
        if (x_coord, y_coord) not in witnesses:
            return
        rgb_ptr = ld.uc.reg_read(UC_X86_REG_RDI) - 8
        actual["writer"][f"({x_coord},{y_coord})"] = {
            "destination": hex(destination),
            "pre_store": f32_record(ld, rgb_ptr),
        }
        writer_pending = (x_coord, y_coord)

    def writer_post(ld: AexLoader, address: int, size: int) -> None:
        nonlocal writer_pending
        if writer_pending is None:
            return
        x, y = writer_pending
        destination = output_data + (y * WIDTH + x) * 8
        actual["writer"][f"({x},{y})"]["stored_argb16_words"] = list(struct.unpack("<4H", ld.read_bytes(destination, 8)))
        writer_pending = None

    loader.add_code_hook(STAGING_DONE, staging_hook)
    loader.add_code_hook(FUN_HORIZONTAL, helper_entry("horizontal"))
    loader.add_code_hook(FUN_VERTICAL, helper_entry("vertical"))
    for address in HORIZONTAL_RETURNS + VERTICAL_RETURNS:
        loader.add_code_hook(address, helper_return)
    loader.add_code_hook(WRITER_PRE, writer_pre)
    loader.add_code_hook(WRITER_POST, writer_post)
    for iteration in range(10):
        actual["dependency_cone"].append({
            "iteration": iteration + 1,
            "horizontal_rows": list(interval_for("horizontal", iteration, witnesses)),
            "vertical_columns": list(interval_for("vertical", iteration, witnesses)),
        })

    started = time.monotonic()
    result = loader.call_function(
        FUN_ENTRY,
        int_args=[context, source_world, output_world, params],
        max_instructions=1_000_000_000,
    )
    actual.update(
        status="return",
        result_rax=hex(result["rax"]),
        elapsed_seconds=round(time.monotonic() - started, 3),
        callbacks=events,
        helper_call_count=len(actual["helper_calls"]),
    )
    actual["witnesses"] = [list(point) for point in witnesses]
    return actual


def merge_actual_runs(runs: list[dict]) -> dict:
    merged = {
        "status": "return" if all(run["status"] == "return" for run in runs) else "incomplete",
        "execution": "one full-worker dependency-cone run per witness",
        "runs": runs,
        "staging": {},
        "stages": [],
        "writer": {},
        "helper_call_count_per_run": [run["helper_call_count"] for run in runs],
        "elapsed_seconds": round(sum(run["elapsed_seconds"] for run in runs), 3),
    }
    for run in runs:
        merged["staging"].update(run["staging"])
        merged["writer"].update(run["writer"])
        for index, stage in enumerate(run["stages"]):
            if index == len(merged["stages"]):
                merged["stages"].append({key: value for key, value in stage.items() if key != "points"} | {"points": {}})
            merged["stages"][index]["points"].update(stage["points"])
    return merged


def compare(actual: dict, portable: dict, windows_rgba: bytes) -> dict:
    comparisons: list[dict] = []
    for index, (a_stage, p_stage) in enumerate(zip(actual["stages"], portable["stages"])):
        for x, y in WITNESSES:
            point = f"({x},{y})"
            actual_bits = a_stage["points"][point]["bits_hex"]
            portable_bits = p_stage["points"][point]["bits_hex"]
            comparisons.append({
                "boundary": "helper_output",
                "stage_index": index,
                "iteration": a_stage["iteration"],
                "direction": a_stage["direction"],
                "radius": a_stage["radius"],
                "point": point,
                "actual_bits_hex": actual_bits,
                "portable_bits_hex": portable_bits,
                "exact": actual_bits == portable_bits,
            })
    final: dict = {}
    for x, y in WITNESSES:
        point = f"({x},{y})"
        writer = actual["writer"][point]
        portable_final = portable["final"][point]
        rgba = list(struct.unpack_from(">4H", windows_rgba, (y * WIDTH + x) * 8))
        final[point] = {
            "actual_pre_store_bits_hex": writer["pre_store"]["bits_hex"],
            "portable_pre_store_bits_hex": portable_final["pre_store_bits_hex"],
            "pre_store_exact": writer["pre_store"]["bits_hex"] == portable_final["pre_store_bits_hex"],
            "actual_stored_rgb_words": writer["stored_argb16_words"][1:],
            "portable_stored_rgb_words": portable_final["stored_rgb_words"],
            "windows_png_rgba16": rgba,
            "actual_matches_windows_rgb": writer["stored_argb16_words"][1:] == rgba[:3],
        }
    first = next((item for item in comparisons if not item["exact"]), None)
    if first is None:
        for point, values in final.items():
            if not values["pre_store_exact"]:
                first = {"boundary": "final_pre_store", "point": point}
                break
    if first is None:
        for point, values in final.items():
            if values["actual_stored_rgb_words"] != values["portable_stored_rgb_words"]:
                first = {"boundary": "stored_word", "point": point}
                break
    windows_differences = [point for point, values in final.items() if not values["actual_matches_windows_rgb"]]
    return {
        "stage_comparisons": comparisons,
        "all_observed_stages_portable_exact": all(item["exact"] for item in comparisons),
        "final": final,
        "first_portable_difference": first,
        "windows_png_difference_points": windows_differences,
        "first_windows_internal_difference": None,
        "first_windows_internal_difference_reason": (
            "Windows evidence is final PNG words only; no same-run Windows helper/pre-store values are present"
            if windows_differences else "no witness difference"
        ),
    }


def write_reports(report: dict) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    if "portable" not in report or "comparison" not in report:
        REPORT_MD.write_text(
            "# OLMBlur case_0006 actual-AEX full-worker probe\n\n"
            "## FACT\n\n"
            f"- Status: `{report.get('actual_aex', {}).get('status')}`\n"
            f"- Classification: `{report.get('classification')}`\n"
        )
        return
    comparison = report.get("comparison", {})
    first = comparison.get("first_portable_difference")
    lines = [
        "# OLMBlur case_0006 actual-AEX dependency-cone worker probe",
        "",
        "## FACT",
        "",
        f"- AEX SHA-256: `{report['identity']['aex_sha256']}`",
        f"- Entry/helper: `{hex(FUN_ENTRY)}`, `{hex(FUN_HORIZONTAL)}`, `{hex(FUN_VERTICAL)}`",
        f"- Worker status: `{report['actual_aex'].get('status')}`; elapsed `{report['actual_aex'].get('elapsed_seconds')}` s",
        f"- Helper calls observed per witness run: `{report['actual_aex'].get('helper_call_count_per_run')}` (expected 120 each)",
        f"- Portable trace self-check against current worker: `{report['portable']['self_check']}`",
        "- Source staging, helper call ABI/planes/origins/offsets, stage outputs, final pre-store float bits, and stored words are retained in the JSON report.",
        "- `pow`, `powf`, and `expf` execute through the loader's host-backed libm callbacks; they are not native Windows CRT calls.",
        "",
        "## Witnesses",
        "",
    ]
    for point, values in comparison.get("final", {}).items():
        lines.append(
            f"- `{point}`: actual pre-store `{values['actual_pre_store_bits_hex']}`, "
            f"portable `{values['portable_pre_store_bits_hex']}`; actual stored RGB "
            f"`{values['actual_stored_rgb_words']}`, portable `{values['portable_stored_rgb_words']}`, "
            f"Windows PNG RGBA `{values['windows_png_rgba16']}`."
        )
    lines.extend([
        "",
        "## INFERENCE",
        "",
        "- The dependency-cone restriction is exact for the two witnesses if each helper is local to its recorded radius and the six chunks are disjoint, as established by the helper ABI fixtures and disassembly. Pixels outside the cone are not full-frame output evidence.",
        f"- First current-portable difference: `{first}`.",
        f"- Windows PNG difference points: `{comparison.get('windows_png_difference_points')}`. The first Windows internal difference is not localized because no same-run Windows typed helper/pre-store trace is available.",
        "- This is a typed worker/helper/store comparison. No PNG-derived tuning or production-source change was made.",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines))


def worker_main() -> int:
    aex_sha = hashlib.sha256(AEX_PATH.read_bytes()).hexdigest()
    if aex_sha != AEX_SHA256:
        raise RuntimeError(f"AEX SHA mismatch: {aex_sha}")
    manifest = json.loads(MANIFEST.read_text())
    case = next(item for item in manifest["cases"] if item["id"] == CASE_ID)
    input_path = BASE / case["before_effects_frame"]
    expected_path = BASE / case["frame"]
    input_w, input_h, input_rgba = png_rgba16(input_path)
    expected_w, expected_h, expected_rgba = png_rgba16(expected_path)
    if (input_w, input_h) != (expected_w, expected_h) or (input_w, input_h) != (WIDTH, HEIGHT):
        raise RuntimeError("case dimensions do not match 1920x1080")
    input_guest = guest_argb_words(input_rgba)
    portable = compile_and_run_portable(input_guest)
    actual = merge_actual_runs([
        execute_worker(input_guest, (point,)) for point in WITNESSES
    ])
    report = {
        "schema": "olm.actual-aex.full-worker-probe/1",
        "classification": {"FACT": "typed actual-AEX dependency-cone observation", "INFERENCE": "cone-local values equal an unpruned full helper run"},
        "identity": {
            "case_id": CASE_ID,
            "aex_path": str(AEX_PATH.relative_to(REPO_ROOT)),
            "aex_sha256": aex_sha,
            "entry": hex(FUN_ENTRY),
            "helpers": [hex(FUN_HORIZONTAL), hex(FUN_VERTICAL)],
            "dimensions": [WIDTH, HEIGHT],
            "pixel_layout": "guest little-endian A,R,G,B words; PNG big-endian R,G,B,A words",
            "params": {"blur": 5.0, "smoothness": 100.0, "repeat": 10, "bias": 1, "legacy": 0},
            "host_contracts": {
                "PF_Handle": "test_olmblur_fullentry.build_pf_suites",
                "math": "AEX import trampolines with Python host libm callbacks for pow/powf/expf/floorf",
                "windows_native_math": False,
            },
            "witnesses": [list(point) for point in WITNESSES],
            "input_png": str(input_path.relative_to(REPO_ROOT)),
            "windows_png": str(expected_path.relative_to(REPO_ROOT)),
        },
        "actual_aex": actual,
        "portable": portable,
        "comparison": compare(actual, portable, expected_rgba),
    }
    write_reports(report)
    print(f"FACT report_json {REPORT_JSON}")
    print(f"FACT report_md {REPORT_MD}")
    print(f"FACT helper_call_count_per_run {actual['helper_call_count_per_run']}")
    print(f"FACT elapsed_seconds {actual['elapsed_seconds']}")
    print(f"INFERENCE first_portable_difference {report['comparison']['first_portable_difference']}")
    return 0


def verify_report() -> int:
    report = json.loads(REPORT_JSON.read_text())
    if hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() != AEX_SHA256:
        raise AssertionError("AEX SHA changed")
    if report["identity"]["aex_sha256"] != AEX_SHA256:
        raise AssertionError("report AEX SHA mismatch")
    if report["actual_aex"]["helper_call_count_per_run"] != [120, 120]:
        raise AssertionError("report does not contain two complete 120-call runs")
    if len(report["actual_aex"]["stages"]) != 20:
        raise AssertionError("report does not contain 20 merged stages")
    observed_radii = [stage["radius"] for stage in report["actual_aex"]["stages"] if stage["direction"] == "horizontal"]
    if observed_radii != list(RADII):
        raise AssertionError(f"unexpected AEX radius sequence: {observed_radii}")
    if not report["portable"]["self_check"]:
        raise AssertionError("portable trace self-check failed")
    comparisons = report["comparison"]["stage_comparisons"]
    if len(comparisons) != 40 or not all(item["exact"] for item in comparisons):
        raise AssertionError("actual/portable stage comparison is incomplete or non-exact")
    report["identity"].setdefault("host_contracts", {
        "PF_Handle": "test_olmblur_fullentry.build_pf_suites",
        "math": "AEX import trampolines with Python host libm callbacks for pow/powf/expf/floorf",
        "windows_native_math": False,
    })
    for run in report["actual_aex"]["runs"]:
        for call in run["helper_calls"]:
            if call["part"] != 0:
                call.pop("weights_bits_hex", None)
            selected = {
                point: value for point, value in call.get("points_before", {}).items()
                if value.get("selected", True)
            }
            for value in selected.values():
                value.pop("selected", None)
            call["points_before"] = selected
            call["points_after"] = {
                point: value for point, value in call.get("points_after", {}).items()
                if point in selected
            }
    windows_differences = [
        point for point, values in report["comparison"]["final"].items()
        if not values["actual_matches_windows_rgb"]
    ]
    if windows_differences != ["(29,71)"]:
        raise AssertionError(f"unexpected Windows witness difference set: {windows_differences}")
    report["comparison"].update(
        all_observed_stages_portable_exact=True,
        windows_png_difference_points=windows_differences,
        first_windows_internal_difference=None,
        first_windows_internal_difference_reason=(
            "Windows evidence is final PNG words only; no same-run Windows helper/pre-store values are present"
            if windows_differences else "no witness difference"
        ),
    )
    write_reports(report)
    print(f"FACT verified_report {REPORT_JSON}")
    print("FACT actual_portable_stage_comparisons 40 exact")
    print(f"INFERENCE windows_internal_boundary localized={not windows_differences}")
    return 0


def parent_main(timeout: int) -> int:
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker"], start_new_session=True)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        blocker = {
            "schema": "olm.actual-aex.full-worker-probe/1",
            "identity": {"case_id": CASE_ID, "aex_sha256": AEX_SHA256, "entry": hex(FUN_ENTRY)},
            "actual_aex": {"status": "hard-timeout", "wall_cap_seconds": timeout},
            "classification": {
                "FACT": "worker did not return before the external wall cap",
                "INFERENCE": "first blocker is execution throughput inside the dependency-cone actual helper run",
            },
        }
        write_reports(blocker)
        print(f"FACT hard_timeout_seconds {timeout}")
        print(f"FACT report_json {REPORT_JSON}")
        return 124


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--verify-report", action="store_true")
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    raise SystemExit(verify_report() if args.verify_report else worker_main() if args.worker else parent_main(args.timeout))
