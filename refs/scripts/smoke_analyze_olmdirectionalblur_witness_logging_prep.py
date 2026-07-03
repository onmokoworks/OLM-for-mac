#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmdirectionalblur_witness_logging_prep.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_logging_prep_") as tmp:
        out_json = Path(tmp) / "logging_prep.json"
        out_md = Path(tmp) / "logging_prep.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmdirectionalblur_witness_logging_prep.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmdirectionalblur_witness_logging_prep"
        assert payload["decision"] == "ready-for-next-witness-level-ab-denominator-validity-logging"
        assert payload["structural_base"] == "rotated-aex-full-choreo"
        source_anchors = payload["source_anchors"]
        assert source_anchors["rotate_helper_line"] > 0
        assert source_anchors["rowdriver_line"] > source_anchors["rotate_helper_line"]
        lanes = {row["family"]: row for row in payload["lanes"]}
        angle0 = lanes["angle0-rowdriver-valid-alpha"]
        diagonal = lanes["diagonal-rotate-validity"]
        assert angle0["primary_witness"]["xy"] == [494, 169]
        assert angle0["required_fields"][3] == "denominator plane pointer/value at the witness"
        assert "579,169" in "\n".join(angle0["witness_focus"])
        assert diagonal["primary_witness"]["xy"] == [507, 367]
        assert any("rotate sampler source coordinates and sample order" == row for row in diagonal["required_fields"])
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMDirectionalBlur Witness Logging Prep",
            "angle0-rowdriver-valid-alpha",
            "diagonal-rotate-validity",
            "Treat as answered when",
            "Treat as not answered when",
        ):
            assert needle in md, needle
    print("[OK] OLMDirectionalBlur witness logging prep smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
