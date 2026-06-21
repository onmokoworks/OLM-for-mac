#!/usr/bin/env python3
"""Smoke-test the focused KiraKira forward-warp / boxFilter input trace package."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="kirakira_forward_warp_pkg_") as tmp:
        output = Path(tmp) / "kirakira_forward_warp_box_input.zip"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                "kirakira-forward-warp-box-input",
                "--output",
                str(output),
            ],
            cwd=root,
            check=True,
        )
        with zipfile.ZipFile(output) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("runtime_trace_package_manifest.json").decode("utf-8"))
            template = json.loads(zf.read("RETURN_RUNTIME_TRACE_TEMPLATE.json").decode("utf-8"))
        actions = manifest.get("runtime_actions", [])
        if len(actions) != 1 or actions[0].get("request_id") != "kirakira_forward_warp_box_input_20260621":
            raise AssertionError(f"unexpected action list: {actions}")
        results = template.get("results", [])
        if len(results) != 1 or results[0].get("request_id") != "kirakira_forward_warp_box_input_20260621":
            raise AssertionError(f"unexpected template results: {results}")
        required = {
            "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md",
            "refs/reports/kirakira_deep_stage_values_20260621/runtime_trace_comparisons/olmkirakira_deep_stage_values.md",
        }
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package files: {missing}")
    print("[OK] KiraKira forward-warp box-input package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
