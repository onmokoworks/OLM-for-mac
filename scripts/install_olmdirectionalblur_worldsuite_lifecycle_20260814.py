#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur WorldSuite-safe candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_worldsuite_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_worldsuite_lifecycle_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "a77f3a5d91787984ca4f1bb4bcffddbea5cb35f71ca12ac31953ed8f30b972e1"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_worldsuite_lifecycle_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_worldsuite_lifecycle_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "8e75d0a799b7b796c8f2cb63c8553df127ccc87d5868e2b0cb0b72a62b404de6"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "daf51a17a553f13fbd3eb82a44b60099acd25eabd0fe14911a23a87ebfd65f1f"
installer.OLD_SHA256 = "9b5fc6b3d78adc7b5b8ccabdaa30247731e1f2918fb2a977ecf88c2c951d2eff"
installer.NEW_SHA256 = "6af1f1d6d67cd8087778b3040f913e34836092b283ad9f8f36dce2fe32767434"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.worldsuite-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
