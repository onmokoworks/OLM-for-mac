#!/usr/bin/env python3
"""Smoke-test scripts/analyze_pending_runtime_trace_packages.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="pending_runtime_trace_smoke_") as tmp:
        out_json = Path(tmp) / "pending_runtime_trace_packages.json"
        out_md = Path(tmp) / "pending_runtime_trace_packages.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_pending_runtime_trace_packages.py",
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
        rows = report.get("requests", [])
        if not isinstance(rows, list) or not rows:
            raise AssertionError("expected runtime trace package rows")
        by_id = {row["request_id"]: row for row in rows}
        radial = by_id.get("olmradialblur_zoom_tiny_rotation_residual_witness_20260622")
        if radial is None:
            raise AssertionError("missing focused RadialBlur request")
        if radial["status"] != "pending":
            raise AssertionError(f"focused RadialBlur request should be pending, got {radial['status']}")
        if "compare_radialblur_trace.py" not in radial["comparison_command"]:
            raise AssertionError("focused RadialBlur request should point to the RadialBlur comparator")
        smoother_old = by_id.get("olmsmoother2_legacy_u8_writer_trace_20260620")
        if smoother_old is not None and smoother_old["status"] != "superseded":
            raise AssertionError("old Smoother2 trace should not be treated as active")
        markdown = out_md.read_text(encoding="utf-8")
        for needle in ("Pending Runtime Trace Packages", "Send First", "olmradialblur_zoom_tiny_rotation"):
            if needle not in markdown:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] pending runtime trace package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
