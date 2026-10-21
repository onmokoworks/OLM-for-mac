#!/usr/bin/env python3
"""Two-phase transactional install for the RadialBlur WorldSuite fix."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/install_olmradialblur_current_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_install_base", BASE)
assert SPEC and SPEC.loader
impl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(impl)

impl.HANDOFF = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_install_20260814"
impl.EXPECTED_PRE_IDENTITY = "9d7402a37c9e4e5204860b0bcff7efed00708cb469e26a9d422a0c3401775bcd"
impl.PRE_IDENTITY = impl.HANDOFF / "olm_installed_identity_manifest_before.json"
impl.POST_IDENTITY = impl.HANDOFF / "olm_installed_identity_manifest_after.json"
impl.PREPARED = impl.HANDOFF / "prepared_transaction.json"
impl.TRANSACTION = impl.HANDOFF / "install_transaction.json"
impl.CANDIDATE = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/Product/OLMRadialBlur.plugin"
impl.AUTHORITY = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/build_identity.json"
impl.AUTHORITY_SHA256 = "641af05eec81269738fa65d99fcd59bd0d16f1d28f89eb95bbe8f978c5c6bb93"
impl.SOURCE_SHA256 = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
impl.OLD_SHA256 = "1b29b5eaa97421c87ea1091c2efc7f7a8ad2866722d91e6b48adb2a6b610643c"
impl.NEW_SHA256 = "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5"


def paths() -> dict[str, Path]:
    return {
        "installed": impl.base.MEDIA_CORE / "OLMRadialBlur.plugin",
        "backup": impl.HANDOFF / "installed_backup/OLMRadialBlur.plugin",
        "pre_swap": impl.HANDOFF / "pre_swap_original/OLMRadialBlur.plugin",
        "moved_old": impl.HANDOFF / "moved_old/OLMRadialBlur.plugin",
        "failed_new": impl.HANDOFF / "failed_new/OLMRadialBlur.plugin",
        "stage": impl.base.MEDIA_CORE / ".OLMRadialBlur.worldsuite-stage-20260814",
    }


impl.paths = paths


if __name__ == "__main__":
    raise SystemExit(impl.main())
