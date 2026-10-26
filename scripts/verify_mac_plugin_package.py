#!/usr/bin/env python3
"""Validate a packaged macOS OLM plug-in zip before AE-host handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from verify_ae_validation_result import EXPECTED_PLUGINS


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


def binary_sha256(path: Path) -> str:
    """Return the digest of the bytes that will actually be loaded by AE."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(*args: str) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def binary_architectures(path: Path) -> set[str]:
    return set(command_output("lipo", "-archs", str(path)).split())


def binary_minimum_macos(path: Path, arch: str) -> str:
    output = command_output("xcrun", "vtool", "-show-build", "-arch", arch, str(path))
    for line in output.splitlines():
        fields = line.split()
        if fields and fields[0] == "minos" and len(fields) == 2:
            return fields[1]
    raise ValueError(f"{path}: no minimum macOS for {arch}")


def binary_sdk_version(path: Path, arch: str) -> str:
    output = command_output("xcrun", "vtool", "-show-build", "-arch", arch, str(path))
    for line in output.splitlines():
        fields = line.split()
        if fields and fields[0] == "sdk" and len(fields) == 2:
            return fields[1]
    raise ValueError(f"{path}: no SDK version for {arch}")


def signing_kind(bundle: Path) -> str:
    detail = subprocess.run(
        ["codesign", "-d", "--verbose=4", str(bundle)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout
    if "Signature=adhoc" in detail.splitlines():
        return "adhoc"
    if any(line.startswith("Authority=Developer ID Application:") for line in detail.splitlines()):
        return "developer-id-application"
    return "unknown"


def single_package_root(root: Path) -> Path:
    children = list(root.iterdir())
    if len(children) != 1 or not children[0].is_dir():
        raise ValueError(f"package must contain one top-level directory, found {len(children)}")
    return children[0]


def verify_layout(root: Path) -> None:
    expected = {name + ".plugin" for name in EXPECTED_PLUGINS} | {"README.md", "README.en.md", "LICENSE"}
    if root.name != "OLM_for_Mac" or {p.name for p in root.iterdir()} != expected:
        raise ValueError("package must contain only OLM_for_Mac with ten bundles, two READMEs and LICENSE")
    for name in ("README.md", "README.en.md", "LICENSE"):
        if not (root / name).is_file():
            raise ValueError(f"missing file: {name}")
    for name in ("README.md", "README.en.md"):
        for link in re.findall(r"\]\(([^)]+)\)", (root / name).read_text()):
            if "://" not in link and not link.startswith("#"):
                if not (root / link.split("#", 1)[0]).is_file():
                    raise ValueError(f"broken README link: {name}: {link}")


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
            verify_layout(root)
            manifest = load_json(Path(str(package) + ".manifest.json"))
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc))

        if manifest.get("kind") != "olm_mac_plugin_package":
            return fail("manifest.kind must be 'olm_mac_plugin_package'")
        for key in ("configuration", "source_root", "packaged_at", "git_commit", "xcode_version", "sdk_version"):
            if not isinstance(manifest.get(key), str) or not manifest[key]:
                return fail(f"manifest.{key} must be a non-empty string")
        if manifest["configuration"] not in {"Debug", "Release"}:
            return fail("manifest.configuration must be Debug or Release")
        if not isinstance(manifest.get("git_dirty"), bool):
            return fail("manifest.git_dirty must be a boolean")
        if len(manifest["git_commit"]) != 40 or any(c not in "0123456789abcdef" for c in manifest["git_commit"].lower()):
            return fail("manifest.git_commit must be a 40-char hexadecimal commit")

        plugins = manifest.get("plugins")
        if not isinstance(plugins, list):
            return fail("manifest.plugins must be a list")
        if len(plugins) != len(EXPECTED_PLUGINS):
            return fail("manifest must contain exactly ten plugins")
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
            if bundle != f"{name}.plugin":
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
            actual_sha = binary_sha256(binary_path)
            if sha.lower() != actual_sha:
                return fail(
                    f"{name}.binary_sha256 mismatch: manifest={sha} actual={actual_sha}"
                )
            arch = entry.get("architectures")
            if arch != ["arm64", "x86_64"]:
                return fail(f"{name}.architectures must be ['arm64', 'x86_64']")
            try:
                actual_arch = binary_architectures(binary_path)
            except (OSError, subprocess.CalledProcessError) as exc:
                return fail(f"{name}: could not inspect architectures: {exc}")
            if actual_arch != set(arch):
                return fail(f"{name}.architectures mismatch: manifest={arch} actual={sorted(actual_arch)}")
            minimum_macos = entry.get("minimum_macos")
            if not isinstance(minimum_macos, dict) or set(minimum_macos) != set(arch):
                return fail(f"{name}.minimum_macos must describe arm64 and x86_64")
            try:
                actual_minos = {item: binary_minimum_macos(binary_path, item) for item in arch}
                actual_sdks = {binary_sdk_version(binary_path, item) for item in arch}
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                return fail(f"{name}: could not inspect minimum macOS: {exc}")
            if minimum_macos != actual_minos:
                return fail(f"{name}.minimum_macos mismatch: manifest={minimum_macos} actual={actual_minos}")
            if actual_sdks != {manifest["sdk_version"]}:
                return fail(
                    f"{name} SDK mismatch: manifest={manifest['sdk_version']} "
                    f"actual={sorted(actual_sdks)}"
                )
            bundle_signing_kind = entry.get("signing_kind")
            try:
                subprocess.run(
                    ["codesign", "--verify", "--deep", "--strict", str(bundle_path)],
                    check=True,
                    capture_output=True,
                )
                actual_signing_kind = signing_kind(bundle_path)
            except (OSError, subprocess.CalledProcessError) as exc:
                return fail(f"{name}: codesign verification failed: {exc}")
            if bundle_signing_kind != actual_signing_kind or actual_signing_kind == "unknown":
                return fail(
                    f"{name}.signing_kind mismatch: manifest={bundle_signing_kind} "
                    f"actual={actual_signing_kind}"
                )

    print(f"[OK] {package}: {len(EXPECTED_PLUGINS)} packaged plug-ins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
