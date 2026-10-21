#!/usr/bin/env python3
"""Aggregate the ten current installed public-entry hostless closures.

Default operation is read-only.  It regenerates the bounded aggregate from the
live authority and ten persisted public-route reports, then requires the saved
report to be byte-semantically identical.  Use --write only to intentionally
refresh the canonical JSON/Markdown pair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.json"
REPORT = ROOT / "refs/conformance/olm_all10_current_installed_public_routes_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_all10_current_installed_public_routes_20260813.md"
AUTHORITY_SHA256 = "8138180651e805e352fdb6ffd2e91abd426803d7395d949a545e73c421f3e6f9"

EXPECTED: dict[str, dict[str, Any]] = {
    "ColorKeep": {
        "report": "refs/conformance/colorkeep_current_installed_complete_union_20260814.json",
        "report_sha256": "50aafd53a7cbc4309417cf0d9f3a89632e1ffcf36f2e3fdf38b92ae162a0c94a",
        "status": "PASS_COLORKEEP_CURRENT_INSTALLED_COMPLETE_BOUNDED_UNION_AE_FREE",
        "coverage": "both Universal slices: all 10 source-bound legacy count5/100 paths, all 5 count9 paths, 18 legacy source mutations, and 136 count9 rejects per slice",
    },
    "OLMBlur": {
        "report": "refs/conformance/olmblur_current_installed_complete_admission_union_20260813.json",
        "report_sha256": "f49ec2e1ef321c8eab4e9f25ad66ed2c84e30114e2ada0fe862cd3387bb28eb5",
        "status": "PASS_OLMBLUR_CURRENT_INSTALLED_COMPLETE_SMART_ADMISSION_UNION_AE_FREE",
        "coverage": "both Universal slices: complete bounded Smart union PF8 12 + PF16 8 + PF32 20 = 40 exact cells and 1,298 negative controls per slice",
    },
    "OLMColorKey": {
        "report": "refs/conformance/olmcolorkey_current_installed_public_closure_20260813.json",
        "report_sha256": "fbc71bb938d127a430f37665234728468b00e6053312e25239725d1cb14d65a6",
        "status": "PASS_OLMCOLORKEY_CURRENT_INSTALLED_BOTH_SLICES_PUBLIC60_AE_FREE",
        "coverage": "both slices: Classic 60 and Smart 60 bounded cells per slice; 13 callback rejects per slice",
    },
    "OLMDirectionalBlur": {
        "report": "refs/conformance/olmdirectionalblur_current_installed_complete_bounded_union_20260814.json",
        "report_sha256": "f1fd17c51ccd42d0c1491c926e763462a6dfba300690880c92cfb4fa25c002b9",
        "status": "PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_COMPLETE_BOUNDED_UNION_AE_FREE",
        "coverage": "current installed arm64: 33 bounded exact public cells; x86_64: 27 exact and six fail-closed pending native Windows UCRT expf counts 8/50/100; includes dual-side, Natural64 exact-source and Type3 Layer routes",
    },
    "OLMDistanceGradation": {
        "report": "refs/conformance/olmdistancegradation_current_installed_mode5_20260813.json",
        "report_sha256": "98f3b2ecc66a1cb56e105fb7697dca46b1e654f8b66ae3a0596166bced1b2ceb",
        "status": "PASS_OLMDISTANCEGRADATION_CURRENT_INSTALLED_MODE5_6_POWER_FAILCLOSED_8_AE_FREE",
        "coverage": "both Universal slices: fixed PF32 Mode5 6 exact cells and all 8 PF32 Power cells fail closed per slice pending native UCRT powf",
    },
    "OLMKiraKira": {
        "report": "refs/conformance/olmkirakira_current_installed_public_closure_20260813.json",
        "report_sha256": "9bc2b377a99e1391844efe5dccf9c4232f40e38a3e72b55ceedc7d63db29f0cf",
        "status": "PASS_OLMKIRAKIRA_CURRENT_INSTALLED_PUBLIC_42_765_3_AE_FREE",
        "coverage": "both Universal slices: 42 bounded public positives, 765 negatives, and 3 full-request controls per slice",
    },
    "OLMRadialBlur": {
        "report": "refs/conformance/olmradialblur_current_installed_complete_public_union_20260814.json",
        "report_sha256": "083bdaf45321bba8753627cb479bc5499d80077ba570262dd744d203fd3dee18",
        "status": "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_COMPLETE_TYPE1_TYPE3_PUBLIC_UNION_AE_FREE",
        "coverage": "both Universal slices: complete bounded public union of 106 exact-source Type1 cells plus all 45 fixed 9x7 Type3 source/Layer pairs per slice; 57 Type1 mutation rejects and 45 Type3 reject-control sets per slice",
    },
    "OLMSmoother": {
        "report": "refs/conformance/olmsmoother_v1_current_installed_admission_union_20260813.json",
        "report_sha256": "34d66834c08ff265b8760ec84f2b2595023ca3ed9120582726f97e3d10c3963a",
        "status": "PASS_OLMSMOOTHER_V1_CURRENT_INSTALLED_COMPLETE_CLASSIC_ADMISSION_UNION_AE_FREE",
        "coverage": "both Universal slices: complete bounded Classic admission union, 67 exact cells per slice",
    },
    "OLMSmoother2": {
        "report": "refs/conformance/olmsmoother2_current_installed_public_20260813.json",
        "report_sha256": "3e1ba25a3f259a8f26ccea21b38c7f4bfc3d63e61881b455e5811711e0810f4f",
        "status": "PASS_OLMSMOOTHER2_CURRENT_INSTALLED_COMPLETE_SMART_ADMISSION_UNION_AE_FREE",
        "coverage": "both Universal slices: complete bounded Smart admission union, 39 exact cells; the newly installed PF8/PF16/PF32 expansion executes 94 public rows per slice in addition to the prior 25-cell union",
    },
    "OLMToonDilate": {
        "report": "refs/conformance/olmtoondilate_current_installed_exact12_20260813.json",
        "report_sha256": "33eb4fe76e7f852c0a698e18eb63871343efd35e258da58359d1786146a796ed",
        "status": "pass_current_installed_exact12_against_paired_windows_public_owner",
        "coverage": "both Universal slices: 12 fixed same-source current installed cells per slice paired to the bounded Windows public owner",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contains(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(contains(item, needle) for item in value)
    if isinstance(value, dict):
        return any(contains(item, needle) for item in value.values())
    return False


def native_ae_false(report: dict[str, Any]) -> bool:
    scope = report.get("scope")
    if isinstance(scope, dict):
        if "native_after_effects" in scope:
            return scope["native_after_effects"] is False
        if "native_after_effects_host_claim" in scope:
            return scope["native_after_effects_host_claim"] is False
    claim = report.get("claim")
    if isinstance(claim, dict) and "native_after_effects" in claim:
        return claim["native_after_effects"] is False
    return False


def both_universal_slices_replayed(report: dict[str, Any]) -> bool:
    if report.get("architectures") == ["arm64", "x86_64"]:
        return True
    summary = report.get("summary")
    if isinstance(summary, dict) and summary.get("architectures") == ["arm64", "x86_64"]:
        return True
    relations = report.get("architecture_relations")
    if isinstance(relations, dict) and set(relations) == {"arm64", "x86_64"}:
        return True
    slices = report.get("slices")
    if isinstance(slices, dict) and set(slices) == {"arm64", "x86_64"}:
        return True
    scope = report.get("scope")
    return isinstance(scope, dict) and (
        (scope.get("installed_arm64") is True and scope.get("installed_x86_64") is True)
        or (scope.get("arm64") is True and scope.get("x86_64_rosetta") is True)
    )


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed for {name}")
        found.extend(f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit())
    return found


def generate() -> dict[str, Any]:
    if sha256(AUTHORITY) != AUTHORITY_SHA256:
        raise RuntimeError("all-ten installed authority hash drift")
    authority = json.loads(AUTHORITY.read_text())
    if authority.get("status") != "pass_all10_current_source_candidate_installed_exact_ae_deferred":
        raise RuntimeError("all-ten authority status drift")
    authority_rows = authority.get("plugins")
    if not isinstance(authority_rows, list) or len(authority_rows) != 10:
        raise RuntimeError("all-ten authority row count drift")
    by_name = {row.get("plugin"): row for row in authority_rows}
    if set(by_name) != set(EXPECTED):
        raise RuntimeError("all-ten authority plug-in set drift")

    rows: list[dict[str, Any]] = []
    for plugin in sorted(EXPECTED):
        expected = EXPECTED[plugin]
        authority_row = by_name[plugin]
        if not all(authority_row.get("checks", {}).values()):
            raise RuntimeError(f"installed authority checks failed for {plugin}")
        report_path = ROOT / expected["report"]
        if sha256(report_path) != expected["report_sha256"]:
            raise RuntimeError(f"public-route report hash drift for {plugin}")
        public = json.loads(report_path.read_text())
        if public.get("status") != expected["status"]:
            raise RuntimeError(f"public-route status drift for {plugin}")
        if public.get("after_effects_processes", []) != [] or not native_ae_false(public):
            raise RuntimeError(f"public-route AE-free boundary drift for {plugin}")
        if not both_universal_slices_replayed(public):
            raise RuntimeError(f"public-route Universal slice coverage drift for {plugin}")
        source_sha = authority_row["source_sha256"]
        binary_sha = authority_row["binary_sha256"]
        # The public replay must bind the installed executable directly.  The
        # source relation is deliberately taken from the independently closed
        # all-ten authority above; some installed replay reports bind a
        # source-closure report rather than repeating the production SHA.
        if not contains(public, binary_sha):
            raise RuntimeError(f"public-route installed identity is not bound for {plugin}")
        rows.append({
            "plugin": plugin,
            "source_sha256": source_sha,
            "installed_binary_sha256": binary_sha,
            "public_report": expected["report"],
            "public_report_sha256": expected["report_sha256"],
            "public_status": expected["status"],
            "bounded_coverage": expected["coverage"],
            "installed_authority_checks_all_true": True,
            "installed_universal_slices_replayed": True,
            "native_after_effects": False,
        })

    processes = ae_processes()
    if processes:
        raise RuntimeError(f"AE-family processes are running: {processes}")
    return {
        "schema": "olm.all10-current-installed-public-routes/1",
        "status": "PASS_ALL10_CURRENT_INSTALLED_PUBLIC_ROUTES_AE_FREE_BOUNDED",
        "installed_authority": {
            "path": str(AUTHORITY.relative_to(ROOT)),
            "sha256": AUTHORITY_SHA256,
            "plugin_count": 10,
        },
        "rows": rows,
        "after_effects_processes": [],
        "scope": {
            "current_installed_public_entry_hostless_replay_for_all_ten": True,
            "all_ten_arm64_and_x86_64_slices_replayed": True,
            "heterogeneous_bounded_coverage_only": True,
            "all_tuples_depths_geometries_claimed": False,
            "native_after_effects_claimed": False,
            "after_effects_launched": False,
            "windows_native_host_claim_generalized": False,
            "developer_id_or_notarization_claimed": False,
        },
    }


def validate_schema(report: dict[str, Any]) -> None:
    if set(report) != {"schema", "status", "installed_authority", "rows", "after_effects_processes", "scope"}:
        raise RuntimeError("aggregate top-level schema drift")
    if report["schema"] != "olm.all10-current-installed-public-routes/1":
        raise RuntimeError("aggregate schema mismatch")
    if report["status"] != "PASS_ALL10_CURRENT_INSTALLED_PUBLIC_ROUTES_AE_FREE_BOUNDED":
        raise RuntimeError("aggregate status mismatch")
    if report["installed_authority"] != {
        "path": str(AUTHORITY.relative_to(ROOT)), "sha256": AUTHORITY_SHA256, "plugin_count": 10
    }:
        raise RuntimeError("aggregate authority mismatch")
    expected_row_keys = {
        "plugin", "source_sha256", "installed_binary_sha256", "public_report",
        "public_report_sha256", "public_status", "bounded_coverage",
        "installed_authority_checks_all_true", "native_after_effects",
        "installed_universal_slices_replayed",
    }
    rows = report["rows"]
    if not isinstance(rows, list) or len(rows) != 10 or [row.get("plugin") for row in rows] != sorted(EXPECTED):
        raise RuntimeError("aggregate row set/order mismatch")
    for row in rows:
        if set(row) != expected_row_keys:
            raise RuntimeError("aggregate row schema drift")
        expected = EXPECTED[row["plugin"]]
        if row["public_report"] != expected["report"] or row["public_report_sha256"] != expected["report_sha256"]:
            raise RuntimeError("aggregate report identity drift")
        if row["public_status"] != expected["status"] or row["bounded_coverage"] != expected["coverage"]:
            raise RuntimeError("aggregate public claim drift")
        if row["installed_authority_checks_all_true"] is not True or row["installed_universal_slices_replayed"] is not True or row["native_after_effects"] is not False:
            raise RuntimeError("aggregate row boundary drift")
    if report["after_effects_processes"] != []:
        raise RuntimeError("aggregate AE process boundary drift")
    if report["scope"] != {
        "current_installed_public_entry_hostless_replay_for_all_ten": True,
        "all_ten_arm64_and_x86_64_slices_replayed": True,
        "heterogeneous_bounded_coverage_only": True,
        "all_tuples_depths_geometries_claimed": False,
        "native_after_effects_claimed": False,
        "after_effects_launched": False,
        "windows_native_host_claim_generalized": False,
        "developer_id_or_notarization_claimed": False,
    }:
        raise RuntimeError("aggregate scope drift")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# All-ten current installed public routes — bounded AE-free closure",
        "",
        f"Status: `{report['status']}`",
        "",
        "This is a heterogeneous, fixture-bounded hostless public-entry replay for all ten current installed plug-ins. It is not a claim over every tuple, source, depth, geometry, native After Effects execution, or native Windows host behavior.",
        "",
        "| Plug-in | Bounded coverage | Public report |",
        "| --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(f"| {row['plugin']} | {row['bounded_coverage']} | `{row['public_report']}` |")
    lines.extend([
        "",
        f"Installed authority: `{report['installed_authority']['path']}` (`{report['installed_authority']['sha256']}`).",
        "",
        "After Effects was not launched; the observed AE-family process set was empty.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = generate()
    validate_schema(generated)
    if args.write:
        REPORT.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(render_markdown(generated))
    if not REPORT.is_file() or not MARKDOWN.is_file():
        raise RuntimeError("canonical aggregate missing; run once with --write")
    saved = json.loads(REPORT.read_text())
    validate_schema(saved)
    if saved != generated:
        raise RuntimeError("canonical aggregate differs from live bounded closure")
    if MARKDOWN.read_text() != render_markdown(saved):
        raise RuntimeError("canonical aggregate markdown drift")
    print("PASS_ALL10_CURRENT_INSTALLED_PUBLIC_ROUTES_AE_FREE_BOUNDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
