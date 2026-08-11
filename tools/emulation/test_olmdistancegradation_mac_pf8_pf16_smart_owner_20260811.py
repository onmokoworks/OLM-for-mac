#!/usr/bin/env python3
"""Prove SmartRender dispatches PF8/PF16 through the parameterized full owner."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/dg_mac_pf8_pf16_smart_owner_harness_20260811.cpp"
MARKER = "PASS_OLMDISTANCEGRADATION_MAC_PF8_PF16_SMART_FULL_OWNER"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dg_smart_full_owner_") as temporary:
        executable = Path(temporary) / "harness"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O0",
            "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"),
            "-o", str(executable),
        ], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable)], capture_output=True, text=True)
        assert run.returncode == 0, {"stdout": run.stdout, "stderr": run.stderr}
        assert MARKER in run.stdout
        print(run.stdout, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
