#!/usr/bin/env python3
"""Materialize the current OLMDistanceGradation case_0023 lane split."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THRESHOLD_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json"
SOURCE_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.json"
PROVENANCE_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.json"
BGOFF_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.json"
AEX_CPU_SIMU_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json"
COMPOSE_WITNESS_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_compose_witness_20260707.json"
SOURCE_MODEL_AUDIT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_source_model_audit_20260707.json"
REFERENCE_EXPORT_AUDIT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold-json", type=Path, default=THRESHOLD_JSON)
    parser.add_argument("--source-json", type=Path, default=SOURCE_JSON)
    parser.add_argument("--provenance-json", type=Path, default=PROVENANCE_JSON)
    parser.add_argument("--bgoff-json", type=Path, default=BGOFF_JSON)
    parser.add_argument("--aex-cpu-simu-json", type=Path, default=AEX_CPU_SIMU_JSON)
    parser.add_argument("--compose-witness-json", type=Path, default=COMPOSE_WITNESS_JSON)
    parser.add_argument("--source-model-audit-json", type=Path, default=SOURCE_MODEL_AUDIT_JSON)
    parser.add_argument("--reference-export-audit-json", type=Path, default=REFERENCE_EXPORT_AUDIT_JSON)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def normalize_reading(reading: list[str], reference_exact: bool) -> list[str]:
    if not reference_exact:
        return reading
    normalized = []
    for item in reading:
        normalized.append(
            item.replace(
                "matching current Mac-side field/debug behavior while the current Windows final endpoint "
                "remains the unresolved ownership split",
                (
                    "matching current Mac-side field/debug behavior. The current Windows Software export is "
                    "not stale, so this points at source/output ownership rather than reference drift"
                ),
            )
        )
    return normalized


def normalize_forbidden_actions(actions: list[str], reference_exact: bool) -> list[str]:
    if not reference_exact:
        return actions
    normalized = []
    for item in actions:
        if item == "Do not treat the packaged expected PNG as equivalent to current Windows output for the threshold-family slice without proof.":
            normalized.append(
                "Do not use the old packaged-stale explanation after the 2026-07-07 reference export audit proved packaged/current Windows exact."
            )
        else:
            normalized.append(item)
    return normalized


def build_report(
    threshold_data: dict[str, Any],
    source_data: dict[str, Any],
    provenance_data: dict[str, Any],
    bgoff_data: dict[str, Any],
    aex_cpu_simu_data: dict[str, Any],
    compose_witness_data: dict[str, Any] | None,
    source_model_audit_data: dict[str, Any] | None,
    reference_export_audit_data: dict[str, Any] | None,
    inputs: dict[str, Path],
) -> dict[str, Any]:
    residual = threshold_data["residual"]
    family_status = source_data["family_status"]
    threshold_triplet = provenance_data["threshold_triplet"]
    bg_witnesses = bgoff_data["witnesses"]

    edge_live = []
    edge_matching = []
    for witness in bg_witnesses:
        xy_value = witness.get("xy")
        xy = f"({xy_value[0]},{xy_value[1]})" if isinstance(xy_value, list) and len(xy_value) == 2 else str(xy_value)
        if witness.get("live_mac_rgba8") == witness.get("windows_bg_off_rgba8"):
            edge_matching.append(xy)
        else:
            edge_live.append(xy)

    reference_exact = bool(reference_export_audit_data.get("reference_exact")) if reference_export_audit_data else False
    safe_claim = (
        "Windows packaged/current references are exact for case_0023; threshold-family is no longer a "
        "packaged-stale lane in this worktree. Edge/source helper samples match, while the compose witness is "
        "now only a recorded field-to-color mapping check; the remaining work is Mac AE output/source ownership "
        "closeout without broad retuning."
        if reference_exact
        else (
            "Threshold-family is provenance/export-first; edge-family is narrowed to field/output-binding proof. "
            "The 2026-07-07 AEX CPU helper witness is not AE exact, but it makes a broad source retune unsafe."
        )
    )

    threshold_summary = (
        "The packaged 2026-06-25 16bpc Windows Software reference is byte-identical to the current-AEX "
        "Windows recaptures now in the worktree. Do not use the older packaged-stale explanation for this lane."
        if reference_exact
        else family_status["threshold_family"]["summary"]
    )
    threshold_next_action = (
        "Keep threshold-family out of implementation tuning; compare Mac AE output against the now-consistent "
        "Windows Software reference set and classify the residual by source/output ownership."
        if reference_exact
        else family_status["threshold_family"]["next_action"]
    )
    threshold_status = (
        "reference-export-exact-mac-source-output-live"
        if reference_exact
        else family_status["threshold_family"]["status"]
    )

    return {
        "kind": "olmdistancegradation_case0023_lane_state",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_id": threshold_data["case_id"],
        "inputs": {name: rel(path) for name, path in inputs.items()},
        "residual": {
            "total_px": residual["total_px"],
            "edge_bucket_px": residual["edge_bucket"]["count"],
            "threshold_bucket_px": residual["threshold_bucket"]["count"],
        },
        "threshold_family": {
            "status": threshold_status,
            "summary": threshold_summary,
            "next_action": threshold_next_action,
            "authoritative_request": source_data["provenance_reference_request"],
            "witness_triplet": threshold_triplet,
            "reference_export_audit": reference_export_audit_data,
        },
        "edge_family": {
            "status": family_status["edge_family"]["status"],
            "summary": family_status["edge_family"]["summary"],
            "next_action": "Keep binary-proof lane on field ownership / output binding; do not reopen threshold-family tuning from packaged PNG drift.",
            "authoritative_request": source_data["pending_windows_followup"],
            "live_bg_off_mismatches": edge_live,
            "matching_bg_off_neighbors": edge_matching,
            "aex_cpu_simu": {
                "status": aex_cpu_simu_data.get("status"),
                "kind": aex_cpu_simu_data.get("kind"),
                "inside_threshold": aex_cpu_simu_data.get("inside_threshold"),
                "outside_threshold": aex_cpu_simu_data.get("outside_threshold"),
                "combine": aex_cpu_simu_data.get("combine"),
                "reading": normalize_reading(aex_cpu_simu_data.get("reading", []), reference_exact),
                "samples": aex_cpu_simu_data.get("samples", []),
            },
            "compose_witness": compose_witness_data,
            "source_model_audit": source_model_audit_data,
        },
        "forbidden_actions": normalize_forbidden_actions(source_data["forbidden_actions"], reference_exact),
        "safe_claim": safe_claim,
    }


def render_markdown(report: dict[str, Any]) -> str:
    threshold = report["threshold_family"]
    edge = report["edge_family"]
    residual = report["residual"]
    lines = [
        f"# OLMDistanceGradation case_0023 Lane State - {report['materialized_at'][:10]}",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Residual split: total `{residual['total_px']}` px = edge `{residual['edge_bucket_px']}` + threshold `{residual['threshold_bucket_px']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## Threshold-family",
        "",
        f"- Status: `{threshold['status']}`",
        f"- Summary: {threshold['summary']}",
        f"- Next action: {threshold['next_action']}",
        f"- Authoritative request: `{threshold['authoritative_request']['request_id']}`",
        f"- Request JSON: `{threshold['authoritative_request']['request_json']}`",
        f"- Contract: `{threshold['authoritative_request']['contract']}`",
        "",
        "| XY | Live classification |",
        "| --- | --- |",
    ]
    for witness in threshold["witness_triplet"]:
        xy = witness.get("xy") or []
        field = witness.get("field_debug") or {}
        classification = (
            f"field_x={field.get('field_x')} raw_inside={field.get('raw_inside')}"
            if field
            else "typed witness"
        )
        lines.append(f"| `({xy[0]},{xy[1]})` | `{classification}` |")
    reference_audit = threshold.get("reference_export_audit")
    if reference_audit:
        lines.extend(
            [
                "",
                "### Reference Export Audit",
                "",
                f"- Reference exact: `{reference_audit.get('reference_exact')}`",
                f"- Safe claim: {reference_audit.get('safe_claim')}",
                "",
                "| Pair | Nonzero px | Max diff | Mean diff |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for name, comparison in reference_audit.get("comparisons", {}).items():
            lines.append(
                f"| `{name}` | `{comparison.get('nonzero_px', '')}` | "
                f"`{comparison.get('max_diff', '')}` | `{comparison.get('mean_diff', '')}` |"
            )
    lines.extend(
        [
            "",
            "## Edge-family",
            "",
            f"- Status: `{edge['status']}`",
            f"- Summary: {edge['summary']}",
            f"- Next action: {edge['next_action']}",
            f"- Historical runtime request: `{edge['authoritative_request']['request_id']}`",
            f"- Runtime request status: `{edge['authoritative_request'].get('status')}`",
            f"- Package: `{edge['authoritative_request']['package']}`",
            f"- Acceptance: `{edge['authoritative_request']['acceptance_note']}`",
            f"- Live bg_off mismatches: `{', '.join(edge['live_bg_off_mismatches'])}`",
            f"- Matching bg_off neighbors: `{', '.join(edge['matching_bg_off_neighbors'])}`",
            f"- AEX CPU simu status: `{edge['aex_cpu_simu']['status']}`",
            f"- AEX CPU simu combine: `{edge['aex_cpu_simu']['combine']}`",
            "",
            "### AEX CPU Simu Reading",
            "",
        ]
    )
    for item in edge["aex_cpu_simu"]["reading"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "| XY | Inside | Outside | Both-add field |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for sample in edge["aex_cpu_simu"]["samples"]:
        xy = sample.get("xy") or []
        if not isinstance(xy, list) or len(xy) != 2:
            continue
        lines.append(
            f"| `({xy[0]},{xy[1]})` | `{sample.get('inside_field')}` | "
            f"`{sample.get('outside_field')}` | `{sample.get('both_add_saturate_field')}` |"
        )
    compose = edge.get("compose_witness")
    if compose:
        lines.extend(
            [
                "",
                "### Compose/Writeback Witness",
                "",
                f"- Status: `{compose.get('status')}`",
                f"- Source: `{compose.get('source')}`",
                f"- Function: `{compose.get('function')}`",
                f"- Promotion rule: `{compose.get('promotion_rule')}`",
                f"- Safe claim: {compose.get('safe_claim')}",
                "",
                "| XY | field_x | promoted RGBA16 | recorded RGBA16 | match |",
                "| --- | ---: | --- | --- | ---: |",
            ]
        )
        for row in compose.get("triplet", []):
            xy = row.get("xy") or []
            if not isinstance(xy, list) or len(xy) != 2:
                continue
            lines.append(
                f"| `({xy[0]},{xy[1]})` | `{row.get('field_x')}` | "
                f"`{row.get('promoted_rgba')}` | `{row.get('windows_final_rgba16')}` | "
                f"`{row.get('match_promoted')}` |"
            )
    source_model = edge.get("source_model_audit")
    if source_model:
        lines.extend(
            [
                "",
                "### Mac Source Model Audit",
                "",
                f"- Status: `{source_model.get('status')}`",
                f"- Source: `{source_model.get('source')}`",
                f"- Safe claim: {source_model.get('safe_claim')}",
                "",
                "| XY | Mac both | AEX both | match |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for row in source_model.get("samples", []):
            xy = row.get("xy") or []
            if not isinstance(xy, list) or len(xy) != 2:
                continue
            mac = row.get("mac_source_model") or {}
            aex = row.get("aex_cpu_helper") or {}
            lines.append(
                f"| `({xy[0]},{xy[1]})` | `{mac.get('both_add_saturate_field')}` | "
                f"`{aex.get('both_add_saturate_field')}` | `{row.get('match')}` |"
            )
    lines.extend(
        [
            "",
            "## Forbidden",
            "",
        ]
    )
    for item in report["forbidden_actions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Inputs",
            "",
        ]
    )
    for name, path in report["inputs"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    inputs = {
        "threshold_json": args.threshold_json.resolve(),
        "source_json": args.source_json.resolve(),
        "provenance_json": args.provenance_json.resolve(),
        "bgoff_json": args.bgoff_json.resolve(),
        "aex_cpu_simu_json": args.aex_cpu_simu_json.resolve(),
    }
    for path in inputs.values():
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
    compose_witness = None
    compose_path = args.compose_witness_json.resolve()
    if compose_path.exists():
        inputs["compose_witness_json"] = compose_path
        compose_witness = load_json(compose_path)
    source_model_audit = None
    source_model_path = args.source_model_audit_json.resolve()
    if source_model_path.exists():
        inputs["source_model_audit_json"] = source_model_path
        source_model_audit = load_json(source_model_path)
    reference_export_audit = None
    reference_export_path = args.reference_export_audit_json.resolve()
    if reference_export_path.exists():
        inputs["reference_export_audit_json"] = reference_export_path
        reference_export_audit = load_json(reference_export_path)

    report = build_report(
        load_json(inputs["threshold_json"]),
        load_json(inputs["source_json"]),
        load_json(inputs["provenance_json"]),
        load_json(inputs["bgoff_json"]),
        load_json(inputs["aex_cpu_simu_json"]),
        compose_witness,
        source_model_audit,
        reference_export_audit,
        inputs,
    )
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_lane_state_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_lane_state_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
