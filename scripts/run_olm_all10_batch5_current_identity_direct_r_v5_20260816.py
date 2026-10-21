#!/usr/bin/env python3
"""One-shot v5 path for the existing direct ``After Effects -r`` smoke."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/run_olm_all10_batch5_current_identity_direct_r_v4_20260816.py"
SPEC = importlib.util.spec_from_file_location("olm_batch5_direct_r_v4", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load the v4 smoke implementation")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

BASE.RUNNER = Path(__file__).resolve()
BASE.RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v5_fresh_ae_smoke_raw_20260816.json"
BASE.SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v5_fresh_ae_smoke_20260816.json"
BASE.ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_direct_r_v5_fresh_ae_smoke_20260816"
BASE.INVOCATION_RECEIPT = BASE.ARTIFACT_DIR.with_name(BASE.ARTIFACT_DIR.name + ".invocation-receipt.json")


if __name__ == "__main__":
    raise SystemExit(BASE.main())
