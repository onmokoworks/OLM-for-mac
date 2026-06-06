#!/usr/bin/env python3
"""Create a zip archive without macOS AppleDouble metadata entries."""

from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory to archive.")
    parser.add_argument("output", type=Path, help="Output zip path.")
    return parser.parse_args()


def should_skip(name: str) -> bool:
    return name == "__MACOSX" or name.startswith("._") or name == ".DS_Store"


def zip_info(path: Path, arcname: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(arcname)
    mode = path.stat().st_mode
    info.external_attr = (mode & 0xFFFF) << 16
    if stat.S_ISDIR(mode):
        info.external_attr |= 0x10
    return info


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise SystemExit(f"source must be a directory: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if any(should_skip(part) for part in path.relative_to(source).parts):
                continue
            rel = path.relative_to(source.parent).as_posix()
            if path.is_dir():
                archive.writestr(zip_info(path, rel + "/"), b"")
            else:
                archive.write(path, rel)
                info = archive.getinfo(rel)
                info.external_attr = (path.stat().st_mode & 0xFFFF) << 16

    print(f"wrote clean zip: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
