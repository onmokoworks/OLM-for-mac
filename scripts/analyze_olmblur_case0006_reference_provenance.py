#!/usr/bin/env python3
"""Audit OLMBlur 16bpc case_0006 reference/export provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refs.scripts.verify_manifest import load_rgba, png_header


CANONICAL_REF = (
    ROOT
    / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
HANDOFF_EXPECTED = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/expected/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
MAC_SINGLE = (
    ROOT
    / "refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
MAC_BATCH = (
    ROOT
    / "refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/candidate/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
HANDOFF_RESULTS = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/results/bitdepth16_olmblur_exact/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
ARCHIVE_RESULTS = (
    ROOT
    / "handoff/archive/ae_pixel_validation_20260618_before_rerun_20260626_204944/results/bitdepth16_olmblur_exact/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
)
HANDOFF_RESULT_JSON = (
    ROOT / "handoff/ae_pixel_validation_20260618/results/bitdepth16_olmblur_exact/AE_PIXEL_VALIDATION_RENDER_RESULT.json"
)
ARCHIVE_RESULT_JSON = (
    ROOT
    / "handoff/archive/ae_pixel_validation_20260618_before_rerun_20260626_204944/results/bitdepth16_olmblur_exact/AE_PIXEL_VALIDATION_RENDER_RESULT.json"
)
OUT_JSON = ROOT / "refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.md"

POINTS = [
    (314, 14),
    (29, 71),
    (601, 598),
    (378, 487),
]


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-ref", type=Path, default=CANONICAL_REF)
    parser.add_argument("--handoff-expected", type=Path, default=HANDOFF_EXPECTED)
    parser.add_argument("--mac-single-export", type=Path, default=MAC_SINGLE)
    parser.add_argument("--mac-batch-export", type=Path, default=MAC_BATCH)
    parser.add_argument("--handoff-results-export", type=Path, default=HANDOFF_RESULTS)
    parser.add_argument("--archive-results-export", type=Path, default=ARCHIVE_RESULTS)
    parser.add_argument("--handoff-result-json", type=Path, default=HANDOFF_RESULT_JSON)
    parser.add_argument("--archive-result-json", type=Path, default=ARCHIVE_RESULT_JSON)
    parser.add_argument("--windows-current-export", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def file_info(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return {
            "path": display_path(path),
            "exists": False,
        }
    header = png_header(path)
    return {
        "path": display_path(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "png_header": header,
    }


def read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sample_points(path: Path) -> dict[str, list[int]]:
    rgba = load_rgba(path)
    values: dict[str, list[int]] = {}
    for x, y in POINTS:
        values[f"{x},{y}"] = [int(v) for v in rgba[y, x]]
    return values


def classify_point_roles(point_values: dict[str, dict[str, list[int]]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    canonical = point_values["canonical_ref"]
    single = point_values["mac_single_export"]
    batch = point_values["mac_batch_export"]
    for key in sorted(canonical):
        roles: list[str] = []
        if single[key] == canonical[key]:
            roles.append("mac_single_matches_canonical")
        if batch[key] == canonical[key]:
            roles.append("mac_batch_matches_canonical")
        if single[key] == batch[key]:
            roles.append("mac_single_matches_mac_batch")
        out[key] = {
            "canonical_ref": canonical[key],
            "mac_single_export": single[key],
            "mac_batch_export": batch[key],
            "match_roles": roles or ["all_split"],
            "single_minus_canonical": [int(a) - int(b) for a, b in zip(single[key], canonical[key])],
            "batch_minus_canonical": [int(a) - int(b) for a, b in zip(batch[key], canonical[key])],
        }
    return out


def classify_overall_point_pattern(point_roles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "mac_single_matches_canonical": 0,
        "mac_batch_matches_canonical": 0,
        "mac_single_matches_mac_batch": 0,
        "all_split": 0,
    }
    witness_pattern: dict[str, list[str]] = {}
    for key, row in point_roles.items():
        for role in row["match_roles"]:
            counts[role] = counts.get(role, 0) + 1
        if key in {"314,14", "29,71"}:
            witness_pattern[key] = row["match_roles"]
    return {
        "counts": counts,
        "witness_pattern": witness_pattern,
        "reading": (
            "No single export artifact dominates all sampled points: batch and single-case exports each match canonical "
            "at some points and disagree at others, while the original witness pair also splits by point."
        ),
    }


def classify_optional_windows_export(
    canonical: dict[str, Any],
    mac_single: dict[str, Any],
    mac_batch: dict[str, Any],
    windows_current: dict[str, Any] | None,
) -> dict[str, Any]:
    if not windows_current or not windows_current.get("exists"):
        return {
            "status": "current-aex-export-missing",
            "reason": (
                "No same-run Windows current-AEX exported PNG is present, so the lane remains "
                "a provenance/export question rather than a reopened implementation bug."
            ),
            "recommended_action": (
                "Keep OLMBlur case_0006 frozen on the Mac side and request only the precise "
                "same-run Windows current-AEX export artifact if this lane must advance."
            ),
        }

    win_sha = windows_current["sha256"]
    if win_sha == canonical["sha256"]:
        return {
            "status": "current-aex-export-matches-canonical-reference",
            "reason": "The same-run Windows current-AEX export is byte-identical to the canonical 2026-06-25 reference.",
            "recommended_action": "Audit Mac export/run provenance before reopening implementation.",
        }
    if win_sha == mac_single["sha256"]:
        return {
            "status": "current-aex-export-matches-mac-single-export",
            "reason": "The same-run Windows current-AEX export matches the Mac single-case export artifact instead of the canonical reference.",
            "recommended_action": "Reclassify case_0006 as a reference-generation/export split unless stronger contradictory witness evidence appears.",
        }
    if win_sha == mac_batch["sha256"]:
        return {
            "status": "current-aex-export-matches-mac-batch-export",
            "reason": "The same-run Windows current-AEX export matches the Mac batch export artifact instead of the canonical reference.",
            "recommended_action": "Reclassify case_0006 as a reference-generation/export split unless stronger contradictory witness evidence appears.",
        }
    return {
        "status": "current-aex-export-matches-neither-known-artifact",
        "reason": "The same-run Windows current-AEX export is distinct from the canonical reference and both known Mac export artifacts.",
        "recommended_action": "Keep the lane provenance-first and compare exact run metadata before any source change.",
    }


def build_alias_groups(files: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    by_sha: dict[str, list[str]] = {}
    for role, info in files.items():
        if not info or not info.get("exists"):
            continue
        by_sha.setdefault(info["sha256"], []).append(role)
    groups: list[dict[str, Any]] = []
    for sha, roles in sorted(by_sha.items(), key=lambda item: (len(item[1]) * -1, item[0])):
        first = files[roles[0]]
        groups.append(
            {
                "sha256": sha,
                "roles": sorted(roles),
                "bytes": first["bytes"],
                "paths": [files[role]["path"] for role in sorted(roles)],
            }
        )
    return groups


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur case_0006 Reference Provenance Audit",
        "",
        "- Scope: `OLMBlur` non-Legacy 16bpc `case_0006`",
        f"- Outcome: `{report['outcome']['status']}`",
        f"- Reason: {report['outcome']['reason']}",
        f"- Recommended action: {report['outcome']['recommended_action']}",
        "",
        "## File Identity",
        "",
        "| Role | Path | Bytes | SHA-256 |",
        "| --- | --- | ---: | --- |",
    ]
    for key in (
        "canonical_ref",
        "handoff_expected",
        "mac_single_export",
        "mac_batch_export",
        "handoff_results_export",
        "archive_results_export",
        "windows_current_export",
    ):
        info = report["files"].get(key)
        if not info:
            continue
        if not info.get("exists"):
            lines.append(f"| {key} | `{info['path']}` | - | missing |")
            continue
        lines.append(
            f"| {key} | `{info['path']}` | `{info['bytes']}` | `{info['sha256']}` |"
        )
    lines.extend(
        [
            "",
            f"- Canonical ref and handoff expected identical: `{report['canonical_vs_handoff_identical']}`",
            "",
            "## Alias Groups",
            "",
        ]
    )
    for group in report["alias_groups"]:
        lines.append(f"- `{group['roles']}` share SHA `{group['sha256']}` ({group['bytes']} bytes)")
    result_meta = report.get("result_metadata") or {}
    if result_meta:
        lines.extend(
            [
                "",
                "## Result Metadata",
                "",
            ]
        )
        for key in ("handoff_result_json", "archive_result_json"):
            meta = result_meta.get(key)
            if not meta:
                continue
            lines.append(
                f"- `{key}`: request_id=`{meta.get('request_id')}`, effect=`{meta.get('effect_name')}`, rendered_count=`{len(meta.get('rendered', []))}`, errors=`{meta.get('errors')}`"
            )
    lines.extend(
        [
            "",
            "## Witness Points",
            "",
            "| XY | canonical ref | Mac single export | Mac batch export | Windows current export |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    point_values = report["point_values"]
    for key in sorted(point_values["canonical_ref"]):
        lines.append(
            f"| `({key})` | `{point_values['canonical_ref'][key]}` | "
            f"`{point_values['mac_single_export'][key]}` | "
            f"`{point_values['mac_batch_export'][key]}` | "
            f"`{point_values.get('windows_current_export', {}).get(key, '-')}` |"
        )
    lines.extend(
        [
            "",
            "## Point-Role Matrix",
            "",
            "| XY | match roles | single-canonical | batch-canonical |",
            "| --- | --- | --- | --- |",
        ]
    )
    for key, row in report["point_role_matrix"].items():
        lines.append(
            f"| `({key})` | `{row['match_roles']}` | `{row['single_minus_canonical']}` | `{row['batch_minus_canonical']}` |"
        )
    lines.extend(
        [
            "",
            f"- overall counts: `{report['overall_point_pattern']['counts']}`",
            f"- witness pattern: `{report['overall_point_pattern']['witness_pattern']}`",
            f"- reading: {report['overall_point_pattern']['reading']}",
            "",
            "## Reading",
            "",
            "- The canonical Windows Software reference path is fixed if the canonical and handoff files are byte-identical.",
            "- If Windows and Mac internal witness values already agree, but exported PNG artifacts still split by path, treat the lane as provenance/export work until a same-run Windows current-AEX export exists.",
            "- Do not reopen `mac/OLMBlur/OLMBlur.cpp` from this lane alone.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    files = {
        "canonical_ref": file_info(args.canonical_ref),
        "handoff_expected": file_info(args.handoff_expected),
        "mac_single_export": file_info(args.mac_single_export),
        "mac_batch_export": file_info(args.mac_batch_export),
        "handoff_results_export": file_info(args.handoff_results_export),
        "archive_results_export": file_info(args.archive_results_export),
        "windows_current_export": file_info(args.windows_current_export),
    }
    point_values = {
        "canonical_ref": sample_points(args.canonical_ref),
        "handoff_expected": sample_points(args.handoff_expected),
        "mac_single_export": sample_points(args.mac_single_export),
        "mac_batch_export": sample_points(args.mac_batch_export),
    }
    if args.windows_current_export and args.windows_current_export.exists():
        point_values["windows_current_export"] = sample_points(args.windows_current_export)
    point_roles = classify_point_roles(point_values)

    report = {
        "kind": "olmblur_case0006_reference_provenance_audit",
        "schema": 1,
        "case_id": "olmblur__case_0006",
        "bit_depth": "16bpc",
        "files": files,
        "alias_groups": build_alias_groups(files),
        "result_metadata": {
            "handoff_result_json": read_optional_json(args.handoff_result_json),
            "archive_result_json": read_optional_json(args.archive_result_json),
        },
        "canonical_vs_handoff_identical": (
            files["canonical_ref"]["exists"]
            and files["handoff_expected"]["exists"]
            and files["canonical_ref"]["sha256"] == files["handoff_expected"]["sha256"]
        ),
        "point_values": point_values,
        "point_role_matrix": point_roles,
        "overall_point_pattern": classify_overall_point_pattern(point_roles),
        "outcome": classify_optional_windows_export(
            files["canonical_ref"],
            files["mac_single_export"],
            files["mac_batch_export"],
            files["windows_current_export"],
        ),
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"outcome={report['outcome']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
