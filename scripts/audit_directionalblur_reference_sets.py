#!/usr/bin/env python3
"""Audit OLMDirectionalBlur reference sets and mixed bulk-return files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REFERENCE_SETS = {
    "legacy_20260604": "refs/win_references/20260604_olm/OLMDirectionalBlur",
    "context_scale_20260611": "refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur",
    "bulk_20260619_mixed_directionalblur": (
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


def classify_filename(name: str) -> str:
    if name.startswith("directionalblur_") or name.startswith("case_"):
        return "directionalblur"
    if name.startswith("radialblur_"):
        return "radialblur"
    if name.startswith("kirakira_"):
        return "kirakira"
    if name.startswith("olmcolorkey_"):
        return "olmcolorkey"
    if name.startswith("smoother2_"):
        return "olmsmoother2"
    return "unknown"


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
                    "class": classify_filename(path.name),
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
        groups = hashes_by_name[filename]
        entry = {
            "filename": filename,
            "variant_count": len(groups),
            "variants": [{"sha256": digest, "sets": sorted(sets)} for digest, sets in sorted(groups.items())],
        }
        if len(groups) == 1 and sum(len(v) for v in groups.values()) > 1:
            duplicates.append(entry)
        elif len(groups) > 1:
            conflicts.append(entry)

    class_counts = {
        set_name: dict(Counter(info["class"] for info in row["files"].values()))
        for set_name, row in by_set.items()
    }
    mixed_bulk_files = [
        filename
        for filename, info in by_set["bulk_20260619_mixed_directionalblur"]["files"].items()
        if info["class"] != "directionalblur"
    ]
    return {
        "kind": "olmdirectionalblur_reference_set_audit",
        "schema": 1,
        "sets": by_set,
        "class_counts": class_counts,
        "duplicate_same_hash": duplicates,
        "conflicting_same_name": conflicts,
        "mixed_bulk_non_directional_files": sorted(mixed_bulk_files),
        "summary": {
            "set_count": len(by_set),
            "conflict_count": len(conflicts),
            "duplicate_count": len(duplicates),
            "mixed_bulk_non_directional_count": len(mixed_bulk_files),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Reference Set Audit",
        "",
        "## Sets",
        "",
        "| Set | Exists | PNGs | Classes | Path |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for name, row in report["sets"].items():
        classes = report["class_counts"].get(name, {})
        lines.append(f"| `{name}` | `{row['exists']}` | {len(row['files'])} | `{classes}` | `{row['path']}` |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Duplicate same-hash filenames: `{report['summary']['duplicate_count']}`",
            f"- Conflicting same-name filenames: `{report['summary']['conflict_count']}`",
            f"- Non-DirectionalBlur PNGs under bulk `OLMDirectionalBlur`: `{report['summary']['mixed_bulk_non_directional_count']}`",
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
    lines.extend(["", "## Mixed Bulk Non-Directional Files", ""])
    if not report["mixed_bulk_non_directional_files"]:
        lines.append("- None.")
    else:
        for filename in report["mixed_bulk_non_directional_files"]:
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
