#!/usr/bin/env python3
"""Smoke-test the OLMColorKey Edge reference provenance audit."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_edge_provenance_") as tmp:
        out_json = Path(tmp) / "audit.json"
        out_md = Path(tmp) / "audit.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/analyze_colorkey_edge_reference_provenance.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        comparisons = data.get("comparisons", [])
        classification = data.get("classification", {})
        if len(comparisons) < 3:
            raise AssertionError("expected at least three reference comparisons")
        if classification.get("status") != "reference-generation-split":
            raise AssertionError(f"expected reference-generation-split, got {classification}")
        if "do not tune Edge Blur" not in classification.get("recommended_action", ""):
            raise AssertionError("classification should warn against tuning from legacy residual")
        exact_rows = [row for row in comparisons if row.get("status") == "compared" and row.get("max_diff") == 0]
        legacy_rows = [
            row
            for row in comparisons
            if row.get("status") == "compared"
            and str(row.get("reference", "")).endswith("refs/win_references/20260604_olm/OLMColorKey/case_0009.png")
        ]
        if not exact_rows:
            raise AssertionError("expected at least one exact reference-generation match")
        if not legacy_rows or legacy_rows[0].get("max_diff") != 47:
            raise AssertionError("expected legacy 20260604 reference to reproduce max_diff=47")
        markdown = out_md.read_text(encoding="utf-8")
        if "OLMColorKey Edge Reference Provenance Audit" not in markdown:
            raise AssertionError("markdown report missing title")
        if "reference-generation-split" not in markdown:
            raise AssertionError("markdown report missing classification")
    print("[OK] ColorKey Edge provenance audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
