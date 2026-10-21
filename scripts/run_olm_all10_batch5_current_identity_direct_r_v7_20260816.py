#!/usr/bin/env python3
"""Deferred Batch5 AE smoke with only DirectionalBlur generically enabled."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/run_olm_all10_batch5_current_identity_direct_r_v4_20260816.py"
SPEC = importlib.util.spec_from_file_location("olm_batch5_direct_r_v4", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load the direct AE smoke implementation")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

BASE.RUNNER = Path(__file__).resolve()
BASE.PAYLOAD = ROOT / "scripts/ae_host_all10_batch5_current_identity_live_v4_20260816.jsx"
BASE.ENABLED_HOST_FRAME_PLUGINS = {"OLMDirectionalBlur"}
BASE.CLAIM_BOUNDARY = "Batch5 installed host load/add/enable-state and exact mapping for all ten; generic effect-enabled host-frame render only for OLMDirectionalBlur. OLMBlur and the other eight bounded effects are disabled before generic saveFrameToPng. Numerical behavior is not assessed. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or public-owner numerical-exact claim."
BASE.RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v7_fresh_ae_smoke_raw_20260816.json"
BASE.SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v7_fresh_ae_smoke_20260816.json"
BASE.ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_direct_r_v7_fresh_ae_smoke_20260816"
BASE.INVOCATION_RECEIPT = BASE.ARTIFACT_DIR.with_name(BASE.ARTIFACT_DIR.name + ".invocation-receipt.json")


if __name__ == "__main__":
    raise SystemExit(BASE.main())
