#!/usr/bin/env python3
"""Run all available OLM runtime-trace comparison routers for a summary JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Comparator:
    request_id: str
    slug: str
    command: list[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("refs/reports/runtime_trace_comparisons"),
        help="Directory for per-request comparison JSON/Markdown and index files.",
    )
    parser.add_argument("--index-json", type=Path, default=None)
    parser.add_argument("--index-md", type=Path, default=None)
    parser.add_argument(
        "--run-missing",
        action="store_true",
        help="Also run comparators whose request_id is absent; useful for checking await-windows-trace behavior.",
    )
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def display_text(root: Path, text: str) -> str:
    return text.replace(str(root.resolve()), ".").replace(str(root), ".")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def comparators(py: str) -> list[Comparator]:
    return [
        Comparator(
            request_id="olmblur_repeat_threshold_runtime_trace_20260619",
            slug="olmblur_repeat_threshold",
            command=[py, "scripts/compare_olmblur_trace.py"],
        ),
        Comparator(
            request_id="kirakira_fun_181150790_stage_values_20260620",
            slug="olmkirakira_stage_values",
            command=[py, "scripts/compare_kirakira_stage_trace.py"],
        ),
        Comparator(
            request_id="kirakira_fun_181150790_deep_stage_values_20260621",
            slug="olmkirakira_deep_stage_values",
            command=[py, "scripts/compare_kirakira_stage_trace.py"],
        ),
        Comparator(
            request_id="kirakira_forward_warp_box_input_20260621",
            slug="olmkirakira_forward_warp_box_input",
            command=[py, "scripts/compare_kirakira_stage_trace.py"],
        ),
        Comparator(
            request_id="kirakira_aggregation_compose_bt709_20260624",
            slug="olmkirakira_aggregation_compose_bt709",
            command=[
                py,
                "scripts/compare_kirakira_stage_trace.py",
                "--local-trace-json",
                "refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json",
            ],
        ),
        Comparator(
            request_id="colorkey_edge_runtime_trace_20260619",
            slug="olmcolorkey_edge",
            command=[py, "scripts/compare_colorkey_edge_trace.py"],
        ),
        Comparator(
            request_id="colorkey_16bpc_case0009_runtime_trace_20260626",
            slug="olmcolorkey_16bpc_case0009",
            command=[py, "scripts/compare_colorkey_16bpc_case0009_trace.py"],
        ),
        Comparator(
            request_id="olmdistancegradation_field_prep_runtime_trace_20260619",
            slug="olmdistancegradation_field_prep",
            command=[py, "scripts/compare_distancegradation_trace.py"],
        ),
        Comparator(
            request_id="olmradialblur_dense_sampler_trace_20260620",
            slug="olmradialblur_dense_sampler",
            command=[py, "scripts/compare_radialblur_trace.py"],
        ),
        Comparator(
            request_id="olmdirectionalblur_dense_sampler_trace_20260620",
            slug="olmdirectionalblur_dense_sampler",
            command=[py, "scripts/compare_directionalblur_trace.py"],
        ),
        Comparator(
            request_id="olmsmoother2_legacy_key_gamma_runtime_trace_20260620",
            slug="olmsmoother2_legacy_key_gamma",
            command=[py, "scripts/compare_smoother2_legacy_trace.py"],
        ),
    ]


def request_ids(summary: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for row in summary.get("results", []):
        if isinstance(row, dict) and isinstance(row.get("request_id"), str):
            ids.add(row["request_id"])
    return ids


def run_comparator(root: Path, summary_path: Path, output_dir: Path, comparator: Comparator) -> dict[str, Any]:
    output_json = output_dir / f"{comparator.slug}.json"
    output_md = output_dir / f"{comparator.slug}.md"
    cmd = [
        *comparator.command,
        "--runtime-summary-json",
        str(summary_path),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]
    proc = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    row: dict[str, Any] = {
        "request_id": comparator.request_id,
        "slug": comparator.slug,
        "command": [
            display_path(root, Path(part)) if part.startswith(str(root)) else part
            for part in cmd
        ],
        "returncode": proc.returncode,
        "stdout": display_text(root, proc.stdout),
        "output_json": display_path(root, output_json),
        "output_md": display_path(root, output_md),
    }
    if proc.returncode == 0 and output_json.exists():
        data = load_json(output_json)
        if isinstance(data, dict):
            row["likely_next_focus"] = data.get("likely_next_focus")
            row["comparison_kind"] = data.get("kind")
    return row


def render_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# OLM Runtime Trace Comparison Index",
        "",
        f"- Runtime summary: `{index['runtime_summary_json']}`",
        f"- Present request IDs: `{', '.join(index['present_request_ids']) or '-'}`",
        "",
        "| Request | Comparator | Status | Likely next focus | Markdown |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in index["comparisons"]:
        status = "OK" if row.get("returncode") == 0 else f"FAIL {row.get('returncode')}"
        md = row.get("output_md")
        lines.append(
            f"| `{row.get('request_id')}` | `{row.get('slug')}` | {status} | "
            f"`{row.get('likely_next_focus', '-')}` | `{md}` |"
        )
    if not index["comparisons"]:
        lines.append("| - | - | - | - | - |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    output_dir = resolve(root, args.output_dir)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    present_ids = request_ids(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for comparator in comparators(sys.executable):
        if args.run_missing or comparator.request_id in present_ids:
            row = run_comparator(root, summary_path, output_dir, comparator)
            rows.append(row)
            print(
                f"{comparator.slug}: "
                f"exit={row['returncode']} focus={row.get('likely_next_focus', '-')}"
            )
    index = {
        "kind": "olm_runtime_trace_comparison_index",
        "schema": 1,
        "runtime_summary_json": display_path(root, summary_path),
        "present_request_ids": sorted(present_ids),
        "comparisons": rows,
    }
    index_json = resolve(root, args.index_json) if args.index_json else output_dir / "index.json"
    index_md = resolve(root, args.index_md) if args.index_md else output_dir / "index.md"
    index_json.parent.mkdir(parents=True, exist_ok=True)
    index_md.parent.mkdir(parents=True, exist_ok=True)
    index_json.write_text(json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    index_md.write_text(render_markdown(index), encoding="utf-8")
    print(f"index_json={index_json}")
    print(f"index_md={index_md}")
    return 0 if all(row.get("returncode") == 0 for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
