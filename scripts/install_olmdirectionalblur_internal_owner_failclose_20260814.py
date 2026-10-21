#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur internal-owner fail-close fix."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_internal_boundary_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_internal_owner_failclose_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "7859c0ab395f25f92f6dc6dd601b06c1cb23780355537fd8037d4d65fc9f5d16"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_internal_owner_failclose_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_internal_owner_failclose_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "4364163ea6fe47faa44888d83b78078f0cc624419461b176b1b651aa4c0a111e"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "78175545ab184c764ba71f43cdb3b738fff1621302c280b6a8840463ddf2f91e"
installer.OLD_SHA256 = "e0bba034e29a1c50e2db7b1cbb2a7ff00280ea6f9b7d46bb326d5b0f9ffcb1f4"
installer.NEW_SHA256 = "0bc5d3a679fe4a79477042fde8aee6f724c72e1ce4ce8fc189b6cac60bc657c4"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.internal-owner-failclose-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
