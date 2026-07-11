#!/usr/bin/env python3
"""Smoke test for the OLMDistanceGradation case_0023 Mac probe result."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    out_json = ROOT / "refs/conformance/olmdistancegradation_case0023_mac_probe_result_20260707.json"
    out_md = ROOT / "refs/conformance/olmdistancegradation_case0023_mac_probe_result_20260707.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/materialize_distancegradation_case0023_mac_probe_result.py",
            "--stamp",
            "20260707",
        ],
        cwd=ROOT,
        check=True,
    )
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_case0023_mac_probe_result"
    assert data["debug_points_match_between_bg_modes"] is True
    assert data["comparisons"]["win_bg_on_vs_mac_bg_on"]["nonzero_px"] == 73
    assert data["comparisons"]["win_bg_off_vs_mac_bg_off"]["nonzero_px"] == 73
    assert "not broad field-helper retuning" in data["safe_claim"]
    text = out_md.read_text(encoding="utf-8")
    assert "Debug points match between bg modes: `True`" in text
    assert "win_bg_on_vs_mac_bg_on" in text
    print("ok: OLMDistanceGradation case_0023 Mac probe result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
