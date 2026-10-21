#!/usr/bin/env python3
"""Read-only auditor for the OLMToonDilate ded9 transactional install plan."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmtoondilate_ded9_incremental_install_20260813"
INSTALLER = ROOT / "scripts/install_olmtoondilate_ded9_incremental_20260813.py"
BUILD_IDENTITY = HANDOFF / "build_identity.json"
REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_transactional_install_readiness_20260813.json"
DOC = REPORT.with_suffix(".md")
SUPERSESSION_REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_transactional_install_readiness_supersession_20260813.json"
SUPERSESSION_DOC = SUPERSESSION_REPORT.with_suffix(".md")
POST_AUDITOR = ROOT / "tools/emulation/audit_olmtoondilate_ded9_incremental_install_identity_20260813.py"
POST_REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"

SOURCE_SHA = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"
PROJECT_SHA = "eba3266a1dba3f50b217463c5bb077e9976b22febe70bfb7c5d05c6bdaca8abc"
OLD_SHA = "fe0a4959a677eb495f290fc384d93a2da4b66119f07bd8d1e5dac0847f95c5e9"
NEW_SHA = "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e"
PRE_IDENTITY_SHA = "869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90"
BUILD_IDENTITY_SHA = "17623fdb49e0dbca5acf37ae1461bce3d2ae65acdbcbcdb62e19d42b6c440f76"
INSTALLER_SHA = "4c31138980c4bface0e7e91d50063aff8c90577d26ec21d83a6ff49e3d232b26"
BUILD_GO = "GO_OLMTOONDILATE_DED9_PREPARE_READY_NO_MUTATION"
INSTALL_GO = "GO_OLMTOONDILATE_DED9_INSTALL_READY_PREPARED_NO_MUTATION"
POST_IDENTITY_SHA = "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"
HISTORICAL_REPORT_SHA = "ba374e2b3a3415bf06caa4622493ee95505b987c102caa591c0178bcacbf04c4"
HISTORICAL_DOC_SHA = "21ee24faaebe19d553d4733cedaf33f9023dcf1e977b3d94e1249aef79a1e2c5"
POST_AUDITOR_SHA = "558080e0148f8538e5abbe7ae0d99b2a1be48899fff3576a0b9b342a59ca1d98"
POST_REPORT_SHA = "39536c468aa358884984f5a22fca759aaa94958e0430b55776e42da50f0aef2d"
SUPERSEDED = "PASS_OLMTOONDILATE_DED9_PREPARED_READINESS_SUPERSEDED_BY_POST_INSTALL_IDENTITY"
CLAIM = (
    "Read-only readiness for an explicit future OLMToonDilate-only transaction: frozen "
    "candidate and current predecessor identity, complete scoped inventories, rollback plan, "
    "same-volume staging, renameatx_np(RENAME_SWAP), and the projected ten-plugin identity "
    "transition. No --install invocation, filesystem installation mutation, AE launch/load/UI/render, "
    "Developer ID, notarization, distribution, or post-install identity claim."
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("olmtoon_ded9_installer", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_evidence() -> dict[str, object]:
    payload = json.loads(BUILD_IDENTITY.read_text(encoding="utf-8"))
    assert sha(BUILD_IDENTITY) == BUILD_IDENTITY_SHA
    assert payload["source_guard"]["production_source"]["sha256"] == SOURCE_SHA
    assert payload["source_guard"]["project_file"]["sha256"] == PROJECT_SHA
    assert payload["artifact"]["signed_binary_sha256"] == NEW_SHA
    assert payload["artifact"]["architectures"] == ["x86_64", "arm64"]
    assert payload["artifact"]["plist_minimum_system_version"] == "11.0"
    assert payload["artifact"]["signature"] == {
        "kind": "adhoc",
        "cdhash": "4cce48186a315684e1bc34a34a25fcb146117d6b",
        "strict_deep_verify": True,
    }
    assert all(
        payload["artifact"]["slices"][arch]["lc_build_version"]["minos"] == "11.0"
        and payload["artifact"]["slices"][arch]["required_exports"]
        == ["_EffectMain", "_PluginDataEntryFunction2"]
        for arch in ("arm64", "x86_64")
    )
    return {
        "path": "handoffs/olmtoondilate_ded9_incremental_install_20260813/build_identity.json",
        "sha256": BUILD_IDENTITY_SHA,
        "created_at_jst": payload["created_at_jst"],
        "configuration": payload["build"]["configuration"],
        "build_result": payload["build"]["result"],
        "architectures": payload["artifact"]["architectures"],
        "plist_minimum_system_version": payload["artifact"]["plist_minimum_system_version"],
        "slice_minimum_versions": {
            arch: payload["artifact"]["slices"][arch]["lc_build_version"]["minos"]
            for arch in ("x86_64", "arm64")
        },
        "required_exports": {
            arch: payload["artifact"]["slices"][arch]["required_exports"]
            for arch in ("x86_64", "arm64")
        },
        "signature": payload["artifact"]["signature"],
        "bundle_inventory_sha256": payload["bundle_inventory_sha256"],
    }


def generate_readiness() -> dict[str, object]:
    assert sha(INSTALLER) == INSTALLER_SHA
    installer = load_installer()
    preflight = installer.collect_preflight(require_state="either")
    state = preflight["transaction_artifact_state"]
    assert state in {"clean", "prepared"}
    assert preflight["status"] == (
        "dry_run_install_ready_prepared_no_mutation"
        if state == "prepared" else "dry_run_prepare_ready_no_mutation"
    )
    assert preflight["production_source_sha256"] == SOURCE_SHA
    assert preflight["project_sha256"] == PROJECT_SHA
    assert preflight["pre_identity_sha256"] == PRE_IDENTITY_SHA
    assert preflight["old_binary_sha256"] == OLD_SHA
    assert preflight["new_binary_sha256"] == NEW_SHA
    assert preflight["after_effects_processes"] == []
    prepared = installer.validate_prepared(preflight) if state == "prepared" else None
    assert preflight["candidate"]["manifest"] != preflight["installed_before"]["manifest"]
    assert preflight["candidate"]["binary_sha256"] == NEW_SHA
    assert preflight["installed_before"]["binary_sha256"] == OLD_SHA
    build = build_evidence()
    report: dict[str, object] = {
        "schema": "olmtoondilate.ded9-transactional-install-readiness/1",
        "status": INSTALL_GO if state == "prepared" else BUILD_GO,
        "generated_from_frozen_build_at": build["created_at_jst"],
        "claim_boundary": CLAIM,
        "production_source_sha256": SOURCE_SHA,
        "project_sha256": PROJECT_SHA,
        "build_identity_sha256": BUILD_IDENTITY_SHA,
        "installer_sha256": INSTALLER_SHA,
        "pre_identity_manifest_sha256": PRE_IDENTITY_SHA,
        "old_installed_executable_sha256": OLD_SHA,
        "candidate_executable_sha256": NEW_SHA,
        "default_installer_mode": "read-only dry-run validation",
        "only_mediacore_or_accepted_identity_mutating_cli_flag": "--install",
        "prepare_cli_flag": "--prepare",
        "prepare_cleanup_cli_flag": "--cleanup-prepare",
        "install_flag_executed": False,
        "after_effects_operation_performed": False,
        "preflight": preflight,
        "authoritative_build_evidence": build,
        "prospective_identity_transition": preflight["identity_transition"],
        "prepared_install_evidence": prepared,
        "transaction_plan": {
            "before_bundle_mutation": [
                "exact pre-identity byte copy",
                "installed_backup full bundle inventory copy",
                "pre_swap_original full bundle inventory copy",
                "preinstall inventory manifest",
            ],
            "stage_location": str(installer.STAGED),
            "stage_is_installed_bundle_sibling": installer.STAGED.parent == installer.INSTALLED.parent,
            "same_volume_verified": True,
            "bundle_exchange": "renameatx_np(RENAME_SWAP)",
            "success_retains_moved_old_third_copy": True,
            "failure_restores_predecessor_bundle": True,
            "failure_restores_exact_pre_identity_bytes": True,
            "identity_write": "same-directory atomic os.replace",
            "manifest_and_bundle_single_atomic_primitive": False,
            "prepare_reexecution": "idempotent only after exact live prepared-artifact revalidation",
            "prepare_failure_cleanup": "automatic removal of only pre-swap preparation outputs",
            "manual_prepare_cleanup": "--cleanup-prepare refuses unless predecessor install and identity remain exact and no post-prepare artifact exists",
        },
        "build_and_prepare_go_conditions": {
            "source_and_project_frozen": True,
            "candidate_full_inventory_observed": True,
            "candidate_universal_exact": True,
            "candidate_macos11_exact": True,
            "candidate_strict_codesign_valid": True,
            "candidate_required_exports_exact": True,
            "predecessor_full_inventory_observed": True,
            "accepted_preidentity_exact": True,
            "toon_row_only_projected": True,
            "other_nine_rows_projected_exact": True,
            "top_level_timestamp_fields_only_projected": True,
            "clean_or_exact_prepared_state": True,
            "after_effects_not_running": True,
            "explicit_prepare_or_install_execution_still_required": True,
        },
        "install_go_conditions": {
            "prepared_artifacts_present": state == "prepared",
            "installed_backup_full_inventory_exact": prepared is not None,
            "pre_swap_original_full_inventory_exact": prepared is not None,
            "pre_identity_exact_and_current": prepared is not None,
            "preinstall_manifest_exact": prepared is not None,
            "candidate_and_predecessor_reverified": prepared is not None,
            "post_prepare_artifacts_absent": prepared is not None,
        },
    }
    validate_semantics(report)
    return report


def validate_semantics(report: dict[str, Any]) -> None:
    assert report["schema"] == "olmtoondilate.ded9-transactional-install-readiness/1"
    assert report["status"] in {BUILD_GO, INSTALL_GO}
    assert report["claim_boundary"] == CLAIM
    assert report["production_source_sha256"] == SOURCE_SHA
    assert report["project_sha256"] == PROJECT_SHA
    assert report["build_identity_sha256"] == BUILD_IDENTITY_SHA
    assert report["installer_sha256"] == INSTALLER_SHA
    assert report["pre_identity_manifest_sha256"] == PRE_IDENTITY_SHA
    assert report["old_installed_executable_sha256"] == OLD_SHA
    assert report["candidate_executable_sha256"] == NEW_SHA
    assert report["default_installer_mode"] == "read-only dry-run validation"
    assert report["only_mediacore_or_accepted_identity_mutating_cli_flag"] == "--install"
    assert report["prepare_cli_flag"] == "--prepare"
    assert report["prepare_cleanup_cli_flag"] == "--cleanup-prepare"
    assert report["install_flag_executed"] is False
    assert report["after_effects_operation_performed"] is False
    state = report["preflight"]["transaction_artifact_state"]
    assert state in {"clean", "prepared"}
    assert report["preflight"]["transaction_artifacts_absent"] is (state == "clean")
    assert report["preflight"]["after_effects_processes"] == []
    assert report["prospective_identity_transition"] == {
        "changed_plugins": ["OLMToonDilate"],
        "changed_fields": {
            "OLMToonDilate": ["sha256", "source_bundle", "source_sha256"],
        },
        "unchanged_plugins": [
            "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
            "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
            "OLMSmoother", "OLMSmoother2",
        ],
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "other_nine_rows_exact": True,
    }
    assert report["transaction_plan"] == {
        "before_bundle_mutation": [
            "exact pre-identity byte copy",
            "installed_backup full bundle inventory copy",
            "pre_swap_original full bundle inventory copy",
            "preinstall inventory manifest",
        ],
        "stage_location": str(load_installer().STAGED),
        "stage_is_installed_bundle_sibling": True,
        "same_volume_verified": True,
        "bundle_exchange": "renameatx_np(RENAME_SWAP)",
        "success_retains_moved_old_third_copy": True,
        "failure_restores_predecessor_bundle": True,
        "failure_restores_exact_pre_identity_bytes": True,
        "identity_write": "same-directory atomic os.replace",
        "manifest_and_bundle_single_atomic_primitive": False,
        "prepare_reexecution": "idempotent only after exact live prepared-artifact revalidation",
        "prepare_failure_cleanup": "automatic removal of only pre-swap preparation outputs",
        "manual_prepare_cleanup": "--cleanup-prepare refuses unless predecessor install and identity remain exact and no post-prepare artifact exists",
    }
    assert all(report["build_and_prepare_go_conditions"].values())
    if state == "prepared":
        assert report["status"] == INSTALL_GO
        assert report["prepared_install_evidence"] is not None
        assert all(report["install_go_conditions"].values())
    else:
        assert report["status"] == BUILD_GO
        assert report["prepared_install_evidence"] is None
        assert not any(report["install_go_conditions"].values())


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMToonDilate ded9 transactional install readiness — 2026-08-13\n\n"
        f"Status: **{report['status']}**. The frozen source `{SOURCE_SHA}`, project `{PROJECT_SHA}`, "
        f"and isolated Universal macOS 11 candidate `{NEW_SHA}` are exact. The currently "
        f"installed predecessor is `{OLD_SHA}` and the accepted ten-plugin pre-identity is "
        f"`{PRE_IDENTITY_SHA}`.\n\n"
        "The installer is read-only by default. `--prepare` records the exact pre-identity, two "
        "full-inventory predecessor copies, and a preinstall inventory while asserting MediaCore "
        "and accepted identity remain exact. Only `--install` mutates those targets, and it refuses "
        "to proceed unless every prepared artifact is independently revalidated. It then stages "
        "beside MediaCore, verifies the staged inventory, "
        "uses `renameatx_np(RENAME_SWAP)`, and retains the exchanged predecessor as the third "
        "`moved_old` copy. Failure restores the predecessor bundle and exact pre-identity bytes.\n\n"
        "The projected accepted-manifest change is limited to the OLMToonDilate row fields "
        "`sha256`, `source_bundle`, and `source_sha256`, plus top-level `accepted_at` and "
        "`installed_after`; the other nine rows remain exact.\n\n"
        "No `--install` invocation or After Effects operation was performed. A clean-state report "
        "is GO only for `--prepare`; install GO is emitted only after live prepared-artifact audit. "
        "This is not a post-install, AE load/render, Developer ID, notarization, distribution, "
        "or release claim. Bundle exchange and identity replacement are separate atomic operations.\n"
    )


def validate_readiness(report: dict[str, Any]) -> None:
    expected = generate_readiness()
    assert report == expected
    assert DOC.read_text(encoding="utf-8") == markdown(expected)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def post_installed() -> bool:
    return IDENTITY.is_file() and sha(IDENTITY) == POST_IDENTITY_SHA


def validate_historical_readiness() -> dict[str, Any]:
    assert sha(REPORT) == HISTORICAL_REPORT_SHA
    assert sha(DOC) == HISTORICAL_DOC_SHA
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    validate_semantics(report)
    assert report["status"] == INSTALL_GO
    assert report["preflight"]["transaction_artifact_state"] == "prepared"
    assert all(report["install_go_conditions"].values())
    assert DOC.read_text(encoding="utf-8") == markdown(report)
    return report


def generate_supersession() -> dict[str, object]:
    historical = validate_historical_readiness()
    assert post_installed()
    assert sha(POST_AUDITOR) == POST_AUDITOR_SHA
    assert sha(POST_REPORT) == POST_REPORT_SHA
    post_module = load_module(POST_AUDITOR, "olmtoon_ded9_post_authority")
    post_report = json.loads(POST_REPORT.read_text(encoding="utf-8"))
    post_module.validate(post_report)
    assert post_report["status"] == post_module.STATUS
    assert post_report["accepted_identity_manifest_sha256"] == POST_IDENTITY_SHA
    return {
        "schema": "olmtoondilate.ded9-transactional-install-readiness/2",
        "status": SUPERSEDED,
        "claim_boundary": (
            "The immutable prepared-state readiness report is retained as historical evidence. "
            "It is no longer evaluated against live pre-install state; current authority is the "
            "bound read-only post-install identity report. No install or AE operation is performed."
        ),
        "historical_prepared_readiness": {
            "path": REPORT.relative_to(ROOT).as_posix(),
            "sha256": HISTORICAL_REPORT_SHA,
            "markdown_sha256": HISTORICAL_DOC_SHA,
            "status": historical["status"],
            "pre_identity_manifest_sha256": PRE_IDENTITY_SHA,
            "candidate_executable_sha256": NEW_SHA,
            "prepared_install_go_conditions_all_true": True,
            "treated_as_live_current_state": False,
        },
        "current_post_install_authority": {
            "auditor_path": POST_AUDITOR.relative_to(ROOT).as_posix(),
            "auditor_sha256": POST_AUDITOR_SHA,
            "report_path": POST_REPORT.relative_to(ROOT).as_posix(),
            "report_sha256": POST_REPORT_SHA,
            "status": post_report["status"],
            "accepted_identity_manifest_sha256": POST_IDENTITY_SHA,
            "installed_executable_sha256": NEW_SHA,
        },
        "install_operation_performed": False,
        "after_effects_operation_performed": False,
    }


def supersession_markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMToonDilate ded9 readiness supersession — 2026-08-13\n\n"
        f"Status: **{SUPERSEDED}**. Prepared-state report `{HISTORICAL_REPORT_SHA}` and its "
        f"Markdown `{HISTORICAL_DOC_SHA}` remain immutable historical evidence. They are not "
        "re-generated as though the pre-install state were still live.\n\n"
        f"Current authority is post-install identity report `{POST_REPORT_SHA}`, which binds "
        f"installed candidate `{NEW_SHA}` and accepted identity `{POST_IDENTITY_SHA}`. The "
        "supersession auditor performs no install or After Effects operation.\n"
    )


def validate_supersession(report: dict[str, Any]) -> None:
    expected = generate_supersession()
    assert report == expected
    assert SUPERSESSION_DOC.read_text(encoding="utf-8") == supersession_markdown(expected)


def generate() -> dict[str, object]:
    return generate_supersession() if post_installed() else generate_readiness()


def validate(report: dict[str, Any]) -> None:
    if post_installed():
        validate_supersession(report)
    else:
        validate_readiness(report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the canonical readiness evidence")
    args = parser.parse_args()
    if post_installed():
        if args.write:
            report = generate_supersession()
            SUPERSESSION_REPORT.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            SUPERSESSION_DOC.write_text(supersession_markdown(report), encoding="utf-8")
            validate_supersession(report)
            print("PASS_OLMTOONDILATE_DED9_TRANSACTIONAL_INSTALL_READINESS_SUPERSESSION_WRITE")
            return 0
        validate_supersession(json.loads(SUPERSESSION_REPORT.read_text(encoding="utf-8")))
        print("PASS_OLMTOONDILATE_DED9_TRANSACTIONAL_INSTALL_READINESS_SUPERSEDED")
        return 0
    if args.write:
        report = generate_readiness()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DOC.write_text(markdown(report), encoding="utf-8")
        validate_readiness(report)
        print("PASS_OLMTOONDILATE_DED9_TRANSACTIONAL_INSTALL_READINESS_WRITE")
        return 0
    validate_readiness(json.loads(REPORT.read_text(encoding="utf-8")))
    print("PASS_OLMTOONDILATE_DED9_TRANSACTIONAL_INSTALL_READINESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
