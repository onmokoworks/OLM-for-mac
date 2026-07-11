#!/usr/bin/env python3
"""Summarize current parallel OLM work lanes for bit-depth and provenance-first work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SHARE_NEW = Path("/Volumes/onmk/olm_pr/new")
KIRAKIRA_WITNESS_PATH_SPLIT_JSON = ROOT / "refs/conformance/olmkirakira_witness_path_split_20260703.json"
KIRAKIRA_LIVE_PROBE_JSON = ROOT / "refs/conformance/olmkirakira_live_hotspot_probe_20260703.json"
BITDEPTH_32BPC_PROBE_STATUS_JSON = ROOT / "refs/conformance/bitdepth_32bpc_probe_status_20260703.json"


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def exists_row(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False}
    return {"path": rel(path), "exists": path.exists()}


def load_32bpc_status_map() -> dict[str, dict[str, Any]]:
    if not BITDEPTH_32BPC_PROBE_STATUS_JSON.exists():
        return {}
    data = read_json(BITDEPTH_32BPC_PROBE_STATUS_JSON)
    suites = data.get("suites", [])
    out: dict[str, dict[str, Any]] = {}
    for row in suites:
        if not isinstance(row, dict):
            continue
        request_id = row.get("request_id")
        if isinstance(request_id, str) and request_id:
            out[request_id] = row
    return out


def in_share(filename: str) -> dict[str, Any]:
    path = SHARE_NEW / filename
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
    }


def bitdepth_lane(
    *,
    plugin: str,
    bit_depth: str,
    request_id: str,
    preview_dir: Path | None,
    request_json: Path | None,
    package_zip: Path | None,
    share_filename: str | None,
    returned_reference_dir: Path | None,
    tracked_note: Path | None,
    compared_artifact: Path | None,
    committed_status_row: dict[str, Any] | None,
    next_action: str,
) -> dict[str, Any]:
    preview_readme = preview_dir / "README.md" if preview_dir else None
    stages = {
        "preview": exists_row(preview_readme),
        "materialized_request_json": exists_row(request_json),
        "packaged_zip": exists_row(package_zip),
        "shared_exchange": in_share(share_filename) if share_filename else {"path": None, "exists": False},
        "returned_reference": exists_row(returned_reference_dir),
        "tracked_note": exists_row(tracked_note),
        "compared_artifact": exists_row(compared_artifact),
    }
    if stages["compared_artifact"]["exists"]:
        lifecycle = "compared"
    elif stages["returned_reference"]["exists"]:
        lifecycle = "returned"
    elif stages["shared_exchange"]["exists"]:
        lifecycle = "shared"
    elif stages["packaged_zip"]["exists"]:
        lifecycle = "packaged"
    elif stages["materialized_request_json"]["exists"]:
        lifecycle = "materialized"
    elif stages["preview"]["exists"]:
        lifecycle = "preview"
    else:
        lifecycle = "missing"
    row = {
        "kind": "bitdepth_lane",
        "plugin": plugin,
        "bit_depth": bit_depth,
        "request_id": request_id,
        "lifecycle": lifecycle,
        "stages": stages,
        "next_action": next_action,
    }
    if committed_status_row:
        row["committed_status"] = {
            "classification": committed_status_row.get("classification"),
            "expected_status": committed_status_row.get("expected_status"),
            "float_preserving_present": committed_status_row.get("float_preserving_present"),
            "preferred_exr_present": committed_status_row.get("preferred_exr_present"),
            "returned_asset_formats": committed_status_row.get("returned_asset_formats"),
            "share_present": committed_status_row.get("share_present"),
            "next_action": committed_status_row.get("next_action"),
        }
    return row


def provenance_lane(
    *,
    plugin: str,
    lane: str,
    audit_json: Path,
    summary_fields: dict[str, str],
    next_action: str,
) -> dict[str, Any]:
    data = read_json(audit_json)
    extracted: dict[str, Any] = {}
    for key, dotted in summary_fields.items():
        cursor: Any = data
        for part in dotted.split("."):
            if not isinstance(cursor, dict):
                cursor = None
                break
            cursor = cursor.get(part)
        extracted[key] = cursor
    return {
        "kind": "provenance_lane",
        "plugin": plugin,
        "lane": lane,
        "audit_json": rel(audit_json),
        "status": extracted.get("status"),
        "summary": extracted.get("summary"),
        "forbidden_action": extracted.get("forbidden_action"),
        "next_allowed_action": extracted.get("next_allowed_action"),
        "next_action": next_action,
    }


def build_report() -> dict[str, Any]:
    status_32bpc = load_32bpc_status_map()
    bitdepth = [
        bitdepth_lane(
            plugin="OLMColorKey",
            bit_depth="32bpc",
            request_id="olm_bitdepth_32bpc_colorkey_probe_20260703",
            preview_dir=ROOT / "refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260703",
            request_json=ROOT / "refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json",
            package_zip=ROOT / "refs/runtime_trace_packages/olm_reference_request_32bpc_colorkey_probe_20260703.zip",
            share_filename="olm_reference_request_32bpc_colorkey_probe_20260703.zip",
            returned_reference_dir=ROOT / "refs/win_references/olm_reference_return_windows_20260703_32bpc_colorkey_probe/OLMbit-depthconformancebatch",
            tracked_note=ROOT / "refs/conformance/olmcolorkey_32bpc_request_materialized_20260703.md",
            compared_artifact=None,
            committed_status_row=status_32bpc.get("olm_bitdepth_32bpc_colorkey_probe_20260703"),
            next_action="PNG-only 32bpc return is now imported and covered, but it remains probe-only. Next ask is an EXR-first float-preserving Windows return before any 32bpc completion claim.",
        ),
        bitdepth_lane(
            plugin="Full exact-origin batch",
            bit_depth="32bpc",
            request_id="olm_bitdepth_32bpc_full_probe_exr_rerun_20260703",
            preview_dir=ROOT / "refs/reports/bit_depth_32bpc_full_probe_exr_rerun_20260703",
            request_json=ROOT / "refs/reference_requests/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json",
            package_zip=ROOT / "refs/runtime_trace_packages/olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip",
            share_filename="olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip",
            returned_reference_dir=ROOT / "refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun/OLMbit-depthconformancebatch",
            tracked_note=ROOT / "refs/reports/bit_depth_32bpc_full_probe_exr_rerun_20260703/README.md",
            compared_artifact=None,
            committed_status_row=status_32bpc.get("olm_bitdepth_32bpc_full_probe_exr_rerun_20260703"),
            next_action="Broad 32bpc EXR-first rerun is imported and covered, but it came back PNG-only/non-float-preserving. Keep it probe-only; another Windows return must preserve float samples before any 32bpc exact claim.",
        ),
        bitdepth_lane(
            plugin="OLMToonDilate",
            bit_depth="16bpc",
            request_id="olm_bitdepth_16bpc_toondilate_exact_20260703",
            preview_dir=ROOT / "refs/reports/bit_depth_16bpc_toondilate_probe_plan_20260703",
            request_json=ROOT / "refs/reference_requests/olm_bitdepth_16bpc_toondilate_exact_20260703.json",
            package_zip=ROOT / "refs/runtime_trace_packages/olm_reference_request_16bpc_toondilate_exact_20260703.zip",
            share_filename="olm_reference_request_16bpc_toondilate_exact_20260703.zip",
            returned_reference_dir=ROOT / "refs/win_references/olm_reference_return_windows_20260703_combined/OLMbit-depthconformancebatch",
            tracked_note=ROOT / "refs/conformance/olmtoondilate_16bpc_request_materialized_20260703.md",
            compared_artifact=ROOT / "refs/conformance/olmtoondilate_16bpc_single_case_host_probe_20260703.md",
            committed_status_row=None,
            next_action="Windows 16bpc reference is now imported and the fresh Mac AE batch rerun is exact for all three ToonDilate cases. Treat this lane as covered and move the next effort to broader bit-depth expansion or final holdout use.",
        ),
        bitdepth_lane(
            plugin="Mixed exact batch",
            bit_depth="16bpc",
            request_id="olm_bitdepth_16bpc_normalized_exact_20260625",
            preview_dir=ROOT / "refs/reports/bit_depth_expansion_plan_20260625",
            request_json=ROOT / "refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json",
            package_zip=ROOT / "refs/runtime_trace_packages/olm_reference_requests_pending_20260703.zip",
            share_filename="olm_reference_requests_pending_20260703.zip",
            returned_reference_dir=ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625",
            tracked_note=ROOT / "refs/conformance/bitdepth_16bpc_reference_return_20260625.md",
            compared_artifact=ROOT / "refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix",
            committed_status_row=None,
            next_action="Keep using this as the authoritative returned 16bpc base batch; do not resend unless request contents change.",
        ),
    ]
    if KIRAKIRA_WITNESS_PATH_SPLIT_JSON.exists():
        kirakira_audit = KIRAKIRA_WITNESS_PATH_SPLIT_JSON
        kirakira_fields = {
            "status": "decision.status",
            "summary": "decision.reason",
            "next_allowed_action": "decision.next_action",
        }
    elif KIRAKIRA_LIVE_PROBE_JSON.exists():
        kirakira_audit = KIRAKIRA_LIVE_PROBE_JSON
        kirakira_fields = {
            "status": "decision.status",
            "summary": "decision.summary",
            "next_allowed_action": "decision.next_action",
        }
    else:
        kirakira_audit = ROOT / "refs/conformance/olmkirakira_reference_provenance_audit_20260701.json"
        kirakira_fields = {
            "status": "decision.status",
            "summary": "decision.reason",
            "forbidden_action": "decision.forbidden_action",
            "next_allowed_action": "decision.next_allowed_action",
        }
    provenance = [
        provenance_lane(
            plugin="OLMBlur",
            lane="case_0006 reference/export provenance",
            audit_json=ROOT / "refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.json",
            summary_fields={
                "status": "decision.status",
                "summary": "decision.reason",
                "next_allowed_action": "decision.next_step",
            },
            next_action="Do not patch OLMBlur source from case_0006 alone; Windows current-AEX export now matches canonical, so reopen only as Mac export / AE-host run provenance.",
        ),
        provenance_lane(
            plugin="OLMKiraKira",
            lane="hotspot live host / provenance / witness placement",
            audit_json=kirakira_audit,
            summary_fields=kirakira_fields,
            next_action="Reconcile historical 8bpc witness assumptions with current live 16bpc host output before more provenance-only reasoning.",
        ),
        provenance_lane(
            plugin="OLMDistanceGradation",
            lane="case_0023 threshold-family provenance split",
            audit_json=ROOT / "refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.json",
            summary_fields={
                "status": "status",
                "summary": "decision.summary",
                "next_allowed_action": "next_action",
            },
            next_action="Keep threshold-family triplet out of implementation tuning; recapture current Windows Software reference or split packaged expected from current-runtime lane.",
        ),
    ]
    return {
        "kind": "olm_parallel_lane_report",
        "schema": 1,
        "share_new": SHARE_NEW.as_posix(),
        "bitdepth_lanes": bitdepth,
        "provenance_lanes": provenance,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLM Parallel Lane Report",
        "",
        f"- Share folder: `{report['share_new']}`",
        "",
        "## Bit-depth lanes",
        "",
        "| Plug-in | Depth | Lifecycle | Committed | Shared | Returned | Compared | Tracked | Next action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["bitdepth_lanes"]:
        stages = row["stages"]
        committed = row.get("committed_status", {})
        committed_label = committed.get("classification", "-")
        lines.append(
            f"| `{row['plugin']}` | `{row['bit_depth']}` | `{row['lifecycle']}` | `{committed_label}` | "
            f"`{stages['shared_exchange']['exists']}` | `{stages['returned_reference']['exists']}` | "
            f"`{stages['compared_artifact']['exists']}` | `{stages['tracked_note']['exists']}` | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Provenance-first lanes",
            "",
            "| Plug-in | Lane | Status | Next allowed action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["provenance_lanes"]:
        lines.append(
            f"| `{row['plugin']}` | `{row['lane']}` | `{row.get('status', '-')}` | "
            f"{row.get('next_allowed_action') or row['next_action']} |"
        )
    lines.extend(["", "## Notes", ""])
    for row in report["provenance_lanes"]:
        lines.append(f"- `{row['plugin']}`: {row.get('summary')}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "refs/reports/parallel_lane_report.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "refs/reports/parallel_lane_report.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={rel(args.output_json)}")
    print(f"report_md={rel(args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
