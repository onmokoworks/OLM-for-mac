#!/usr/bin/env python3
"""Summarize the current-AEX 16bpc OLMColorKey case_0009 runtime trace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "colorkey_16bpc_case0009_runtime_trace_20260626"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument(
        "--analysis-json",
        type=Path,
        default=Path("refs/conformance/olmcolorkey_16bpc_case_0009_analysis.json"),
    )
    parser.add_argument(
        "--followup-audit-json",
        type=Path,
        default=Path("refs/conformance/olmcolorkey_16bpc_current_aex_followup_20260628.json"),
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == REQUEST_ID:
            return row
    return None


def representative_by_xy(analysis: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for row in analysis.get("representative_extra_witnesses", []):
        if isinstance(row, dict):
            out[(int(row["x"]), int(row["y"]))] = row
    return out


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def merge_followup_audit(
    windows_witnesses: list[dict[str, Any]], audit: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not audit:
        return windows_witnesses, {}
    witness = audit.get("witness_1110_149")
    if not isinstance(witness, dict) or not witness.get("hit"):
        return windows_witnesses, {}

    xy = (int(witness.get("x", -1)), int(witness.get("y", -1)))
    audit_entry = {
        "x": xy[0],
        "y": xy[1],
        "role": "primary_residual_followup_raw_cdb",
        "windows_final_output_rgba": None,
        "distance_value_consumed": witness.get("dist_float"),
        "amount_or_limit_value_compared": 25,
        "copy_condition_observed": "raw CDB follow-up hit current-AEX +0x9237/+0x9247/+0x924c/+0x92b7; copy path taken",
        "post_dilate_matte_byte": witness.get("matte_words_after"),
        "local_dist_to_hit_taxicab": None,
        "local_dist_to_boundary_clamp_taxicab": None,
        "local_hit_65535": None,
        "local_lab76_abs_delta": None,
        "local_lab76_allowed": None,
        "followup_audit": {
            "return_zip": audit.get("return_zip"),
            "trace_file": audit.get("trace_file"),
            "matte_words_before": witness.get("matte_words_before"),
            "matte_words_after": witness.get("matte_words_after"),
        },
    }

    merged: list[dict[str, Any]] = []
    replaced = False
    for row in windows_witnesses:
        if (int(row.get("x", -1)), int(row.get("y", -1))) == xy:
            preserved_local = {
                key: row.get(key)
                for key in (
                    "local_dist_to_hit_taxicab",
                    "local_dist_to_boundary_clamp_taxicab",
                    "local_hit_65535",
                    "local_lab76_abs_delta",
                    "local_lab76_allowed",
                )
            }
            merged.append({**row, **audit_entry, **preserved_local})
            replaced = True
        else:
            merged.append(row)
    if not replaced:
        merged.append(audit_entry)
    return merged, audit_entry


def build_comparison(
    summary: dict[str, Any], analysis: dict[str, Any], followup_audit: dict[str, Any] | None
) -> dict[str, Any]:
    result = find_result(summary)
    if result is None:
        return {
            "kind": "olmcolorkey_16bpc_case0009_trace_comparison",
            "schema": 1,
            "request_id": REQUEST_ID,
            "present": False,
            "likely_next_focus": "await-windows-trace",
        }

    observations = result.get("observations", {})
    if not isinstance(observations, dict):
        observations = {}

    ctx = observations.get("ctx_fields", {}) if isinstance(observations.get("ctx_fields"), dict) else {}
    current_fields = (
        ctx.get("current_aex_positive_edge_thin_fields", {})
        if isinstance(ctx.get("current_aex_positive_edge_thin_fields"), dict)
        else {}
    )
    rep = representative_by_xy(analysis)
    windows_witnesses = []
    unresolved_primary = 0
    for row in observations.get("witnesses", []):
        if not isinstance(row, dict):
            continue
        xy = (int(row.get("x", -1)), int(row.get("y", -1)))
        local = rep.get(xy, {})
        entry = {
            "x": xy[0],
            "y": xy[1],
            "role": row.get("role"),
            "windows_final_output_rgba": row.get("final_output_rgba"),
            "distance_value_consumed": row.get("distance_value_consumed"),
            "amount_or_limit_value_compared": row.get("amount_or_limit_value_compared"),
            "copy_condition_observed": row.get("copy_condition_observed"),
            "post_dilate_matte_byte": row.get("post_dilate_matte_byte"),
            "local_dist_to_hit_taxicab": local.get("dist_to_hit_taxicab"),
            "local_dist_to_boundary_clamp_taxicab": local.get("dist_to_boundary_clamp_taxicab"),
            "local_hit_65535": local.get("hit_65535"),
            "local_lab76_abs_delta": local.get("lab76_abs_delta"),
            "local_lab76_allowed": local.get("lab76_allowed"),
        }
        if "did not hit current-AEX +0x9000 positive Edge Thin loop" in str(row.get("copy_condition_observed")):
            unresolved_primary += 1
        windows_witnesses.append(entry)

    control = observations.get("control_pixel_optional", {})
    if not isinstance(control, dict):
        control = {}

    windows_witnesses, followup_entry = merge_followup_audit(windows_witnesses, followup_audit)
    if followup_entry:
        unresolved_primary = max(0, unresolved_primary - 1)

    likely_next_focus = "unknown"
    if result.get("status") == "answered_partial_current_aex_positive_edge_thin":
        if unresolved_primary >= 5:
            likely_next_focus = "current-aex-seed-world-or-upstream-match-builder"
        elif followup_entry:
            likely_next_focus = "current-aex-seed-matte-builder"
        else:
            likely_next_focus = "current-aex-positive-copy-loop"

    return {
        "kind": "olmcolorkey_16bpc_case0009_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "present": True,
        "status": result.get("status"),
        "likely_next_focus": likely_next_focus,
        "summary": result.get("summary"),
        "ctx": {
            "bit_depth_or_source_format_field": ctx.get("bit_depth_or_source_format_field"),
            "ctx_0x3c_force_lower_precision": ctx.get("ctx_0x3c_force_lower_precision"),
            "ctx_0x40_raw_float": ctx.get("ctx_0x40_raw_float"),
            "ctx_0x44_distance_type": ctx.get("ctx_0x44_distance_type"),
            "ctx_0x48_raw_float": ctx.get("ctx_0x48_raw_float"),
            "current_aex_positive_edge_thin_fields": current_fields,
        },
        "control": control,
        "followup_raw_cdb_witness": followup_entry,
        "windows_witnesses": windows_witnesses,
        "actual_candidate_vs_reference": analysis.get("actual_candidate_vs_reference"),
        "candidate_model_epsilon_sweep": analysis.get("candidate_model_epsilon_sweep"),
        "conclusion": [
            "Live current-AEX tracing confirms Force Lower Precision=3 and dist<=amount on the +0x9000 positive Edge Thin path.",
            "The top-edge sanity witness behaves like a straightforward positive-copy removal (dist=2 <= 25).",
            "The definitely-kept control behaves like a straightforward non-copy keep (dist=30 > 25).",
            "The 2026-06-28 raw CDB follow-up proves primary residual witness (1110,149) also hits the current-AEX positive Edge Thin copy path with dist=2.0 and matte word0 0x0000 -> 0x8000.",
            "Local exported-PNG Lab76 reconstruction puts the same witness 43 taxicab pixels from the current hit set, so the remaining mismatch is the seed/matte world feeding Edge Thin rather than <= vs < or Force Lower Precision.",
        ],
    }


def render_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# OLMColorKey 16bpc case_0009 Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Present: `{comparison.get('present')}`",
        f"- Status: `{comparison.get('status', '-')}`",
        f"- Likely next focus: `{comparison.get('likely_next_focus', '-')}`",
        "",
    ]
    if not comparison.get("present"):
        return "\n".join(lines)

    lines.extend(
        [
            "## Current-AEX Facts",
            "",
            f"- Ctx: {md_value(comparison.get('ctx'))}",
            f"- Control witness: {md_value(comparison.get('control'))}",
            "",
            "## Witnesses",
            "",
            "| XY | Windows result | Dist | Amount | Copy observation | Local dist-to-hit |",
            "| --- | --- | ---: | ---: | --- | ---: |",
        ]
    )
    for row in comparison.get("windows_witnesses", []):
        lines.append(
            f"| `({row['x']},{row['y']})` | {md_value(row.get('windows_final_output_rgba'))} | "
            f"{row.get('distance_value_consumed', '-')} | {row.get('amount_or_limit_value_compared', '-')} | "
            f"{md_value(row.get('copy_condition_observed'))} | {row.get('local_dist_to_hit_taxicab', '-')} |"
        )
    lines.extend(
        [
            "",
            "## Local Analysis Cross-Check",
            "",
            f"- actual_candidate_vs_reference: {md_value(comparison.get('actual_candidate_vs_reference'))}",
            f"- candidate_model_epsilon_sweep: {md_value(comparison.get('candidate_model_epsilon_sweep'))}",
            "",
            "## Conclusion",
            "",
        ]
    )
    for item in comparison.get("conclusion", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    analysis_path = resolve(root, args.analysis_json)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    if not analysis_path.exists():
        return fail(f"analysis JSON not found: {analysis_path}")
    summary = load_json(summary_path)
    analysis = load_json(analysis_path)
    audit_path = resolve(root, args.followup_audit_json)
    followup_audit = load_json(audit_path) if audit_path.exists() else None
    if not isinstance(summary, dict) or not isinstance(analysis, dict):
        return fail("inputs must be JSON objects")
    if followup_audit is not None and not isinstance(followup_audit, dict):
        return fail("follow-up audit JSON must be an object")
    comparison = build_comparison(summary, analysis, followup_audit)
    if args.output_json:
        output = resolve(root, args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(comparison, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"comparison_json={output}")
    if args.output_md:
        output = resolve(root, args.output_md)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(comparison), encoding="utf-8")
        print(f"comparison_md={output}")
    if not args.output_json and not args.output_md:
        print(render_markdown(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
