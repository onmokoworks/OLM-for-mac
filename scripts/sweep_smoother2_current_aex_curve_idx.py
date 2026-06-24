#!/usr/bin/env python3
"""Sweep OLMSmoother2 current-AEX gamma curve index overrides."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "smoother2_legacy_full_current_aex_recapture_20260621"
EXPECTED_EFFECT = "OLM Smoother v2"
DEFAULT_CASES = [
    "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex",
    "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex",
    "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex",
    "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("refs/reports/olmsmoother2_current_aex_curve_idx_sweep"))
    parser.add_argument("--curve-idx", action="append", type=int, default=None)
    parser.add_argument("--keep-run-dirs", action="store_true")
    return parser.parse_args()


def load_status_rows(root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(root / "refs" / "scripts"))
    from check_reference_request_status import load_status_rows as load_rows

    return load_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")


def covered_manifest(root: Path) -> Path:
    for row in load_status_rows(root):
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        manifest = (row.get("best") or {}).get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    raise FileNotFoundError(f"covered manifest not found for {REQUEST_ID}")


def run(command: list[Any], root: Path) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(str(part) for part in command), flush=True)
    return subprocess.run([str(part) for part in command], cwd=root)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_curve(root: Path, manifest_dir: Path, output_dir: Path, curve_idx: int, case_ids: list[str]) -> list[dict[str, str]]:
    run_dir = output_dir / f"run_curve_{curve_idx}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" --input "{input}" --params "{params}" '
        f'--output "{{output}}" --curve-idx-override {curve_idx}'
    )
    ref_run = [
        sys.executable,
        root / "refs" / "scripts" / "run_reference_test.py",
        manifest_dir,
        "--run-dir",
        run_dir,
        "--expected-effect",
        EXPECTED_EFFECT,
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
        ref_run.extend(["--case-id", case_id])
    proc = run(ref_run, root)
    if proc.returncode != 0:
        raise RuntimeError(f"curve {curve_idx} failed with exit {proc.returncode}")
    return read_csv(run_dir / "reports" / "diff.csv")


def metric_summary(curve_idx: int, rows: list[dict[str, str]]) -> dict[str, Any]:
    max_diff = max(int(row["max_diff"]) for row in rows)
    mean_sum = sum(float(row["mean_diff"]) for row in rows)
    nonzero_sum = sum(float(row["nonzero_px_percent"]) for row in rows)
    exact_count = sum(1 for row in rows if int(row["max_diff"]) == 0 and float(row["mean_diff"]) == 0.0)
    return {
        "curve_idx": curve_idx,
        "max_diff": max_diff,
        "mean_sum": mean_sum,
        "nonzero_px_percent_sum": nonzero_sum,
        "exact_count": exact_count,
        "rows": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Curve Index Sweep",
        "",
        f"- Request: `{report['request_id']}`",
        f"- Manifest: `{report['manifest']}`",
        "",
        "| Curve | Max | Mean sum | Nonzero % sum | Exact cases |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["summaries"]:
        lines.append(
            f"| {row['curve_idx']} | {row['max_diff']} | {row['mean_sum']:.6f} | "
            f"{row['nonzero_px_percent_sum']:.6f} | {row['exact_count']} |"
        )
    lines.extend(["", "## Best Curve By Case", "", "| Case | Best curve | Max | Mean | Nonzero % |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in report["best_by_case"]:
        lines.append(
            f"| `{row['case_id']}` | {row['curve_idx']} | {row['max_diff']} | "
            f"{row['mean_diff']:.6f} | {row['nonzero_px_percent']:.6f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    manifest_path = covered_manifest(root)
    case_ids = args.case_id or DEFAULT_CASES
    curve_indices = args.curve_idx or list(range(0, 9))
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    if output_dir.exists() and not args.keep_run_dirs:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    build = run([root / "refs" / "scripts" / "build_olmsmoother2_cli.sh"], root)
    if build.returncode != 0:
        return build.returncode

    summaries = [
        metric_summary(curve_idx, run_curve(root, manifest_path.parent, output_dir, curve_idx, case_ids))
        for curve_idx in curve_indices
    ]
    summaries.sort(key=lambda row: (float(row["mean_sum"]), int(row["max_diff"]), float(row["nonzero_px_percent_sum"])))

    by_case: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in case_ids}
    for summary in summaries:
        for row in summary["rows"]:
            by_case[row["id"]].append(
                {
                    "case_id": row["id"],
                    "curve_idx": summary["curve_idx"],
                    "max_diff": int(row["max_diff"]),
                    "mean_diff": float(row["mean_diff"]),
                    "nonzero_px_percent": float(row["nonzero_px_percent"]),
                }
            )
    best_by_case = [
        sorted(rows, key=lambda row: (row["mean_diff"], row["max_diff"], row["nonzero_px_percent"]))[0]
        for rows in by_case.values()
    ]

    report = {
        "kind": "olmsmoother2_current_aex_curve_idx_sweep",
        "schema": 1,
        "request_id": REQUEST_ID,
        "manifest": str(manifest_path),
        "curve_indices": curve_indices,
        "case_ids": case_ids,
        "summaries": summaries,
        "best_by_case": best_by_case,
    }
    json_path = output_dir / "curve_idx_sweep.json"
    md_path = output_dir / "curve_idx_sweep.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={json_path}")
    print(f"report_md={md_path}")
    print("=== best overall ===")
    best = summaries[0]
    print(
        f"curve={best['curve_idx']} max={best['max_diff']} "
        f"mean_sum={best['mean_sum']:.6f} nonzero_sum={best['nonzero_px_percent_sum']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
