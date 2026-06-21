#!/usr/bin/env python3
"""Run and trace OLMSmoother2 current-AEX legacy residual witness pixels."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


REQUEST_ID = "smoother2_legacy_full_current_aex_recapture_20260621"
EXPECTED_EFFECT = "OLM Smoother v2"
DEFAULT_CASES = [
    "legacy_case_0004_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/olmsmoother2_current_aex_residual_audit"))
    parser.add_argument("--keep-run-dir", action="store_true")
    return parser.parse_args()


def load_status_rows(root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(root / "refs" / "scripts"))
    from check_reference_request_status import load_status_rows as load_rows

    return load_rows(root / "refs" / "reference_requests", root / "refs" / "win_references")


def covered_manifest(root: Path) -> Path:
    for row in load_status_rows(root):
        if row.get("request_id") != REQUEST_ID or row.get("status") != "covered":
            continue
        manifest = (row.get("best") or {}).get("manifest")
        if isinstance(manifest, str) and manifest:
            path = Path(manifest)
            return path if path.is_absolute() else (root / path).resolve()
    raise FileNotFoundError(f"covered manifest not found for {REQUEST_ID}")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def case_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for index, case in enumerate(manifest.get("cases", []), start=1):
        if isinstance(case, dict):
            rows[str(case.get("id") or f"case_{index:04d}")] = case
    return rows


def run(command: list[Any], root: Path, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(str(part) for part in command), flush=True)
    return subprocess.run(
        [str(part) for part in command],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def read_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def max_witness(reference_path: Path, candidate_path: Path) -> dict[str, Any]:
    reference = read_rgba(reference_path)
    candidate = read_rgba(candidate_path)
    if reference.shape != candidate.shape:
        raise ValueError(f"shape mismatch: {reference_path} {reference.shape} vs {candidate_path} {candidate.shape}")
    delta = np.abs(reference.astype(np.int32) - candidate.astype(np.int32))
    pixel_delta = delta.max(axis=-1)
    y, x = np.unravel_index(np.argmax(pixel_delta), pixel_delta.shape)
    return {
        "x": int(x),
        "y": int(y),
        "max_channel_diff": int(pixel_delta[y, x]),
        "reference_rgba": [int(v) for v in reference[y, x]],
        "candidate_rgba": [int(v) for v in candidate[y, x]],
        "delta_rgba": [int(v) for v in delta[y, x]],
        "mean_diff": float(delta.mean()),
        "nonzero_px": int((delta.any(axis=-1)).sum()),
        "total_px": int(reference.shape[0] * reference.shape[1]),
    }


def read_diff_rows(csv_path: Path) -> dict[str, dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Residual Audit",
        "",
        f"- Request: `{report['request_id']}`",
        f"- Manifest: `{report['manifest']}`",
        f"- Run dir: `{report['run_dir']}`",
        "",
        "| Case | Max witness | Reference | Candidate | Delta | Diff metrics | Trace log |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        w = row["witness"]
        metrics = row.get("diff_metrics", {})
        lines.append(
            f"| `{row['case_id']}` | `({w['x']},{w['y']}) max={w['max_channel_diff']}` | "
            f"`{w['reference_rgba']}` | `{w['candidate_rgba']}` | `{w['delta_rgba']}` | "
            f"`max={metrics.get('max_diff')} mean={metrics.get('mean_diff')} nz%={metrics.get('nonzero_px_percent')}` | "
            f"`{row['trace_log']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Use this report to pick the next binary-grounded witness.",
            "- A local trace is not Windows proof; it only identifies the current Mac path and residual coordinate.",
            "- Do not promote diagnostic switches unless the full case metrics improve and the IR has asm/runtime support.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    manifest_path = covered_manifest(root)
    manifest = load_json(manifest_path)
    cases = case_by_id(manifest)
    case_ids = args.case_id or DEFAULT_CASES
    missing = [case_id for case_id in case_ids if case_id not in cases]
    if missing:
        print("[FAIL] missing case ids: " + ", ".join(missing), file=sys.stderr)
        return 2

    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    if output_dir.exists() and not args.keep_run_dir:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    build = run([root / "refs" / "scripts" / "build_olmsmoother2_cli.sh"], root)
    if build.returncode != 0:
        return build.returncode

    run_dir = output_dir / "run"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = '"cli/OLMSmoother2/olmsmoother2_cli" --input "{input}" --params "{params}" --output "{output}"'
    ref_run = [
        sys.executable,
        root / "refs" / "scripts" / "run_reference_test.py",
        manifest_path.parent,
        "--run-dir",
        run_dir,
        "--expected-effect",
        EXPECTED_EFFECT,
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "255",
        "--nonzero-px-percent",
        "100",
    ]
    for case_id in case_ids:
        ref_run.extend(["--case-id", case_id])
    proc = run(ref_run, root)
    if proc.returncode != 0:
        return proc.returncode

    diff_rows = read_diff_rows(run_dir / "reports" / "diff.csv")
    report_cases: list[dict[str, Any]] = []
    for case_id in case_ids:
        case = cases[case_id]
        frame = str(case.get("frame") or f"{case_id}.png")
        before = str(case.get("before_effects_frame") or "")
        reference_png = run_dir / "reference" / frame
        candidate_png = run_dir / "candidate" / frame
        params_matches = sorted((run_dir / "candidate" / "_params").glob(f"*{case_id}*.json"))
        if not params_matches:
            raise FileNotFoundError(f"params JSON not found for {case_id}")
        params_json = params_matches[0]
        input_png = run_dir / "reference" / before
        witness = max_witness(reference_png, candidate_png)
        trace_log = output_dir / f"{case_id}_trace_{witness['x']}_{witness['y']}.log"
        trace_png = output_dir / f"{case_id}_trace.png"
        trace = run(
            [
                root / "cli" / "OLMSmoother2" / "olmsmoother2_cli",
                "--input",
                input_png,
                "--params",
                params_json,
                "--output",
                trace_png,
                "--trace-pixel",
                f"{witness['x']},{witness['y']}",
            ],
            root,
            capture=True,
        )
        trace_log.write_text(trace.stdout or "", encoding="utf-8")
        if trace.returncode != 0:
            return trace.returncode
        report_cases.append(
            {
                "case_id": case_id,
                "frame": frame,
                "before_effects_frame": before,
                "witness": witness,
                "diff_metrics": diff_rows.get(case_id, {}),
                "params_json": str(params_json),
                "trace_log": str(trace_log),
            }
        )

    report = {
        "kind": "olmsmoother2_current_aex_residual_audit",
        "schema": 1,
        "request_id": REQUEST_ID,
        "manifest": str(manifest_path),
        "run_dir": str(run_dir),
        "cases": report_cases,
    }
    json_path = output_dir / "residual_audit.json"
    md_path = output_dir / "residual_audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={json_path}")
    print(f"report_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
