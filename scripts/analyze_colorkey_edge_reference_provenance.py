#!/usr/bin/env python3
"""Audit OLMColorKey Edge image residuals against known reference generations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=root
        / "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/candidate/case_0009.png",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        action="append",
        default=[
            root / "refs/win_references/20260604_olm/OLMColorKey/case_0009.png",
            root
            / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey/case_0009.png",
            root
            / "refs/reports/ae_host_validation_20260618_232926/cli_checks/olmcolorkey_cpp_distance_type_fix/reference/case_0009.png",
        ],
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def compare(reference: Path, candidate: Path) -> dict[str, Any]:
    ref = load_rgba(reference)
    cand = load_rgba(candidate)
    if ref.shape != cand.shape:
        return {
            "reference": str(reference),
            "candidate": str(candidate),
            "status": "shape-mismatch",
            "reference_shape": list(ref.shape),
            "candidate_shape": list(cand.shape),
        }
    diff = np.abs(ref - cand)
    flat = diff.reshape(-1, 4)
    max_pos = np.unravel_index(int(np.argmax(diff)), diff.shape)
    y, x, channel = (int(max_pos[0]), int(max_pos[1]), int(max_pos[2]))
    nonzero_px = int(np.any(diff != 0, axis=2).sum())
    total_px = int(diff.shape[0] * diff.shape[1])
    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "status": "compared",
        "total_px": total_px,
        "nonzero_px": nonzero_px,
        "nonzero_px_percent": nonzero_px * 100.0 / total_px,
        "max_diff": int(diff.max()),
        "mean_diff": float(diff.mean()),
        "channel_max_rgba": [int(v) for v in flat.max(axis=0)],
        "channel_mean_rgba": [float(v) for v in flat.mean(axis=0)],
        "max_at": {
            "x": x,
            "y": y,
            "channel": channel,
            "reference": [int(v) for v in ref[y, x]],
            "candidate": [int(v) for v in cand[y, x]],
            "delta": [int(v) for v in diff[y, x]],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMColorKey Edge Reference Provenance Audit",
        "",
        f"- Candidate: `{report['candidate']}`",
        "",
        "| Reference | Max | Mean | Nonzero px % | Channel max RGBA | Max witness |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report["comparisons"]:
        if row.get("status") != "compared":
            lines.append(f"| `{row['reference']}` | - | - | - | - | `{row['status']}` |")
            continue
        witness = row["max_at"]
        lines.append(
            "| "
            f"`{row['reference']}` | "
            f"{row['max_diff']} | "
            f"{row['mean_diff']:.9f} | "
            f"{row['nonzero_px_percent']:.6f} | "
            f"`{row['channel_max_rgba']}` | "
            f"`x={witness['x']} y={witness['y']} c={witness['channel']} "
            f"ref={witness['reference']} cand={witness['candidate']} delta={witness['delta']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    candidate = args.candidate
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    comparisons = []
    for reference in args.reference:
        if not reference.exists():
            comparisons.append({"reference": str(reference), "status": "missing"})
            continue
        comparisons.append(compare(reference, candidate))
    report = {
        "kind": "olmcolorkey_edge_reference_provenance",
        "schema": 1,
        "candidate": str(candidate),
        "comparisons": comparisons,
    }
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
