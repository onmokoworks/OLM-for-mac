#!/usr/bin/env python3
"""Normalize AE-rendered PNG sequence names to the frame names in a manifest."""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="directory containing AE-rendered PNG files")
    parser.add_argument(
        "--manifest",
        default="refs/cases/olmsmoother_v1_minimal.json",
        help="case manifest JSON",
    )
    parser.add_argument("--dest", default=None, help="normalized output directory")
    parser.add_argument(
        "--mode",
        choices=("copy", "move"),
        default="copy",
        help="copy or move files into the normalized directory",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    manifest_path = Path(args.manifest).resolve()
    dest_dir = Path(args.dest).resolve() if args.dest else source_dir / "_normalized"

    if not source_dir.is_dir():
        print(f"not a directory: {source_dir}", file=sys.stderr)
        return 2
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    cases = manifest["cases"]
    pngs = sorted(
        path
        for path in source_dir.glob("*.png")
        if path.is_file() and path.parent != dest_dir
    )

    if len(pngs) != len(cases):
        print(
            f"expected {len(cases)} PNGs from manifest, found {len(pngs)} in {source_dir}",
            file=sys.stderr,
        )
        for path in pngs:
            print(f"  found: {path.name}", file=sys.stderr)
        return 1

    mapping = []
    for source_png, case in zip(pngs, cases):
        target_png = dest_dir / case["frame"]
        mapping.append(
            {
                "case_id": case["id"],
                "source": source_png.name,
                "target": case["frame"],
                "params": case.get("params", {}),
            }
        )
        print(f"{source_png.name} -> {case['frame']}  {case['id']}")

    if args.dry_run:
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in mapping:
        source_png = source_dir / item["source"]
        target_png = dest_dir / item["target"]
        if args.mode == "copy":
            shutil.copy2(source_png, target_png)
        else:
            shutil.move(str(source_png), str(target_png))

    map_path = dest_dir / "render_name_map.json"
    with map_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "schema": 1,
                "kind": "olm_normalized_render_names",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_dir": str(source_dir),
                "manifest": str(manifest_path),
                "mode": args.mode,
                "mapping": mapping,
            },
            handle,
            indent=2,
            sort_keys=True,
        )

    print(f"wrote: {dest_dir}")
    print(f"map={map_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
