#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def find_case(rows: list[dict], case_id: str) -> dict:
    for row in rows:
        if row.get("case_id") == case_id:
            return row
    raise KeyError(f"case not found: {case_id}")


def latest_runtime_observations(runtime_summary: dict) -> dict:
    results = runtime_summary.get("results", [])
    if not isinstance(results, list) or not results:
        raise ValueError("runtime summary results missing")
    observations = results[0].get("observations", {})
    if not isinstance(observations, dict):
        raise ValueError("runtime summary observations missing")
    return observations


def build_summary(
    rep: dict,
    rejected: dict,
    runtime_package: Path,
    runtime_summary: dict,
    runtime_summary_path: Path,
) -> dict:
    case0012 = find_case(rep["cases"], "olmdistancegradation_extended__case_0012")
    case0020 = find_case(rep["cases"], "olmdistancegradation_extended__case_0020")
    rejected_reverted = next(row for row in rejected["rows"] if row["variant"] == "reverted_after_ae_restart")
    runtime_obs = latest_runtime_observations(runtime_summary)
    runtime_cases = {
        str(case.get("case_id")): case
        for case in runtime_obs.get("cases", [])
        if isinstance(case, dict)
    }
    runtime_case0012 = runtime_cases.get("olmdistancegradation_extended__case_0012", {})
    runtime_case0016 = runtime_cases.get("olmdistancegradation_extended__case_0016", {})
    return {
        "kind": "olmdistancegradation_layer_source_pending_proof",
        "date": "2026-06-29",
        "runtime_package": str(runtime_package),
        "latest_runtime_summary": str(runtime_summary_path),
        "priority": 1,
        "active_request": "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629",
        "decision_boundary": (
            "Determine whether Windows Layer/no-bg 16bpc compose derives RGB from straight source "
            "times output alpha, from already-premultiplied source, or from another ownership rule."
        ),
        "why_png_is_not_enough": [
            "The direct Layer/no-bg unpremultiply hypothesis is already rejected because it widened coverage from 25421 to 285406 changed pixels.",
            "The current narrowed Mac fix matches the primary case_0012 witness alpha and nearly matches RGB, but the family is still not AE exact.",
            "The remaining ambiguity is the exact source RGB ownership inside the Windows compose branch, not a generic threshold or writeback issue.",
        ],
        "witness_cases": [
            {
                "case_id": case0012["case_id"],
                "family": case0012["family"],
                "changed_pixel_count": case0012["changed_pixel_count"],
                "primary_points": case0012["samples"][:2],
                "current_reverted_max_witness": rejected_reverted["max_witness"],
                "latest_windows_runtime_note": {
                    "branch_decision": runtime_obs.get("branch_decision"),
                    "pixels": runtime_case0012.get("pixels"),
                },
                "expected_use": "Primary Layer/no-bg source-ownership branch proof.",
            },
            {
                "case_id": "olmdistancegradation_extended__case_0016",
                "family": "layer-no-bg-companion-ownership-separator",
                "changed_pixel_count": runtime_case0016.get("pixels", [{}])[0].get("delta") if runtime_case0016.get("pixels") else None,
                "primary_points": runtime_case0016.get("pixels", []),
                "expected_use": "Companion Layer/no-bg witness that cleanly separates straight-source-times-output-alpha from double-premultiplied ownership.",
            },
            {
                "case_id": case0020["case_id"],
                "family": case0020["family"],
                "changed_pixel_count": case0020["changed_pixel_count"],
                "primary_points": case0020["samples"][:2],
                "expected_use": "Secondary Constant/background control family; not the current runtime-trace target.",
            },
        ],
        "return_is_actionable_if": [
            "It records the actual source-layer RGBA values consumed by the Windows Layer/no-bg compose path at case_0012/case_0016 witnesses.",
            "It records any premultiply or unpremultiply step between source-layer read and the already supported straight-source-times-output-alpha branch.",
            "It records the output floats before 16bpc writeback and the final RGBA16 words at the same pixels.",
        ],
        "return_is_not_actionable_if": [
            "It only returns final PNG or final RGBA16 values without the compose-path source ownership steps.",
            "It records the wrong branch family (for example only case_0020 Constant/background behavior).",
            "It confirms values after the point where RGB ownership has already been collapsed and cannot distinguish straight vs premultiplied source handling.",
        ],
    }


def write_markdown(summary: dict, out: Path) -> None:
    case0012, case0016, case0020 = summary["witness_cases"]
    lines = [
        "# OLMDistanceGradation Pending Layer/no-bg Proof",
        "",
        f"- Active request: `{summary['active_request']}`",
        f"- Runtime package: `{summary['runtime_package']}`",
        f"- Latest runtime summary: `{summary['latest_runtime_summary']}`",
        f"- Priority: `{summary['priority']}`",
        "",
        "## Decision Boundary",
        "",
        summary["decision_boundary"],
        "",
        "## Why PNG Alone Is Not Enough",
        "",
    ]
    for item in summary["why_png_is_not_enough"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Witness Focus",
            "",
            f"### {case0012['case_id']}",
            "",
            f"- Family: `{case0012['family']}`",
            f"- Changed pixels: `{case0012['changed_pixel_count']}`",
            f"- Use: {case0012['expected_use']}",
            f"- Primary point A: `{case0012['primary_points'][0]}`",
            f"- Primary point B: `{case0012['primary_points'][1]}`",
            f"- Current reverted max witness: `{case0012['current_reverted_max_witness']}`",
            f"- Latest Windows runtime note: `{case0012['latest_windows_runtime_note']}`",
            "",
            f"### {case0016['case_id']}",
            "",
            f"- Family: `{case0016['family']}`",
            f"- Use: {case0016['expected_use']}",
            f"- Companion point(s): `{case0016['primary_points']}`",
            "",
            f"### {case0020['case_id']}",
            "",
            f"- Family: `{case0020['family']}`",
            f"- Changed pixels: `{case0020['changed_pixel_count']}`",
            f"- Use: {case0020['expected_use']}",
            f"- Control point A: `{case0020['primary_points'][0]}`",
            f"- Control point B: `{case0020['primary_points'][1]}`",
            "",
            "## Actionable Return Criteria",
            "",
        ]
    )
    for item in summary["return_is_actionable_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Actionable", ""])
    for item in summary["return_is_not_actionable_if"]:
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--representative-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdistancegradation_16bpc_representative_witnesses_20260629.json",
    )
    parser.add_argument(
        "--rejected-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.json",
    )
    parser.add_argument(
        "--runtime-package",
        type=Path,
        default=repo_root() / "refs" / "runtime_trace_packages" / "olm_runtime_trace_distancegradation_layer_no_bg_source_ownership_20260629.zip",
    )
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        default=(
            repo_root()
            / "refs"
            / "reports"
            / "runtime_trace_bundle"
            / "olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows"
            / "runtime_trace_summary_distancegradation_layer_no_bg_source_ownership_20260629_235638.json"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdistancegradation_pending_layer_source_proof_20260629.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmdistancegradation_pending_layer_source_proof_20260629.md",
    )
    args = parser.parse_args()

    summary = build_summary(
        load_json(args.representative_json),
        load_json(args.rejected_json),
        args.runtime_package,
        load_json(args.runtime_summary_json),
        args.runtime_summary_json,
    )
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
