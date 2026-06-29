#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmdirectionalblur_pending_witness_proof.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectional_pending_") as tmp:
        out_json = Path(tmp) / "pending_witness.json"
        out_md = Path(tmp) / "pending_witness.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmdirectionalblur_pending_witness_proof.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdirectionalblur_pending_witness_proof"
        assert report["angle0_lane"]["classification"] == "angle0-rgb-only-rowdriver-or-valid-alpha"
        assert report["angle0_lane"]["primary_witness"]["xy"] == [494, 169]
        assert report["diagonal_lane"]["classification"] == "diagonal-rgb-alpha-rotate-validity"
        assert report["diagonal_lane"]["primary_witness"]["xy"] == [507, 367]
        assert "helper-local source-to-destination range witness" in report["angle0_lane"]["required_next_proof"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Angle-0 Lane",
            "Diagonal Lane",
            "579,169",
            "507, 367",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMDirectionalBlur pending witness proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
