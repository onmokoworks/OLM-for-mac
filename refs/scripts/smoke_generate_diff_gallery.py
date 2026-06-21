#!/usr/bin/env python3
"""Smoke-test the OLM diff gallery generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olm_diff_gallery_smoke_") as tmp:
        out_dir = Path(tmp) / "diff_gallery"
        proc = subprocess.run(
            [
                sys.executable,
                "refs/scripts/generate_diff_gallery.py",
                "--output-dir",
                str(out_dir),
                "--limit-per-report",
                "3",
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        html_path = out_dir / "index.html"
        data_path = out_dir / "data.json"
        if not html_path.exists() or not data_path.exists():
            print("[FAIL] diff gallery output files missing")
            return 1
        data = json.loads(data_path.read_text(encoding="utf-8"))
        if data.get("kind") != "olm_diff_gallery":
            print("[FAIL] unexpected diff gallery data kind")
            return 1
        html = html_path.read_text(encoding="utf-8")
        for needle in ("OLM Diff Gallery", "OLMBlur", "OLMKiraKira", "No durable non-exact image comparison"):
            if needle not in html:
                print(f"[FAIL] diff gallery HTML missing: {needle}")
                return 1
        missing = []
        for item in data.get("items", []):
            for asset in item.get("assets", {}).values():
                for path in asset.values():
                    if path and not (root / path).exists() and not (out_dir / Path(path).name).exists():
                        # Assets are copied under the smoke output dir; root-relative paths
                        # in data.json are only used for the durable default output.
                        local = out_dir / "assets" / Path(path).name
                        if not local.exists():
                            missing.append(str(path))
        if missing:
            print("[FAIL] missing gallery assets: " + ", ".join(missing[:5]))
            return 1
    print("[OK] generate diff gallery smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
