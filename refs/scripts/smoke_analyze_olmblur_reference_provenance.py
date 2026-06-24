#!/usr/bin/env python3
"""Smoke-test the OLMBlur reference provenance audit."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmblur_provenance_") as tmp:
        out_json = Path(tmp) / "audit.json"
        out_md = Path(tmp) / "audit.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/analyze_olmblur_reference_provenance.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if len(data.get("cases", [])) != 7:
            raise AssertionError("expected seven OLMBlur cases")
        classification = data.get("classification", {})
        if classification.get("status") != "normalized-software-exact-with-legacy-drift":
            raise AssertionError("expected normalized exact with legacy drift classification")
        if classification.get("case_count") != 7:
            raise AssertionError("expected classification to cover seven OLMBlur cases")
        if classification.get("normalized_nonzero_count") != 0:
            raise AssertionError("expected classification normalized nonzero count to be zero")
        if classification.get("legacy_nonzero_count") != 4:
            raise AssertionError("expected classification legacy nonzero count to be four")
        if classification.get("legacy_nonzero_cases") != ["case_0001", "case_0002", "case_0003", "case_0004"]:
            raise AssertionError("unexpected OLMBlur old-reference drift cases")
        if data.get("normalized_nonzero_count") != 0:
            raise AssertionError("expected all AE-host candidates to match normalized refs exactly")
        if data.get("legacy_nonzero_count") != 4:
            raise AssertionError("expected four old-reference drift cases")
        md = out_md.read_text(encoding="utf-8")
        if "OLMBlur Reference Provenance Audit" not in md:
            raise AssertionError("markdown report missing title")
        if "normalized-software-exact-with-legacy-drift" not in md:
            raise AssertionError("markdown report missing classification")
    print("[OK] OLMBlur provenance audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
