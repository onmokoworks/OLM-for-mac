#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur test-seam-compatible candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_testseam_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_testseam_compat_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "1ae637d09701656113d938273486631d596c2c619f02f57a67a85ad34e8073a7"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "15185edc77645fe47a829a1373abd2c2a9907cc87257bc91e5e01fb00deb8e2a"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845"
installer.OLD_SHA256 = "6af1f1d6d67cd8087778b3040f913e34836092b283ad9f8f36dce2fe32767434"
installer.NEW_SHA256 = "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.testseam-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
