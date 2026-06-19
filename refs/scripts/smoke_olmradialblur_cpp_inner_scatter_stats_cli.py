#!/usr/bin/env python3
"""Verify the C++ OLMRadialBlur inner scatter stats diagnostic."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmradialblur_cpp_inner_scatter_stats_smoke")
    stats_path = run_dir / "inner_scatter_stats.json"
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--inner-scatter-stats {stats_path}"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "refs" / "scripts" / "run_reference_test.py"),
            str(reference),
            "--run-dir",
            str(run_dir),
            "--case-id",
            "case_0011",
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
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode != 0:
        return proc.returncode
    if not stats_path.exists():
        print(f"missing stats JSON: {stats_path}", file=sys.stderr)
        return 1

    data = json.loads(stats_path.read_text(encoding="utf-8"))
    required_positive = [
        "inner_calls",
        "inner_total_effective_span",
        "inner_total_loop_limit",
        "inner_writes",
    ]
    for key in required_positive:
        if int(data.get(key, 0)) <= 0:
            print(f"stats key {key} must be positive: {data.get(key)!r}", file=sys.stderr)
            return 1
    if not isinstance(data.get("inner_effective_span_hist"), dict) or not data["inner_effective_span_hist"]:
        print("stats must include a non-empty inner_effective_span_hist", file=sys.stderr)
        return 1

    print(f"[OK] OLMRadialBlur inner scatter stats: {stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
