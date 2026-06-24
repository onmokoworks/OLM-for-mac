#!/usr/bin/env python3
"""Run OLMDirectionalBlur algorithm candidates against selected references.

This is a diagnostic matrix, not a conformance gate. It keeps production code
unchanged and shows which existing probe variants improve or regress each case.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur"

QUICK_CASES = ["case_0001", "case_0005"]
WIDE_CASES = ["case_0001", "case_0002", "case_0003", "case_0004", "case_0005"]

CANDIDATES = [
    {"name": "direct", "algorithm": "direct"},
    {"name": "rotated-aex-choreo", "algorithm": "rotated-aex-choreo"},
    {"name": "rotated-aex-full-choreo", "algorithm": "rotated-aex-full-choreo"},
    {"name": "rotated-aex-pad-full-choreo", "algorithm": "rotated-aex-pad-full-choreo"},
    {"name": "rotated-aex-prepass-full-choreo", "algorithm": "rotated-aex-prepass-full-choreo"},
    {"name": "rotated-aex-exact-rowdriver", "algorithm": "rotated-aex-exact-rowdriver"},
    {"name": "rotated-aex-exact-scatter-helper", "algorithm": "rotated-aex-exact-scatter-helper"},
    {"name": "rotated-aex-truncated-span", "algorithm": "rotated-aex-truncated-span"},
    {"name": "rotated-aex-trunc-output", "algorithm": "rotated-aex-trunc-output"},
    {"name": "rotated-aex-binary-alpha", "algorithm": "rotated-aex-binary-alpha"},
    {"name": "rotated-aex-straight-source-rgb", "algorithm": "rotated-aex-straight-source-rgb"},
    {"name": "rotated-rowdriver-prepass", "algorithm": "rotated-rowdriver-prepass"},
    {"name": "rotated-front-strength", "algorithm": "rotated-front-strength"},
    {"name": "rotated-map-alpha-coeff", "algorithm": "rotated-map-alpha-coeff"},
]


def run(cmd: list[str | Path], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(part) for part in cmd],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("quick", "wide"), default="quick")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--keep-runs", action="store_true")
    return parser.parse_args()


def profile_cases(profile: str) -> list[str]:
    return QUICK_CASES if profile == "quick" else WIDE_CASES


def candidate_command(algorithm: str) -> str:
    return (
        '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--algorithm {algorithm} "
        "--angle-sign -1 --sample-sign 1 --strength-scale auto"
    )


def load_diff(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "reports/diff.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_candidate(candidate: dict[str, str], cases: list[str], output_dir: Path) -> tuple[list[dict[str, Any]], Path]:
    run_dir = output_dir / "runs" / candidate["name"]
    if run_dir.exists():
        shutil.rmtree(run_dir)
    cmd = [
        sys.executable,
        "refs/scripts/run_reference_test.py",
        str(REFERENCE),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM DirectionalBlur",
        "--command",
        candidate_command(candidate["algorithm"]),
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in cases:
        cmd.extend(["--case-id", case_id])
    proc = run(cmd, ROOT)
    (output_dir / "logs").mkdir(parents=True, exist_ok=True)
    (output_dir / "logs" / f"{candidate['name']}.log").write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"candidate {candidate['name']} failed; see {output_dir / 'logs' / (candidate['name'] + '.log')}")
    report = load_diff(run_dir)
    rows = []
    for row in report.get("cases", []):
        rows.append(
            {
                "candidate": candidate["name"],
                "case": row.get("id"),
                "max_diff": row.get("max_diff"),
                "mean_diff": row.get("mean_diff"),
                "nonzero_px_percent": row.get("nonzero_px_percent"),
            }
        )
    return rows, run_dir


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["candidate", "case", "max_diff", "mean_diff", "nonzero_px_percent"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(str(row["candidate"]), []).append(row)
    summary = []
    for name, items in by_candidate.items():
        mean_sum = sum(float(row.get("mean_diff") or 0.0) for row in items)
        max_diff = max(int(row.get("max_diff") or 0) for row in items)
        summary.append({"candidate": name, "case_count": len(items), "mean_sum": mean_sum, "max_diff": max_diff})
    return sorted(summary, key=lambda row: (row["mean_sum"], row["max_diff"], row["candidate"]))


def render_markdown(rows: list[dict[str, Any]], summary: list[dict[str, Any]], cases: list[str]) -> str:
    by_pair = {(row["candidate"], row["case"]): row for row in rows}
    lines = [
        "# OLMDirectionalBlur Candidate Matrix",
        "",
        "This diagnostic compares existing CLI probe variants. It is not a conformance gate.",
        "",
        "## Summary",
        "",
        "| Candidate | Cases | Mean sum | Max diff |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            f"| {row['candidate']} | {row['case_count']} | {row['mean_sum']:.6f} | {row['max_diff']} |"
        )
    lines.extend(["", "## Case Matrix", "", "| Candidate | " + " | ".join(cases) + " |", "| --- | " + " | ".join("---:" for _ in cases) + " |"])
    for item in summary:
        name = item["candidate"]
        values = []
        for case_id in cases:
            row = by_pair.get((name, case_id), {})
            values.append(f"{int(row.get('max_diff') or 0)} / {float(row.get('mean_diff') or 0.0):.4f}")
        lines.append(f"| {name} | " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir or ROOT / f"refs/reports/olmdirectionalblur_candidate_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = profile_cases(args.profile)

    build = run([ROOT / "refs/scripts/build_olmdirectionalblur_cli.sh"], ROOT)
    (output_dir / "build.log").write_text(build.stdout, encoding="utf-8")
    if build.returncode != 0:
        print(build.stdout, file=sys.stderr)
        return build.returncode

    rows: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        candidate_rows, _ = run_candidate(candidate, cases, output_dir)
        rows.extend(candidate_rows)

    summary = summarize(rows)
    write_csv(rows, output_dir / "candidate_matrix.csv")
    (output_dir / "candidate_matrix.md").write_text(render_markdown(rows, summary, cases), encoding="utf-8")
    (output_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "olmdirectionalblur_candidate_matrix",
                "profile": args.profile,
                "cases": cases,
                "summary": summary,
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    if not args.keep_runs:
        shutil.rmtree(output_dir / "runs", ignore_errors=True)
    print(f"report={output_dir / 'candidate_matrix.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
