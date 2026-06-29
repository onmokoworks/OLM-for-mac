#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_writer_only_hypothesis.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "analyze_olmblur_writer_only_hypothesis.py"
    with tempfile.TemporaryDirectory(prefix="olmblur_writer_only_") as td:
        out_json = Path(td) / "writer_only.json"
        out_md = Path(td) / "writer_only.md"
        proc = subprocess.run(
            [sys.executable, str(script), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmblur_writer_only_hypothesis"
        assert payload["decision"] == "writer-only-swap-cannot-explain-all-active-witnesses"
        diag_counts = payload["diagnosis_counts"]
        assert diag_counts["floor05-only-match"] >= 1
        assert diag_counts["nearby-only-match"] >= 1
        assert diag_counts["writer-rule-irrelevant-at-this-witness"] >= 1
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMBlur Writer-Only Hypothesis Audit",
            "olmblur__case_0006",
            "(314,14)",
            "writer-only-swap-cannot-explain-all-active-witnesses",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] OLMBlur writer-only hypothesis smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
