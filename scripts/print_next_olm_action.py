#!/usr/bin/env python3
"""Print the next highest-value OLM porting action from current artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import list_olm_return_candidates

REFS_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "refs" / "scripts"
sys.path.insert(0, str(REFS_SCRIPT_DIR))

from check_reference_request_status import (  # noqa: E402
    load_status_rows,
    expected_required_sets,
    manifest_case_ids,
    manifest_render_sets,
    relevant_manifest_cases,
)
from next_reference_actions import build_reference_action_data  # noqa: E402
from verify_reference_request_package import packaged_request_ids  # noqa: E402
from verify_reference_request_result import effect_matches, load_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to inspect for returned zips. Defaults to ~/Downloads and /tmp.",
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=None,
        help="Current handoff package path. When omitted, the newest handoff in the scanned paths is used.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


OLM_SCAN_NAME_TOKENS = {
    "olm",
    "aex",
    "aftereffects",
    "ae_host",
    "ae-host",
    "ae_pixel",
    "ae-pixel",
    "colorkey",
    "color_key",
    "color-keep",
    "colorkeep",
    "distancegradation",
    "directionalblur",
    "kira",
    "radialblur",
    "smoother",
    "toon",
    "runtime_trace",
    "windows_action_bundle",
    "reference_return",
    "reference_request",
}


def likely_olm_scan_candidate(path: Path) -> bool:
    name = path.name.lower()
    return any(token in name for token in OLM_SCAN_NAME_TOKENS)


def request_status(root: Path) -> dict[str, Any]:
    requests = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    if not isinstance(requests, list):
        requests = []
    pending = [
        row.get("request_id")
        for row in requests
        if isinstance(row, dict) and row.get("status") != "covered"
    ]
    covered = [
        row.get("request_id")
        for row in requests
        if isinstance(row, dict) and row.get("status") == "covered"
    ]
    return {
        "pending": [item for item in pending if isinstance(item, str)],
        "covered": [item for item in covered if isinstance(item, str)],
        "rows": requests,
    }


def pending_pinning_rows(status: dict[str, Any]) -> list[dict[str, Any]]:
    pending_ids = set(status.get("pending", []))
    rows = status.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("request_id"), str) and row["request_id"] in pending_ids
    ]


def pending_pinning_summary(status: dict[str, Any]) -> dict[str, Any] | None:
    rows = pending_pinning_rows(status)
    if not rows:
        return None
    total_requests = len(rows)
    total_cases = 0
    current_cases = 0
    packaged_cases = 0
    linked_cases = 0
    improved_requests = 0
    fully_packaged_requests = 0
    request_summaries: list[str] = []
    for row in rows:
        pinning = row.get("pinning") or {}
        total = int(pinning.get("total_cases", 0) or 0)
        current = int(pinning.get("current_params_full_cases", 0) or 0)
        packaged = int(pinning.get("packaged_params_full_cases", 0) or 0)
        linked = int(pinning.get("linked_cases", 0) or 0)
        total_cases += total
        current_cases += current
        packaged_cases += packaged
        linked_cases += linked
        if packaged > current:
            improved_requests += 1
        if packaged == total and total > 0:
            fully_packaged_requests += 1
        request_summaries.append(f"{row['request_id']} {current}/{total}->{packaged}/{total}")
    return {
        "request_count": total_requests,
        "total_cases": total_cases,
        "current_params_full_cases": current_cases,
        "packaged_params_full_cases": packaged_cases,
        "linked_cases": linked_cases,
        "improved_requests": improved_requests,
        "fully_packaged_requests": fully_packaged_requests,
        "request_summaries": request_summaries[:6],
    }


def next_reference_actions(root: Path) -> dict[str, Any]:
    rows = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    return build_reference_action_data(rows)


def runtime_trace_actions(
    next_actions: dict[str, Any],
    trace_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actions = next_actions.get("covered_actions", [])
    if not isinstance(actions, list):
        return []
    pending_report_ids = pending_runtime_trace_request_ids(repo_root())
    if pending_report_ids:
        return [
            action
            for action in actions
            if isinstance(action, dict)
            and (action.get("status") == "runtime-trace" or action.get("mode") == "external-trace")
            and isinstance(action.get("request_id"), str)
            and action.get("request_id") in pending_report_ids
        ]
    answered = set(trace_summary.get("answered_request_ids", [])) if trace_summary else set()
    answered.update(trace_summary.get("superseded_request_ids", []) if trace_summary else [])
    return [
        action
        for action in actions
        if isinstance(action, dict)
        and (action.get("status") == "runtime-trace" or action.get("mode") == "external-trace")
        and action.get("request_id") not in answered
    ]


def pending_runtime_trace_request_ids(root: Path) -> set[str]:
    rows = pending_runtime_trace_rows(root)
    return {row["request_id"] for row in rows if isinstance(row.get("request_id"), str)}


def pending_runtime_trace_priorities(root: Path) -> dict[str, int]:
    priorities: dict[str, int] = {}
    for row in pending_runtime_trace_rows(root):
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            continue
        try:
            priorities[request_id] = int(row.get("priority") or 999999)
        except (TypeError, ValueError):
            priorities[request_id] = 999999
    return priorities


def pending_runtime_trace_rows(root: Path) -> list[dict[str, Any]]:
    path = root / "refs" / "reports" / "pending_runtime_trace_packages.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    rows = data.get("requests")
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("status") == "pending"
    ]


def runtime_trace_summary(root: Path) -> dict[str, Any] | None:
    report_dir = root / "refs" / "reports"
    summary_paths = sorted(report_dir.glob("**/runtime_trace_summary*.json")) if report_dir.exists() else []
    superseded = runtime_trace_superseded(root)
    if not summary_paths and not superseded:
        return None
    summaries: list[tuple[Path, dict[str, Any]]] = []
    answered_ids: list[str] = []
    for summary_path in summary_paths:
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        required = data.get("required", [])
        if not isinstance(required, list):
            required = []
        for row in required:
            if not isinstance(row, dict) or row.get("answered") is not True:
                continue
            request_id = row.get("request_id")
            if isinstance(request_id, str):
                answered_ids.append(request_id)
        for row in data.get("results", []):
            if not isinstance(row, dict):
                continue
            request_id = row.get("request_id")
            status = str(row.get("status") or "").lower()
            if isinstance(request_id, str) and status.startswith("answered"):
                answered_ids.append(request_id)
        summaries.append((summary_path, data))
    if not answered_ids and not superseded:
        return None
    if summaries:
        latest_path, _latest_data = max(summaries, key=lambda item: item[0].stat().st_mtime)
        markdown_path = latest_path.with_suffix(".md")
        stat = latest_path.stat()
        latest_path_text = str(latest_path)
        markdown_path_text = str(markdown_path) if markdown_path.exists() else ""
        mtime = stat.st_mtime
    else:
        latest_path_text = str(root / "refs" / "reports" / "runtime_trace_superseded.json")
        markdown_path_text = ""
        mtime = (root / "refs" / "reports" / "runtime_trace_superseded.json").stat().st_mtime
    return {
        "path": latest_path_text,
        "markdown_path": markdown_path_text,
        "mtime": mtime,
        "answered_request_ids": sorted(set(answered_ids)),
        "superseded_request_ids": sorted(superseded),
    }


def runtime_trace_request_statuses(root: Path, request_id: str) -> list[str]:
    """Return observed statuses for a runtime-trace request from summary files."""
    statuses: list[str] = []
    report_dir = root / "refs" / "reports"
    summary_paths = sorted(report_dir.glob("**/runtime_trace_summary*.json")) if report_dir.exists() else []
    for summary_path in summary_paths:
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        for row in data.get("required", []):
            if not isinstance(row, dict) or row.get("request_id") != request_id:
                continue
            row_statuses = row.get("statuses", [])
            if isinstance(row_statuses, list):
                statuses.extend(str(status).lower() for status in row_statuses if status)
        for row in data.get("results", []):
            if not isinstance(row, dict) or row.get("request_id") != request_id:
                continue
            status = row.get("status")
            if status:
                statuses.append(str(status).lower())
    return sorted(set(statuses))


def runtime_trace_request_latest_mtime(root: Path, request_id: str) -> float:
    """Return latest summary mtime that mentions a runtime-trace request."""
    latest = 0.0
    report_dir = root / "refs" / "reports"
    summary_paths = sorted(report_dir.glob("**/runtime_trace_summary*.json")) if report_dir.exists() else []
    for summary_path in summary_paths:
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        mentioned = False
        for row in data.get("required", []):
            if isinstance(row, dict) and row.get("request_id") == request_id:
                mentioned = True
        for row in data.get("results", []):
            if isinstance(row, dict) and row.get("request_id") == request_id:
                mentioned = True
        if mentioned:
            try:
                latest = max(latest, summary_path.stat().st_mtime)
            except OSError:
                continue
    return latest


def zip_contains_text(path: Path, needle: str) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.endswith("/"):
                    continue
                try:
                    text = archive.read(name).decode("utf-8", "ignore")
                except (KeyError, UnicodeDecodeError):
                    continue
                if needle in text:
                    return True
    except (OSError, zipfile.BadZipFile):
        return False
    return False


def runtime_trace_superseded(root: Path) -> set[str]:
    path = root / "refs" / "reports" / "runtime_trace_superseded.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(data, dict):
        return set()
    ids: set[str] = set()
    for row in data.get("superseded", []):
        if not isinstance(row, dict):
            continue
        request_id = row.get("request_id")
        if isinstance(request_id, str) and request_id:
            ids.add(request_id)
    return ids


def bitdepth16_compare_pending(root: Path) -> dict[str, Any] | None:
    summary_path = root / "refs" / "conformance" / "bitdepth_16bpc_reference_return_20260625.json"
    if not summary_path.exists():
        return None
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(summary, dict) or summary.get("status") != "reference-covered-compare-pending":
        return None

    decision_paths = [
        root / "refs" / "conformance" / "olmcolorkey_edge_8bpc_decision.json",
        root / "refs" / "conformance" / "olmdistancegradation_8bpc_decision.json",
        root / "refs" / "conformance" / "olmblur_8bpc_decision.json",
    ]
    feature_rows = []
    for path in decision_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        ref16 = data.get("windows_16bpc_reference") if isinstance(data, dict) else None
        if not isinstance(ref16, dict) or ref16.get("status") != "reference-covered-compare-pending":
            return None
        feature_rows.append(
            {
                "path": str(path.relative_to(root)),
                "case_count": ref16.get("case_count"),
                "groups": ref16.get("groups"),
            }
        )

    package_dirs = sorted(
        (root / "handoffs" / "ae_host_validation").glob("*_16bpc_mac_ae_validation"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    package_dir = package_dirs[0] if package_dirs else None
    packages = sorted(str(path) for path in package_dir.glob("*.zip")) if package_dir else []
    bundle_paths = sorted(
        (root / "handoffs" / "ae_host_validation").glob("*_16bpc_mac_ae_validation_bundle/*.zip"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    bundle_path = bundle_paths[0] if bundle_paths else None

    return {
        "path": str(bundle_path or package_dir or summary_path),
        "kind": "bitdepth-16bpc-reference-summary",
        "request_id": summary.get("request_id"),
        "manifest": summary.get("imported_manifest"),
        "case_count": summary.get("case_count"),
        "not_complete_reason": summary.get("not_complete_reason"),
        "reference_summary": str(summary_path),
        "bundle": str(bundle_path) if bundle_path else "",
        "package_dir": str(package_dir) if package_dir else "",
        "packages": packages,
        "features": feature_rows,
    }


def bitdepth16_mac_validation_result(root: Path) -> dict[str, Any] | None:
    paths = sorted(
        (root / "refs" / "conformance").glob("bitdepth_16bpc_mac_ae_validation_*.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    path = paths[0] if paths else None
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    if status not in {"not-ae-exact", "ae-exact"}:
        return None
    return {
        "path": str(path),
        "markdown_path": str(path.with_suffix(".md")) if path.with_suffix(".md").exists() else "",
        "kind": "bitdepth-16bpc-mac-ae-validation",
        "mtime": path.stat().st_mtime,
        "status": status,
        "case_total": data.get("case_total"),
        "case_exact": data.get("case_exact"),
        "case_fail": data.get("case_fail"),
        "run_dir": data.get("run_dir"),
        "requests": data.get("requests", []),
    }


def ae_host_automation_blocker(root: Path) -> dict[str, Any] | None:
    paths = sorted(
        (root / "refs" / "conformance").glob("ae_host_automation_blocker_*.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if not paths:
        return None
    path = paths[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("status") != "host-blocked":
        return None
    return {
        "path": str(path.with_suffix(".md")) if path.with_suffix(".md").exists() else str(path),
        "json_path": str(path),
        "kind": "ae-host-automation-blocker",
        "mtime": path.stat().st_mtime,
        "status": data.get("status"),
        "summary": data.get("summary"),
        "next_allowed_action": data.get("next_allowed_action"),
    }


def ae_host_exact_summary(root: Path) -> dict[str, Any] | None:
    report_root = root / "refs" / "reports"
    summaries: list[dict[str, Any]] = []

    for summary_md in report_root.glob("ae_host_validation_*/exact_return/AE_HOST_EXACT_SUMMARY.md"):
        summary_json = summary_md.parent / "reports" / "AE_VALIDATION_EXACT_REPORT.json"
        result: dict[str, Any] = {
            "path": str(summary_md),
            "json_path": str(summary_json) if summary_json.exists() else "",
            "kind": "ae-host-exact-summary",
            "mtime": summary_md.stat().st_mtime,
        }
        if summary_json.exists():
            try:
                data = json.loads(summary_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            if isinstance(data, dict):
                requests = data.get("requests", [])
                cases = [
                    case
                    for request in requests
                    if isinstance(request, dict)
                    for case in request.get("cases", [])
                    if isinstance(case, dict)
                ]
                exact = [case for case in cases if case_is_exact(case)]
                result["case_count"] = len(cases)
                result["exact_count"] = len(exact)
                result["all_exact"] = len(cases) == len(exact) if cases else False
        summaries.append(result)

    for validation_dir in report_root.glob("ae_host_validation_*"):
        if not validation_dir.is_dir():
            continue
        report_jsons = [
            path
            for path in validation_dir.glob("ae_pixel_*/reports/*.json")
            if path.name != "AE_VALIDATION_EXACT_REPORT.json"
        ]
        if not report_jsons:
            continue
        cases: list[dict[str, Any]] = []
        latest_mtime = validation_dir.stat().st_mtime
        for path in report_jsons:
            latest_mtime = max(latest_mtime, path.stat().st_mtime)
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and isinstance(data.get("cases"), list):
                cases.extend(case for case in data["cases"] if isinstance(case, dict))
        if not cases:
            continue
        exact = [case for case in cases if case_is_exact(case)]
        summaries.append(
            {
                "path": str(validation_dir),
                "json_path": "",
                "kind": "ae-pixel-validation-summary",
                "mtime": latest_mtime,
                "case_count": len(cases),
                "exact_count": len(exact),
                "all_exact": len(cases) == len(exact),
            }
        )

    if not summaries:
        return None
    return max(summaries, key=lambda row: float(row.get("mtime", 0)))


def case_is_exact(case: dict[str, Any]) -> bool:
    if case.get("exact_pass") is True:
        return True
    if case.get("pass") is True and case.get("status") == "compared":
        try:
            return int(case.get("max_diff")) == 0
        except (TypeError, ValueError):
            return False
    if case.get("status") == "compared":
        try:
            return int(case.get("max_diff")) == 0
        except (TypeError, ValueError):
            return False
    return False


def ae_host_failure_classification(root: Path, ae_summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if not ae_summary:
        return None
    summary_path = Path(str(ae_summary.get("path", "")))
    if not summary_path:
        return None
    if summary_path.is_dir():
        report_dir = summary_path
    elif summary_path.name == "AE_HOST_EXACT_SUMMARY.md":
        report_dir = summary_path.parent
    elif summary_path.parent.name == "reports":
        report_dir = summary_path.parents[1]
    else:
        report_dir = summary_path.parent if summary_path.parent.exists() else root / "refs" / "reports"
    matches = sorted(
        report_dir.glob("ae_host_exact_failure_classification_*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        return None
    path = matches[0]
    return {
        "path": str(path),
        "kind": "ae-host-exact-failure-classification",
        "mtime": path.stat().st_mtime,
        "summary_path": str(summary_path),
        "is_current": path.stat().st_mtime >= float(ae_summary.get("mtime", 0)),
    }


def binary_grounded_followup_report(root: Path) -> dict[str, Any] | None:
    report_candidates = [
        root / "refs" / "conformance" / "olmdistancegradation_16bpc_case0026_analysis_20260628.md",
        root / "refs" / "reports" / "olmsmoother2_current_aex_proof_plan_20260625" / "proof_plan.md",
        root / "refs" / "reports" / "olmsmoother2_witness_neighborhood_20260624" / "neighborhood.md",
        root / "refs" / "reports" / "olmsmoother2_current_aex_witness_contract_20260624" / "witness_contract.md",
        root / "refs" / "reports" / "olmsmoother2_current_aex_decision_matrix_20260624" / "decision_matrix.md",
        root / "refs" / "reports" / "olmsmoother2_current_aex_diff_clusters_latest" / "diff_clusters.md",
        root / "refs" / "reports" / "olmsmoother2_current_aex_curve_idx_sweep_latest" / "curve_idx_sweep.md",
    ]
    fallback_candidates = [
        root / "notes" / "IR_OLMSmoother2.md",
    ]
    existing = [path for path in report_candidates if path.exists()]
    if not existing:
        existing = [path for path in fallback_candidates if path.exists()]
    if not existing:
        return None
    path = max(existing, key=lambda item: item.stat().st_mtime)
    return {
        "path": str(path),
        "kind": "binary-grounded-residual-report",
        "mtime": path.stat().st_mtime,
    }


def latest_runtime_trace_package(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == "runtime-trace-request-package"]
    package_dir = root / "refs" / "runtime_trace_packages"
    if package_dir.exists():
        for path in package_dir.glob("*.zip"):
            if not path.is_file():
                continue
            manifest = runtime_trace_package_manifest(path)
            if not manifest or manifest.get("kind") != "olm_runtime_trace_request_package":
                continue
            row = list_olm_return_candidates.build_row(path)
            row["kind"] = "runtime-trace-request-package"
            row["suggested_command"] = "send this package to the Windows debugger/helper"
            matches.append(row)
    matches = [row for row in matches if row.get("kind") == "runtime-trace-request-package"]
    if not matches:
        return None
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


def runtime_trace_package_manifest(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith("runtime_trace_package_manifest.json"):
                    continue
                data = json.loads(archive.read(name).decode("utf-8"))
                return data if isinstance(data, dict) else None
    except Exception:
        return None
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def staged_runtime_trace_package(
    runtime_package: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    target_path = Path(str(runtime_package.get("path", "")))
    if not target_path.is_file():
        return None
    try:
        target_hash = file_sha256(target_path)
        target_resolved = target_path.resolve()
    except OSError:
        return None
    target_ids = set()
    listed_ids = runtime_package.get("request_ids")
    if isinstance(listed_ids, list):
        target_ids.update(request_id for request_id in listed_ids if isinstance(request_id, str))
    target_manifest = runtime_trace_package_manifest(target_path)
    if isinstance(target_manifest, dict):
        for action in target_manifest.get("runtime_actions", []):
            if isinstance(action, dict) and isinstance(action.get("request_id"), str):
                target_ids.add(action["request_id"])
    for row in rows:
        if row.get("kind") != "runtime-trace-request-package":
            continue
        row_path = Path(str(row.get("path", "")))
        if not row_path.is_file():
            continue
        # Project-local packages and stale /tmp copies are preparation
        # artifacts, not active Windows exchanges. The current workflow treats
        # only olm_pr/new as staged.
        parts = set(row_path.parts)
        if not ("olm_pr" in parts and "new" in parts):
            continue
        try:
            if row_path.resolve() == target_resolved:
                continue
            row_hash = file_sha256(row_path)
        except OSError:
            continue
        row_manifest = runtime_trace_package_manifest(row_path)
        row_ids = set()
        if isinstance(row_manifest, dict):
            for action in row_manifest.get("runtime_actions", []):
                if isinstance(action, dict) and isinstance(action.get("request_id"), str):
                    row_ids.add(action["request_id"])
        if row_hash != target_hash and not (target_ids and row_ids and target_ids & row_ids):
            continue
        staged = dict(row)
        staged["sha256"] = target_hash
        staged["staged_sha256"] = row_hash
        staged["matched_request_ids"] = sorted(target_ids & row_ids)
        return staged
    return None


def runtime_trace_acceptance_note(request_ids: list[str]) -> str:
    mapping = {
        "olmradialblur_case0010_final_writeback_20260708": "refs/conformance/olmradialblur_case0010_final_writeback_contract_20260708.md",
        "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702": "refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md",
        "olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702": "refs/conformance/olmradialblur_tiny_rotation_anchor_pointer_watch_return_acceptance_20260702.md",
        "olmradialblur_tiny_rotation_anchor_watch_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_anchor_watch_return_acceptance_20260701.md",
        "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_backstep_return_acceptance_20260701.md",
        "olmradialblur_tiny_rotation_substitute_path_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_return_acceptance_20260701.md",
        "olmradialblur_caller_collapse_followup_20260701": "refs/conformance/olmradialblur_outer_return_acceptance_20260701.md",
        "olmdirectionalblur_angle0_single_shot_witness_20260708": "refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md",
        "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702": "refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md",
        "olmdistancegradation_case0023_refcon_wordmap_followup_20260702": "refs/conformance/olmdistancegradation_case0023_refcon_wordmap_return_acceptance_20260702.md",
        "olmdistancegradation_depthgate_907_store_export_witness_20260708": "refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md",
        "olmdistancegradation_case0012_case0014_store_export_rounding_20260708": "refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_contract_20260708.md",
        "olmdistancegradation_case0014_layer_source_witness_20260708": "refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md",
        "olmdistancegradation_case0023_output_word_triplet_followup_20260701": "refs/conformance/olmdistancegradation_case0023_output_word_triplet_return_acceptance_20260701.md",
        "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701": "refs/conformance/olmdistancegradation_case0023_triplet_xy_compose_return_acceptance_20260701.md",
        "olmdistancegradation_case0023_threshold_family_followup_20260701": "refs/conformance/olmdistancegradation_case0023_threshold_return_acceptance_20260701.md",
        "olmdistancegradation_case0023_final_source_ownership_20260707": "refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md",
        "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710": "refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md",
        "olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
        "olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_packsite_contract_20260709.md",
        "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630": "refs/conformance/olmdistancegradation_case0023_return_acceptance_20260701.md",
        "olmblur_case0006_helper_prestore_witness_20260630": "refs/conformance/olmblur_case0006_reference_provenance_20260701.md",
        "olmsmoother2_current_aex_producer_bytes_20260708": "refs/conformance/olmsmoother2_current_aex_producer_bytes_contract_20260708.md",
    }
    for request_id in request_ids:
        note = mapping.get(request_id)
        if note:
            return note
    return ""


def windows_action_bundle_manifest(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith("windows_action_bundle_manifest.json"):
                    continue
                data = json.loads(archive.read(name).decode("utf-8"))
                return data if isinstance(data, dict) else None
    except Exception:
        return None
    return None


def action_bundle_contains_runtime_package(bundle_manifest: dict[str, Any] | None, runtime_package: dict[str, Any]) -> bool:
    if not bundle_manifest:
        return False
    target_path = Path(str(runtime_package.get("path", "")))
    target_names = {target_path.name, str(target_path)}
    for item in bundle_manifest.get("runtime_trace_packages", []):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", ""))
        bundle_path = str(item.get("bundle_path", ""))
        if source in target_names or Path(source).name in target_names:
            return True
        if bundle_path in target_names or Path(bundle_path).name in target_names:
            return True
    return False


def project_runtime_trace_packages(
    root: Path,
    trace_summary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    package_dir = root / "refs" / "runtime_trace_packages"
    if not package_dir.exists():
        return []
    pending_priorities = pending_runtime_trace_priorities(root)
    pending_report = root / "refs" / "reports" / "pending_runtime_trace_packages.json"
    if pending_report.exists() and not pending_priorities:
        return []
    answered = set(trace_summary.get("answered_request_ids", [])) if trace_summary else set()
    answered.update(trace_summary.get("superseded_request_ids", []) if trace_summary else [])
    stale_request_ids = {
        # Superseded by the 2026-06-21 current-AEX residual/writer-backtrack/
        # step-over returns. Re-sending these repeats the same low-repro CDB
        # breakpoint path unless the Windows helper can freeze scheduling.
        "olmsmoother2_legacy_current_aex_polygon_trace_20260621",
        "olmsmoother2_legacy_current_aex_polygon_backtrack_trace_20260621",
        "olmsmoother2_legacy_current_aex_polygon_stepover_trace_20260621",
        "olmsmoother2_legacy_current_aex_residuals_trace_20260621",
    }
    latest_by_profile: dict[str, dict[str, Any]] = {}
    for path in package_dir.glob("*.zip"):
        manifest = runtime_trace_package_manifest(path)
        if not manifest or manifest.get("kind") != "olm_runtime_trace_request_package":
            continue
        actions = [
            action
            for action in manifest.get("runtime_actions", [])
            if isinstance(action, dict)
        ]
        request_ids = [
            str(action["request_id"])
            for action in actions
            if isinstance(action.get("request_id"), str)
        ]
        if request_ids and all(request_id.startswith("windows_ae_") for request_id in request_ids):
            continue
        if request_ids and all(request_id in stale_request_ids for request_id in request_ids):
            continue
        profile = str(manifest.get("profile", ""))
        if request_ids and all(
            request_id in answered and request_id not in pending_priorities
            for request_id in request_ids
        ):
            continue
        if pending_priorities and request_ids and not any(request_id in pending_priorities for request_id in request_ids):
            continue
        row = list_olm_return_candidates.build_row(path)
        row["kind"] = "runtime-trace-request-package"
        row["suggested_command"] = "send this package to the Windows debugger/helper"
        row["profile"] = profile
        row["request_ids"] = request_ids
        row["acceptance_note"] = runtime_trace_acceptance_note(request_ids)
        row["plugin_areas"] = [
            str(action.get("plugin_area", ""))
            for action in actions
            if action.get("plugin_area")
        ]
        profile_key = str(row.get("profile") or path.stem)
        previous = latest_by_profile.get(profile_key)
        if previous is None or float(row["mtime"]) > float(previous["mtime"]):
            latest_by_profile[profile_key] = row
    priority = [
        # Current non-Smoother hard-path queue. These packages are focused on
        # concrete witness pixels or primitive facts, so they should be surfaced
        # before older Smoother2 debugger packages when no Windows PNG requests
        # are pending.
        "radialblur-caller-collapse-witness",
        "radialblur-residual-witness",
        "olmblur-final-word-witness",
        "kirakira-boxfilter-pass1-microprobe",
        "directionalblur-helper-coverage-witness",
        "directionalblur-residual-witness",
        "directionalblur-angle0-single-shot-witness",
        "kirakira-compose-writeback-witness",
        "distancegradation-depthgate-907-store-export-witness",
        "distancegradation-case0014-layer-source-witness",
        "radialblur",
        "kirakira",
        "directionalblur",
        "olmblur",
        "colorkey",
        "distancegradation",
        "dense-live-followup",
        "smoother2-current-aex-f270-witness",
        "smoother2-legacy-cce0-internals-trace",
        "smoother2-legacy-cce0-pixel-trace",
        "smoother2-legacy-u8-pixel-trace",
        "smoother2-legacy-u8-writer-trace",
        "smoother2-legacy-writeback-extract",
        "smoother2",
    ]

    def sort_key(row: dict[str, Any]) -> tuple[int, float]:
        if pending_priorities:
            request_priorities = [
                pending_priorities[request_id]
                for request_id in row.get("request_ids", [])
                if request_id in pending_priorities
            ]
            if request_priorities:
                return (min(request_priorities), -float(row.get("mtime", 0)))
        haystack = " ".join(
            [
                str(row.get("profile", "")),
                " ".join(row.get("request_ids", [])),
                " ".join(row.get("plugin_areas", [])),
                Path(str(row.get("path", ""))).name,
            ]
        ).lower()
        rank = next((index for index, key in enumerate(priority) if key in haystack), len(priority))
        return (rank, -float(row.get("mtime", 0)))

    return sorted(latest_by_profile.values(), key=sort_key)


def latest_windows_action_bundle(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == "windows-action-bundle"]
    batch_dir = root / "handoffs" / "windows_batch"
    if batch_dir.exists():
        matches.extend(
            list_olm_return_candidates.build_row(path)
            for path in batch_dir.glob("*.zip")
            if path.is_file()
        )
        matches = [row for row in matches if row.get("kind") == "windows-action-bundle"]
    if not matches:
        return None
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


def latest_ae_pixel_validation_return(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == "ae-pixel-validation-return"]
    returns_dir = root / "handoffs" / "windows_returns"
    if returns_dir.exists():
        matches.extend(
            list_olm_return_candidates.build_row(path)
            for path in returns_dir.glob("**/*.zip")
            if path.is_file()
        )
        matches = [row for row in matches if row.get("kind") == "ae-pixel-validation-return"]
    if not matches:
        return None
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


def pending_requests(root: Path, request_ids: list[str]) -> list[dict[str, Any]]:
    request_dir = root / "refs" / "reference_requests"
    requests = []
    for request_id in request_ids:
        path = request_dir / f"{request_id}.json"
        if path.exists():
            requests.append(load_json(path))
    return requests


def handoff_summary(root: Path, handoff: Path | None) -> dict[str, Any]:
    if handoff is None:
        return {"path": "", "valid": False, "problem": "no handoff package found in scanned paths"}
    script = root / "scripts" / "print_current_handoff.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--package", str(handoff), "--json"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        return {"path": str(handoff), "valid": False, "problem": proc.stdout.strip()}
    data = json.loads(proc.stdout)
    contents = data.get("handoff_contents", {})
    return {
        "path": data.get("handoff_package", str(handoff)),
        "valid": True,
        "git_commit": contents.get("git_commit", ""),
        "git_dirty": contents.get("git_dirty"),
    }


def candidate_rows(paths: list[Path]) -> list[dict[str, Any]]:
    share_new = Path("/Volumes/onmk/olm_pr/new")
    roots = paths or [share_new, Path.home() / "Downloads", Path("/tmp")]
    if paths:
        expanded = {path.expanduser() for path in paths}
        default_scan_roots = {Path.home() / "Downloads", Path("/tmp")}
        if expanded & default_scan_roots:
            roots = [share_new, *roots]
    candidates: list[Path] = []
    for root in roots:
        root = root.expanduser()
        if root.is_file():
            candidates.append(root)
            continue
        if not root.is_dir():
            continue
        candidates.extend(
            path
            for path in list_olm_return_candidates.candidate_paths([root])
            if likely_olm_scan_candidate(path)
        )
    return [
        list_olm_return_candidates.build_row(path)
        for path in sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)
    ]


def newest(rows: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == kind]
    if not matches:
        return None
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


def package_matches_pending(row: dict[str, Any], pending: list[str]) -> bool:
    try:
        ids = packaged_request_ids(Path(row["path"]).resolve())
    except Exception:
        return False
    return ids == sorted(pending)


def reference_request_package(root: Path, rows: list[dict[str, Any]], pending: list[str]) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == "reference-request-package"]
    matches = [row for row in matches if package_matches_pending(row, pending)]
    if not matches:
        return None

    project_batch = root / "handoffs" / "windows_batch"
    project_matches = [
        row
        for row in matches
        if Path(str(row.get("path", ""))).resolve().is_relative_to(project_batch)
    ]
    if project_matches:
        return max(project_matches, key=lambda row: float(row.get("mtime", 0)))

    pending_named = [
        row
        for row in matches
        if "pending" in Path(str(row.get("path", ""))).name
    ]
    if pending_named:
        return max(pending_named, key=lambda row: float(row.get("mtime", 0)))
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


def staged_reference_request_package(
    request_pkg: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    target_path = Path(str(request_pkg.get("path", "")))
    if not target_path.is_file():
        return None
    try:
        target_hash = file_sha256(target_path)
        target_resolved = target_path.resolve()
        target_ids = set(packaged_request_ids(target_resolved))
    except Exception:
        return None
    for row in rows:
        if row.get("kind") != "reference-request-package":
            continue
        row_path = Path(str(row.get("path", "")))
        if not row_path.is_file():
            continue
        parts = set(row_path.parts)
        if not ("olm_pr" in parts and "new" in parts):
            continue
        try:
            if row_path.resolve() == target_resolved:
                continue
            row_hash = file_sha256(row_path)
            row_ids = set(packaged_request_ids(row_path.resolve()))
        except Exception:
            continue
        if row_hash != target_hash and not (target_ids and row_ids and target_ids == row_ids):
            continue
        staged = dict(row)
        staged["sha256"] = target_hash
        staged["staged_sha256"] = row_hash
        staged["matched_request_ids"] = sorted(target_ids & row_ids)
        return staged
    return None


def win_reference_return_intake_command(pending: list[str]) -> str:
    if len(pending) == 1:
        request_id = pending[0]
        request_path = Path("refs/reference_requests") / f"{request_id}.json"
        return (
            "python3 scripts/intake_olm_return.py path/to/returned_reference.zip "
            f"--kind win-reference --request {request_path} --set-id {request_id} --quick"
        )
    return (
        "python3 scripts/intake_olm_return.py path/to/returned_reference.zip "
        "--kind win-reference --quick"
    )


def zip_contains_file(names: set[str], root: str, value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return f"{root}{value}" in names


def zip_files_ok(names: set[str], manifest_name: str, manifest: dict[str, Any]) -> bool:
    root = str(Path(manifest_name).parent)
    if root == ".":
        root = ""
    else:
        root += "/"
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            return False
        if not zip_contains_file(names, root, case.get("frame")):
            return False
        if not zip_contains_file(names, root, case.get("before_effects_frame")):
            return False
    return True


def manifest_covers_request(manifest: dict[str, Any], request: dict[str, Any]) -> bool:
    if not effect_matches(request, manifest):
        return False
    relevant_cases = relevant_manifest_cases(request, manifest)
    if not relevant_cases:
        return False
    required_cases = {
        case["id"]
        for case in request.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str) and not case.get("optional")
    }
    if required_cases and not required_cases <= manifest_case_ids(relevant_cases):
        return False
    found_sets = manifest_render_sets(relevant_cases, manifest)
    for acceptable in expected_required_sets(request):
        if acceptable and not (acceptable & found_sets):
            return False
    return True


def covered_pending_requests(row: dict[str, Any], requests: list[dict[str, Any]]) -> list[str]:
    path = Path(row["path"])
    matches: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(list_olm_return_candidates.clean_zip_names(path))
            manifests = [name for name in names if name.endswith("reference_manifest.json")]
            for manifest_name in manifests:
                manifest = list_olm_return_candidates.read_zip_json(path, manifest_name)
                if not manifest or not zip_files_ok(names, manifest_name, manifest):
                    continue
                for request in requests:
                    request_id = request.get("request_id")
                    if isinstance(request_id, str) and manifest_covers_request(manifest, request):
                        matches.append(request_id)
    except Exception:
        return []
    return sorted(set(matches))


def actionable_win_reference_rows(rows: list[dict[str, Any]], requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actionable = []
    for row in rows:
        if row.get("kind") != "win-reference-return":
            continue
        covered = covered_pending_requests(row, requests)
        if not covered:
            continue
        row = dict(row)
        row["covered_pending_requests"] = covered
        actionable.append(row)
    return sorted(actionable, key=lambda row: float(row.get("mtime", 0)), reverse=True)


def staged_exchange_runtime_requests(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    staged: list[dict[str, Any]] = []
    for row in rows:
        if row.get("kind") != "runtime-trace-request-package":
            continue
        path_text = str(row.get("path", ""))
        if not path_text:
            continue
        path = Path(path_text)
        parts = set(path.parts)
        if "olm_pr" in parts and "new" in parts:
            staged.append(row)
    return sorted(staged, key=lambda row: float(row.get("mtime", 0)), reverse=True)


def decide(
    root: Path,
    rows: list[dict[str, Any]],
    status: dict[str, Any],
    handoff: dict[str, Any],
    pending_request_defs: list[dict[str, Any]],
    next_actions: dict[str, Any],
    trace_summary: dict[str, Any] | None,
    ae_exact_summary: dict[str, Any] | None,
    ae_failure_classification: dict[str, Any] | None,
    binary_followup_report: dict[str, Any] | None,
    bitdepth16_mac_result: dict[str, Any] | None = None,
    bitdepth16_pending: dict[str, Any] | None = None,
    ae_automation_blocker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_return = newest(rows, "runtime-trace-return")
    if runtime_return:
        if trace_summary is None or float(runtime_return.get("mtime", 0)) > float(trace_summary.get("mtime", 0)):
            return {
                "action": "import-runtime-trace-return",
                "reason": "A returned runtime trace package can unblock binary-grounded RadialBlur/KiraKira decisions.",
                "target": runtime_return,
                "command": runtime_return.get("suggested_command", ""),
            }

    win_return = actionable_win_reference_rows(rows, pending_request_defs)
    if win_return:
        row = win_return[0]
        return {
            "action": "import-windows-reference-return",
            "reason": "A returned Windows reference set covers pending requests: "
            + ", ".join(row["covered_pending_requests"]),
            "target": row,
            "command": row.get("suggested_command", ""),
        }

    ae_return = newest(rows, "ae-host-return")
    if ae_return:
        return {
            "action": "import-ae-host-return",
            "reason": "A returned AE-host validation set can prove packaged plug-in behavior.",
            "target": ae_return,
            "command": ae_return.get("suggested_command", ""),
        }

    if ae_automation_blocker:
        blocker_command = ae_automation_blocker.get("next_allowed_action") or (
            "start After Effects normally, clear any hidden startup/script dialog, run "
            "python3 scripts/diagnose_ae_host_block.py, then retry the bounded single-case probe"
        )
        return {
            "action": "clear-mac-ae-automation-blocker",
            "reason": (
                ae_automation_blocker.get("summary")
                or "Mac AE automation is blocked before reliable OLM-specific validation can run."
            ),
            "target": ae_automation_blocker,
            "command": blocker_command,
        }

    staged_runtime_requests = staged_exchange_runtime_requests(rows)
    if staged_runtime_requests:
        staged = staged_runtime_requests[0]
        return {
            "action": "await-runtime-trace-return",
            "reason": (
                "A runtime trace request package is already staged in the Windows "
                "exchange folder; wait for or import its return before sending "
                "additional Windows reference requests."
            ),
            "target": staged,
            "staged_package": staged,
            "command": "wait for the Windows CDB/runtime trace return; do not overwrite the staged request",
            "acceptance_note": staged.get("acceptance_note", ""),
            "pending_windows_refs": len(status.get("pending", [])),
            "pending_runtime_traces": len(runtime_trace_actions(next_actions, trace_summary)),
        }

    project_runtime_packages = project_runtime_trace_packages(root, trace_summary)
    for runtime_package in project_runtime_packages:
        staged_package = staged_runtime_trace_package(runtime_package, rows)
        if staged_package:
            return {
                "action": "await-runtime-trace-return",
                "reason": (
                    "A runtime trace request package is already staged in the Windows "
                    "exchange folder; wait for or import its return before sending "
                    "additional Windows reference requests."
                ),
                "target": runtime_package,
                "staged_package": staged_package,
                "command": "wait for the Windows CDB/runtime trace return; do not overwrite the staged request",
                "acceptance_note": runtime_package.get("acceptance_note", ""),
                "pending_windows_refs": len(status.get("pending", [])),
                "pending_runtime_traces": len(runtime_trace_actions(next_actions, trace_summary)),
            }

    pending = status["pending"]
    if pending and project_runtime_packages:
        runtime_package = project_runtime_packages[0]
        request_ids = runtime_package.get("request_ids", [])
        request_text = ", ".join(request_ids) if request_ids else Path(str(runtime_package.get("path", ""))).stem
        return {
            "action": "send-runtime-trace-package",
            "reason": (
                "A binary-proof runtime trace is pending on the critical path; "
                "send it before the broader Windows PNG reference queue."
            ),
            "target": runtime_package,
            "command": f"send this runtime trace package to the Windows debugger/helper ({request_text})",
            "acceptance_note": runtime_package.get("acceptance_note", ""),
            "deferred_windows_refs": len(pending),
        }
    if pending:
        pinning = pending_pinning_summary(status)
        request_pkg = reference_request_package(root, rows, pending)
        if request_pkg:
            staged_package = staged_reference_request_package(request_pkg, rows)
            if staged_package:
                return {
                    "action": "await-windows-reference-return",
                    "reason": (
                        "A Windows reference request package is already staged in the "
                        "Windows exchange folder; wait for or import its rendered return "
                        "before publishing another request."
                    ),
                    "target": request_pkg,
                    "staged_package": staged_package,
                    "command": "wait for the Windows AE reference return; do not overwrite the staged request",
                    "return_intake_command": win_reference_return_intake_command(pending),
                    "pending_pinning": pinning,
                }
            return {
                "action": "send-windows-reference-package",
                "reason": "All difficult implementation paths are stopped at pending Windows references.",
                "target": request_pkg,
                "command": "send this package to the Windows AE renderer",
                "return_intake_command": win_reference_return_intake_command(pending),
                "pending_pinning": pinning,
            }
        return {
            "action": "package-windows-reference-requests",
            "reason": "Pending Windows references exist, but no request package was found in the scanned paths.",
            "target": None,
            "command": "python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending.zip",
            "pending_pinning": pinning,
        }

    if project_runtime_packages:
        runtime_package = project_runtime_packages[0]
        action_bundle = latest_windows_action_bundle(root, rows)
        bundle_manifest = windows_action_bundle_manifest(Path(str(action_bundle.get("path", "")))) if action_bundle else None
        if not action_bundle_contains_runtime_package(bundle_manifest, runtime_package):
            action_bundle = None
            bundle_manifest = None
        ae_pixel_return = latest_ae_pixel_validation_return(root, rows)
        if (
            action_bundle
            and ae_pixel_return
            and float(ae_pixel_return.get("mtime", 0)) >= float(action_bundle.get("mtime", 0))
        ):
            return {
                "action": "await-runtime-trace-return",
                "reason": "The current Windows action bundle already returned AE pixel validation results; the remaining value is its CDB/runtime trace return.",
                "target": runtime_package,
                "supporting_return": ae_pixel_return,
                "command": "wait for or import the Windows CDB/runtime trace return; if it was not started, send the runtime_trace package listed as target",
            }
        if action_bundle and float(action_bundle.get("mtime", 0)) >= float(runtime_package.get("mtime", 0)):
            focus = str(bundle_manifest.get("priority", "")) if bundle_manifest else ""
            if focus == "blur-kirakira":
                reason = (
                    "No Windows PNG requests are pending; the current project-local Windows bundle "
                    "is focused on OLMBlur and OLMKiraKira runtime traces."
                )
            elif focus == "pending-runtime":
                reason = (
                    "No Windows PNG requests are pending; the current project-local Windows bundle "
                    "wraps all pending runtime trace packages."
                )
            else:
                reason = (
                    "No Windows PNG requests are pending; the current project-local Windows bundle "
                    "wraps the Smoother-first runtime trace and AE exact validation requests."
                )
            return {
                "action": "send-windows-action-bundle",
                "reason": reason,
                "target": action_bundle,
                "command": "send this bundle to the Windows helper",
            }
        request_ids = runtime_package.get("request_ids", [])
        request_text = ", ".join(request_ids) if request_ids else Path(str(runtime_package.get("path", ""))).stem
        staged_package = staged_runtime_trace_package(runtime_package, rows)
        if staged_package:
            return {
                "action": "await-runtime-trace-return",
                "reason": (
                    "The highest-value unresolved runtime trace package is already staged "
                    "in the scanned Windows exchange folder; wait for or import its return."
                ),
                "target": runtime_package,
                "staged_package": staged_package,
                "command": (
                    "wait for the Windows CDB/runtime trace return for "
                    f"{request_text}; do not resend unless the staged package is removed or stale"
                ),
                "acceptance_note": runtime_package.get("acceptance_note", ""),
            }
        return {
            "action": "send-runtime-trace-package",
            "reason": "No Windows PNG requests are pending; the highest-value unresolved proof is a project-local runtime trace package.",
            "target": runtime_package,
            "command": f"send this runtime trace package to the Windows debugger/helper ({request_text})",
            "acceptance_note": runtime_package.get("acceptance_note", ""),
        }

    runtime_actions = runtime_trace_actions(next_actions, trace_summary)
    if runtime_actions:
        if trace_summary:
            summary_target = {
                "path": trace_summary.get("markdown_path") or trace_summary.get("path"),
                "json_path": trace_summary.get("path"),
                "kind": "runtime-trace-summary",
                "answered_request_ids": trace_summary.get("answered_request_ids", []),
            }
            return {
                "action": "dispatch-runtime-trace-followup",
                "reason": "Runtime trace facts are imported; use them for binary-grounded RadialBlur/KiraKira implementation decisions before requesting more refs.",
                "target": summary_target,
                "command": "read refs/reports/runtime_trace_summary.md and assign bounded RadialBlur/KiraKira follow-up from the answered facts",
            }
        runtime_package = latest_runtime_trace_package(root, rows)
        if runtime_package:
            return {
                "action": "send-runtime-trace-package",
                "reason": "PNG references are covered, but hard paths are stopped at debugger/runtime trace facts.",
                "target": runtime_package,
                "command": "send this package to the Windows debugger/helper",
            }
        return {
            "action": "package-runtime-trace-requests",
            "reason": "Runtime trace facts are the next blocker, but no package was found.",
            "target": None,
            "command": "python3 scripts/package_runtime_trace_requests.py",
        }

    if bitdepth16_mac_result and bitdepth16_mac_result.get("status") == "not-ae-exact":
        trace_ids: set[str] = set()
        if trace_summary:
            trace_ids.update(trace_summary.get("answered_request_ids", []))
            trace_ids.update(trace_summary.get("superseded_request_ids", []))
        if "olmdistancegradation_16bpc_case0026_x_witness_20260628" in trace_ids:
            target_path = root / "notes" / "IR_OLMDistanceGradation.md"
            power_fix = root / "refs" / "conformance" / "olmdistancegradation_16bpc_power_param_fix_20260629.md"
            residual_families = (
                root
                / "refs"
                / "conformance"
                / "olmdistancegradation_16bpc_powerfix_residual_families_20260629.md"
            )
            depth_gate_result = (
                root
                / "refs"
                / "conformance"
                / "olmdistancegradation_depth_gate_result_20260708.md"
            )
            if depth_gate_result.exists():
                current_integrated_16bpc = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_current_integrated_16bpc_batch_20260709.md"
                )
                if current_integrated_16bpc.exists():
                    layer_disabled_ab = (
                        root
                        / "refs"
                        / "conformance"
                        / "olmdistancegradation_layer_changes_disabled_ab_20260709.md"
                    )
                    if layer_disabled_ab.exists():
                        old_mask_rejected = (
                            root
                            / "refs"
                            / "conformance"
                            / "olmdistancegradation_source_mask_old_rule_ab_rejected_20260709.md"
                        )
                        if old_mask_rejected.exists():
                            true16_reverify = (
                                root
                                / "refs"
                                / "conformance"
                                / "olmdistancegradation_depthgate_true16_reverify_20260709.md"
                            )
                            if true16_reverify.exists():
                                true16_family_audit = (
                                    root
                                    / "refs"
                                    / "conformance"
                                    / "olmdistancegradation_true16_residual_family_audit_20260709.md"
                                )
                                if true16_family_audit.exists():
                                    ra_quant_probe = (
                                        root
                                        / "refs"
                                        / "conformance"
                                        / "olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md"
                                    )
                                    if ra_quant_probe.exists():
                                        local_field_probe = (
                                            root
                                            / "refs"
                                            / "conformance"
                                            / "olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md"
                                        )
                                        if local_field_probe.exists():
                                            pointer_map_return = (
                                                root
                                                / "refs"
                                                / "conformance"
                                                / "olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md"
                                            )
                                            if pointer_map_return.exists():
                                                pf16_classification = (
                                                    root
                                                    / "refs"
                                                    / "conformance"
                                                    / "olmdistancegradation_0010_0011_pf16_store_classification_20260709.md"
                                                )
                                                if pf16_classification.exists():
                                                    field_pack_audit = (
                                                        root
                                                        / "refs"
                                                        / "conformance"
                                                        / "olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md"
                                                    )
                                                    if field_pack_audit.exists():
                                                        norm_denom_audit = (
                                                            root
                                                            / "refs"
                                                            / "conformance"
                                                            / "olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md"
                                                        )
                                                        if norm_denom_audit.exists():
                                                            field_prep_audit = (
                                                                root
                                                                / "refs"
                                                                / "conformance"
                                                                / "olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.md"
                                                            )
                                                            if field_prep_audit.exists():
                                                                aex_fieldgen_probe = (
                                                                    root
                                                                    / "refs"
                                                                    / "conformance"
                                                                    / "olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md"
                                                                )
                                                                if aex_fieldgen_probe.exists():
                                                                    field_world_return_intake = (
                                                                        root
                                                                        / "refs"
                                                                        / "conformance"
                                                                        / "olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md"
                                                                    )
                                                                    if field_world_return_intake.exists():
                                                                        compose_input_contract = (
                                                                            root
                                                                            / "refs"
                                                                            / "conformance"
                                                                            / "olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md"
                                                                        )
                                                                        if compose_input_contract.exists():
                                                                            compose_input_return_intake = (
                                                                                root
                                                                                / "refs"
                                                                                / "conformance"
                                                                                / (
                                                                                    "olmdistancegradation_0010_0011_"
                                                                                    "compose_input_pointer_return_intake_20260710.md"
                                                                                )
                                                                            )
                                                                            if compose_input_return_intake.exists():
                                                                                compose_exact_address_contract = (
                                                                                    root
                                                                                    / "refs"
                                                                                    / "conformance"
                                                                                    / (
                                                                                        "olmdistancegradation_0010_0011_"
                                                                                        "compose_exact_address_contract_20260710.md"
                                                                                    )
                                                                                )
                                                                                return {
                                                                                    "action": (
                                                                                        "package-distancegradation-0010-0011-compose-exact-address-witness"
                                                                                    ),
                                                                                    "reason": (
                                                                                        "The compose-input return confirms the register roles "
                                                                                        "(`RCX` field-world at `+0x117057d`, `RDX` source/"
                                                                                        "shade at `+0x11705f1`) but missed exact `(6,40)` "
                                                                                        "and `(901,394)` because `rbp=y` is not a reliable "
                                                                                        "discriminator. The next proof should derive field/"
                                                                                        "source/output addresses from base + rowbytes + pixel "
                                                                                        "size and gate the same sites by address."
                                                                                    ),
                                                                                    "target": {
                                                                                        "type": "conformance_report",
                                                                                        "path": str(compose_exact_address_contract),
                                                                                        "request_id": (
                                                                                            "olmdistancegradation_0010_0011_"
                                                                                            "compose_exact_address_witness_20260710"
                                                                                        ),
                                                                                    },
                                                                                    "pending_windows_refs": len(status.get("pending", [])),
                                                                                    "pending_runtime_traces": len(status.get("runtime_pending", [])),
                                                                                }
                                                                            return {
                                                                                "action": (
                                                                                    "package-distancegradation-0010-0011-compose-input-pointer-witness"
                                                                                ),
                                                                                "reason": (
                                                                                    "Static asm corrects the previous late-`rdx` "
                                                                                    "interpretation: at `DistanceGradation+0x1170814`, "
                                                                                    "`rdx` is source/shade input, while the field-world "
                                                                                    "read is built in `RCX` and consumed earlier around "
                                                                                    "`+0x117057d`. The next proof should bind both "
                                                                                    "`RCX` field-world and `RDX` source/shade inputs for "
                                                                                    "the two sparse 16bpc witnesses."
                                                                                ),
                                                                                "target": {
                                                                                    "type": "conformance_report",
                                                                                    "path": str(compose_input_contract),
                                                                                    "request_id": (
                                                                                        "olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709"
                                                                                    ),
                                                                                },
                                                                                "pending_windows_refs": len(status.get("pending", [])),
                                                                                "pending_runtime_traces": len(status.get("runtime_pending", [])),
                                                                            }
                                                                        rdx_producer_contract = (
                                                                            root
                                                                            / "refs"
                                                                            / "conformance"
                                                                            / "olmdistancegradation_0010_0011_rdx_producer_packsite_contract_20260709.md"
                                                                        )
                                                                        return {
                                                                            "action": (
                                                                                "package-distancegradation-0010-0011-rdx-producer-packsite-witness"
                                                                            ),
                                                                            "reason": (
                                                                                "The Windows field-world pack/read return is useful but "
                                                                                "partial: it captured the final-writer read-side `rdx` "
                                                                                "candidate and the retained-run relation `rdx = rdi - "
                                                                                "0xfe0000`, but not the upstream producer/pack site. The "
                                                                                "next proof should watch writes to the derived `rdx` "
                                                                                "addresses before `DistanceGradation+0x1170814`, not repeat "
                                                                                "final PF interleave or the same boundary stop."
                                                                            ),
                                                                            "target": {
                                                                                "type": "conformance_report",
                                                                                "path": str(rdx_producer_contract),
                                                                                "request_id": (
                                                                                    "olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709"
                                                                                ),
                                                                            },
                                                                            "pending_windows_refs": len(status.get("pending", [])),
                                                                            "pending_runtime_traces": len(status.get("runtime_pending", [])),
                                                                        }
                                                                    return {
                                                                        "action": (
                                                                            "package-distancegradation-0010-0011-field-world-pack-read-witness"
                                                                        ),
                                                                        "reason": (
                                                                            "The local real-AEX fieldgen probe reproduces current "
                                                                            "Mac field floats for case_0010/0011, but the Windows-required "
                                                                            "field-word relation sign-flips: outside (6,40) matches floor, "
                                                                            "while inside (901,394) and (915,392) require ceil. The next "
                                                                            "proof is no longer fieldgen/helper or final-writer tuning; "
                                                                            "Windows should bind the real field-world pack/read boundary "
                                                                            "for those exact pixels, with true16 TIFF/EXR only as export "
                                                                            "confirmation."
                                                                        ),
                                                                        "target": {
                                                                            "type": "conformance_report",
                                                                            "path": str(aex_fieldgen_probe),
                                                                            "request_id": (
                                                                                "olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709"
                                                                            ),
                                                                        },
                                                                        "pending_windows_refs": len(status.get("pending", [])),
                                                                        "pending_runtime_traces": len(status.get("runtime_pending", [])),
                                                                    }
                                                                return {
                                                                    "action": (
                                                                        "run-distancegradation-0010-0011-aex-fieldgen-probe"
                                                                    ),
                                                                    "reason": (
                                                                        "OLMDistanceGradation case_0010/0011 now has writer/output "
                                                                        "mapping and an OpenCV field-prep source-shape audit. The "
                                                                        "remaining local discriminator is a case-bound AEX CPU "
                                                                        "fieldgen probe at (6,40), (901,394), and (915,392), with "
                                                                        "threshold/dist_transform/resize_same_shape/normalize_minmax "
                                                                        "detours registered. If it reproduces the Windows-required "
                                                                        "field words, patch Mac field-prep; if it reproduces current "
                                                                        "Mac values, ask Windows for the narrower primitive max/normalize/"
                                                                        "field-world trace or true16 TIFF/EXR same-run export."
                                                                    ),
                                                                    "target": {
                                                                        "type": "conformance_report",
                                                                        "path": str(field_prep_audit),
                                                                        "request_id": (
                                                                            "olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709"
                                                                        ),
                                                                    },
                                                                    "pending_windows_refs": len(status.get("pending", [])),
                                                                    "pending_runtime_traces": len(status.get("runtime_pending", [])),
                                                                }
                                                            return {
                                                                "action": (
                                                                    "inspect-distancegradation-0010-0011-opencv-field-prep"
                                                                ),
                                                                "reason": (
                                                                    "OLMDistanceGradation case_0010/0011 denominator audit "
                                                                    "shows a mixed actual-max/threshold half-boundary family: "
                                                                    "(6,40) is normalized by the outside field's actual max, "
                                                                    "while (901,394) and (915,392) are threshold-limited inside "
                                                                    "witnesses. The next local proof is the AEX/OpenCV field-prep "
                                                                    "detail that measures/clamps max and packs the PF16 field world "
                                                                    "before FUN_181170480 consumes it."
                                                                ),
                                                                "target": {
                                                                    "type": "conformance_report",
                                                                    "path": str(norm_denom_audit),
                                                                    "request_id": (
                                                                        "olmdistancegradation_0010_0011_normalization_denominator_audit_20260709"
                                                                    ),
                                                                },
                                                                "pending_windows_refs": len(status.get("pending", [])),
                                                                "pending_runtime_traces": len(runtime_actions),
                                                            }
                                                        return {
                                                            "action": (
                                                                "inspect-distancegradation-0010-0011-normalization-denominator"
                                                            ),
                                                            "reason": (
                                                                "OLMDistanceGradation case_0010/0011 field-pack/read "
                                                                "audit shows the AEX-shaped PF16 field-world read is the "
                                                                "right boundary to inspect, but simply packing the current "
                                                                "Mac float field with floor/ceil/round cannot match all "
                                                                "sign-flipped witnesses. The next local proof is the "
                                                                "raw-distance / normalization-denominator / OpenCV field-pack "
                                                                "boundary, not final clamp16() and not another broad Windows "
                                                                "request."
                                                            ),
                                                            "target": {
                                                                "type": "conformance_report",
                                                                "path": str(field_pack_audit),
                                                                "request_id": (
                                                                    "olmdistancegradation_0010_0011_field_pack_read_audit_20260709"
                                                                ),
                                                            },
                                                            "pending_windows_refs": len(status.get("pending", [])),
                                                            "pending_runtime_traces": len(runtime_actions),
                                                        }
                                                    return {
                                                        "action": "inspect-distancegradation-0010-0011-field-pack-read",
                                                        "reason": (
                                                            "OLMDistanceGradation case_0010/0011 is now classified "
                                                            "past final rounding: Windows `xmm2_alpha` is already close "
                                                            "to PF16 store words 3268 and 9876 before the writer, while "
                                                            "a global Mac clamp16 truncation/rounding swap would only help "
                                                            "one of the two sign-flipped witnesses. Inspect the 16bpc "
                                                            "field-world pack/read path consumed by FUN_181170480 before "
                                                            "asking Windows for another export-only proof."
                                                        ),
                                                        "target": {
                                                            "type": "conformance_report",
                                                            "path": str(pf16_classification),
                                                            "request_id": (
                                                                "olmdistancegradation_0010_0011_pf16_store_classification_20260709"
                                                            ),
                                                        },
                                                        "pending_windows_refs": len(status.get("pending", [])),
                                                        "pending_runtime_traces": len(runtime_actions),
                                                    }
                                                return {
                                                    "action": "classify-distancegradation-0010-0011-pf16-store",
                                                    "reason": (
                                                        "OLMDistanceGradation case_0010/0011 pointer-map evidence "
                                                        "has returned partial_success_missing_true16_export. It binds "
                                                        "case_0010 (6,40) and (901,394) to the Windows output formula "
                                                        "`out = base + y * 0x3c00 + x * 8` and same-run PF16 final "
                                                        "words 3268 and 9876. Do not resend the same debugger package; "
                                                        "classify the Mac field/compose/float-to-PF16/store/export "
                                                        "split against those words first."
                                                    ),
                                                    "target": {
                                                        "type": "conformance_report",
                                                        "path": str(pointer_map_return),
                                                        "request_id": (
                                                            "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709"
                                                        ),
                                                    },
                                                    "pending_windows_refs": len(status.get("pending", [])),
                                                    "pending_runtime_traces": len(runtime_actions),
                                                }
                                            request_id = (
                                                "olmdistancegradation_0010_0011_field_store_witness_20260709"
                                            )
                                            package_path = (
                                                root
                                                / "refs"
                                                / "runtime_trace_packages"
                                                / "olm_runtime_trace_olmdistancegradation_0010_0011_field_store_witness_20260709.zip"
                                            )
                                            if package_path.exists():
                                                runtime_package = list_olm_return_candidates.build_row(package_path)
                                                runtime_package["kind"] = "runtime-trace-request-package"
                                                runtime_package["request_ids"] = [request_id]
                                                staged_package = staged_runtime_trace_package(runtime_package, rows)
                                                request_statuses = runtime_trace_request_statuses(root, request_id)
                                                latest_status_mtime = runtime_trace_request_latest_mtime(root, request_id)
                                                staged_mtime = 0.0
                                                staged_retry_after_failed_partial = False
                                                if staged_package and staged_package.get("path"):
                                                    staged_path = Path(staged_package["path"])
                                                    try:
                                                        staged_mtime = staged_path.stat().st_mtime
                                                    except OSError:
                                                        staged_mtime = 0.0
                                                    staged_retry_after_failed_partial = zip_contains_text(
                                                        staged_path,
                                                        "The first Windows return for this request is `failed_partial`.",
                                                    )
                                                if (
                                                    ("failed_partial" in request_statuses or "failed" in request_statuses)
                                                    and staged_mtime <= latest_status_mtime
                                                    and not staged_retry_after_failed_partial
                                                ):
                                                    revised_request_id = (
                                                        "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709"
                                                    )
                                                    revised_package_path = (
                                                        root
                                                        / "refs"
                                                        / "runtime_trace_packages"
                                                        / "olm_runtime_trace_olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709.zip"
                                                    )
                                                    revised_contract = (
                                                        "refs/conformance/"
                                                        "olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md"
                                                    )
                                                    revised_target: dict[str, Any]
                                                    if revised_package_path.exists():
                                                        revised_target = list_olm_return_candidates.build_row(
                                                            revised_package_path
                                                        )
                                                        revised_target["kind"] = "runtime-trace-request-package"
                                                        revised_target["request_ids"] = [revised_request_id]
                                                    else:
                                                        revised_target = {
                                                            "type": "runtime_trace_package_profile",
                                                            "path": str(root / revised_contract),
                                                            "request_id": revised_request_id,
                                                        }
                                                    return {
                                                        "action": (
                                                            "package-distancegradation-0010-0011-field-store-prewarm-witness"
                                                        ),
                                                        "reason": (
                                                            "The OLMDistanceGradation case_0010/0011 field/store "
                                                            "witness package has already returned failed_partial. "
                                                            "It narrowed the residual to sign-flipping one-word "
                                                            "PF16 alpha-store differences, but did not include the "
                                                            "required same-run Windows source/field/pre-store/PF16/"
                                                            "export facts because the retained attempt never reached "
                                                            "the DistanceGradation.aex module-load stop. Use the "
                                                            "prewarm retry package so module load is proven before "
                                                            "binding final pixel hooks."
                                                        ),
                                                        "target": revised_target,
                                                        "request_statuses": request_statuses,
                                                        "command": (
                                                            "python3 scripts/package_runtime_trace_requests.py "
                                                            "--profile distancegradation-0010-0011-field-store-prewarm-witness "
                                                            "--output refs/runtime_trace_packages/"
                                                            "olm_runtime_trace_olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709.zip"
                                                        ),
                                                        "acceptance_note": revised_contract,
                                                        "pending_windows_refs": len(status.get("pending", [])),
                                                        "pending_runtime_traces": len(runtime_actions),
                                                    }
                                                if staged_package:
                                                    return {
                                                        "action": "await-runtime-trace-return",
                                                        "reason": (
                                                            "A revised OLMDistanceGradation case_0010/0011 field/store "
                                                            "witness package is staged in the Windows exchange folder; "
                                                            "wait for or import its return."
                                                        ),
                                                        "target": runtime_package,
                                                        "staged_package": staged_package,
                                                        "command": (
                                                            "wait for the Windows CDB/runtime trace return for "
                                                            "olmdistancegradation_0010_0011_field_store_witness_20260709; "
                                                            "do not resend unless the staged package is removed or stale"
                                                        ),
                                                        "acceptance_note": (
                                                            "refs/conformance/"
                                                            "olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md"
                                                        ),
                                                        "pending_windows_refs": len(status.get("pending", [])),
                                                        "pending_runtime_traces": len(runtime_actions),
                                                    }
                                            return {
                                                "action": "package-distancegradation-0010-0011-field-store-witness",
                                                "reason": (
                                                    "OLMDistanceGradation case_0010/0011 are narrowed to sign-flipping "
                                                    "one-word PF16 alpha-store differences exposed as R/A ±2. Local "
                                                    "Mac evidence now shows Mac Meijster EDT and the repository "
                                                    "OpenCV-compatible EDT are bit-identical at the target fields, "
                                                    "and simple field-pack/store simulations are not a safe broad fix. "
                                                    "The next useful proof is a narrow Windows same-run witness for "
                                                    "one Mac-low/Windows-high point and one Mac-high/Windows-low point."
                                                ),
                                                "target": {
                                                    "type": "runtime_trace_package_profile",
                                                    "path": str(local_field_probe),
                                                    "request_id": "olmdistancegradation_0010_0011_field_store_witness_20260709",
                                                },
                                                "run": (
                                                    "python3 scripts/package_runtime_trace_requests.py "
                                                    "--profile distancegradation-0010-0011-field-store-witness "
                                                    "--output refs/runtime_trace_packages/"
                                                    "olm_runtime_trace_olmdistancegradation_0010_0011_field_store_witness_20260709.zip"
                                                ),
                                                "pending_windows_refs": len(status.get("pending", [])),
                                                "pending_runtime_traces": len(runtime_actions),
                                            }
                                        return {
                                            "action": "prove-distancegradation-0010-0011-field-normalization",
                                            "reason": (
                                                "OLMDistanceGradation case_0010/0011 are now narrowed to one-word "
                                                "PF16 alpha-store differences exposed as R/A ±2 in the PNG. The "
                                                "debug witnesses show Render Mode=Gradation Color/no-bg stores full "
                                                "red while visible red follows alpha; the sign flips by point, so a "
                                                "global clamp16 rounding toggle is not justified. The next bounded "
                                                "local proof is the exact distance-field normalization/field-packing "
                                                "rule for the recorded raw distances."
                                            ),
                                            "target": {
                                                "type": "conformance_report",
                                                "path": str(ra_quant_probe),
                                                "request_id": "olmdistancegradation_0010_0011_ra_quantization_probe_20260709",
                                            },
                                            "run": (
                                                "compare the witness raw distances and normalized field_x/store_a "
                                                "against the OpenCV/AEX float path; if local evidence is insufficient, "
                                                "prepare a two-point Windows same-run field/store witness"
                                            ),
                                            "pending_windows_refs": len(status.get("pending", [])),
                                            "pending_runtime_traces": len(runtime_actions),
                                        }
                                    return {
                                        "action": "close-distancegradation-0010-0011-ra-quantization",
                                        "reason": (
                                            "OLMDistanceGradation's true16 residual families are now classified. "
                                            "The smallest live family is case_0010/0011: only R and A differ, all "
                                            "nonzero deltas are abs=2, and the family totals 852 pixels. This is a "
                                            "better next target than the broader Layer/no-bg or field/export families "
                                            "because it can be tested as a narrow PF16 store/export or quantization "
                                            "rule without touching distance-field topology."
                                        ),
                                        "target": {
                                            "type": "conformance_report",
                                            "path": str(true16_family_audit),
                                            "request_id": "olmdistancegradation_true16_residual_family_audit_20260709",
                                        },
                                        "run": (
                                            "probe case_0010/0011 representative R/A pixels with canonical 16bpc "
                                            "arrays and Mac AE debug store logs; only prepare a Windows witness if "
                                            "local PF16 store/export evidence cannot decide the rounding rule"
                                        ),
                                        "pending_windows_refs": len(status.get("pending", [])),
                                        "pending_runtime_traces": len(runtime_actions),
                                    }
                                return {
                                    "action": "classify-distancegradation-true16-residual-families",
                                    "reason": (
                                        "OLMDistanceGradation's old 7/16 depthgate count has been superseded: "
                                        "re-verifying /tmp/olmdg_16ext_depthgate2 with the canonical 16bpc verifier "
                                        "also gives 5/16. The depth-gated source mask remains necessary because "
                                        "global alpha>0 reopens case_0023 and drops the batch to 1/16, but there is "
                                        "no longer a live current-vs-depthgate provenance delta to chase. The next "
                                        "bounded task is to classify and close the real true16 residual families: "
                                        "sparse case_0010/0011, Layer/no-bg case_0012/0013/0014/0016, and "
                                        "case_0024..0028."
                                    ),
                                    "target": {
                                        "type": "conformance_report",
                                        "path": str(true16_reverify),
                                        "request_id": "olmdistancegradation_depthgate_true16_reverify_20260709",
                                    },
                                    "run": (
                                        "use the canonical 16bpc verifier only; do not use PIL/8-bit comparison for "
                                        "16bpc verdicts. Build a per-family true16 residual audit before changing "
                                        "Mac source."
                                    ),
                                    "pending_windows_refs": len(status.get("pending", [])),
                                    "pending_runtime_traces": len(runtime_actions),
                                }
                            return {
                                "action": "isolate-distancegradation-depthgate-provenance-delta",
                                "reason": (
                                    "OLMDistanceGradation's current integrated 16bpc canonical batch is 5/16 exact, "
                                    "while the 2026-07-08 depthgate checkpoint was 7/16. Two local A/Bs narrowed the "
                                    "split: disabling Layer/no-bg compose/inheritance does not recover the RGB/use-bg "
                                    "cases, and reverting source_mask_owns_alpha() to global alpha>0 is much worse "
                                    "(1/16, case_0023 reopened). The depth-gated mask is necessary, so the next bounded "
                                    "task is to find the remaining provenance or mode-specific delta between the "
                                    "depthgate checkpoint and current integrated build."
                                ),
                                "target": {
                                    "type": "conformance_report",
                                    "path": str(old_mask_rejected),
                                    "request_id": "olmdistancegradation_source_mask_old_rule_ab_rejected_20260709",
                                },
                                "run": (
                                    "compare current source/build against the depthgate checkpoint assumptions; check "
                                    "whether depthgate applies too broadly by mode without replacing it globally, and "
                                    "validate every candidate with the canonical 16bpc batch"
                                ),
                                "pending_windows_refs": len(status.get("pending", [])),
                                "pending_runtime_traces": len(runtime_actions),
                            }
                        return {
                            "action": "ab-distancegradation-source-mask-scope",
                            "reason": (
                                "OLMDistanceGradation's current integrated 16bpc canonical batch is 5/16 exact, "
                                "while the 2026-07-08 depthgate checkpoint was 7/16. Disabling the Layer/no-bg "
                                "compose/inheritance changes did not recover case_0010/0011/0024..0028, so the "
                                "next bounded task is to A/B the global 16bpc source_mask_owns_alpha rule or "
                                "limit that depth-gated mask to the binary-grounded mode family while preserving "
                                "case_0023 and the Layer/no-bg improvements."
                            ),
                            "target": {
                                "type": "conformance_report",
                                "path": str(layer_disabled_ab),
                                "request_id": "olmdistancegradation_layer_changes_disabled_ab_20260709",
                            },
                            "run": (
                                "test alpha>0 vs alpha>1.5/255 source-mask ownership under the canonical 16bpc "
                                "batch, then try the narrowest mode-specific depthgate rule that keeps case_0023 "
                                "exact without regressing RGB/use-bg cases"
                            ),
                            "pending_windows_refs": len(status.get("pending", [])),
                            "pending_runtime_traces": len(runtime_actions),
                        }
                    return {
                        "action": "isolate-distancegradation-16bpc-integration-split",
                        "reason": (
                            "OLMDistanceGradation's current integrated 16bpc canonical batch is 5/16 exact, "
                            "while the 2026-07-08 depthgate checkpoint was 7/16. Later Layer/no-bg work "
                            "greatly improves case_0012/0013/0014/0016, but the current build is worse than "
                            "the depthgate baseline for case_0010/0011/0024..0028. The next bounded task is "
                            "to isolate which post-depthgate change moved RGB/use-bg and near-miss families, "
                            "then keep the Layer improvements without losing the depthgate baseline."
                        ),
                        "target": {
                            "type": "conformance_report",
                            "path": str(current_integrated_16bpc),
                            "request_id": "olmdistancegradation_current_integrated_16bpc_batch_20260709",
                        },
                        "run": (
                            "bisect the post-depthgate DG changes with the canonical 16bpc batch; do not "
                            "call the current build 7/16 and do not request more Windows data for the old "
                            "case_0024..0027 max=1 family until the Mac build is back to that shape"
                        ),
                        "pending_windows_refs": len(status.get("pending", [])),
                        "pending_runtime_traces": len(runtime_actions),
                    }
                nearmiss_witness = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_depthgate_nearmiss_witness_20260708.md"
                )
                quantization_intake = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_depthgate_quantization_return_intake_20260708.md"
                )
                layer_both_lowalpha = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_layer_both_lowalpha_20260708.md"
                )
                layer_case0012_pointdebug = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_case0012_pointdebug_20260708.md"
                )
                layer_case0012_closeout = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_case0012_dominant_channel_closeout_20260708.md"
                )
                layer_lowalpha_final = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_layer_lowalpha_final_20260708.md"
                )
                layer_straight_patch = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_layer_straight_patch_20260708.md"
                )
                if layer_case0012_closeout.exists():
                    return {
                        "action": "continue-distancegradation-16bpc-export-rounding-closeout",
                        "reason": (
                            "OLMDistanceGradation 16bpc Layer/no-bg source ownership is now narrowed: "
                            "the dominant-channel Both mask rule reduces case_0012 from true16 max 28 "
                            "to max 2 and preserves case_0013/0014/0016 at 2/4/2. The remaining family "
                            "is shared 16bpc export/rounding, not broad Layer-source topology."
                        ),
                        "target": {
                            "type": "conformance_report",
                            "path": str(layer_case0012_closeout),
                            "request_id": "olmdistancegradation_case0012_dominant_channel_closeout_20260708",
                        },
                        "run": (
                            "classify the remaining max 2/4 true16 residual as AE export rounding, "
                            "PF16 store rounding, or Windows store/export behavior; preserve the "
                            "dominant-channel 150/255 guard and do not broaden it without proof"
                        ),
                        "pending_windows_refs": len(status.get("pending", [])),
                        "pending_runtime_traces": len(runtime_actions),
                    }
                if layer_case0012_pointdebug.exists():
                    return {
                        "action": "continue-distancegradation-layer-source-closeout",
                        "reason": (
                            "OLMDistanceGradation 16bpc case_0012 is now isolated to a uniform "
                            "Layer/no-bg Both low-alpha store/export-scaling band: sampled max-delta "
                            "points share source [195,195,195,3597], field_x 0.00819672085, "
                            "and Mac pre-export store [1785,1785,1785,32499], while the true16 "
                            "PNG comparison remains candidate [3539,3539,3539,64997] vs Windows "
                            "[3567,3567,3567,64997]."
                        ),
                        "target": {
                            "type": "conformance_report",
                            "path": str(layer_case0012_pointdebug),
                            "request_id": "olmdistancegradation_case0012_pointdebug_20260708",
                        },
                        "run": (
                            "bind the PF16 store values to exported true16 PNG values and decide "
                            "whether the missing +28 RGB is pre-store rounding, AE export scaling, "
                            "or Windows store/export behavior; do not broaden the low-alpha rule"
                        ),
                        "pending_windows_refs": len(status.get("pending", [])),
                        "pending_runtime_traces": len(runtime_actions),
                    }
                if layer_both_lowalpha.exists():
                    return {
                        "action": "continue-distancegradation-layer-source-closeout",
                        "reason": (
                            "The OLMDistanceGradation 16bpc Layer/no-bg Both low-alpha channel-mask "
                            "rule keeps case_0013/0014/0016 at true16 max 2/4/2 and reduces case_0012 "
                            "from max 90 to max 28. This is now a narrow case_0012 low-alpha "
                            "quantization/source-word lane, not a broad Layer-source rewrite lane."
                        ),
                        "target": {
                            "type": "conformance_report",
                            "path": str(layer_both_lowalpha),
                            "request_id": "olmdistancegradation_layer_both_lowalpha_20260708",
                        },
                        "run": (
                            "focus OLMDistanceGradation case_0012 remaining low-alpha word/rounding "
                            "residual around source alpha 3597; preserve the 8bpc Layer/no-bg path, "
                            "the 16bpc straight-source RGB rule, and the Both-only low-alpha channel-mask rule"
                        ),
                        "pending_windows_refs": len(status.get("pending", [])),
                        "pending_runtime_traces": len(runtime_actions),
                    }
                if layer_lowalpha_final.exists():
                    return {
                        "action": "continue-distancegradation-layer-source-closeout",
                        "reason": (
                            "The OLMDistanceGradation 16bpc Layer/no-bg low-alpha hidden-color patch "
                            "keeps case_0013/0014/0016 at true16 max 2/4/2 and reduces case_0012 "
                            "from max 251 to max 90. This is now a narrower case_0012 low-alpha "
                            "fringe/quantization lane, not a broad Layer-source rewrite lane."
                        ),
                        "target": {
                            "type": "conformance_report",
                            "path": str(layer_lowalpha_final),
                            "request_id": "olmdistancegradation_layer_lowalpha_final_20260708",
                        },
                        "run": (
                            "focus OLMDistanceGradation case_0012 remaining low-alpha premultiplied "
                            "source-fringe pixels and true16 quantization; preserve the 8bpc Layer/no-bg "
                            "path, the 16bpc straight-source RGB rule, and the current narrow hidden-color rule"
                        ),
                        "pending_windows_refs": len(status.get("pending", [])),
                        "pending_runtime_traces": len(runtime_actions),
                    }
                if layer_straight_patch.exists():
                    return {
                        "action": "continue-distancegradation-layer-source-closeout",
                        "reason": (
                            "The OLMDistanceGradation 16bpc Layer/no-bg straight-source RGB patch "
                            "reduced case_0013/0014/0016 to true16 max 2/4/2 and leaves case_0012 "
                            "as the only substantial Layer-source residual (true16 max 251). This is "
                            "now a narrower local closeout lane than the old broad Layer-source family."
                        ),
                        "target": {
                            "path": str(layer_straight_patch),
                            "kind": "ae-host-grounded-layer-source-rerun",
                            "request_id": "olmdistancegradation_layer_straight_patch_20260708",
                        },
                        "command": (
                            "focus OLMDistanceGradation case_0012 low-alpha source-fringe/background "
                            "ownership and the remaining true16 quantization rule; preserve the 8bpc "
                            "Layer/no-bg path and do not reapply final-alpha RGB scaling for 16bpc"
                        ),
                    }
                if (
                    "olmdistancegradation_depthgate_quantization_witness_20260708" in trace_ids
                    and quantization_intake.exists()
                ):
                    return {
                        "action": "decide-distancegradation-depthgate-endgame",
                        "reason": (
                            "The OLMDistanceGradation depth-gate quantization witness has returned. "
                            "Three of four clean case_0026 representatives classify as "
                            "16bpc-to-export quantization, and only `(907,222)` remains unresolved. "
                            "Do not repeat broad field/source/compose tuning from this near-miss family."
                        ),
                        "target": {
                            "path": str(quantization_intake),
                            "kind": "runtime-trace-intake",
                            "request_id": "olmdistancegradation_depthgate_quantization_witness_20260708",
                        },
                        "command": (
                            "either close `(907,222)` with one direct Windows PF16 store/export stop, "
                            "or move OLMDistanceGradation attention to the separate broad Layer-source "
                            "family `case_0012/0013/0014`"
                        ),
                    }
                if nearmiss_witness.exists():
                    return {
                        "action": "prove-distancegradation-depthgate-quantization-witness",
                        "reason": (
                            "OLMDistanceGradation depth-gate follow-up has classified case_0024..0027 "
                            "as a coherent max=1 near-miss family. Mac AE debug witnesses for the clean "
                            "case_0026/case_0027 pair point at compose/interpolation/store/export "
                            "quantization rather than distance-field topology. The next bounded proof is "
                            "a Windows or local AEX-level pre-store/export witness for selected case_0026 "
                            "points, not a field/source-mask retune."
                        ),
                        "target": {
                            "path": str(nearmiss_witness),
                            "kind": "ae-host-grounded-nearmiss-witness",
                            "request_id": "olmdistancegradation_depthgate_nearmiss_20260708",
                        },
                        "command": (
                            "use case_0026 points (907,222), (395,477), (1589,579), (898,670) "
                            "with case_0027 as Render Mode control; prove whether Windows differs at "
                            "interpolation output float, PF_Pixel16 store rounding/clamp, or AE PNG export"
                        ),
                    }
                return {
                    "action": "classify-distancegradation-depthgate-nearmiss-family",
                    "reason": (
                        "The current primary OLMDistanceGradation evidence is the 2026-07-08 "
                        "depth-gated source-mask result. It closes 16bpc case_0023, improves "
                        "the 16bpc extended batch to 7/16 AE exact, preserves the 8bpc code path "
                        "as HEAD-equivalent by using alpha > 0 for PF_Pixel8, and records why "
                        "run_ae_single_case.py must not be used as an 8bpc verdict runner. The "
                        "next bounded DG lane is the new max=1 near-miss family case_0024..0027, "
                        "not another case_0023 ownership proof."
                    ),
                    "target": {
                        "path": str(depth_gate_result),
                        "kind": "ae-host-grounded-depth-gate-result",
                        "request_id": "olmdistancegradation_depth_gate_20260708",
                    },
                    "command": (
                        "classify /tmp/olmdg_16ext_depthgate2 case_0024..0027 diff positions "
                        "and parameter correlations; keep case_0012/0013/0014 as the separate "
                        "Layer-source family and do not use CLI reimplementation as Windows truth"
                    ),
                }
            case0023_alpha_threshold_result = (
                root
                / "refs"
                / "conformance"
                / "olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md"
            )
            if residual_families.exists() and not case0023_alpha_threshold_result.exists():
                case0023_lane_state = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_case0023_lane_state_20260707.md"
                )
                both_add_overlap = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_both_add_overlap_audit_20260707.md"
                )
                case0020_field = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_16bpc_case0020_field_witness_20260629.md"
                )
                constant_binary_fix = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_16bpc_constant_binary_fix_20260629.md"
                )
                constant_boundary = (
                    root
                    / "refs"
                    / "conformance"
                    / "olmdistancegradation_16bpc_constant_remaining_boundary_20260629.md"
                )
                target_for_distancegradation = (
                    case0023_lane_state
                    if case0023_lane_state.exists()
                    else both_add_overlap
                    if both_add_overlap.exists()
                    else constant_boundary
                    if constant_boundary.exists()
                    else constant_binary_fix
                    if constant_binary_fix.exists()
                    else case0020_field
                    if case0020_field.exists()
                    else residual_families
                )
                target_kind = "residual-family-report"
                target_request_id = "olmdistancegradation_16bpc_case0026_x_witness_20260628"
                if case0023_lane_state.exists():
                    target_kind = "lane-state-report"
                    target_request_id = "olmdistancegradation_case0023_final_source_ownership_20260707"
                elif both_add_overlap.exists():
                    target_kind = "local-model-audit"
                    target_request_id = "olmdistancegradation_both_add_overlap_audit_20260707"
                elif constant_boundary.exists():
                    target_kind = "boundary-localization-report"
                elif constant_binary_fix.exists():
                    target_kind = "implementation-fix-report"
                elif case0020_field.exists():
                    target_kind = "field-witness-report"
                return {
                    "action": "prove-distancegradation-16bpc-residual-family",
                    "reason": (
                        "The 16bpc DistanceGradation Power-value bug is fixed and the remaining "
                        "extended failures are split into residual families. Constant mode now uses "
                        "the binary threshold path grounded in FUN_181174760. The active case_0023 "
                        "lane is now bounded by a 2026-07-07 reference export audit: the packaged "
                        "2026-06-25 16bpc Windows reference is byte-identical to the 2026-07-03 and "
                        "2026-07-06 current-AEX Windows recaptures. The 2026-07-07 AEX CPU helper witness also "
                        "shows the Both add-saturate helper already produces the live edge zero. "
                        "The 2026-07-07 Mac source-model audit matches those AEX helper samples, and "
                        "the compose witness executes FUN_181170480 locally as a recorded field-to-color "
                        "mapping check. The Mac-only bg_on/bg_off probe then shows "
                        "identical debug fields in both modes while the exported PNGs still differ from "
                        "Windows by 73px. The same probe now also captures source RGBA, x_row/a_row, "
                        "compose floats, and 16bpc stores; those stores match the Mac PNG after "
                        "transparent-RGB zeroing. The neighborhood probe then shows the sampled 3x3 "
                        "neighborhoods differ only at (1699,7) and (415,393), and logged shade source "
                        "matches the request input PNG under AE PF_Pixel16 promotion. The 2026-07-07 "
                        "final/source ownership return is answered: (1699,7) is a Windows source/mask "
                        "ownership lane, and (415,393) is an export/path split lane. This closes the "
                        "send-first runtime trace request without justifying stale-reference, broad "
                        "field-helper, Both-merge, compose, or source-input tuning."
                    ),
                    "target": {
                        "path": str(target_for_distancegradation),
                        "kind": target_kind,
                        "request_id": target_request_id,
                    },
                    "command": (
                        "use refs/conformance/olmdistancegradation_case0023_lane_state_20260707.md "
                        "as the live DG lane; preserve the Power and Constant binary-threshold fixes, "
                        "keep the packaged/current Windows reference exactness, Both-mode cv::add, the "
                        "source-model/AEX-helper sampled equivalence, and the compose/writeback mapping "
                        "witness, refs/conformance/olmdistancegradation_case0023_mac_probe_result_20260707.md "
                        "as IR facts, refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md "
                        "as the bounded neighborhood/source-input fact, and "
                        "refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_final_source_ownership_20260707.md "
                        "as the answered final/source ownership proof; next DG work must be narrow "
                        "Mac-side source/mask/output ownership closeout, not a resend or broad retune"
                    ),
                }
            if power_fix.exists():
                return {
                    "action": "classify-distancegradation-16bpc-powerfix-residuals",
                    "reason": (
                        "The case_0026 field-prep and Power-value collapse are now explained: "
                        "the port was applying FIX_2_FLOAT to an already-floating Power param. "
                        "After the fix, extended 16bpc is still not AE exact, so the next work "
                        "is residual-family classification rather than another Windows trip."
                    ),
                    "target": {
                        "path": str(power_fix),
                        "kind": "ae-host-grounded-implementation-fix",
                        "request_id": "olmdistancegradation_16bpc_case0026_x_witness_20260628",
                    },
                    "command": (
                        "classify refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424 "
                        "by Constant/background, Power/source, and compose/writeback residual families"
                    ),
                }
            current_mac_rerun = (
                root
                / "refs"
                / "conformance"
                / "olmdistancegradation_16bpc_case0026_current_mac_ae_rerun_20260629.md"
            )
            if current_mac_rerun.exists():
                return {
                    "action": "inspect-mac-distancegradation-case0026-field-prep",
                    "reason": (
                        "The Windows trace proves case_0026 ramps before compose, and the "
                        "current Mac AE rerender still saturates to the Gradation Color endpoint. "
                        "The active mismatch is now Mac field-prep or installed-binary behavior, "
                        "not a stale PNG or Windows compose branch."
                    ),
                    "target": {
                        "path": str(target_path),
                        "kind": "binary-grounded-ir",
                        "request_id": "olmdistancegradation_16bpc_case0026_x_witness_20260628",
                    },
                    "command": (
                        "inspect mac/OLMDistanceGradation field-prep for 16bpc case_0026 and "
                        "verify the installed plug-in binary/source path before changing compose"
                    ),
                }
            return {
                "action": "recover-mac-ae-distancegradation-case0026-render",
                "reason": (
                    "The Windows case_0026 field/X witness has returned: the ramp exists before "
                    "16bpc compose. The remaining proof is a current Mac AE rerender, currently "
                    "blocked by the AE host dialog/automation issue."
                ),
                "target": {
                    "path": str(target_path),
                    "kind": "binary-grounded-ir",
                    "request_id": "olmdistancegradation_16bpc_case0026_x_witness_20260628",
                },
                "command": (
                    "launch/clear Mac AE, run python3 scripts/diagnose_ae_host_block.py, "
                    "then rerender only olmdistancegradation_extended__case_0026 with the "
                    "current installed plug-in"
                ),
            }
        if (
            binary_followup_report
            and binary_followup_report.get("mtime", 0) >= bitdepth16_mac_result.get("mtime", 0)
        ):
            return {
                "action": "continue-binary-grounded-followup",
                "reason": (
                    "Mac AE 16bpc validation is not exact, and a newer residual report has "
                    "already classified the largest current residual; continue from that proof "
                    "instead of re-reading the broad validation summary."
                ),
                "target": binary_followup_report,
                "command": "read the residual report and capture/prove the named field/X witness",
            }
        return {
            "action": "investigate-16bpc-mac-ae-residuals",
            "reason": (
                "Mac AE 16bpc validation has been run and is not exact; do not rerun the same bundle "
                "until the 16bpc residual classes are explained or implementation changes are made."
            ),
            "target": bitdepth16_mac_result,
            "command": "read the target markdown_path and start with the largest 16bpc residual class",
        }

    if bitdepth16_pending:
        return {
            "action": "prepare-mac-ae-16bpc-validation",
            "reason": (
                "ColorKey Edge, DistanceGradation, and OLMBlur already have covered Windows "
                "Software 16bpc references; the next proof is Mac AE 16bpc comparison, not "
                "more Windows PNGs or Smoother2 producer tracing."
            ),
            "target": bitdepth16_pending,
            "command": (
                "run the bundled 16bpc AE-host validation requests on Mac AE and return rendered PNGs; "
                "verify the return directory with scripts/verify_ae_pixel_validation_batch.py"
            ),
        }

    if ae_exact_summary and not ae_exact_summary.get("all_exact"):
        if ae_failure_classification and ae_failure_classification.get("is_current"):
            target = ae_failure_classification
            reason = "AE-host exact failures are already classified; continue from the classified residuals instead of re-reading the summary."
            command = "read the classification report, then work the next binary-grounded residual or package a clean normalized AE-host request"
            if (
                binary_followup_report
                and binary_followup_report.get("mtime", 0) >= ae_failure_classification.get("mtime", 0)
            ):
                target = binary_followup_report
                reason = "AE-host exact failures are classified and newer binary-grounded residual reports exist; continue from the latest residual report."
                command = "read the latest residual report/IR and work the next narrow binary-grounded proof"
            return {
                "action": "continue-binary-grounded-followup",
                "reason": reason,
                "target": target,
                "command": command,
            }
        return {
            "action": "analyze-ae-host-exact-failures",
            "reason": "AE-host exact validation has returned and not all cases are exact; classify failures before sending another package.",
            "target": {
                "path": ae_exact_summary.get("path", ""),
                "json_path": ae_exact_summary.get("json_path", ""),
                "kind": "ae-host-exact-summary",
                "exact_count": ae_exact_summary.get("exact_count"),
                "case_count": ae_exact_summary.get("case_count"),
            },
            "command": "read the AE_HOST_EXACT_SUMMARY.md report and split exact cases from binary-grounded residuals",
        }

    if handoff.get("valid"):
        return {
            "action": "send-ae-host-validation-package",
            "reason": "Windows references are covered; next proof is AE-host validation of packaged plug-ins.",
            "target": handoff,
            "command": f"send {handoff['path']} to the AE host and return AE_VALIDATION_RESULT*.json plus pixel PNGs",
        }
    return {
        "action": "rebuild-handoff-package",
        "reason": "No valid current handoff package was found.",
        "target": handoff,
        "command": "scripts/package_olm_handoff.sh --output /tmp/olm_port_handoff_current.zip",
    }


def main() -> int:
    args = parse_args()
    root = repo_root()
    rows = candidate_rows(args.paths)
    rows.extend(candidate_rows([root / "handoffs" / "windows_batch"]))
    rows = list({str(Path(str(row.get("path", ""))).resolve()): row for row in rows if row.get("path")}.values())
    interesting = [row for row in rows if row.get("kind") != "unknown"]
    status_rows = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    status = {
        "pending": [
            row.get("request_id")
            for row in status_rows
            if isinstance(row, dict) and row.get("status") != "covered" and isinstance(row.get("request_id"), str)
        ],
        "covered": [
            row.get("request_id")
            for row in status_rows
            if isinstance(row, dict) and row.get("status") == "covered" and isinstance(row.get("request_id"), str)
        ],
        "rows": status_rows,
    }
    next_actions = build_reference_action_data(status_rows)
    trace_summary = runtime_trace_summary(root)
    ae_exact_summary = ae_host_exact_summary(root)
    ae_failure_classification = ae_host_failure_classification(root, ae_exact_summary)
    binary_followup = binary_grounded_followup_report(root)
    bitdepth16_mac_result = bitdepth16_mac_validation_result(root)
    bitdepth16_pending = bitdepth16_compare_pending(root)
    ae_automation_blocker = ae_host_automation_blocker(root)
    pending_request_defs = pending_requests(root, status["pending"])
    pending_runtime_rows = pending_runtime_trace_rows(root)
    handoff_path = args.handoff
    if handoff_path is None:
        latest_handoff = newest(interesting, "olm-handoff-package")
        if latest_handoff and latest_handoff.get("path"):
            handoff_path = Path(str(latest_handoff["path"]))
    handoff = handoff_summary(root, handoff_path)
    decision = decide(
        root,
        interesting,
        status,
        handoff,
        pending_request_defs,
        next_actions,
        trace_summary,
        ae_exact_summary,
        ae_failure_classification,
        binary_followup,
        bitdepth16_mac_result,
        bitdepth16_pending,
        ae_automation_blocker,
    )

    output = {
        "decision": decision,
        "pending_requests": status["pending"],
        "pending_runtime_trace_requests": [
            {
                "request_id": row.get("request_id"),
                "package": row.get("package"),
                "priority": row.get("priority"),
                "acceptance_note": row.get("acceptance_note"),
            }
            for row in pending_runtime_rows
        ],
        "pending_pinning": pending_pinning_summary(status),
        "covered_requests": status["covered"],
        "runtime_trace_actions": [
            action.get("request_id")
            for action in runtime_trace_actions(next_actions, trace_summary)
            if isinstance(action.get("request_id"), str)
        ],
        "runtime_trace_summary": trace_summary,
        "ae_host_exact_summary": ae_exact_summary,
        "ae_host_failure_classification": ae_failure_classification,
        "binary_grounded_followup_report": binary_followup,
        "ae_host_automation_blocker": ae_automation_blocker,
        "bitdepth16_mac_validation_result": bitdepth16_mac_result,
        "bitdepth16_compare_pending": bitdepth16_pending,
        "handoff": handoff,
        "candidates": interesting[:12],
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0

    print("OLM next action")
    print(f"- action: {decision['action']}")
    print(f"- reason: {decision['reason']}")
    target = decision.get("target")
    if isinstance(target, dict) and target.get("path"):
        print(f"- target: {target['path']}")
    if decision.get("command"):
        print(f"- run/do: {decision['command']}")
    if decision.get("acceptance_note"):
        print(f"- acceptance note: {decision['acceptance_note']}")
    if decision.get("return_intake_command"):
        print(f"- after return: {decision['return_intake_command']}")
    print(f"- pending Windows refs: {len(status['pending'])}")
    if status["pending"]:
        print("  " + ", ".join(status["pending"]))
    print(f"- pending runtime traces: {len(pending_runtime_rows)}")
    if pending_runtime_rows:
        print(
            "  "
            + ", ".join(
                str(row.get("request_id") or "")
                for row in pending_runtime_rows
                if row.get("request_id")
            )
        )
    pinning = decision.get("pending_pinning") or output.get("pending_pinning")
    if isinstance(pinning, dict):
        print(
            "- pending pinning: "
            f"current {pinning.get('current_params_full_cases', 0)}/{pinning.get('total_cases', 0)} "
            f"-> packaged {pinning.get('packaged_params_full_cases', 0)}/{pinning.get('total_cases', 0)} "
            f"(linked {pinning.get('linked_cases', 0)}, improved requests {pinning.get('improved_requests', 0)})"
        )
        summaries = pinning.get("request_summaries") or []
        if summaries:
            print("  " + " | ".join(str(item) for item in summaries))
    if decision["action"] in {"send-ae-host-validation-package", "rebuild-handoff-package"}:
        if handoff.get("valid"):
            dirty = " dirty" if handoff.get("git_dirty") else ""
            print(f"- handoff: {handoff['path']} @ {handoff.get('git_commit', '')}{dirty}")
        else:
            print(f"- handoff problem: {handoff.get('problem', 'not valid')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
