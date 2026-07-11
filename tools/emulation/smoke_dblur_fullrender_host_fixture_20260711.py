#!/usr/bin/env python3
"""Validate the last bounded full-render fixture artifact without rerunning AEX."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/dblur_fullrender_host_fixture_20260711.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    execution = report["execution"]
    assert report["status"] == "blocked"
    assert report["blocked"]["reason"] == "rowdriver-instruction-budget"
    last_rip = int(report["blocked"]["last_rip"], 16)
    assert 0x1800013E0 <= last_rip < 0x180001830
    assert len(execution["iterate_calls"]) == 1
    assert execution["checkpoints"]["first_iterate"]["callback"] == "0x180006980"
    assert execution["checkpoints"]["rowdriver"]["entry"] == "0x1800038d0"
    assert len(execution["rotate_detours"]) == 1
    assert execution["rotate_detours"][0]["dimensions"] == [1104, 1104]
    assert execution["rotate_detours"][0]["angle_bits"] == "0x3fc90fdb"
    assert report["rotate_detour"]["fixture_gate"] == "6/6 byte-exact against actual AEX"
    assert execution["unimplemented_imports"] == []
    assert execution["budget"]["instructions"] == execution["budget"]["instruction_limit"] == 200_000_000
    assert report["output"]["complete"] is False
    assert report["output"]["sha256"] is None
    print(json.dumps({
        "status": "pass",
        "passed_stage": "FUN_180001ec0 rotate-in",
        "blocker": report["blocked"]["reason"],
        "last_rip": report["blocked"]["last_rip"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
