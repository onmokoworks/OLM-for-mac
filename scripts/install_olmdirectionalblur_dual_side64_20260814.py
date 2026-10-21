#!/usr/bin/env python3
"""Two-phase transaction for the source-bound DirectionalBlur dual-side64 candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_transaction_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_dual_side64_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "c56a25298870d8aff5c9dfeef8f5229cb448160688e3121fcb0b186947c129d2"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_dual_side64_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_dual_side64_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "26f11f351587fcc0c0a5f897781a33a7c815ac748822bec4aa0352bfb640ab91"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "bd329d362a05ef3683a892e533c80900861f89b91ed4f83019b7f44c4fe7a6cf"
installer.OLD_SHA256 = "371c3b624c42d81d67f0e140f14f75d23dcfba302fbca716407902046d2cd0f0"
installer.NEW_SHA256 = "e0bba034e29a1c50e2db7b1cbb2a7ff00280ea6f9b7d46bb326d5b0f9ffcb1f4"

def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.dual64-stage-20260814",
    }

installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
