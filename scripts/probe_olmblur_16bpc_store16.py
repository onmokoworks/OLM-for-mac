#!/usr/bin/env python3
"""Run bounded Mac AE witness captures for OLMBlur 16bpc store16 behavior."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST_DIR = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "requests"
    / "ae_pixel_bitdepth16_olmblur_exact_20260625"
)
DEFAULT_CASES = ["olmblur__case_0006", "olmblur__case_0007"]
DEFAULT_POINTS = "314,14;29,71;0,0;951,7"


POINT_RE = re.compile(
    r"OLMBLUR_DEBUG_POINT x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
    r"raw=\((?P<raw>[^)]*)\) raw_hex=\((?P<raw_hex>[^)]*)\) "
    r"floor05=\((?P<floor>[^)]*)\) nearby=\((?P<nearby>[^)]*)\) "
    r"rounded=\((?P<rounded>[^)]*)\) clamped=\((?P<clamped>[^)]*)\) "
    r"stored=\((?P<stored>[^)]*)\)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST_DIR)
    parser.add_argument("--case-id", action="append", default=[], help="Case id to run. May be repeated.")
    parser.add_argument("--points", default=DEFAULT_POINTS, help="Semicolon-separated x,y list.")
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Do not launch AE; write the probe plan only.")
    return parser.parse_args()


def parse_triplet(text: str) -> list[str]:
    return [part.strip() for part in text.split(",")]


def parse_debug_dump(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    points: list[dict[str, Any]] = []
    for line in lines:
        match = POINT_RE.match(line.strip())
        if not match:
            continue
        points.append(
            {
                "x": int(match.group("x")),
                "y": int(match.group("y")),
                "raw": parse_triplet(match.group("raw")),
                "raw_hex": parse_triplet(match.group("raw_hex")),
                "floor05": parse_triplet(match.group("floor")),
                "nearby": parse_triplet(match.group("nearby")),
                "rounded": parse_triplet(match.group("rounded")),
                "clamped": parse_triplet(match.group("clamped")),
                "stored": parse_triplet(match.group("stored")),
                "line": line.strip(),
            }
        )
    return {
        "path": str(path),
        "line_count": len(lines),
        "points": points,
    }


def build_probe_plan(args: argparse.Namespace, output_dir: Path, case_ids: list[str]) -> dict[str, Any]:
    return {
        "kind": "olmblur_16bpc_store16_probe_plan",
        "request_dir": str(args.request_dir.resolve()),
        "case_ids": case_ids,
        "points": args.points,
        "app_name": args.app_name,
        "output_dir": str(output_dir),
    }


def run_case(args: argparse.Namespace, case_id: str, output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    debug_path = case_dir / "blur_debug.txt"
    cmd = [
        "python3",
        str(ROOT / "scripts" / "run_ae_single_case.py"),
        "--request-dir",
        str(args.request_dir.resolve()),
        "--case-id",
        case_id,
        "--output-dir",
        str(case_dir),
        "--app-name",
        args.app_name,
        "--ae-env",
        f"OLMBLUR_DEBUG_DUMP_PATH={debug_path}",
        "--ae-env",
        f"OLMBLUR_DEBUG_POINTS={args.points}",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    result_json = case_dir / "AE_SINGLE_CASE_RESULT.json"
    result = json.loads(result_json.read_text(encoding="utf-8-sig")) if result_json.exists() else {}
    debug = parse_debug_dump(debug_path)
    return {
        "case_id": case_id,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "result_json": str(result_json),
        "result": result,
        "debug": debug,
    }


def write_reports(output_dir: Path, report: dict[str, Any]) -> None:
    json_path = output_dir / "probe_report.json"
    md_path = output_dir / "probe_report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# OLMBlur 16bpc Store16 Probe",
        "",
        f"- Request dir: `{report['request_dir']}`",
        f"- Points: `{report['points']}`",
        f"- Cases: {', '.join(report['case_ids'])}",
        f"- Dry run: `{str(report['dry_run']).lower()}`",
        "",
    ]
    for case in report["cases"]:
        result = case.get("result") or {}
        debug = case.get("debug") or {"line_count": 0, "points": []}
        lines.extend(
            [
                f"## {case['case_id']}",
                "",
                f"- returncode: `{case.get('returncode', 'dry-run')}`",
                f"- AE status: `{result.get('status', 'n/a')}`",
                f"- output_png: `{result.get('output_png', '')}`",
                f"- debug lines: `{debug.get('line_count', 0)}`",
                "",
            ]
        )
        for point in debug.get("points", []):
            lines.append(
                f"- ({point['x']},{point['y']}): raw={point['raw']} floor05={point['floor05']} "
                f"nearby={point['nearby']} stored={point['stored']}"
            )
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    case_ids = args.case_id or DEFAULT_CASES
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else ROOT / "refs" / "reports" / f"ae_single_case_olmblur_16bpc_witness_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = build_probe_plan(args, output_dir, case_ids)
    report["dry_run"] = args.dry_run
    report_cases: list[dict[str, Any]] = []
    if args.dry_run:
        for case_id in case_ids:
            report_cases.append(
                {
                    "case_id": case_id,
                    "command": [
                        "python3",
                        str(ROOT / "scripts" / "run_ae_single_case.py"),
                        "--request-dir",
                        str(args.request_dir.resolve()),
                        "--case-id",
                        case_id,
                        "--output-dir",
                        str(output_dir / case_id),
                        "--app-name",
                        args.app_name,
                        "--ae-env",
                        f"OLMBLUR_DEBUG_DUMP_PATH={output_dir / case_id / 'blur_debug.txt'}",
                        "--ae-env",
                        f"OLMBLUR_DEBUG_POINTS={args.points}",
                    ],
                }
            )
    else:
        for case_id in case_ids:
            report_cases.append(run_case(args, case_id, output_dir))
    report["cases"] = report_cases
    write_reports(output_dir, report)
    print(f"[OK] probe report: {output_dir / 'probe_report.json'}")
    print(f"[OK] probe markdown: {output_dir / 'probe_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
