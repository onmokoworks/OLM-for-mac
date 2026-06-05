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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def slug(value: str, fallback: str = "reference") -> str:
    value = value.strip().replace(" ", "")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value or fallback


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


def matching_requests(
    manifest: dict[str, Any],
    requests: list[tuple[Path, dict[str, Any]]],
) -> list[tuple[Path, dict[str, Any]]]:
    manifest_names = manifest_effect_names(manifest)
    manifest_ids = manifest_request_case_ids(manifest)
    matches = []
    for path, request in requests:
        effect_overlap = bool(manifest_names & request_effect_names(request))
        case_overlap = bool(manifest_ids & request_case_ids(request))
        if case_overlap or (effect_overlap and not manifest_ids):
            matches.append((path, request))
    return matches


def infer_effect_folder(manifest: dict[str, Any], matches: list[tuple[Path, dict[str, Any]]]) -> str:
    if matches:
        names = request_effect_names(matches[0][1])
        if names:
            return slug(sorted(names)[0], "request")
    names = manifest_effect_names(manifest)
    return slug(sorted(names)[0], "reference")


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
        matches = matching_requests(manifest, requests)
        effect_folder = infer_effect_folder(manifest, matches)
        dest_dir = dest_root / set_id / effect_folder
        try:
            copy_manifest_folder(manifest_path, dest_dir, replace)
        except Exception as exc:  # noqa: BLE001 - report destination-specific import errors.
            print(f"[FAIL] {manifest_path}: {exc}", file=sys.stderr)
            failures += 1
            continue

        dest_manifest = dest_dir / "reference_manifest.json"
        receipt = {
            "schema": 1,
            "kind": "olm_imported_request_reference",
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(manifest_path),
            "dest_manifest": str(dest_manifest),
            "matched_requests": [str(path.relative_to(repo_root())) for path, _request in matches],
        }
        (dest_dir / "reference_import.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        if not matches:
            print(f"[WARN] imported without matching request: {dest_manifest}")
        elif len(matches) > 1:
            names = ", ".join(path.name for path, _request in matches)
            print(f"[WARN] imported with multiple matching requests ({names}): {dest_manifest}")
        else:
            request_path = matches[0][0]
            proc = run_verifier(request_path, dest_manifest, allow_missing_optional_render_sets)
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
            if proc.returncode != 0:
                failures += 1

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
                archive.extractall(tmp)
            return run_on_root(Path(tmp))

    print(f"source is neither a directory nor a zip file: {source}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
