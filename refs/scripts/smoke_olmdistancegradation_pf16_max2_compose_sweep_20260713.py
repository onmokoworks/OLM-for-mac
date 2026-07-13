#!/usr/bin/env python3
"""Smoke-check the bounded DG PF16 max-2 compose report contract."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/emulation/test_olmdistancegradation_pf16_max2_compose_sweep_20260713.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_16bpc_max2_compose_sweep_20260713.json"


def main() -> int:
    ast.parse(TOOL.read_text(encoding="utf-8"))
    source = TOOL.read_text(encoding="utf-8")
    for token in ("FUN_181170480", "n-1", "n+1", "floor(word * 255 / 32768)", "round-half-up", "Windows-live-field"):
        assert token in source or token in REPORT.read_text(encoding="utf-8"), token

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "pass_bounded_actual_aex"
    assert report["binary"]["calls"] == 12
    assert len(report["points"]) == 4
    assert all(len(item["neighborhood"]) == 3 for item in report["points"])
    assert report["claims_boundary"] == {
        "windows_live_field_values": False,
        "ae_exact": False,
        "broad_png_tuning": False,
        "production_source_changed": False,
    }
    quant = report["case0026_store_export_recalculation"]
    assert quant["classified_count"] == 3
    assert quant["unresolved_points"] == [[907, 222]]
    assert quant["fact_3_of_4_classified_and_only_907_222_unresolved"] is True
    print("smoke_olmdistancegradation_pf16_max2_compose_sweep_20260713=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
