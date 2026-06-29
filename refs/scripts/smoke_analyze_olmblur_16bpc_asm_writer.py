#!/usr/bin/env python3
"""Smoke-test OLMBlur 16bpc ASM writer audit generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_asm_writer_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "audit.json"
        out_md = tmp_path / "audit.md"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "analyze_olmblur_16bpc_asm_writer.py"),
                "--summary-json",
                str(out_json),
                "--summary-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olmblur_16bpc_asm_writer_audit":
            raise AssertionError("unexpected audit kind")
        by_name = {
            row.get("name"): row
            for row in data.get("windows", [])
            if isinstance(row, dict)
        }
        standard = by_name.get("standard_16bpc_word_writer")
        alternate = by_name.get("alternate_16bpc_direct_word_writer")
        legacy8 = by_name.get("legacy_8bpc_byte_writer_family")
        if not standard or standard.get("classification") != "round-add-helper-truncate-word-store":
            raise AssertionError("standard 16bpc writer classification changed")
        if not alternate or alternate.get("classification") != "direct-memory-truncate-word-store":
            raise AssertionError("alternate 16bpc writer classification changed")
        if not legacy8 or legacy8.get("classification") != "round-add-helper-truncate-byte-store":
            raise AssertionError("legacy 8bpc writer family classification changed")
        if standard.get("word_stores") != 3 or alternate.get("word_stores") < 6:
            raise AssertionError("expected 16bpc word stores were not found")
        if "CVTTSS2SI" not in out_md.read_text(encoding="utf-8"):
            raise AssertionError("markdown should include instruction excerpts")
    print("[OK] OLMBlur 16bpc ASM writer audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
