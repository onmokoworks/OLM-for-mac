#!/usr/bin/env python3
"""Smoke-test summarize_ae_host_return.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from smoke_olm_return_intake import make_ae_host_return


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts" / "summarize_ae_host_return.py"
    with tempfile.TemporaryDirectory(prefix="olm_smoke_ae_host_summary_") as tmp:
        tmp_path = Path(tmp)
        handoff_zip, result_zip = make_ae_host_return(repo, tmp_path)
        out_json = tmp_path / "summary.json"
        out_md = tmp_path / "summary.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                str(result_zip),
                "--package",
                str(handoff_zip),
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
        if report["plugin_status_counts"].get("passed") != 10:
            print("[FAIL] expected 10 passed plugin rows", file=sys.stderr)
            return 1
        if report["pixel_request_counts"].get("matched", 0) == 0:
            print("[FAIL] expected matched pixel requests", file=sys.stderr)
            return 1
    print("[OK] summarize AE host return smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
