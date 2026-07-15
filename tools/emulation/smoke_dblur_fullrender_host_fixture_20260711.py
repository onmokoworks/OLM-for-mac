#!/usr/bin/env python3
"""Validate the bounded complete host-fixture artifact without rerunning AEX."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/dblur_fullrender_host_fixture_20260711.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    execution = report["execution"]
    assert report["kind"] == "dblur_fullrender_host_fixture"
    assert report["schema"] == 1
    assert report["status"] == "ok"
    assert report.get("blocked") is None

    output = report["output"]
    assert output["format"] == "ARGB8"
    assert output["dimensions"] == [960, 540]
    assert output["complete"] is True
    assert output["byte_count"] == 960 * 540 * 4
    assert output["sha256"] == "595f8fea0a1801832a8f6fcb93f836eccdfad96fab8df83c8abd5e0d277afa1a"

    iterate_calls = execution["iterate_calls"]
    assert len(iterate_calls) == 2
    assert [call["callback"] for call in iterate_calls] == ["0x180006980", "0x180006b30"]
    assert all(call["callback_error"] == 0 for call in iterate_calls)
    assert all(call["area_words"] == [0, 0, 960, 540] for call in iterate_calls)
    assert all(call["start"] == 0 and call["end"] == 540 for call in iterate_calls)

    checkpoints = execution["checkpoints"]
    assert checkpoints["first_iterate"]["callback"] == "0x180006980"
    assert checkpoints["rowdriver"]["entry"] == "0x1800038d0"
    assert checkpoints["rotateback"]["callsite"] == "0x180005628"
    assert checkpoints["normalization"]["after_rotateback"] is True
    assert checkpoints["final_host_output"]["callback"] == "0x180006b30"
    assert checkpoints["final_host_output"]["area_words"] == [0, 0, 960, 540]

    rotate_detours = execution["rotate_detours"]
    assert len(rotate_detours) == 2
    assert all(call["dimensions"] == [1104, 1104] for call in rotate_detours)
    assert [call["angle_bits"] for call in rotate_detours] == ["0x3fc90fdb", "0xbfc90fdb"]
    assert report["rotate_detour"]["fixture_gate"] == "6/6 byte-exact against actual AEX"
    assert execution["unimplemented_imports"] == []

    budget = execution["budget"]
    assert budget["instruction_limit"] == 200_000_000
    assert 0 < budget["instructions"] < budget["instruction_limit"]
    assert budget["exhausted"] is False

    # This artifact ends at the modeled host-output boundary. It is not an
    # actual After Effects render comparison and cannot support an AE-exact claim.
    assert report.get("reference_comparison") is None
    print(json.dumps({
        "status": "pass",
        "passed_stage": "final host output",
        "format": output["format"],
        "dimensions": output["dimensions"],
        "iterate_callbacks": [call["callback"] for call in iterate_calls],
        "instructions": budget["instructions"],
        "instruction_limit": budget["instruction_limit"],
        "claim_scope": "bounded host-fixture output; not AE exact",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
