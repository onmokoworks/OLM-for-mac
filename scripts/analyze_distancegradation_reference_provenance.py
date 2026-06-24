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


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root()))
    except ValueError:
        return str(path)


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


def audit_group(root: Path, name: str) -> dict[str, Any]:
    cfg = CASE_GROUPS[name]
    candidate_dir = root / cfg["candidate_dir"]
    legacy_ref_dir = root / cfg["legacy_ref_dir"]
    normalized_ref_dir = root / cfg["normalized_ref_dir"]
    cases = []
    for candidate in sorted(candidate_dir.glob("case_*.png")):
        row = {
            "id": candidate.stem,
            "candidate": display_path(candidate),
            "legacy": compare(legacy_ref_dir / candidate.name, candidate)
            if (legacy_ref_dir / candidate.name).exists()
            else {"status": "missing", "reference": display_path(legacy_ref_dir / candidate.name)},
            "normalized": compare(normalized_ref_dir / candidate.name, candidate)
            if (normalized_ref_dir / candidate.name).exists()
            else {"status": "missing", "reference": display_path(normalized_ref_dir / candidate.name)},
        }
        cases.append(row)
    legacy_nonzero = [row for row in cases if row["legacy"].get("max_diff", 0) != 0]
    normalized_nonzero = [row for row in cases if row["normalized"].get("max_diff", 0) != 0]
    if len(cases) > 0 and len(normalized_nonzero) == 0 and len(legacy_nonzero) > 0:
        classification = {
            "status": "reference-generation-split",
            "reason": "AE-host candidates are exact against normalized refs but drift against the older legacy set",
            "recommended_action": "prefer normalized refs for 8bpc Software conformance; do not tune from legacy-only drift",
        }
    elif len(cases) > 0 and len(normalized_nonzero) == 0:
        classification = {
            "status": "normalized-software-exact",
            "reason": "AE-host candidates exactly match normalized refs for this group",
            "recommended_action": "preserve this 8bpc behavior and add 16/32bpc refs",
        }
    else:
        classification = {
            "status": "unresolved-normalized-residual",
            "reason": "at least one candidate differs from the normalized reference generation",
            "recommended_action": "inspect normalized residuals before claiming 8bpc conformance",
        }
    return {
        "group": name,
        "candidate_dir": display_path(candidate_dir),
        "legacy_ref_dir": display_path(legacy_ref_dir),
        "normalized_ref_dir": display_path(normalized_ref_dir),
        "case_count": len(cases),
        "legacy_nonzero_count": len(legacy_nonzero),
        "normalized_nonzero_count": len(normalized_nonzero),
        "classification": classification,
        "cases": cases,
    }


def classify_report(groups: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_nonzero_total = sum(int(group["normalized_nonzero_count"]) for group in groups)
    legacy_nonzero_total = sum(int(group["legacy_nonzero_count"]) for group in groups)
    case_total = sum(int(group["case_count"]) for group in groups)
    if normalized_nonzero_total == 0 and legacy_nonzero_total > 0:
        status = "normalized-software-exact-with-legacy-drift"
        reason = "all audited AE-host candidates match normalized refs; only older legacy references drift"
        action = "use normalized refs as the active 8bpc Software baseline; keep legacy drift as provenance evidence"
    elif normalized_nonzero_total == 0:
        status = "normalized-software-exact"
        reason = "all audited AE-host candidates match normalized refs"
        action = "preserve 8bpc behavior and add 16/32bpc references"
    else:
        status = "unresolved-normalized-residual"
        reason = "one or more audited candidates differ from normalized refs"
        action = "investigate normalized residuals before changing conformance status"
    return {
        "status": status,
        "reason": reason,
        "recommended_action": action,
        "case_total": case_total,
        "legacy_nonzero_total": legacy_nonzero_total,
        "normalized_nonzero_total": normalized_nonzero_total,
    }


def render_markdown(report: dict[str, Any]) -> str:
    classification = report["classification"]
    lines = [
        "# OLMDistanceGradation Reference Provenance Audit",
        "",
        f"- Classification: `{classification['status']}`",
        f"- Reason: {classification['reason']}",
        f"- Recommended action: {classification['recommended_action']}",
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
                f"- Classification: `{group['classification']['status']}`",
                f"- Recommended action: {group['classification']['recommended_action']}",
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
    audited_groups = [audit_group(root, group) for group in groups]
    report = {
        "kind": "olmdistancegradation_reference_provenance",
        "schema": 1,
        "classification": classify_report(audited_groups),
        "groups": audited_groups,
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
