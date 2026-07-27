#!/usr/bin/env python3
"""Rewrite only OLMColorKey all-nine AEPX file references for Windows."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path


FILE_REFERENCE = re.compile(r"<fileReference\b[^>]*/>")
FULLPATH = re.compile(r'\bfullpath="([^"]*)"')
TARGET_IS_FOLDER = re.compile(r'\btarget_is_folder="([01])"')
PLATFORM = re.compile(r'\bplatform="[^"]*"')
INPUT_COUNT = 9
OUTPUT_COUNT = 18


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def references(text: str) -> list[str]:
    found = FILE_REFERENCE.findall(text)
    if len(found) != INPUT_COUNT + OUTPUT_COUNT:
        raise ValueError(f"expected 27 fileReference elements, got {len(found)}")
    return found


def classify(refs: list[str]) -> tuple[list[str], list[str]]:
    inputs: list[str] = []
    outputs: list[str] = []
    for ref in refs:
        match = TARGET_IS_FOLDER.search(ref)
        if match is None:
            raise ValueError("fileReference lacks target_is_folder")
        (outputs if match.group(1) == "1" else inputs).append(ref)
    if len(inputs) != INPUT_COUNT or len(outputs) != OUTPUT_COUNT:
        raise ValueError(
            f"expected 9 input and 18 output references, got {len(inputs)} and {len(outputs)}"
        )
    return inputs, outputs


def rewrite_reference(ref: str, fullpath: str) -> str:
    if FULLPATH.search(ref) is None or PLATFORM.search(ref) is None:
        raise ValueError("fileReference lacks fullpath or platform")
    replacement = f'fullpath="{html.escape(fullpath, quote=True)}"'
    rewritten = FULLPATH.sub(lambda _match: replacement, ref, count=1)
    return PLATFORM.sub('platform="Win"', rewritten, count=1)


def portable_basename(path: str) -> str:
    return re.split(r"[/\\]", html.unescape(path))[-1]


def canonicalize(text: str) -> bytes:
    refs = references(text)
    inputs, outputs = classify(refs)
    roles: dict[str, str] = {}
    for index, ref in enumerate(inputs, 1):
        path_match = FULLPATH.search(ref)
        if path_match is None:
            raise ValueError("input reference lacks fullpath")
        roles[ref] = (
            f'<fileReference role="input_{index:02d}:'
            f'{portable_basename(path_match.group(1))}"/>'
        )
    for index, ref in enumerate(outputs, 1):
        roles[ref] = f'<fileReference role="output_{index:02d}"/>'
    return FILE_REFERENCE.sub(lambda match: roles[match.group(0)], text).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac-aepx", type=Path, required=True)
    parser.add_argument("--windows-input-dir", required=True)
    parser.add_argument("--windows-output-dir", required=True)
    parser.add_argument("--windows-aepx", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    mac_text = args.mac_aepx.read_text(encoding="utf-8")
    refs = references(mac_text)
    inputs, outputs = classify(refs)
    replacements: dict[str, str] = {}
    input_names: list[str] = []
    for ref in inputs:
        path_match = FULLPATH.search(ref)
        if path_match is None:
            raise ValueError("input reference lacks fullpath")
        name = portable_basename(path_match.group(1))
        input_names.append(name)
        replacements[ref] = rewrite_reference(
            ref, args.windows_input_dir.rstrip("\\/") + "\\" + name
        )
    for ref in outputs:
        replacements[ref] = rewrite_reference(ref, args.windows_output_dir.rstrip("\\/"))

    windows_text = FILE_REFERENCE.sub(
        lambda match: replacements[match.group(0)], mac_text
    )
    if canonicalize(mac_text) != canonicalize(windows_text):
        raise ValueError("canonicalized Mac and Windows AEPX differ")
    args.windows_aepx.parent.mkdir(parents=True, exist_ok=True)
    args.windows_aepx.write_text(windows_text, encoding="utf-8", newline="")

    canonical_sha = hashlib.sha256(canonicalize(mac_text)).hexdigest()
    manifest = {
        "kind": "olmcolorkey_32bpc_all9_windows_aepx_transform",
        "schema_version": 1,
        "mac_aepx": {
            "path": str(args.mac_aepx.resolve()),
            "sha256": digest(args.mac_aepx),
        },
        "windows_aepx": {
            "path": str(args.windows_aepx.resolve()),
            "sha256": digest(args.windows_aepx),
        },
        "file_references": {
            "input_count": len(inputs),
            "output_count": len(outputs),
            "changed_count": len(refs),
            "unique_source_count": len(replacements),
            "input_names": input_names,
        },
        "canonical": {
            "mac_sha256": canonical_sha,
            "windows_sha256": hashlib.sha256(canonicalize(windows_text)).hexdigest(),
            "byte_exact": True,
        },
        "windows_paths": {
            "input_dir": args.windows_input_dir,
            "output_dir": args.windows_output_dir,
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
