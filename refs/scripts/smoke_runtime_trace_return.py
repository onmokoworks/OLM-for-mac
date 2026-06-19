#!/usr/bin/env python3
"""Smoke-test runtime trace return verification and intake routing."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(cmd: list[str], repo: Path) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def make_return_zip(path: Path, *, member: str = "runtime_trace_result.json", bare_results: bool = False) -> None:
    result = {
        "schema": 1,
        "results": [
            {
                "request_id": "radialblur_inner_runtime_trace_20260618",
                "status": "answered",
                "summary": "Synthetic smoke: R14D after +0x1d18 was 31.",
                "observations": {
                    "case_id": "rb_inner_only_strength_small",
                    "r14d_after_0x1d18": 31,
                },
            },
            {
                "request_id": "kirakira_opencv455_primitive_fact_20260618",
                "status": "answered",
                "summary": "Synthetic smoke: FUN_181281260 selected FUN_1812e39d0.",
                "observations": {
                    "filterengine_branch": "FUN_1812e39d0",
                    "box_filter": "RowSum<float,double>/ColumnSum<double,float> equivalent",
                },
            },
        ],
    }
    if not bare_results:
        result["kind"] = "olm_runtime_trace_result"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, json.dumps(result, indent=2))


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olm_runtime_trace_return_smoke_") as tmp:
        tmp_path = Path(tmp)
        package = tmp_path / "runtime_request.zip"
        package_proc = run([py, "scripts/package_runtime_trace_requests.py", "--output", str(package)], repo)
        if package_proc.returncode != 0:
            return package_proc.returncode

        returned = tmp_path / "runtime_trace_return.zip"
        make_return_zip(returned)
        summary_json = tmp_path / "runtime_summary.json"
        summary_md = tmp_path / "runtime_summary.md"
        proc = run(
            [
                py,
                "scripts/verify_runtime_trace_return.py",
                str(returned),
                "--package",
                str(package),
                "--require-all",
                "--summary-json",
                str(summary_json),
                "--summary-md",
                str(summary_md),
            ],
            repo,
        )
        if proc.returncode != 0:
            return proc.returncode
        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        if not all(row["answered"] for row in summary["required"]):
            print("[FAIL] runtime trace summary did not mark all required rows answered")
            return 1
        markdown = summary_md.read_text(encoding="utf-8")
        for needle in ("# OLM Runtime Trace Return Summary", "r14d_after_0x1d18", "filterengine_branch"):
            if needle not in markdown:
                print(f"[FAIL] runtime trace Markdown summary missing: {needle}")
                return 1

        intake_summary = tmp_path / "runtime_intake_summary.json"
        intake_markdown = tmp_path / "runtime_intake_summary.md"
        intake_comparisons = tmp_path / "runtime_intake_comparisons"
        intake = run(
            [
                py,
                "scripts/intake_olm_return.py",
                str(returned),
                "--runtime-package",
                str(package),
                "--runtime-summary-json",
                str(intake_summary),
                "--runtime-summary-md",
                str(intake_markdown),
                "--runtime-comparison-dir",
                str(intake_comparisons),
            ],
            repo,
        )
        if intake.returncode != 0:
            return intake.returncode
        if "[INFO] detected return kind: runtime-trace" not in intake.stdout:
            print("[FAIL] intake did not auto-detect runtime-trace return")
            return 1
        if not intake_summary.exists():
            print("[FAIL] intake did not write runtime summary JSON")
            return 1
        if not intake_markdown.exists():
            print("[FAIL] intake did not write runtime summary Markdown")
            return 1
        if not (intake_comparisons / "index.json").exists():
            print("[FAIL] intake did not write runtime comparison index JSON")
            return 1

        nested_returned = tmp_path / "nested_runtime_trace_return.zip"
        make_return_zip(nested_returned, member="runtime_trace_return/runtime_trace_result.json")
        nested_summary = tmp_path / "nested_runtime_summary.json"
        nested = run(
            [
                py,
                "scripts/verify_runtime_trace_return.py",
                str(nested_returned),
                "--package",
                str(package),
                "--require-all",
                "--summary-json",
                str(nested_summary),
            ],
            repo,
        )
        if nested.returncode != 0:
            return nested.returncode

        bare_returned = tmp_path / "bare_runtime_trace_return.zip"
        make_return_zip(bare_returned, member="nested/result.json", bare_results=True)
        bare_intake_summary = tmp_path / "bare_runtime_intake_summary.json"
        bare_intake_markdown = tmp_path / "bare_runtime_intake_summary.md"
        bare_intake = run(
            [
                py,
                "scripts/intake_olm_return.py",
                str(bare_returned),
                "--runtime-package",
                str(package),
                "--runtime-summary-json",
                str(bare_intake_summary),
                "--runtime-summary-md",
                str(bare_intake_markdown),
                "--no-runtime-comparisons",
            ],
            repo,
        )
        if bare_intake.returncode != 0:
            return bare_intake.returncode
        if "[INFO] detected return kind: runtime-trace" not in bare_intake.stdout:
            print("[FAIL] intake did not auto-detect bare runtime-trace results")
            return 1
        if not bare_intake_markdown.exists():
            print("[FAIL] intake did not write bare runtime Markdown summary")
            return 1
    print("[OK] runtime trace return smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
