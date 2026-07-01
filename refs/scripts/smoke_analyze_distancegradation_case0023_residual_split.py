#!/usr/bin/env python3
"""Smoke-test the DistanceGradation case_0023 residual split report."""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    path = root / "refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_16bpc_case0023_residual_split"
    assert data["residual_px"] == 73
    buckets = {round(row["inside_distance"], 6): row for row in data["inside_distance_buckets"]}
    assert round(1.0, 6) in buckets
    assert round(36.013885498046875, 6) in buckets
    assert buckets[1.0]["count"] == 65
    assert buckets[round(36.013885498046875, 6)]["count"] == 8
    assert buckets[1.0]["outside_distance_values"] == [0.0]
    assert buckets[round(36.013885498046875, 6)]["outside_distance_values"] == [0.0]
    pairs = data["candidate_to_reference_endpoint_pairs"]
    assert pairs["7195,0,61165,65535 -> 65535,0,0,65535"] == 65
    assert pairs["65535,0,0,65535 -> 7195,0,61165,65535"] == 8
    print("[OK] DistanceGradation case_0023 residual split smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
