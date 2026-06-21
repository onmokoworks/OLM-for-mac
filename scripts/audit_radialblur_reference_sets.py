#!/usr/bin/env python3
"""Audit duplicate OLMRadialBlur reference sets and misplaced bulk files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REFERENCE_SETS = {
    "legacy_20260604": "refs/win_references/20260604_olm/OLMRadialBlur",
    "extra_20260605_img2": "refs/win_references/20260605_extra/OLMRadialBlur_img2",
    "recapture_20260615_inner": "refs/win_references/olm_reference_return_windows_recapture_20260615/OLMRadialBlur_inner",
    "recapture_20260615_sizevar": "refs/win_references/olm_reference_return_windows_recapture_20260615/OLMRadialBlur_sizevar",
    "filtered_20260617_inner": "refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_filtered_software/OLMRadialBlur",
    "full_20260617_inner": "refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_full_software/OLMRadialBlur",
    "bulk_20260619_misplaced_directionalblur": (
        "refs/win_references/olm_windows_bulk_png_refs_20260619_014632_all_existing_requests_windows_result_20260619_0210/"
        "OLMDirectionalBlur"
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root: Path) -> dict[str, dict[str, Any]]:
    by_set: dict[str, dict[str, Any]] = {}
    for name, rel in REFERENCE_SETS.items():
        base = root / rel
        files: dict[str, dict[str, Any]] = {}
        if base.exists():
            for path in sorted(base.glob("*.png")):
                if path.name.endswith("_before_effects.png"):
                    continue
                files[path.name] = {
                    "path": str(path),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
        by_set[name] = {"path": str(base), "exists": base.exists(), "files": files}
    return by_set


def build_report(root: Path) -> dict[str, Any]:
    by_set = collect(root)
    hashes_by_name: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for set_name, row in by_set.items():
        for filename, info in row["files"].items():
            hashes_by_name[filename][info["sha256"]].append(set_name)
    duplicates = []
    conflicts = []
    for filename in sorted(hashes_by_name):
        hash_groups = hashes_by_name[filename]
        entry = {
            "filename": filename,
            "variant_count": len(hash_groups),
            "variants": [
                {"sha256": digest, "sets": sorted(sets)} for digest, sets in sorted(hash_groups.items())
            ],
        }
        if len(hash_groups) == 1 and sum(len(v) for v in hash_groups.values()) > 1:
            duplicates.append(entry)
        elif len(hash_groups) > 1:
            conflicts.append(entry)
    misplaced = [
        filename
        for filename in by_set["bulk_20260619_misplaced_directionalblur"]["files"]
        if filename.startswith("radialblur_")
    ]
    return {
        "kind": "olmradialblur_reference_set_audit",
        "schema": 1,
        "sets": by_set,
        "duplicate_same_hash": duplicates,
        "conflicting_same_name": conflicts,
        "misplaced_bulk_radialblur_files": sorted(misplaced),
        "summary": {
            "set_count": len(by_set),
            "conflict_count": len(conflicts),
            "duplicate_count": len(duplicates),
            "misplaced_bulk_radialblur_count": len(misplaced),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Reference Set Audit",
        "",
        "## Sets",
        "",
        "| Set | Exists | PNGs | Path |",
        "| --- | --- | ---: | --- |",
    ]
    for name, row in report["sets"].items():
        lines.append(f"| `{name}` | `{row['exists']}` | {len(row['files'])} | `{row['path']}` |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Duplicate same-hash filenames: `{report['summary']['duplicate_count']}`",
            f"- Conflicting same-name filenames: `{report['summary']['conflict_count']}`",
            f"- Misplaced bulk RadialBlur files under `OLMDirectionalBlur`: `{report['summary']['misplaced_bulk_radialblur_count']}`",
            "",
            "## Conflicting Same-Name Files",
            "",
        ]
    )
    if not report["conflicting_same_name"]:
        lines.append("- None.")
    else:
        for item in report["conflicting_same_name"]:
            lines.append(f"- `{item['filename']}`: `{item['variant_count']}` variants")
            for variant in item["variants"]:
                lines.append(f"  - `{variant['sha256'][:12]}` in `{variant['sets']}`")
    lines.extend(["", "## Misplaced Bulk Files", ""])
    if not report["misplaced_bulk_radialblur_files"]:
        lines.append("- None.")
    else:
        for filename in report["misplaced_bulk_radialblur_files"]:
            lines.append(f"- `{filename}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(repo_root())
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
