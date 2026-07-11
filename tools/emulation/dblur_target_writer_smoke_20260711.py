#!/usr/bin/env python3
"""Validate the compact DirectionalBlur target-writer witness contract."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WITNESS = ROOT / "refs/conformance/dblur_target_writer_capture_20260711.json"
REQUIRED = {
    "target_xy", "source_xy", "destination_B_address", "direction",
    "callsite_return", "pre_B_rgba", "post_B_rgba", "pre_denom",
    "post_denom", "pre_valid", "post_valid", "target_write_addresses",
}


def main() -> int:
    raw = WITNESS.read_text(encoding="utf-8")
    assert len(raw.splitlines()) < 500
    assert len(raw.encode("utf-8")) < 50_000
    assert "/Users/" not in raw
    data = json.loads(WITNESS.read_text(encoding="utf-8"))
    assert data["kind"] == "dblur_target_writer_capture"
    assert data["status"] == "ok"
    assert data["source_coordinate_policy"] == "discover_actual_helper_contributors; source_959_not_forced"
    assert data["aex"]["path"] == "plugins_2025/OLMDirectionalBlur.aex"
    summary = data["summary"]
    assert summary["target_writer_call_count"] == 845
    expected = {"494": 465, "579": 380}
    for target, call_count in expected.items():
        item = summary[target]
        assert item["helper_call_count"] == call_count
        assert item["source_x_count"] == call_count
        assert item["unique_directions"] == [1]
        assert item["unique_spans"] == [1064]
        assert item["target_write_count"] == call_count * 4
        assert item["source_nonzero_event_count"] == 0
        assert item["pre_B_nonzero_event_count"] == 0
        assert item["post_B_nonzero_event_count"] == 0
        assert item["first_B_change_event"] is None
        assert item["B_change_events_capped"] == []
        assert len(item["first_representative_calls"]) <= 8
        assert len(item["last_representative_calls"]) <= 8
        for record in item["first_representative_calls"] + item["last_representative_calls"]:
            assert REQUIRED - {"target_xy"} <= record.keys()
            assert record["source_xy"][1] == 169
            assert record["direction"] == 1
            assert record["target_write_addresses"]
    assert summary["494"]["source_x_range"] == [495, 959]
    assert summary["579"]["source_x_range"] == [580, 959]
    assert summary["494"]["final_B_rgba"] == [0.0, 0.0, 0.0, 1.0]
    assert summary["579"]["final_B_rgba"] == [0.0, 0.0, 0.0, 1.0]
    print(json.dumps({"status": "pass", "json_bytes": os.path.getsize(WITNESS),
                      "json_lines": len(raw.splitlines()), "helper_calls": 845,
                      "by_target": expected}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
