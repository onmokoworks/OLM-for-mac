#!/usr/bin/env python3
"""Smoke-test the rejected OLMDistanceGradation Layer/no-bg unpremultiply report."""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    path = root / "refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_16bpc_rejected_layer_unpremultiply"
    rows = {row["variant"]: row for row in data["rows"]}
    rejected = rows["rejected_layer_unpremultiply_cached_before_restart"]
    reverted = rows["reverted_after_ae_restart"]
    assert rejected["nonzero_px"] > reverted["nonzero_px"]
    assert rejected["mean_abs_diff"] > reverted["mean_abs_diff"]
    assert reverted["nonzero_px"] == 25421
    assert "binary/runtime proof" in data["conclusion"]
    print("[OK] DistanceGradation rejected Layer/no-bg unpremultiply smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
