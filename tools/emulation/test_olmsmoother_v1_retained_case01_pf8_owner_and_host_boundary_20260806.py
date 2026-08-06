#!/usr/bin/env python3
"""Pin the last retained-case01 PF8 owner call and AE PNG boundary."""

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
REFERENCE = ROOT / "refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/OLMSmoother"
SOURCE = REFERENCE / "olm_final_random10_olm_smoother_20260629__software__fr24__final_random10_olm_smoother_01_before_effects.png"
EXPECTED = REFERENCE / "olm_final_random10_olm_smoother_20260629__software__fr24__final_random10_olm_smoother_01.png"
PARAMS = REFERENCE / "reference_manifest.json"
OUT = ROOT / "refs/conformance/olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argb(image: Image.Image) -> bytearray:
    result = bytearray()
    for red, green, blue, alpha in image.convert("RGBA").getdata():
        result += bytes((alpha, red, green, blue))
    return result


def world(loader: AexLoader, pixels: int, width: int, height: int) -> int:
    rowbytes = width * 4
    address = loader.host_alloc(0x50, align=16)
    loader.write_bytes(address, b"\0" * 0x50)
    loader.write_bytes(address + 4, struct.pack("<iii", width, height, rowbytes))
    loader.write_bytes(address + 0x10, struct.pack("<Q", pixels))
    loader.write_bytes(address + 0x18, struct.pack("<Qiii", pixels, rowbytes, width, height))
    return address


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    source_image = Image.open(SOURCE).convert("RGBA")
    expected_image = Image.open(EXPECTED).convert("RGBA")
    width, height = source_image.size
    source_argb = argb(source_image)

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-case01-boundary-") as name:
        temporary = Path(name)
        executable = temporary / "olmsmoother_cli"
        production_path = temporary / "production.png"
        subprocess.run([str(BUILD), str(executable)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([str(executable), "--input", str(SOURCE), "--params", str(PARAMS),
                        "--output", str(production_path)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        production_image = Image.open(production_path).convert("RGBA")

        boundary = []
        for index, (expected, production) in enumerate(
                zip(expected_image.getdata(), production_image.getdata())):
            if expected == production:
                continue
            alpha = production[3]
            modeled_rgb = tuple(
                int(int(channel * alpha / 255.0 + 0.5) * 255 / alpha)
                if alpha else 0 for channel in production[:3])
            modeled = modeled_rgb + (alpha,)
            boundary.append({
                "xy": [index % width, index // width],
                "production_rgba": list(production),
                "windows_ae_png_rgba": list(expected),
                "premultiply_round_unpremultiply_truncate_rgba": list(modeled),
            })

        # The sole owner of the four former non-host residuals is the natural
        # MainInterpKernel8 call at (288,539), direction 1. Execute that actual
        # AEX call and compare its four affected raw ARGB pixels with production.
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        source = loader.host_alloc(len(source_argb), align=16)
        destination = loader.host_alloc(len(source_argb), align=16)
        loader.write_bytes(source, bytes(source_argb))
        loader.write_bytes(destination, bytes(source_argb))
        state = loader.host_alloc(0x80, align=16)
        loader.write_bytes(state, b"\0" * 0x80)
        loader.write_bytes(state + 8, struct.pack("<ii", 33, 33))
        loader.write_bytes(state + 0x10, struct.pack(
            "<QQ", world(loader, source, width, height),
            world(loader, destination, width, height)))
        loader.write_bytes(state + 0x24, struct.pack("<i", 33))
        center_x, center_y, direction = 288, 539, 1
        pointers = [source + ((center_y + dy) * width + center_x + dx) * 4
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        neighborhood = loader.host_alloc(9 * 8, align=16)
        loader.write_bytes(neighborhood, struct.pack("<9Q", *pointers))
        outputs = [loader.host_alloc(4, align=4) for _ in range(9)]
        loader.call_function(0x1800033D0,
                             [state, neighborhood, center_x, center_y, direction, *outputs],
                             max_instructions=500000)
        words = [struct.unpack("<I", loader.read_bytes(pointer, 4))[0]
                 for pointer in outputs]
        loader.call_function(
            0x180005570,
            [state, neighborhood, center_x, center_y, direction,
             words[0], words[1] & 0xFF, words[2] & 0xFF, *words[3:]],
            max_instructions=250000)
        owner_pixels = []
        for y in (540, 541, 549, 550):
            offset = (y * width + center_x) * 4
            actual = loader.read_bytes(destination + offset, 4)
            red, green, blue, alpha = production_image.getpixel((center_x, y))
            production = bytes((alpha, red, green, blue))
            owner_pixels.append({"xy": [center_x, y],
                                 "actual_aex_argb": actual.hex(),
                                 "production_argb": production.hex()})

        report = {
            "schema_version": 1,
            "status": "exact" if (
                all(item["actual_aex_argb"] == item["production_argb"]
                    for item in owner_pixels)
                and len(boundary) == 98
                and all(item["premultiply_round_unpremultiply_truncate_rgba"] ==
                        item["windows_ae_png_rgba"] for item in boundary)) else "fail",
            "scope": "OLMSmoother v1 retained case01 PF8 final owner call and separately modeled Windows AE PNG alpha boundary",
            "actual_aex_sha256": AEX_SHA256,
            "input_sha256": sha256(SOURCE),
            "windows_ae_png_sha256": sha256(EXPECTED),
            "production_png_sha256": sha256(production_path),
            "owner_call": {"center": [center_x, center_y], "direction": direction,
                           "subhandler_words": words, "raw_pixels": owner_pixels},
            "windows_ae_png_boundary": {
                "mismatched_pixels": len(boundary),
                "all_explained_by_premultiply_round_unpremultiply_truncate": all(
                    item["premultiply_round_unpremultiply_truncate_rgba"] ==
                    item["windows_ae_png_rgba"] for item in boundary),
                "alpha_values": sorted({item["production_rgba"][3] for item in boundary}),
                "claim": "host-boundary model only; not plugin arithmetic",
            },
            "claim_boundary": "The four formerly unexplained raw owner pixels are actual-AEX exact. The remaining 98 file pixels are classified only as a Windows AE PNG premultiply/unpremultiply boundary.",
        }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["status"] == "exact"


if __name__ == "__main__":
    main()
