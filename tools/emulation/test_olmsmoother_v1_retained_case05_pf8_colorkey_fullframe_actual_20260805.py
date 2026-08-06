#!/usr/bin/env python3
"""Verify a retained Color-Key-enabled PF8 Windows render byte-for-byte."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "refs/scripts/build_olmsmoother_cli.sh"
REFERENCE_DIR = ROOT / "refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/OLMSmoother"
MANIFEST = REFERENCE_DIR / "reference_manifest.json"
CASE_ID = "final_random10_olm_smoother_05"
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
OUT = ROOT / "refs/conformance/olmsmoother_v1_retained_case05_pf8_colorkey_fullframe_actual_production_20260805.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def named_value(case: dict, name: str):
    params = case["effects"][0]["params"]
    return next(param["value"] for param in params if param["name"] == name)


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    manifest = json.loads(MANIFEST.read_text())
    case = next(item for item in manifest["cases"] if item["id"] == CASE_ID)
    use_key = int(named_value(case, "Use Color Key"))
    key_float = named_value(case, "Color Key")
    tolerance = int(named_value(case, "Do Smooth Range"))
    key_rgb = [round(float(value) * 255) for value in key_float[:3]]
    assert use_key == 1
    source = REFERENCE_DIR / case["before_effects_frame"]
    expected_path = REFERENCE_DIR / case["frame"]

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-case05-") as temp_name:
        temp = Path(temp_name)
        executable = temp / "olmsmoother_cli"
        params = temp / "case05.json"
        actual_path = temp / "case05.png"
        params.write_text(json.dumps(case))
        subprocess.run([str(BUILD), str(executable)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        completed = subprocess.run([
            str(executable), "--input", str(source), "--params", str(params),
            "--output", str(actual_path),
        ], cwd=ROOT, check=True, capture_output=True, text=True)
        expected_image = Image.open(expected_path).convert("RGBA")
        actual_image = Image.open(actual_path).convert("RGBA")
        assert expected_image.size == actual_image.size
        expected = expected_image.tobytes()
        actual = actual_image.tobytes()
        differences = [abs(left - right) for left, right in zip(expected, actual)]
        mismatched_bytes = sum(left != right for left, right in zip(expected, actual))
        mismatched_pixels = sum(
            expected[index:index + 4] != actual[index:index + 4]
            for index in range(0, len(expected), 4)
        )
        source_pixels = Image.open(source).convert("RGBA").getdata()
        exact_key_rgb_pixels = sum(tuple(pixel[:3]) == tuple(key_rgb)
                                   for pixel in source_pixels)
        report = {
            "schema_version": 1,
            "status": "exact" if mismatched_bytes == 0 else "fail",
            "scope": ("OLMSmoother v1 retained Windows Software PF8 "
                      "final_random10 case05, Use Color Key=1"),
            "actual_aex_sha256": AEX_SHA256,
            "input_sha256": sha256(source),
            "actual_aex_reference_png_sha256": sha256(expected_path),
            "production_png_sha256": sha256(actual_path),
            "width": expected_image.width,
            "height": expected_image.height,
            "use_color_key": use_key,
            "color_key_float": key_float,
            "color_key_rgb8": key_rgb,
            "do_smooth_range": tolerance,
            "input_exact_key_rgb_pixels": exact_key_rgb_pixels,
            "cli_stdout": completed.stdout.strip(),
            "mismatched_pixels": mismatched_pixels,
            "mismatched_channel_bytes": mismatched_bytes,
            "max_abs_diff": max(differences, default=0),
            "mean_abs_diff_all_rgba": sum(differences) / len(differences),
        }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["status"] == "exact"


if __name__ == "__main__":
    main()
