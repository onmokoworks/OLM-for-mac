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
)
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
        default=Path("/tmp/olm_port_handoff_20260606_current.zip"),
        help="Current handoff package path.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def pending_requests(root: Path, request_ids: list[str]) -> list[dict[str, Any]]:
    request_dir = root / "refs" / "reference_requests"
    requests = []
    for request_id in request_ids:
        path = request_dir / f"{request_id}.json"
        if path.exists():
            requests.append(load_json(path))
    return requests


def handoff_summary(root: Path, handoff: Path) -> dict[str, Any]:
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
    return [
        list_olm_return_candidates.build_row(path)
        for path in list_olm_return_candidates.candidate_paths(paths)
    ]


def newest(rows: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("kind") == kind]
    if not matches:
        return None
    return max(matches, key=lambda row: float(row.get("mtime", 0)))


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
    required_cases = {
        case["id"]
        for case in request.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str) and not case.get("optional")
    }
    if required_cases and not required_cases <= manifest_case_ids(manifest):
        return False
    found_sets = manifest_render_sets(manifest)
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
    rows: list[dict[str, Any]],
    status: dict[str, Any],
    handoff: dict[str, Any],
    pending_request_defs: list[dict[str, Any]],
) -> dict[str, Any]:
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
        request_pkg = newest(rows, "reference-request-package")
        if request_pkg:
            return {
                "action": "send-windows-reference-package",
                "reason": "All difficult implementation paths are stopped at pending Windows references.",
                "target": request_pkg,
                "command": "send this package to the Windows AE renderer",
            }
        return {
            "action": "package-windows-reference-requests",
            "reason": "Pending Windows references exist, but no request package was found in the scanned paths.",
            "target": None,
            "command": "python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending_20260606.zip",
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
        "command": "scripts/package_olm_handoff.sh --output /tmp/olm_port_handoff_20260606_current.zip",
    }


def main() -> int:
    args = parse_args()
    root = repo_root()
    rows = candidate_rows(args.paths)
    interesting = [row for row in rows if row.get("kind") != "unknown"]
    status = request_status(root)
    pending_request_defs = pending_requests(root, status["pending"])
    handoff = handoff_summary(root, args.handoff)
    decision = decide(interesting, status, handoff, pending_request_defs)

    output = {
        "decision": decision,
        "pending_requests": status["pending"],
        "covered_requests": status["covered"],
        "handoff": handoff,
        "candidates": interesting[:12],
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0

    print("OLM next action")
    print(f"- action: {decision['action']}")
    print(f"- reason: {decision['reason']}")
    if decision.get("command"):
        print(f"- run/do: {decision['command']}")
    print(f"- pending Windows refs: {len(status['pending'])}")
    if status["pending"]:
        print("  " + ", ".join(status["pending"]))
    if handoff.get("valid"):
        dirty = " dirty" if handoff.get("git_dirty") else ""
        print(f"- handoff: {handoff['path']} @ {handoff.get('git_commit', '')}{dirty}")
    else:
        print(f"- handoff problem: {handoff.get('problem', 'not valid')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
