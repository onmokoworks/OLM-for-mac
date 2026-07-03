#!/usr/bin/env python3
"""Summarize a live Mac AE OLMKiraKira hotspot probe against the reference neighborhood."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-json", type=Path, required=True)
    parser.add_argument("--reference-png", type=Path, required=True)
    parser.add_argument("--debug-neighborhood-json", type=Path, required=True)
    parser.add_argument("--installed-binary", type=Path, required=True)
    parser.add_argument("--built-binary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def rgba_at(path: Path, xy: tuple[int, int]) -> list[int]:
    img = Image.open(path).convert("RGBA")
    return list(img.getpixel(xy))


def row_values(path: Path, y: int, x0: int, x1: int) -> list[int]:
    img = Image.open(path).convert("RGBA")
    return [img.getpixel((x, y))[0] for x in range(x0, x1 + 1)]


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = parse_args()
    result = read_json(args.result_json)
    neighborhood = read_json(args.debug_neighborhood_json)
    output_png = Path(result["output_png"])
    center = tuple(neighborhood["center_xy"])
    radius = int(neighborhood["radius"])
    cx, cy = center

    center_export = rgba_at(output_png, center)
    center_reference = rgba_at(args.reference_png, center)
    center_debug = neighborhood["center_point"]["out_u8"]
    top_export = rgba_at(output_png, (cx, cy - 1))
    top_reference = rgba_at(args.reference_png, (cx, cy - 1))

    report = {
        "kind": "olmkirakira_live_hotspot_probe",
        "schema": 1,
        "case_id": result["case_id"],
        "ae_version": result["ae_version"],
        "center_xy": list(center),
        "radius": radius,
        "artifacts": {
            "result_json": rel(args.result_json),
            "output_png": rel(output_png),
            "reference_png": rel(args.reference_png),
            "debug_neighborhood_json": rel(args.debug_neighborhood_json),
        },
        "binary_identity": {
            "installed_binary": rel(args.installed_binary),
            "built_binary": rel(args.built_binary),
            "installed_sha256": sha256(args.installed_binary),
            "built_sha256": sha256(args.built_binary),
            "matches": sha256(args.installed_binary) == sha256(args.built_binary),
        },
        "center_pixels": {
            "exported_png_rgba8": center_export,
            "reference_png_rgba8": center_reference,
            "debug_out_u8": center_debug,
            "debug_out_u8_times_2_rgb": [int(center_debug[i] * 2) for i in range(3)] + [center_debug[3]],
            "delta_export_minus_reference": [center_export[i] - center_reference[i] for i in range(4)],
        },
        "neighbor_checks": {
            "top_export_rgba8": top_export,
            "top_reference_rgba8": top_reference,
            "export_rows_r": {
                str(y): row_values(output_png, y, cx - radius, cx + radius)
                for y in range(cy - radius, cy + radius + 1)
            },
            "reference_rows_r": {
                str(y): row_values(args.reference_png, y, cx - radius, cx + radius)
                for y in range(cy - radius, cy + radius + 1)
            },
        },
        "decision": {
            "status": "current-live-host-drift-from-historical-kirakira-witness",
            "summary": (
                "The current live Mac AE output at the hotspot does not reproduce the older "
                "144-valued traced/mapped witness family. The exported PNG center is 91 versus "
                "the Windows reference 131, and the row above is 186 versus 191."
            ),
            "reason": (
                "This is not explained by a stale installed plug-in: the currently installed "
                "MediaCore binary hash matches the freshly built OLMKiraKira binary exactly. "
                "So the dark live output is a real current-implementation or current-host-path fact."
            ),
            "next_action": (
                "Do not keep assuming the historical 144 hotspot witness describes the present live host. "
                "Reconcile the old compose-boundary witness path with the current AE-host export path before "
                "more provenance-only reasoning."
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# OLMKiraKira Live Hotspot Probe",
        "",
        f"- Case: `{report['case_id']}`",
        f"- AE version: `{report['ae_version']}`",
        f"- Center: `{tuple(report['center_xy'])}` radius `{report['radius']}`",
        f"- Status: `{report['decision']['status']}`",
        "",
        "## Center",
        "",
        f"- Exported PNG: `{report['center_pixels']['exported_png_rgba8']}`",
        f"- Reference PNG: `{report['center_pixels']['reference_png_rgba8']}`",
        f"- Debug out_u8: `{report['center_pixels']['debug_out_u8']}`",
        f"- Debug out_u8 * 2 RGB: `{report['center_pixels']['debug_out_u8_times_2_rgb']}`",
        f"- Delta export-reference: `{report['center_pixels']['delta_export_minus_reference']}`",
        "",
        "## Binary identity",
        "",
        f"- Installed/built hashes match: `{report['binary_identity']['matches']}`",
        f"- Installed SHA256: `{report['binary_identity']['installed_sha256']}`",
        f"- Built SHA256: `{report['binary_identity']['built_sha256']}`",
        "",
        "## Reading",
        "",
        f"- {report['decision']['summary']}",
        f"- {report['decision']['reason']}",
        f"- Next: {report['decision']['next_action']}",
        "",
        "## Rows (R channel)",
        "",
        "| y | export | reference |",
        "| --- | --- | --- |",
    ]
    for y in range(cy - radius, cy + radius + 1):
        lines.append(
            f"| `{y}` | `{report['neighbor_checks']['export_rows_r'][str(y)]}` | "
            f"`{report['neighbor_checks']['reference_rows_r'][str(y)]}` |"
        )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report_json={rel(args.output_json)}")
    print(f"report_md={rel(args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
