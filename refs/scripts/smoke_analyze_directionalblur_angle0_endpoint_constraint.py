#!/usr/bin/env python3
"""Smoke-test scripts/analyze_directionalblur_angle0_endpoint_constraint.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "analyze_directionalblur_angle0_endpoint_constraint.py"
    with tempfile.TemporaryDirectory(prefix="olmdirectional_endpoint_") as td:
        out_json = Path(td) / "endpoint.json"
        out_md = Path(td) / "endpoint.md"
        proc = subprocess.run(
            [sys.executable, str(script), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmdirectionalblur_angle0_endpoint_constraint"
        assert payload["witness_row_y"] == 169
        assert payload["endpoint_reasoning"]["rightmost_visible_strip_x"] == 579
        assert payload["endpoint_reasoning"]["required_min_source_x_for_same_row_front_helper"] == 580
        assert payload["endpoint_reasoning"]["same_row_segment_contains_that_source_x"] is False
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Angle-0 Endpoint Constraint",
            "579",
            "580",
            "front-helper-only explanation",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] OLMDirectionalBlur angle0 endpoint constraint smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
