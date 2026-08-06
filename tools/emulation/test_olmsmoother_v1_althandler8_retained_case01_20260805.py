#!/usr/bin/env python3
"""Compare retained case01 PF8 AltHandler calls against the Windows AEX."""

import ctypes
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader


AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
BUILD = ROOT / "refs/scripts/build_olmsmoother_cli.sh"
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_mainkernel8_production_harness_20260805.cpp"
REFERENCE_DIR = ROOT / "refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/OLMSmoother"
SOURCE = REFERENCE_DIR / "olm_final_random10_olm_smoother_20260629__software__fr24__final_random10_olm_smoother_01_before_effects.png"
EXPECTED = REFERENCE_DIR / "olm_final_random10_olm_smoother_20260629__software__fr24__final_random10_olm_smoother_01.png"
PARAMS = REFERENCE_DIR / "reference_manifest.json"
OUT = ROOT / "refs/conformance/olmsmoother_v1_retained_case01_pf8_althandler_actual_production_20260805.json"
CLASSIFIER8 = 0x180008060
ALTHANDLER8 = 0x1800047F0
DIRECTIONS = (5, 3, 1, 7)
DX = (-1, 0, 1, -1, 0, 1, -1, 0, 1)
DY = (-1, -1, -1, 0, 0, 0, 1, 1, 1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argb_bytes(image: Image.Image) -> bytearray:
    result = bytearray()
    for red, green, blue, alpha in image.convert("RGBA").getdata():
        result += bytes((alpha, red, green, blue))
    return result


def dual_world(loader: AexLoader, pixels: int, width: int, height: int, rowbytes: int) -> int:
    world = loader.host_alloc(0x50, align=16)
    loader.write_bytes(world, b"\0" * 0x50)
    loader.write_bytes(world + 4, struct.pack("<iii", width, height, rowbytes))
    loader.write_bytes(world + 0x10, struct.pack("<Q", pixels))
    loader.write_bytes(world + 0x18, struct.pack("<Qiii", pixels, rowbytes, width, height))
    return world


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    source_image = Image.open(SOURCE).convert("RGBA")
    expected_image = Image.open(EXPECTED).convert("RGBA")
    width, height = source_image.size
    rowbytes = width * 4
    argb = argb_bytes(source_image)

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-alt8-") as temp_name:
        temp = Path(temp_name)
        cli = temp / "olmsmoother_cli"
        actual_png = temp / "case01.png"
        library_path = temp / "libolmsmoother_alt8.dylib"
        subprocess.run([str(BUILD), str(cli)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([str(cli), "--input", str(SOURCE), "--params", str(PARAMS),
                        "--output", str(actual_png)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([
            "clang++", "-std=c++17", "-O2", "-shared", "-fPIC",
            "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS),
            "-o", str(library_path),
        ], cwd=ROOT, check=True, capture_output=True, text=True)

        production_image = Image.open(actual_png).convert("RGBA")
        residuals = [
            (index % width, index // width)
            for index, (expected, production) in enumerate(
                zip(expected_image.getdata(), production_image.getdata()))
            if expected != production
        ]

        library = ctypes.CDLL(str(library_path))
        classifier = library.olmsmoother_run_classifier8_production
        classifier.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_int32,
                               ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
                               ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
        classifier.restype = ctypes.c_int
        alt = library.olmsmoother_run_althandler8_production
        alt.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                        ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
                        ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
                        ctypes.c_int32, ctypes.c_int32]
        production_source = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
        production_destination = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)

        loader = AexLoader(str(AEX), verbose=False, fast=True)
        source = loader.host_alloc(len(argb), align=16)
        destination = loader.host_alloc(len(argb), align=16)
        loader.write_bytes(source, bytes(argb))
        loader.write_bytes(destination, bytes(argb))
        src_world = dual_world(loader, source, width, height, rowbytes)
        dst_world = dual_world(loader, destination, width, height, rowbytes)
        state = loader.host_alloc(0x80, align=16)
        loader.write_bytes(state, b"\0" * 0x80)
        loader.write_bytes(state + 8, struct.pack("<ii", 33, 33))
        loader.write_bytes(state + 0x10, struct.pack("<QQ", src_world, dst_world))
        loader.write_bytes(state + 0x20, struct.pack("<ii", 33, 33))
        neighborhood = loader.host_alloc(9 * 8, align=16)

        candidates = set()
        for target_x, target_y in residuals:
            for direction in DIRECTIONS:
                center_x = target_x - DX[direction]
                center_y = target_y - DY[direction]
                if 0 <= center_x < width and 0 <= center_y < height:
                    candidates.add((center_x, center_y, direction, 2, target_x, target_y))
                candidates.add((target_x, target_y, direction, 3, target_x, target_y))

        tested = []
        classifier_mismatches = []
        handler_mismatches = []
        writes = 0
        for center_x, center_y, direction, wanted_scan, target_x, target_y in sorted(candidates):
            pointers = []
            for neighbor_y in range(center_y - 1, center_y + 2):
                for neighbor_x in range(center_x - 1, center_x + 2):
                    if 0 <= neighbor_x < width and 0 <= neighbor_y < height:
                        pointers.append(source + neighbor_y * rowbytes + neighbor_x * 4)
                    else:
                        pointers.append(0)
            loader.write_bytes(neighborhood, struct.pack("<9Q", *pointers))
            production_scan = classifier(production_source, width, height, rowbytes,
                                         33, center_x, center_y, direction)
            actual_scan = loader.call_function(
                CLASSIFIER8, [state, center_x, center_y, neighborhood, direction],
                max_instructions=100000)["rax"] & 0xFFFFFFFF
            if actual_scan & 0x80000000:
                actual_scan -= 0x100000000
            if production_scan != actual_scan:
                classifier_mismatches.append({
                    "center": [center_x, center_y], "direction": direction,
                    "actual": actual_scan, "production": production_scan,
                })
            if actual_scan != wanted_scan:
                continue

            offset = target_y * rowbytes + target_x * 4
            original = bytes(argb[offset:offset + 4])
            loader.write_bytes(destination + offset, original)
            for channel, value in enumerate(original):
                production_destination[offset + channel] = value
            loader.call_function(
                ALTHANDLER8,
                [state, neighborhood, center_x, center_y, direction, actual_scan],
                max_instructions=1000000)
            alt(production_source, production_destination, width, height, rowbytes,
                33, center_x, center_y, direction, production_scan)
            actual_pixel = loader.read_bytes(destination + offset, 4)
            production_pixel = bytes(production_destination[offset:offset + 4])
            if actual_pixel != original:
                writes += 1
            item = {
                "center": [center_x, center_y], "direction": direction,
                "scan_type": actual_scan, "target": [target_x, target_y],
                "source_argb": original.hex(), "actual_argb": actual_pixel.hex(),
                "production_argb": production_pixel.hex(),
            }
            tested.append(item)
            if actual_pixel != production_pixel:
                handler_mismatches.append(item)

        report = {
            "schema_version": 1,
            "status": "exact" if not classifier_mismatches and not handler_mismatches else "fail",
            "scope": "OLMSmoother v1 retained case01 PF8 AltHandler paths that can touch a full-frame residual",
            "actual_aex_sha256": AEX_SHA256,
            "input_sha256": sha256(SOURCE),
            "expected_png_sha256": sha256(EXPECTED),
            "production_png_sha256": sha256(actual_png),
            "fullframe_residual_pixels": len(residuals),
            "candidate_calls": len(candidates),
            "tested_alt_calls": len(tested),
            "tested_alt_calls_writing_target": writes,
            "classifier_mismatches": classifier_mismatches,
            "handler_mismatches": handler_mismatches,
        }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["status"] == "exact"


if __name__ == "__main__":
    main()
