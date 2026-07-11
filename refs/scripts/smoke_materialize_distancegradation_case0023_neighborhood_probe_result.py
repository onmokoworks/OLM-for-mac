#!/usr/bin/env python3
"""Smoke test for the OLMDistanceGradation case_0023 neighborhood probe result."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    out_json = ROOT / "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.json"
    out_md = ROOT / "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/materialize_distancegradation_case0023_neighborhood_probe_result.py",
            "--stamp",
            "20260707",
        ],
        cwd=ROOT,
        check=True,
    )
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_case0023_neighborhood_probe_result"
    assert data["points_count"] == 18
    assert data["debug_fields_match_between_bg_modes"] is True
    assert data["shade_stores_match_mac_png"] is True
    assert data["shade_source_matches_input_png"] is True
    assert data["comparisons"]["win_bg_on_vs_mac_bg_on"]["nonzero_px"] == 73
    assert data["comparisons"]["win_bg_off_vs_mac_bg_off"]["nonzero_px"] == 73
    assert data["mismatch_points"]["bg_on"] == [[415, 393], [1699, 7]]
    assert data["mismatch_points"]["bg_off"] == [[415, 393], [1699, 7]]
    text = out_md.read_text(encoding="utf-8")
    assert "Mismatch Points" in text
    assert "Shade source matches input PNG: `True`" in text
    assert "bg_on: (415,393), (1699,7)" in text
    print("ok: OLMDistanceGradation case_0023 neighborhood probe result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
