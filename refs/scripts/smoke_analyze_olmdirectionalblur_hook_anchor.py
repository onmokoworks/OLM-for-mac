#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmdirectionalblur_hook_anchor.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_hook_anchor_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts" / "analyze_olmdirectionalblur_hook_anchor.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmdirectionalblur_hook_anchor_audit"
        assert payload["angle0_lane"]["primary_witness"]["xy"] == [494, 169]
        assert payload["diagonal_lane"]["primary_witness"]["xy"] == [507, 367]
        assert payload["angle0_lane"]["identical_mask"] is True
        assert "valid-alpha side-channel" in payload["wanted_angle0_fields"]
        assert "rotate sampler source coordinates and order" in payload["wanted_diagonal_fields"]
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDirectionalBlur Hook Anchor Audit",
            "Angle-0 Anchor",
            "Diagonal Anchor",
            "Windows Hook Ask",
        ):
            assert needle in md, needle
    print("[OK] OLMDirectionalBlur hook-anchor smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
