#!/usr/bin/env python3
"""Analyze the requested OLMSmoother2 no-key grid once Windows refs arrive.

The reference request is intentionally pending in the normal local state. This
script exits 0 with a SKIP message until a matching imported manifest is found.
When covered, it runs the C++ OLMSmoother2 CLI and prints max/mean grouped by
Smoothness and Smooth Range so the remaining no-key residual can be diagnosed
without adding another ad-hoc notebook.
"""

from __future__ import annotations

import csv
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_reference_request_status import load_status_rows
from verify_reference_request_result import case_request_id


REQUEST_ID = "smoother2_no_key_grid_20260606"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def covered_manifest(root: Path) -> Path | None:
    rows = load_status_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")
    for row in rows:
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        best = row.get("best") or {}
        manifest = best.get("manifest")
        if isinstance(manifest, str) and manifest:
            return (root / manifest).resolve() if not Path(manifest).is_absolute() else Path(manifest)
    return None


def request_case_params(root: Path) -> dict[str, dict[str, Any]]:
    request = load_json(root / "refs" / "reference_requests" / f"{REQUEST_ID}.json")
    result: dict[str, dict[str, Any]] = {}
    for case in request.get("cases", []):
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            continue
        params = case.get("params")
        if isinstance(params, dict):
            result[case["id"]] = params
    return result


def selected_case_params(manifest_path: Path, request_params: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    manifest = load_json(manifest_path)
    result: dict[str, dict[str, Any]] = {}
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        req_id = case_request_id(case)
        if req_id in request_params:
            result[str(case.get("id") or req_id)] = request_params[req_id]
    return result


def run_grid(root: Path, manifest_path: Path, case_ids: list[str], cli_extra: list[str], run_suffix: str) -> Path:
    cli = root / "cli" / "OLMSmoother2" / "olmsmoother2_cli"
    if not cli.exists():
        raise FileNotFoundError(f"missing CLI binary (run build_olmsmoother2_cli.sh): {cli}")

    safe_suffix = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in run_suffix).strip("_")
    run_dir = Path("/tmp/olmsmoother2_no_key_grid_smoke" + (f"_{safe_suffix}" if safe_suffix else ""))
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    if cli_extra:
        command += " " + " ".join(shlex.quote(arg) for arg in cli_extra)
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(manifest_path.parent),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Smoother v2",
        "--command",
        command,
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])

    result = subprocess.run(args, cwd=root)
    report_path = run_dir / "reports" / "diff.json"
    if not report_path.exists():
        raise RuntimeError(f"grid run did not produce report: {report_path} (exit {result.returncode})")
    return report_path


def print_grouped_report(report_path: Path, case_params: dict[str, dict[str, Any]]) -> int:
    report = load_json(report_path)
    rows = []
    for row in report.get("cases", []):
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("id") or "")
        params = case_params.get(case_id, {})
        smoothness = params.get("Smoothness", "?")
        smooth_range = params.get("Smooth Range", "?")
        rows.append(
            {
                "case_id": case_id,
                "smoothness": smoothness,
                "smooth_range": smooth_range,
                "max_diff": row.get("max_diff", ""),
                "mean_diff": row.get("mean_diff", ""),
                "nonzero_px_percent": row.get("nonzero_px_percent", ""),
            }
        )

    rows.sort(key=lambda item: (item["smooth_range"], item["smoothness"], item["case_id"]))
    print("=== OLMSmoother2 no-key grid diff by Smooth Range / Smoothness ===")
    for row in rows:
        mean = row["mean_diff"]
        mean_text = f"{mean:.4f}" if isinstance(mean, (float, int)) else str(mean)
        nz = row["nonzero_px_percent"]
        nz_text = f"{nz:.4f}" if isinstance(nz, (float, int)) else str(nz)
        print(
            f"range={row['smooth_range']} smoothness={row['smoothness']:>3} "
            f"{row['case_id']}: max={row['max_diff']} mean={mean_text} nz%={nz_text}"
        )

    csv_path = report_path.parent / "no_key_grid_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["case_id", "smoothness", "smooth_range", "max_diff", "mean_diff", "nonzero_px_percent"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"summary_csv={csv_path}")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cli-extra",
        action="append",
        default=[],
        help="Extra argument string appended to olmsmoother2_cli, e.g. --cli-extra='--idx0-mode half'. May be repeated.",
    )
    parser.add_argument(
        "--run-suffix",
        default="",
        help="Suffix for the /tmp run directory so diagnostic runs can be compared side by side.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    manifest_path = covered_manifest(root)
    if manifest_path is None:
        print(f"[SKIP] {REQUEST_ID} is still pending; import the Windows reference set first.")
        print("       python3 refs/scripts/check_reference_request_status.py")
        return 0

    request_params = request_case_params(root)
    case_params = selected_case_params(manifest_path, request_params)
    if not case_params:
        print(f"[FAIL] covered manifest has no matching {REQUEST_ID} cases: {manifest_path}", file=sys.stderr)
        return 1

    try:
        cli_extra = [part for extra in args.cli_extra for part in shlex.split(extra)]
        report_path = run_grid(root, manifest_path, list(case_params), cli_extra, args.run_suffix)
        return print_grouped_report(report_path, case_params)
    except Exception as exc:  # noqa: BLE001 - command-line smoke should be direct.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
