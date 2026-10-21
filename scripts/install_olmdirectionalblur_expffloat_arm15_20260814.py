#!/usr/bin/env python3
"""Two-phase transaction for the DirectionalBlur arm64 15-cell expf promotion."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("directional_expffloat_arm15_base", BASE)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

installer.NAME = "OLMDirectionalBlur"
installer.HANDOFF = ROOT / "handoffs/olmdirectionalblur_expffloat_arm15_install_20260814"
installer.IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
installer.EXPECTED_PRE_IDENTITY = "25cbff11edbb247b9f0d93fa5a6ef881df02c93824c128f9e0da740ee9f8e229"
installer.PRE_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_before.json"
installer.POST_IDENTITY = installer.HANDOFF / "olm_installed_identity_manifest_after.json"
installer.PREPARED = installer.HANDOFF / "prepared_transaction.json"
installer.TRANSACTION = installer.HANDOFF / "install_transaction.json"
installer.CANDIDATE = ROOT / "handoffs/olmdirectionalblur_expffloat_arm15_universal_candidate_20260814/Product/OLMDirectionalBlur.plugin"
installer.AUTHORITY = ROOT / "handoffs/olmdirectionalblur_expffloat_arm15_universal_candidate_20260814/build_identity.json"
installer.AUTHORITY_SHA256 = "c692c8fac4e25f1cfbe0e3e9b90a957b51913ae3c0a742ef3555a89b307ee7c2"
installer.SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
installer.SOURCE_SHA256 = "754db0d2500209db69dfd87d950dea7f900f7287ec25fddfe3c02d1b71af6ff2"
installer.OLD_SHA256 = "4e238ac00e75f294efb60ee50d25d633586c691dc69bcb5a6292221f27e04d77"
installer.NEW_SHA256 = "3528d12c38f4618c203d8851c1a0efcf7eafa7bfbf1a40bc4f5a31b767b122a7"


def directional_paths():
    return {
        "installed": installer.base.MEDIA_CORE / "OLMDirectionalBlur.plugin",
        "backup": installer.HANDOFF / "installed_backup/OLMDirectionalBlur.plugin",
        "pre_swap": installer.HANDOFF / "pre_swap_original/OLMDirectionalBlur.plugin",
        "moved_old": installer.HANDOFF / "moved_old/OLMDirectionalBlur.plugin",
        "failed_new": installer.HANDOFF / "failed_new/OLMDirectionalBlur.plugin",
        "stage": installer.base.MEDIA_CORE / ".OLMDirectionalBlur.expffloat-arm15-stage-20260814",
    }


installer.paths = directional_paths

if __name__ == "__main__":
    raise SystemExit(installer.main())
