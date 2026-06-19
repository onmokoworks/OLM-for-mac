#!/usr/bin/env python3
"""Verify OLMRadialBlur Inner small-span scatter ownership diagnostics."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = (
        root
        / "refs"
        / "win_references"
        / "olm_reference_return_windows_20260617_radialblur_inner_full_software"
        / "OLMRadialBlur"
    )
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmradialblur_inner_small_scatter_stats_smoke")
    stats_path = run_dir / "inner_small_scatter_stats.json"
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
            "rb_inner_only_strength_small",
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
    expected_hists = {
        "inner_caller_span_hist": {"32": 1987200},
        "inner_effective_span_hist": {"31": 1418861},
        "inner_loop_limit_hist": {"31": 1418861},
    }
    for key, expected in expected_hists.items():
        if data.get(key) != expected:
            print(f"unexpected {key}: {data.get(key)!r}, expected {expected!r}", file=sys.stderr)
            return 1
    if int(data.get("inner_writes", 0)) != 42565830:
        print(f"unexpected inner_writes: {data.get('inner_writes')!r}", file=sys.stderr)
        return 1

    print(f"[OK] OLMRadialBlur small-span scatter stats: {stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
