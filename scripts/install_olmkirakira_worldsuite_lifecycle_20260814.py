#!/usr/bin/env python3
"""Two-phase transactional install for the bounded Kira WorldSuite candidate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/install_olmkirakira_fp_contract_incremental_20260813.py"
SPEC = importlib.util.spec_from_file_location("kira_incremental_installer_base", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load Kira incremental installer base")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

base.HANDOFF = ROOT / "handoffs/olmkirakira_worldsuite_lifecycle_install_20260814"
base.CANDIDATE = ROOT / "handoffs/olmkirakira_worldsuite_lifecycle_candidate_20260814/Product/OLMKiraKira.plugin"
base.BUILD_IDENTITY = ROOT / "handoffs/olmkirakira_worldsuite_lifecycle_candidate_20260814/build_identity.json"
base.STAGED = base.MEDIACORE / ".OLMKiraKira.plugin.codex-worldsuite-stage"
base.FAILED_NEW = base.MEDIACORE / ".OLMKiraKira.plugin.codex-worldsuite-failed"
base.BACKUP = base.HANDOFF / "installed_backup/OLMKiraKira.plugin"
base.PRE_SWAP = base.HANDOFF / "pre_swap_original/OLMKiraKira.plugin"
base.MOVED_OLD = base.HANDOFF / "moved_old/OLMKiraKira.plugin"
base.PRE_IDENTITY = base.HANDOFF / "olm_installed_identity_manifest_before.json"
base.POST_IDENTITY = base.HANDOFF / "olm_installed_identity_manifest_after.json"
base.PREPARED = base.HANDOFF / "prepared_install.json"
base.TRANSACTION = base.HANDOFF / "install_transaction.json"

base.SOURCE_SHA = "f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2"
base.OLD_SHA = "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18"
base.NEW_SHA = "edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7"
base.PRE_IDENTITY_SHA = "b186a6448dc68f3d117617962237f0ff56087c99530f7823b1cb97abfdd872a3"
base.BUILD_IDENTITY_SHA = "95de37e83599eb629d2ae405adc5d2a3835a3ba5cc30ea4b3008544b59bdbad6"


if __name__ == "__main__":
    try:
        raise SystemExit(base.main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_WORLDSUITE_INSTALL: {exc}", file=__import__("sys").stderr)
        raise
