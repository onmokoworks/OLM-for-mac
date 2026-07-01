#!/usr/bin/env python3
"""Summarize current 8bpc Software-reference provenance for low-risk exact slices."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class FeatureSet:
    name: str
    candidate_dir: str
    normalized_ref_dir: str
    legacy_ref_dir: str
    next_proof: str


FEATURES = [
    FeatureSet(
        name="OLMBlur",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur",
        legacy_ref_dir="refs/win_references/20260604_olm/OLMBlur",
        next_proof="Preserve 8bpc AE exact; binary-ground max=1 CLI witnesses only if closing AE-free residuals, then add 16/32bpc references.",
    ),
    FeatureSet(
        name="OLMColorKey",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey",
        legacy_ref_dir="refs/win_references/20260604_olm/OLMColorKey",
        next_proof="Prefer normalized 8bpc refs; request a narrow Edge trace only if a current Software residual reappears, then add 16/32bpc references.",
    ),
    FeatureSet(
        name="OLMToonDilate",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate",
        legacy_ref_dir="refs/win_references/20260604_olm/OLMToonDilate",
        next_proof="Keep the packaged 8bpc AE exact slice stable, then add 16/32bpc references for cases 0001..0003 without reopening the two-pass chamfer / premultiply rule.",
    ),
    FeatureSet(
        name="OLMDistanceGradation basic",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_basic_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_basic",
        legacy_ref_dir="refs/win_references/20260605_extra/OLMDistanceGradation",
        next_proof="Keep 8bpc AE exact; binary-ground field prep/OpenCV details before changing CLI, then add 16/32bpc references.",
    ),
    FeatureSet(
        name="OLMDistanceGradation extended",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_extended_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_extended",
        legacy_ref_dir="refs/win_references/20260605_extra/OLMDistanceGradation",
        next_proof="Keep 8bpc AE exact; binary-ground Constant/render-mode field prep before changing CLI, then add 16/32bpc references.",
    ),
    FeatureSet(
        name="OLMDistanceGradation blur",
        candidate_dir="refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_blur_exact_20260619/candidate",
        normalized_ref_dir="refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMDistanceGradation_blur",
        legacy_ref_dir="refs/win_references/20260605_extra/OLMDistanceGradation",
        next_proof="Keep 8bpc AE exact; trace OpenCV distanceTransform/GaussianBlur args before changing blur semantics, then add 16/32bpc references.",
    ),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=root / "refs/reports/software_reference_canonicalization_8bpc.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=root / "refs/reports/software_reference_canonicalization_8bpc.md",
    )
    return parser.parse_args()


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def load_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.int16)


def compare(reference: Path, candidate: Path, root: Path) -> dict[str, Any]:
    if not reference.exists():
        return {"status": "missing", "reference": display_path(root, reference)}
    ref = load_rgba(reference)
    cand = load_rgba(candidate)
    if ref.shape != cand.shape:
        return {
            "status": "shape-mismatch",
            "reference": display_path(root, reference),
            "candidate": display_path(root, candidate),
            "reference_shape": list(ref.shape),
            "candidate_shape": list(cand.shape),
        }
    diff = np.abs(ref - cand)
    y, x, channel = (int(v) for v in np.unravel_index(int(np.argmax(diff)), diff.shape))
    return {
        "status": "compared",
        "reference": display_path(root, reference),
        "candidate": display_path(root, candidate),
        "max_diff": int(diff.max()),
        "mean_diff": float(diff.mean()),
        "max_at": {
            "x": x,
            "y": y,
            "channel": channel,
            "reference": [int(v) for v in ref[y, x]],
            "candidate": [int(v) for v in cand[y, x]],
        },
    }


def audit_feature(root: Path, feature: FeatureSet) -> dict[str, Any]:
    candidate_dir = root / feature.candidate_dir
    normalized_dir = root / feature.normalized_ref_dir
    legacy_dir = root / feature.legacy_ref_dir
    cases = []
    for candidate in sorted(candidate_dir.glob("case_*.png")):
        normalized = compare(normalized_dir / candidate.name, candidate, root)
        legacy = compare(legacy_dir / candidate.name, candidate, root)
        cases.append(
            {
                "id": candidate.stem,
                "normalized": normalized,
                "legacy": legacy,
            }
        )
    normalized_nonzero = [row for row in cases if row["normalized"].get("max_diff", 0) != 0]
    legacy_nonzero = [row for row in cases if row["legacy"].get("max_diff", 0) != 0]
    missing = [
        row
        for row in cases
        if row["normalized"].get("status") != "compared" or row["legacy"].get("status") not in {"compared", "missing"}
    ]
    return {
        "name": feature.name,
        "candidate_dir": display_path(root, candidate_dir),
        "normalized_ref_dir": display_path(root, normalized_dir),
        "legacy_ref_dir": display_path(root, legacy_dir),
        "case_count": len(cases),
        "normalized_nonzero_count": len(normalized_nonzero),
        "legacy_nonzero_count": len(legacy_nonzero),
        "missing_or_shape_mismatch_count": len(missing),
        "canonical_8bpc_status": "normalized-software-exact" if cases and not normalized_nonzero and not missing else "needs-audit",
        "legacy_drift_cases": [
            {
                "id": row["id"],
                "max_diff": row["legacy"].get("max_diff"),
                "mean_diff": row["legacy"].get("mean_diff"),
                "max_at": row["legacy"].get("max_at"),
            }
            for row in legacy_nonzero
        ],
        "next_proof": feature.next_proof,
        "cases": cases,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8bpc Software Reference Canonicalization Audit",
        "",
        "This report checks whether current AE-host candidates match the normalized Windows Software references,",
        "separately from older reference generations that may drift.",
        "",
        "| Feature | Cases | Normalized nonzero | Legacy nonzero | Status | Next proof |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for feature in report["features"]:
        lines.append(
            f"| {feature['name']} | {feature['case_count']} | "
            f"{feature['normalized_nonzero_count']} | {feature['legacy_nonzero_count']} | "
            f"`{feature['canonical_8bpc_status']}` | {feature['next_proof']} |"
        )
    for feature in report["features"]:
        if not feature["legacy_drift_cases"]:
            continue
        lines.extend(["", f"## {feature['name']} Legacy Drift Cases", ""])
        for row in feature["legacy_drift_cases"]:
            witness = row.get("max_at") or {}
            lines.append(
                f"- `{row['id']}`: max `{row['max_diff']}`, mean `{row['mean_diff']:.9f}`, "
                f"witness `x={witness.get('x')} y={witness.get('y')} c={witness.get('channel')} "
                f"ref={witness.get('reference')} cand={witness.get('candidate')}`"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    report = {
        "kind": "software_reference_canonicalization_8bpc",
        "schema": 1,
        "features": [audit_feature(root, feature) for feature in FEATURES],
    }
    for output in (args.output_json, args.output_md):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={display_path(root, args.output_json)}")
    print(f"report_md={display_path(root, args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
