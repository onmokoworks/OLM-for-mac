#!/usr/bin/env python3
"""Audit the retained OLMKiraKira Smart incremental-install identity.

The default invocation is read-only.  It validates checked-in evidence against
the current source/build/staging/install/retained-pre-install bytes and metadata.
Only an explicit ``--write`` regenerates the JSON and Markdown reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoff/mac_plugin_backups/mediacore_20260812_kira_smart_before_install"
SOURCE_BUNDLE = ROOT / "mac/OLMKiraKira/Mac/build/Debug/OLMKiraKira.plugin"
STAGED_BUNDLE = HANDOFF / "staged/OLMKiraKira.plugin"
INSTALLED_BUNDLE = (
    Path.home()
    / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin"
)
RETAINED_INSTALLED_BUNDLE = HANDOFF / "installed/OLMKiraKira.plugin"
PRE_SWAP_ORIGINAL_BUNDLE = HANDOFF / "pre_swap_original/OLMKiraKira.plugin"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_20260806.json"
POST_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
PBXPROJ = ROOT / "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj"
HIGHLIGHT_HEADER = ROOT / "core/kirakira_highlight.h"
WORKSPACE_MANIFEST = ROOT / "refs/conformance/olmkirakira_smart_workspace_dependency_manifest_20260812.json"
BUILD_LOG = HANDOFF / "xcodebuild_macos11.log"
SMOKE = ROOT / "refs/conformance/olm_all10_post_kira_smart_fresh_ae_smoke_20260812.json"
SMOKE_RAW = ROOT / "refs/conformance/olm_all10_post_kira_smart_fresh_ae_smoke_raw_20260812.json"
SMOKE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
SMOKE_JSX = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
SMOKE_AE_RETURN = ROOT / "handoffs/olm_all10_post_kira_smart_fresh_ae_smoke_20260812/ae_return.json"
REPORT = ROOT / "refs/conformance/olmkirakira_smart_incremental_install_identity_20260812.json"
DOC = REPORT.with_suffix(".md")

SOURCE_SHA = "f2e285be7e6caae764bef7c4fa4a6c422bd5312368ba3481022b9eabe9035492"
PBXPROJ_SHA = "81b2d4246a5dac6f0d8579cb545a7fd9ab201ee63d42a07ccfe544404aff4e4f"
HIGHLIGHT_HEADER_SHA = "e98232e4224b6ae4dd372216e10c29f3ba6621f68ab6cb10b56a02b9cc248390"
WORKSPACE_MANIFEST_SHA = "f57094013568922da6055a718a77c08f33b9ba70437e5ee3c345b7cd42aff94c"
BUILD_LOG_SHA = "77077280531ac224f0c80cf665eaa01d2da268c7ccf496eba4f527b3cd196769"
OLD_SHA = "a09cffa91eb9a022493808ecbc92606a6827f1f0e79ddfc9674a8e9919e3dffc"
NEW_SHA = "69da64666478b25957aa268f6bb6fbc869c3d50b61759f9ca00172045afb5194"
PRE_IDENTITY_SHA = "44e1dca88bb9413ca28e86792fcf9b7d5b48f71a6b770f35bd414897f5bc0061"
POST_IDENTITY_SHA = "1ad14c2f9c9fe1732ec6155ab49d33a479e8ce6c881c56d626f6a6881f8fefea"
SMOKE_SHA = "7f3ea689a5dd4e9b9c9f86a13f6a983f7000c1cb54596589b811d0726a8d8fd9"
SMOKE_RAW_SHA = "bed310c1fe564243572c6801bf4a0f03d31f8a71fbea5494ce5d97b4391cddbe"
SMOKE_RUNNER_SHA = "35fa2ecde4299dd9084ed1c89e50f20fd5ee016477cf18c9a460e696ddd6d459"
SMOKE_JSX_SHA = "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511"
SMOKE_AE_RETURN_SHA = "f87bb1a8d14017f24a0f16692554916c5e23797409692823b4e3bf83d4fc1176"
GENERATED_AT = "2026-08-12T13:00:56.725008+00:00"
PLUGIN = "OLMKiraKira"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
BUNDLE_PATHS = (
    ("source", SOURCE_BUNDLE),
    ("staged", STAGED_BUNDLE),
    ("installed", INSTALLED_BUNDLE),
    ("retained_installed_backup", RETAINED_INSTALLED_BUNDLE),
    ("pre_swap_original", PRE_SWAP_ORIGINAL_BUNDLE),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_or_absolute(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def binary(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMKiraKira"


def bundle_manifest(bundle: Path) -> list[dict[str, object]]:
    assert bundle.is_dir(), bundle
    rows: list[dict[str, object]] = []
    paths = sorted(
        [bundle, *bundle.rglob("*")],
        key=lambda item: item.relative_to(bundle).as_posix(),
    )
    for path in paths:
        info = path.lstat()
        name = "." if path == bundle else path.relative_to(bundle).as_posix()
        row: dict[str, object] = {"path": name, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update({"type": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            row["type"] = "directory"
        elif path.is_file():
            row.update({"type": "file", "bytes": info.st_size, "sha256": sha(path)})
        else:
            raise AssertionError(f"unsupported bundle entry: {path}")
        rows.append(row)
    return rows


def minimum_versions(executable: Path, architectures: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for architecture in architectures:
        result = run("otool", "-arch", architecture, "-l", str(executable))
        assert result.returncode == 0, result.stderr
        matches = re.findall(r"^\s+minos\s+(\S+)\s*$", result.stdout, re.MULTILINE)
        assert len(matches) == 1, (architecture, matches)
        versions[architecture] = matches[0]
    return versions


def live_bundle(bundle: Path) -> dict[str, object]:
    executable = binary(bundle)
    assert executable.is_file(), executable
    arch_result = run("lipo", "-archs", str(executable))
    assert arch_result.returncode == 0, arch_result.stderr
    architectures = arch_result.stdout.split()
    signature = run("codesign", "--verify", "--deep", "--strict", str(bundle))
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    return {
        "path": rel_or_absolute(bundle),
        "binary_sha256": sha(executable),
        "architectures": architectures,
        "universal_exact": set(architectures) == {"arm64", "x86_64"},
        "strict_codesign": signature.returncode == 0,
        "deployment": {
            "info_plist_minimum_system_version": info.get("LSMinimumSystemVersion"),
            "macho_slice_minimum_versions": minimum_versions(executable, architectures),
        },
        "manifest": bundle_manifest(bundle),
    }


def installed_bundle_count() -> int:
    return len([path for path in INSTALLED_BUNDLE.parent.rglob("OLMKiraKira.plugin") if path.is_dir()])


def ae_pids() -> list[int]:
    result = run(
        "pgrep", "-f",
        r"^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects( |$)",
    )
    assert result.returncode in (0, 1)
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def build_evidence() -> dict[str, object]:
    text = BUILD_LOG.read_text(encoding="utf-8", errors="strict")
    project_text = PBXPROJ.read_text(encoding="utf-8", errors="strict")
    compiled = sorted(set(re.findall(
        r"^CompileC .*?/OLMKiraKira\.o .*?/OLMKiraKira\.cpp normal (arm64|x86_64) ",
        text,
        re.MULTILINE,
    )))
    linked = sorted(set(re.findall(
        r"^Ld .*?/Binary/OLMKiraKira normal (arm64|x86_64) ",
        text,
        re.MULTILINE,
    )))
    return {
        "path": rel_or_absolute(BUILD_LOG),
        "sha256": sha(BUILD_LOG),
        "build_succeeded_marker": "** BUILD SUCCEEDED **" in text,
        "compiled_architectures": compiled,
        "linked_architectures": linked,
        "warning_marker_line_count": sum("warning:" in line for line in text.splitlines()),
        "error_marker_line_count": sum("error:" in line for line in text.splitlines()),
        "project_macosx_deployment_target_11_exact_occurrences": project_text.count(
            "MACOSX_DEPLOYMENT_TARGET = 11.0;"
        ),
    }


def identity_transition() -> dict[str, object]:
    pre = json.loads(PRE_IDENTITY.read_text(encoding="utf-8"))
    post = json.loads(POST_IDENTITY.read_text(encoding="utf-8"))
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    assert set(pre_rows) == set(post_rows) == PLUGINS
    changed: dict[str, list[str]] = {}
    for name in sorted(PLUGINS):
        fields = sorted(
            key for key in set(pre_rows[name]) | set(post_rows[name])
            if pre_rows[name].get(key) != post_rows[name].get(key)
        )
        if fields:
            changed[name] = fields
    top_level_changed = sorted(
        key for key in set(pre) | set(post)
        if key != "plugins" and pre.get(key) != post.get(key)
    )
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "top_level_changed_fields": top_level_changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "old_executable_sha256": pre_rows[PLUGIN]["sha256"],
        "new_executable_sha256": post_rows[PLUGIN]["sha256"],
    }


def retained_smoke_evidence() -> dict[str, object]:
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    rows = {row["plugin"]: row for row in smoke["plugins"]}
    kira = rows[PLUGIN]
    assert smoke["schema"] == "olm.all10-current-install-fresh-ae-smoke/1"
    assert smoke["status"] == "pass" and smoke["passed"] is True
    assert set(rows) == PLUGINS and len(smoke["plugins"]) == 10
    assert all(row["status"] == "pass" for row in smoke["plugins"])
    return {
        "observation_only": True,
        "report_path": rel_or_absolute(SMOKE),
        "report_sha256": sha(SMOKE),
        "raw_report_sha256": sha(SMOKE_RAW),
        "runner_sha256": sha(SMOKE_RUNNER),
        "payload_jsx_sha256": sha(SMOKE_JSX),
        "ae_return_sha256": sha(SMOKE_AE_RETURN),
        "all_ten_passed": True,
        "plugin_count": len(smoke["plugins"]),
        "kira": {
            "accepted_executable_sha256": kira["accepted_executable_sha256"],
            "installed_executable_sha256": kira["installed_executable_sha256"],
            "post_render_on_disk_sha256": kira["post_render_on_disk_sha256"],
            "loaded": kira["loaded"],
            "loaded_module_count": kira["loaded_module_count"],
            "post_render_mapping_exact": kira["post_render_mapping_exact"],
            "effect_disabled_during_host_frame": kira["effect_disabled_during_host_frame"],
            "effect_enabled_host_frame_attempted": kira["effect_enabled_host_frame_attempted"],
            "effect_enabled_numerical_render_attempted": kira["effect_enabled_numerical_render_attempted"],
            "numerical_render_expected": kira["numerical_render_expected"],
            "numerical_render_supported": kira["numerical_render_supported"],
            "numerical_render_succeeded": kira["numerical_render_succeeded"],
        },
        "claim_boundary": (
            "Retained post-install AE smoke proves all-ten load/add/mapping observations; "
            "OLMKiraKira used an effect-disabled host frame and did not attempt or support "
            "a numerical render. It is not OLMKiraKira Smart numerical AE exact evidence."
        ),
    }


def generate() -> dict[str, object]:
    return {
        "schema": "olmkirakira.smart-incremental-install-identity/1",
        "status": "PASS_RECOVERABLE_KIRA_ONLY_INSTALL_IDENTITY",
        "generated_at": GENERATED_AT,
        "claim_boundary": (
            "Observed recoverable build/stage/MediaCore identity transition for only OLMKiraKira, "
            "plus separately retained all-ten AE load/add/mapping smoke; no OLMKiraKira Smart "
            "numerical AE exact claim and no install, AE launch, render, or build performed by this audit"
        ),
        "production_source_sha256": sha(SOURCE),
        "project_sha256": sha(PBXPROJ),
        "highlight_header_sha256": sha(HIGHLIGHT_HEADER),
        "workspace_dependency_manifest_sha256": sha(WORKSPACE_MANIFEST),
        "co_bound_input_boundary": (
            "The highlight header and Smart workspace dependency manifest are current hash-bound "
            "inputs/evidence; the retained build transcript does not independently record their content hashes"
        ),
        "pre_identity_manifest_sha256": sha(PRE_IDENTITY),
        "accepted_identity_manifest_sha256": sha(POST_IDENTITY),
        "after_effects_processes_at_audit": ae_pids(),
        "installed_bundle_count": installed_bundle_count(),
        "inventory_scope": {
            "captured": ["path", "entry_type", "posix_mode", "file_size", "file_sha256", "symlink_target"],
            "not_claimed": ["mtime", "extended_attributes"],
        },
        "build_evidence": build_evidence(),
        "bundles": {name: live_bundle(path) for name, path in BUNDLE_PATHS},
        "identity_transition": identity_transition(),
        "observed_retention": {
            "canonical_source_staged_current_installed_full_bundle_exact": True,
            "retained_installed_backup_pre_swap_original_full_bundle_exact": True,
            "retained_pre_install_bytes_and_metadata_present": True,
            "transaction_method_or_order_inferred": False,
        },
        "retained_post_install_ae_smoke": retained_smoke_evidence(),
    }


def validate(report: dict[str, object]) -> None:
    assert set(report) == {
        "schema", "status", "generated_at", "claim_boundary", "production_source_sha256",
        "project_sha256", "highlight_header_sha256", "workspace_dependency_manifest_sha256",
        "co_bound_input_boundary", "pre_identity_manifest_sha256", "accepted_identity_manifest_sha256",
        "after_effects_processes_at_audit", "installed_bundle_count", "inventory_scope", "build_evidence", "bundles",
        "identity_transition", "observed_retention", "retained_post_install_ae_smoke",
    }
    assert report == generate()

    assert report["production_source_sha256"] == SOURCE_SHA
    assert report["project_sha256"] == PBXPROJ_SHA
    assert report["highlight_header_sha256"] == HIGHLIGHT_HEADER_SHA
    assert report["workspace_dependency_manifest_sha256"] == WORKSPACE_MANIFEST_SHA
    assert report["build_evidence"] == {
        "path": rel_or_absolute(BUILD_LOG),
        "sha256": BUILD_LOG_SHA,
        "build_succeeded_marker": True,
        "compiled_architectures": ["arm64", "x86_64"],
        "linked_architectures": ["arm64", "x86_64"],
        "warning_marker_line_count": 348,
        "error_marker_line_count": 0,
        "project_macosx_deployment_target_11_exact_occurrences": 2,
    }
    assert report["pre_identity_manifest_sha256"] == PRE_IDENTITY_SHA
    assert report["accepted_identity_manifest_sha256"] == POST_IDENTITY_SHA
    assert report["after_effects_processes_at_audit"] == []
    assert report["installed_bundle_count"] == 1
    assert report["inventory_scope"] == {
        "captured": ["path", "entry_type", "posix_mode", "file_size", "file_sha256", "symlink_target"],
        "not_claimed": ["mtime", "extended_attributes"],
    }

    bundles = report["bundles"]
    assert set(bundles) == {name for name, _ in BUNDLE_PATHS}
    assert bundles["source"]["binary_sha256"] == NEW_SHA
    assert bundles["staged"]["binary_sha256"] == NEW_SHA
    assert bundles["installed"]["binary_sha256"] == NEW_SHA
    assert bundles["source"]["manifest"] == bundles["staged"]["manifest"] == bundles["installed"]["manifest"]
    assert bundles["retained_installed_backup"]["binary_sha256"] == OLD_SHA
    assert bundles["pre_swap_original"]["binary_sha256"] == OLD_SHA
    assert bundles["retained_installed_backup"]["manifest"] == bundles["pre_swap_original"]["manifest"]
    assert all(row["universal_exact"] and row["strict_codesign"] for row in bundles.values())
    for name in ("source", "staged", "installed"):
        assert bundles[name]["deployment"] == {
            "info_plist_minimum_system_version": "11.0",
            "macho_slice_minimum_versions": {"arm64": "11.0", "x86_64": "11.0"},
        }

    assert report["identity_transition"] == {
        "changed_plugins": [PLUGIN],
        "changed_fields": {PLUGIN: ["sha256", "source_sha256"]},
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "unchanged_plugins": sorted(PLUGINS - {PLUGIN}),
        "old_executable_sha256": OLD_SHA,
        "new_executable_sha256": NEW_SHA,
    }
    smoke = report["retained_post_install_ae_smoke"]
    assert smoke["report_sha256"] == SMOKE_SHA
    assert smoke["raw_report_sha256"] == SMOKE_RAW_SHA
    assert smoke["runner_sha256"] == SMOKE_RUNNER_SHA
    assert smoke["payload_jsx_sha256"] == SMOKE_JSX_SHA
    assert smoke["ae_return_sha256"] == SMOKE_AE_RETURN_SHA
    assert set(smoke["kira"].values()) <= {NEW_SHA, True, False, 1, None}
    assert smoke["kira"] == {
        "accepted_executable_sha256": NEW_SHA,
        "installed_executable_sha256": NEW_SHA,
        "post_render_on_disk_sha256": NEW_SHA,
        "loaded": True,
        "loaded_module_count": 1,
        "post_render_mapping_exact": True,
        "effect_disabled_during_host_frame": True,
        "effect_enabled_host_frame_attempted": False,
        "effect_enabled_numerical_render_attempted": False,
        "numerical_render_expected": False,
        "numerical_render_supported": False,
        "numerical_render_succeeded": None,
    }
    assert DOC.read_text(encoding="utf-8") == expected_doc()


def expected_doc() -> str:
    return (
        "# OLMKiraKira Smart incremental install identity\n\n"
        "Status: **PASS_RECOVERABLE_KIRA_ONLY_INSTALL_IDENTITY**. The canonical source bundle, "
        "retained staged bundle, and current sole MediaCore bundle are exact within the recorded "
        "inventory scope at "
        f"`{NEW_SHA}`. The retained handoff installed snapshot and `pre_swap_original` are "
        f"exact within that scope at `{OLD_SHA}`. The scope records paths, entry types, POSIX modes, "
        "file sizes and SHA-256 values, and symlink targets; mtimes and extended attributes are not claimed. "
        "The accepted identity transition changes only OLMKiraKira `sha256`/`source_sha256`, plus the "
        "top-level `accepted_at` and `installed_after` timestamps; the other nine plugin rows are exact.\n\n"
        "The production source, project, material highlight header, and frozen Smart workspace dependency "
        "manifest are co-bound by current hashes. The retained build transcript does not independently "
        "record the header or dependency-manifest content hashes. The hash-bound build log records "
        "`BUILD SUCCEEDED` and compile/link evidence for both arm64 and x86_64. It also retains 348 "
        "warning-marker lines and zero error-marker lines; this is not a warning-clean claim. The "
        "hash-bound project contains exactly two macOS 11.0 deployment-target settings. Canonical "
        "deployment metadata is macOS 11.0 in Info.plist and both Mach-O slices; all observed bundles "
        "are Universal and pass strict codesign verification. The retained all-ten post-install AE smoke "
        "is separately bound and records OLMKiraKira load/mapping at the new hash, but its host frame was "
        "effect-disabled and no numerical render was attempted or supported. It is not Smart numerical "
        "AE exact evidence.\n\n"
        "Transaction wording is intentionally limited to the retained bytes and scoped metadata now "
        "observed. No copy/swap method or ordering is inferred. This audit performs no install, AE "
        "launch/render, or build.\n"
    )


def write(report: dict[str, object]) -> None:
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(expected_doc(), encoding="utf-8")
    validate(report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Explicitly regenerate JSON and Markdown.")
    args = parser.parse_args()
    if args.write:
        write(generate())
    else:
        validate(json.loads(REPORT.read_text(encoding="utf-8")))
    print("PASS_OLMKIRAKIRA_SMART_INCREMENTAL_INSTALL_IDENTITY_20260812")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
