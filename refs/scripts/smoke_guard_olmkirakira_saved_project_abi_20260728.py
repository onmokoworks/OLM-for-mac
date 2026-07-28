#!/usr/bin/env python3
"""Tests for the fail-closed KiraKira saved-project ABI gate."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import guard_olmkirakira_saved_project_abi_20260728 as gate  # noqa: E402


def canonical_rows() -> list[dict[str, object]]:
    return [
        {
            "property_index": row.order,
            "match_name": row.match_name,
            "name": row.name,
            "value": False if row.name == "Use Ramp" else None,
        }
        for row in gate.WINDOWS_ABI
    ]


def main() -> int:
    gate.verify_embedded_abi()
    assert len(gate.WINDOWS_ABI) == 40
    assert Counter(row.kind for row in gate.WINDOWS_ABI) == {
        "mapped": 25, "ramp_label": 5, "ramp_payload": 5, "separator": 5,
    }
    assert [(r.order, r.disk_id) for r in gate.WINDOWS_ABI[:12]] == [
        (1, 8), (2, 9), (3, 17), (4, 10), (5, 2), (6, 11),
        (7, 27), (8, 7), (9, 12), (10, 3), (11, 13), (12, 29),
    ]
    assert [(r.order, r.disk_id) for r in gate.WINDOWS_ABI[-5:]] == [
        (36, 39), (37, 24), (38, 25), (39, 40), (40, 1),
    ]

    safe = gate.gate_saved_project(canonical_rows(), "match_name")
    assert safe["status"] == "accepted", safe
    assert safe["code"] == "safe_match_name_mapping", safe
    assert safe["mapped_count"] == 25, safe
    assert {row["disk_id"] for row in safe["mapped_rows"]} == {
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
        14, 15, 16, 17, 18, 20, 22, 24, 26, 27, 28, 35,
    }

    ramp_rows = canonical_rows()
    next(row for row in ramp_rows if row["match_name"].endswith("-0018"))["value"] = True
    blocked = gate.gate_saved_project(ramp_rows, "match_name")
    assert blocked["code"] == "ramp_payload_unsupported", blocked
    assert blocked["mapped_count"] == 0, blocked

    prefix = [{"property_index": i, "value": 0} for i in range(1, 12)]
    assert gate.gate_saved_project(prefix, "index")["status"] == "accepted"
    after_11 = prefix + [{"property_index": 12, "value": None}]
    assert gate.gate_saved_project(after_11, "index")["code"] == "index_only_after_row_11"
    assert gate.gate_saved_project([], "index")["code"] == "empty_transfer"
    assert gate.gate_saved_project([], "match_name")["code"] == "empty_transfer"
    assert gate.gate_saved_project(
        [{"property_index": 2, "value": 0}], "index"
    )["code"] == "noncanonical_index_prefix"
    assert gate.gate_saved_project(
        [{"property_index": 1}, {"property_index": 1}], "index"
    )["code"] == "noncanonical_index_prefix"
    assert gate.gate_saved_project(
        [{"property_index": 1}, {"property_index": 3}], "index"
    )["code"] == "noncanonical_index_prefix"
    assert gate.gate_saved_project(
        [{"property_index": 1}, {"property_index": 0}], "index"
    )["code"] == "invalid_property_index"
    assert gate.gate_saved_project(
        [{"property_index": 1}, {"property_index": 99}], "index"
    )["code"] == "invalid_property_index"

    missing_identity = canonical_rows()
    del missing_identity[0]["match_name"]
    assert gate.gate_saved_project(missing_identity, "match_name")["code"] == "missing_match_name"

    duplicate_identity = canonical_rows()
    duplicate_identity[1]["match_name"] = duplicate_identity[0]["match_name"]
    assert gate.gate_saved_project(
        duplicate_identity, "match_name"
    )["code"] == "duplicate_match_name"

    unknown_identity = canonical_rows()
    unknown_identity[0]["match_name"] = "OLM OLM Kira Kira-9999"
    assert gate.gate_saved_project(
        unknown_identity, "match_name"
    )["code"] == "unknown_match_name"

    one_match_row = [canonical_rows()[0]]
    assert gate.gate_saved_project(
        one_match_row, "match_name"
    )["code"] == "incomplete_mapped_surface"
    allowed_partial = gate.gate_saved_project(
        one_match_row, "match_name", allow_partial=True
    )
    assert allowed_partial["status"] == "accepted", allowed_partial
    assert allowed_partial["mapped_count"] == 1, allowed_partial

    drift = canonical_rows()
    drift[11]["property_index"] = 13
    assert gate.gate_saved_project(drift, "match_name")["code"] == "windows_abi_order_mismatch"

    print("[OK] OLMKiraKira saved-project ABI/ramp gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
