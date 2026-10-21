#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur fixed Type3 Layer promotion."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_type3_layer_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_type3_layer_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "b316ca630efa464a00e5e02becc4bdbd2a69095e89a71c1581b194b79b079b4c"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_type3_layer_universal_candidate_20260814/Product.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_type3_layer_universal_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "14b810d138096532f02ef78d5de584275b33bc4f483d6166e2a89ecc9f06cb98"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "82b2b4f2d669f439ecd055d3f26844260d3b500aec873d1d4e8ce752ea70c068"
installer.OLD_SHA256 = "3528d12c38f4618c203d8851c1a0efcf7eafa7bfbf1a40bc4f5a31b767b122a7"
installer.NEW_SHA256 = "9b5fc6b3d78adc7b5b8ccabdaa30247731e1f2918fb2a977ecf88c2c951d2eff"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.type3-layer-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
