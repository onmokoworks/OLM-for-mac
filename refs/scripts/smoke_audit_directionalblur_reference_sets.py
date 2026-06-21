#!/usr/bin/env python3
"""Smoke-test the OLMDirectionalBlur reference set audit."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmdirectionalblur_ref_audit_") as tmp:
        out_json = Path(tmp) / "audit.json"
        out_md = Path(tmp) / "audit.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/audit_directionalblur_reference_sets.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        if summary.get("set_count") != 3:
            raise AssertionError(f"unexpected set count: {summary}")
        if summary.get("mixed_bulk_non_directional_count", 0) < 1:
            raise AssertionError("expected mixed non-DirectionalBlur files under bulk OLMDirectionalBlur")
        classes = data.get("class_counts", {}).get("bulk_20260619_mixed_directionalblur", {})
        if "directionalblur" not in classes or len(classes) < 2:
            raise AssertionError(f"expected mixed bulk class counts, got {classes}")
        if "OLMDirectionalBlur Reference Set Audit" not in out_md.read_text(encoding="utf-8"):
            raise AssertionError("markdown report missing title")
    print("[OK] DirectionalBlur reference set audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
