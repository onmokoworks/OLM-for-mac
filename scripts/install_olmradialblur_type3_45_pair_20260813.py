#!/usr/bin/env python3
"""Two-phase transaction for the final 45-pair RadialBlur Type3 candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_transaction_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.HANDOFF = ROOT / "handoffs/olmradialblur_type3_45_pair_install_20260813"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "7be33d88077c3ba90f7d9eeb73c156b0de53ac173d6bb46b5a15d46b0155fce3"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmradialblur_type3_45_pair_candidate_20260813/Product/OLMRadialBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmradialblur_type3_45_pair_candidate_20260813/build_identity.json"
installer.AUTHORITY_SHA256 = "e9a45dfb386a3d5902ca34430ab488df31de5d34068cf2dc939a90530e648a04"
installer.SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
installer.SOURCE_SHA256 = "efb54d652e60e83efa12e3522a2181d6f58beb90df85ff662d20acfb1e3c480b"
installer.OLD_SHA256 = "ce5b57e17e7e58157d308f3c853b2f5dce49c8012bee1ef71a1d978757ba0e7a"
installer.NEW_SHA256 = "1b29b5eaa97421c87ea1091c2efc7f7a8ad2866722d91e6b48adb2a6b610643c"

if __name__ == "__main__":
    raise SystemExit(installer.main())
