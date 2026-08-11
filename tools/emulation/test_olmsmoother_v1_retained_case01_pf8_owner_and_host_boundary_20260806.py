#!/usr/bin/env python3
"""Pin the retained-case01 PF8 owner fact without overclaiming its PNG boundary."""

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
PRODUCTION_SOURCE = ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
EXPECTED_SOURCE_SHA256 = "5276e925f0e7f6de61532a6f9adc3c33a9c8e7330deb0b96eb83f16a30273776"
EXPECTED_WINDOWS_PNG_SHA256 = "afbf8c8b2a96e3b496179b0b0407a391a46f6efb6e04fa0b524fbb355a745470"


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
    assert sha256(SOURCE) == EXPECTED_SOURCE_SHA256
    assert sha256(EXPECTED) == EXPECTED_WINDOWS_PNG_SHA256
    manifest = json.loads(PARAMS.read_text())
    case = next(item for item in manifest["cases"]
                if item["id"] == "final_random10_olm_smoother_01")
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

        owner_exact = all(item["actual_aex_argb"] == item["production_argb"]
                          for item in owner_pixels)
        modeled = [item for item in boundary
                   if item["premultiply_round_unpremultiply_truncate_rgba"] ==
                   item["windows_ae_png_rgba"]]
        unexplained = [item for item in boundary if item not in modeled]
        alpha_pairs = {}
        for item in boundary:
            key = "%d->%d" % (item["production_rgba"][3],
                               item["windows_ae_png_rgba"][3])
            alpha_pairs[key] = alpha_pairs.get(key, 0) + 1
        # This fixture records AE/project metadata and decoded PNGs, but not the
        # loaded AEX identity or the import/export alpha and color-management
        # interpretation.  It therefore cannot prove an AE-host conversion.
        fixture_identity_complete = False
        host_boundary_exact = False
        report = {
            "schema_version": 2,
            "status": "owner_exact_host_boundary_unresolved" if owner_exact else "fail",
            "scope": "OLMSmoother v1 retained case01 PF8 isolated owner call and separately unresolved Windows AE PNG boundary",
            "actual_aex_sha256": AEX_SHA256,
            "input_sha256": EXPECTED_SOURCE_SHA256,
            "windows_ae_png_sha256": EXPECTED_WINDOWS_PNG_SHA256,
            "production_png_sha256": sha256(production_path),
            "production_source_sha256": sha256(PRODUCTION_SOURCE),
            "owner_call": {"center": [center_x, center_y], "direction": direction,
                           "subhandler_words": words, "raw_pixels": owner_pixels},
            "windows_ae_png_boundary": {
                "mismatched_pixels": len(boundary),
                "premultiply_model_explained_pixels": len(modeled),
                "premultiply_model_unexplained_pixels": len(unexplained),
                "all_explained_by_premultiply_round_unpremultiply_truncate": not unexplained,
                "alpha_values": sorted({item["production_rgba"][3] for item in boundary}),
                "alpha_pair_counts": alpha_pairs,
                "unexplained_pixels": unexplained,
                "exact_claim": host_boundary_exact,
                "classification": "unresolved_retained_windows_ae_png_boundary",
                "claim": "observation only; neither plugin arithmetic nor a host conversion model is inferred",
            },
            "retained_fixture_audit": {
                "ae_version": manifest.get("ae_version"),
                "renderer": case["render_set_id"],
                "project_gpu_accel_type": case["project_gpu_accel_type"],
                "input_png_mode": source_image.mode,
                "output_png_mode": expected_image.mode,
                "input_png_metadata": source_image.info,
                "output_png_metadata": expected_image.info,
                "loaded_aex_sha256_recorded_at_capture": False,
                "input_alpha_interpretation_recorded": False,
                "output_premultiply_conversion_recorded": False,
                "project_working_space_recorded": False,
                "fixture_identity_complete": fixture_identity_complete,
            },
            "claim_boundary": "The four isolated owner pixels are actual-AEX exact. The retained Windows AE PNG comparison is unresolved because capture-time binary identity and import/export alpha/color-management conditions are absent; it is not an exactness gate.",
        }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    # Fail closed: owner drift fails; missing host provenance must remain an
    # explicit non-exact classification and may never silently become exact.
    assert owner_exact
    assert report["status"] == "owner_exact_host_boundary_unresolved"
    assert not report["windows_ae_png_boundary"]["exact_claim"]
    assert not report["retained_fixture_audit"]["fixture_identity_complete"]
    assert len(boundary) == 101
    assert len(modeled) == 98
    assert len(unexplained) == 3


if __name__ == "__main__":
    main()
