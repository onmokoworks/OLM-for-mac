#!/usr/bin/env python3
"""Two-phase transaction for the RadialBlur Type1 source-guard batch 4."""

from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_transaction_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.HANDOFF = ROOT / "handoffs/olmradialblur_type1_source_guard_batch4_install_20260813"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "4d0b65792e6ccec43577fac7cde4f78e59180cab72cec36443a7b032fea6a70a"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmradialblur_type1_source_guard_batch4_candidate_20260813/Product/OLMRadialBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmradialblur_type1_source_guard_batch4_candidate_20260813/build_identity.json"
installer.AUTHORITY_SHA256 = "4cd62598eb62d6b33dedd2d1d06153f78cebf784de44e91e7105d5db61d42403"
installer.SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
installer.SOURCE_SHA256 = "44f1e7f964c267601cc0b50f669a1fccdb42b7f33026f4ab41fb556d15bc5acb"
installer.OLD_SHA256 = "da72af556cad862abf8eaa2c5388d82455b1f8d073cb739c97c357e0f1beb859"
installer.NEW_SHA256 = "2934d1367a5fd9d1fead35894271d9adf58ca1e008cab436e0a7d6bbb6f13083"

if __name__ == "__main__":
    raise SystemExit(installer.main())
