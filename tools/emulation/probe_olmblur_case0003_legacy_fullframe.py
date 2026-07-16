#!/usr/bin/env python3
"""Pinned actual-AEX schedule capture and native portable case_0003 replay."""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_case0006_fullentry as fullworker  # noqa: E402

AEX = ROOT / "plugins_2025/OLMBlur.aex"
MANIFEST = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
INPUT_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/input"
WINDOWS_PNG = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0003.png"
VERIFIER_REPORT = ROOT / "refs/conformance/olmblur_16bpc_current_plugin_verifier_report_20260715.json"
HELPER_MANIFEST = ROOT / "tools/emulation/fixtures/olmblur_fullworker_helper/manifest.json"
PORTABLE_HELPER = ROOT / "core/olmblur_fullworker_helper.cpp"
LEGACY_WORKER = ROOT / "core/olmblur_worker16_legacy.cpp"
PORTABLE_RUNNER = Path(__file__).with_suffix(".cpp")

AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
INPUT_SHA256 = "930317e23068ea93bfd72961c2215e755e73cfd4ec784d97bccca223ed94e30a"
PF16_SHA256 = "afd4269575102eda52e581cec8e77fe62f5f7e808e33cf64d6baf186c81b70aa"
WINDOWS_SHA256 = "ecd4ad9d746b65782fa7173f996cd58b3c45051984cd30e467f5e639164f90af"
VERIFIER_REPORT_SHA256 = "a56f6ba2bb85b75cd9333963efc6e980b431b7a5e2eceacc0fcb993e20d982e8"
HELPER_MANIFEST_SHA256 = "e5e6798f0ebe31a1429847ea847a5b4d815987decf783c112a97d3b2203309d4"
PORTABLE_HELPER_SHA256 = "0c0643143abafd5bd5635fd18755a95e8a297b38786b58913e3af2f5df5c6ad2"

WIDTH, HEIGHT = 960, 540
CASE_ID = "olmblur__case_0003"
PARAMS = {"blur_amount": 248.600006103516, "smoothness": 100, "repeat": 10, "bias_direction": 1, "legacy": 1}
POINTS = ((936, 1), (739, 2), (23, 36), (59, 76), (640, 85), (383, 124),
          (204, 179), (250, 213), (273, 218), (273, 221), (298, 228), (227, 278),
          (564, 281), (165, 345), (165, 346), (129, 403), (362, 406), (362, 408),
          (756, 425), (25, 482))

ENTRY = 0x180005F20
HORIZONTAL = 0x1800014F0
VERTICAL = 0x180001EA0
STAGING_DONE = 0x1800065AE
SCHEDULE_DONE = 0x180006B6E
NATIVE_TIMEOUT_SECONDS = 300


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_sha(path: Path, expected: str) -> None:
    if not path.is_file():
        raise AssertionError(f"required dependency is missing: {path}")
    actual = sha256(path.read_bytes())
    if actual != expected:
        raise AssertionError(f"dependency hash mismatch for {path}: {actual}")


