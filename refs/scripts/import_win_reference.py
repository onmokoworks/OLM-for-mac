#!/usr/bin/env python3
"""Import returned Windows AE reference results into refs/win_references."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
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
    return Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def safe_extract_zip_normalized(archive: zipfile.ZipFile, dest: Path) -> None:
    """Extract zip entries while accepting Windows-style backslash separators."""
    dest = dest.resolve()
    for info in archive.infolist():
        normalized_name = info.filename.replace("\\", "/")
        parts = [part for part in normalized_name.split("/") if part]
        if not parts:
            continue
        if any(part == ".." for part in parts):
            raise ValueError(f"unsafe zip path: {info.filename}")
        target = dest.joinpath(*parts).resolve()
        if not target.is_relative_to(dest):
            raise ValueError(f"unsafe zip path: {info.filename}")
        if info.is_dir() or normalized_name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open("wb") as out:
            shutil.copyfileobj(source, out)


def slug(value: str, fallback: str = "reference") -> str:
    value = value.strip().replace(" ", "")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value or fallback


def companion_assets(path: Path) -> list[Path]:
    if not path.exists():
        return []
    companions: list[Path] = []
    stem = path.stem
    for candidate in sorted(path.parent.glob(f"{stem}.*")):
        if candidate == path or not candidate.is_file():
            continue
        if candidate.name.startswith("._") or candidate.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        companions.append(candidate)
    return companions


def copy_asset_with_companions(source_manifest: Path, rel: str, dest_dir: Path, copied: set[str]) -> list[str]:
    copied_now: list[str] = []
    src = source_manifest.parent / rel
    if not src.exists():
        return copied_now
    targets = [src, *companion_assets(src)]
    for asset in targets:
        rel_name = asset.name
        if rel_name in copied:
            continue
        dest_path = dest_dir / rel_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, dest_path)
        copied.add(rel_name)
        copied_now.append(rel_name)
    return copied_now


def summarize_media_assets(dest_dir: Path) -> dict[str, Any]:
    files = [path for path in dest_dir.rglob("*") if path.is_file()]
    by_extension: dict[str, int] = {}
    for path in files:
        ext = path.suffix.lower()
        if ext not in MEDIA_EXTENSIONS:
            continue
        by_extension[ext] = by_extension.get(ext, 0) + 1
    return {
        "media_extensions": dict(sorted(by_extension.items())),
        "float_preserving_present": any(ext in FLOAT_PRESERVING_EXTENSIONS for ext in by_extension),
        "preferred_exr_present": ".exr" in by_extension,
    }


def find_png(source_root: Path, frame: str) -> Path | None:
    candidates = [
        source_root / frame,
        source_root / "png" / frame,
        source_root / "win" / frame,
        source_root / "reference" / frame,
    ]
    return next((path for path in candidates if path.exists()), None)


def load_package_metadata(source_root: Path) -> dict[str, Any] | None:
    path = source_root / "reference_package.json"
    if not path.exists():
        return None
    return load_json(path)


def import_legacy(source_root: Path, local_manifest_path: Path, dest_dir: Path) -> int:
    local_manifest = load_json(local_manifest_path)
    package = load_package_metadata(source_root)
    package_cases = {}
    if package:
        package_cases = {case["frame"]: case for case in package.get("cases", [])}

    imported = []
    missing = []
    mismatched = []
    dest_dir.mkdir(parents=True, exist_ok=True)

    for case in local_manifest["cases"]:
        frame = case["frame"]
        source_png = find_png(source_root, frame)
        if source_png is None:
            missing.append(frame)
            continue

        actual_hash = sha256(source_png)
        package_case = package_cases.get(frame)
        if package_case and package_case.get("sha256") != actual_hash:
            mismatched.append(frame)
            continue

        shutil.copy2(source_png, dest_dir / frame)
        imported.append(
            {
                "id": case["id"],
                "frame": frame,
                "params": case.get("params", {}),
                "sha256": actual_hash,
                "bytes": source_png.stat().st_size,
            }
        )

    if missing or mismatched:
        if missing:
            print("missing frames:", ", ".join(missing), file=sys.stderr)
        if mismatched:
            print("hash mismatches:", ", ".join(mismatched), file=sys.stderr)
        return 1

    receipt = {
        "schema": 1,
        "kind": "olm_imported_win_reference",
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_root),
        "package": package,
        "local_manifest": str(local_manifest_path),
        "dest_dir": str(dest_dir),
        "cases": imported,
    }
    receipt_path = dest_dir / "reference_import.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"imported {len(imported)} frames into {dest_dir}")
    print(f"receipt={receipt_path}")
    return 0


def manifest_effect_names(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    effect = manifest.get("effect")
    if isinstance(effect, dict):
        for key in ("name", "match_name"):
            value = effect.get(key)
            if isinstance(value, str) and value:
                names.add(value)
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        for source_key in ("effect", "selected_effect"):
            source = case.get(source_key)
            if isinstance(source, dict):
                for key in ("name", "match_name"):
                    value = source.get(key)
                    if isinstance(value, str) and value:
                        names.add(value)
            elif isinstance(source, str) and source:
                names.add(source)
        for effect_item in case.get("effects", case.get("selected_layer_effects", [])) or []:
            if isinstance(effect_item, dict):
                for key in ("name", "match_name"):
                    value = effect_item.get(key)
                    if isinstance(value, str) and value:
                        names.add(value)
    return names


def request_effect_names(request: dict[str, Any]) -> set[str]:
    effect = request.get("effect")
    if not isinstance(effect, dict):
        return set()
    return {
        value
        for value in (effect.get("name"), effect.get("match_name"))
        if isinstance(value, str) and value
    }


def request_case_ids(request: dict[str, Any]) -> set[str]:
    return {
        case["id"]
        for case in request.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }


def request_id(request: dict[str, Any]) -> str | None:
    value = request.get("request_id")
    return value if isinstance(value, str) and value else None


def manifest_request_ids(manifest: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    value = manifest.get("request_id")
    if isinstance(value, str) and value:
        ids.add(value)
    for item in manifest.get("requests", []):
        if isinstance(item, dict):
            value = item.get("request_id")
            if isinstance(value, str) and value:
                ids.add(value)
    for case in manifest.get("cases", []):
        if isinstance(case, dict):
            value = case.get("request_id")
            if isinstance(value, str) and value:
                ids.add(value)
    return ids


def manifest_request_case_ids(manifest: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        for key in ("request_case_id", "source_case_id"):
            value = case.get(key)
            if isinstance(value, str) and value:
                ids.add(value)
    return ids


def load_requests(request_paths: list[Path], request_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    if not request_paths:
        request_paths = sorted(request_dir.glob("*.json"))
    loaded = []
    for path in request_paths:
        path = path.resolve()
        loaded.append((path, load_json(path)))
    return loaded


def display_request_path(path: Path) -> str:
    try:
        return str(path.relative_to(repo_root()))
    except ValueError:
        return str(path)


def matching_requests(
    manifest: dict[str, Any],
    requests: list[tuple[Path, dict[str, Any]]],
) -> list[tuple[Path, dict[str, Any]]]:
    manifest_names = manifest_effect_names(manifest)
    manifest_req_ids = manifest_request_ids(manifest)
    manifest_ids = manifest_request_case_ids(manifest)
    matches = []
    for path, request in requests:
        req_id = request_id(request)
        request_id_match = bool(req_id and req_id in manifest_req_ids)
        effect_overlap = bool(manifest_names & request_effect_names(request))
        case_overlap = bool(manifest_ids & request_case_ids(request))
        if request_id_match or case_overlap or (effect_overlap and not manifest_ids and not manifest_req_ids):
            matches.append((path, request))
    return matches


def infer_effect_folder(manifest: dict[str, Any], matches: list[tuple[Path, dict[str, Any]]]) -> str:
    if matches:
        names = request_effect_names(matches[0][1])
        if names:
            return slug(sorted(names)[0], "request")
    names = manifest_effect_names(manifest)
    return slug(sorted(names)[0], "reference")


def case_effect_name(case: dict[str, Any]) -> str | None:
    for source_key in ("effect", "selected_effect"):
        source = case.get(source_key)
        if isinstance(source, dict):
            for key in ("match_name", "name"):
                value = source.get(key)
                if isinstance(value, str) and value:
                    return value
        elif isinstance(source, str) and source:
            return source
    for effect_item in case.get("effects", case.get("selected_layer_effects", [])) or []:
        if isinstance(effect_item, dict):
            for key in ("match_name", "name"):
                value = effect_item.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def manifest_case_group_key(case: dict[str, Any]) -> str:
    request_id = case.get("request_id")
    if isinstance(request_id, str) and request_id:
        return request_id
    effect_name = case_effect_name(case)
    if effect_name:
        return effect_name
    case_id = case.get("id")
    if isinstance(case_id, str) and case_id:
        return case_id
    return "ungrouped"


def split_manifest_if_aggregate(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    cases = manifest.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return [("manifest", manifest)]

    grouped: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        key = manifest_case_group_key(case)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(case)

    if len(order) <= 1:
        return [("manifest", manifest)]

    requests_index: dict[str, dict[str, Any]] = {}
    for item in manifest.get("requests", []):
        if isinstance(item, dict):
            value = item.get("request_id")
            if isinstance(value, str) and value:
                requests_index[value] = item

    parts: list[tuple[str, dict[str, Any]]] = []
    for key in order:
        part = dict(manifest)
        part["cases"] = grouped[key]
        first = grouped[key][0]
        request_id = first.get("request_id")
        if isinstance(request_id, str) and request_id:
            part["request_id"] = request_id
            if request_id in requests_index:
                part["requests"] = [requests_index[request_id]]
        else:
            part.pop("request_id", None)
            part.pop("requests", None)

        effect_name = case_effect_name(first)
        if effect_name:
            effect = {
                "name": effect_name,
                "match_name": effect_name,
            }
            first_effects = first.get("effects", first.get("selected_layer_effects", [])) or []
            if first_effects and isinstance(first_effects[0], dict):
                effect["name"] = first_effects[0].get("name") or effect_name
                effect["match_name"] = first_effects[0].get("match_name") or effect_name
            part["effect"] = effect
        parts.append((key, part))
    return parts


def copy_case_assets(source_manifest: Path, dest_dir: Path, manifest: dict[str, Any], replace: bool) -> None:
    if dest_dir.exists():
        if not replace:
            raise FileExistsError(f"destination already exists: {dest_dir} (use --replace)")
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: set[str] = set()
    case_artifacts: dict[str, dict[str, list[str]]] = {}
    for case in manifest.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        case_key = case_id if isinstance(case_id, str) and case_id else "unknown"
        artifact_row = case_artifacts.setdefault(case_key, {})
        for key in ("frame", "before_effects_frame"):
            rel = case.get(key)
            if not isinstance(rel, str) or not rel or rel in copied:
                continue
            copied_now = copy_asset_with_companions(source_manifest, rel, dest_dir, copied)
            if copied_now:
                artifact_row[key] = copied_now

    for extra_name in ("ae_runner_log.txt", "RUN_SUMMARY.md", "run_complete.json", "package_manifest.json"):
        src = source_manifest.parent / extra_name
        if src.exists():
            shutil.copy2(src, dest_dir / extra_name)

    (dest_dir / "reference_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    return case_artifacts


def copy_manifest_folder(source_manifest: Path, dest_dir: Path, replace: bool) -> None:
    if dest_dir.exists():
        if not replace:
            raise FileExistsError(f"destination already exists: {dest_dir} (use --replace)")
        shutil.rmtree(dest_dir)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_manifest.parent, dest_dir)


def run_verifier(
    request_path: Path,
    manifest_path: Path,
    allow_missing_optional_render_sets: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(repo_root() / "refs/scripts/verify_reference_request_result.py"),
    ]
    if allow_missing_optional_render_sets:
        cmd.append("--allow-missing-optional-render-sets")
    cmd.extend([str(request_path), str(manifest_path)])
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def import_request_results(
    source_root: Path,
    dest_root: Path,
    set_id: str,
    request_paths: list[Path],
    replace: bool,
    allow_missing_optional_render_sets: bool,
) -> int:
    manifests = sorted(source_root.rglob("reference_manifest.json"))
    if not manifests:
        print(f"reference_manifest.json not found under {source_root}", file=sys.stderr)
        return 1

    requests = load_requests(request_paths, repo_root() / "refs/reference_requests")
    imported = []
    failures = 0

    for manifest_path in manifests:
        manifest = load_json(manifest_path)
        manifest_parts = split_manifest_if_aggregate(manifest)

        for _part_key, part_manifest in manifest_parts:
            matches = matching_requests(part_manifest, requests)
            effect_folder = infer_effect_folder(part_manifest, matches)
            dest_dir = dest_root / set_id / effect_folder
            try:
                if len(manifest_parts) == 1:
                    copy_manifest_folder(manifest_path, dest_dir, replace)
                    case_artifacts = {}
                else:
                    case_artifacts = copy_case_assets(manifest_path, dest_dir, part_manifest, replace)
            except Exception as exc:  # noqa: BLE001 - report destination-specific import errors.
                print(f"[FAIL] {manifest_path}: {exc}", file=sys.stderr)
                failures += 1
                continue

            dest_manifest = dest_dir / "reference_manifest.json"
            media_summary = summarize_media_assets(dest_dir)
            receipt = {
                "schema": 1,
                "kind": "olm_imported_request_reference",
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "source_manifest": str(manifest_path),
                "dest_manifest": str(dest_manifest),
                "matched_requests": [display_request_path(path) for path, _request in matches],
                "split_from_aggregate": len(manifest_parts) > 1,
                "split_case_count": len(part_manifest.get("cases", [])),
                "case_artifacts": case_artifacts,
                **media_summary,
            }
            (dest_dir / "reference_import.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            if not matches:
                print(f"[WARN] imported without matching request: {dest_manifest}")
            else:
                if len(matches) > 1:
                    names = ", ".join(path.name for path, _request in matches)
                    print(f"[INFO] imported aggregate manifest with matching requests ({names}): {dest_manifest}")
                verified_ok = 0
                verified_failed = 0
                for request_path, _request in matches:
                    proc = run_verifier(request_path, dest_manifest, allow_missing_optional_render_sets)
                    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
                    if proc.returncode != 0:
                        verified_failed += 1
                    else:
                        verified_ok += 1
                if verified_failed and (len(matches) == 1 or verified_ok == 0):
                    failures += verified_failed

            imported.append(dest_manifest)

    print(f"imported_manifests={len(imported)}")
    for path in imported:
        print(f"- {path}")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Returned Windows reference zip or folder")
    parser.add_argument(
        "--dest-root",
        type=Path,
        default=Path("refs/win_references"),
        help="destination root for request-result imports",
    )
    parser.add_argument(
        "--set-id",
        default=None,
        help="reference set directory name. Defaults to the source stem.",
    )
    parser.add_argument(
        "--request",
        action="append",
        type=Path,
        default=[],
        help="request JSON to verify against. Defaults to all refs/reference_requests/*.json",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing destination directory",
    )
    parser.add_argument(
        "--allow-missing-optional-render-sets",
        action="store_true",
        help="pass through to verify_reference_request_result.py",
    )
    parser.add_argument(
        "--legacy-manifest",
        type=Path,
        default=None,
        help="legacy PNG-only import manifest. Enables the old refs/win importer mode.",
    )
    parser.add_argument(
        "--legacy-dest",
        type=Path,
        default=Path("refs/win"),
        help="legacy PNG-only destination directory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source).resolve()
    if not source.exists():
        print(f"source not found: {source}", file=sys.stderr)
        return 2

    def run_on_root(root: Path) -> int:
        if args.legacy_manifest is not None:
            manifest_path = args.legacy_manifest.resolve()
            if not manifest_path.exists():
                print(f"manifest not found: {manifest_path}", file=sys.stderr)
                return 2
            return import_legacy(root, manifest_path, args.legacy_dest.resolve())

        set_id = slug(args.set_id or source.stem, "returned_reference")
        return import_request_results(
            root,
            args.dest_root.resolve(),
            set_id,
            args.request,
            args.replace,
            args.allow_missing_optional_render_sets,
        )

    if source.is_dir():
        return run_on_root(source)

    if zipfile.is_zipfile(source):
        with tempfile.TemporaryDirectory(prefix="olm_win_ref_") as tmp:
            with zipfile.ZipFile(source) as archive:
                safe_extract_zip_normalized(archive, Path(tmp))
            return run_on_root(Path(tmp))

    print(f"source is neither a directory nor a zip file: {source}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
