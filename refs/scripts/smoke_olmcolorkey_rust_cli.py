#!/usr/bin/env python3
"""Smoke-test the Rust OLMColorKey CLI RGB/Edge Thin gates and Edge Blur diagnostics."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

EDGE_BLUR_DIFFERENTIAL = "tests/test_olmcolorkey_edge_blur_apply_differential_20260716.py"


def run_group(root: Path, reference: Path, run_dir: Path, case_ids: list[str], *threshold_args: str) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMColorKey/olmcolorkey_rust_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])
    args.extend(threshold_args)
    return subprocess.run(args, cwd=root).returncode


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


def run_superseded_old_reference_diagnostic(root: Path, reference: Path, run_dir: Path) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMColorKey/olmcolorkey_rust_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
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

    rc = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_rust_cli.sh")], cwd=root).returncode
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_rgb_smoke"),
        ["case_0001", "case_0002", "case_0003", "case_0004"],
    )
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_edgethin_exact_smoke"),
        ["case_0007"],
    )
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_edgethin_residual_smoke"),
        ["case_0005", "case_0006"],
        "--max-diff",
        "255",
        "--mean-diff",
        "0.31",
        "--nonzero-px-percent",
        "0.49",
    )
    if rc != 0:
        return rc

    rc = run_current_aex_gate(root, "olmcolorkey_rust")
    if rc != 0:
        return rc

    return run_superseded_old_reference_diagnostic(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_superseded_old_reference"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
