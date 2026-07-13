#!/usr/bin/env python3
"""Validate the actual-AEX Gaussian output capture or its exact blocker."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["schema"] == "olmkirakira-mode3-gaussian-output-actual-aex/1"
    execution = report["execution"]
    assert execution["entry"] == "0x181272ec0"
    assert execution["caller_return"] == "0x181151105"
    assert execution["input_shape"] == [7, 9]
    assert execution["input_nonzero"] is True
    assert execution["entry_hit_count"] >= 1
    if report["status"] == "captured":
        assert execution["return_hit_count"] >= 1
        mat = report["output_capture"]["output_array_after"]["mat"]
        assert mat["word_count"] == 63
        assert len(mat["words_u32"]) == 63
        assert mat["nonzero_word_count"] > 0
        print("smoke_olmkirakira_mode3_gaussian_output_actual_aex=captured")
    else:
        assert report["status"] == "blocked"
        blocker = report["blocker"]
        assert blocker["base_error"] or blocker["last_rip"]
        print("smoke_olmkirakira_mode3_gaussian_output_actual_aex=blocked-with-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
