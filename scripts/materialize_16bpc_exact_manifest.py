#!/usr/bin/env python3
"""Materialize currently proven 16bpc exact slices into committed conformance artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = ROOT / "scripts" / "verify_ae_pixel_validation_result.py"

SUITES = [
    {
        "plugin": "OLMColorKey",
        "feature": "OLMColorKey covered 16bpc slice",
        "request": ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmcolorkey_exact_20260625",
        "result": ROOT / "handoff" / "ae_pixel_validation_20260618" / "results" / "bitdepth16_olmcolorkey_exact",
        "bit_depth": "16bpc",
        "notes": "Live Mac AE verification against the imported Windows Software 16bpc request currently passes 9/9 with max_diff=0.",
        "evidence_status": "AE exact",
    },
    {
        "plugin": "OLMToonDilate",
        "feature": "OLMToonDilate covered 16bpc slice",
        "request": ROOT / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_olm_bitdepth_16bpc_toondilate_exact_20260703",
        "result": ROOT / "handoff" / "ae_pixel_validation_20260618" / "results" / "olm_bitdepth_16bpc_toondilate_exact",
        "bit_depth": "16bpc",
        "notes": "Live Mac AE verification against the imported Windows Software 16bpc request currently passes 3/3 with max_diff=0.",
        "evidence_status": "AE exact",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for the committed conformance artifacts (default: today in local time).",
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="Optional explicit output path for the manifest JSON.",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=None,
        help="Optional explicit output path for the markdown summary.",
    )
    return parser.parse_args()


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_verify(request: Path, result: Path) -> tuple[dict[str, Any], Path]:
    with tempfile.TemporaryDirectory(prefix="olm_16bpc_exact_") as tmp:
        run_dir = Path(tmp) / "verify"
        proc = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT), str(request), str(result), "--run-dir", str(run_dir)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"verification failed for {request.name}\n{proc.stdout}")
        report_dir = run_dir / "reports"
        json_reports = sorted(report_dir.glob("*.json"))
        if len(json_reports) != 1:
            raise RuntimeError(f"expected one report json in {report_dir}, found {len(json_reports)}")
        data = json.loads(json_reports[0].read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"invalid report json: {json_reports[0]}")
        return data, json_reports[0]


def result_status(row: dict[str, Any]) -> str:
    if row.get("status") == "missing":
        return "invalid"
    try:
        max_diff = float(row.get("max_diff"))
    except (TypeError, ValueError):
        return "invalid"
    if row.get("status") == "compared" and max_diff == 0:
        return "AE exact"
    return "AE residual"


def candidate_path(result_dir: Path, frame: str) -> Path | None:
    path = result_dir / frame
    return path if path.exists() else None


def build_manifest() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    suites_out: list[dict[str, Any]] = []
    for suite in SUITES:
        report, ephemeral_report_path = run_verify(suite["request"], suite["result"])
        rows = [row for row in report.get("cases", []) if isinstance(row, dict)]
        suite_counts = Counter()
        for row in rows:
            status = result_status(row)
            suite_counts[status] += 1
            frame = row.get("frame")
            output_path = candidate_path(suite["result"], frame) if isinstance(frame, str) else None
            cases.append(
                {
                    "plugin": suite["plugin"],
                    "feature": suite["feature"],
                    "case_id": str(row.get("id") or row.get("frame") or ""),
                    "bit_depth": suite["bit_depth"],
                    "reference_kind": "Windows AE Software",
                    "runner_kind": "Mac AE plugin",
                    "result_status": status,
                    "request_path": rel(suite["request"]),
                    "result_path": rel(suite["result"]),
                    "output_path": rel(output_path),
                    "output_sha256": sha256(output_path),
                    "max_diff": row.get("max_diff"),
                    "mean_diff": row.get("mean_diff"),
                    "nonzero_px_percent": row.get("nonzero_px_percent"),
                    "source_report_kind": "ephemeral_verify_run",
                    "notes": suite["notes"],
                }
            )
        suites_out.append(
            {
                "plugin": suite["plugin"],
                "feature": suite["feature"],
                "bit_depth": suite["bit_depth"],
                "request": rel(suite["request"]),
                "result": rel(suite["result"]),
                "case_count": len(rows),
                "counts": dict(sorted(suite_counts.items())),
                "evidence_status": suite["evidence_status"],
                "notes": suite["notes"],
                "verification_method": "scripts/verify_ae_pixel_validation_result.py",
                "ephemeral_report": str(ephemeral_report_path),
            }
        )
    counts = Counter(row["result_status"] for row in cases)
    by_plugin: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in cases:
        by_plugin[row["plugin"]][row["result_status"]] += 1
        by_plugin[row["plugin"]]["total"] += 1
    return {
        "kind": "olm_conformance_manifest",
        "schema": 1,
        "scope": "covered 16bpc AE-host exact slices",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correctness_bar": "Only result_status == 'AE exact' is complete for the declared bit-depth slice.",
        "summary": {
            "total_cases": len(cases),
            "counts": dict(sorted(counts.items())),
            "by_plugin": {plugin: dict(sorted(values.items())) for plugin, values in sorted(by_plugin.items())},
        },
        "suites": suites_out,
        "cases": cases,
    }


def write_markdown(manifest: dict[str, Any], path: Path) -> None:
    summary = manifest["summary"]
    lines = [
        "# Covered 16bpc Exact Slices",
        "",
        "This note freezes the 16bpc slices that can currently be re-verified",
        "locally against Windows AE Software references with zero diff.",
        "",
        f"- Generated at: `{manifest['generated_at']}`",
        f"- Total cases: `{summary['total_cases']}`",
        "",
        "## Totals",
        "",
    ]
    for status, count in summary["counts"].items():
        lines.append(f"- {status}: `{count}`")
    lines.extend(
        [
            "",
            "## By Plug-in",
            "",
            "| Plug-in | Total | AE exact | AE residual |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for plugin, counts in summary["by_plugin"].items():
        lines.append(
            f"| {plugin} | {counts.get('total', 0)} | {counts.get('AE exact', 0)} | {counts.get('AE residual', 0)} |"
        )
    lines.extend(["", "## Suites", ""])
    for suite in manifest["suites"]:
        lines.extend(
            [
                f"### {suite['plugin']}",
                "",
                f"- Feature: `{suite['feature']}`",
                f"- Bit depth: `{suite['bit_depth']}`",
                f"- Request: `{suite['request']}`",
                f"- Result dir: `{suite['result']}`",
                f"- Counts: `{suite['counts']}`",
                f"- Notes: {suite['notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- These rows are narrow covered slices only. They do not imply whole-plugin 16bpc completion.",
            "- `OLMColorKey` and `OLMToonDilate` can already be held to 16bpc `AE exact` for the declared covered cases.",
            "- `OLMBlur`, `OLMDistanceGradation`, and the unresolved hard plugins still need separate 16bpc proof lanes.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    out_json = args.manifest_json or ROOT / "refs" / "conformance" / f"bitdepth_16bpc_exact_manifest_{args.stamp}.json"
    out_md = args.summary_md or ROOT / "refs" / "conformance" / f"bitdepth_16bpc_exact_manifest_{args.stamp}.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(manifest, out_md)
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
