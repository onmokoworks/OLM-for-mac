#!/usr/bin/env python3
"""Run every current installed bounded public-entry replay without launching AE."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("ColorKeep", "tools/emulation/test_colorkeep_current_installed_complete_union_20260814.py"),
    ("OLMBlur", "tools/emulation/test_olmblur_current_installed_complete_admission_union_20260813.py"),
    ("OLMColorKey", "tools/emulation/test_olmcolorkey_current_installed_public_closure_20260813.py"),
    ("OLMDirectionalBlur", "tools/emulation/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py"),
    ("OLMDistanceGradation", "tools/emulation/test_olmdistancegradation_current_installed_mode5_20260813.py"),
    ("OLMKiraKira", "tools/emulation/test_olmkirakira_current_installed_public_closure_20260813.py"),
    ("OLMRadialBlur", "tools/emulation/test_olmradialblur_current_installed_complete_public_union_20260814.py"),
    ("OLMSmoother", "tools/emulation/test_olmsmoother_v1_current_installed_admission_union_20260813.py"),
    ("OLMSmoother2", "tools/emulation/test_olmsmoother2_current_installed_public_20260813.py"),
    ("OLMToonDilate", "tools/emulation/test_olmtoondilate_current_installed_exact12_20260813.py"),
)


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed for {name}")
        found.extend(f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit())
    return found


def main() -> int:
    initial = ae_processes()
    if initial:
        raise RuntimeError(f"AE-family processes must be stopped: {initial}")
    started = time.monotonic()
    for plugin, path in COMMANDS:
        run = subprocess.run(
            [sys.executable, path], cwd=ROOT, text=True, capture_output=True,
        )
        if run.returncode:
            sys.stderr.write(f"FAIL {plugin}\n{run.stdout}{run.stderr}")
            return run.returncode
        marker = next((line for line in run.stdout.splitlines() if line.startswith("PASS_") or line.startswith("pass_")), None)
        if marker is None:
            raise RuntimeError(f"missing pass marker for {plugin}")
        print(f"PASS {plugin} marker={marker}")
    aggregate = subprocess.run(
        [sys.executable, "scripts/run_olm_all10_installed_public_routes_20260813.py"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if aggregate.returncode:
        sys.stderr.write(aggregate.stdout + aggregate.stderr)
        return aggregate.returncode
    final = ae_processes()
    if final:
        raise RuntimeError(f"AE-family process appeared during hostless checkpoint: {final}")
    print(f"PASS_OLM_ALL10_CURRENT_INSTALLED_PUBLIC_REPLAYS_BOTH_SLICES elapsed={time.monotonic()-started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
