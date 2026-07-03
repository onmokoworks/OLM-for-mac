#!/usr/bin/env python3
"""Freeze the OLMBlur case_0006 current-AEX export contract as a machine audit."""

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
OUT_JSON = ROOT / "refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md"

POINTS = [
    (314, 14, "lane-defining witness A"),
    (29, 71, "lane-defining witness B"),
    (601, 598, "batch-aligned support point"),
    (378, 487, "single-case-aligned support point"),
]

PARAMETERS = {
    "Blur Amount": 5,
    "Blur Smoothness": 100,
    "Number of Repeat": 10,
    "Bias Direction": 1,
    "Legacy": 0,
}


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


def file_info(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return {"path": display_path(path), "exists": False}
    return {
        "path": display_path(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "png_header": png_header(path),
    }


def sample_points(path: Path) -> dict[str, list[int]]:
    rgba = load_rgba(path)
    values: dict[str, list[int]] = {}
    for x, y, _reason in POINTS:
        values[f"{x},{y}"] = [int(v) for v in rgba[y, x]]
    return values


def classify_outcome(
    canonical_info: dict[str, Any],
    mac_single_info: dict[str, Any],
    mac_batch_info: dict[str, Any],
    windows_info: dict[str, Any] | None,
) -> dict[str, Any]:
    if not windows_info or not windows_info.get("exists"):
        return {
            "status": "awaiting-windows-current-aex-export",
            "outcome_family": "pending",
            "reason": (
                "No same-run Windows current-AEX export has been imported yet, so the contract remains "
                "a provenance gate rather than a source-change signal."
            ),
            "next_step": (
                "Import the Windows current-AEX export PNG from the same run class as the witness capture "
                "and rerun this audit."
            ),
        }

    win_sha = windows_info["sha256"]
    if win_sha == canonical_info["sha256"]:
        return {
            "status": "outcome-a-current-aex-matches-canonical",
            "outcome_family": "A",
            "reason": (
                "The imported Windows current-AEX export is byte-identical to the canonical 2026-06-25 "
                "Windows Software reference."
            ),
            "next_step": "Audit Mac export/run provenance before reopening implementation.",
        }
    if win_sha == mac_single_info["sha256"]:
        return {
            "status": "outcome-b-current-aex-matches-mac-single",
            "outcome_family": "B",
            "reason": (
                "The imported Windows current-AEX export matches the tracked Mac single-case export instead "
                "of the canonical reference."
            ),
            "next_step": "Reclassify case_0006 as a reference-generation/export split; keep source frozen.",
        }
    if win_sha == mac_batch_info["sha256"]:
        return {
            "status": "outcome-b-current-aex-matches-mac-batch",
            "outcome_family": "B",
            "reason": (
                "The imported Windows current-AEX export matches the tracked Mac batch export instead of "
                "the canonical reference."
            ),
            "next_step": "Reclassify case_0006 as a reference-generation/export split; keep source frozen.",
        }
    return {
        "status": "outcome-c-current-aex-matches-neither-known-artifact",
        "outcome_family": "C",
        "reason": (
            "The imported Windows current-AEX export is distinct from the canonical reference and both "
            "tracked Mac export classes."
        ),
        "next_step": "Keep the lane provenance-first and compare exact run metadata before any source change.",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    canonical_info = file_info(args.canonical_ref)
    mac_single_info = file_info(args.mac_single_export)
    mac_batch_info = file_info(args.mac_batch_export)
    windows_info = file_info(args.windows_current_export)

    point_values = {
        "canonical_ref": sample_points(args.canonical_ref),
        "mac_single_export": sample_points(args.mac_single_export),
        "mac_batch_export": sample_points(args.mac_batch_export),
    }
    if args.windows_current_export and args.windows_current_export.exists():
        point_values["windows_current_export"] = sample_points(args.windows_current_export)

    point_rows = []
    for x, y, why in POINTS:
        key = f"{x},{y}"
        row = {
            "xy": [x, y],
            "reason": why,
            "canonical_ref": point_values["canonical_ref"][key],
            "mac_single_export": point_values["mac_single_export"][key],
            "mac_batch_export": point_values["mac_batch_export"][key],
        }
        if "windows_current_export" in point_values:
            row["windows_current_export"] = point_values["windows_current_export"][key]
        point_rows.append(row)

    return {
        "kind": "olmblur_case0006_current_aex_export_contract_audit",
        "schema": 1,
        "plugin": "OLMBlur",
        "case_id": "olmblur__case_0006",
        "bit_depth": "16bpc",
        "renderer": "SOFTWARE",
        "parameters": PARAMETERS,
        "files": {
            "canonical_ref": canonical_info,
            "mac_single_export": mac_single_info,
            "mac_batch_export": mac_batch_info,
            "windows_current_export": windows_info,
        },
        "required_windows_payload": [
            "exported PNG file",
            "AE version",
            "project renderer metadata",
            "bit depth metadata",
            "parameter/property snapshot for the same slice",
            "statement whether the PNG came from the same current-AEX build/path and same render class as the witness run",
        ],
        "witness_points": point_rows,
        "decision": classify_outcome(canonical_info, mac_single_info, mac_batch_info, windows_info),
        "forbidden_moves": [
            "global 16bpc writer swap",
            "helper surgery from case_0006 alone",
            "treat canonical reference as equivalent to current-AEX export without proof",
            "collapse case_0006 into case_0007 Legacy work",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    files = report["files"]
    decision = report["decision"]
    lines = [
        "# OLMBlur case_0006 Current-AEX Export Contract Audit",
        "",
        f"- Plug-in: `{report['plugin']}`",
        f"- Case: `{report['case_id']}`",
        f"- Bit depth: `{report['bit_depth']}`",
        f"- Renderer: `{report['renderer']}`",
        f"- Decision: `{decision['status']}`",
        f"- Reason: {decision['reason']}",
        f"- Next step: {decision['next_step']}",
        "",
        "## Parameters",
        "",
    ]
    for key, value in report["parameters"].items():
        lines.append(f"- `{key}={value}`")

    lines.extend(
        [
            "",
            "## File Identity",
            "",
            "| Role | Path | Bytes | SHA-256 |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for role in ("canonical_ref", "mac_single_export", "mac_batch_export", "windows_current_export"):
        info = files.get(role)
        if not info:
            continue
        lines.append(
            f"| {role} | `{info['path']}` | `{info.get('bytes', '-')}` | `{info.get('sha256', '-')}` |"
        )

    lines.extend(
        [
            "",
            "## Required Windows Payload",
            "",
        ]
    )
    for item in report["required_windows_payload"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Witness Points",
            "",
            "| XY | Reason | canonical ref | Mac single | Mac batch | Windows current export |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["witness_points"]:
        windows = row.get("windows_current_export", "-")
        lines.append(
            f"| `{tuple(row['xy'])}` | {row['reason']} | `{row['canonical_ref']}` | "
            f"`{row['mac_single_export']}` | `{row['mac_batch_export']}` | `{windows}` |"
        )

    lines.extend(
        [
            "",
            "## Forbidden Moves",
            "",
        ]
    )
    for item in report["forbidden_moves"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-ref", type=Path, default=CANONICAL_REF)
    parser.add_argument("--mac-single-export", type=Path, default=MAC_SINGLE)
    parser.add_argument("--mac-batch-export", type=Path, default=MAC_BATCH)
    parser.add_argument("--windows-current-export", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
