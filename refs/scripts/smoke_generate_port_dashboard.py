#!/usr/bin/env python3
"""Smoke-test the local OLM port dashboard generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olm_dashboard_smoke_") as tmp:
        runtime_package = Path(tmp) / "runtime_trace_requests_smoke.zip"
        package = subprocess.run(
            [py, "scripts/package_runtime_trace_requests.py", "--output", str(runtime_package)],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(package.stdout, end="" if package.stdout.endswith("\n") else "\n")
        if package.returncode != 0:
            return package.returncode
        if not runtime_package.exists():
            print("[FAIL] runtime trace smoke package missing")
            return 1

        out_dir = Path(tmp) / "dashboard"
        markdown_path = Path(tmp) / "PORT_DASHBOARD.md"
        proc = subprocess.run(
            [
                py,
                "refs/scripts/generate_port_dashboard.py",
                "--output-dir",
                str(out_dir),
                "--markdown",
                str(markdown_path),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode

        data_path = out_dir / "data.json"
        html_path = out_dir / "index.html"
        if not data_path.exists() or not html_path.exists() or not markdown_path.exists():
            print("[FAIL] dashboard output files missing")
            return 1
        data = json.loads(data_path.read_text(encoding="utf-8"))
        policy = data.get("completion_policy") or {}
        if policy.get("completion_status") != "AE exact":
            print("[FAIL] dashboard completion policy did not record AE exact")
            return 1
        if policy.get("reference_path") != "Windows AE Software render":
            print("[FAIL] dashboard completion policy did not record Windows Software reference")
            return 1
        runtime = data.get("runtime_trace_package") or {}
        if runtime.get("status") != "ready" or not str(runtime.get("relative_path", "")).endswith(".zip"):
            print("[FAIL] runtime trace package not recorded as ready")
            return 1
        send_target = data.get("send_target") or {}
        if send_target.get("status") != "ready" or not str(send_target.get("relative_path", "")).endswith(".zip"):
            print("[FAIL] send target not recorded as ready")
            return 1
        audit = data.get("mediacore_audit") or {}
        if "status" not in audit or "duplicate_count" not in audit:
            print("[FAIL] MediaCore audit summary missing")
            return 1
        actions = data.get("next_actions", {}).get("covered_actions", [])
        trace_actions = [
            action
            for action in actions
            if action.get("status") == "runtime-trace" or action.get("mode") == "external-trace"
        ]
        if len(trace_actions) < 2:
            print("[FAIL] expected RadialBlur and KiraKira runtime trace actions")
            return 1
        html = html_path.read_text(encoding="utf-8")
        for needle in ("Completion Policy", "Next Send Target", "Runtime Trace Package", "MediaCore Audit", "Blocking External Trace Actions"):
            if needle not in html:
                print(f"[FAIL] dashboard HTML missing section: {needle}")
                return 1
        markdown = markdown_path.read_text(encoding="utf-8")
        for needle in ("# OLM Port Dashboard", "Completion means AE exact", "Next send target", "Runtime trace package", "Blocking External Trace Actions"):
            if needle not in markdown:
                print(f"[FAIL] dashboard Markdown missing section: {needle}")
                return 1
    print("[OK] generate port dashboard smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