def load_case() -> tuple[bytes, dict]:
    for path, expected in ((AEX, AEX_SHA256), (MANIFEST, MANIFEST_SHA256),
                           (HELPER_MANIFEST, HELPER_MANIFEST_SHA256),
                           (PORTABLE_HELPER, PORTABLE_HELPER_SHA256),
                           (WINDOWS_PNG, WINDOWS_SHA256), (VERIFIER_REPORT, VERIFIER_REPORT_SHA256)):
        require_sha(path, expected)
    helper_manifest = json.loads(HELPER_MANIFEST.read_text())
    if helper_manifest.get("binary_sha256") != AEX_SHA256 or helper_manifest.get("functions") != {
            "horizontal": hex(HORIZONTAL), "vertical": hex(VERTICAL)}:
        raise AssertionError("grounded full-worker helper manifest identity differs")
    manifest = json.loads(MANIFEST.read_text())
    case = next((item for item in manifest["cases"] if item["id"] == CASE_ID), None)
    if case is None:
        raise AssertionError("case_0003 manifest entry is missing")
    values = {item["name"]: item["value"] for item in case["effects"][0]["params"]}
    params = {"blur_amount": values["Blur Amount"], "smoothness": values["Blur Smoothness"],
              "repeat": int(values["Number of Repeat"]), "bias_direction": int(values["Bias Direction"]),
              "legacy": int(values["Legacy"])}
    if params != PARAMS:
        raise AssertionError(f"case_0003 parameters differ: {params!r}")
    input_path = INPUT_DIR / case["before_effects_frame"]
    require_sha(input_path, INPUT_SHA256)
    width, height, rgba = fullworker.png_rgba16(input_path)
    if (width, height) != (WIDTH, HEIGHT):
        raise AssertionError(f"case_0003 dimensions differ: {(width, height)!r}")
    pf16 = bytearray(len(rgba))
    for offset in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, offset)
        struct.pack_into("<4H", pf16, offset, *((word + 1) // 2 for word in (a, r, g, b)))
    if sha256(pf16) != PF16_SHA256:
        raise AssertionError("decoded PF16 input hash differs")
    return bytes(pf16), {"path": str(input_path.relative_to(ROOT)), "png_sha256": INPUT_SHA256,
                         "pf16_sha256": PF16_SHA256}


def expected_staging(pf16: bytes) -> tuple[bytes, bytes]:
    plane = bytearray(WIDTH * HEIGHT * 12)
    flags = bytearray(WIDTH * HEIGHT)
    for pixel in range(WIDTH * HEIGHT):
        a, r, g, b = struct.unpack_from("<4H", pf16, pixel * 8)
        struct.pack_into("<3f", plane, pixel * 12, float(r), float(g), float(b))
        flags[pixel] = int(a != 0)
    return bytes(plane), bytes(flags)


def capture_schedule(pf16: bytes) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda _uc, _args: (loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda _uc, _args: (loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1))) or 0))
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
    loader.write_bytes(block + 0x30, b"\x01")
    capture: dict = {"plane": None, "flags": None, "calls": [], "schedule_done": False}

    def staging_hook(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        plane = struct.unpack("<Q", ld.read_bytes(rsp + 0x50, 8))[0]
        flags = ld.uc.reg_read(UC_X86_REG_RDI)
        capture["plane_pointer"] = plane
        capture["flags"] = ld.read_bytes(flags, WIDTH * HEIGHT)
        capture["plane"] = ld.read_bytes(plane, WIDTH * HEIGHT * 12)

    def helper_hook(direction: str):
        def hook(ld: AexLoader, address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            width, height, columns, rows, offset, radius = (
                struct.unpack("<i", ld.read_bytes(rsp + stack_offset, 4))[0]
                for stack_offset in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
            if radius < 0 or radius > max(WIDTH, HEIGHT):
                raise AssertionError(f"captured helper radius is invalid: {radius}")
            weights_pointer = ld.uc.reg_read(UC_X86_REG_R9)
            weights = ld.read_bytes(weights_pointer, (radius * 2 + 1) * 4)
            capture["calls"].append({
                "call_index": len(capture["calls"]), "function": hex(address), "direction": direction,
                "width": width, "height": height, "columns": columns, "rows": rows,
                "offset": offset, "radius": radius, "source_pointer": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
                "destination_pointer": hex(ld.uc.reg_read(UC_X86_REG_R8)),
                "weights_pointer": hex(weights_pointer), "weights": weights,
                "weights_hex": weights.hex(), "weights_sha256": sha256(weights),
            })
        return hook

    def schedule_done_hook(ld: AexLoader, _address: int, _size: int) -> None:
        capture["schedule_done"] = True
        ld.uc.emu_stop()

    loader.add_code_hook(STAGING_DONE, staging_hook)
    loader.add_code_hook(HORIZONTAL, helper_hook("horizontal"))
    loader.add_code_hook(VERTICAL, helper_hook("vertical"))
    loader.add_code_hook(SCHEDULE_DONE, schedule_done_hook)
    loader.write_bytes(HORIZONTAL, b"\xc3")
    loader.write_bytes(VERTICAL, b"\xc3")
    result = loader.call_function(ENTRY, int_args=[context, world(source_data), world(output_data), block],
                                  max_instructions=40_000_000)
    if capture["plane"] is None or capture["flags"] is None or not capture["schedule_done"]:
        raise AssertionError("actual worker did not complete detoured schedule capture")
    capture["instructions"] = result["instructions"]
    capture["callbacks"] = events
    return capture


def validate_schedule(calls: list[dict]) -> list[dict]:
    if len(calls) != 120:
        raise AssertionError(f"expected 120 helper calls, captured {len(calls)}")
    iterations = []
    for index in range(10):
        group = calls[index * 12:(index + 1) * 12]
        if [call["direction"] for call in group] != ["horizontal"] * 6 + ["vertical"] * 6:
            raise AssertionError(f"direction order differs in iteration {index + 1}")
        if any((call["width"], call["height"]) != (WIDTH, HEIGHT) for call in group):
            raise AssertionError(f"dimensions differ in iteration {index + 1}")
        horizontal, vertical = group[:6], group[6:]
        h_ranges = [[call["offset"], call["offset"] + call["rows"]] for call in horizontal]
        v_ranges = [[call["offset"], call["offset"] + call["columns"]] for call in vertical]
        if h_ranges != [[0, 90], [90, 180], [180, 270], [270, 360], [360, 450], [450, 540]]:
            raise AssertionError(f"horizontal partition differs: {h_ranges!r}")
        if v_ranges != [[0, 160], [160, 320], [320, 480], [480, 640], [640, 800], [800, 960]]:
            raise AssertionError(f"vertical partition differs: {v_ranges!r}")
        radii = {call["radius"] for call in group}
        weights = {call["weights_hex"] for call in group}
        if len(radii) != 1 or len(weights) != 1:
            raise AssertionError(f"radius/coefficients disagree across iteration {index + 1}")
        iterations.append({"iteration": index + 1, "radius": next(iter(radii)),
                           "weights_sha256": sha256(bytes.fromhex(next(iter(weights)))),
                           "horizontal_pass_ranges": h_ranges, "vertical_pass_ranges": v_ranges})
    plane_a = calls[0]["source_pointer"]
    plane_b = calls[0]["destination_pointer"]
    for index, call in enumerate(calls):
        within = index % 12
        expected = (plane_a, plane_b) if within < 6 else (plane_b, plane_a)
        if (call["source_pointer"], call["destination_pointer"]) != expected:
            raise AssertionError(f"source/destination alternation differs at call {index}")
    return iterations


def compile_runner(executable: Path) -> list[str]:
    command = [os.environ.get("CXX", "c++"), "-std=c++17", "-O2", "-ffp-contract=off", "-fno-fast-math",
               "-Icore", str(PORTABLE_HELPER), str(PORTABLE_RUNNER), "-o", str(executable)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"portable compile failed: {result.stderr.strip()}")
    return [command[0], *command[1:6], "core/olmblur_fullworker_helper.cpp",
            str(PORTABLE_RUNNER.relative_to(ROOT)), "-o", "<temporary>/case0003_legacy_fullframe"]


def run_actual_micro(direction: str, weights: bytes, radius: int) -> tuple[bytes, bytes, int, int, list[int], bytes]:
    width, height = (2, 1) if direction == "horizontal" else (1, 2)
    columns = rows = 1
    flags = b"\x01\x01"
    source = struct.pack("<6f", 101.25, 202.5, 303.75, 1001.5, 2002.25, 3003.125)
    destination = bytes(len(source))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    def alloc(data: bytes) -> int:
        address = loader.bump_alloc(len(data), align=16)
        loader.write_bytes(address, data)
        return address
    dst = alloc(destination)
    args = [alloc(flags), alloc(source), dst, alloc(weights), width,
            0 if direction == "horizontal" else height, columns, rows, 0, radius]
    cap = 3_000_000
    result = loader.call_function(HORIZONTAL if direction == "horizontal" else VERTICAL,
                                  int_args=args, max_instructions=cap)
    if result["instructions"] >= cap:
        raise AssertionError(f"{direction} microfixture reached instruction cap")
    return flags, source, result["instructions"], cap, [width, height], loader.read_bytes(dst, len(source))


def run_portable_micro(executable: Path, temp: Path, direction: str, flags: bytes, source: bytes,
                       weights: bytes, radius: int) -> bytes:
    paths = {}
    for name, data in (("flags", flags), ("source", source), ("weights", weights)):
        path = temp / f"micro_{direction}_{name}.bin"
        path.write_bytes(data)
        paths[name] = path
    output = temp / f"micro_{direction}_output.bin"
    result = subprocess.run([str(executable), "--micro", direction, str(paths["flags"]),
                             str(paths["source"]), str(paths["weights"]), str(output), str(radius)],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"portable {direction} microfixture failed: {result.stderr.strip()}")
    return output.read_bytes()


def write_schedule(path: Path, calls: list[dict]) -> None:
    data = bytearray(b"OLMBL3S1" + struct.pack("<I", len(calls)))
    for call in calls:
        data.extend(struct.pack("<7I", int(call["direction"] == "vertical"), call["width"], call["height"],
                                call["columns"], call["rows"], call["offset"], call["radius"]))
        data.extend(call["weights"])
    path.write_bytes(data)


def retained_words(path: Path) -> dict[str, list[int]]:
    width, height, rgba = fullworker.png_rgba16(path)
    if (width, height) != (WIDTH, HEIGHT):
        raise AssertionError(f"retained PNG dimensions differ: {path}")
    result = {}
    for x, y in POINTS:
        r, g, b, a = struct.unpack_from(">4H", rgba, (y * WIDTH + x) * 8)
        result[f"({x},{y})"] = [(word + 1) // 2 for word in (a, r, g, b)]
    return result


def verifier_words() -> dict[str, dict[str, list[int]]]:
    report = json.loads(VERIFIER_REPORT.read_text())
    case = next((item for item in report.get("cases", []) if item.get("id") == CASE_ID), None)
    if case is None or case.get("nonzero_px") != 20:
        raise AssertionError("authoritative current-plugin verifier case differs")
    result = {}
    for sample in case.get("samples", []):
        point = f"({sample['x']},{sample['y']})"
        if (sample["x"], sample["y"]) not in POINTS:
            raise AssertionError(f"verifier contains an unknown residual point: {point}")
        candidate_rgba = sample["candidate"]
        reference_rgba = sample["reference"]
        result[point] = {
            "mac_argb16_words": [(candidate_rgba[index] + 1) // 2 for index in (3, 0, 1, 2)],
            "windows_argb16_words": [(reference_rgba[index] + 1) // 2 for index in (3, 0, 1, 2)],
            "mac_exported_rgba16_words": candidate_rgba,
            "windows_exported_rgba16_words": reference_rgba,
        }
    if len(result) != 10:
        raise AssertionError(f"verifier sample limit changed: {len(result)}")
    return result


def run_probe() -> dict:
    pf16, input_identity = load_case()
    expected_plane, expected_flags = expected_staging(pf16)
    capture = capture_schedule(pf16)
    if capture["plane"] != expected_plane or capture["flags"] != expected_flags:
        raise AssertionError("actual staged plane/flags differ from exact PF16 decode")
    iterations = validate_schedule(capture["calls"])
    distinct = {}
    for call in capture["calls"]:
        distinct.setdefault((call["radius"], call["direction"]), call)

    with tempfile.TemporaryDirectory(prefix="olmblur_case0003_legacy_") as temporary:
        temp = Path(temporary)
        executable = temp / "case0003_legacy_fullframe"
        compile_command = compile_runner(executable)
        coefficient_paths = [temp / name for name in (
            "case0003_current.bin", "case0003_candidate.bin",
            "case0007_current.bin", "case0007_candidate.bin")]
        coefficient_run = subprocess.run(
            [str(executable), "--coefficients", *(str(path) for path in coefficient_paths)],
            cwd=ROOT, text=True, capture_output=True, check=False)
        if coefficient_run.returncode:
            raise AssertionError(f"coefficient comparison failed: {coefficient_run.stderr.strip()}")
        case0003_current, case0003_candidate, case0007_current, case0007_candidate = (
            path.read_bytes() for path in coefficient_paths)
        captured_coefficients = b"".join(
            capture["calls"][iteration * 12]["weights"] for iteration in range(10))
        if len(case0003_current) != len(captured_coefficients) or len(case0003_candidate) != len(captured_coefficients):
            raise AssertionError("case_0003 coefficient byte count differs")
        words = len(captured_coefficients) // 4
        captured_words = struct.unpack(f"<{words}I", captured_coefficients)
        current_words = struct.unpack(f"<{words}I", case0003_current)
        candidate_words = struct.unpack(f"<{words}I", case0003_candidate)
        current_diff_indices = [index for index, values in enumerate(zip(current_words, captured_words))
                                if values[0] != values[1]]
        candidate_diff_indices = [index for index, values in enumerate(zip(candidate_words, captured_words))
                                  if values[0] != values[1]]
        iteration_width = 248 * 2 + 1
        current_diff_by_iteration = [
            sum(start <= index < start + iteration_width for index in current_diff_indices)
            for start in range(0, words, iteration_width)]
        if candidate_diff_indices:
            raise AssertionError("double-exp candidate differs from captured case_0003 coefficients")
        if current_diff_by_iteration != [0, 0, 0, 0, 2, 2, 4, 6, 2, 0]:
            raise AssertionError(f"current case_0003 coefficient residual changed: {current_diff_by_iteration}")
        if case0007_current != case0007_candidate:
            raise AssertionError("double-exp candidate changes exact Legacy case_0007 coefficients")
        layer_a = []
        for (radius, direction), call in distinct.items():
            flags, source, instructions, cap, dimensions, actual = run_actual_micro(
                direction, call["weights"], radius)
            portable = run_portable_micro(executable, temp, direction, flags, source, call["weights"], radius)
            if actual != portable:
                raise AssertionError(f"actual/portable helper mismatch for radius={radius} {direction}")
            layer_a.append({"radius": radius, "direction": direction, "dimensions": dimensions,
                            "output_count": 1, "coefficient_iteration": call["call_index"] // 12 + 1,
                            "weights_sha256": call["weights_sha256"], "actual_instructions": instructions,
                            "instruction_cap": cap, "actual_output_sha256": sha256(actual),
                            "portable_output_sha256": sha256(portable), "exact": True})

        input_path = temp / "input.pf16"
        schedule_path = temp / "schedule.bin"
        input_path.write_bytes(pf16)
        write_schedule(schedule_path, capture["calls"])
        command = [str(executable), str(input_path), str(schedule_path),
                   *(str(value) for point in POINTS for value in point)]
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                                       timeout=NATIVE_TIMEOUT_SECONDS, check=False)
        except subprocess.TimeoutExpired as error:
            raise AssertionError(f"native full-frame replay exceeded {NATIVE_TIMEOUT_SECONDS}s") from error
        wall_seconds = time.monotonic() - started
        if completed.returncode:
            raise AssertionError(f"native full-frame replay failed: {completed.stderr.strip()}")
        lines = completed.stdout.strip().splitlines()
        if len(lines) != len(POINTS) + 1 or not lines[0].startswith("runtime_seconds "):
            raise AssertionError(f"native output shape differs: {completed.stdout[:500]!r}")
        native_seconds = float(lines[0].split()[1])
        if native_seconds > NATIVE_TIMEOUT_SECONDS or wall_seconds > NATIVE_TIMEOUT_SECONDS:
            raise AssertionError("native runtime exceeded declared cap")
        predictions = {}
        for line, expected_point in zip(lines[1:], POINTS):
            fields = line.split()
            x, y = map(int, fields[:2])
            if (x, y) != expected_point or len(fields) != 8:
                raise AssertionError(f"native witness order differs: {line!r}")
            bits = fields[2::2]
            predictions[f"({x},{y})"] = {
                "pre_store_bits_hex": bits,
                "pre_store_float32": [struct.unpack("<f", struct.pack("<I", int(value, 16)))[0]
                                      for value in bits],
                "writer_predicted_rgb_words": [int(value) for value in fields[3::2]],
            }

    windows = retained_words(WINDOWS_PNG)
    verifier = verifier_words()
    comparisons = {}
    for point, prediction in predictions.items():
        predicted = prediction["writer_predicted_rgb_words"]
        authoritative = verifier.get(point)
        if authoritative is not None and authoritative["windows_argb16_words"] != windows[point]:
            raise AssertionError(f"verifier and pinned Windows PNG disagree at {point}")
        mac_words = authoritative["mac_argb16_words"] if authoritative is not None else None
        comparisons[point] = {
            "portable_writer_predicted_rgb_words": predicted,
            "retained_mac_argb16_words": mac_words, "retained_windows_argb16_words": windows[point],
            "retained_mac_source": (str(VERIFIER_REPORT.relative_to(ROOT)) if authoritative is not None else None),
            "retained_windows_source": str(WINDOWS_PNG.relative_to(ROOT)),
            "portable_matches_mac_rgb": (predicted == mac_words[1:] if mac_words is not None else None),
            "portable_matches_windows_rgb": predicted == windows[point][1:],
            "mac_minus_windows_rgb": ([a - b for a, b in zip(mac_words[1:], windows[point][1:])]
                                      if mac_words is not None else None),
        }

    public_calls = [{key: value for key, value in call.items() if key != "weights"}
                    for call in capture["calls"]]
    return {
        "schema": "olmblur.case0003.legacy-schedule-fullframe/1", "status": "pass_two_layer_witness",
        "platform": "Mac-only Unicorn execution of pinned PE AEX plus compiled native portable C++ Layer B",
        "forbidden_execution": {"windows": False, "nas": False, "ssh": False, "after_effects_interrupted": False,
                                "actual_full_frame_x86_worker": False},
        "identity": {"case_id": CASE_ID, "aex": str(AEX.relative_to(ROOT)), "aex_sha256": AEX_SHA256,
                     "entry": hex(ENTRY), "helpers": [hex(HORIZONTAL), hex(VERTICAL)], "input": input_identity,
                     "manifest_sha256": MANIFEST_SHA256, "helper_manifest_sha256": HELPER_MANIFEST_SHA256,
                     "portable_helper_sha256": PORTABLE_HELPER_SHA256,
                     "windows_png_sha256": WINDOWS_SHA256,
                     "current_mac_verifier_report_sha256": VERIFIER_REPORT_SHA256},
        "parameters": PARAMS,
        "schedule_capture": {"staging_boundary": hex(STAGING_DONE), "schedule_stop": hex(SCHEDULE_DONE),
                             "instructions": capture["instructions"], "helper_body_detour": "RET at both helper entries",
                             "math_backend": "AEX guest caller with AexLoader host-backed Python math callbacks; not Windows CRT",
                             "coefficient_provenance": "captured callback-produced guest coefficient bytes; not tuned and not Windows truth",
                             "callback_events": capture["callbacks"], "call_count": len(public_calls),
                             "calls": public_calls, "iterations": iterations,
                             "staged_plane_sha256": sha256(capture["plane"]),
                             "flags_sha256": sha256(capture["flags"]), "staging_matches_pf16_decode": True},
        "dependency": {"sum_of_iteration_radii": sum(item["radius"] for item in iterations),
                       "frame_dimensions": [WIDTH, HEIGHT], "reaches_frame_boundary": True,
                       "layer_b_scope": "complete 960x540 frame required"},
        "layer_a_actual_helper_microfixtures": {"distinct_radius_direction_count": len(distinct),
                                                "all_exact": all(item["exact"] for item in layer_a),
                                                "fixtures": layer_a},
        "coefficient_candidate": {
            "production_source": str(LEGACY_WORKER.relative_to(ROOT)),
            "production_source_sha256": sha256(LEGACY_WORKER.read_bytes()),
            "current_float_exp_diff_words": len(current_diff_indices),
            "current_float_exp_diff_by_iteration": current_diff_by_iteration,
            "double_exp_float_cast_exact_words": words,
            "double_exp_float_cast_diff_words": len(candidate_diff_indices),
            "case0007_exact_control_words": len(case0007_current) // 4,
            "case0007_candidate_changes": 0,
            "scope": "16bpc Legacy worker only; 8bpc and 32bpc workers unchanged",
        },
        "layer_b_native_portable": {"execution": "compiled native portable C++ only", "compile_command": compile_command,
                                    "runtime_seconds": native_seconds, "wall_seconds": wall_seconds,
                                    "runtime_cap_seconds": NATIVE_TIMEOUT_SECONDS,
                                    "operation_order": "captured ten iterations, each H calls 0..5 then V calls 6..11; float32 helper order preserved",
                                    "predictions": predictions, "retained_comparisons": comparisons,
                                    "writer_grounding": "portable floor(float32 + 0.5f), clamp 0..32768 rule covered by retained complete-worker fixtures in test_olmblur_worker16_legacy.py"},
        "classification": "captured_legacy_schedule_actual_helpers_micro_exact_native_fullframe_predictions",
        "claim_limit": "Host-backed callback coefficient bytes are Mac probe inputs, explicitly not Windows CRT truth; comparisons do not tune them or establish Windows pre-store equivalence.",
    }


if __name__ == "__main__":
    result = run_probe()
    print(json.dumps({"status": result["status"], "schedule_calls": result["schedule_capture"]["call_count"],
                      "microfixtures": len(result["layer_a_actual_helper_microfixtures"]["fixtures"]),
                      "native_seconds": result["layer_b_native_portable"]["runtime_seconds"]}, indent=2))
