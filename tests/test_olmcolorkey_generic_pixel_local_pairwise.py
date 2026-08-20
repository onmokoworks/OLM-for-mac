from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests/probe_olmcolorkey_generic_pixel_local_pairwise.cpp"


def _compile_and_run(geometry: str = "all") -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="olmck-generic-pairwise.") as raw:
        executable = Path(raw) / "probe"
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
        ).stdout.strip()
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations", "-isysroot", sdk,
            "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources",
            "-Imac/OLMColorKey", str(PROBE),
            "mac/OLMColorKey/OLMColorKey_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
            "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(executable),
        ]
        if geometry == "sanitizer":
            command[5:5] = ["-O1", "-g", "-fsanitize=address,undefined",
                            "-fno-omit-frame-pointer"]
        subprocess.run(command, cwd=ROOT, check=True)
        run = subprocess.run(
            [str(executable), "--geometry", geometry], cwd=ROOT,
            capture_output=True, text=True, check=True
        )
    return run


def test_generic_pixel_local_pairwise_matrix() -> None:
    assert _compile_and_run().stderr.strip() == (
        "GENERIC_PIXEL_LOCAL_PAIRWISE pass=1 geometry=all cells=42"
    )


def test_windows_oracle_connection_is_bounded_and_available() -> None:
    # Use compact, tracked actual-AEX/production reports instead of the 4.9 MiB
    # returned-image tree, which is intentionally absent in a clean checkout.
    colors = json.loads((
        ROOT / "refs/conformance/olmcolorkey_colorspace_2_5_matrix_actual_aex_20260810.json"
    ).read_text())
    toggles = json.loads((
        ROOT / "refs/conformance/olmcolorkey_keep_premult_replace_actual_aex_20260811.json"
    ).read_text())
    composition = json.loads((
        ROOT / "refs/conformance/olmcolorkey_replace_edge_composition_actual_aex_20260811.json"
    ).read_text())
    assert colors["status"] == toggles["status"] == composition["status"] == "exact"
    assert colors["matrix"]["color_spaces"] == [2, 5]  # HSV and YUV
    assert colors["matrix"]["pixel_formats"] == ["PF8", "PF16", "PF32"]
    assert len(colors["cases"]) == 36
    assert toggles["matrix"] == {
        "color_keep": [False, True],
        "pixel_formats": ["PF8", "PF16", "PF32"],
        "premultiplied": [False, True],
        "replace": [False, True],
    }
    assert len(toggles["cases"]) == 24
    assert composition["schema_version"] == 1
    assert composition["matrix"] == {
        "edge_modes": [
            "none",
            "thin_negative4",
            "thin_positive4",
            "blur_direction2_amount4",
            "thin_negative4_blur_direction2_amount4",
            "thin_positive4_blur_direction2_amount4",
        ],
        "pixel_formats": ["PF8", "PF16", "PF32"],
        "replace": [False, True],
    }
    assert len(composition["cases"]) == 36
    assert {
        colors["actual_aex_sha256"],
        toggles["actual_aex_sha256"],
        composition["actual_aex_sha256"],
    } == {"9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"}
    assert composition["claim_boundary"] == (
        "Exact for the declared 13x11 two-key fixture, Replace off/on, Edge "
        "none/Thin -4/Thin +4/Blur Direction 2 Amount 4, the two Thin+Blur "
        "combinations, and PF8/PF16/PF32. Other directions, amounts, geometry, "
        "and AE-host execution are not claimed."
    )
    for report in (colors, toggles, composition):
        assert len(report["actual_aex_sha256"]) == 64
        assert all(case["status"] == "exact" for case in report["cases"])
        assert all(case["actual_sha256"] == case["production_sha256"]
                   for case in report["cases"])
    assert all(case["native_full_worker_path"] for case in composition["cases"])


def test_generic_edge_thin_under_asan_ubsan() -> None:
    assert _compile_and_run("sanitizer").stderr.strip() == (
        "GENERIC_PIXEL_LOCAL_PAIRWISE pass=1 geometry=sanitizer cells=27"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--geometry", choices=("hd", "uhd", "all", "sanitizer"), default="all"
    )
    args = parser.parse_args()
    run = _compile_and_run(args.geometry)
    print(run.stderr.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
