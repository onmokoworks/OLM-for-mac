#!/usr/bin/env python3
"""Materialize the current committed 32bpc probe status into refs/conformance."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from summarize_win_reference_return import build_report


ROOT = Path(__file__).resolve().parents[1]
SHARE_ROOT = Path("/Volumes/onmk/olm_pr/new")

SUITES = [
    {
        "plugin": "OLMColorKey",
        "scope": "focused 32bpc probe",
        "request_json": ROOT / "refs" / "reference_requests" / "olm_bitdepth_32bpc_colorkey_probe_20260703.json",
        "package_zip": ROOT / "refs" / "runtime_trace_packages" / "olm_reference_request_32bpc_colorkey_probe_20260703.zip",
        "share_copy": SHARE_ROOT / "olm_reference_request_32bpc_colorkey_probe_20260703.zip",
        "returned_reference_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_colorkey_probe",
        "imported_set_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_colorkey_probe" / "OLMbit-depthconformancebatch",
        "expected_status": "probe-only",
        "next_action": "Keep this return probe-only because it is PNG-only; wait for a float-preserving EXR-first return before any 32bpc exact claim.",
    },
    {
        "plugin": "Cross-plugin batch",
        "scope": "broad 32bpc full probe",
        "request_json": ROOT / "refs" / "reference_requests" / "olm_bitdepth_32bpc_full_probe_20260703.json",
        "package_zip": ROOT / "refs" / "runtime_trace_packages" / "olm_reference_request_32bpc_full_probe_20260703.zip",
        "share_copy": SHARE_ROOT / "olm_reference_request_32bpc_full_probe_20260703.zip",
        "returned_reference_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_full_probe",
        "imported_set_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_full_probe" / "OLMbit-depthconformancebatch",
        "expected_status": "probe-only",
        "next_action": "Keep this broad batch probe-only because it is PNG-only; request a float-preserving EXR-first rerun before any 32bpc exact claim.",
    },
    {
        "plugin": "Cross-plugin batch",
        "scope": "broad 32bpc EXR-first rerun",
        "request_json": ROOT / "refs" / "reference_requests" / "olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json",
        "package_zip": ROOT / "refs" / "runtime_trace_packages" / "olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip",
        "share_copy": SHARE_ROOT / "olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip",
        "returned_reference_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun",
        "imported_set_dir": ROOT / "refs" / "win_references" / "olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun" / "OLMbit-depthconformancebatch",
        "expected_status": "probe-only",
        "next_action": "The EXR-first rerun still came back PNG-only/non-float-preserving, so it remains probe-only. Another Windows return must preserve float samples before any 32bpc exact claim.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for the committed conformance artifacts (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def public_path(path: Path | None) -> str | None:
    if path is None:
        return None
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return path.name
    return str(path)


def sanitize_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_paths(item) for item in value]
    if isinstance(value, str):
        if str(ROOT) in value:
            return value.replace(str(ROOT) + "/", "")
        if value.startswith(str(SHARE_ROOT)):
            return Path(value).name
    return value


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def suite_plugins(request_data: dict[str, Any]) -> list[str]:
    plugins = sorted(
        {
            case.get("plugin")
            for case in request_data.get("cases", [])
            if isinstance(case, dict) and isinstance(case.get("plugin"), str) and case.get("plugin")
        }
    )
    return plugins


def suite_status(suite: dict[str, Any]) -> dict[str, Any]:
    request_data = load_json(suite["request_json"])
    out: dict[str, Any] = {
        "plugin": suite["plugin"],
        "scope": suite["scope"],
        "request_id": request_data.get("request_id"),
        "request_json": rel(suite["request_json"]),
        "package_zip": rel(suite["package_zip"]),
        "share_copy": public_path(suite["share_copy"]),
        "share_present": suite["share_copy"].exists(),
        "case_count": len(request_data.get("cases", [])),
        "plugins": suite_plugins(request_data),
        "expected_status": suite["expected_status"],
        "next_action": suite["next_action"],
    }
    returned_dir = suite.get("returned_reference_dir")
    imported_dir = suite.get("imported_set_dir")
    if returned_dir and Path(returned_dir).exists():
        report = build_report(Path(returned_dir), Path(returned_dir), Path(imported_dir) if imported_dir else None, None)
        source_summary = report["source_summary"]
        imported_summary = sanitize_paths(report.get("imported_summary"))
        out.update(
            {
                "returned_reference_dir": rel(Path(returned_dir)),
                "imported_set_dir": rel(Path(imported_dir)) if imported_dir else None,
                "returned_case_count": source_summary.get("case_count", 0),
                "returned_asset_formats": source_summary.get("asset_formats", {}),
                "float_preserving_present": source_summary.get("float_preserving_present", False),
                "preferred_exr_present": source_summary.get("preferred_exr_present", False),
                "classification": report.get("reference_quality", "unclassified"),
                "reference_quality_reason": report.get("reference_quality_reason"),
                "imported_summary": imported_summary,
            }
        )
    else:
        out.update(
            {
                "returned_reference_dir": rel(Path(returned_dir)) if returned_dir else None,
                "imported_set_dir": rel(Path(imported_dir)) if imported_dir else None,
                "returned_case_count": 0,
                "returned_asset_formats": {},
                "float_preserving_present": False,
                "preferred_exr_present": False,
                "classification": "awaiting-return",
                "reference_quality_reason": "No returned reference directory is available yet.",
                "imported_summary": None,
            }
        )
    return out


def build_manifest() -> dict[str, Any]:
    suites = [suite_status(suite) for suite in SUITES]
    return {
        "kind": "olm_32bpc_probe_status",
        "schema": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "compare_policy": "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md",
        "suites": suites,
    }


def write_markdown(manifest: dict[str, Any], path: Path) -> None:
    lines = [
        "# 32bpc Probe Status",
        "",
        "This note freezes the current committed 32bpc probe state so that",
        "32bpc evidence does not live only in ignored reports or ad-hoc memory.",
        "",
        f"- Generated at: `{manifest['generated_at']}`",
        f"- Compare policy: `{manifest['compare_policy']}`",
        "",
        "| Lane | Cases | Classification | float-preserving | Share | Next action |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for suite in manifest["suites"]:
        lines.append(
            f"| `{suite['plugin']} / {suite['scope']}` | `{suite['case_count']}` | "
            f"`{suite['classification']}` | `{suite['float_preserving_present']}` | "
            f"`{suite['share_present']}` | {suite['next_action']} |"
        )
    lines.extend(["", "## Lane details", ""])
    for suite in manifest["suites"]:
        lines.extend(
            [
                f"### {suite['plugin']} - {suite['scope']}",
                "",
                f"- Request id: `{suite['request_id']}`",
                f"- Request JSON: `{suite['request_json']}`",
                f"- Package zip: `{suite['package_zip']}`",
                f"- Share copy: `{suite['share_copy']}` (`present={suite['share_present']}`)",
                f"- Cases: `{suite['case_count']}`",
                f"- Plug-ins covered: `{suite['plugins']}`",
                f"- Classification: `{suite['classification']}`",
                f"- float_preserving_present: `{suite['float_preserving_present']}`",
                f"- preferred_exr_present: `{suite['preferred_exr_present']}`",
                f"- Reference quality reason: `{suite['reference_quality_reason']}`",
                f"- Next action: {suite['next_action']}",
                "",
            ]
        )
        if suite["returned_reference_dir"]:
            lines.extend(
                [
                    f"- Returned dir: `{suite['returned_reference_dir']}`",
                    f"- Imported dir: `{suite['imported_set_dir']}`",
                    f"- Returned asset formats: `{suite['returned_asset_formats']}`",
                    "",
                ]
            )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- A PNG-only 32bpc return is useful as a probe and as request coverage proof, but not as `AE exact` evidence.",
            "- A float-preserving return may be compared mechanically now that `verify_manifest.py` keeps EXR/TIFF/HDR companions in float compare mode.",
            "- The broad full batch is intentionally tracked even before return so Windows/Mac handoff state stays explicit.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = build_manifest()
    out_json = args.output_json or ROOT / "refs" / "conformance" / f"bitdepth_32bpc_probe_status_{args.stamp}.json"
    out_md = args.output_md or ROOT / "refs" / "conformance" / f"bitdepth_32bpc_probe_status_{args.stamp}.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(manifest, out_md)
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
