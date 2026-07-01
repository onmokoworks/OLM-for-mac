#!/usr/bin/env python3
"""Smoke-test the tiny-Rotation row-coupling probe report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_row_coupling_smoke_") as tmp:
        out_dir = Path(tmp)
        out_json = out_dir / "row_coupling_probe.json"
        out_md = out_dir / "row_coupling_probe.md"
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_tiny_rotation_row_coupling_probe.py",
                "--output-json",
                out_json,
                "--output-md",
                out_md,
            ],
            cwd=root,
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmradialblur_tiny_rotation_row_coupling_probe"
        assert payload["reference"]["bright_count"] == 17
        variants = {row["name"]: row for row in payload["variants"]}
        assert variants["baseline"]["bright_count"] == 0
        assert variants["prev2-k2-positive"]["bright_count"] == 0
        assert variants["prev2-row-tail-positive"]["bright_count"] == 0
        assert variants["baseline"]["patch_r"] == [[0, 0, 0], [4, 0, 0], [5, 1, 0]]
        assert variants["prev2-k2-positive"]["patch_r"] == [[0, 0, 0], [4, 0, 0], [5, 1, 0]]
        markdown = out_md.read_text(encoding="utf-8")
        assert "bright-pixel count remains zero" in markdown
        assert "prev2-k2-positive" in markdown
    print("[OK] OLMRadialBlur tiny-Rotation row-coupling probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
