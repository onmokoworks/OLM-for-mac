from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests/probe_olmcolorkey_generic_pixel_local_beta.cpp"


def test_generic_pixel_local_beta_worlds() -> None:
    with tempfile.TemporaryDirectory(prefix="olmck-generic-pixel-local.") as raw:
        executable = Path(raw) / "probe"
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
        ).stdout.strip()
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            "-isysroot", sdk, "-IHeaders", "-IHeaders/SP", "-IUtil",
            "-IResources", "-Imac/OLMColorKey", str(PROBE),
            "mac/OLMColorKey/OLMColorKey_Strings.cpp",
            "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp",
            "-framework", "Cocoa", "-o", str(executable),
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        run = subprocess.run(
            [str(executable)], cwd=ROOT, capture_output=True, text=True, check=True
        )
    assert run.stderr.strip() == "GENERIC_PIXEL_LOCAL_BETA pass=1"
