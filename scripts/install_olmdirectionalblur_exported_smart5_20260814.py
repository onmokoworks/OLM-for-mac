#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur exported-Smart five-cell promotion."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_exported_smart5_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_exported_smart5_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "ba1e5c7d9e16a1ef50e164ed0c896e5ca5f820204d7f43209e68f10a610fae7f"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_exported_smart5_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_exported_smart5_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "484b423d3536f5a4b4365f78771f8416ddda0cadb58f5be72ac0c1e9f1aff931"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "5b41b7e787884611634d05771a71a1c8874a5b1a75af93c39bc8cd3c0147f799"
installer.OLD_SHA256 = "0bc5d3a679fe4a79477042fde8aee6f724c72e1ce4ce8fc189b6cac60bc657c4"
installer.NEW_SHA256 = "2863d86f8000f8e014d5a58cefb86291d7c25400075b3b803e696d5490f1f701"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.exported-smart5-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
