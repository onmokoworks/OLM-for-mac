#!/usr/bin/env python3
"""Smoke-test the DistanceGradation case_0023 plateau transition report."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    path = root / "refs/conformance/olmdistancegradation_16bpc_case0023_plateau_transition_20260701.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_16bpc_case0023_plateau_transition"
    assert data["case_id"] == "olmdistancegradation_extended__case_0023"
    assert data["current_constant"]["residual_px"] >= data["trunc_plateau_binary"]["residual_px"]
    buckets = {f"{row['inside_distance']:.6f}": row for row in data["bucket_transition"]}
    assert "1.000000" in buckets
    assert any(row["delta_count"] != 0 for row in data["bucket_transition"])
    print("[OK] DistanceGradation case_0023 plateau transition smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
