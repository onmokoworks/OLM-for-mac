#!/usr/bin/env python3
"""Run a bounded OLMRadialBlur Inner candidate matrix.

This is a Mac-side analysis helper. It does not decide compatibility; it
classifies which existing diagnostic switches improve or regress the current
Windows Software Inner reference set so the IR can be updated with negative
and positive evidence.
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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF = (
    ROOT
    / "refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_full_software/OLMRadialBlur"
)
CASES = (
    "rb_inner_existing_0011_software_pair",
    "rb_inner_existing_0012_software_pair",
    "rb_inner_only_strength_small",
    "rb_inner_only_strength_large",
    "rb_inner_offset_mode_3",
    "rb_inner_edgefade_only",
    "rb_outer_inner_edgefade",
    "rb_inner_quality_1",
    "rb_inner_existing_0013_software_pair",
    "rb_inner_quality_50",
)
QUICK_CASES = (
    "rb_inner_only_strength_small",
    "rb_inner_only_strength_large",
    "rb_inner_edgefade_only",
    "rb_inner_quality_1",
    "rb_inner_quality_50",
)


CANDIDATES: tuple[tuple[str, str], ...] = (
    ("current-default", ""),
    ("no-span-minus-one", "--no-inner-scatter-span-minus-one"),
    ("loop-minus-one", "--inner-scatter-loop-minus-one"),
    ("table-span-minus-one", "--inner-scatter-table-span-minus-one"),
    ("circular-wrap", "--inner-wrap-mode circular"),
    ("polar-sample-aex-alpha", "--polar-sample-mode aex-alpha"),
    ("polar-sample-conditional", "--polar-sample-mode conditional-inner"),
    ("polar-valid-aex-repeat", "--polar-valid-mode aex-repeat"),
    ("dynamic-offset-aex-row", "--dynamic-offset-mode aex-row"),
    ("dynamic-offset-min-radius", "--dynamic-offset-mode min-radius"),
    ("grid-aex-float", "--rotation-grid-mode aex-float"),
    ("gaussian-aex-float", "--rotation-gaussian-mode aex-float"),
    ("param10-factor", "--inner-scatter-param10-plane factor"),
    ("param10-polar-alpha", "--inner-scatter-param10-plane polar-alpha"),
    ("param10-prepass-alpha", "--inner-scatter-param10-plane prepass-alpha"),
    ("rgb-denom-max", "--inner-rgb-denominator-mode max"),
    ("final-alpha-denom", "--inner-final-alpha-mode denom"),
    ("final-alpha-source", "--inner-final-alpha-mode source"),
    ("prepass-rgb-premul", "--inner-scatter-rgb-mode prepass-premul"),
    ("prepass-overwrite-seed", "--inner-prepass-overwrite-seed"),
    ("prepass-seed-alpha", "--inner-seed-alpha-mode prepass"),
    ("prepass-span-strength", "--inner-prepass-span-mode strength"),
    ("prepass-span-offset", "--inner-prepass-span-mode offset"),
    ("prepass-weight-row-span", "--inner-prepass-weight-mode row-span"),
)
QUICK_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("current-default", ""),
    ("no-span-minus-one", "--no-inner-scatter-span-minus-one"),
    ("loop-minus-one", "--inner-scatter-loop-minus-one"),
    ("table-span-minus-one", "--inner-scatter-table-span-minus-one"),
    ("circular-wrap", "--inner-wrap-mode circular"),
    ("polar-sample-aex-alpha", "--polar-sample-mode aex-alpha"),
    ("dynamic-offset-aex-row", "--dynamic-offset-mode aex-row"),
    ("grid-aex-float", "--rotation-grid-mode aex-float"),
)


def run(cmd: list[str], cwd: Path, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def build_cli() -> None:
    run([str(ROOT / "refs/scripts/build_olmradialblur_cli.sh")], ROOT)


def run_candidate(
    ref_dir: Path,
    out_root: Path,
    label: str,
    extra_args: str,
    cases: tuple[str, ...],
) -> list[dict[str, object]]:
    run_dir = out_root / "runs" / label
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    if extra_args:
        command += f" {extra_args}"
    args = [
        sys.executable,
        str(ROOT / "refs/scripts/run_reference_test.py"),
        str(ref_dir),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in cases:
        args.extend(["--case-id", case_id])
    proc = run(args, ROOT, capture=True)
    (run_dir / "command.log").write_text(proc.stdout or "", encoding="utf-8")
    diff = json.loads((run_dir / "reports/diff.json").read_text(encoding="utf-8"))
    rows = []
    for case in diff["cases"]:
        rows.append(
            {
                "candidate": label,
                "case_id": case["id"],
                "max_diff": case["max_diff"],
                "mean_diff": case["mean_diff"],
                "nonzero_px_percent": case["nonzero_px_percent"],
            }
        )
    return rows


def summarize(
    rows: list[dict[str, object]],
    cases: tuple[str, ...],
    candidates: tuple[tuple[str, str], ...],
) -> tuple[str, str]:
    baseline = {
        row["case_id"]: row
        for row in rows
        if row["candidate"] == "current-default"
    }
    candidate_names = [name for name, _ in candidates]
    lines = [
        "# OLMRadialBlur Inner Candidate Matrix",
        "",
        "This report is Mac-side diagnostic evidence only. It compares existing",
        "CLI switches against the 20260617 Windows Software full Inner set and",
        "does not promote any candidate to compatibility.",
        "",
        "## Per-Candidate Mean Sum",
        "",
        "| Candidate | mean sum | improved cases | worsened cases | exact cases |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    best_by_sum: tuple[str, float] | None = None
    for candidate in candidate_names:
        subset = [row for row in rows if row["candidate"] == candidate]
        mean_sum = sum(float(row["mean_diff"]) for row in subset)
        improved = 0
        worsened = 0
        exact = 0
        for row in subset:
            base = baseline[row["case_id"]]
            delta = float(row["mean_diff"]) - float(base["mean_diff"])
            if delta < -1.0e-9:
                improved += 1
            elif delta > 1.0e-9:
                worsened += 1
            if int(row["max_diff"]) == 0 and float(row["mean_diff"]) == 0.0:
                exact += 1
        lines.append(f"| `{candidate}` | {mean_sum:.6f} | {improved} | {worsened} | {exact} |")
        if best_by_sum is None or mean_sum < best_by_sum[1]:
            best_by_sum = (candidate, mean_sum)
    if best_by_sum:
        lines.extend(["", f"Lowest mean sum: `{best_by_sum[0]}` ({best_by_sum[1]:.6f})."])

    lines.extend(
        [
            "",
            "## Per-Case Best",
            "",
            "| Case | baseline mean | best candidate | best mean | baseline max | best max |",
            "| --- | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for case_id in cases:
        subset = [row for row in rows if row["case_id"] == case_id]
        base = baseline[case_id]
        best = min(subset, key=lambda row: (float(row["mean_diff"]), int(row["max_diff"])))
        lines.append(
            f"| `{case_id}` | {float(base['mean_diff']):.6f} | "
            f"`{best['candidate']}` | {float(best['mean_diff']):.6f} | "
            f"{int(base['max_diff'])} | {int(best['max_diff'])} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- No row is an `AE exact` result unless max and mean are both zero.",
            "- Candidates that improve strong/high-Quality cases while worsening",
            "  small-span cases should stay diagnostic until asm/runtime evidence",
            "  explains the split.",
            "- A candidate that changes only mean but leaves high max residuals is",
            "  useful for localization, not completion.",
            "",
        ]
    )
    return "\n".join(lines), best_by_sum[0] if best_by_sum else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=DEFAULT_REF)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / f"refs/reports/olmradialblur_inner_candidate_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--profile",
        choices=("quick", "wide", "full"),
        default="quick",
        help=(
            "quick runs a representative 5x8 matrix; wide runs all 10 cases "
            "against the quick 8 candidates; full runs all 10x24 candidates."
        ),
    )
    args = parser.parse_args()

    ref_dir = args.reference.resolve()
    if not ref_dir.exists():
        print(f"missing reference directory: {ref_dir}", file=sys.stderr)
        return 2
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_build:
        build_cli()

    cases = QUICK_CASES if args.profile == "quick" else CASES
    candidates = QUICK_CANDIDATES if args.profile in {"quick", "wide"} else CANDIDATES

    rows: list[dict[str, object]] = []
    for label, extra in candidates:
        print(f"[run] {label}", flush=True)
        rows.extend(run_candidate(ref_dir, out_dir, label, extra, cases))

    csv_path = out_dir / "candidate_matrix.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate", "case_id", "max_diff", "mean_diff", "nonzero_px_percent"],
        )
        writer.writeheader()
        writer.writerows(rows)

    md, best = summarize(rows, cases, candidates)
    (out_dir / "candidate_matrix.md").write_text(md, encoding="utf-8")
    summary = {
        "reference": str(ref_dir),
        "best_by_mean_sum": best,
        "profile": args.profile,
        "cases": list(cases),
        "candidates": [name for name, _ in candidates],
        "csv": str(csv_path),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_dir / 'candidate_matrix.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
