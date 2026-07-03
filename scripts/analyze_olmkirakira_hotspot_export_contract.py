#!/usr/bin/env python3
"""Freeze the OLMKiraKira hotspot export/provenance contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]

REFERENCE_PNG = (
    ROOT
    / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/reference/"
    / "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
)
CANDIDATE_PNG = (
    ROOT
    / "refs/reports/olmkirakira_remeasure_20260624_bt709_software/candidate/"
    / "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
)
MAC_WITNESS_JSON = ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"
WINDOWS_COMPARE_JSON = (
    ROOT / "refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json"
)
OUT_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md"

CASE_ID = "kk_vertical_len50_brightness1_strength100"
HOTSPOT = (934, 118)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-png", type=Path, default=REFERENCE_PNG)
    parser.add_argument("--candidate-png", type=Path, default=CANDIDATE_PNG)
    parser.add_argument("--mac-witness-json", type=Path, default=MAC_WITNESS_JSON)
    parser.add_argument("--windows-compare-json", type=Path, default=WINDOWS_COMPARE_JSON)
    parser.add_argument("--windows-current-export", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def rel(path: Path | None) -> str | None:
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rgba(path: Path, xy: tuple[int, int]) -> list[int]:
    with Image.open(path).convert("RGBA") as image:
        return [int(v) for v in image.getpixel(xy)]


def file_info(path: Path | None, xy: tuple[int, int] | None = None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return {"path": rel(path), "exists": False}
    info: dict[str, Any] = {
        "path": rel(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if xy is not None:
        info["hotspot_rgba"] = read_rgba(path, xy)
    return info


def windows_hotspot(compare: dict[str, Any]) -> dict[str, Any]:
    for row in compare["windows"]["merge_mode_1_compose"]["sample_inputs_outputs"]:
        if row["label"] == "hotspot":
            return row
    raise KeyError("missing hotspot compose witness")


def classify(
    reference_info: dict[str, Any],
    candidate_info: dict[str, Any],
    windows_traced_rgba: list[int],
    windows_current_export_info: dict[str, Any] | None,
) -> dict[str, Any]:
    if not windows_current_export_info or not windows_current_export_info.get("exists"):
        return {
            "status": "awaiting-same-run-export-or-witness-placement-proof",
            "family": "pending",
            "reason": (
                "The traced hotspot already agrees with the current Mac compose-boundary witness at 144, "
                "while the canonical reference PNG is 131. Without a same-run Windows export or explicit "
                "witness-placement/endgame-control proof, this remains a provenance lane."
            ),
            "next_step": (
                "Import a same-run Windows current-AEX export for the hotspot case, or a proof artifact that "
                "shows the traced hotspot is not the final export class."
            ),
        }

    current_rgba = windows_current_export_info["hotspot_rgba"]
    if current_rgba == windows_traced_rgba:
        return {
            "status": "outcome-a-export-matches-traced-hotspot",
            "family": "A",
            "reason": (
                "The same-run Windows export matches the traced hotspot class at 144, so the canonical 131 "
                "reference is not the same export class for this lane."
            ),
            "next_step": "Reclassify the lane as reference-generation or witness-placement drift; keep source frozen.",
        }
    if current_rgba == reference_info["hotspot_rgba"]:
        return {
            "status": "outcome-b-export-matches-canonical-reference",
            "family": "B",
            "reason": (
                "The same-run Windows export matches the canonical 131 reference instead of the traced 144 hotspot."
            ),
            "next_step": (
                "Treat the traced hotspot as an incomplete observation of the final export path and seek witness "
                "placement or endgame-control coverage before changing source."
            ),
        }
    if current_rgba == candidate_info["hotspot_rgba"]:
        return {
            "status": "outcome-c-export-matches-archived-bt709-candidate",
            "family": "C",
            "reason": (
                "The same-run Windows export matches the archived 145 candidate rather than the traced hotspot or "
                "canonical reference."
            ),
            "next_step": "Keep the lane provenance-first and compare exact export metadata before any source change.",
        }
    return {
        "status": "outcome-d-export-matches-neither-known-hotspot-class",
        "family": "D",
        "reason": (
            "The same-run Windows export is distinct from the canonical 131 reference, traced 144 hotspot, and "
            "archived 145 candidate."
        ),
        "next_step": "Keep the lane provenance-first and collect exact export metadata or endgame-control witness coverage.",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    mac_witness = read_json(args.mac_witness_json)["points"]["934,118"]
    compare = read_json(args.windows_compare_json)
    traced = windows_hotspot(compare)

    reference_info = file_info(args.reference_png, HOTSPOT)
    candidate_info = file_info(args.candidate_png, HOTSPOT)
    windows_current_export_info = file_info(args.windows_current_export, HOTSPOT)

    traced_rgba = list(traced["final_writeback_or_png_rgba"])
    mac_rgba = list(mac_witness["out_u8"])

    return {
        "kind": "olmkirakira_hotspot_export_contract_audit",
        "schema": 1,
        "plugin": "OLMKiraKira",
        "case_id": CASE_ID,
        "hotspot_xy": [HOTSPOT[0], HOTSPOT[1]],
        "artifacts": {
            "canonical_reference_png": reference_info,
            "archived_bt709_candidate_png": candidate_info,
            "current_mac_compose_witness": {
                "path": rel(args.mac_witness_json),
                "hotspot_rgba": mac_rgba,
                "compose_rgba_float": mac_witness["out_prequantized_rgba_float"],
            },
            "windows_traced_hotspot": {
                "path": rel(args.windows_compare_json),
                "hotspot_rgba": traced_rgba,
                "compose_rgba_float": traced["composed_rgba_float"],
                "glow_after_opacity_rgba_float": traced["glow_after_opacity_rgba_float"],
            },
            "windows_current_export": windows_current_export_info,
        },
        "required_windows_payload": [
            "same-run exported PNG file for the hotspot case",
            "AE version",
            "project renderer metadata",
            "parameter/property snapshot for the same case",
            "statement whether the export comes from the same current-AEX build/path as the trace run",
            "if export and trace differ, any witness-placement or endgame-control note explaining the split",
        ],
        "decision": classify(reference_info, candidate_info, traced_rgba, windows_current_export_info),
        "forbidden_moves": [
            "retune BT.709 seed",
            "retune boxFilter or ray-helper choreography from hotspot PNGs",
            "promote a broad compose or final-quantization rewrite from the canonical 131 mismatch alone",
            "treat missing endgame controls as proof that hotspot compose math is wrong",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    art = report["artifacts"]
    decision = report["decision"]
    lines = [
        "# OLMKiraKira Hotspot Export Contract Audit",
        "",
        f"- Plug-in: `{report['plugin']}`",
        f"- Case: `{report['case_id']}`",
        f"- Hotspot: `{tuple(report['hotspot_xy'])}`",
        f"- Decision: `{decision['status']}`",
        f"- Reason: {decision['reason']}",
        f"- Next step: {decision['next_step']}",
        "",
        "## Artifact Hotspot Values",
        "",
        f"- canonical Windows reference PNG: `{art['canonical_reference_png']['hotspot_rgba']}`",
        f"- archived BT.709 candidate PNG: `{art['archived_bt709_candidate_png']['hotspot_rgba']}`",
        f"- current Mac compose-boundary witness: `{art['current_mac_compose_witness']['hotspot_rgba']}`",
        f"- answered Windows traced hotspot: `{art['windows_traced_hotspot']['hotspot_rgba']}`",
        f"- same-run Windows current export: `{art['windows_current_export']['hotspot_rgba'] if art['windows_current_export'] and art['windows_current_export'].get('exists') else '-'}`",
        "",
        "## Required Windows Payload",
        "",
    ]
    for item in report["required_windows_payload"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Moves", ""])
    for item in report["forbidden_moves"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


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
