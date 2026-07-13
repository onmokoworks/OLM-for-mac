#!/usr/bin/env python3
"""Smoke-check the DG 16bpc livefield/source actual-AEX manifest."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/emulation/test_olmdistancegradation_16bpc_livefield_source_actual_aex.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json"


def main() -> int:
    source = TOOL.read_text(encoding="utf-8")
    ast.parse(source)
    for token in (
        "field_raw_words_agrb",
        "source_raw_words_agrb_exact",
        "no_exact_livefield_replays",
        "derive missing field words from PNGs",
    ):
        assert token in source, token

    if REPORT.exists():
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        assert data["schema"] == "olmdistancegradation-livefield-source-actual-aex/1"
        assert data["status"] in {"no_exact_livefield_replays", "replayed_exact_livefield_inputs"}
        summary = {item["case_id"]: item for item in data["family_summary"]}
        assert summary["case_0024"]["located_live_trace_points"] == 0
        assert summary["case_0025"]["located_live_trace_points"] == 0
        assert summary["case_0027"]["located_live_trace_points"] == 0
        assert summary["case_0026"]["located_live_trace_points"] == 4
        assert summary["case_0026"]["exact_replayable_points"] == 0
        assert "field_raw_words_agrb" in summary["case_0026"]["missing_for_exact_replay"]
        candidates = data["point_candidates"]
        assert len(candidates) == 4
        first = candidates[0]
        assert first["case_id"] == "case_0026"
        assert first["source_raw_words_agrb_exact"] == [65535, 65535, 0, 10794]
        assert first["field_raw_words_agrb"] is None
    print("smoke_olmdistancegradation_16bpc_livefield_source_actual_aex=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
