#!/usr/bin/env python3
"""Build the current portable v1 renderer and compare case_0001 byte-for-byte."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "refs/scripts/build_olmsmoother_cli.sh"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png"
EXPECTED = ROOT / "refs/win_references/20260604_olm/OLMSmoother/case_0001.png"
PARAMS = ROOT / "refs/win_references/20260604_olm/OLMSmoother/reference_manifest.json"
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
OUT = ROOT / "refs/conformance/olmsmoother_v1_case0001_pf8_fullframe_actual_aex_20260805.json"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-fullframe-") as directory:
        directory = Path(directory)
        executable = directory / "olmsmoother_cli"
        actual_path = directory / "case_0001.png"
        subprocess.run([str(BUILD), str(executable)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([
            str(executable), "--input", str(SOURCE), "--params", str(PARAMS),
            "--output", str(actual_path),
        ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

        expected_image = Image.open(EXPECTED).convert("RGBA")
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
        report = {
            "schema_version": 1,
            "status": "exact" if mismatched_bytes == 0 else "fail",
            "scope": "OLMSmoother v1 classic PF8 case_0001, Use Color Key=0, Do Smooth Range=6",
            "actual_aex_sha256": AEX_SHA256,
            "input_sha256": sha256(SOURCE),
            "actual_aex_reference_png_sha256": sha256(EXPECTED),
            "production_png_sha256": sha256(actual_path),
            "width": expected_image.width,
            "height": expected_image.height,
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
