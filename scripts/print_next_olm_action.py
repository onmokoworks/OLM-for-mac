#!/usr/bin/env python3
"""Print the next highest-value OLM porting action from current artifacts."""

from __future__ import annotations

import argparse
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
    expected_required_sets,
    manifest_case_ids,
    manifest_render_sets,
    relevant_manifest_cases,
)
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
    script = root / "refs" / "scripts" / "check_reference_request_status.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--json"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    data = json.loads(proc.stdout)
    requests = data.get("requests", [])
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


def next_reference_actions(root: Path) -> dict[str, Any]:
    script = root / "refs" / "scripts" / "next_reference_actions.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--json"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    data = json.loads(proc.stdout)
    return data if isinstance(data, dict) else {}


def runtime_trace_actions(
    next_actions: dict[str, Any],
    trace_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actions = next_actions.get("covered_actions", [])
    if not isinstance(actions, list):
        return []
    answered = set(trace_summary.get("answered_request_ids", [])) if trace_summary else set()
    answered.update(trace_summary.get("superseded_request_ids", []) if trace_summary else [])
    return [
        action
        for action in actions
        if isinstance(action, dict)
        and (action.get("status") == "runtime-trace" or action.get("mode") == "external-trace")
        and action.get("request_id") not in answered
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
        matches.extend(
            list_olm_return_candidates.build_row(path)
            for path in package_dir.glob("*.zip")
            if path.is_file()
        )
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
        if request_ids and all(request_id in stale_request_ids for request_id in request_ids):
            continue
        profile = str(manifest.get("profile", ""))
        if request_ids and all(request_id in answered for request_id in request_ids):
            continue
        row = list_olm_return_candidates.build_row(path)
        row["profile"] = profile
        row["request_ids"] = request_ids
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
        "radialblur-residual-witness",
        "kirakira-boxfilter-pass1-microprobe",
        "directionalblur-residual-witness",
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
    roots = paths or [Path.home() / "Downloads", Path("/tmp")]
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

    pending = status["pending"]
    if pending:
        request_pkg = reference_request_package(root, rows, pending)
        if request_pkg:
            return {
                "action": "send-windows-reference-package",
                "reason": "All difficult implementation paths are stopped at pending Windows references.",
                "target": request_pkg,
                "command": "send this package to the Windows AE renderer",
                "return_intake_command": win_reference_return_intake_command(pending),
            }
        return {
            "action": "package-windows-reference-requests",
            "reason": "Pending Windows references exist, but no request package was found in the scanned paths.",
            "target": None,
            "command": "python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending.zip",
        }

    project_runtime_packages = project_runtime_trace_packages(root, trace_summary)
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
        return {
            "action": "send-runtime-trace-package",
            "reason": "No Windows PNG requests are pending; the highest-value unresolved proof is a project-local runtime trace package.",
            "target": runtime_package,
            "command": f"send this runtime trace package to the Windows debugger/helper ({request_text})",
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
    status = request_status(root)
    next_actions = next_reference_actions(root)
    trace_summary = runtime_trace_summary(root)
    ae_exact_summary = ae_host_exact_summary(root)
    ae_failure_classification = ae_host_failure_classification(root, ae_exact_summary)
    binary_followup = binary_grounded_followup_report(root)
    pending_request_defs = pending_requests(root, status["pending"])
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
    )

    output = {
        "decision": decision,
        "pending_requests": status["pending"],
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
    if decision.get("return_intake_command"):
        print(f"- after return: {decision['return_intake_command']}")
    print(f"- pending Windows refs: {len(status['pending'])}")
    if status["pending"]:
        print("  " + ", ".join(status["pending"]))
    if decision["action"] in {"send-ae-host-validation-package", "rebuild-handoff-package"}:
        if handoff.get("valid"):
            dirty = " dirty" if handoff.get("git_dirty") else ""
            print(f"- handoff: {handoff['path']} @ {handoff.get('git_commit', '')}{dirty}")
        else:
            print(f"- handoff problem: {handoff.get('problem', 'not valid')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
