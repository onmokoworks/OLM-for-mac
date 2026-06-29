#!/usr/bin/env python3
"""Smoke-test summarize_win_reference_return.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from smoke_olm_return_intake import make_windows_ref_return


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    intake = repo / "scripts" / "intake_olm_return.py"
    summary = repo / "scripts" / "summarize_win_reference_return.py"
    with tempfile.TemporaryDirectory(prefix="olm_smoke_win_ref_summary_") as tmp:
        tmp_path = Path(tmp)
        return_zip, requests_dir, request_path = make_windows_ref_return(tmp_path)
        dest_root = tmp_path / "win_references"
        next_actions = tmp_path / "next_actions.json"
        intake_proc = subprocess.run(
            [
                sys.executable,
                str(intake),
                str(return_zip),
                "--dest-root",
                str(dest_root),
                "--requests-dir",
                str(requests_dir),
                "--request",
                str(request_path),
                "--set-id",
                "synthetic_return",
                "--next-actions-json",
                str(next_actions),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(intake_proc.stdout, end="" if intake_proc.stdout.endswith("\n") else "\n")
        if intake_proc.returncode != 0:
            return intake_proc.returncode
        out_json = tmp_path / "summary.json"
        out_md = tmp_path / "summary.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(summary),
                str(return_zip),
                "--imported-set-dir",
                str(dest_root / "synthetic_return"),
                "--next-actions-json",
                str(next_actions),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(out_json.read_text(encoding="utf-8"))
        if report["source_summary"]["manifest_count"] != 1:
            print("[FAIL] expected one source manifest", file=sys.stderr)
            return 1
        if report["next_action"].get("request_id") != "synthetic_intake_20260606":
            print("[FAIL] expected next action request id", file=sys.stderr)
            return 1
    print("[OK] summarize Windows reference return smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
