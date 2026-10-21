#!/usr/bin/env python3
"""Two-phase transaction for the final 35-pair RadialBlur Type3 candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_transaction_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.HANDOFF = ROOT / "handoffs/olmradialblur_type3_35_pair_install_20260813"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "c6ebb4cdb39eeecb569f35a969df7e1bd1ff54e3bcfedef87fab9f16d2ec5850"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmradialblur_type3_35_pair_candidate_20260813/Product/OLMRadialBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmradialblur_type3_35_pair_candidate_20260813/build_identity.json"
installer.AUTHORITY_SHA256 = "a083703f380503c82a7329ef3e101202d3fbb22f426a9f82b0e373dbb36b5300"
installer.SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
installer.SOURCE_SHA256 = "f4930b60f0ef31572b682156a0327e0abf2f29158cc722c606f0e3cefc761d6e"
installer.OLD_SHA256 = "d50934aa86a452f43990143af286930d8999c8ef5f82374fff5fb41a1522773e"
installer.NEW_SHA256 = "ce5b57e17e7e58157d308f3c853b2f5dce49c8012bee1ef71a1d978757ba0e7a"

if __name__ == "__main__":
    raise SystemExit(installer.main())
