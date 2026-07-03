#!/usr/bin/env python3
"""Summarize a Windows reference return and its imported destination set."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".exr",
    ".hdr",
    ".bmp",
}
FLOAT_PRESERVING_EXTENSIONS = {
    ".exr",
    ".tif",
    ".tiff",
    ".hdr",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Returned Windows reference zip or folder.")
    parser.add_argument("--imported-set-dir", type=Path, default=None, help="Imported refs/win_references/<set_id> directory.")
    parser.add_argument("--next-actions-json", type=Path, default=None, help="Optional next_reference_actions JSON emitted by intake.")
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def extract_if_zip(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return source
    if not source.exists() or not zipfile.is_zipfile(source):
        raise ValueError(f"not a directory or zip: {source}")
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            normalized = member.filename.replace("\\", "/")
            if not normalized or normalized.endswith("/"):
                continue
            if normalized.startswith("/") or ".." in Path(normalized).parts:
                raise ValueError(f"unsafe zip member: {member.filename}")
            target = dest / normalized
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
    visible_children = [
        path
        for path in dest.iterdir()
        if path.name != "__MACOSX" and not path.name.startswith("._")
    ]
    roots = [path for path in visible_children if path.is_dir()]
    return roots[0] if len(visible_children) == 1 and len(roots) == 1 else dest


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def manifest_effect_name(data: dict[str, Any]) -> str | None:
    effect = data.get("effect")
    if isinstance(effect, dict):
        for key in ("name", "match_name"):
            value = effect.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def request_ids_from_manifest(data: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for source in (data, *([item for item in data.get("requests", []) if isinstance(item, dict)]), *([item for item in data.get("cases", []) if isinstance(item, dict)])):
        value = source.get("request_id")
        if isinstance(value, str) and value:
            ids.add(value)
    return ids


def summarize_source(source_root: Path) -> dict[str, Any]:
    manifests = sorted(
        path
        for path in source_root.rglob("reference_manifest.json")
        if "__MACOSX" not in path.parts and not path.name.startswith("._")
    )
    request_ids: set[str] = set()
    effects = Counter()
    total_cases = 0
    render_sets = Counter()
    gpu_names = Counter()
    asset_formats = Counter()
    per_manifest: list[dict[str, Any]] = []
    for path in manifests:
        data = load_json(path)
        cases = data.get("cases", [])
        case_count = len(cases) if isinstance(cases, list) else 0
        total_cases += case_count
        request_ids.update(request_ids_from_manifest(data))
        effect_name = manifest_effect_name(data) or path.parent.name
        effects[effect_name] += case_count or 1
        for case in cases if isinstance(cases, list) else []:
            if not isinstance(case, dict):
                continue
            render_set = case.get("render_set")
            if isinstance(render_set, str) and render_set:
                render_sets[render_set] += 1
            gpu = case.get("project_gpu_accel_type")
            if isinstance(gpu, dict):
                current_name = gpu.get("current_name")
                if isinstance(current_name, str) and current_name:
                    gpu_names[current_name] += 1
            for key in ("frame", "before_effects_frame"):
                rel = case.get(key)
                if not isinstance(rel, str) or not rel:
                    continue
                base = path.parent / rel
                if base.exists():
                    asset_formats[base.suffix.lower()] += 1
                for companion in sorted(base.parent.glob(f"{base.stem}.*")) if base.parent.exists() else []:
                    if companion == base or not companion.is_file():
                        continue
                    ext = companion.suffix.lower()
                    if ext in MEDIA_EXTENSIONS:
                        asset_formats[ext] += 1
        per_manifest.append(
            {
                "manifest": str(path),
                "effect": effect_name,
                "case_count": case_count,
                "request_ids": sorted(request_ids_from_manifest(data)),
            }
        )
    return {
        "manifest_count": len(manifests),
        "case_count": total_cases,
        "request_ids": sorted(request_ids),
        "effects": dict(sorted(effects.items())),
        "render_sets": dict(sorted(render_sets.items())),
        "gpu_names": dict(sorted(gpu_names.items())),
        "asset_formats": dict(sorted(asset_formats.items())),
        "float_preserving_present": any(ext in FLOAT_PRESERVING_EXTENSIONS for ext in asset_formats),
        "preferred_exr_present": ".exr" in asset_formats,
        "manifests": per_manifest,
    }


def summarize_imported_set(imported_set_dir: Path | None) -> dict[str, Any] | None:
    if imported_set_dir is None or not imported_set_dir.exists():
        return None
    receipts = sorted(imported_set_dir.rglob("reference_import.json"))
    manifests = sorted(imported_set_dir.rglob("reference_manifest.json"))
    matched_request_counts = Counter()
    media_extensions = Counter()
    float_preserving_present = False
    preferred_exr_present = False
    for receipt_path in receipts:
        data = load_json(receipt_path)
        for request in data.get("matched_requests", []):
            if isinstance(request, str):
                matched_request_counts[request] += 1
        for ext, count in (data.get("media_extensions") or {}).items():
            if isinstance(ext, str) and isinstance(count, int):
                media_extensions[ext] += count
        float_preserving_present = float_preserving_present or bool(data.get("float_preserving_present"))
        preferred_exr_present = preferred_exr_present or bool(data.get("preferred_exr_present"))
    return {
        "imported_set_dir": str(imported_set_dir.resolve()),
        "receipt_count": len(receipts),
        "manifest_count": len(manifests),
        "matched_requests": dict(sorted(matched_request_counts.items())),
        "media_extensions": dict(sorted(media_extensions.items())),
        "float_preserving_present": float_preserving_present,
        "preferred_exr_present": preferred_exr_present,
    }


def summarize_next_actions(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    data = load_json(path)
    next_action = data.get("next_action")
    if not isinstance(next_action, dict):
        return {"path": str(path.resolve())}
    summary = {"path": str(path.resolve())}
    for key in ("request_id", "priority", "status", "reason"):
        if key in next_action:
            summary[key] = next_action[key]
    return summary


def build_report(source_root: Path, source: Path, imported_set_dir: Path | None, next_actions_json: Path | None) -> dict[str, Any]:
    source_summary = summarize_source(source_root)
    imported_summary = summarize_imported_set(imported_set_dir)
    next_action_summary = summarize_next_actions(next_actions_json)
    next_lane = "reference-followup"
    if next_action_summary is None:
        next_lane = "reference-imported"
    if source_summary["manifest_count"] == 0:
        next_lane = "reference-empty"
    return {
        "kind": "win_reference_return_summary",
        "schema": 1,
        "source": str(source.resolve()),
        "next_lane": next_lane,
        "source_summary": source_summary,
        "imported_summary": imported_summary,
        "next_action": next_action_summary,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Windows Reference Return Summary",
        "",
        f"- Source: `{report['source']}`",
        f"- next_lane: `{report['next_lane']}`",
        "",
    ]
    source_summary = report["source_summary"]
    lines.extend(
        [
            "## Source",
            "",
            f"- Manifest count: `{source_summary['manifest_count']}`",
            f"- Case count: `{source_summary['case_count']}`",
            f"- Request IDs: `{source_summary['request_ids']}`",
            f"- Effects: `{source_summary['effects']}`",
            f"- Render sets: `{source_summary['render_sets']}`",
            f"- GPU names: `{source_summary['gpu_names']}`",
            f"- Asset formats: `{source_summary['asset_formats']}`",
            f"- float_preserving_present: `{source_summary['float_preserving_present']}`",
            f"- preferred_exr_present: `{source_summary['preferred_exr_present']}`",
            "",
        ]
    )
    imported = report.get("imported_summary")
    if imported:
        lines.extend(
            [
                "## Imported Set",
                "",
                f"- Path: `{imported['imported_set_dir']}`",
                f"- Receipts: `{imported['receipt_count']}`",
                f"- Manifests: `{imported['manifest_count']}`",
                f"- Matched requests: `{imported['matched_requests']}`",
                f"- Media extensions: `{imported['media_extensions']}`",
                f"- float_preserving_present: `{imported['float_preserving_present']}`",
                f"- preferred_exr_present: `{imported['preferred_exr_present']}`",
                "",
            ]
        )
    next_action = report.get("next_action")
    if next_action:
        lines.append("## Next Action")
        lines.append("")
        for key, value in next_action.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olm_win_ref_summary_") as tmp:
        tmp_path = Path(tmp)
        source_root = extract_if_zip(args.source, tmp_path / "source")
        imported_set_dir = resolve(root, args.imported_set_dir) if args.imported_set_dir else None
        next_actions_json = resolve(root, args.next_actions_json) if args.next_actions_json else None
        report = build_report(source_root, args.source, imported_set_dir, next_actions_json)

    stem = args.source.stem if args.source.suffix else args.source.name
    output_json = resolve(root, args.output_json) if args.output_json else root / "refs" / "reports" / f"{stem}_win_reference_summary.json"
    output_md = resolve(root, args.output_md) if args.output_md else root / "refs" / "reports" / f"{stem}_win_reference_summary.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"win_reference_summary_json={output_json}")
    print(f"win_reference_summary_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
