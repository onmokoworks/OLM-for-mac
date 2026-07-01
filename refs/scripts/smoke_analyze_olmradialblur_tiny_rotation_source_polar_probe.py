#!/usr/bin/env python3
"""Smoke-test the tiny-Rotation source-polar probe report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradialblur_source_polar_smoke_") as tmp:
        out_dir = Path(tmp)
        out_json = out_dir / "source_polar_probe.json"
        out_md = out_dir / "source_polar_probe.md"
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_olmradialblur_tiny_rotation_source_polar_probe.py",
                "--output-json",
                out_json,
                "--output-md",
                out_md,
            ],
            cwd=root,
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmradialblur_tiny_rotation_source_polar_probe"
        assert payload["sample_indices"] == [1603, 1604, 844, 845]
        assert payload["strongest_positive"][0]["xy"] == [1608, 838]
        assert payload["dominant_local_positive_cluster"][0]["xy"] == [1601, 843]
        assert payload["direct_source_cells"][0]["xy"] == [1603, 844]
        assert payload["direct_source_cells"][0]["rgba"][:3] == [0, 0, 0]
        markdown = out_md.read_text(encoding="utf-8")
        assert "row 843 / angles 1601..1602" in markdown
    print("[OK] OLMRadialBlur tiny-Rotation source-polar probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
