#!/usr/bin/env python3
"""Measure whether row-coupled tiny-Rotation probes restore the missing bright lobe."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_row_coupling_probe_20260701.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_tiny_rotation_row_coupling_probe_20260701.md"
CASE_ID = "case_0010"
WITNESS_XY = (1614, 6)
BRIGHT_THRESHOLD = 200
WINDOW_RADIUS = 12
PATCH_RADIUS = 2
VARIANTS = [
    {
        "name": "baseline",
        "label": "baseline",
        "extra_args": [],
        "expected_mean_diff": 0.01032033661265432,
    },
    {
        "name": "prev2-k2-positive",
        "label": "prev2-k2-positive scale=0.0025",
        "extra_args": ["--outer-row-coupled-mode", "prev2-k2-positive", "--outer-row-coupled-scale", "0.0025"],
        "expected_mean_diff": 0.010719039351851851,
    },
    {
        "name": "prev2-row-tail-positive",
        "label": "prev2-row-tail-positive scale=0.005",
        "extra_args": ["--outer-row-coupled-mode", "prev2-row-tail-positive", "--outer-row-coupled-scale", "0.005"],
        "expected_mean_diff": 0.012562572337962962,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def run(cmd: list[str | Path]) -> None:
    subprocess.run([str(part) for part in cmd], cwd=ROOT, check=True)


def build_cli() -> None:
    run([ROOT / "refs" / "scripts" / "build_olmradialblur_cli.sh"])


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def bright_stats(rgba: np.ndarray) -> dict[str, object]:
    x, y = WITNESS_XY
    x0 = max(0, x - WINDOW_RADIUS)
    x1 = min(rgba.shape[1], x + WINDOW_RADIUS + 1)
    y0 = max(0, y - WINDOW_RADIUS)
    y1 = min(rgba.shape[0], y + WINDOW_RADIUS + 1)
    crop = rgba[y0:y1, x0:x1, 0]
    ys, xs = np.where(crop >= BRIGHT_THRESHOLD)
    count = int(xs.size)
    if count:
        xs_full = xs + x0
        ys_full = ys + y0
        center_of_mass = [float(xs_full.mean()), float(ys_full.mean())]
        top_pixels = sorted(
            [
                [int(crop[yy, xx]), int(xx + x0), int(yy + y0)]
                for yy, xx in zip(ys.tolist(), xs.tolist())
            ],
            reverse=True,
        )[:12]
    else:
        center_of_mass = None
        top_pixels = []
    patch = rgba[y - PATCH_RADIUS : y + 1, x - PATCH_RADIUS : x + 1, 0].astype(int).tolist()
    witness_rgba = rgba[y, x].astype(int).tolist()
    return {
        "bright_count": count,
        "center_of_mass": center_of_mass,
        "top_pixels": top_pixels,
        "witness_rgba": witness_rgba,
        "patch_r": patch,
    }


def run_variant(tmp_root: Path, variant: dict[str, object]) -> dict[str, object]:
    run_dir = tmp_root / str(variant["name"])
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = [
        "cli/OLMRadialBlur/olmradialblur_cli",
        "--input",
        "{input}",
        "--params",
        "{params}",
        "--output",
        "{output}",
    ]
    command.extend(str(part) for part in variant["extra_args"])  # type: ignore[index]
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
            " ".join(command),
            "--max-diff",
            "255",
            "--mean-diff",
            "1",
            "--nonzero-px-percent",
            "100",
        ]
    )
    diff = json.loads((run_dir / "reports" / "diff.json").read_text(encoding="utf-8"))
    case = diff["cases"][0]
    reference = load_rgba(run_dir / "reference" / f"{CASE_ID}.png")
    candidate = load_rgba(run_dir / "candidate" / f"{CASE_ID}.png")
    return {
        "name": variant["name"],
        "label": variant["label"],
        "extra_args": variant["extra_args"],
        "run_dir": str(run_dir),
        "diff": {
            "max_diff": int(case["max_diff"]),
            "mean_diff": float(case["mean_diff"]),
            "nonzero_px": int(case["nonzero_px"]),
            "nonzero_px_percent": float(case["nonzero_px_percent"]),
        },
        "reference": bright_stats(reference),
        "candidate": bright_stats(candidate),
    }


def build_report(rows: list[dict[str, object]]) -> dict[str, object]:
    reference = rows[0]["reference"]
    candidates = []
    for row in rows:
        candidate = row["candidate"]
        candidates.append(
            {
                "name": row["name"],
                "label": row["label"],
                "diff": row["diff"],
                "bright_count": candidate["bright_count"],
                "center_of_mass": candidate["center_of_mass"],
                "witness_rgba": candidate["witness_rgba"],
                "patch_r": candidate["patch_r"],
            }
        )
    return {
        "kind": "olmradialblur_tiny_rotation_row_coupling_probe",
        "case_id": CASE_ID,
        "witness_xy": list(WITNESS_XY),
        "window_radius": WINDOW_RADIUS,
        "bright_threshold_r": BRIGHT_THRESHOLD,
        "reference": {
            "bright_count": reference["bright_count"],
            "center_of_mass": reference["center_of_mass"],
            "witness_rgba": reference["witness_rgba"],
            "patch_r": reference["patch_r"],
            "top_pixels": reference["top_pixels"],
        },
        "variants": candidates,
        "conclusion": {
            "summary": (
                "The tested row-coupled diagnostics still do not recreate the missing bright lobe "
                "near the tiny Rotation witness. They can move global mean_diff, but the local "
                "25x25 bright-pixel count remains zero and the witness stays black."
            ),
            "implication": (
                "The useful clue remains structural and diagnostic only: a sparse cross-row "
                "positive family may exist upstream, but these current row-coupled surrogates are "
                "not close enough to promote into the port."
            ),
        },
    }


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# OLMRadialBlur tiny Rotation Row-Coupling Probe",
        "",
        "Date: 2026-07-01",
        "",
        "Goal:",
        "",
        "- Re-run the best current tiny-Rotation row-coupled diagnostics and check whether they",
        "  actually restore the missing bright lobe near the witness `(1614,6)`, not just the",
        "  global `mean_diff`.",
        "",
        "Reference bright lobe:",
        "",
        f"- bright count (`R >= {report['bright_threshold_r']}` in `25x25` window): `{report['reference']['bright_count']}`",
        f"- center of mass: `{report['reference']['center_of_mass']}`",
        f"- witness RGBA: `{report['reference']['witness_rgba']}`",
        f"- witness patch R (rows `y-2..y`, cols `x-2..x`): `{report['reference']['patch_r']}`",
        "",
        "## Variants",
        "",
        "| Variant | mean_diff | bright_count | witness_rgba | patch_r |",
        "| - | -: | -: | - | - |",
    ]
    for row in report["variants"]:
        diff = row["diff"]
        lines.append(
            f"| `{row['label']}` | `{diff['mean_diff']:.9f}` | `{row['bright_count']}` | "
            f"`{row['witness_rgba']}` | `{row['patch_r']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["conclusion"]["summary"],
            "",
            report["conclusion"]["implication"],
            "",
            "- `prev2-k2-positive` still leaves the witness patch identical to baseline",
            "  (`[[0,0,0],[4,0,0],[5,1,0]]`) and does not produce any nearby `R >= 200` pixels.",
            "- `prev2-row-tail-positive` worsens `mean_diff` further and also leaves the local",
            "  bright-pixel count at zero.",
            "- So the earlier row-coupling hints are still useful as a qualitative clue about an",
            "  upstream positive family, but they are not a close numeric stand-in for the AEX",
            "  bright-lobe path.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    build_cli()
    with tempfile.TemporaryDirectory(prefix="olmradialblur_row_coupling_") as tmp:
        tmp_root = Path(tmp)
        rows = [run_variant(tmp_root, variant) for variant in VARIANTS]
    report = build_report(rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
