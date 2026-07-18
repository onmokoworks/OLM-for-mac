#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from audit_olmcolorkey_edge_thin_caller_amount_20260718 import ROOT, run


def main() -> int:
    actual = run()
    fixture = json.loads(
        (ROOT / "refs/conformance/olmcolorkey_edge_thin_caller_amount_20260718.json").read_text(
            encoding="utf-8"
        )
    )
    assert actual == fixture
    assert actual["status"] == "pass"
    assert actual["matrix_counts"] == {"amounts": 7, "comparisons": 54, "distance_types": 3}
    assert actual["distance_dispatch_matrix"] == [
        {"distance_type": 1, "target": "type1"},
        {"distance_type": 2, "target": "type2"},
        {"distance_type": 3, "target": "type3"},
    ]
    assert all(row["exact_int32_to_float32"] for row in actual["amount_conversion_matrix"])
    for row in actual["comparison_matrix"]:
        if row["path"] == "positive":
            assert (row["result"] == "copy") == (row["distance"] <= row["amount"])
        else:
            assert (row["result"] == "zero") == (row["distance"] < abs(row["amount"]))
    print("PASS_OLMCOLORKEY_EDGE_THIN_CALLER_AMOUNT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
