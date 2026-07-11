#!/usr/bin/env python3
"""Smoke-test curated runtime-trace comparison refresh helper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        index_json = tmp / "index.json"
        index_md = tmp / "index.md"
        proc = subprocess.run(
            [
                "python3",
                "scripts/refresh_curated_runtime_trace_comparisons.py",
                "--target",
                "distancegradation-case0023-refcon-wordmap",
                "--target",
                "radialblur-tiny-rotation-anchor-pointer",
                "--target",
                "smoother2-producer-path-diff",
                "--index-json",
                str(index_json),
                "--index-md",
                str(index_md),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr, end="")
            return proc.returncode
        data = json.loads(index_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olm_curated_runtime_trace_refresh_index":
            print("unexpected index kind", file=sys.stderr)
            return 1
        targets = data.get("targets")
        if not isinstance(targets, list) or len(targets) != 3:
            print("unexpected targets payload", file=sys.stderr)
            return 1
        slugs = {row.get("slug") for row in targets if isinstance(row, dict)}
        if slugs != {
            "distancegradation-case0023-refcon-wordmap",
            "radialblur-tiny-rotation-anchor-pointer",
            "smoother2-producer-path-diff",
        }:
            print("unexpected slug set", file=sys.stderr)
            return 1
        if not index_md.exists():
            print("missing markdown index", file=sys.stderr)
            return 1
    print("[OK] curated runtime-trace refresh smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
