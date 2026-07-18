#!/usr/bin/env python3
"""Regression test for the bounded DG PF16 actual-AEX store audit."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_olmdistancegradation_pf16_store_boundary_20260718 as audit  # noqa: E402


def main() -> int:
    report = audit.run()
    matches = report["facts"]["actual_aex_matches_all"]
    assert matches["trunc"] is True
    assert matches["half_up"] is False
    assert matches["nearest_even"] is False
    assert report["claims"]["ae_exact_claim"] is False
    assert report["facts"]["production_source_changed"] is False
    print("PASS_OLMDISTANCEGRADATION_PF16_STORE_BOUNDARY_ACTUAL_AEX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
