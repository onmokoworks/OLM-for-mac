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
        if data.get("normalized_nonzero_count") != 0:
            raise AssertionError("expected all AE-host candidates to match normalized refs exactly")
        if data.get("legacy_nonzero_count") != 4:
            raise AssertionError("expected four old-reference drift cases")
        if "OLMBlur Reference Provenance Audit" not in out_md.read_text(encoding="utf-8"):
            raise AssertionError("markdown report missing title")
    print("[OK] OLMBlur provenance audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
