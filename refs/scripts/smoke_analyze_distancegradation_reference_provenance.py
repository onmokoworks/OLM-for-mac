#!/usr/bin/env python3
"""Smoke-test the OLMDistanceGradation reference provenance audit."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmdistancegradation_provenance_") as tmp:
        out_json = Path(tmp) / "audit.json"
        out_md = Path(tmp) / "audit.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts/analyze_distancegradation_reference_provenance.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        groups = {group["group"]: group for group in data.get("groups", [])}
        if set(groups) != {"basic", "extended", "blur"}:
            raise AssertionError(f"unexpected groups: {sorted(groups)}")
        if any(group["normalized_nonzero_count"] != 0 for group in groups.values()):
            raise AssertionError("expected all AE-host candidates to match normalized refs exactly")
        if groups["extended"]["legacy_nonzero_count"] < 1:
            raise AssertionError("expected extended cases to expose legacy reference-generation drift")
        if "OLMDistanceGradation Reference Provenance Audit" not in out_md.read_text(encoding="utf-8"):
            raise AssertionError("markdown report missing title")
    print("[OK] DistanceGradation provenance audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
