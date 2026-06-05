#!/usr/bin/env python3
"""Analyze the requested OLMColorKey Replace/color-space refs once imported.

This request intentionally targets behavior the current CLI does not fully
implement yet. While the Windows reference is pending, the script exits 0 with
a SKIP message. Once covered, it prints a grouped manifest audit and only runs
the current C++ CLI on the safe subset that has ``Enable Replace = 0``; Replace
cases stay as analysis inputs until implementation is backed by the new refs.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from audit_olmcolorkey_manifest import grouped_params
from check_reference_request_status import load_status_rows
from verify_reference_request_result import case_request_id


REQUEST_ID = "olmcolorkey_replace_colorspace_20260606"


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
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    return None


def case_rows(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = load_json(manifest_path)
    rows = []
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        params = grouped_params(case)
        rows.append(
            {
                "case_id": str(case.get("id") or ""),
                "request_case_id": case_request_id(case) or "",
                "color_keep": params.get("color_keep", ""),
                "color_space": params.get("color_space", ""),
                "threshold": params.get("threshold", ""),
                "per_component": params.get("per_component", ""),
                "number_of_colors": params.get("number_of_colors", ""),
                "enable_replace": params.get("enable_replace", ""),
                "edge_thin_amount": params.get("edge_thin_amount", ""),
                "edge_blur_amount": params.get("edge_blur_amount", ""),
            }
        )
    return rows


def print_audit(rows: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "olmcolorkey_replace_colorspace_audit.csv"
    fields = [
        "case_id",
        "request_case_id",
        "color_keep",
        "color_space",
        "threshold",
        "per_component",
        "number_of_colors",
        "enable_replace",
        "edge_thin_amount",
        "edge_blur_amount",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("=== OLMColorKey Replace/color-space coverage ===")
    for row in rows:
        print(
            f"{row['case_id'] or row['request_case_id']}: "
            f"request={row['request_case_id']} "
            f"space={row['color_space']} replace={row['enable_replace']} "
            f"keep={row['color_keep']} colors={row['number_of_colors']} "
            f"per_component={row['per_component']} "
            f"edge_thin={row['edge_thin_amount']} edge_blur={row['edge_blur_amount']}"
        )
    print(f"audit_csv={csv_path}")


def safe_cli_case_ids(rows: list[dict[str, Any]]) -> list[str]:
    safe = []
    for row in rows:
        if str(row.get("enable_replace")) not in {"0", "0.0", "False", "false", ""}:
            continue
        # Current CLI has RGB and partial Lab76 coverage; other non-black color
        # spaces are request evidence for future implementation, not a green
        # runnable subset yet.
        if str(row.get("color_space")) not in {"1", "1.0", "3", "3.0"}:
            continue
        case_id = row["case_id"] or row["request_case_id"]
        if case_id:
            safe.append(str(case_id))
    return safe


def run_safe_cli(root: Path, manifest_path: Path, case_ids: list[str], out_dir: Path) -> int:
    if not case_ids:
        print("[INFO] no current-CLI-safe cases in returned ColorKey request manifest")
        return 0

    cli = root / "cli" / "OLMColorKey" / "olmcolorkey_cli"
    if not cli.exists():
        build = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_cli.sh")], cwd=root)
        if build.returncode != 0:
            return build.returncode
    if not cli.exists():
        print(f"[FAIL] missing CLI binary: {cli}", file=sys.stderr)
        return 1

    run_dir = out_dir / "cli_subset"
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMColorKey/olmcolorkey_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(manifest_path.parent),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])

    result = subprocess.run(args, cwd=root)
    if result.returncode == 0:
        print(f"[OK] current C++ CLI produced comparable outputs for {len(case_ids)} safe case(s)")
    else:
        print(f"[WARN] current C++ CLI subset run exited {result.returncode}; inspect {run_dir}")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    manifest_path = covered_manifest(root)
    if manifest_path is None:
        print(f"[SKIP] {REQUEST_ID} is still pending; import the Windows reference set first.")
        print("       python3 refs/scripts/check_reference_request_status.py")
        return 0

    try:
        rows = case_rows(manifest_path)
        if not rows:
            print(f"[FAIL] covered manifest has no cases: {manifest_path}", file=sys.stderr)
            return 1
        out_dir = Path("/tmp/olmcolorkey_replace_colorspace_request_smoke")
        if out_dir.exists():
            shutil.rmtree(out_dir)
        print_audit(rows, out_dir)
        return run_safe_cli(root, manifest_path, safe_cli_case_ids(rows), out_dir)
    except Exception as exc:  # noqa: BLE001 - command-line smoke should be direct.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
