"""Compile and run the portable OLMBlur 32bpc Legacy replay."""

from pathlib import Path
import subprocess
import tempfile


def test_worker32_legacy_replay() -> None:
    root = Path(__file__).resolve().parents[2]
    fixture_root = Path(__file__).parent / "fixtures" / "olmblur_worker32_legacy"
    with tempfile.TemporaryDirectory() as temp:
        binary = Path(temp) / "replay"
        subprocess.run([
            "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
            "core/olmblur_fullworker_helper.cpp",
            "core/olmblur_worker32_legacy.cpp",
            "tools/emulation/replay_olmblur_worker32_legacy.cpp",
            "-o", str(binary),
        ], cwd=root, check=True)
        subprocess.run([str(binary), str(fixture_root)], cwd=root, check=True)
