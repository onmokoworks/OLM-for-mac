#!/usr/bin/env python3
"""Summarize an AE host return into a compact plugin/pixel-coverage report."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Returned AE host result folder or zip.")
    parser.add_argument(
        "--package",
        type=Path,
        default=None,
        help="Optional Mac plug-in package or handoff zip for pixel-request coverage.",
    )
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


def find_validation_jsons(result_root: Path) -> list[Path]:
    return sorted(
        path
        for path in result_root.rglob("AE_VALIDATION_RESULT*.json")
        if "__MACOSX" not in path.parts and not path.name.startswith("._")
    )


def is_host_validation_json(path: Path) -> bool:
    try:
        data = load_json(path)
    except Exception:
        return False
    return data.get("kind") == "olm_ae_host_validation_result"


def find_nested_mac_package(package_root: Path) -> Path | None:
    manifest_path = package_root / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
        except Exception:
            manifest = {}
        if manifest.get("kind") == "olm_mac_plugin_package":
            return package_root
        nested = manifest.get("mac_plugins_zip")
        if manifest.get("kind") == "olm_port_handoff_package" and isinstance(nested, str):
            nested_path = package_root / nested
            if nested_path.exists():
                return nested_path
    matches = list(package_root.rglob("olm_mac_plugins*_clean.zip"))
    if len(matches) == 1:
        return matches[0]
    return None


def materialize_mac_package(package_root: Path, tmp_path: Path) -> Path:
    mac_package = find_nested_mac_package(package_root)
    if mac_package is None:
        raise ValueError("could not locate nested Mac plug-in package")
    if mac_package.is_dir():
        return mac_package
    return extract_if_zip(mac_package, tmp_path / "mac_package")


def pixel_request_entries(mac_root: Path) -> list[tuple[str, Path]]:
    manifest = load_json(mac_root / "manifest.json")
    entries = manifest.get("ae_pixel_validation_requests", [])
    found: list[tuple[str, Path]] = []
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            request_id = entry.get("request_id")
            rel = entry.get("zip")
            if isinstance(request_id, str) and isinstance(rel, str):
                path = mac_root / rel
                if path.exists():
                    found.append((request_id, path))
    return found


def request_aliases(request_id: str, request_zip: Path) -> set[str]:
    aliases = {request_id, request_zip.stem}
    for prefix in ("ae_pixel_", "olm"):
        if request_id.startswith(prefix):
            aliases.add(request_id[len(prefix) :])
    aliases.add(request_zip.stem.replace("_request", ""))
    return {alias.lower() for alias in aliases if alias}


def find_pixel_result(result_root: Path, request_id: str, request_zip: Path) -> Path | None:
    aliases = request_aliases(request_id, request_zip)
    candidates: list[Path] = []
    for path in result_root.rglob("*"):
        if path.name.startswith("._") or "__MACOSX" in path.parts:
            continue
        stem = path.stem.lower()
        name = path.name.lower()
        if any(alias in stem or alias in name for alias in aliases):
            if path.is_dir() or (path.is_file() and zipfile.is_zipfile(path)):
                candidates.append(path)
    exact = [path for path in candidates if path.stem.lower() in aliases or path.name.lower() in aliases]
    if len(exact) == 1:
        return exact[0]
    if len(candidates) == 1:
        return candidates[0]
    return None


def plugin_status(entry: dict[str, Any]) -> str:
    states = [entry.get("loaded"), entry.get("applied"), entry.get("render_succeeded")]
    if any(value is False for value in states):
        return "failed"
    if all(value is True for value in states):
        return "passed"
    return "incomplete"


def build_report(result_root: Path, package_root: Path | None, source_result: Path, source_package: Path | None) -> dict[str, Any]:
    validation_files = [path for path in find_validation_jsons(result_root) if is_host_validation_json(path)]
    plugin_rows: list[dict[str, Any]] = []
    plugin_counts = Counter()
    metadata: dict[str, Any] = {}
    for path in validation_files:
        data = load_json(path)
        if not metadata:
            for key in ("ae_version", "macos_version", "machine", "package_configuration", "project_gpu_accel_type"):
                if key in data:
                    metadata[key] = data[key]
        for entry in data.get("plugins", []):
            if not isinstance(entry, dict):
                continue
            status = plugin_status(entry)
            plugin_counts[status] += 1
            plugin_rows.append(
                {
                    "validation_json": str(path),
                    "name": entry.get("name"),
                    "status": status,
                    "loaded": entry.get("loaded"),
                    "applied": entry.get("applied"),
                    "render_succeeded": entry.get("render_succeeded"),
                    "error": entry.get("error", ""),
                }
            )

    pixel_rows: list[dict[str, Any]] = []
    pixel_counts = Counter()
    if package_root is not None:
        mac_root = materialize_mac_package(package_root, result_root.parent / "_mac_package_extract")
        for request_id, request_zip in pixel_request_entries(mac_root):
            candidate = find_pixel_result(result_root, request_id, request_zip)
            status = "matched" if candidate is not None else "missing"
            pixel_counts[status] += 1
            pixel_rows.append(
                {
                    "request_id": request_id,
                    "request_zip": str(request_zip),
                    "status": status,
                    "matched_result": str(candidate) if candidate is not None else None,
                }
            )

    next_lane = "host-fix" if plugin_counts.get("failed", 0) or pixel_counts.get("missing", 0) else "ae-validate"
    host_status = "host-debuggable"
    if plugin_counts.get("failed", 0):
        host_status = "host-fix-needed"
    elif pixel_counts and pixel_counts.get("missing", 0):
        host_status = "pixel-coverage-partial"
    elif validation_files:
        host_status = "host-stable"

    return {
        "kind": "ae_host_return_summary",
        "schema": 1,
        "source_result": str(source_result.resolve()),
        "source_package": str(source_package.resolve()) if source_package else None,
        "validation_file_count": len(validation_files),
        "plugin_status_counts": dict(sorted(plugin_counts.items())),
        "pixel_request_counts": dict(sorted(pixel_counts.items())),
        "host_status": host_status,
        "next_lane": next_lane,
        "metadata": metadata,
        "plugins": plugin_rows,
        "pixel_requests": pixel_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AE Host Return Summary",
        "",
        f"- Source result: `{report['source_result']}`",
    ]
    if report.get("source_package"):
        lines.append(f"- Source package: `{report['source_package']}`")
    lines.extend(
        [
            f"- Validation JSONs: `{report['validation_file_count']}`",
            f"- Plugin status counts: `{report['plugin_status_counts']}`",
            f"- Pixel request counts: `{report['pixel_request_counts']}`",
            f"- host_status: `{report['host_status']}`",
            f"- next_lane: `{report['next_lane']}`",
            "",
        ]
    )
    metadata = report.get("metadata") or {}
    if metadata:
        lines.append("## Environment")
        lines.append("")
        for key in ("ae_version", "macos_version", "machine", "package_configuration"):
            if metadata.get(key):
                lines.append(f"- {key}: `{metadata[key]}`")
        gpu = metadata.get("project_gpu_accel_type")
        if isinstance(gpu, dict):
            lines.append(f"- project_gpu_accel_type: `{gpu.get('current_name')}` raw=`{gpu.get('raw')}`")
        lines.append("")
    if report["plugins"]:
        lines.append("## Plugins")
        lines.append("")
        for row in report["plugins"]:
            lines.append(
                f"- `{row['name']}`: `{row['status']}` "
                f"(loaded={row['loaded']}, applied={row['applied']}, render={row['render_succeeded']})"
            )
            if row.get("error"):
                lines.append(f"  - error: {row['error']}")
        lines.append("")
    if report["pixel_requests"]:
        lines.append("## Pixel Requests")
        lines.append("")
        for row in report["pixel_requests"]:
            line = f"- `{row['request_id']}`: `{row['status']}`"
            if row.get("matched_result"):
                line += f" -> `{row['matched_result']}`"
            lines.append(line)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olm_ae_host_summary_") as tmp:
        tmp_path = Path(tmp)
        result_root = extract_if_zip(args.result, tmp_path / "result")
        package_root: Path | None = None
        if args.package is not None:
            package_root = extract_if_zip(args.package, tmp_path / "package")
        report = build_report(result_root, package_root, args.result, args.package)

    stem = args.result.stem if args.result.suffix else args.result.name
    output_json = resolve(root, args.output_json) if args.output_json else root / "refs" / "reports" / f"{stem}_ae_host_summary.json"
    output_md = resolve(root, args.output_md) if args.output_md else root / "refs" / "reports" / f"{stem}_ae_host_summary.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"ae_host_summary_json={output_json}")
    print(f"ae_host_summary_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
