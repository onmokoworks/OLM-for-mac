#!/usr/bin/env python3
"""Generate the minimal conformance manifest/summary for packaged 8bpc AE checks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BITDEPTH_16BPC_EXACT_MANIFEST = ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260703.json"
BITDEPTH_32BPC_PROBE_STATUS = ROOT / "refs/conformance/bitdepth_32bpc_probe_status_20260703.json"

SUITES = [
    {
        "plugin": "OLMBlur",
        "feature": "OLMBlur packaged normalized slices",
        "report": "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/reports/ae_pixel_all_exact.json",
        "result_on_diff": "AE residual",
        "notes": "7/7 packaged 8bpc Mac AE exact; feature-level evidence status is AE exact but CLI unexplained because CLI max=1 remains a separate diagnostic.",
        "evidence_status": "AE exact but CLI unexplained",
    },
    {
        "plugin": "OLMColorKey",
        "feature": "OLMColorKey packaged normalized slices",
        "report": "refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmcolorkey_exact_20260619/reports/ae_pixel_all_exact.json",
        "result_on_diff": "reference-generation split",
        "notes": "ColorKey case_0009 is exact against normalized refs; old 20260604 Edge Blur drift is a reference-generation split, not an active AE failure.",
        "evidence_status": "normalized AE exact with legacy reference split",
    },
    {
        "plugin": "OLMToonDilate",
        "feature": "OLMToonDilate packaged slices",
        "report": "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/reports/ae_pixel_all_exact.json",
        "result_on_diff": "AE residual",
        "notes": "3/3 packaged 8bpc Mac AE exact.",
    },
    {
        "plugin": "OLMDistanceGradation",
        "feature": "OLMDistanceGradation basic packaged slices",
        "report": "refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json",
        "report_section": "ae_8bpc.cases",
        "group": "basic",
        "result_on_diff": "known-red",
        "notes": "Depth-correct current-binary 8bpc measurement: 0/12 exact; historical exact candidates have unbound loaded-plugin provenance.",
        "evidence_status": "current-binary depth-correct AE measurement",
    },
    {
        "plugin": "OLMDistanceGradation",
        "feature": "OLMDistanceGradation extended packaged slices",
        "report": "refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json",
        "report_section": "ae_8bpc.cases",
        "group": "extended",
        "result_on_diff": "known-red",
        "notes": "Depth-correct current-binary 8bpc measurement: 0/16 exact; historical exact candidates have unbound loaded-plugin provenance.",
        "evidence_status": "current-binary depth-correct AE measurement",
    },
    {
        "plugin": "OLMDistanceGradation",
        "feature": "OLMDistanceGradation blur packaged slice",
        "report": "refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json",
        "report_section": "ae_8bpc.cases",
        "group": "blur",
        "result_on_diff": "known-red",
        "notes": "Depth-correct current-binary 8bpc measurement: case_0029 max=23; historical exact candidate has unbound loaded-plugin provenance.",
        "evidence_status": "current-binary depth-correct AE measurement",
    },
    {
        "plugin": "OLMSmoother",
        "feature": "OLMSmoother v1 packaged compatibility slices",
        "report": "refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother_v1_20260619/reports/ae_pixel_exact.json",
        "result_on_diff": "AE residual",
        "notes": "3/3 packaged 8bpc Mac AE exact; v2 compatibility policy remains separate.",
    },
    {
        "plugin": "OLMSmoother2",
        "feature": "OLMSmoother2 no-key grid packaged slices",
        "report": "refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json",
        "result_on_diff": "AE residual",
        "notes": "12/12 no-key grid packaged 8bpc Mac AE exact.",
    },
    {
        "plugin": "OLMSmoother2",
        "feature": "OLMSmoother2 legacy/key packaged follow-up",
        "report": "refs/reports/ae_host_validation_20260620_smoother2_legacy_followup/ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json",
        "result_on_diff": "known-red",
        "notes": "Known-red legacy/key/gamma follow-up. Do not count these failures as AE exact.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=ROOT / "refs" / "conformance" / "packaged_8bpc_manifest.json",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "conformance_summary_packaged_8bpc.json",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "refs" / "reports" / "conformance_summary_packaged_8bpc.md",
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


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def supplemental_16bpc() -> dict[str, Any] | None:
    if not BITDEPTH_16BPC_EXACT_MANIFEST.exists():
        return None
    data = load_json(BITDEPTH_16BPC_EXACT_MANIFEST)
    summary = data.get("summary", {})
    return {
        "path": rel(BITDEPTH_16BPC_EXACT_MANIFEST),
        "scope": data.get("scope"),
        "counts": summary.get("counts", {}),
        "by_plugin": summary.get("by_plugin", {}),
    }


def supplemental_32bpc() -> dict[str, Any] | None:
    if not BITDEPTH_32BPC_PROBE_STATUS.exists():
        return None
    data = load_json(BITDEPTH_32BPC_PROBE_STATUS)
    suites = data.get("suites", [])
    lanes: list[dict[str, Any]] = []
    for row in suites:
        if not isinstance(row, dict):
            continue
        lanes.append(
            {
                "plugin": row.get("plugin"),
                "scope": row.get("scope"),
                "request_id": row.get("request_id"),
                "classification": row.get("classification"),
                "float_preserving_present": row.get("float_preserving_present"),
                "share_present": row.get("share_present"),
            }
        )
    return {
        "path": rel(BITDEPTH_32BPC_PROBE_STATUS),
        "compare_policy": "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md",
        "lanes": lanes,
    }


def result_status(row: dict[str, Any], suite: dict[str, str]) -> str:
    if row.get("status") == "missing":
        return "invalid"
    try:
        max_diff = int(row.get("max_diff"))
    except (TypeError, ValueError):
        return "invalid"
    if row.get("status") == "compared" and max_diff == 0:
        return "AE exact"
    if max_diff == 1:
        return "off-by-1 candidate"
    return suite["result_on_diff"]


def candidate_path(report_path: Path, frame: Any) -> Path | None:
    if not isinstance(frame, str) or not frame:
        return None
    path = report_path.parents[1] / "candidate" / frame
    return path if path.exists() else None


def report_rows(report: dict[str, Any], suite: dict[str, Any]) -> list[dict[str, Any]]:
    if suite.get("report_section") != "ae_8bpc.cases":
        return [row for row in report.get("cases", []) if isinstance(row, dict)]

    rows = report.get("ae_8bpc", {}).get("cases", [])
    group = suite.get("group")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("group") != group:
            continue
        case_id = str(row.get("case_id") or "")
        nonzero_px = row.get("nonzero_px")
        nonzero_px_percent = None
        if isinstance(nonzero_px, int):
            nonzero_px_percent = nonzero_px * 100.0 / (1920 * 1080)
        normalized.append(
            {
                "id": case_id,
                "frame": f"{case_id}.png",
                "status": "compared",
                "max_diff": row.get("max_diff"),
                "mean_diff": row.get("mean_diff"),
                "nonzero_px": nonzero_px,
                "nonzero_px_percent": nonzero_px_percent,
            }
        )
    return normalized


def build_manifest() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    suites_out: list[dict[str, Any]] = []
    for suite in SUITES:
        report_path = ROOT / suite["report"]
        report = load_json(report_path)
        rows = report_rows(report, suite)
        suite_counts = Counter()
        for row in rows:
            status = result_status(row, suite)
            suite_counts[status] += 1
            out_path = candidate_path(report_path, row.get("frame"))
            case_id = str(row.get("id") or row.get("frame") or "")
            cases.append(
                {
                    "plugin": suite["plugin"],
                    "feature": suite["feature"],
                    "case_id": case_id,
                    "bit_depth": "8bpc",
                    "reference_kind": "Windows AE Software",
                    "runner_kind": "Mac AE plugin",
                    "result_status": status,
                    "input_path": None,
                    "input_sha256": None,
                    "reference_path": None,
                    "reference_sha256": None,
                    "output_path": rel(out_path),
                    "output_sha256": sha256(out_path),
                    "max_diff": row.get("max_diff"),
                    "mean_diff": row.get("mean_diff"),
                    "nonzero_px_percent": row.get("nonzero_px_percent"),
                    "params": {},
                    "source_report": rel(report_path),
                    "notes": suite["notes"],
                }
            )
        suites_out.append(
            {
                "plugin": suite["plugin"],
                "feature": suite["feature"],
                "report": rel(report_path),
                "case_count": len(rows),
                "counts": dict(sorted(suite_counts.items())),
                "evidence_status": suite.get("evidence_status", "packaged AE-host measured"),
                "notes": suite["notes"],
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
        "scope": "packaged 8bpc AE-host validation M0",
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
    summary_16 = supplemental_16bpc()
    summary_32 = supplemental_32bpc()
    lines = [
        "# Packaged 8bpc Conformance Summary",
        "",
        "This is the minimal M0 machine summary for packaged 8bpc AE-host validation.",
        "`AE exact` is counted separately from known-red and other diagnostic states.",
        "",
        "## Totals",
        "",
        f"- Total cases: `{summary['total_cases']}`",
    ]
    for status, count in summary["counts"].items():
        lines.append(f"- {status}: `{count}`")
    lines.extend(
        [
            "",
            "## By Plug-in",
            "",
            "| Plug-in | Total | AE exact | reference-generation split | known-red | off-by-1 candidate | AE residual | invalid |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for plugin, counts in summary["by_plugin"].items():
        lines.append(
            "| {plugin} | {total} | {ae} | {split} | {red} | {off} | {residual} | {invalid} |".format(
                plugin=plugin,
                total=counts.get("total", 0),
                ae=counts.get("AE exact", 0),
                split=counts.get("reference-generation split", 0),
                red=counts.get("known-red", 0),
                off=counts.get("off-by-1 candidate", 0),
                residual=counts.get("AE residual", 0),
                invalid=counts.get("invalid", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Suites",
            "",
            "| Feature | Cases | Counts | Evidence status | Source report |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for suite in manifest["suites"]:
        counts = ", ".join(f"{key}={value}" for key, value in suite["counts"].items())
        lines.append(
            f"| {suite['feature']} | {suite['case_count']} | `{counts}` | "
            f"`{suite['evidence_status']}` | `{suite['report']}` |"
        )
    lines.extend(
        [
            "",
            "## Next Focus",
            "",
            "1. Keep this M0 summary as the source of truth for packaged 8bpc counts.",
            "2. Treat OLMBlur as `AE exact but CLI unexplained` until the max=1 CLI residual is binary-grounded.",
            "3. Treat OLMColorKey `case_0009` as a `reference-generation split`, not as an active AE residual.",
            "4. Do not promote Smoother2 legacy/key cases from `known-red` without new AE exact proof.",
        ]
    )
    if summary_16:
        lines.extend(
            [
                "",
                "## Supplemental 16bpc Exact Slices",
                "",
                "This section is supplemental only. It does not change the packaged 8bpc counts above.",
                f"- Source: `{summary_16['path']}`",
            ]
        )
        for status, count in sorted((summary_16.get("counts") or {}).items()):
            lines.append(f"- {status}: `{count}`")
        lines.extend(["", "| Plug-in | Total | AE exact |", "| --- | ---: | ---: |"])
        by_plugin = summary_16.get("by_plugin") or {}
        for plugin, counts in sorted(by_plugin.items()):
            if not isinstance(counts, dict):
                continue
            lines.append(
                f"| {plugin} | {counts.get('total', 0)} | {counts.get('AE exact', 0)} |"
            )
    if summary_32:
        lines.extend(
            [
                "",
                "## Supplemental 32bpc Probe Lanes",
                "",
                "These lanes are non-completion state only. They do not contribute to `AE exact` counts.",
                f"- Source: `{summary_32['path']}`",
                f"- Compare policy: `{summary_32['compare_policy']}`",
                "",
                "| Plug-in | Scope | Classification | float-preserving | Shared |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in summary_32["lanes"]:
            lines.append(
                f"| {row.get('plugin')} | {row.get('scope')} | `{row.get('classification')}` | "
                f"`{row.get('float_preserving_present')}` | `{row.get('share_present')}` |"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    generated_at = datetime.now(timezone.utc).isoformat()
    summary_16 = supplemental_16bpc()
    summary_32 = supplemental_32bpc()
    args.manifest_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.summary_json.write_text(
        json.dumps(
            {
                "kind": "olm_conformance_summary",
                "schema": 1,
                "generated_at": generated_at,
                "scope": manifest["scope"],
                "summary": manifest["summary"],
                "manifest": rel(args.manifest_json),
                "supplemental_16bpc_exact": summary_16,
                "supplemental_32bpc_probe": summary_32,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_markdown(manifest, args.summary_md)
    print(f"manifest_json={args.manifest_json}")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    print(f"total_cases={manifest['summary']['total_cases']}")
    print("counts=" + json.dumps(manifest["summary"]["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
