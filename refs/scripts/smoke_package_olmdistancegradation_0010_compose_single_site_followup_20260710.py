#!/usr/bin/env python3
"""Verify the focused OLMDistanceGradation single-site Windows package."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUEST_ID = "olmdistancegradation_0010_compose_single_site_followup_20260710"
ARCHIVE_NAME = "olmdistancegradation_0010_compose_single_site_followup_windows_20260710.zip"
REQUEST_ROOT = (
    "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        default=repo_root() / "refs/runtime_trace_packages" / ARCHIVE_NAME,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_path = args.archive if args.archive.is_absolute() else repo_root() / args.archive
    if not zipfile.is_zipfile(archive_path):
        raise AssertionError(f"not a readable zip: {archive_path}")

    required = {
        "README_RUNTIME_TRACE.md",
        "runtime_trace_package_manifest.json",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "next_reference_actions_snapshot.json",
        "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
        "artifacts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1",
        "scripts/ae_render_single_case.jsx",
        f"{REQUEST_ROOT}/request_manifest.json",
        f"{REQUEST_ROOT}/reference_manifest.json",
        f"{REQUEST_ROOT}/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
        f"{REQUEST_ROOT}/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010.png",
    }
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package entries: {missing}")
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        snapshot = json.loads(archive.read("next_reference_actions_snapshot.json"))
        request = json.loads(archive.read(f"{REQUEST_ROOT}/request_manifest.json"))
        readme = archive.read("README_RUNTIME_TRACE.md").decode("utf-8")
        launcher = archive.read(
            "artifacts/run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1"
        ).decode("utf-8")

    if manifest.get("kind") != "olm_runtime_trace_request_package":
        raise AssertionError(f"unexpected manifest kind: {manifest.get('kind')}")
    actions = manifest.get("runtime_actions", [])
    if len(actions) != 1 or actions[0].get("request_id") != REQUEST_ID:
        raise AssertionError(f"unexpected runtime actions: {actions}")
    command = actions[0].get("command", "")
    for token in ("(6,40)", "+0x117057d", "+0x11705f1", "+0x1170814", "RDI == target_output"):
        if token not in command:
            raise AssertionError(f"runtime action missing matrix token: {token}")

    results = template.get("results", [])
    if len(results) != 1 or results[0].get("request_id") != REQUEST_ID:
        raise AssertionError(f"unexpected return template request: {results}")
    observations = results[0].get("observations", {})
    if observations.get("target_xy") != [6, 40]:
        raise AssertionError(f"unexpected target: {observations.get('target_xy')}")
    site_runs = observations.get("site_runs", {})
    if set(site_runs) != {"field", "source", "writer"}:
        raise AssertionError(f"unexpected site matrix: {site_runs.keys()}")
    if "rcx_field_words_u16" not in site_runs["field"]:
        raise AssertionError("field template lacks typed RCX words")
    if "rdx_source_words_u16" not in site_runs["source"]:
        raise AssertionError("source template lacks typed RDX words")
    if "final_pf16_words_at_rdi" not in site_runs["writer"]:
        raise AssertionError("writer template lacks PF16 output words")

    if snapshot.get("request_id") != REQUEST_ID:
        raise AssertionError(f"snapshot request mismatch: {snapshot.get('request_id')}")
    if request.get("request_id") != "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625":
        raise AssertionError(f"unexpected AE request id: {request.get('request_id')}")
    for site in ("field", "source", "writer"):
        if f"-Site {site} -X 6 -Y 40" not in readme:
            raise AssertionError(f"handoff lacks exact {site} smoke")
    if "scripts\\ae_render_single_case.jsx" not in launcher or "$requestRelative" not in launcher:
        raise AssertionError("launcher does not resolve packaged runner/request assets")

    print(f"[OK] {REQUEST_ID} package smoke passed: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
