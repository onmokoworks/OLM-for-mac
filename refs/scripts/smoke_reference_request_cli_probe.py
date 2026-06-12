#!/usr/bin/env python3
"""Run a permissive CLI probe for a covered Windows reference request.

This is an import-time analysis hook, not a green correctness gate. It exits 0
while the request is pending. Once refs are imported, it verifies coverage is
available, prints the request case mapping, runs the requested CLI on matching
manifest cases, and leaves diff reports under /tmp for the parent/sub-agents to
inspect before promoting any implementation changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_reference_request_status import load_status_rows
from verify_reference_request_result import case_request_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--expected-effect", required=True)
    parser.add_argument("--command", required=True, help="run_reference_test.py command template")
    parser.add_argument("--build-script", default=None, help="Optional build script to run before probing")
    parser.add_argument("--run-name", default=None, help="Name under /tmp; defaults to request id")
    parser.add_argument(
        "--requests-dir",
        type=Path,
        default=None,
        help="Directory containing request JSON files. Defaults to refs/reference_requests.",
    )
    parser.add_argument(
        "--references-dir",
        type=Path,
        default=None,
        help="Directory containing imported reference manifests. Defaults to refs/win_references.",
    )
    parser.add_argument(
        "--case-request-id",
        action="append",
        default=[],
        help="Limit to this request case id. May be repeated.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def covered_manifest(requests_dir: Path, references_dir: Path, request_id: str) -> Path | None:
    rows = load_status_rows(requests_dir, references_dir)
    for row in rows:
        if row.get("request_id") != request_id or row.get("status") != "covered":
            continue
        best = row.get("best") or {}
        manifest = best.get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    return None


def request_params(requests_dir: Path, request_id: str) -> dict[str, dict[str, Any]]:
    request = load_json(requests_dir / f"{request_id}.json")
    common = request.get("common_params") if isinstance(request.get("common_params"), dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for case in request.get("cases", []):
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            continue
        params: dict[str, Any] = dict(common)
        if isinstance(case.get("params"), dict):
            params.update(case["params"])
        result[case["id"]] = params
    return result


def matching_cases(
    manifest_path: Path,
    request_case_params: dict[str, dict[str, Any]],
    wanted_request_ids: set[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    manifest = load_json(manifest_path)
    case_ids: list[str] = []
    rows: list[dict[str, Any]] = []
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        req_id = case_request_id(case)
        if req_id not in request_case_params:
            continue
        if wanted_request_ids and req_id not in wanted_request_ids:
            continue
        case_id = str(case.get("id") or req_id)
        case_ids.append(case_id)
        rows.append(
            {
                "case_id": case_id,
                "request_case_id": req_id,
                "render_set": case.get("render_set") or case.get("render_set_id") or "",
                "params": request_case_params[req_id],
                "case": case,
            }
        )
    return case_ids, rows


def print_case_map(rows: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "request_case_map.csv"
    fieldnames = ["case_id", "request_case_id", "render_set", "params_json"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "request_case_id": row["request_case_id"],
                    "render_set": row["render_set"],
                    "params_json": json.dumps(row["params"], sort_keys=True),
                }
            )

    print("=== request case map ===")
    for row in rows:
        params = row["params"]
        interesting = ", ".join(f"{key}={value}" for key, value in sorted(params.items())[:10])
        suffix = " ..." if len(params) > 10 else ""
        print(
            f"{row['case_id']}: request={row['request_case_id']} "
            f"render_set={row['render_set']} {interesting}{suffix}"
        )
    print(f"case_map_csv={csv_path}")


def run_probe(root: Path, manifest_path: Path, args: argparse.Namespace, case_ids: list[str], out_dir: Path) -> int:
    if args.build_script:
        build = subprocess.run([str(root / args.build_script)], cwd=root)
        if build.returncode != 0:
            return build.returncode

    run_dir = out_dir / "cli_probe"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    filtered_source = out_dir / "filtered_reference"
    if filtered_source.exists():
        shutil.rmtree(filtered_source)
    filtered_source.mkdir(parents=True)

    manifest = load_json(manifest_path)
    allow_ids = set(case_ids)
    filtered_cases = []
    copied = set()
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or case_request_id(case) or "")
        if case_id not in allow_ids:
            continue
        frame = case.get("frame")
        before = case.get("before_effects_frame")
        if not isinstance(frame, str) or not isinstance(before, str):
            continue
        if not (manifest_path.parent / frame).exists() or not (manifest_path.parent / before).exists():
            continue
        filtered_cases.append(case)
        for name in (frame, before):
            if name in copied:
                continue
            shutil.copy2(manifest_path.parent / name, filtered_source / name)
            copied.add(name)
    if not filtered_cases:
        print(f"[FAIL] no matching cases have complete PNG files: {manifest_path}", file=sys.stderr)
        return 1
    filtered_manifest = dict(manifest)
    filtered_manifest["cases"] = filtered_cases
    (filtered_source / "reference_manifest.json").write_text(
        json.dumps(filtered_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(filtered_source),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        args.expected_effect,
        "--command",
        args.command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    print("$ " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=root)
    report = run_dir / "reports" / "diff.json"
    if report.exists():
        print(f"diff_report={report}")
    return result.returncode


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    requests_dir = (args.requests_dir or root / "refs" / "reference_requests").resolve()
    references_dir = (args.references_dir or root / "refs" / "win_references").resolve()
    manifest_path = covered_manifest(requests_dir, references_dir, args.request_id)
    if manifest_path is None:
        print(f"[SKIP] {args.request_id} is still pending; import the Windows reference set first.")
        print("       python3 refs/scripts/check_reference_request_status.py")
        return 0

    try:
        request_case_params = request_params(requests_dir, args.request_id)
        case_ids, rows = matching_cases(manifest_path, request_case_params, set(args.case_request_id))
        if not case_ids:
            print(f"[FAIL] covered manifest has no matching {args.request_id} cases: {manifest_path}", file=sys.stderr)
            return 1
        out_dir = Path("/tmp") / (args.run_name or args.request_id)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        print_case_map(rows, out_dir)
        return run_probe(root, manifest_path, args, case_ids, out_dir)
    except Exception as exc:  # noqa: BLE001 - smoke should show exact blocker.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
