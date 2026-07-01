#!/usr/bin/env python3
"""Bounded caller-collapse / validity-plane diagnostic for OLMRadialBlur.

This keeps the existing core algorithm untouched and only widens the witness:
one witness dump now carries a tiny same-row plane probe around the target
pixel so we can compare final inverse-sampled output against the local
preserved-validity proxy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_caller_collapse_plane_diag_20260701.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_caller_collapse_plane_diag_20260701.md"
CLI = ROOT / "cli" / "OLMRadialBlur" / "olmradialblur_cli"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def load_rgba_row(path: Path, y: int, x0: int, x1: int) -> list[list[int]]:
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    if y < 0 or y >= height:
        raise ValueError(f"row {y} outside image height {height}")
    return [list(image.getpixel((x, y))) for x in range(max(0, x0), min(width - 1, x1) + 1)]


def summarize_probe(probe: dict[str, Any], candidate_png: Path, reference_png: Path) -> dict[str, Any]:
    points = probe["row_probe"]
    if not points:
        raise ValueError("row_probe is empty")
    xs = [int(point["xy"][0]) for point in points]
    y = int(points[0]["xy"][1])
    x0 = min(xs)
    x1 = max(xs)
    candidate_row = load_rgba_row(candidate_png, y, x0, x1)
    reference_row = load_rgba_row(reference_png, y, x0, x1)

    row = []
    max_alpha_valid_gap = None
    max_rgb_ref_gap = None
    for idx, point in enumerate(points):
        sample_u8 = [int(v) for v in point["sample_u8"]]
        ref_u8 = reference_row[idx]
        cand_u8 = candidate_row[idx]
        alpha_u8 = int(point["alpha_u8"])
        validity_alpha_u8 = int(point["validity_alpha_u8"])
        alpha_valid_gap = alpha_u8 - validity_alpha_u8
        rgb_ref_gap = [cand_u8[c] - ref_u8[c] for c in range(3)]
        entry = {
            "x": int(point["xy"][0]),
            "y": y,
            "sample_u8": sample_u8,
            "candidate_u8": cand_u8,
            "reference_u8": ref_u8,
            "candidate_minus_reference_u8": [cand_u8[c] - ref_u8[c] for c in range(4)],
            "alpha_u8": alpha_u8,
            "validity_alpha_u8": validity_alpha_u8,
            "alpha_minus_validity_alpha_u8": alpha_valid_gap,
            "cell_valid": [float(v) for v in point["cell_valid"]],
            "cell_alpha": [float(v) for v in point["cell_alpha"]],
            "sample_rgba": [float(v) for v in point["sample_rgba"]],
        }
        row.append(entry)
        if max_alpha_valid_gap is None or alpha_valid_gap > max_alpha_valid_gap["gap"]:
            max_alpha_valid_gap = {"x": entry["x"], "gap": alpha_valid_gap}
        rgb_gap_mag = max(abs(v) for v in rgb_ref_gap)
        if max_rgb_ref_gap is None or rgb_gap_mag > max_rgb_ref_gap["mag"]:
            max_rgb_ref_gap = {"x": entry["x"], "mag": rgb_gap_mag, "delta": rgb_ref_gap}

    return {
        "row_y": y,
        "x_range": [x0, x1],
        "row": row,
        "max_alpha_validity_gap": max_alpha_valid_gap,
        "max_rgb_reference_gap": max_rgb_ref_gap,
    }


def capture_case(case_id: str, smoke_script: str, witness_x: int, witness_y: int, run_dir: Path) -> dict[str, Any]:
    run(["python3", smoke_script])
    before = run_dir / "reference" / f"{case_id}_before_effects.png"
    reference = run_dir / "reference" / f"{case_id}.png"
    params = run_dir / "candidate" / "_params" / f"{case_id}.json"
    output = run_dir / "candidate" / f"{case_id}_caller_collapse_plane.png"
    witness_json = run_dir / "candidate" / f"{case_id}_caller_collapse_plane.json"
    run(
        [
            str(CLI),
            "--input",
            str(before),
            "--params",
            str(params),
            "--output",
            str(output),
            "--witness-dump",
            str(witness_json),
            "--witness-x",
            str(witness_x),
            "--witness-y",
            str(witness_y),
        ]
    )
    probe = json.loads(witness_json.read_text(encoding="utf-8"))
    summary = summarize_probe(probe, output, reference)
    return {
        "case_id": case_id,
        "path_kind": probe["path_kind"],
        "witness_xy": probe["xy"],
        "row_probe_half_span": probe["row_probe_half_span"],
        "witness_alpha_u8": int(probe["sample_u8"][3]),
        "witness_validity_alpha_u8": int(round(float(probe["validity_alpha"]) * 255.0)),
        "witness_sample_u8": [int(v) for v in probe["sample_u8"]],
        "witness_cell_valid": [
            float(probe["cell00_valid"]),
            float(probe["cell10_valid"]),
            float(probe["cell01_valid"]),
            float(probe["cell11_valid"]),
        ],
        "row_probe": summary,
    }


def build_report() -> dict[str, Any]:
    run([str(ROOT / "refs" / "scripts" / "build_olmradialblur_cli.sh")])
    zoom = capture_case(
        "case_0009",
        "refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py",
        6,
        0,
        Path("/tmp/olmradialblur_cpp_zoom_smoke"),
    )
    rotation = capture_case(
        "case_0010",
        "refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py",
        1614,
        6,
        Path("/tmp/olmradialblur_cpp_tiny_rotation_smoke"),
    )

    zoom_gap = zoom["row_probe"]["max_alpha_validity_gap"]
    rotation_gap = rotation["row_probe"]["max_alpha_validity_gap"]
    return {
        "kind": "olmradialblur_caller_collapse_plane_diag",
        "status": "diagnostic",
        "date": "2026-07-01",
        "zoom_case_0009": zoom,
        "tiny_rotation_case_0010": rotation,
        "reading": {
            "zoom": (
                "Across the bounded top-row probe, final inverse-sampled alpha stays near-opaque "
                "while the current preserved-validity proxy collapses much earlier. That makes the "
                "live Zoom caller-collapse lane narrower than direct sampling of the current "
                "validity plane."
            ),
            "tiny_rotation": (
                "Across the bounded tiny Rotation probe, validity alpha stays fully live, so the "
                "remaining failure is not an alpha-plane collapse. The surviving gap stays in the "
                "polar RGB / substitute-path population that feeds the final inverse sample."
            ),
            "extrema": {
                "zoom_max_alpha_validity_gap": zoom_gap,
                "rotation_max_alpha_validity_gap": rotation_gap,
            },
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    zoom = report["zoom_case_0009"]
    rotation = report["tiny_rotation_case_0010"]

    def section(title: str, case: dict[str, Any]) -> list[str]:
        row = case["row_probe"]["row"]
        lines = [
            f"## {title}",
            "",
            f"- Witness XY: `{case['witness_xy']}`",
            f"- Probe half-span: `{case['row_probe_half_span']}`",
            f"- Largest `alpha_u8 - validity_alpha_u8` gap: `{case['row_probe']['max_alpha_validity_gap']}`",
            f"- Largest RGB-vs-reference gap on the probe: `{case['row_probe']['max_rgb_reference_gap']}`",
            "",
            "Representative row probe:",
            "",
            "| x | sample_u8 | ref_u8 | alpha_u8 | validity_alpha_u8 | gap | cell_valid |",
            "| - | - | - | - | - | - | - |",
        ]
        for point in row:
            lines.append(
                f"| {point['x']} | `{point['sample_u8']}` | `{point['reference_u8']}` | "
                f"{point['alpha_u8']} | {point['validity_alpha_u8']} | "
                f"{point['alpha_minus_validity_alpha_u8']} | `{point['cell_valid']}` |"
            )
        lines.extend(["", "Interpretation:", "", report["reading"]["zoom" if case["case_id"] == "case_0009" else "tiny_rotation"], ""])
        return lines

    lines = [
        "# OLMRadialBlur Caller-Collapse Plane Diagnostic",
        "",
        "Date: 2026-07-01",
        "",
        "Bounded Mac-side diagnostic using the existing C++ slice plus an expanded witness dump. "
        "Each witness now captures a 9-pixel same-row probe centered on the original witness so "
        "we can compare final inverse-sampled alpha against the local preserved-validity proxy.",
        "",
    ]
    lines.extend(section("Zoom `case_0009`", zoom))
    lines.extend(section("tiny Rotation `case_0010`", rotation))
    lines.extend(
        [
            "## Bottom line",
            "",
            "- Zoom: the local validity plane collapses much faster than the final alpha plane, so the remaining caller-collapse behavior is not direct use of the current preserved-validity bits.",
            "- tiny Rotation: the local validity plane is already fully live across the bounded probe, so the remaining failure stays in the RGB/substitute path rather than in a validity-only alpha collapse.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
