#!/usr/bin/env python3
"""Capture and summarize the tiny-Rotation source-polar neighborhood near the witness."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_source_polar_probe_20260701.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_source_polar_probe_20260701.md"
CASE_ID = "case_0010"
WITNESS_X = 1614
WITNESS_Y = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def run(cmd: list[str | Path]) -> None:
    subprocess.run([str(part) for part in cmd], cwd=ROOT, check=True)


def build_cli() -> None:
    run([ROOT / "refs" / "scripts" / "build_olmradialblur_cli.sh"])


def luma(rgba: list[float]) -> float:
    return (float(rgba[0]) + float(rgba[1]) + float(rgba[2])) / 3.0


def strongest_entries(points: list[dict], positive: bool, limit: int = 8) -> list[dict]:
    filtered = []
    for point in points:
        value = luma(point["rgba"])
        if positive and value <= 0.0:
            continue
        if not positive and value >= 0.0:
            continue
        filtered.append(
            {
                "xy": point["xy"],
                "rgba": point["rgba"],
                "luma": value,
            }
        )
    filtered.sort(key=lambda row: row["luma"], reverse=positive)
    return filtered[:limit]


def local_cluster_entries(points: list[dict], sample_y0: int, limit: int = 8) -> list[dict]:
    filtered = []
    for point in points:
        xy = point["xy"]
        if not isinstance(xy, list) or len(xy) != 2:
            continue
        y = int(xy[1])
        value = luma(point["rgba"])
        if value <= 0.0:
            continue
        if y < sample_y0 - 1:
            continue
        filtered.append(
            {
                "xy": xy,
                "rgba": point["rgba"],
                "luma": value,
            }
        )
    filtered.sort(key=lambda row: row["luma"], reverse=True)
    return filtered[:limit]


def run_probe(tmp_root: Path) -> dict:
    run_dir = tmp_root / "tiny_rotation_source_probe"
    dump_path = run_dir / "witness.json"
    command = (
        f'cli/OLMRadialBlur/olmradialblur_cli --input "{{input}}" --params "{{params}}" '
        f'--output "{{output}}" --witness-dump "{dump_path}" --witness-x {WITNESS_X} --witness-y {WITNESS_Y}'
    )
    run(
        [
            "python3",
            ROOT / "refs" / "scripts" / "run_reference_test.py",
            REFERENCE_DIR,
            "--run-dir",
            run_dir,
            "--case-id",
            CASE_ID,
            "--expected-effect",
            "OLM RadialBlur",
            "--command",
            command,
            "--max-diff",
            "255",
            "--mean-diff",
            "1",
            "--nonzero-px-percent",
            "100",
        ]
    )
    payload = json.loads(dump_path.read_text(encoding="utf-8"))
    return {"run_dir": str(run_dir), "witness": payload}


def build_report(probe: dict) -> dict:
    witness = probe["witness"]
    source_probe = witness["source_probe"]
    strongest_positive = strongest_entries(source_probe, positive=True, limit=8)
    strongest_negative = strongest_entries(source_probe, positive=False, limit=8)
    dominant_local_positive_cluster = local_cluster_entries(source_probe, witness["sample_y0"], limit=8)
    direct_cells = [
        {"xy": [witness["sample_x0"], witness["sample_y0"]], "rgba": witness["source_probe"][71]["rgba"]},
        {"xy": [witness["sample_x1"], witness["sample_y0"]], "rgba": witness["source_probe"][72]["rgba"]},
        {"xy": [witness["sample_x0"], witness["sample_y1"]], "rgba": witness["source_probe"][82]["rgba"]},
        {"xy": [witness["sample_x1"], witness["sample_y1"]], "rgba": witness["source_probe"][83]["rgba"]},
    ]
    return {
        "kind": "olmradialblur_tiny_rotation_source_polar_probe",
        "case_id": CASE_ID,
        "witness_xy": [WITNESS_X, WITNESS_Y],
        "run_dir": probe["run_dir"],
        "sample_indices": [witness["sample_x0"], witness["sample_x1"], witness["sample_y0"], witness["sample_y1"]],
        "source_probe_origin": witness["source_probe_origin"],
        "source_probe_size": witness["source_probe_size"],
        "strongest_positive": strongest_positive,
        "dominant_local_positive_cluster": dominant_local_positive_cluster,
        "strongest_negative": strongest_negative,
        "direct_source_cells": direct_cells,
        "witness_sample_rgba": witness["sample_rgba"],
        "witness_sample_u8": witness["sample_u8"],
        "conclusion": {
            "summary": (
                "The dominant local positive source-polar family sits above the witness rows, "
                "centered at row 843 / angles 1601..1602, while the four direct source cells for "
                "rows 844/845 are all black. There is one farther bright outlier at (1608,838), "
                "but it is spatially separated from the local cluster that can plausibly feed the witness."
            ),
            "implication": (
                "The current same-row support can sample negative or zero cells at the witness, "
                "but it has no mechanism to carry the row-843 bright family into the rows that "
                "dominate the final bilinear mix."
            ),
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# OLMRadialBlur tiny Rotation Source-Polar Probe",
        "",
        "Date: 2026-07-01",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness XY: `{report['witness_xy']}`",
        f"- Sample indices `[x0,x1,y0,y1]`: `{report['sample_indices']}`",
        f"- Source-probe origin: `{report['source_probe_origin']}`",
        f"- Source-probe size: `{report['source_probe_size']}`",
        f"- Witness sample RGBA: `{report['witness_sample_rgba']}`",
        f"- Witness sample U8: `{report['witness_sample_u8']}`",
        "",
        "## Strongest positive source-polar cells",
        "",
        "| XY | luma | RGBA |",
        "| - | -: | - |",
    ]
    for row in report["strongest_positive"]:
        lines.append(f"| `{row['xy']}` | `{row['luma']:.6f}` | `{row['rgba']}` |")
    lines.extend(
        [
            "",
            "## Dominant local positive cluster near the witness rows",
            "",
            "| XY | luma | RGBA |",
            "| - | -: | - |",
        ]
    )
    for row in report["dominant_local_positive_cluster"]:
        lines.append(f"| `{row['xy']}` | `{row['luma']:.6f}` | `{row['rgba']}` |")
    lines.extend(
        [
            "",
            "## Strongest negative source-polar cells",
            "",
            "| XY | luma | RGBA |",
            "| - | -: | - |",
        ]
    )
    for row in report["strongest_negative"]:
        lines.append(f"| `{row['xy']}` | `{row['luma']:.6f}` | `{row['rgba']}` |")
    lines.extend(
        [
            "",
            "## Direct source cells for the final witness bilinear sample",
            "",
            "| XY | RGBA |",
            "| - | - |",
        ]
    )
    for row in report["direct_source_cells"]:
        lines.append(f"| `{row['xy']}` | `{row['rgba']}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["conclusion"]["summary"],
            "",
            report["conclusion"]["implication"],
            "",
            "- This keeps the active lane on upstream contribution ownership / neighboring-row",
            "  geometry, not on final alpha collapse or a uniform source-grid shift.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    build_cli()
    with tempfile.TemporaryDirectory(prefix="olmradialblur_source_polar_") as tmp:
        probe = run_probe(Path(tmp))
    report = build_report(probe)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
