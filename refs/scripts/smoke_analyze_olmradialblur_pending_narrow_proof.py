#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_pending_narrow_proof.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmradial_pending_") as tmp:
        out_json = Path(tmp) / "pending_narrow.json"
        out_md = Path(tmp) / "pending_narrow.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_pending_narrow_proof.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_pending_narrow_proof"
        lanes = {row["lane"]: row for row in report["narrow_lanes"]}
        assert lanes["zoom"]["witness"]["x"] == 6 and lanes["zoom"]["witness"]["y"] == 0
        assert lanes["tiny_rotation"]["witness"]["x"] == 1614 and lanes["tiny_rotation"]["witness"]["y"] == 6
        assert lanes["inner"]["classification"] == "partial_trace_after_effective_span"
        assert "alpha 0.99999994 versus local 1.0" in lanes["zoom"]["required_next_proof"]
        assert lanes["zoom"]["caller_collapse_boundary"]["preserved_validity_plane"] == "+0xf252"
        assert lanes["tiny_rotation"]["caller_collapse_boundary"]["final_polar_rgba_plane"] == "+0xe"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "zoom",
            "tiny_rotation",
            "inner",
            "1614,6",
            "+0xf252",
            "+0xe",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur pending narrow proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
