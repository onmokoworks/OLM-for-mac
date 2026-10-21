#!/usr/bin/env python3
"""Post-install/rollback audit for the RadialBlur WorldSuite lifecycle fix."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/audit_olmradialblur_current_incremental_install_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_install_audit_base", BASE)
assert SPEC and SPEC.loader
impl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(impl)

impl.INSTALLER = ROOT / "scripts/install_olmradialblur_worldsuite_lifecycle_20260814.py"
impl.INSTALLER_SHA = "8bdd3e750d57011d1d45541e8e58ea9618222ce2a42d0201115c68fb3b08d393"
impl.TRANSACTION_SHA = "22fce8b993d6ec3c8285433e83a54775c7738f71da0a697638cdedbb7e8ff78a"
impl.POST_IDENTITY_SHA = "b186a6448dc68f3d117617962237f0ff56087c99530f7823b1cb97abfdd872a3"
impl.REPORT = ROOT / "refs/conformance/olmradialblur_worldsuite_lifecycle_install_20260814.json"
impl.DOC = impl.REPORT.with_suffix(".md")
impl.DOC_TEXT = """# OLMRadialBlur WorldSuite lifecycle incremental install

Verdict: `PASS_RADIAL_CURRENT_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED`.

Source `b74b3d2c…fdb0d1` and Universal minOS 11 candidate/installed executable
`9be59d18…676b5` are full-inventory exact. The predecessor `1b29b5ea…643c`
remains in three full-inventory-exact rollback copies. Only the Radial identity
row and the two top-level timestamps changed; the other nine rows are exact.

Two all-ten preflights are byte-identical and observe no After Effects process.
This is an installed identity and rollback closure. Native-AE smoke remains
deferred to a later batched checkpoint.
"""


def load_installer_impl():
    spec = importlib.util.spec_from_file_location("radial_worldsuite_installer", impl.INSTALLER)
    assert spec and spec.loader
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    return wrapper.impl


impl.installer = load_installer_impl


if __name__ == "__main__":
    raise SystemExit(impl.main())
