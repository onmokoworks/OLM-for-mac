#!/usr/bin/env python3
"""Audit OLMDistanceGradation AE-host candidates against reference generations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


CASE_GROUPS = {
    "basic": {
        "candidate_dir": "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_basic_exact_20260619/candidate",
        "legacy_ref_dir": "refs/win_references/20260605_extra/OLMDistanceGradation",
        "normalized_ref_dir": "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_basic",
    },
    "extended": {
        "candidate_dir": "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_extended_exact_20260619/candidate",
        "legacy_ref_dir": "refs/win_references/20260605_extra/OLMDistanceGradation",
        "normalized_ref_dir": "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_extended",
    },
    "blur": {
        "candidate_dir": "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_blur_exact_20260619/candidate",
        "legacy_ref_dir": "refs/win_references/20260605_extra/OLMDistanceGradation",
        "normalized_ref_dir": "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_blur",
    },
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=tuple(CASE_GROUPS), action="append")
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
    y, x, channel = (int(v) for v in np.unravel_index(int(np.argmax(diff)), diff.shape))
    nonzero_px = int(np.any(diff != 0, axis=2).sum())
    total_px = int(diff.shape[0] * diff.shape[1])
    return {
        "reference": str(reference),
        "candidate": str(candidate),
        "status": "compared",
        "max_diff": int(diff.max()),
        "mean_diff": float(diff.mean()),
        "nonzero_px": nonzero_px,
        "nonzero_px_percent": nonzero_px * 100.0 / total_px,
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


def audit_group(root: Path, name: str) -> dict[str, Any]:
    cfg = CASE_GROUPS[name]
    candidate_dir = root / cfg["candidate_dir"]
    legacy_ref_dir = root / cfg["legacy_ref_dir"]
    normalized_ref_dir = root / cfg["normalized_ref_dir"]
    cases = []
    for candidate in sorted(candidate_dir.glob("case_*.png")):
        row = {
            "id": candidate.stem,
            "candidate": str(candidate),
            "legacy": compare(legacy_ref_dir / candidate.name, candidate)
            if (legacy_ref_dir / candidate.name).exists()
            else {"status": "missing", "reference": str(legacy_ref_dir / candidate.name)},
            "normalized": compare(normalized_ref_dir / candidate.name, candidate)
            if (normalized_ref_dir / candidate.name).exists()
            else {"status": "missing", "reference": str(normalized_ref_dir / candidate.name)},
        }
        cases.append(row)
    legacy_nonzero = [row for row in cases if row["legacy"].get("max_diff", 0) != 0]
    normalized_nonzero = [row for row in cases if row["normalized"].get("max_diff", 0) != 0]
    return {
        "group": name,
        "candidate_dir": str(candidate_dir),
        "legacy_ref_dir": str(legacy_ref_dir),
        "normalized_ref_dir": str(normalized_ref_dir),
        "case_count": len(cases),
        "legacy_nonzero_count": len(legacy_nonzero),
        "normalized_nonzero_count": len(normalized_nonzero),
        "cases": cases,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation Reference Provenance Audit",
        "",
        "| Group | Cases | Legacy nonzero | Normalized nonzero |",
        "| --- | ---: | ---: | ---: |",
    ]
    for group in report["groups"]:
        lines.append(
            f"| {group['group']} | {group['case_count']} | "
            f"{group['legacy_nonzero_count']} | {group['normalized_nonzero_count']} |"
        )
    for group in report["groups"]:
        lines.extend(
            [
                "",
                f"## {group['group']}",
                "",
                "| Case | Legacy max/mean | Normalized max/mean | Legacy max witness |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in group["cases"]:
            legacy = row["legacy"]
            normalized = row["normalized"]
            legacy_summary = (
                f"{legacy.get('max_diff')} / {legacy.get('mean_diff'):.9f}"
                if legacy.get("status") == "compared"
                else legacy.get("status", "-")
            )
            normalized_summary = (
                f"{normalized.get('max_diff')} / {normalized.get('mean_diff'):.9f}"
                if normalized.get("status") == "compared"
                else normalized.get("status", "-")
            )
            witness = legacy.get("max_at", {})
            witness_text = (
                f"`x={witness.get('x')} y={witness.get('y')} c={witness.get('channel')} "
                f"ref={witness.get('reference')} cand={witness.get('candidate')} delta={witness.get('delta')}`"
                if legacy.get("max_diff", 0) != 0
                else "-"
            )
            lines.append(f"| {row['id']} | {legacy_summary} | {normalized_summary} | {witness_text} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    groups = args.group or list(CASE_GROUPS)
    report = {
        "kind": "olmdistancegradation_reference_provenance",
        "schema": 1,
        "groups": [audit_group(root, group) for group in groups],
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
