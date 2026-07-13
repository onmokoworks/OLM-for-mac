#!/usr/bin/env python3
"""Regression smoke for the actual-AEX OLMBlur PF16 writer and case_0006 stores."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITER_RUNNER = ROOT / "tools/emulation/test_olmblur_writer16_half_ties_20260713.py"
CASE0006_REPORT = ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(WRITER_RUNNER)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    writer = json.loads(completed.stdout)

    # The first pair distinguishes actual CVTTSS2SI-style add-half/truncate
    # from nearest-even; the third keeps the 16-bit upper-bound clamp covered.
    require(writer["status"] == "pass_actual_aex_distinguishes_half_ties", "writer probe did not pass")
    require(writer["input_raw_f32"] == [1100.5, 1101.5, 32767.5], "writer probe inputs drifted")
    require(writer["stored_agrb16"] == [32768, 1101, 1102, 32768], "actual-AEX half-tie stores drifted")
    require(writer["add_half_then_truncate_rgb"] == [1101, 1102, 32768], "add-half/truncate oracle drifted")
    require(writer["nearest_even_rgb"] == [1100, 1102, 32768], "nearest-even discriminator drifted")
    require(writer["binary_sha256"] == AEX_SHA256, "writer probe AEX hash drifted")

    case0006 = json.loads(CASE0006_REPORT.read_text(encoding="utf-8"))
    require(case0006["identity"]["aex_sha256"] == AEX_SHA256, "case_0006 AEX hash drifted")
    final = case0006["comparison"]["final"]
    require(final["(314,14)"]["actual_stored_rgb_words"] == [2201, 2201, 2201], "case_0006 (314,14) store drifted")
    require(final["(29,71)"]["actual_stored_rgb_words"] == [727, 727, 727], "case_0006 (29,71) store drifted")

    print("[OK] OLMBlur actual-AEX PF16 half-tie and case_0006 store regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
