#!/usr/bin/env python3
"""Validate a packaged macOS OLM plug-in zip before AE-host handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from verify_ae_validation_result import EXPECTED_PLUGINS


EXPECTED_PIXEL_REQUESTS = {
    "OLMBlur": "ae_pixel_olmblur_20260606",
    "OLMColorKey": "ae_pixel_olmcolorkey_20260606",
    "OLMToonDilate": "ae_pixel_olmtoondilate_20260606",
    "OLMDistanceGradation": "ae_pixel_olmdistancegradation_20260606",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="zip produced by scripts/package_mac_plugins.sh")
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def has_macos_metadata(package: Path) -> str | None:
    with zipfile.ZipFile(package) as archive:
        for name in archive.namelist():
            parts = Path(name).parts
            if "__MACOSX" in parts:
                return name
            if any(part.startswith("._") for part in parts):
                return name
            if any(part == ".DS_Store" for part in parts):
                return name
    return None


def zip_modes(package: Path) -> dict[str, int]:
    modes: dict[str, int] = {}
    with zipfile.ZipFile(package) as archive:
        for info in archive.infolist():
            modes[info.filename.rstrip("/")] = (info.external_attr >> 16) & 0xFFFF
    return modes


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - command-line verifier should show exact failure.
        raise ValueError(f"could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def single_package_root(root: Path) -> Path:
    children = [path for path in root.iterdir() if path.is_dir() and path.name != "__MACOSX"]
    if len(children) != 1:
        raise ValueError(f"package must contain one top-level directory, found {len(children)}")
    return children[0]


def verify_validation_template(repo: Path, template: Path) -> int:
    verifier = repo / "scripts" / "verify_ae_validation_result.py"
    proc = subprocess.run(
        [sys.executable, str(verifier), "--allow-incomplete", str(template)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc.returncode


def verify_pixel_request_zip(path: Path, expected_request_id: str) -> str | None:
    if not path.exists():
        return f"pixel validation request missing: {path.name}"
    if not zipfile.is_zipfile(path):
        return f"pixel validation request is not a zip: {path.name}"
    with tempfile.TemporaryDirectory(prefix="olm_pixel_request_verify_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(tmp_path)
        matches = list(tmp_path.rglob("request_manifest.json"))
        if len(matches) != 1:
            return f"pixel validation request must contain one request_manifest.json, found {len(matches)}"
        try:
            data = load_json(matches[0])
        except Exception as exc:  # noqa: BLE001
            return str(exc)
        if data.get("kind") != "olm_ae_pixel_validation_request":
            return "pixel request kind must be 'olm_ae_pixel_validation_request'"
        if data.get("request_id") != expected_request_id:
            return f"pixel request_id must be {expected_request_id!r}"
        for rel in ("reference_manifest.json", data.get("input_dir", ""), data.get("expected_dir", "")):
            if not isinstance(rel, str) or not rel:
                return "pixel request has an invalid relative path"
            if not (matches[0].parent / rel).exists():
                return f"pixel request missing required path: {rel}"
    return None


def main() -> int:
    args = parse_args()
    package = args.package.resolve()
    repo = Path(__file__).resolve().parents[1]
    if not package.exists():
        return fail(f"package not found: {package}")
    if not zipfile.is_zipfile(package):
        return fail(f"not a zip file: {package}")
    metadata_entry = has_macos_metadata(package)
    if metadata_entry:
        return fail(f"package contains macOS metadata entry: {metadata_entry}")
    archive_modes = zip_modes(package)

    with tempfile.TemporaryDirectory(prefix="olm_mac_plugin_pkg_verify_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(tmp_path)

        try:
            root = single_package_root(tmp_path)
            manifest = load_json(root / "manifest.json")
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc))

        if manifest.get("kind") != "olm_mac_plugin_package":
            return fail("manifest.kind must be 'olm_mac_plugin_package'")
        for key in ("configuration", "source_root", "packaged_at"):
            if not isinstance(manifest.get(key), str) or not manifest[key]:
                return fail(f"manifest.{key} must be a non-empty string")

        for rel_key in ("install_notes", "validation_checklist", "validation_result_template"):
            rel = manifest.get(rel_key)
            if not isinstance(rel, str) or not rel:
                return fail(f"manifest.{rel_key} must be a non-empty string")
            if not (root / rel).exists():
                return fail(f"manifest.{rel_key} missing file: {rel}")

        pixel_requests = manifest.get("ae_pixel_validation_requests")
        if not isinstance(pixel_requests, list) or not pixel_requests:
            return fail("manifest.ae_pixel_validation_requests must be a non-empty list")
        by_pixel_name = {entry.get("name"): entry for entry in pixel_requests if isinstance(entry, dict)}
        for name, request_id in EXPECTED_PIXEL_REQUESTS.items():
            entry = by_pixel_name.get(name)
            if not entry:
                return fail(f"missing AE pixel validation request entry: {name}")
            if entry.get("request_id") != request_id:
                return fail(f"{name}.request_id must be {request_id!r}")
            rel = entry.get("zip")
            if not isinstance(rel, str) or not rel:
                return fail(f"{name}.zip must be a non-empty string")
            problem = verify_pixel_request_zip(root / rel, request_id)
            if problem:
                return fail(f"{name}: {problem}")

        plugins = manifest.get("plugins")
        if not isinstance(plugins, list):
            return fail("manifest.plugins must be a list")
        by_name = {entry.get("name"): entry for entry in plugins if isinstance(entry, dict)}
        missing = [name for name in EXPECTED_PLUGINS if name not in by_name]
        extra = [name for name in by_name if name not in EXPECTED_PLUGINS]
        if missing:
            return fail(f"missing plugin package entries: {', '.join(missing)}")
        if extra:
            return fail(f"unknown plugin package entries: {', '.join(extra)}")

        for name in EXPECTED_PLUGINS:
            entry = by_name[name]
            bundle = entry.get("bundle")
            if not isinstance(bundle, str) or not bundle:
                return fail(f"{name}.bundle must be a non-empty string")
            bundle_path = root / bundle
            if not bundle_path.is_dir():
                return fail(f"{name} bundle directory missing: {bundle}")
            binary_path = bundle_path / "Contents" / "MacOS" / name
            if not binary_path.exists():
                return fail(f"{name} bundle binary missing: {binary_path.relative_to(root)}")
            archive_binary = f"{root.name}/{entry['bundle']}/Contents/MacOS/{name}"
            if archive_modes.get(archive_binary, 0) & 0o111 == 0:
                return fail(f"{name} bundle binary is not executable in zip metadata: {archive_binary}")
            sha = entry.get("binary_sha256")
            if not isinstance(sha, str) or len(sha) != 64:
                return fail(f"{name}.binary_sha256 must be a 64-char hex string")
            arch = entry.get("architectures")
            if arch != ["arm64", "x86_64"]:
                return fail(f"{name}.architectures must be ['arm64', 'x86_64']")

        template = root / manifest["validation_result_template"]
        if verify_validation_template(repo, template) != 0:
            return fail("validation result template failed schema verification")

    print(f"[OK] {package}: {len(EXPECTED_PLUGINS)} packaged plug-ins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
