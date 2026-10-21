#!/usr/bin/env python3
"""Two-phase transaction for the final 32-pair RadialBlur Type3 candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_transaction_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.HANDOFF = ROOT / "handoffs/olmradialblur_type3_complete_pair_install_20260813"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "3722313db6f77ff1e8ba44ff13a95a66b4a46727f86275d0801b0576048b55ed"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmradialblur_type3_complete_pair_candidate_20260813/Product/OLMRadialBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmradialblur_type3_complete_pair_candidate_20260813/build_identity.json"
installer.AUTHORITY_SHA256 = "0cea554c10ba54f2d18c70b528527be58625a4b29491893ce12db6853a5bc045"
installer.SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
installer.SOURCE_SHA256 = "b2ea7d913720fb361eb3f1a647d5a9f34feb20e0afcd23f679153f967a805cbb"
installer.OLD_SHA256 = "2934d1367a5fd9d1fead35894271d9adf58ca1e008cab436e0a7d6bbb6f13083"
installer.NEW_SHA256 = "d50934aa86a452f43990143af286930d8999c8ef5f82374fff5fb41a1522773e"

if __name__ == "__main__":
    raise SystemExit(installer.main())
