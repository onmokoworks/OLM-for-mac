#!/usr/bin/env python3
"""Smoke-test the bounded OLMDistanceGradation residual classifier."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_residual_families_") as tmp:
        out_json = Path(tmp) / "classifier.json"
        out_md = Path(tmp) / "classifier.md"
        subprocess.run(
            [sys.executable, "scripts/analyze_distancegradation_16bpc_residual_families.py", "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdistancegradation_16bpc_residual_family_classifier"
        assert report["current_exact_cases"] == ["0008", "0010", "0011", "0020", "0021", "0022", "0023"]
        families = {family["id"]: family for family in report["families"]}
        assert families["layer-no-bg"]["cases"] == ["0012", "0013", "0014", "0016"]
        assert families["max-2"]["cases"] == ["0024", "0025", "0026", "0027"]
        assert families["outlier-0028"]["cases"] == ["0028"]
        assert "PF16 store words" in families["layer-no-bg"]["next_missing_boundary"]
        assert "field-world value" in families["max-2"]["next_missing_boundary"]
        assert "source/premultiply ownership" in families["outlier-0028"]["next_missing_boundary"]
        markdown = out_md.read_text(encoding="utf-8")
        for needle in ("Residual-Family Classifier", "layer-no-bg", "max-2", "outlier-0028", "No PNG-only tuning"):
            assert needle in markdown, needle
    print("[OK] DistanceGradation 16bpc residual-family classifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
