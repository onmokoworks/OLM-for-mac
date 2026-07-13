#!/usr/bin/env python3
"""Verify the retained OLMBlur case_0006 actual-AEX full-worker evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmblur_case0006_actual_aex_fullworker_20260713.json"
EXPECTED_HASH = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    identity = payload["identity"]
    actual = payload["actual_aex"]
    comparison = payload["comparison"]

    require(identity["aex_sha256"] == EXPECTED_HASH, "AEX hash drifted")
    require(identity["entry"] == "0x180002280", "Non-Legacy entry drifted")
    require(actual["status"] == "return", "actual-AEX worker did not return")
    require(actual["helper_call_count_per_run"] == [120, 120], "helper-call coverage is incomplete")
    require(payload["portable"]["self_check"] is True, "portable worker self-check failed")
    require(comparison["all_observed_stages_portable_exact"] is True, "an observed helper stage differs")
    require(comparison["first_portable_difference"] is None, "unexpected portable difference")

    final = comparison["final"]
    require(final["(314,14)"]["pre_store_exact"] is True, "first pre-store witness differs")
    require(final["(314,14)"]["actual_matches_windows_rgb"] is True, "first Windows final witness differs")
    require(final["(29,71)"]["pre_store_exact"] is True, "second pre-store witness differs")
    require(final["(29,71)"]["actual_stored_rgb_words"] == [727, 727, 727], "second actual store drifted")
    require(final["(29,71)"]["windows_png_rgba16"][:3] == [725, 725, 725], "second Windows reference drifted")
    require(final["(29,71)"]["actual_matches_windows_rgb"] is False, "second provenance split disappeared")
    require(
        comparison["first_windows_internal_difference"] is None,
        "report must not invent a Windows internal boundary without a same-run trace",
    )

    print("[OK] OLMBlur case_0006 actual-AEX full-worker evidence is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
