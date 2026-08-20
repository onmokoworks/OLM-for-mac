from __future__ import annotations

import argparse
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
        "GENERIC_PIXEL_LOCAL_PAIRWISE pass=1 geometry=all cells=36"
    )


def test_windows_oracle_connection_is_bounded_and_available() -> None:
    # Existing returned Windows references cover the comparator/replace math.
    # They are not HD/4K or arbitrary-stride evidence; the C++ probe above only
    # promotes source/geometry/stride invariance of the same production renderer.
    required = [
        ROOT / "refs/win_references/20260604_olm/OLMColorKey",
        ROOT / "refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json",
        ROOT / "refs/scripts/smoke_olmcolorkey_replace_colorspace_request_cli.py",
    ]
    assert all(path.exists() for path in required)


def test_generic_edge_thin_under_asan_ubsan() -> None:
    assert _compile_and_run("sanitizer").stderr.strip() == (
        "GENERIC_PIXEL_LOCAL_PAIRWISE pass=1 geometry=sanitizer cells=22"
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
