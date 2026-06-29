#!/usr/bin/env python3
"""Compare DirectionalBlur full-choreo vs scatter-helper ownership footprints."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "refs/reports/olmdirectionalblur_scatter_ownership_20260629.json"
OUT_MD = ROOT / "refs/reports/olmdirectionalblur_scatter_ownership_20260629.md"

TMP = Path("/private/tmp")
FULL_ROOT = TMP / "olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_full"
SCATTER_ROOT = TMP / "olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_scatter"


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def segment_ranges(xs: np.ndarray) -> list[list[int]]:
    if xs.size == 0:
        return []
    segs: list[list[int]] = []
    start = prev = int(xs[0])
    for raw in xs[1:]:
        x = int(raw)
        if x == prev + 1:
            prev = x
            continue
        segs.append([start, prev])
        start = prev = x
    segs.append([start, prev])
    return segs


def analyze_case(case_id: str, witness_row: int | None = None) -> dict:
    full = load_rgba(FULL_ROOT / "candidate" / f"{case_id}.png")
    scatter = load_rgba(SCATTER_ROOT / "candidate" / f"{case_id}.png")
    ref = load_rgba(FULL_ROOT / "reference" / f"{case_id}.png")

    full_vs_ref = full - ref
    scatter_vs_ref = scatter - ref
    scatter_vs_full = scatter - full

    report = {
        "case_id": case_id,
        "full_vs_ref": {
            "max_abs": [int(v) for v in np.abs(full_vs_ref).reshape(-1, 4).max(axis=0)],
            "nonzero_px": int(np.any(full_vs_ref != 0, axis=2).sum()),
        },
        "scatter_vs_ref": {
            "max_abs": [int(v) for v in np.abs(scatter_vs_ref).reshape(-1, 4).max(axis=0)],
            "nonzero_px": int(np.any(scatter_vs_ref != 0, axis=2).sum()),
        },
        "scatter_vs_full": {
            "max_abs": [int(v) for v in np.abs(scatter_vs_full).reshape(-1, 4).max(axis=0)],
            "nonzero_px": int(np.any(scatter_vs_full != 0, axis=2).sum()),
        },
    }

    if witness_row is not None:
        full_row_mask = np.any(full_vs_ref[witness_row, :, :] != 0, axis=1)
        scatter_row_mask = np.any(scatter_vs_ref[witness_row, :, :] != 0, axis=1)
        full_xs = np.where(full_row_mask)[0]
        scatter_xs = np.where(scatter_row_mask)[0]
        report["witness_row"] = {
            "y": witness_row,
            "full_nonzero_count": int(full_xs.size),
            "scatter_nonzero_count": int(scatter_xs.size),
            "full_segments": segment_ranges(full_xs),
            "scatter_segments": segment_ranges(scatter_xs),
            "identical_mask": bool(np.array_equal(full_row_mask, scatter_row_mask)),
        }

    mask = np.any(scatter_vs_full != 0, axis=2)
    ys, xs = np.where(mask)
    report["scatter_vs_full_bbox"] = (
        [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if xs.size else None
    )
    if xs.size:
        score = np.abs(scatter_vs_full).max(axis=2)
        ranked = sorted(((int(score[y, x]), int(x), int(y)) for y, x in zip(ys, xs)), reverse=True)[:8]
        report["scatter_vs_full_top_witnesses"] = [
            {
                "x": x,
                "y": y,
                "full_rgba": [int(v) for v in full[y, x]],
                "scatter_rgba": [int(v) for v in scatter[y, x]],
                "signed_delta": [int(v) for v in scatter_vs_full[y, x]],
            }
            for _, x, y in ranked
        ]
    else:
        report["scatter_vs_full_top_witnesses"] = []
    return report


def analyze() -> dict:
    return {
        "kind": "olmdirectionalblur_scatter_ownership",
        "generated_at": "2026-06-29",
        "full_root": str(FULL_ROOT),
        "scatter_root": str(SCATTER_ROOT),
        "cases": {
            "case_0001": analyze_case("case_0001", witness_row=169),
            "case_0005": analyze_case("case_0005"),
        },
    }


def write_report(report: dict) -> None:
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    c1 = report["cases"]["case_0001"]
    c5 = report["cases"]["case_0005"]
    row = c1["witness_row"]
    lines = [
        "# OLMDirectionalBlur Scatter Ownership Audit",
        "",
        "- Compare `rotated-aex-full-choreo` against `rotated-aex-exact-scatter-helper` on the current local smoke outputs.",
        "- Goal: determine whether source-driven scatter changes the angle-0 long-strip destination coverage, or only weaker secondary structure.",
        "",
        "## case_0001",
        "",
        f"- Witness row `y={row['y']}` full-choreo nonzero count: `{row['full_nonzero_count']}`",
        f"- Witness row `y={row['y']}` scatter-helper nonzero count: `{row['scatter_nonzero_count']}`",
        f"- Witness row masks identical: `{row['identical_mask']}`",
        f"- Full segments: `{row['full_segments']}`",
        f"- Scatter segments: `{row['scatter_segments']}`",
        f"- Scatter-vs-full bbox: `{c1['scatter_vs_full_bbox']}`",
        f"- Scatter-vs-full max abs RGBA: `{c1['scatter_vs_full']['max_abs']}`",
        "",
        "Interpretation:",
        "- The dominant angle-0 strip coverage is unchanged if the row masks are identical.",
        "- Any scatter-helper effect is therefore outside the primary strip witness, in weaker red structure.",
        "",
        "## case_0005",
        "",
        f"- Scatter-vs-full bbox: `{c5['scatter_vs_full_bbox']}`",
        f"- Scatter-vs-full max abs RGBA: `{c5['scatter_vs_full']['max_abs']}`",
        "- Top witnesses show where source-driven scatter changes diagonal behavior.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = analyze()
    write_report(report)
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
