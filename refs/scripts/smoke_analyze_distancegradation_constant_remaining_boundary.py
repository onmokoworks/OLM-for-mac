#!/usr/bin/env python3
"""Smoke-test the OLMDistanceGradation Constant remaining boundary report."""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    path = root / "refs/conformance/olmdistancegradation_16bpc_constant_remaining_boundary_20260629.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_16bpc_constant_remaining_boundary"
    rows = data["rows"]
    assert len(rows) == 4
    for row in rows:
        assert row["nonzero_px"] > 0
        assert row["active_within_1_0"] == row["nonzero_px"]
    assert "distanceTransform threshold" in data["conclusion"]
    print("[OK] DistanceGradation Constant remaining boundary smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
