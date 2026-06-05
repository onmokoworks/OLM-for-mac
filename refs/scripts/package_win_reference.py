#!/usr/bin/env python3
"""Package Windows reference PNGs with the case manifest for transfer to macOS."""

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("png_dir", help="directory containing rendered f0.png, f1.png, ...")
    parser.add_argument(
        "--manifest",
        default="refs/cases/olmsmoother_v1_minimal.json",
        help="case manifest JSON",
    )
    parser.add_argument("--out", default=None, help="output zip path")
    args = parser.parse_args()

    png_dir = Path(args.png_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    if not png_dir.is_dir():
        print(f"not a directory: {png_dir}", file=sys.stderr)
        return 2

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    out_path = (
        Path(args.out).resolve()
        if args.out
        else png_dir / f"{manifest.get('plugin', 'olm')}_{manifest.get('variant', 'reference')}_win_reference.zip"
    )

    package = {
        "schema": 1,
        "kind": "olm_win_reference_package",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_png_dir": str(png_dir),
        "manifest_name": manifest_path.name,
        "plugin": manifest.get("plugin"),
        "variant": manifest.get("variant"),
        "input": manifest.get("input"),
        "cases": [],
    }

    missing = []
    for case in manifest["cases"]:
        frame = case["frame"]
        png_path = png_dir / frame
        if not png_path.exists():
            missing.append(frame)
            continue
        package["cases"].append(
            {
                "id": case["id"],
                "frame": frame,
                "params": case.get("params", {}),
                "sha256": sha256(png_path),
                "bytes": png_path.stat().st_size,
            }
        )

    if missing:
        print("missing rendered frames:", ", ".join(missing), file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest_path, "case_manifest.json")
        archive.writestr("reference_package.json", json.dumps(package, indent=2, sort_keys=True))
        for case in package["cases"]:
            archive.write(png_dir / case["frame"], f"png/{case['frame']}")

    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
