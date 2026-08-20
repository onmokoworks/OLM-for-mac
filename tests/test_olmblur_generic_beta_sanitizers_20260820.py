"""Compile and execute the OLMBlur generic production path hostlessly."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmblur_generic_beta_sanitized_20260820.cpp"
SOURCES = [
    "mac/OLMBlur/OLMBlur_Strings.cpp", "Util/AEGP_SuiteHandler.cpp",
    "Util/MissingSuiteError.cpp", "core/olmblur_helper.cpp",
    "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker16_nonlegacy.cpp",
    "core/olmblur_worker16_legacy.cpp", "core/olmblur_worker32_nonlegacy.cpp",
    "core/olmblur_worker32_legacy.cpp", "core/olmblur_worker8_legacy.cpp",
    "core/olmblur_worker_orchestration.cpp",
]


def compile_probe(directory: Path, sanitize: bool) -> Path:
    executable = directory / "olmblur_generic"
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True
    ).stdout.strip()
    command = [
        "clang++", "-std=c++17", "-O1" if sanitize else "-O2", "-g",
        "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1", "-fno-fast-math",
        "-ffp-contract=off", "-Wno-pragma-pack", "-Wno-deprecated-declarations",
        "-isysroot", sdk,
    ]
    if sanitize:
        command += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
    for include in ("Headers", "Headers/SP", "Util", "Resources", "core",
                    "mac/OLMBlur", "tools/emulation"):
        command += ["-I", str(ROOT / include)]
    command += [str(PROBE), *[str(ROOT / source) for source in SOURCES],
                "-framework", "Cocoa", "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    return executable


def run_probe(executable: Path, geometry: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(executable), geometry], cwd=ROOT, text=True, capture_output=True,
        env={**os.environ, "ASAN_OPTIONS": "halt_on_error=1",
             "UBSAN_OPTIONS": "halt_on_error=1"}, check=False,
    )


def test_olmblur_generic_production_sanitizers() -> None:
    sanitize = os.environ.get("OLM_BLUR_SANITIZE", "1") != "0"
    geometry = os.environ.get("OLM_PERF_GEOMETRY", "odd")
    with tempfile.TemporaryDirectory(prefix="olmblur-generic-") as raw:
        run = run_probe(compile_probe(Path(raw), sanitize), geometry)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "runtime error:" not in run.stderr
    expected = 7 if geometry == "hd" else (6 if geometry in {"odd", "uhd"} else 4)
    assert run.stdout.count(" ok=1 ") == expected, run.stdout


if __name__ == "__main__":
    test_olmblur_generic_production_sanitizers()
