from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[1] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmcolorkey_real_sdk_suite_lifecycle_20260813.cpp"


class ColorKeyRealSdkSuiteLifecycle(unittest.TestCase):
    def test_world_and_color_suite_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olmcolorkey-real-sdk.") as raw:
            executable = Path(raw) / "probe"
            sdk = subprocess.run(
                ["xcrun", "--show-sdk-path"], capture_output=True,
                text=True, check=True,
            ).stdout.strip()
            command = [
                _UCRT_CXX, "-std=c++17", "-arch", "arm64", "-O2",
                "-Wno-pragma-pack", "-Wno-deprecated-declarations",
                "-isysroot", sdk, "-IHeaders", "-IHeaders/SP", "-IUtil",
                "-IResources", "-Imac/OLMColorKey", str(PROBE),
                "mac/OLMColorKey/OLMColorKey_Strings.cpp",
                str(resolve_asset("Util/AEGP_SuiteHandler.cpp")), str(resolve_asset("Util/MissingSuiteError.cpp")),
                "-framework", "Cocoa", "-o", str(executable),
            ]
            subprocess.run(command, cwd=ROOT, check=True)
            run = subprocess.run(
                [str(executable)], cwd=ROOT, text=True,
                capture_output=True, check=True,
            )
        lines = run.stdout.splitlines()
        self.assertEqual(lines[-1], "COLORKEY_REAL_SDK_SUITE_LIFECYCLE_EXACT=1")
        self.assertEqual(len([line for line in lines if line.startswith("WORLD ")]), 6)
        self.assertEqual(len([line for line in lines if line.startswith("COLOR ")]), 6)
        self.assertEqual(len([line for line in lines if line.startswith("PARAM ")]), 67)


if __name__ == "__main__":
    unittest.main()
