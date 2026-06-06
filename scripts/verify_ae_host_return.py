#!/usr/bin/env python3
"""Verify an AE host return bundle against a Mac plug-in or OLM handoff package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Mac plug-in zip or OLM handoff zip.")
    parser.add_argument("result", type=Path, help="Returned AE host result folder or zip.")
    parser.add_argument(
        "--require-all-pass",
        action="store_true",
        help="Require all plug-ins in AE_VALIDATION_RESULT*.json to load/apply/render.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Directory for pixel verification reports. Defaults to /tmp/olm_ae_host_return.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def extract_if_zip(source: Path, dest: Path) -> Path:
    source = source.resolve()
    if source.is_dir():
        return source
    if not source.exists() or not zipfile.is_zipfile(source):
        raise ValueError(f"not a directory or zip: {source}")
    with zipfile.ZipFile(source) as archive:
        archive.extractall(dest)
    visible_children = [
        path
        for path in dest.iterdir()
        if path.name != "__MACOSX" and not path.name.startswith("._")
    ]
    roots = [
        path
        for path in visible_children
        if path.is_dir()
    ]
    return roots[0] if len(visible_children) == 1 and len(roots) == 1 else dest


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def find_nested_mac_package(package_root: Path) -> Path | None:
    if (package_root / "manifest.json").exists():
        try:
            manifest = load_json(package_root / "manifest.json")
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
    if len(candidates) == 1:
        return candidates[0]

    png_roots = {
        path.parent
        for path in result_root.rglob("*.png")
        if not path.name.startswith("._") and "__MACOSX" not in path.parts
    }
    if len(png_roots) == 1 and len(aliases) == 1:
        return next(iter(png_roots))
    return None


def find_validation_jsons(result_root: Path) -> list[Path]:
    matches = [
        path
        for path in result_root.rglob("AE_VALIDATION_RESULT*.json")
        if "template" not in path.name.lower() and "__MACOSX" not in path.parts
    ]
    return sorted(matches)


def run(cmd: list[str], root: Path) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=root).returncode


def main() -> int:
    args = parse_args()
    repo = repo_root()
    with tempfile.TemporaryDirectory(prefix="olm_ae_host_return_") as tmp:
        tmp_path = Path(tmp)
        try:
            package_root = extract_if_zip(args.package, tmp_path / "package")
            result_root = extract_if_zip(args.result, tmp_path / "result")
            mac_root = materialize_mac_package(package_root, tmp_path)
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc))

        run_dir = args.run_dir.resolve() if args.run_dir else Path("/tmp") / "olm_ae_host_return"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True)

        checks = 0
        failures = 0
        for validation_json in find_validation_jsons(result_root):
            cmd = [sys.executable, "scripts/verify_ae_validation_result.py", str(validation_json)]
            if args.require_all_pass:
                cmd.append("--require-all-pass")
            failures += run(cmd, repo) != 0
            checks += 1

        for request_id, request_zip in pixel_request_entries(mac_root):
            candidate = find_pixel_result(result_root, request_id, request_zip)
            if candidate is None:
                print(f"[SKIP] {request_id}: no matching pixel return found")
                continue
            cmd = [
                sys.executable,
                "scripts/verify_ae_pixel_validation_result.py",
                str(request_zip),
                str(candidate),
                "--run-dir",
                str(run_dir / request_id),
            ]
            failures += run(cmd, repo) != 0
            checks += 1

        if checks == 0:
            return fail("no AE validation JSON or matching pixel validation returns found")
        if failures:
            return 1

    print(f"[OK] AE host return verified with {checks} check(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
