#!/usr/bin/env python3
"""Smoke-test runtime trace intake with Windows-style zip member paths."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


REQUEST_ID = "synthetic_windows_path_runtime_trace_20260708"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="verify_runtime_windows_zip_") as tmp_name:
        tmp = Path(tmp_name)
        package = tmp / "request.zip"
        returned = tmp / "return.zip"
        summary_json = tmp / "summary.json"
        summary_md = tmp / "summary.md"

        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(
                "runtime_trace_package_manifest.json",
                json.dumps(
                    {
                        "runtime_actions": [
                            {
                                "request_id": REQUEST_ID,
                                "plugin_area": "synthetic",
                            }
                        ]
                    },
                    indent=2,
                ),
            )

        with zipfile.ZipFile(returned, "w") as archive:
            archive.writestr(
                r"synthetic_return\RETURN_RUNTIME_TRACE_RESULT.json",
                json.dumps(
                    {
                        "kind": "olm_runtime_trace_result",
                        "results": [
                            {
                                "request_id": REQUEST_ID,
                                "status": "answered_partial",
                                "summary": "synthetic Windows path return",
                                "observations": {"value": 1},
                            }
                        ],
                    },
                    indent=2,
                ),
            )
            archive.writestr(
                r"synthetic_return\very\deep\windows\path\payload.txt",
                "payload",
            )

        proc = subprocess.run(
            [
                py,
                "scripts/verify_runtime_trace_return.py",
                str(returned),
                "--require-all",
                "--package",
                str(package),
                "--summary-json",
                str(summary_json),
                "--summary-md",
                str(summary_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        required = summary.get("required", [])
        if not required or required[0].get("request_id") != REQUEST_ID or not required[0].get("answered"):
            print(f"[FAIL] unexpected required summary: {required}")
            return 1
        if "synthetic Windows path return" not in summary_md.read_text(encoding="utf-8"):
            print("[FAIL] summary markdown missing synthetic return text")
            return 1
    print("[OK] runtime trace Windows-path zip smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
