#!/usr/bin/env python3
"""Smoke-test the OLMDistanceGradation Constant binary threshold fix report."""

from __future__ import annotations

import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    path = root / "refs/conformance/olmdistancegradation_16bpc_constant_binary_fix_20260629.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_16bpc_constant_binary_fix"
    changed = {row["case_id"]: row for row in data["changed_cases"]}
    assert changed["olmdistancegradation_extended__case_0020"]["old_nonzero_px"] == 1001
    assert changed["olmdistancegradation_extended__case_0020"]["new_nonzero_px"] == 1
    assert changed["olmdistancegradation_extended__case_0021"]["new_nonzero_px"] == 1
    assert changed["olmdistancegradation_extended__case_0022"]["new_nonzero_px"] == 192
    assert changed["olmdistancegradation_extended__case_0023"]["new_nonzero_px"] == 73
    assert data["exact"] == 1
    assert data["total"] == 16
    print("[OK] DistanceGradation Constant binary threshold fix smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
