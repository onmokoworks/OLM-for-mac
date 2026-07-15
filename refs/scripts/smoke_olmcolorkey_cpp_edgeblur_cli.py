#!/usr/bin/env python3
"""Smoke-test the C++ OLMColorKey Edge Blur gate and legacy diagnostics."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

EDGE_BLUR_DIFFERENTIAL = "tests/test_olmcolorkey_edge_blur_apply_differential_20260716.py"


def run_current_aex_gate(root: Path, label: str) -> int:
    report_path = Path(f"/tmp/{label}_current_aex_edge_blur_report.json")
    if report_path.exists():
        report_path.unlink()
    args = [
        sys.executable,
        str(root / EDGE_BLUR_DIFFERENTIAL),
        "--report",
        str(report_path),
        "--enforce",
    ]
    rc = subprocess.run(args, cwd=root).returncode
    if rc != 0:
        return rc
    if not report_path.exists():
        print(f"[FAIL] missing current-AEX differential report: {report_path}", file=sys.stderr)
        return 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    exact_cases = int(((report.get("production_result") or {}).get("exact_cases")) or 0)
    total_cases = len(report.get("cases") or [])
    print(
        f"[OK] current-AEX Edge Blur differential exact_cases={exact_cases}/{total_cases} "
        f"report_json={report_path}"
    )
    return 0


def run_superseded_old_reference_diagnostic(root: Path, reference: Path, command: str, run_dir: Path) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0008",
        "--case-id",
        "case_0009",
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
    ]
    rc = subprocess.run(args, cwd=root).returncode
    report_json = run_dir / "reports" / "diff.json"
    if not report_json.exists():
        return rc if rc != 0 else 1

    report = json.loads(report_json.read_text(encoding="utf-8"))
    case_ids = [row.get("id") for row in report.get("cases", [])]
    if case_ids != ["case_0008", "case_0009"]:
        print(f"[FAIL] superseded-old-reference diagnostic drifted: {case_ids}", file=sys.stderr)
        return 1
    print("=== superseded-old-reference diagnostic ===")
    for row in report.get("cases", []):
        print(
            "[INFO] superseded-old-reference "
            f"{row.get('id')}: status={row.get('status')} max={row.get('max_diff')} "
            f"mean={float(row.get('mean_diff', 0.0)):.4f} "
            f"nz%={float(row.get('nonzero_px_percent', 0.0)):.4f}"
        )
    print(f"legacy_report_json={report_json}")
    print(f"legacy_diff_dir={run_dir / 'diff'}")
    return 0 if rc in (0, 1) else rc


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    command = (
        '"cli/OLMColorKey/olmcolorkey_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    rc = run_current_aex_gate(root, "olmcolorkey_cpp_edgeblur")
    if rc != 0:
        return rc

    return run_superseded_old_reference_diagnostic(
        root,
        reference,
        command,
        Path("/tmp/olmcolorkey_cpp_edgeblur_superseded_old_reference"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
