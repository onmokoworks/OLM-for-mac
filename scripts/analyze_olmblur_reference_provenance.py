#!/usr/bin/env python3
"""Audit OLMBlur AE-host candidates against old and normalized references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root()))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-dir",
        type=Path,
        default=root / "refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/candidate",
    )
    parser.add_argument("--legacy-ref-dir", type=Path, default=root / "refs/win_references/20260604_olm/OLMBlur")
    parser.add_argument(
        "--normalized-ref-dir",
        type=Path,
        default=root / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur",
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
            "reference": display_path(reference),
            "candidate": display_path(candidate),
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
        "reference": display_path(reference),
        "candidate": display_path(candidate),
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


def classify_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    legacy_nonzero = [row["id"] for row in cases if row["legacy"].get("max_diff", 0) != 0]
    normalized_nonzero = [row["id"] for row in cases if row["normalized"].get("max_diff", 0) != 0]
    if not normalized_nonzero and legacy_nonzero:
        status = "normalized-software-exact-with-legacy-drift"
        reason = (
            "All AE-host candidates match the normalized 2026-06-18 Software references exactly, "
            "while older 2026-06-04 PNGs still drift for a subset of cases."
        )
        recommended_action = (
            "Prefer normalized Software references for OLMBlur; do not tune implementation behavior "
            "toward the older drift cases. Keep the CLI max=1 witnesses as binary-grounding diagnostics."
        )
    elif not normalized_nonzero:
        status = "normalized-software-exact"
        reason = "All AE-host candidates match the normalized Software references exactly."
        recommended_action = "Preserve current AE behavior and broaden validation to 16bpc/32bpc when references exist."
    else:
        status = "unresolved-normalized-residual"
        reason = "At least one AE-host candidate differs from the normalized Software reference."
        recommended_action = "Classify the normalized residual before changing OLMBlur behavior."
    return {
        "status": status,
        "reason": reason,
        "recommended_action": recommended_action,
        "case_count": len(cases),
        "legacy_nonzero_count": len(legacy_nonzero),
        "normalized_nonzero_count": len(normalized_nonzero),
        "legacy_nonzero_cases": legacy_nonzero,
        "normalized_nonzero_cases": normalized_nonzero,
    }


def render_markdown(report: dict[str, Any]) -> str:
    classification = report["classification"]
    lines = [
        "# OLMBlur Reference Provenance Audit",
        "",
        f"- Candidate dir: `{report['candidate_dir']}`",
        f"- Legacy ref dir: `{report['legacy_ref_dir']}`",
        f"- Normalized ref dir: `{report['normalized_ref_dir']}`",
        f"- Classification: `{classification['status']}`",
        f"- Reason: {classification['reason']}",
        f"- Recommended action: {classification['recommended_action']}",
        "",
        "| Case | Legacy max/mean | Normalized max/mean | Legacy max witness |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
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
    lines.extend(
        [
            "",
            f"- Legacy nonzero cases: `{report['legacy_nonzero_count']}`",
            f"- Normalized nonzero cases: `{report['normalized_nonzero_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    cases = []
    for candidate in sorted(args.candidate_dir.glob("case_*.png")):
        legacy_path = args.legacy_ref_dir / candidate.name
        normalized_path = args.normalized_ref_dir / candidate.name
        cases.append(
            {
                "id": candidate.stem,
                "candidate": display_path(candidate),
                "legacy": compare(legacy_path, candidate)
                if legacy_path.exists()
                else {"status": "missing", "reference": display_path(legacy_path)},
                "normalized": compare(normalized_path, candidate)
                if normalized_path.exists()
                else {"status": "missing", "reference": display_path(normalized_path)},
            }
        )
    report = {
        "kind": "olmblur_reference_provenance",
        "schema": 1,
        "candidate_dir": display_path(args.candidate_dir),
        "legacy_ref_dir": display_path(args.legacy_ref_dir),
        "normalized_ref_dir": display_path(args.normalized_ref_dir),
        "legacy_nonzero_count": sum(1 for row in cases if row["legacy"].get("max_diff", 0) != 0),
        "normalized_nonzero_count": sum(1 for row in cases if row["normalized"].get("max_diff", 0) != 0),
        "classification": classify_cases(cases),
        "cases": cases,
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
