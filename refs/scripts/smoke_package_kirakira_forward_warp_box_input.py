#!/usr/bin/env python3
"""Smoke-test focused KiraKira boxFilter trace packages."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def assert_package(profile: str, output_name: str, request_id: str, required: set[str]) -> None:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix=f"{profile.replace('-', '_')}_pkg_") as tmp:
        output = Path(tmp) / output_name
        subprocess.run(
            [
                "python3",
                str(root / "scripts/package_runtime_trace_requests.py"),
                "--profile",
                profile,
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
        if len(actions) != 1 or actions[0].get("request_id") != request_id:
            raise AssertionError(f"unexpected action list: {actions}")
        results = template.get("results", [])
        if len(results) != 1 or results[0].get("request_id") != request_id:
            raise AssertionError(f"unexpected template results: {results}")
        missing = sorted(required - names)
        if missing:
            raise AssertionError(f"missing package files: {missing}")


def main() -> int:
    base_required = {
        "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md",
        "refs/reports/kirakira_deep_stage_values_20260621/runtime_trace_comparisons/olmkirakira_deep_stage_values.md",
    }
    assert_package(
        "kirakira-forward-warp-box-input",
        "kirakira_forward_warp_box_input.zip",
        "kirakira_forward_warp_box_input_20260621",
        base_required,
    )
    assert_package(
        "kirakira-boxfilter-pass1-microprobe",
        "kirakira_boxfilter_pass1_microprobe.zip",
        "kirakira_boxfilter_pass1_microprobe_20260622",
        {
            *base_required,
            "refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.md",
            "refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json",
            "refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.json",
            "refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.md",
        },
    )
    print("[OK] KiraKira forward-warp box-input package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
