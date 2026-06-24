#!/usr/bin/env python3
"""Summarize runtime trace packages, answer status, and next intake commands."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


PRIORITY_PROFILES = {
    "radialblur-residual-witness": 10,
    "kirakira-boxfilter-pass1-microprobe": 20,
    "directionalblur-residual-witness": 30,
    "kirakira-forward-warp-box-input": 40,
    "kirakira-stage-values-deep": 50,
    "olmblur-repeat-threshold": 60,
    "colorkey-edge": 70,
    "distancegradation-field-prep": 80,
}

COMPARISON_COMMANDS = [
    (
        "olmradialblur_zoom_tiny_rotation_residual_witness_20260622",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.md",
    ),
    (
        "kirakira_boxfilter_pass1_microprobe_20260622",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.md",
    ),
    (
        "olmdirectionalblur_angle0_diagonal_residual_witness_20260622",
        "python3 scripts/compare_directionalblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.json --output-md refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.md",
    ),
    (
        "kirakira_forward_warp_box_input_20260621",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.md",
    ),
    (
        "kirakira_fun_181150790",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_stage_values.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_stage_values.md",
    ),
    (
        "olmblur_repeat_threshold",
        "python3 scripts/compare_olmblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold.json --output-md refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold.md",
    ),
    (
        "colorkey_edge",
        "python3 scripts/compare_colorkey_edge_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmcolorkey_edge.json --output-md refs/reports/runtime_trace_comparisons/olmcolorkey_edge.md",
    ),
    (
        "olmdistancegradation",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep.md",
    ),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=root / "refs/runtime_trace_packages")
    parser.add_argument("--output-json", type=Path, default=root / "refs/reports/pending_runtime_trace_packages.json")
    parser.add_argument("--output-md", type=Path, default=root / "refs/reports/pending_runtime_trace_packages.md")
    return parser.parse_args()


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def package_manifest(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            name = next(
                (member for member in archive.namelist() if member.replace("\\", "/").endswith("runtime_trace_package_manifest.json")),
                None,
            )
            if name is None:
                return None
            data = json.loads(archive.read(name).decode("utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) and data.get("kind") == "olm_runtime_trace_request_package" else None


def answered_request_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((root / "refs/reports").glob("**/runtime_trace_summary*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        for row in data.get("required", []):
            if isinstance(row, dict) and row.get("answered") is True and isinstance(row.get("request_id"), str):
                ids.add(row["request_id"])
        for row in data.get("results", []):
            if not isinstance(row, dict) or not isinstance(row.get("request_id"), str):
                continue
            status = str(row.get("status") or "").lower()
            if status.startswith("answered") or status in {"ok", "complete"}:
                ids.add(row["request_id"])
    return ids


def superseded_request_ids(root: Path) -> set[str]:
    data = read_json(root / "refs/reports/runtime_trace_superseded.json")
    if not isinstance(data, dict):
        return set()
    ids = set()
    for row in data.get("superseded", []):
        if isinstance(row, dict) and isinstance(row.get("request_id"), str):
            ids.add(row["request_id"])
    return ids


def comparison_command(request_id: str) -> str:
    for needle, command in COMPARISON_COMMANDS:
        if needle in request_id:
            return command
    return "python3 scripts/intake_olm_return.py path/to/return.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons"


def row_status(request_id: str, answered: set[str], superseded: set[str]) -> str:
    if request_id in superseded:
        return "superseded"
    if request_id in answered:
        return "answered"
    return "pending"


def collect(root: Path, package_dir: Path) -> list[dict[str, Any]]:
    answered = answered_request_ids(root)
    superseded = superseded_request_ids(root)
    rows: list[dict[str, Any]] = []
    for package in sorted(package_dir.glob("*.zip")):
        manifest = package_manifest(package)
        if manifest is None:
            continue
        profile = str(manifest.get("profile") or "")
        for action in manifest.get("runtime_actions", []):
            if not isinstance(action, dict):
                continue
            request_id = str(action.get("request_id") or "")
            if not request_id:
                continue
            status = row_status(request_id, answered, superseded)
            rows.append(
                {
                    "request_id": request_id,
                    "status": status,
                    "profile": profile,
                    "priority": PRIORITY_PROFILES.get(profile, 500),
                    "package": display_path(root, package),
                    "plugin_area": action.get("plugin_area") or "",
                    "command": action.get("command") or "",
                    "stop_condition": action.get("stop_condition") or "",
                    "intake_command": "python3 scripts/intake_olm_return.py path/to/return.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons",
                    "comparison_command": comparison_command(request_id),
                }
            )
    newest_by_request: dict[str, dict[str, Any]] = {}
    for row in rows:
        current = newest_by_request.get(row["request_id"])
        if current is None or row["package"] > current["package"]:
            newest_by_request[row["request_id"]] = row
    return sorted(newest_by_request.values(), key=lambda row: (row["status"] != "pending", row["priority"], row["request_id"]))


def short(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def render_markdown(report: dict[str, Any]) -> str:
    rows = report["requests"]
    pending = [row for row in rows if row["status"] == "pending"]
    lines = [
        "# Pending Runtime Trace Packages",
        "",
        "This report lists project-local Windows debugger/runtime trace packages and whether each request still needs a return.",
        "",
        f"- Pending: `{len(pending)}`",
        f"- Answered/superseded: `{len(rows) - len(pending)}`",
        "",
        "| Status | Priority | Request | Package | Why needed |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['status']}` | {row['priority']} | `{row['request_id']}` | "
            f"`{row['package']}` | {short(row['plugin_area'] or row['command'])} |"
        )
    if pending:
        lines.extend(["", "## Send First", ""])
        first = pending[0]
        lines.extend(
            [
                f"- Package: `{first['package']}`",
                f"- Request: `{first['request_id']}`",
                f"- Why: {first['plugin_area']}",
                f"- Stop condition: {first['stop_condition']}",
                "",
                "After the Windows return is imported:",
                "",
                "```bash",
                first["intake_command"],
                first["comparison_command"],
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    rows = collect(root, args.package_dir)
    report = {
        "kind": "pending_runtime_trace_packages",
        "schema": 1,
        "requests": rows,
    }
    for output in (args.output_json, args.output_md):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={display_path(root, args.output_json)}")
    print(f"report_md={display_path(root, args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
